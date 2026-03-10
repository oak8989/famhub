from fastapi import APIRouter, Depends
from typing import List
from models.schemas import Task
from auth import get_current_user
from database import db
from routers.websocket import notify_family
from routers.utilities import send_push_to_family

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[Task])
async def get_tasks(user: dict = Depends(get_current_user)):
    tasks = await db.tasks.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for t in tasks:
        t.pop("family_id", None)
    return tasks


@router.post("", response_model=Task)
async def create_task(task: Task, user: dict = Depends(get_current_user)):
    task_doc = task.model_dump()
    task_doc["family_id"] = user["family_id"]
    task_doc["created_by"] = user["user_id"]
    if task.assigned_to:
        assigned_user = await db.users.find_one({"id": task.assigned_to}, {"_id": 0})
        if assigned_user:
            task_doc["assigned_to_name"] = assigned_user.get("name")
    await db.tasks.insert_one(task_doc)
    del task_doc["_id"]
    del task_doc["family_id"]
    await notify_family(user["family_id"], "update", "tasks")
    name = task_doc.get("assigned_to_name", "someone")
    await send_push_to_family(user["family_id"], "New Task", f"'{task_doc['title']}' assigned to {name}", "/tasks")
    return task_doc


@router.put("/{task_id}")
async def update_task(task_id: str, task: Task, user: dict = Depends(get_current_user)):
    task_doc = task.model_dump()
    if task.assigned_to:
        assigned_user = await db.users.find_one({"id": task.assigned_to}, {"_id": 0})
        if assigned_user:
            task_doc["assigned_to_name"] = assigned_user.get("name")
    await db.tasks.update_one({"id": task_id, "family_id": user["family_id"]}, {"$set": task_doc})
    await notify_family(user["family_id"], "update", "tasks")
    return task_doc


@router.delete("/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    await db.tasks.delete_one({"id": task_id, "family_id": user["family_id"]})
    await notify_family(user["family_id"], "update", "tasks")
    return {"message": "Task deleted"}
