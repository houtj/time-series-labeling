from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
import pymongo
from bson.json_util import dumps


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')

CHANGE_STREAM_DB=""
client = pymongo.MongoClient(CHANGE_STREAM_DB)
change_stream = client.test_db.watch()

@socketio.on('connect')
def handle_message(data):
    print('init')
    try:
        for change in change_stream:
            c = dumps(change)
            print(c)
            emit('database', c)
    except:
        print('error')
        return

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    emit('my response', {'response':'ok'}, callback=lambda x: print(x))


if __name__ == '__main__':
    socketio.run(app, port=8000)