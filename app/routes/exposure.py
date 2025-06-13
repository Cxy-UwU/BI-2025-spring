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
