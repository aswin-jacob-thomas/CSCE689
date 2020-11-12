from localCloud import LocalCloud
from flask import Flask
import flask
import json

app = Flask(__name__)

@app.route('/', methods=['POST'])
def init():
    request = flask.request
    cloudId = json.loads(request.data)['cloudId']
    cloud = LocalCloud(cloudId)
    cloud.initialize()
    print("Initialization of cloud ", cloudId, 'complete')
    return 'Success'

@app.route('/read', method=['POST'])
def read():
    request = flask.request
    cloudId = json.loads(request.data)['cloudId']
    cloud = LocalCloud(cloudId)
    cloud.read()
    return 'This is read'

@app.route('/write')
def write():
    return 'This is write'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
