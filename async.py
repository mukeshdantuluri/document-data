from fastapi import FastAPI, HTTPException
import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel
import random

app = FastAPI(title="Background Task Manager", version="1.0.0")

class TaskStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskInfo(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None

# In-memory storage for task status (use Redis/DB in production)
tasks: Dict[str, TaskInfo] = {}

async def simulate_background_work(task_id: str, duration: int = 10):
    """
    Simulate some background work that takes time to complete.
    This could be file processing, data analysis, API calls, etc.
    """
    try:
        # Update status to running
        tasks[task_id].status = TaskStatus.RUNNING
        
        # Simulate work with multiple steps
        for i in range(duration):
            await asyncio.sleep(1)  # Simulate 1 second of work
            print(f"Task {task_id}: Step {i+1}/{duration}")
            
            # Simulate potential failure (10% chance)
            if random.random() < 0.1:
                raise Exception(f"Random failure at step {i+1}")
        
        # Mark as completed
        tasks[task_id].status = TaskStatus.COMPLETED
        tasks[task_id].completed_at = datetime.now()
        tasks[task_id].result = f"Task completed successfully after {duration} steps"
        
    except Exception as e:
        # Mark as failed
        tasks[task_id].status = TaskStatus.FAILED
        tasks[task_id].completed_at = datetime.now()
        tasks[task_id].error = str(e)
        print(f"Task {task_id} failed: {e}")

@app.post("/start-task")
async def start_background_task(duration: int = 10):
    """
    Start a new background task.
    Returns the task_id to track progress.
    """
    if duration < 1 or duration > 60:
        raise HTTPException(status_code=400, detail="Duration must be between 1 and 60 seconds")
    
    task_id = str(uuid.uuid4())
    
    # Create task info
    task_info = TaskInfo(
        task_id=task_id,
        status=TaskStatus.RUNNING,
        created_at=datetime.now()
    )
    tasks[task_id] = task_info
    
    # Start the background task
    asyncio.create_task(simulate_background_work(task_id, duration))
    
    return {
        "message": "Task started successfully",
        "task_id": task_id,
        "estimated_duration": f"{duration} seconds"
    }

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the current status of a background task.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = tasks[task_id]
    
    response = {
        "task_id": task_id,
        "status": task_info.status,
        "created_at": task_info.created_at.isoformat(),
    }
    
    if task_info.completed_at:
        response["completed_at"] = task_info.completed_at.isoformat()
        
        # Calculate duration
        duration = (task_info.completed_at - task_info.created_at).total_seconds()
        response["duration_seconds"] = duration
    
    if task_info.status == TaskStatus.COMPLETED and task_info.result:
        response["result"] = task_info.result
    elif task_info.status == TaskStatus.FAILED and task_info.error:
        response["error"] = task_info.error
    
    return response

@app.get("/tasks")
async def list_all_tasks():
    """
    List all tasks and their current status.
    """
    if not tasks:
        return {"message": "No tasks found", "tasks": []}
    
    task_list = []
    for task_id, task_info in tasks.items():
        task_data = {
            "task_id": task_id,
            "status": task_info.status,
            "created_at": task_info.created_at.isoformat(),
        }
        
        if task_info.completed_at:
            task_data["completed_at"] = task_info.completed_at.isoformat()
        
        task_list.append(task_data)
    
    return {"tasks": task_list, "total_tasks": len(task_list)}

@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a task from memory (cleanup).
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del tasks[task_id]
    return {"message": f"Task {task_id} deleted successfully"}

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "FastAPI Background Task Manager",
        "endpoints": {
            "start_task": "POST /start-task?duration=10",
            "check_status": "GET /task-status/{task_id}",
            "list_tasks": "GET /tasks",
            "delete_task": "DELETE /task/{task_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
