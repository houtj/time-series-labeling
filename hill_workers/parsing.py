import simplejson as json
import os
from pathlib import Path
import pymongo
import pandas as pd
import time
import re
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CHANGE_STREAM_DB = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/")
client = pymongo.MongoClient(CHANGE_STREAM_DB)
db = client['hill_ts']
data_folder_path = os.getenv("DATA_FOLDER_PATH", './data_folder')

def parse_file(db, f):
    json_dict = []
    print(str(f['_id']))
    folderInfo = db['folders'].find_one({'fileList': str(f['_id'])})
    assert folderInfo is not None
    templateId = folderInfo['template']['id']
    templateInfo = db['templates'].find_one({'_id': ObjectId(templateId)})
    assert templateInfo is not None
    local_path = f'{data_folder_path}/{f["rawPath"]}'
    if templateInfo['fileType'] == '.xlsx':
        sheet_name = templateInfo['sheetName']
        try:
            sheet_name = int(sheet_name)
        except:
            pass
        try:
            df = pd.read_excel(local_path, sheet_name= sheet_name, engine='openpyxl', header=templateInfo['headRow'])
            df = df.loc[templateInfo['skipRow']:, :]
        except:
            raise Exception('cannot open file')
    if templateInfo['fileType'] == '.xls':
        sheet_name = templateInfo['sheetName']
        try:
            sheet_name = int(sheet_name)
        except:
            pass
        try:
            df = pd.read_excel(local_path, sheet_name=sheet_name, engine='xlrd', header=templateInfo['headRow'])
            df = df.loc[templateInfo['skipRow']:, :]
        except:
            raise Exception('cannot open file')
    if templateInfo['fileType'] == '.csv':
        try:
            df = pd.read_csv(local_path, header=templateInfo['headRow'])
            df = df.loc[templateInfo['skipRow']:, :]
        except:
            raise Exception('cannot open file')
    columnNames = df.columns.values.tolist()
    x_regex = templateInfo['x']['regex']
    if 'col:' in x_regex:
        x_regex = x_regex.replace('col:', '')
        x_regex = x_regex.strip()
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
            print(columnNames)
            raise Exception(f'x axies not found for regex {x_regex}')
        x = df[c]
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
    for channel in templateInfo['channels']:
        channel_data = get_channel(channel, df)
        if channel_data is None:
            continue
        json_dict.append({
            'x':False,
            'name': channel['channelName'],
            'unit': channel['unit'],
            'color': channel['color'],
            'data': channel_data
        })
    return json_dict

def get_channel(channel, df):
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
            # if re.match(channel_regex, c):
            #     break
            if channel_regex==c:
                break
        else:
            if channel['mandatory'] == False:
                return None
            else:
                raise Exception(f'Channel {channel["channelName"]} not found')
        channel_data = df[c].astype(float)
    channel_data = channel_data.values.tolist()
    return channel_data

while True:
    files_to_be_parsed = db['files'].find({'parsing': 'parsing start'})
    for f in list(files_to_be_parsed):
        try:
            local_folder = Path(f["rawPath"]).parent
            file_stem = Path(f["rawPath"]).stem
            file_id = local_folder.name
            project_id = local_folder.parent.name

            json_name = Path(f['rawPath']).stem+'.json'
            json_dict = parse_file(db, f)

            with open(f"{data_folder_path}/{str(local_folder)}/{file_stem}.json", 'w') as json_file:
                json.dump(json_dict, json_file, ignore_nan=True)
            db['files'].update_one({'_id': f['_id']}, {'$set': {'parsing': 'parsed', 'jsonPath': f'{project_id}/{file_id}/{json_name}'}})
            print('done')
        except Exception as err:
            raise
            db['files'].update_one({'_id': f['_id']}, {'$set': {'parsing': f'error {str(err)}'}})
            print('failed')
    time.sleep(30)
        
        
    