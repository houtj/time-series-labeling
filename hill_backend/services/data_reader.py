"""
Data Reader Service
Provides memory-mapped file reading for efficient access to large binary time series files
"""

import numpy as np
import json
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


class MemoryMappedDataReader:
    """
    Efficiently read slices from large binary time series files using memory mapping.
    
    The binary file format is a flat array of float64 values arranged as:
    [x_values][ch1_values][ch2_values]...
    
    Each array is contiguous with length = total_points.
    """
    
    def __init__(self, binary_path: str, meta_path: str):
        """
        Initialize the reader with paths to binary and metadata files.
        
        Args:
            binary_path: Path to the .bin file
            meta_path: Path to the _meta.json file
        """
        self.binary_path = Path(binary_path)
        self.meta_path = Path(meta_path)
        
        # Load metadata
        with open(self.meta_path, 'r') as f:
            self.meta = json.load(f)
        
        self.total_points = self.meta['totalPoints']
        self.num_columns = self.meta['shape'][1]
        self.dtype = np.dtype(self.meta.get('dtype', 'float64'))
        
        # Memory-map the binary file
        # Shape is (total_points, num_columns) for row-major access
        self._mmap = np.memmap(
            self.binary_path,
            dtype=self.dtype,
            mode='r',
            shape=(self.total_points, self.num_columns)
        )
        
        logger.debug(f"Opened memory-mapped file: {self.binary_path}, shape: {self._mmap.shape}")
    
    @property
    def x_min(self) -> float:
        """Get minimum x value."""
        return float(self.meta['xColumn']['min'])
    
    @property
    def x_max(self) -> float:
        """Get maximum x value."""
        return float(self.meta['xColumn']['max'])
    
    @property
    def channels(self) -> list[dict[str, Any]]:
        """Get channel metadata."""
        return self.meta['channels']
    
    @property
    def x_column_info(self) -> dict[str, Any]:
        """Get x-axis column metadata."""
        return self.meta['xColumn']
    
    @property
    def x_type(self) -> str:
        """Get x-axis type: 'timestamp' or 'numeric'."""
        return self.meta['xColumn'].get('type', 'numeric')
    
    @property
    def x_format(self) -> str | None:
        """Get x-axis format string for timestamp display."""
        return self.meta['xColumn'].get('format')
    
    @property
    def version(self) -> int:
        """Get metadata version."""
        return self.meta.get('version', 1)
    
    def get_slice(
        self, 
        x_min: float, 
        x_max: float
    ) -> tuple[np.ndarray, int]:
        """
        Get a slice of data for the specified x range.
        
        Args:
            x_min: Start of range (in x-axis units)
            x_max: End of range (in x-axis units)
        
        Returns:
            Tuple of:
                - data: 2D array of shape (slice_length, num_columns)
                - original_count: Number of points in the original range
        """
        # Get x column (column 0)
        x_col = self._mmap[:, 0]
        
        # Binary search for range indices
        start_idx = int(np.searchsorted(x_col, x_min, side='left'))
        end_idx = int(np.searchsorted(x_col, x_max, side='right'))
        
        # Clamp to valid range
        start_idx = max(0, start_idx)
        end_idx = min(self.total_points, end_idx)
        
        original_count = end_idx - start_idx
        
        # Read the slice (this actually loads data from disk)
        data = np.array(self._mmap[start_idx:end_idx, :])
        
        logger.debug(f"Read slice [{start_idx}:{end_idx}] = {original_count} points")
        
        return data, original_count
    
    def get_full_data(self) -> tuple[np.ndarray, int]:
        """
        Get all data from the file.
        
        Returns:
            Tuple of:
                - data: 2D array of shape (total_points, num_columns)
                - original_count: Total number of points
        """
        return np.array(self._mmap[:, :]), self.total_points
    
    def close(self):
        """Close the memory-mapped file."""
        if hasattr(self, '_mmap'):
            del self._mmap


# Cache of open readers to avoid reopening files
_reader_cache: dict[str, MemoryMappedDataReader] = {}


def get_data_reader(binary_path: str, meta_path: str) -> MemoryMappedDataReader:
    """
    Get or create a data reader for the specified file.
    
    Readers are cached to avoid reopening files on every request.
    
    Args:
        binary_path: Path to the .bin file
        meta_path: Path to the _meta.json file
    
    Returns:
        MemoryMappedDataReader instance
    """
    cache_key = binary_path
    
    if cache_key not in _reader_cache:
        _reader_cache[cache_key] = MemoryMappedDataReader(binary_path, meta_path)
        logger.debug(f"Created new data reader for: {binary_path}")
    
    return _reader_cache[cache_key]


def clear_reader_cache():
    """Clear the reader cache, closing all open files."""
    global _reader_cache
    for reader in _reader_cache.values():
        reader.close()
    _reader_cache = {}
    logger.debug("Cleared data reader cache")
