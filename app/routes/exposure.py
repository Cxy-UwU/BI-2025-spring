import json
from datetime import datetime

from flask import Blueprint, request
import subprocess

exposure_bp = Blueprint('exposure', __name__)

process = None


@exposure_bp.route('/start_exposure', methods=['GET'])
def start_exposure():
    speed = request.args.get('speed', default=1, type=int)
    global process
    if process and process.poll() is None:
        return "Already running", 400
    process = subprocess.Popen(["python", "data_transfer.py", str(speed)])
    return "Started", 200


@exposure_bp.route('/stop_exposure', methods=['GET'])
def stop_exposure():
    global process
    if process:
        process.terminate()
        process = None
    return "Stopped", 200


@exposure_bp.route('/get_exposure_time', methods=['GET'])
def get_exposure_time():
    config_path = 'input_config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            ts = data.get('current_time')
            if ts is not None:
                time_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                return time_str, 200
            else:
                return "尚无数据", 200
    except FileNotFoundError:
        return "尚无数据", 200
