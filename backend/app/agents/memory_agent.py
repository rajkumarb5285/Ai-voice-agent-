"""
Memory Agent Node
Retrieves all relevant memory context before agent processing.
Also handles storing new memories after response generation.
"""
import time
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger


async def memory_retrieval_node(state: AgentState, db=None) -> AgentState:
    """
    Pull short-term, long-term, semantic, and episodic context
    and inject into state for downstream agents.
    Fast-fail with 2s timeout per memory source to keep voice responses snappy.
    """
    import asyncio
    start = time.time()
    user_id = state["user_id"]
    conversation_id = state["conversation_id"]
    user_input = state["user_input"]

    logger.info("memory_retrieval_start", user_id=user_id)

    MEMORY_TIMEOUT = 2.0  # 2 second timeout per memory source

    short_term_ctx = ""
    long_term_ctx = ""
    semantic_ctx = ""
    episodic_ctx = ""

    async def _get_short_term():
        from app.memory.short_term import ShortTermMemory
        stm = ShortTermMemory(user_id, conversation_id)
        ctx = await stm.get_context_string(limit=10)
        await stm.add_message("user", user_input)
        return ctx

    async def _get_long_term():
        from app.memory.long_term import LongTermMemory
        ltm = LongTermMemory(db, user_id)
        return await ltm.get_profile_summary()

    async def _get_episodic():
        from app.memory.episodic import EpisodicMemory
        epm = EpisodicMemory(db, user_id)
        return await epm.get_timeline_summary(limit=5)

    async def _get_semantic():
        from app.memory.semantic import SemanticMemory
        sem = SemanticMemory(user_id)
        return await sem.search_as_context(user_input, n_results=3)

    # Run all memory retrievals concurrently with timeouts
    tasks = [
        asyncio.wait_for(_get_short_term(), timeout=MEMORY_TIMEOUT),
        asyncio.wait_for(_get_semantic(), timeout=MEMORY_TIMEOUT),
    ]
    if db:
        tasks.extend([
            asyncio.wait_for(_get_long_term(), timeout=MEMORY_TIMEOUT),
            asyncio.wait_for(_get_episodic(), timeout=MEMORY_TIMEOUT)
        ])

    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results in the order they were added
    try:
        if not isinstance(results[0], Exception):
            short_term_ctx = results[0]
        else:
            logger.warning("short_term_memory_timeout_or_error", error=str(results[0]))
            
        if not isinstance(results[1], Exception):
            semantic_ctx = results[1]
        else:
            logger.warning("semantic_memory_timeout_or_error", error=str(results[1]))
            
        if db:
            if not isinstance(results[2], Exception):
                long_term_ctx = results[2]
            else:
                logger.warning("long_term_memory_timeout_or_error", error=str(results[2]))
                
            if not isinstance(results[3], Exception):
                episodic_ctx = results[3]
            else:
                logger.warning("episodic_memory_timeout_or_error", error=str(results[3]))
                
    except Exception as e:
        logger.error("memory_retrieval_concurrent_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Memory Agent",
        "action": "Retrieved contextual memories",
        "status": "completed",
        "output_summary": f"Short-term: {len(short_term_ctx)} chars | Long-term: {len(long_term_ctx)} chars | Semantic: {len(semantic_ctx)} chars",
        "duration_ms": latency,
    }

    return {
        **state,
        "short_term_context": short_term_ctx,
        "long_term_context": long_term_ctx,
        "semantic_context": semantic_ctx,
        "episodic_context": episodic_ctx,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }


async def memory_update_node(state: AgentState, db=None) -> AgentState:
    """
    After response is generated, persist important information to memory.
    Extracts memories from the conversation automatically.
    """
    start = time.time()
    user_id = state["user_id"]
    conversation_id = state["conversation_id"]
    final_response = state.get("final_response", "")
    user_input = state["user_input"]

    # Store assistant response in short-term memory
    try:
        from app.memory.short_term import ShortTermMemory
        stm = ShortTermMemory(user_id, conversation_id)
        await stm.add_message("assistant", final_response, {"agent": state.get("intent")})
    except Exception as e:
        logger.warning("short_term_memory_update_error", error=str(e))

    # Extract and store any explicit memories requested
    memories_to_store = state.get("memories_to_store", [])
    if memories_to_store and db:
        try:
            from app.memory.long_term import LongTermMemory
            from app.memory.semantic import SemanticMemory
            ltm = LongTermMemory(db, user_id)
            sem = SemanticMemory(user_id)

            for mem in memories_to_store:
                await ltm.store(
                    content=mem.get("content", ""),
                    category=mem.get("category", "general"),
                    title=mem.get("title"),
                    importance_score=mem.get("importance_score", 0.6),
                )
                await sem.store(
                    content=mem.get("content", ""),
                    metadata={"category": mem.get("category", "general"), "source": "agent"},
                )
        except Exception as e:
            logger.warning("memory_store_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Memory Agent",
        "action": f"Stored {len(memories_to_store)} new memories",
        "status": "completed",
        "duration_ms": latency,
    }

    return {
        **state,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }
