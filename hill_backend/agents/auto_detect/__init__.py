"""Auto-Detection Package"""
from .coordinator import run_multi_agent_detection, AgentCoordinator
from .tools import get_basic_statistics, PlotViewer

# Main entry point
async def run_auto_detection(file_id: str, description: str = "Auto-detection requested", notification_callback=None):
    """
    Main entry point for running auto-detection using multi-agent system
    
    This is a re-export that maintains backward compatibility
    """
    import os
    import json
    import pandas as pd
    from bson.objectid import ObjectId
    from dotenv import load_dotenv
    from pathlib import Path

    load_dotenv(Path(__file__).parent.parent.parent / '.env')
    
    try:
        # Import database functions
        from database import get_db, get_data_folder_path
        
        # Load file data and project information
        db = get_db()
        data_folder_path = get_data_folder_path()
        
        # Get file info
        file_info = db['files'].find_one({'_id': ObjectId(file_id)})
        if not file_info:
            if notification_callback:
                await notification_callback(file_id, {
                    'type': 'detection_failed',
                    'data': {'message': 'File not found'}
                })
            return {'success': False, 'error': 'File not found'}
        
        if not file_info.get('jsonPath'):
            if notification_callback:
                await notification_callback(file_id, {
                    'type': 'detection_failed', 
                    'data': {'message': 'No data file available for this file'}
                })
            return {'success': False, 'error': 'No data file available'}
        
        # Load the time series data
        json_path = file_info['jsonPath']
        file_path = f'{data_folder_path}/{json_path}'
        
        with open(file_path, 'r') as f:
            data_json = json.load(f)
        
        # Convert to DataFrame for analysis
        if isinstance(data_json, list):
            df_data = {}
            x_axis_data = None
            x_axis_name = None
            
            for channel in data_json:
                if isinstance(channel, dict) and 'name' in channel and 'data' in channel:
                    channel_name = channel['name']
                    channel_data = channel['data']
                    
                    if channel.get('x', False):
                        x_axis_data = channel_data
                        x_axis_name = channel_name
                    else:
                        df_data[channel_name] = channel_data
            
            if x_axis_data and len(df_data) > 0:
                max_len = max(len(values) for values in df_data.values())
                for channel_name, values in df_data.items():
                    if len(values) < max_len:
                        df_data[channel_name] = values + [None] * (max_len - len(values))
                    elif len(values) > max_len:
                        df_data[channel_name] = values[:max_len]
                
                df = pd.DataFrame(df_data)
            else:
                df = pd.DataFrame(df_data)
        else:
            df = pd.DataFrame(data_json)
        
        # Get project info
        folder_info = db['folders'].find_one({'fileList': file_id})
        project_info = None
        if folder_info:
            project_info = db['projects'].find_one({'_id': ObjectId(folder_info['project']['id'])})
        
        # Create event patterns dictionary from project classes
        event_patterns = {}
        if project_info and 'classes' in project_info:
            for cls in project_info['classes']:
                if cls.get('description'):
                    event_patterns[cls['name']] = cls['description']
        
        # Run the multi-agent detection system
        result = await run_multi_agent_detection(
            file_id=file_id,
            df=df,
            project_info=project_info,
            event_patterns=event_patterns,
            notification_callback=notification_callback
        )
        
        return result
        
    except Exception as e:
        if notification_callback:
            await notification_callback(file_id, {
                'type': 'detection_failed',
                'data': {'message': f'Auto-detection failed: {str(e)}'}
            })
        
        return {
            'success': False,
            'error': str(e)
        }


__all__ = [
    'run_multi_agent_detection',
    'run_auto_detection',
    'AgentCoordinator', 
    'get_basic_statistics',
    'PlotViewer'
]
