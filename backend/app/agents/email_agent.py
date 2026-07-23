"""
Email Agent Node
Draft, summarize, and manage email communications.
"""
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

EMAIL_SYSTEM_PROMPT = """You are an expert email communication specialist.

Your capabilities:
- Draft professional, compelling emails
- Adjust tone (formal, casual, assertive, empathetic)
- Summarize long email threads
- Suggest reply strategies
- Write follow-ups, cold emails, and cover letters
- Proofread and improve existing drafts

Always ask about tone and context if unclear.
Structure emails with: Subject line, greeting, body, call-to-action, sign-off.

User's communication preferences:
{user_context}
"""

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.5,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


async def email_agent_node(state: AgentState, db=None) -> AgentState:
    if "email_agent" not in state.get("selected_agents", []):
        return state

    start = time.time()
    user_input = state["user_input"]
    user_ctx = state.get("long_term_context", "")

    logger.info("email_agent_start")

    tool_result = None
    action_taken = "Drafted email communication"

    if db:
        try:
            from app.tools.email_tool import EmailTool
            import uuid
            import json
            import re
            
            email_tool = EmailTool(db, uuid.UUID(state["user_id"]))
            lowered_input = user_input.lower()
            
            if any(k in lowered_input for k in ["send email", "draft email", "write email", "email to"]):
                # Extract email parameters using a quick LLM call
                extraction_prompt = f"""
                Extract the recipient email address, subject, body, and whether it's a draft from the user input.
                User input: "{user_input}"
                
                Respond ONLY with a JSON object:
                {{
                    "to_address": "email or empty string",
                    "subject": "subject or empty string",
                    "body": "body or empty string",
                    "draft": true/false
                }}
                """
                extraction_resp = await llm.ainvoke(extraction_prompt)
                match = re.search(r'\{.*\}', extraction_resp.content, re.DOTALL)
                if match:
                    params = json.loads(match.group())
                    to_addr = params.get("to_address")
                    subj = params.get("subject") or "No Subject"
                    body_text = params.get("body") or "No Body"
                    is_draft = params.get("draft", False)
                    
                    if to_addr:
                        res = await email_tool.send_email(
                            to_address=to_addr,
                            subject=subj,
                            body=body_text,
                            draft=is_draft
                        )
                        tool_result = res
                        action_taken = f"Saved email draft to {to_addr}" if is_draft else f"Sent email to {to_addr}"
            
            elif any(k in lowered_input for k in ["list email", "show email", "check email", "inbox", "sent email"]):
                folder = "sent" if "sent" in lowered_input else "inbox"
                tool_result = await email_tool.list_emails(folder=folder)
                action_taken = f"Checked {folder} folder"
                
        except Exception as e:
            logger.error("email_agent_tool_error", error=str(e))
            tool_result = f"Error performing email action: {str(e)}"

    # Generate synthesized conversational response
    prompt_with_tools = EMAIL_SYSTEM_PROMPT.format(user_context=user_ctx[:300])
    if tool_result:
        prompt_with_tools += f"\n\nTool Execution Result: {json.dumps(tool_result)}"

    try:
        response = await llm.ainvoke([
            SystemMessage(content=prompt_with_tools),
            HumanMessage(content=user_input),
        ])
        email_output = response.content
    except Exception as e:
        email_output = f"Email agent error: {str(e)}"
        logger.error("email_agent_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Email Agent",
        "action": action_taken,
        "status": "completed",
        "output_summary": email_output[:150],
        "duration_ms": latency,
    }

    current_outputs = state.get("agent_outputs", {})
    current_outputs["email_agent"] = email_output

    return {
        **state,
        "agent_outputs": current_outputs,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }

