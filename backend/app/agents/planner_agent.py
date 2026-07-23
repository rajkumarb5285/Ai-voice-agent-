"""
Planner Agent Node
Breaks complex tasks into actionable steps and creates execution plans.
"""
import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

PLANNER_SYSTEM_PROMPT = """You are a strategic planning AI. Your role is to:
1. Analyze complex user goals and requests
2. Break them down into clear, actionable steps
3. Identify dependencies and sequencing
4. Assign priorities and estimated timeframes
5. Create executable plans

Return your plan as a JSON array of steps:
[
  {{
    "step": 1,
    "title": "Step title",
    "description": "Detailed description",
    "estimated_time": "1 hour",
    "priority": "high|medium|low",
    "dependencies": [],
    "tools_needed": []
  }}
]

User Profile Context:
{user_context}
"""

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.4,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


async def planner_agent_node(state: AgentState) -> AgentState:
    """Create detailed action plans for complex user requests."""
    if "planner_agent" not in state.get("selected_agents", []):
        return state

    start = time.time()
    user_input = state["user_input"]
    user_ctx = state.get("long_term_context", "No profile available")

    logger.info("planner_agent_start", request=user_input[:100])

    try:
        response = await llm.ainvoke([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT.format(user_context=user_ctx[:500])),
            HumanMessage(content=f"Create a detailed plan for: {user_input}"),
        ])

        plan_text = response.content

        # Try to parse JSON plan
        plan_steps = []
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', plan_text, re.DOTALL)
            if json_match:
                plan_steps = json.loads(json_match.group())
        except Exception:
            plan_steps = []

        human_plan = plan_text if not plan_steps else None

        # Format for output
        if plan_steps:
            plan_output = f"Here's your action plan:\n\n"
            for step in plan_steps:
                plan_output += f"**Step {step.get('step', '')}**: {step.get('title', '')}\n"
                plan_output += f"  {step.get('description', '')}\n"
                plan_output += f"  ⏱ {step.get('estimated_time', 'TBD')} | Priority: {step.get('priority', 'medium')}\n\n"
        else:
            plan_output = plan_text

    except Exception as e:
        logger.error("planner_agent_error", error=str(e))
        plan_steps = []
        plan_output = f"Planning failed: {str(e)}"

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Planner Agent",
        "action": f"Created {len(plan_steps)}-step plan",
        "status": "completed",
        "output_summary": plan_output[:150],
        "duration_ms": latency,
    }

    current_outputs = state.get("agent_outputs", {})
    current_outputs["planner_agent"] = plan_output

    return {
        **state,
        "plan": plan_steps,
        "agent_outputs": current_outputs,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }
