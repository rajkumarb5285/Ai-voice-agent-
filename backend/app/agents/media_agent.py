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
    
    # 1. Check for AI Video Generation Request
    video_triggers = ["create video", "generate video", "make a video", "video of", "produce video", "animate"]
    if any(trigger in input_lower for trigger in video_triggers):
        # Extract clean video prompt
        video_prompt = user_input
        for trig in video_triggers:
            video_prompt = re.sub(re.escape(trig), "", video_prompt, flags=re.IGNORECASE).strip()
        if not video_prompt:
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
    image_triggers = ["generate image", "create image", "make an image", "draw", "picture of", "photo of", "image of"]
    if any(trigger in input_lower for trigger in image_triggers):
        image_prompt = user_input
        for trig in image_triggers:
            image_prompt = re.sub(re.escape(trig), "", image_prompt, flags=re.IGNORECASE).strip()
        if not image_prompt:
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
        api_key=settings.groq_api_key or settings.openai_api_key,
        base_url=settings.openai_base_url,
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
        response_text = f"I am ready to assist you with general chat, image generation, and HD video generation! How can I help you today?"

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
