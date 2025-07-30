##############################################
asyncio
############################################
import uuid
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Shared dictionary for task status
task_status = {}
task_lock = asyncio.Lock()


class TaskInput(BaseModel):
    a: int
    b: int


@app.post("/start-task")
async def start_task(input_data: TaskInput):
    task_id = str(uuid.uuid4())

    # Create background task
    async def long_running_task(task_id: str, a: int, b: int):
        async with task_lock:
            task_status[task_id] = "RUNNING"
        try:
            await asyncio.sleep(5)  # Simulate a delay
            result = a + b
            async with task_lock:
                task_status[task_id] = f"COMPLETED: {result}"
        except Exception as e:
            async with task_lock:
                task_status[task_id] = f"FAILED: {str(e)}"

    async with task_lock:
        task_status[task_id] = "PENDING"

    # Schedule the task to run in the background
    asyncio.create_task(long_running_task(task_id, input_data.a, input_data.b))

    return {"task_id": task_id}


@app.get("/task-status/{task_id}")
async def get_status(task_id: str):
    async with task_lock:
        status = task_status.get(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Task ID not found")
    return {"task_id": task_id, "status": status}




##############################################
background
############################################
import uuid
import time
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict
from threading import Lock

app = FastAPI()

# Thread-safe shared dict to store task statuses
task_status: Dict[str, str] = {}
task_lock = Lock()


class TaskInput(BaseModel):
    a: int
    b: int


def long_running_task(task_id: str, a: int, b: int):
    with task_lock:
        task_status[task_id] = "RUNNING"
    try:
        time.sleep(5)  # simulate long processing
        result = a + b
        with task_lock:
            task_status[task_id] = f"COMPLETED: {result}"
    except Exception as e:
        with task_lock:
            task_status[task_id] = f"FAILED: {str(e)}"


@app.post("/start-task")
def start_task(input_data: TaskInput, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())

    with task_lock:
        task_status[task_id] = "PENDING"

    background_tasks.add_task(long_running_task, task_id, input_data.a, input_data.b)

    return {"task_id": task_id}


@app.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    with task_lock:
        status = task_status.get(task_id)

    if status is None:
        raise HTTPException(status_code=404, detail="Task ID not found")

    return {"task_id": task_id, "status": status}


