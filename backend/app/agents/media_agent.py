import time
import re
from typing import Dict, Any
from app.agents.state import AgentState
from app.tools.media_generator import generate_image_tool, generate_video_tool
from app.utils.logger import logger
from langchain_openai import ChatOpenAI
from app.config import settings

async def media_agent_node(state: AgentState) -> AgentState:
    """
    General & Multimodal Media Agent — handles general ChatGPT-style chat,
    file analysis, high-definition AI image generation, and HD AI video generation.
    """
    start_time = time.time()
    user_input = state["user_input"]
    input_lower = user_input.lower()

    # Create word checks
    has_create_word = any(w in input_lower for w in ["generate", "create", "make", "produce", "show", "build", "draw"])

    # 1. Check for AI Video Generation Request
    has_video_word = any(v in input_lower for v in ["video", "movie", "animate", "animation"])
    is_video_request = has_video_word and (has_create_word or input_lower.startswith("video"))

    if is_video_request:
        video_prompt = re.sub(r'\b(generate|create|make|produce|show|build|test|a|an|the|video|movie|animation|of|for)\b', '', user_input, flags=re.IGNORECASE).strip()
        if not video_prompt or len(video_prompt) < 2:
            video_prompt = user_input

        res = generate_video_tool(video_prompt)
        video_url = res["media_url"]
        preview_url = res["preview_url"]

        response_text = (
            f"🎬 **HD AI Video Generated Successfully!**\n\n"
            f"**Prompt:** *{video_prompt}*\n\n"
            f"[video:{video_url}]\n\n"
            f"![Video Preview]({preview_url})\n\n"
            f"Hope you enjoy this high-quality AI video! Let me know if you want to generate another video or image."
        )

        duration = int((time.time() - start_time) * 1000)
        current_outputs = dict(state.get("agent_outputs", {}))
        current_outputs["media_agent"] = response_text

        return {
            **state,
            "agent_outputs": current_outputs,
            "agent_activities": state.get("agent_activities", []) + [{
                "agent_name": "MediaAgent",
                "action": "Generated HD AI Video",
                "status": "completed",
                "output_summary": f"Video generated for: {video_prompt[:60]}",
                "duration_ms": duration,
            }],
        }

    # 2. Check for AI Image Generation Request
    has_image_word = any(img in input_lower for img in ["image", "picture", "photo", "pic", "draw"])
    is_image_request = has_image_word and (has_create_word or "draw" in input_lower or input_lower.startswith("image"))

    if is_image_request:
        image_prompt = re.sub(r'\b(generate|create|make|produce|show|draw|a|an|the|image|picture|photo|pic|of|for)\b', '', user_input, flags=re.IGNORECASE).strip()
        if not image_prompt or len(image_prompt) < 2:
            image_prompt = user_input

        res = generate_image_tool(image_prompt)
        image_url = res["media_url"]

        response_text = (
            f"🎨 **AI Image Generated Successfully!**\n\n"
            f"**Prompt:** *{image_prompt}*\n\n"
            f"![{image_prompt}]({image_url})\n\n"
            f"Here is your high-definition image preview! Let me know if you would like any modifications or another creation."
        )

        duration = int((time.time() - start_time) * 1000)
        current_outputs = dict(state.get("agent_outputs", {}))
        current_outputs["media_agent"] = response_text

        return {
            **state,
            "agent_outputs": current_outputs,
            "agent_activities": state.get("agent_activities", []) + [{
                "agent_name": "MediaAgent",
                "action": "Generated AI Image",
                "status": "completed",
                "output_summary": f"Image generated for: {image_prompt[:60]}",
                "duration_ms": duration,
            }],
        }

    # 3. General ChatGPT-style Intelligent Conversation
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
        temperature=0.7,
        max_tokens=1000,
    )


    system_prompt = (
        "You are Ava's General Intelligence Agent — a highly creative, articulate, and versatile AI assistant like ChatGPT.\n"
        "Answer the user's questions clearly, accurately, and with engaging formatting."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    try:
        response = await llm.ainvoke(messages)
        response_text = response.content
    except Exception as e:
        logger.error("media_agent_llm_failed", error=str(e))
        response_text = "I am ready to assist you with general chat, image generation, and HD video generation! How can I help you today?"

    duration = int((time.time() - start_time) * 1000)
    current_outputs = dict(state.get("agent_outputs", {}))
    current_outputs["media_agent"] = response_text

    return {
        **state,
        "agent_outputs": current_outputs,
        "agent_activities": state.get("agent_activities", []) + [{
            "agent_name": "MediaAgent",
            "action": "Processed General/Multimodal Query",
            "status": "completed",
            "output_summary": response_text[:150],
            "duration_ms": duration,
        }],
    }
