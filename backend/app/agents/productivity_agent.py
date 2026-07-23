"""
Productivity Agent Node
Manages tasks, calendar, reminders, and daily planning.
"""
import time
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

PRODUCTIVITY_SYSTEM_PROMPT = """You are an elite productivity and time management coach.

You help users:
- Plan their day and week effectively
- Prioritize tasks using methods like Eisenhower Matrix, Time Blocking
- Set realistic deadlines and milestones
- Create routines and systems for success
- Avoid procrastination and overwhelm
- Review and reflect on productivity

Current date/time: {current_datetime}

User's upcoming context:
{user_context}
"""

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.4,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


async def productivity_agent_node(state: AgentState, db=None) -> AgentState:
    if "productivity_agent" not in state.get("selected_agents", []):
        return state

    start = time.time()
    user_input = state["user_input"]
    user_ctx = state.get("long_term_context", "")
    current_dt = datetime.utcnow().strftime("%A, %B %d %Y — %H:%M UTC")

    logger.info("productivity_agent_start", request=user_input[:100])

    tool_result = None
    action_taken = "Provided productivity guidance"

    if db:
        try:
            from app.tools.calendar_tool import CalendarTool
            import uuid
            import json
            import re
            
            calendar_tool = CalendarTool(db, uuid.UUID(state["user_id"]))
            from app.tools.task_tool import TaskTool
            task_tool = TaskTool(db, uuid.UUID(state["user_id"]))
            lowered_input = user_input.lower()
            
            if any(k in lowered_input for k in ["schedule", "calendar", "event", "meeting", "appointment", "book"]):
                if any(k in lowered_input for k in ["show", "list", "view", "what", "upcoming"]):
                    # List events
                    tool_result = await calendar_tool.list_events()
                    action_taken = "Checked calendar events"
                elif any(k in lowered_input for k in ["delete", "remove", "cancel"]):
                    # Extract event title or ID to delete
                    extraction_prompt = f"""
                    Extract the event ID or unique details to identify the event to delete.
                    User input: "{user_input}"
                    
                    Respond ONLY with a JSON object:
                    {{
                        "event_id": "ID of the event or empty string"
                    }}
                    """
                    extraction_resp = await llm.ainvoke(extraction_prompt)
                    match = re.search(r'\{.*\}', extraction_resp.content, re.DOTALL)
                    if match:
                        params = json.loads(match.group())
                        event_id = params.get("event_id")
                        if event_id:
                            tool_result = await calendar_tool.delete_event(event_id)
                            action_taken = "Deleted calendar event"
                else:
                    # Create calendar event
                    extraction_prompt = f"""
                    Extract calendar event details (title, start_time, end_time, description, location, is_all_day) from the user input.
                    Current datetime is: {current_dt}
                    User input: "{user_input}"
                    
                    Respond ONLY with a JSON object:
                    {{
                        "title": "event title",
                        "start_time": "YYYY-MM-DDTHH:MM:SS",
                        "end_time": "YYYY-MM-DDTHH:MM:SS",
                        "description": "optional description or null",
                        "location": "optional location or null",
                        "is_all_day": true/false
                    }}
                    """
                    extraction_resp = await llm.ainvoke(extraction_prompt)
                    match = re.search(r'\{.*\}', extraction_resp.content, re.DOTALL)
                    if match:
                        params = json.loads(match.group())
                        title = params.get("title") or "Calendar Event"
                        try:
                            start_time = datetime.fromisoformat(params.get("start_time"))
                            end_time = datetime.fromisoformat(params.get("end_time"))
                            
                            res = await calendar_tool.create_event(
                                title=title,
                                start_time=start_time,
                                end_time=end_time,
                                description=params.get("description"),
                                location=params.get("location"),
                                is_all_day=params.get("is_all_day", False)
                            )
                            tool_result = res
                            action_taken = f"Scheduled event: {title}"
                        except Exception as parse_err:
                            logger.warning("calendar_time_parse_failed", error=str(parse_err))
                            tool_result = {"status": "error", "message": f"Failed to parse event dates/times. Please be specific."}
            elif any(k in lowered_input for k in ["task", "todo", "remind me", "reminder", "don't forget"]):
                if any(k in lowered_input for k in ["show", "list", "view", "what", "upcoming"]):
                    tool_result = await task_tool.list_tasks()
                    action_taken = "Checked task list"
                else:
                    # Create a task
                    extraction_prompt = f"""
                    Extract task details (title, description, priority, category, due_date) from the user input.
                    Current datetime is: {current_dt}
                    User input: "{user_input}"
                    
                    Respond ONLY with a JSON object:
                    {{
                        "title": "task title (what to do)",
                        "description": "optional description details or null",
                        "priority": "low|medium|high|urgent",
                        "category": "optional category or null",
                        "due_date": "YYYY-MM-DDTHH:MM:SS or null"
                    }}
                    """
                    extraction_resp = await llm.ainvoke(extraction_prompt)
                    match = re.search(r'\{.*\}', extraction_resp.content, re.DOTALL)
                    if match:
                        params = json.loads(match.group())
                        title = params.get("title") or user_input[:60]
                        due_date_str = params.get("due_date")
                        due_date = None
                        if due_date_str:
                            try:
                                due_date = datetime.fromisoformat(due_date_str)
                            except:
                                pass
                        
                        res = await task_tool.create_task(
                            title=title,
                            description=params.get("description"),
                            priority=params.get("priority") or "medium",
                            category=params.get("category"),
                            due_date=due_date
                        )
                        tool_result = res
                        action_taken = f"Created task: {title}"
            
        except Exception as e:
            logger.error("productivity_agent_tool_error", error=str(e))
            tool_result = f"Error performing calendar action: {str(e)}"

    # Incorporate tool result into LLM response synthesis
    prompt_with_tools = PRODUCTIVITY_SYSTEM_PROMPT.format(
        current_datetime=current_dt,
        user_context=user_ctx[:400],
    )
    if tool_result:
        prompt_with_tools += f"\n\nTool Execution Result: {json.dumps(tool_result)}"

    try:
        response = await llm.ainvoke([
            SystemMessage(content=prompt_with_tools),
            HumanMessage(content=user_input),
        ])
        productivity_output = response.content

        # Auto-detect if we should create a task (as backup)
        memories = []
        if any(kw in user_input.lower() for kw in ["remind me", "task", "todo", "don't forget"]):
            memories.append({
                "content": f"Task/reminder: {user_input}",
                "category": "task",
                "title": user_input[:60],
                "importance_score": 0.7,
            })

    except Exception as e:
        productivity_output = f"Productivity assistant error: {str(e)}"
        memories = []
        logger.error("productivity_agent_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Productivity Agent",
        "action": action_taken,
        "status": "completed",
        "output_summary": productivity_output[:150],
        "duration_ms": latency,
    }

    current_outputs = state.get("agent_outputs", {})
    current_outputs["productivity_agent"] = productivity_output

    existing_memories = state.get("memories_to_store", [])

    return {
        **state,
        "agent_outputs": current_outputs,
        "memories_to_store": existing_memories + memories,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }

