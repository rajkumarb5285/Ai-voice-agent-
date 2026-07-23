from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.memory import Memory, MemoryType
from app.models.schemas import MemoryCreate, MemoryResponse, MemorySearchRequest
from app.memory.long_term import LongTermMemory
from app.memory.semantic import SemanticMemory
from app.utils.logger import logger

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/", response_model=List[MemoryResponse])
async def list_memories(
    memory_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all stored memories for the current user."""
    stmt = (
        select(Memory)
        .where(Memory.user_id == current_user.id)
        .order_by(desc(Memory.importance_score), desc(Memory.created_at))
        .limit(limit)
    )
    if memory_type:
        stmt = stmt.where(Memory.memory_type == MemoryType(memory_type))
    if category:
        stmt = stmt.where(Memory.category == category)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=MemoryResponse, status_code=201)
async def create_memory(
    data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually store a memory (user can explicitly tell agent to remember something)."""
    ltm = LongTermMemory(db, str(current_user.id))
    memory = await ltm.store(
        content=data.content,
        category=data.category or "general",
        title=data.title,
        importance_score=data.importance_score,
        metadata=data.metadata_ or {},
    )

    # Also embed in vector store
    try:
        sem = SemanticMemory(str(current_user.id))
        chroma_id = await sem.store(
            content=data.content,
            document_id=str(memory.id),
            metadata={"category": data.category or "general"},
        )
        memory.chroma_id = chroma_id
        await db.commit()
    except Exception as e:
        logger.warning("semantic_store_failed", error=str(e))

    return memory


@router.post("/search")
async def search_memories(
    request: MemorySearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Semantic search over user's memories."""
    sem = SemanticMemory(str(current_user.id))
    results = await sem.search(
        query=request.query,
        n_results=request.n_results,
    )
    return {"results": results, "query": request.query}


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ltm = LongTermMemory(db, str(current_user.id))
    deleted = await ltm.delete(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Also remove from vector store
    try:
        sem = SemanticMemory(str(current_user.id))
        await sem.delete(memory_id)
    except Exception:
        pass

    return {"status": "deleted", "id": memory_id}


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's stored profile (goals, skills, preferences)."""
    ltm = LongTermMemory(db, str(current_user.id))
    profile = await ltm.get_user_profile()
    summary = await ltm.get_profile_summary()
    return {"profile": profile, "summary": summary}


@router.patch("/profile")
async def update_profile(
    updates: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile fields (name, goals, skills, timezone, etc.)."""
    ltm = LongTermMemory(db, str(current_user.id))
    updated = await ltm.update_user_profile(updates)
    return {"profile": updated}
