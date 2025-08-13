import os
import pymongo
from bson.json_util import dumps

CHANGE_STREAM_DB = ''
client = pymongo.MongoClient(CHANGE_STREAM_DB)
change_stream_1 = client.test_db.username.watch()
change_stream_2 = client.changestream.collection.watch()
for change in change_stream_1:
    print(dumps(change))
    print('') # for readability only

for change in change_stream_2:
    print(dumps(change))
    print('')