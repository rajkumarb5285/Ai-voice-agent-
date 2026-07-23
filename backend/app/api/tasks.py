from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.schemas import TaskCreate, TaskUpdate, TaskResponse
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(desc(Task.created_at))
        .limit(limit)
    )
    if status:
        stmt = stmt.where(Task.status == TaskStatus(status))
    if priority:
        stmt = stmt.where(Task.priority == TaskPriority(priority))
    if category:
        stmt = stmt.where(Task.category == category)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = Task(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        priority=TaskPriority(data.priority),
        category=data.category,
        due_date=data.due_date,
        steps=data.steps or [],
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    if isinstance(task_id, str):
        try:
            task_id = uuid.UUID(task_id)
        except ValueError:
            pass
    stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = data.model_dump(exclude_none=True)
    if "status" in updates:
        updates["status"] = TaskStatus(updates["status"])
        if updates["status"] == TaskStatus.COMPLETED:
            updates["completed_at"] = datetime.utcnow()
    if "priority" in updates:
        updates["priority"] = TaskPriority(updates["priority"])

    for key, val in updates.items():
        setattr(task, key, val)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    if isinstance(task_id, str):
        try:
            task_id = uuid.UUID(task_id)
        except ValueError:
            pass
    stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return {"status": "deleted", "id": task_id}


@router.get("/summary")
async def get_task_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Quick stats for the task dashboard."""
    from sqlalchemy import func
    stmt = (
        select(Task.status, func.count(Task.id).label("count"))
        .where(Task.user_id == current_user.id)
        .group_by(Task.status)
    )
    result = await db.execute(stmt)
    rows = result.all()
    summary = {row.status.value: row.count for row in rows}
    return {
        "total": sum(summary.values()),
        "pending": summary.get("pending", 0),
        "in_progress": summary.get("in_progress", 0),
        "completed": summary.get("completed", 0),
        "cancelled": summary.get("cancelled", 0),
    }
