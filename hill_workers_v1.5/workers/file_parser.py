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
import simplejson as json
import pandas as pd
from bson.objectid import ObjectId

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from database import get_db, get_data_folder_path
from redis_client import get_redis_client


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
    
    # Convert to time if needed
    if templateInfo['x']['isTime'] == True:
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
        'unit': templateInfo['x']['unit'],
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
            
            # Save JSON
            local_folder = Path(file_doc["rawPath"]).parent
            file_stem = Path(file_doc["rawPath"]).stem
            json_path = f"{local_folder}/{file_stem}.json"
            
            json_file_path = Path(self.data_folder_path) / json_path
            json_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(json_file_path, 'w') as f:
                json.dump(json_dict, f, ignore_nan=True)
            
            logger.info(f"Saved JSON to {json_path}")
            
            # Update database
            project_id = local_folder.parent.name
            file_id_name = local_folder.name
            json_name = f"{file_stem}.json"
            
            self.db['files'].update_one(
                {'_id': file_doc['_id']},
                {'$set': {
                    'parsing': 'parsed',
                    'jsonPath': f'{project_id}/{file_id_name}/{json_name}'
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

