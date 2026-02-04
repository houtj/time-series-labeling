"""
Resampler Service
Downsamples multi-channel time series data using MinMaxLTTB with union of indices
"""

import numpy as np
from tsdownsample import MinMaxLTTBDownsampler
import logging

logger = logging.getLogger(__name__)


class ResamplerService:
    """
    Downsample multi-channel time series using MinMaxLTTB with union of indices.
    
    This ensures all channels share the same x-values after downsampling,
    preserving visually important points from each channel.
    """
    
    def __init__(self, target_points_per_channel: int = 20000):
        """
        Initialize the resampler.
        
        Args:
            target_points_per_channel: Target number of points to keep per channel.
                                       Final count may be higher due to union of indices.
        """
        self.target_points = target_points_per_channel
        self.downsampler = MinMaxLTTBDownsampler()
    
    def resample(
        self, 
        x: np.ndarray, 
        channels: list[np.ndarray]
    ) -> tuple[np.ndarray, list[np.ndarray], bool]:
        """
        Resample multiple channels, keeping union of important indices.
        
        Args:
            x: X-axis values (timestamps or indices), shape (N,)
            channels: List of y-value arrays, each shape (N,)
        
        Returns:
            Tuple of:
                - x_out: Resampled x values
                - channels_out: List of resampled channel arrays
                - is_full_resolution: True if no resampling was needed
        """
        n_points = len(x)
        n_channels = len(channels)
        
        # Calculate max possible points after union
        max_union_points = self.target_points * n_channels
        
        # No resampling needed if data is small enough
        if n_points <= self.target_points:
            logger.debug(f"No resampling needed: {n_points} points <= {self.target_points} target")
            return x, channels, True
        
        logger.debug(f"Resampling {n_points} points with {n_channels} channels, target {self.target_points}/channel")
        
        # Ensure x is contiguous (required by tsdownsample)
        x_contig = np.ascontiguousarray(x)
        
        # Collect indices from each channel using MinMaxLTTB
        all_indices = set()
        
        for i, ch in enumerate(channels):
            try:
                # Ensure channel array is contiguous (required by tsdownsample)
                ch_contig = np.ascontiguousarray(ch)
                
                # MinMaxLTTB returns indices of selected points
                indices = self.downsampler.downsample(x_contig, ch_contig, n_out=self.target_points)
                all_indices.update(indices.tolist())
                logger.debug(f"Channel {i}: selected {len(indices)} points")
            except Exception as e:
                logger.warning(f"Failed to downsample channel {i}: {e}, using uniform sampling")
                # Fallback to uniform sampling for this channel
                step = max(1, n_points // self.target_points)
                indices = np.arange(0, n_points, step)[:self.target_points]
                all_indices.update(indices.tolist())
        
        # Sort indices to maintain order
        selected_indices = np.array(sorted(all_indices), dtype=np.int64)
        
        logger.debug(f"Union produced {len(selected_indices)} points from {n_points} original")
        
        # Extract values at selected indices
        x_out = x[selected_indices]
        channels_out = [ch[selected_indices] for ch in channels]
        
        return x_out, channels_out, False
    
    def resample_array(
        self, 
        data: np.ndarray,
        x_column: int = 0
    ) -> tuple[np.ndarray, bool]:
        """
        Resample a 2D array where first column is x and rest are channels.
        
        Args:
            data: 2D array shape (N, M) where M = 1 (x) + num_channels
            x_column: Index of the x-axis column (default: 0)
        
        Returns:
            Tuple of:
                - Resampled 2D array
                - is_full_resolution: True if no resampling was needed
        """
        x = data[:, x_column]
        
        # Extract all other columns as channels
        channel_indices = [i for i in range(data.shape[1]) if i != x_column]
        channels = [data[:, i] for i in channel_indices]
        
        x_out, channels_out, is_full = self.resample(x, channels)
        
        # Reconstruct array with x in original position
        result_cols = []
        ch_idx = 0
        for i in range(data.shape[1]):
            if i == x_column:
                result_cols.append(x_out)
            else:
                result_cols.append(channels_out[ch_idx])
                ch_idx += 1
        
        result = np.column_stack(result_cols)
        return result, is_full


# Singleton instance for reuse
_default_resampler: ResamplerService | None = None


def get_resampler(target_points: int = 20000) -> ResamplerService:
    """Get or create a resampler instance."""
    global _default_resampler
    if _default_resampler is None or _default_resampler.target_points != target_points:
        _default_resampler = ResamplerService(target_points)
    return _default_resampler
