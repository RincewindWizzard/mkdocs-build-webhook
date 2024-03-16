from flask import Flask, request,jsonify
from loguru import logger
app = Flask(__name__)


@app.route("/", methods=['GET'])
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/", methods=['POST'])
def hello_world():
    if request.method == 'POST':
        json_data = request.get_json()
        logger.debug(f'{json_data}')
    return jsonify({'received_data': json_data}), 200
