"""
Coding Agent Node
Generate, debug, review, and explain code across all major languages.
"""
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

CODING_SYSTEM_PROMPT = """You are an expert software engineer and coding mentor.

Your capabilities:
- Write clean, production-ready code in any language
- Debug and fix issues with clear explanations
- Review code for best practices, performance, and security
- Explain complex concepts with simple examples
- Suggest modern tools and frameworks

User's tech context:
{user_context}

Always:
- Include comments for complex logic
- Follow language-specific best practices
- Provide complete, runnable examples
- Explain WHY, not just WHAT
- Format code in proper markdown code blocks
"""

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.2,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


async def coding_agent_node(state: AgentState) -> AgentState:
    if "coding_agent" not in state.get("selected_agents", []):
        return state

    start = time.time()
    user_input = state["user_input"]
    user_ctx = state.get("long_term_context", "")
    short_ctx = state.get("short_term_context", "")

    logger.info("coding_agent_start", request=user_input[:100])

    context = f"Recent conversation:\n{short_ctx[-500:]}" if short_ctx else ""

    try:
        response = await llm.ainvoke([
            SystemMessage(content=CODING_SYSTEM_PROMPT.format(user_context=user_ctx[:300])),
            HumanMessage(content=f"{context}\n\nUser request: {user_input}"),
        ])
        coding_output = response.content
    except Exception as e:
        coding_output = f"Coding assistant error: {str(e)}"
        logger.error("coding_agent_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Coding Agent",
        "action": "Generated code solution",
        "status": "completed",
        "output_summary": coding_output[:150],
        "duration_ms": latency,
    }

    current_outputs = state.get("agent_outputs", {})
    current_outputs["coding_agent"] = coding_output

    return {
        **state,
        "agent_outputs": current_outputs,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }
