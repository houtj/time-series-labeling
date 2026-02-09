"""
File Parser Worker
Consumes file parsing tasks from Redis Streams and processes them

Run: python -m workers.file_parser
"""
import logging
import sys
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
import simplejson as json
import pandas as pd
import numpy as np
from bson.objectid import ObjectId

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from database import get_db, get_data_folder_path
from redis_client import get_redis_client

# Threshold for using binary format (100k points)
BINARY_FORMAT_THRESHOLD = 100_000

# Common time format patterns for auto-detection
TIME_FORMAT_PATTERNS = [
    ('%Y-%m-%d %H:%M:%S.%f', r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+'),
    ('%Y-%m-%d %H:%M:%S', r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'),
    ('%Y-%m-%dT%H:%M:%S.%f', r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+'),
    ('%Y-%m-%dT%H:%M:%S', r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'),
    ('%Y/%m/%d %H:%M:%S', r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}'),
    ('%m/%d/%Y %H:%M:%S', r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}'),
    ('%d/%m/%Y %H:%M:%S', r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}'),
    ('%Y-%m-%d', r'\d{4}-\d{2}-\d{2}$'),
    ('%H:%M:%S.%f', r'\d{2}:\d{2}:\d{2}\.\d+$'),
    ('%H:%M:%S', r'\d{2}:\d{2}:\d{2}$'),
]


# ===== Time Format Detection =====

def detect_time_format(sample_strings: list[str]) -> Optional[str]:
    """
    Detect the time format from sample strings.
    
    Args:
        sample_strings: List of sample time strings
    
    Returns:
        Format string (strftime format) or None if not detected
    """
    if not sample_strings:
        return None
    
    sample = str(sample_strings[0]).strip()
    
    # Try each pattern
    for fmt, pattern in TIME_FORMAT_PATTERNS:
        if re.match(pattern, sample):
            # Verify by parsing
            try:
                datetime.strptime(sample, fmt)
                return fmt
            except ValueError:
                continue
    
    # Try pandas auto-detection as fallback
    try:
        pd.to_datetime(sample)
        return 'auto'  # Will use pandas for parsing
    except:
        pass
    
    return None


def is_numeric_series(series: pd.Series) -> bool:
    """
    Check if a pandas Series contains numeric values.
    
    Args:
        series: pandas Series to check
    
    Returns:
        True if the series is numeric (int/float), False otherwise
    """
    # Check if dtype is already numeric
    if pd.api.types.is_numeric_dtype(series):
        return True
    
    # Try converting to numeric - if it fails, it's not numeric
    try:
        pd.to_numeric(series, errors='raise')
        return True
    except (ValueError, TypeError):
        return False


def parse_time_string(time_str: str, fmt: str) -> float:
    """
    Parse a time string to Unix timestamp (seconds since epoch).
    
    Args:
        time_str: Time string to parse
        fmt: strftime format string or 'auto'
    
    Returns:
        Unix timestamp as float (includes fractional seconds)
    """
    try:
        if fmt == 'auto':
            dt = pd.to_datetime(time_str)
            return dt.timestamp()
        else:
            dt = datetime.strptime(str(time_str).strip(), fmt)
            return dt.timestamp()
    except Exception as e:
        raise ValueError(f"Failed to parse time '{time_str}' with format '{fmt}': {e}")


def convert_times_to_timestamps(time_strings: list, fmt: str) -> tuple[np.ndarray, str]:
    """
    Convert a list of time strings to Unix timestamps.
    
    Args:
        time_strings: List of time strings
        fmt: strftime format string or 'auto'
    
    Returns:
        Tuple of (numpy array of timestamps, detected/confirmed format string)
    """
    n = len(time_strings)
    timestamps = np.zeros(n, dtype=np.float64)
    
    # For 'auto' format, use pandas for bulk conversion (faster)
    if fmt == 'auto':
        try:
            dt_series = pd.to_datetime(time_strings)
            # Get the inferred format from first value for display
            sample = str(time_strings[0]).strip()
            detected_fmt = detect_display_format(sample, dt_series[0])
            timestamps = (dt_series.astype('int64') / 1e9).values  # Convert to seconds
            return timestamps, detected_fmt
        except Exception as e:
            raise ValueError(f"Failed to parse times with auto format: {e}")
    
    # Parse individually with known format
    for i, ts in enumerate(time_strings):
        timestamps[i] = parse_time_string(ts, fmt)
    
    return timestamps, fmt


def detect_display_format(sample_str: str, parsed_dt: datetime) -> str:
    """
    Determine the best display format for a time string.
    
    Args:
        sample_str: Original time string
        parsed_dt: Parsed datetime
    
    Returns:
        strftime format string for display
    """
    sample = str(sample_str).strip()
    
    # Check if has microseconds
    has_micro = '.' in sample and any(c.isdigit() for c in sample.split('.')[-1])
    
    # Check if has date part
    has_date = '-' in sample or '/' in sample
    
    # Check if has time part
    has_time = ':' in sample
    
    if has_date and has_time:
        if has_micro:
            return '%Y-%m-%d %H:%M:%S.%f'
        else:
            return '%Y-%m-%d %H:%M:%S'
    elif has_date:
        return '%Y-%m-%d'
    elif has_time:
        if has_micro:
            return '%H:%M:%S.%f'
        else:
            return '%H:%M:%S'
    else:
        return '%Y-%m-%d %H:%M:%S'  # Default


# ===== Logging Setup =====

def setup_logging():
    """Configure structured logging"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (persistent logs)
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# ===== Parsing Logic (from original parsing.py) =====

logger = logging.getLogger(__name__)

def parse_file(db, f, data_folder_path):
    """
    Parse file according to template configuration
    
    Args:
        db: Database instance
        f: File document from MongoDB
        data_folder_path: Path to data folder
    
    Returns:
        List of channel data dictionaries
    """
    json_dict = []
    file_id = str(f['_id'])
    
    logger.debug(f"Parsing file ID: {file_id}")
    
    # Get folder and template info
    folderInfo = db['folders'].find_one({'fileList': file_id})
    if folderInfo is None:
        raise ValueError(f"Folder not found for file {file_id}")
    
    templateId = folderInfo['template']['id']
    templateInfo = db['templates'].find_one({'_id': ObjectId(templateId)})
    if templateInfo is None:
        raise ValueError(f"Template not found: {templateId}")
    
    local_path = f'{data_folder_path}/{f["rawPath"]}'
    
    # Parse file based on type
    if templateInfo['fileType'] == '.xlsx':
        sheet_name = templateInfo['sheetName']
        try:
            sheet_name = int(sheet_name)
        except:
            pass
        try:
            df = pd.read_excel(local_path, sheet_name=sheet_name, engine='openpyxl', header=templateInfo['headRow'])
            df = df.loc[templateInfo['skipRow']:, :]
        except Exception as e:
            raise Exception(f'Cannot open Excel file: {e}')
    
    elif templateInfo['fileType'] == '.xls':
        sheet_name = templateInfo['sheetName']
        try:
            sheet_name = int(sheet_name)
        except:
            pass
        try:
            df = pd.read_excel(local_path, sheet_name=sheet_name, engine='xlrd', header=templateInfo['headRow'])
            df = df.loc[templateInfo['skipRow']:, :]
        except Exception as e:
            raise Exception(f'Cannot open XLS file: {e}')
    
    elif templateInfo['fileType'] == '.csv':
        try:
            df = pd.read_csv(local_path, header=templateInfo['headRow'])
            df = df.loc[templateInfo['skipRow']:, :]
        except Exception as e:
            raise Exception(f'Cannot open CSV file: {e}')
    
    else:
        raise ValueError(f"Unsupported file type: {templateInfo['fileType']}")
    
    # Extract X-axis
    use_index = templateInfo.get('x', {}).get('useIndex', False)

    if use_index:
        # Use row index as x-axis (0 to N-1)
        x = list(range(len(df)))
        logger.info(f"Using row index as x-axis: 0 to {len(df) - 1}")
        json_dict.append({
            'x': True,
            'name': 'index',
            'unit': '',
            'data': x
        })
    else:
        columnNames = df.columns.values.tolist()
        x_regex = templateInfo['x']['regex']

        if 'col:' in x_regex:
            x_regex = x_regex.replace('col:', '').strip()
            try:
                x_regex = int(x_regex)
            except:
                raise Exception(f'expect col:[number], got col:{x_regex} for x_axis')
            x = df.iloc[:, x_regex]
        else:
            for c in columnNames:
                if re.match(x_regex, c):
                    break
            else:
                logger.error(f"Available columns: {columnNames}")
                raise Exception(f'x axis not found for regex {x_regex}')
            x = df[c]

        # Validate: if isTime is not enabled, x-axis must be numeric
        is_time_enabled = templateInfo.get('x', {}).get('isTime', False)

        if not is_time_enabled and not is_numeric_series(x):
            sample_value = x.iloc[0] if len(x) > 0 else "N/A"
            raise Exception(
                f'X-axis contains non-numeric values (e.g., "{sample_value}"), '
                f'but "isTime" is not enabled in the template. '
                f'Please enable "isTime" for the x-axis if the data contains timestamps.'
            )

        # Convert to time if needed (default to False if not specified)
        if is_time_enabled:
            try:
                x = pd.to_datetime(x).dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    x = pd.to_datetime(x, format='mixed').dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    raise Exception('x axis cannot be converted to time')

        x = x.values.tolist()
        json_dict.append({
            'x': True,
            'name': templateInfo['x']['name'],
            'unit': templateInfo['x'].get('unit', ''),
            'data': x
        })
    
    # Extract channels
    for channel in templateInfo['channels']:
        channel_data = get_channel(channel, df)
        if channel_data is None:
            continue
        json_dict.append({
            'x': False,
            'name': channel['channelName'],
            'unit': channel['unit'],
            'color': channel['color'],
            'data': channel_data
        })
    
    logger.debug(f"Parsed {len(json_dict)} channels from file")
    return json_dict


def get_channel(channel, df):
    """
    Extract channel data from DataFrame
    
    Args:
        channel: Channel configuration dict
        df: pandas DataFrame
    
    Returns:
        List of channel values or None if not found and not mandatory
    """
    columnNames = df.columns.values.tolist()
    channel_regex = channel['regex']
    
    if 'col:' in channel_regex:
        channel_regex = channel_regex.replace('col:', '').strip()
        try:
            channel_regex = int(channel_regex)
        except:
            if channel['mandatory'] == False:
                return None
            else:
                raise Exception(f'expect col:[number], got col:{channel_regex} for {channel["channelName"]}')
        channel_data = df.iloc[:, channel_regex].astype(float)
    else:
        for c in columnNames:
            if channel_regex == c:
                break
        else:
            if channel['mandatory'] == False:
                return None
            else:
                raise Exception(f'Channel {channel["channelName"]} not found')
        channel_data = df[c].astype(float)
    
    channel_data = channel_data.values.tolist()
    return channel_data


def save_as_binary_format(json_dict: list, output_path: str) -> dict:
    """
    Save parsed data in memory-mappable binary format.
    
    For time-based x-axis:
    - Converts time strings to Unix timestamps (float64 seconds since epoch)
    - Stores format string in metadata for display conversion
    
    For numeric x-axis:
    - Stores values directly as float64
    
    Args:
        json_dict: Parsed data in JSON format (list of channel dicts)
        output_path: Base path for output files (without extension)
    
    Returns:
        Metadata dict with file information
    """
    # Find x-axis and channels
    x_trace = next(d for d in json_dict if d['x'])
    channels = [d for d in json_dict if not d['x']]
    
    n_points = len(x_trace['data'])
    n_cols = 1 + len(channels)  # x + channels
    
    # Determine if x-axis is time-based (string) or numeric
    x_data = x_trace['data']
    x_is_time = isinstance(x_data[0], str) if x_data else False
    
    if x_is_time:
        # Detect time format
        sample_strings = x_data[:10]  # Use first 10 for detection
        detected_format = detect_time_format(sample_strings)
        
        if detected_format is None:
            logger.warning("Could not detect time format, treating as numeric indices")
            x_numeric = np.arange(n_points, dtype=np.float64)
            x_type = 'numeric'
            x_format = None
        else:
            # Convert time strings to Unix timestamps
            logger.info(f"Detected time format: {detected_format}")
            try:
                x_numeric, x_format = convert_times_to_timestamps(x_data, detected_format)
                x_type = 'timestamp'
                logger.info(f"Converted {n_points} time strings to timestamps")
                logger.info(f"Timestamp range: {x_numeric[0]:.3f} to {x_numeric[-1]:.3f}")
            except Exception as e:
                logger.error(f"Failed to convert times: {e}, using numeric indices")
                x_numeric = np.arange(n_points, dtype=np.float64)
                x_type = 'numeric'
                x_format = None
    else:
        x_numeric = np.array(x_data, dtype=np.float64)
        x_type = 'numeric'
        x_format = None
    
    # Create numpy array (row-major: each row is [x, ch1, ch2, ...])
    arr = np.zeros((n_points, n_cols), dtype=np.float64)
    arr[:, 0] = x_numeric
    
    for i, ch in enumerate(channels):
        ch_data = np.array(ch['data'], dtype=np.float64)
        # Handle NaN values - keep as NaN for proper handling
        arr[:, i + 1] = ch_data
    
    # Save binary file
    binary_path = f"{output_path}.bin"
    arr.tofile(binary_path)
    
    logger.info(f"Saved binary file: {binary_path}, shape: {arr.shape}")
    
    # Create metadata
    meta = {
        "format": "binary",
        "version": 2,  # Version 2 uses timestamps instead of indices
        "shape": [n_points, n_cols],
        "dtype": "float64",
        "totalPoints": n_points,
        "xColumn": {
            "name": x_trace['name'],
            "unit": x_trace.get('unit', ''),
            "type": x_type,  # 'timestamp' or 'numeric'
            "column": 0,
            "min": float(x_numeric[0]),
            "max": float(x_numeric[-1]),
        },
        "channels": [
            {
                "name": ch['name'],
                "unit": ch.get('unit', ''),
                "color": ch.get('color', '#000000'),
                "column": i + 1
            }
            for i, ch in enumerate(channels)
        ]
    }
    
    # Add format string for timestamp display
    if x_type == 'timestamp' and x_format:
        meta["xColumn"]["format"] = x_format
        meta["xColumn"]["timezone"] = "local"  # Default to local, can be configured
    
    # Save metadata
    meta_path = f"{output_path}_meta.json"
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    
    logger.info(f"Saved metadata file: {meta_path}")
    
    return meta


def generate_overview_data(json_dict: list, target_points_per_channel: int = 5000) -> tuple[list, dict]:
    """
    Generate downsampled overview data for initial chart display.
    
    Uses MinMaxLTTB with union of indices to preserve important features.
    For time-based x-axis, converts to timestamps for consistent handling.
    
    Args:
        json_dict: Parsed data in JSON format
        target_points_per_channel: Target points per channel
    
    Returns:
        Tuple of (downsampled data in JSON format, overview metadata dict)
    """
    from tsdownsample import MinMaxLTTBDownsampler
    
    # Find x-axis and channels
    x_trace = next(d for d in json_dict if d['x'])
    channels = [d for d in json_dict if not d['x']]
    
    n_points = len(x_trace['data'])
    x_data = x_trace['data']
    x_is_time = isinstance(x_data[0], str) if x_data else False
    
    # Prepare x values and detect format
    x_format = None
    if x_is_time:
        sample_strings = x_data[:10]
        detected_format = detect_time_format(sample_strings)
        if detected_format:
            try:
                x_numeric, x_format = convert_times_to_timestamps(x_data, detected_format)
            except:
                # Fallback to indices
                x_numeric = np.arange(n_points, dtype=np.float64)
                x_is_time = False
        else:
            x_numeric = np.arange(n_points, dtype=np.float64)
            x_is_time = False
    else:
        x_numeric = np.array(x_data, dtype=np.float64)
    
    # Overview metadata
    overview_meta = {
        'xType': 'timestamp' if x_is_time else 'numeric',
        'xFormat': x_format,
        'xMin': float(x_numeric[0]),
        'xMax': float(x_numeric[-1]),
        'totalPoints': n_points
    }
    
    # No resampling needed if data is small
    if n_points <= target_points_per_channel:
        # Still convert times to timestamps for consistency
        if x_is_time and x_format:
            result = [{
                'x': True,
                'name': x_trace['name'],
                'unit': x_trace.get('unit', ''),
                'data': x_numeric.tolist()
            }]
        else:
            result = [{
                'x': True,
                'name': x_trace['name'],
                'unit': x_trace.get('unit', ''),
                'data': x_data if not x_is_time else x_numeric.tolist()
            }]
        
        for ch in channels:
            result.append({
                'x': False,
                'name': ch['name'],
                'unit': ch.get('unit', ''),
                'color': ch.get('color', '#000000'),
                'data': ch['data']
            })
        
        overview_meta['overviewPoints'] = n_points
        return result, overview_meta
    
    # Collect channel data as numpy arrays
    channel_arrays = []
    for ch in channels:
        ch_arr = np.array(ch['data'], dtype=np.float64)
        ch_arr = np.nan_to_num(ch_arr, nan=0.0)  # Replace NaN for algorithm
        channel_arrays.append(ch_arr)
    
    # Run MinMaxLTTB on each channel and collect indices
    downsampler = MinMaxLTTBDownsampler()
    all_indices = set()
    
    for ch_arr in channel_arrays:
        try:
            indices = downsampler.downsample(x_numeric, ch_arr, n_out=target_points_per_channel)
            all_indices.update(indices.tolist())
        except Exception as e:
            logger.warning(f"MinMaxLTTB failed: {e}, using uniform sampling")
            step = max(1, n_points // target_points_per_channel)
            indices = list(range(0, n_points, step))[:target_points_per_channel]
            all_indices.update(indices)
    
    # Sort indices
    selected_indices = sorted(all_indices)
    
    logger.info(f"Generated overview: {n_points} -> {len(selected_indices)} points")
    
    # Build output with timestamps (not time strings)
    result = []
    
    # X-axis - always use numeric values (timestamps or original numbers)
    x_out = [float(x_numeric[i]) for i in selected_indices]
    
    result.append({
        'x': True,
        'name': x_trace['name'],
        'unit': x_trace.get('unit', ''),
        'data': x_out
    })
    
    # Channels
    for ch in channels:
        ch_out = [ch['data'][i] for i in selected_indices]
        result.append({
            'x': False,
            'name': ch['name'],
            'unit': ch.get('unit', ''),
            'color': ch.get('color', '#000000'),
            'data': ch_out
        })
    
    overview_meta['overviewPoints'] = len(selected_indices)
    return result, overview_meta


# ===== Worker Class =====

class FileParserWorker:
    """File parsing worker using Redis Streams"""
    
    def __init__(self):
        """Initialize worker"""
        self.db = get_db()
        self.data_folder_path = get_data_folder_path()
        self.redis = get_redis_client()
        
        logger.info("FileParserWorker initialized")
        logger.info(f"Worker name: {settings.WORKER_NAME}")
        logger.info(f"Data folder: {self.data_folder_path}")
    
    def run(self):
        """Main worker loop - consume from Redis Streams"""
        logger.info("=" * 60)
        logger.info("File Parser Worker started")
        logger.info(f"Consumer group: {self.redis.PARSER_GROUP}")
        logger.info(f"Batch size: {settings.BATCH_SIZE}")
        logger.info(f"Block time: {settings.BLOCK_TIME_MS}ms")
        logger.info("=" * 60)
        
        # Health check
        if not self.redis.health_check():
            logger.error("Redis connection failed! Exiting...")
            return
        
        logger.info("Redis connection established")
        
        last_stats_log = time.time()
        
        while True:
            try:
                # Log queue stats periodically (every 60 seconds)
                if time.time() - last_stats_log > 60:
                    self._log_queue_stats()
                    last_stats_log = time.time()
                
                # Read messages from queue (blocking)
                messages = self.redis.read_messages(
                    consumer_name=settings.WORKER_NAME,
                    count=settings.BATCH_SIZE,
                    block_ms=settings.BLOCK_TIME_MS
                )
                
                if not messages:
                    logger.debug("No messages in queue, waiting...")
                    continue
                
                # Process messages
                for stream_name, message_list in messages:
                    for msg_id, data in message_list:
                        self._process_message(msg_id, data)
            
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(5)  # Brief pause before retry
        
        logger.info("File Parser Worker stopped")
    
    def _process_message(self, msg_id: bytes, data: dict):
        """
        Process a single message from the queue
        
        Args:
            msg_id: Redis message ID
            data: Message data containing file_id
        """
        # Decode data
        file_id = data[b'file_id'].decode('utf-8')
        msg_id_str = msg_id.decode('utf-8')
        
        logger.info(f"Processing message {msg_id_str} for file {file_id}")
        
        try:
            # Get file from database
            file_doc = self.db['files'].find_one({'_id': ObjectId(file_id)})
            
            if not file_doc:
                logger.error(f"File not found in database: {file_id}")
                self.redis.acknowledge(msg_id)
                return
            
            file_name = file_doc.get('name', 'unknown')
            logger.info(f"Parsing file: {file_name}")
            
            # Parse file
            json_dict = parse_file(self.db, file_doc, self.data_folder_path)
            
            # Determine total points from x-axis
            x_trace = next(d for d in json_dict if d['x'])
            total_points = len(x_trace['data'])
            
            # Setup paths
            local_folder = Path(file_doc["rawPath"]).parent
            file_stem = Path(file_doc["rawPath"]).stem
            output_dir = Path(self.data_folder_path) / local_folder
            output_dir.mkdir(parents=True, exist_ok=True)
            
            project_id = local_folder.parent.name if local_folder.parent.name else str(local_folder.parent)
            file_id_name = local_folder.name
            
            # Determine storage format based on size
            use_binary_format = total_points >= BINARY_FORMAT_THRESHOLD
            
            if use_binary_format:
                logger.info(f"Using binary format for large file: {total_points} points")
                
                # Save binary format
                binary_base_path = str(output_dir / file_stem)
                meta = save_as_binary_format(json_dict, binary_base_path)
                
                # Generate and save overview data for initial display
                overview_data, overview_meta = generate_overview_data(json_dict, target_points_per_channel=5000)
                overview_path = f"{local_folder}/{file_stem}_overview.json"
                overview_file_path = Path(self.data_folder_path) / overview_path
                
                # Save overview with metadata embedded
                overview_output = {
                    'meta': overview_meta,
                    'data': overview_data
                }
                with open(overview_file_path, 'w') as f:
                    json.dump(overview_output, f, ignore_nan=True)
                
                logger.info(f"Saved overview to {overview_path}")
                
                # Also save full JSON for backward compatibility (optional, can be removed later)
                json_path = f"{local_folder}/{file_stem}.json"
                json_file_path = Path(self.data_folder_path) / json_path
                
                with open(json_file_path, 'w') as f:
                    json.dump(json_dict, f, ignore_nan=True)
                
                # Extract x-axis info from metadata
                x_type = meta.get('xColumn', {}).get('type', 'numeric')
                x_format = meta.get('xColumn', {}).get('format', None)
                x_min = meta.get('xColumn', {}).get('min', 0)
                x_max = meta.get('xColumn', {}).get('max', total_points - 1)
                
                # Update database with binary format info
                update_data = {
                    'parsing': 'parsed',
                    'jsonPath': f'{project_id}/{file_id_name}/{file_stem}.json',
                    'binaryPath': f'{project_id}/{file_id_name}/{file_stem}.bin',
                    'metaPath': f'{project_id}/{file_id_name}/{file_stem}_meta.json',
                    'overviewPath': f'{project_id}/{file_id_name}/{file_stem}_overview.json',
                    'useBinaryFormat': True,
                    'totalPoints': total_points,
                    'xType': x_type,
                    'xMin': x_min,
                    'xMax': x_max,
                }
                if x_format:
                    update_data['xFormat'] = x_format
                
                self.db['files'].update_one(
                    {'_id': file_doc['_id']},
                    {'$set': update_data}
                )
                
                logger.info(f"Successfully processed large file: {file_name} ({total_points} points, xType={x_type})")
            
            else:
                logger.info(f"Using JSON format for small file: {total_points} points")
                
                # Save JSON (original behavior)
                json_path = f"{local_folder}/{file_stem}.json"
                json_file_path = Path(self.data_folder_path) / json_path
                
                with open(json_file_path, 'w') as f:
                    json.dump(json_dict, f, ignore_nan=True)
                
                logger.info(f"Saved JSON to {json_path}")
                
                # Update database
                self.db['files'].update_one(
                    {'_id': file_doc['_id']},
                    {'$set': {
                        'parsing': 'parsed',
                        'jsonPath': f'{project_id}/{file_id_name}/{file_stem}.json',
                        'useBinaryFormat': False,
                        'totalPoints': total_points
                    }}
                )
                
                logger.info(f"Successfully processed file: {file_name}")
            
            # Acknowledge success
            self.redis.acknowledge(msg_id)
            
        except Exception as e:
            logger.error(f"Failed to process file {file_id}: {e}", exc_info=True)
            
            # Update file status with error
            try:
                self.db['files'].update_one(
                    {'_id': ObjectId(file_id)},
                    {'$set': {'parsing': f'error: {str(e)}'}}
                )
                logger.info(f"Updated file status to error")
            except Exception as update_error:
                logger.error(f"Failed to update error status: {update_error}")
            
            # Acknowledge to prevent infinite retry
            self.redis.acknowledge(msg_id)
    
    def _log_queue_stats(self):
        """Log queue statistics"""
        try:
            queue_len = self.redis.get_queue_length()
            pending = self.redis.get_pending_count()
            logger.info(f"Queue stats - Total messages: {queue_len}, Pending ACK: {pending}")
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")


# ===== Entry Point =====

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    # Create and run worker
    worker = FileParserWorker()
    
    try:
        worker.run()
    except Exception as e:
        logger.critical(f"Worker crashed: {e}", exc_info=True)
        sys.exit(1)

