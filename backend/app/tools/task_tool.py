import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.task import Task, TaskStatus, TaskPriority
from app.utils.logger import logger

class TaskTool:
    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    async def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            stmt = select(Task).where(Task.user_id == self.user_id)
            if status:
                stmt = stmt.where(Task.status == TaskStatus(status))
            stmt = stmt.order_by(Task.created_at.desc())
            result = await self.db.execute(stmt)
            tasks = result.scalars().all()
            return [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "category": t.category,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "steps": t.steps,
                }
                for t in tasks
            ]
        except Exception as e:
            logger.error("task_list_failed", user_id=self.user_id, error=str(e))
            return [{"error": f"Failed to retrieve tasks: {str(e)}"}]

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        due_date: Optional[datetime] = None,
        steps: Optional[list] = None,
    ) -> Dict[str, Any]:
        try:
            # Validate priority
            p_val = priority.lower()
            if p_val not in ["low", "medium", "high", "urgent"]:
                p_val = "medium"

            task = Task(
                user_id=self.user_id,
                title=title,
                description=description,
                status=TaskStatus.PENDING,
                priority=TaskPriority(p_val),
                category=category,
                due_date=due_date,
                steps=steps or [],
                is_ai_generated=True,
            )
            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)
            logger.info("task_created_via_tool", task_id=task.id, title=title)
            return {
                "status": "success",
                "message": f"Task '{title}' has been successfully created.",
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "priority": task.priority.value,
                    "status": task.status.value,
                }
            }
        except Exception as e:
            logger.error("task_create_failed", user_id=self.user_id, error=str(e))
            return {"status": "error", "message": f"Failed to create task: {str(e)}"}
