from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.memory import Memory, MemoryType
from app.utils.logger import logger


class EpisodicMemory:
    """
    PostgreSQL-backed episodic memory.
    Records important events and experiences — what happened, when, and why it mattered.
    Examples: "User completed Python course", "User got a job interview", "Big presentation day"
    """

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        import uuid
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                pass
        self.user_id = user_id

    async def record_event(
        self,
        event_description: str,
        category: str = "general",
        title: Optional[str] = None,
        importance_score: float = 0.6,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        memory = Memory(
            user_id=self.user_id,
            memory_type=MemoryType.EPISODIC,
            category=category,
            title=title or event_description[:100],
            content=event_description,
            importance_score=importance_score,
            metadata_={
                "recorded_at": datetime.utcnow().isoformat(),
                **(metadata or {}),
            },
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        logger.info("episodic_event_recorded", title=memory.title, category=category)
        return memory

    async def get_recent_events(self, limit: int = 10) -> List[Memory]:
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == self.user_id,
                Memory.memory_type == MemoryType.EPISODIC,
            )
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_events_by_category(self, category: str, limit: int = 10) -> List[Memory]:
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == self.user_id,
                Memory.memory_type == MemoryType.EPISODIC,
                Memory.category == category,
            )
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_timeline_summary(self, limit: int = 5) -> str:
        """Returns a text timeline for prompt context."""
        events = await self.get_recent_events(limit)
        if not events:
            return ""
        lines = ["=== Recent Events ==="]
        for e in events:
            date_str = e.created_at.strftime("%b %d, %Y")
            lines.append(f"- {date_str}: {e.title}")
        return "\n".join(lines)
