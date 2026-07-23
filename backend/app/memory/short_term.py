import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.redis_client import get_redis
from app.utils.logger import logger


class ShortTermMemory:
    """
    Redis-based in-session memory.
    Stores the last N messages and session state per user/conversation.
    TTL: 24 hours by default (refreshed on each interaction).
    """

    SESSION_TTL = 86400  # 24 hours
    MAX_MESSAGES = 50

    def __init__(self, user_id: str, conversation_id: str):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.session_key = f"session:{user_id}:{conversation_id}"
        self.messages_key = f"messages:{user_id}:{conversation_id}"
        self.state_key = f"state:{user_id}:{conversation_id}"

    async def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        redis = await get_redis()
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        await redis.rpush(self.messages_key, json.dumps(message))
        # Keep only last MAX_MESSAGES
        await redis.ltrim(self.messages_key, -self.MAX_MESSAGES, -1)
        await redis.expire(self.messages_key, self.SESSION_TTL)

    async def get_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        redis = await get_redis()
        raw = await redis.lrange(self.messages_key, -limit, -1)
        return [json.loads(m) for m in raw]

    async def get_context_string(self, limit: int = 10) -> str:
        messages = await self.get_messages(limit)
        lines = []
        for m in messages:
            role = m["role"].upper()
            lines.append(f"{role}: {m['content']}")
        return "\n".join(lines)

    async def set_state(self, key: str, value: Any):
        redis = await get_redis()
        state = await self.get_state()
        state[key] = value
        await redis.set(self.state_key, json.dumps(state), ex=self.SESSION_TTL)

    async def get_state(self) -> Dict[str, Any]:
        redis = await get_redis()
        raw = await redis.get(self.state_key)
        return json.loads(raw) if raw else {}

    async def clear(self):
        redis = await get_redis()
        await redis.delete(self.messages_key, self.state_key, self.session_key)

    async def set_user_intent(self, intent: str):
        await self.set_state("last_intent", intent)

    async def get_user_intent(self) -> Optional[str]:
        state = await self.get_state()
        return state.get("last_intent")

    async def set_active_agents(self, agents: List[str]):
        await self.set_state("active_agents", agents)

    async def get_active_agents(self) -> List[str]:
        state = await self.get_state()
        return state.get("active_agents", [])
