from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import uuid
import time
import threading

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=4)

# Dictionary to store task statuses and results
tasks = {}
task_lock = threading.Lock()

def long_running_task(task_id, seconds):
    try:
        update_task(task_id, "in_progress")
        time.sleep(seconds)  # Simulate work
        result = f"Task {task_id} completed after {seconds} seconds"
        update_task(task_id, "completed", result=result)
    except Exception as e:
        update_task(task_id, "failed", result=str(e))

def update_task(task_id, status, result=None):
    with task_lock:
        tasks[task_id]['status'] = status
        if result is not None:
            tasks[task_id]['result'] = result

@app.route("/submit-job", methods=["POST"])
def submit_job():
    data = request.json
    seconds = data.get("duration", 5)
    task_id = str(uuid.uuid4())
    
    with task_lock:
        tasks[task_id] = {"status": "pending", "result": None}
    
    executor.submit(long_running_task, task_id, seconds)
    return jsonify({"task_id": task_id}), 202

@app.route("/task-status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    with task_lock:
        task = tasks.get(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"task_id": task_id, "status": task["status"], "result": task["result"]})

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
