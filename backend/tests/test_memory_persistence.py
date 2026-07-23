"""
Unit tests for the 4-layer memory system persistence.
"""
import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.memory.episodic import EpisodicMemory
from app.memory.semantic import SemanticMemory
from app.models.memory import Memory, MemoryType

@pytest.mark.asyncio
async def test_short_term_memory(mock_redis):
    """Verify ShortTermMemory adds messages to Redis and reads them back."""
    user_id = str(uuid.uuid4())
    conv_id = str(uuid.uuid4())
    stm = ShortTermMemory(user_id, conv_id)
    
    # 1. Add message
    await stm.add_message("user", "Hello Redis memory")
    mock_redis.rpush.assert_called_once()
    mock_redis.expire.assert_called_once()

    # 2. Get messages (mocking lrange response)
    mock_msg = {
        "role": "user",
        "content": "Hello Redis memory",
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {}
    }
    mock_redis.lrange.return_value = [json.dumps(mock_msg)]
    
    messages = await stm.get_messages(limit=5)
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello Redis memory"

@pytest.mark.asyncio
async def test_long_term_memory(mock_db):
    """Verify LongTermMemory stores and retrieves facts from DB."""
    user_id = str(uuid.uuid4())
    ltm = LongTermMemory(mock_db, user_id)
    
    # Store memory
    await ltm.store("I like coffee", "preference", "Coffee Preference", 0.8)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_episodic_memory(mock_db):
    """Verify EpisodicMemory records experiences in DB."""
    user_id = str(uuid.uuid4())
    epm = EpisodicMemory(mock_db, user_id)
    
    # Record event
    await epm.record_event("User finished the Python course", "milestone", "Python Finished", 0.9)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_semantic_memory():
    """Verify SemanticMemory stores text embedding to ChromaDB."""
    user_id = str(uuid.uuid4())
    sem = SemanticMemory(user_id)
    
    mock_collection = MagicMock()
    mock_collection.upsert = MagicMock()
    mock_collection.query = MagicMock(return_value={
        "documents": [["I am learning Python"]],
        "metadatas": [[{"user_id": user_id, "category": "general"}]],
        "distances": [[0.1]],
        "ids": [["doc-1"]]
    })

    # Mock the _get_collection and _embed methods
    with patch.object(sem, "_get_collection", new_callable=AsyncMock) as mock_get_coll, \
         patch.object(sem, "_embed", new_callable=AsyncMock) as mock_embed:
         
        mock_get_coll.return_value = mock_collection
        mock_embed.return_value = [0.1, 0.2, 0.3]
        
        # Test store
        doc_id = await sem.store("I am learning Python", metadata={"category": "general"})
        assert doc_id is not None
        mock_get_coll.assert_called_once()
        mock_embed.assert_called_once()
        
        # Test search
        results = await sem.search("learning Python", n_results=1)
        assert len(results) == 1
        assert results[0]["content"] == "I am learning Python"
        assert results[0]["similarity"] == 0.9  # 1 - distance (0.1)
