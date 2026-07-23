from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.memory import Memory, MemoryType
from app.models.user import User
from app.utils.logger import logger
import uuid


class LongTermMemory:
    """
    PostgreSQL-backed long-term user profile and preference memory.
    Stores user goals, skills, preferences, routines, and important facts.
    """

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                pass
        self.user_id = user_id

    async def store(
        self,
        content: str,
        category: str,
        title: Optional[str] = None,
        importance_score: float = 0.5,
        metadata: Optional[Dict] = None,
    ) -> Memory:
        memory = Memory(
            user_id=self.user_id,
            memory_type=MemoryType.LONG_TERM,
            category=category,
            title=title,
            content=content,
            importance_score=importance_score,
            metadata_=metadata or {},
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        logger.info("long_term_memory_stored", category=category, title=title)
        return memory

    async def retrieve(
        self,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[Memory]:
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == self.user_id,
                Memory.memory_type == MemoryType.LONG_TERM,
            )
            .order_by(Memory.importance_score.desc(), Memory.created_at.desc())
            .limit(limit)
        )
        if category:
            stmt = stmt.where(Memory.category == category)

        result = await self.db.execute(stmt)
        memories = result.scalars().all()

        # Update accessed_at
        for m in memories:
            m.accessed_at = datetime.utcnow()
        await self.db.commit()

        return memories

    async def get_user_profile(self) -> Dict[str, Any]:
        """Retrieve structured user profile from PostgreSQL."""
        stmt = select(User).where(User.id == self.user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        return user.profile if user and user.profile else {}

    async def update_user_profile(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Merge updates into the user's JSON profile field."""
        profile = await self.get_user_profile()
        profile.update(updates)
        await self.db.execute(
            update(User).where(User.id == self.user_id).values(profile=profile)
        )
        await self.db.commit()
        return profile

    async def get_profile_summary(self) -> str:
        """Return a concise text summary of the user profile for prompt injection."""
        profile = await self.get_user_profile()
        memories = await self.retrieve(limit=10)

        lines = ["=== User Profile ==="]
        if profile.get("name"):
            lines.append(f"Name: {profile['name']}")
        if profile.get("goals"):
            lines.append(f"Goals: {', '.join(profile['goals'])}")
        if profile.get("skills"):
            lines.append(f"Skills: {', '.join(profile['skills'])}")
        if profile.get("timezone"):
            lines.append(f"Timezone: {profile['timezone']}")

        if memories:
            lines.append("\n=== Key Facts ===")
            for m in memories[:5]:
                lines.append(f"- [{m.category}] {m.content}")

        return "\n".join(lines)

    async def delete(self, memory_id: str) -> bool:
        if isinstance(memory_id, str):
            try:
                memory_id = uuid.UUID(memory_id)
            except ValueError:
                pass
        stmt = select(Memory).where(
            Memory.id == memory_id,
            Memory.user_id == self.user_id,
        )
        result = await self.db.execute(stmt)
        memory = result.scalar_one_or_none()
        if memory:
            await self.db.delete(memory)
            await self.db.commit()
            return True
        return False
