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


@app.route('/read', methods=['POST'])
def read():
    request = flask.request
    body = json.loads(request.data)
    cloudId = body['cloudId']
    filename = body['filename']
    cloud = LocalCloud(cloudId)
    return cloud.read(filename)

@app.route('/write', methods=['POST'])
def write():
    request = flask.request
    body = json.loads(request.data)
    cloudId = body['cloudId']
    data2write = body['data2write']
    filename = body['filename']
    cloud = LocalCloud(cloudId)
    cloud.write(data2write, filename)
    return 'Write finished!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
