import urllib.parse
import time
import random
import logging

logger = logging.getLogger("voice_agent")

def generate_image_tool(prompt: str, width: int = 1024, height: int = 1024) -> dict:
    """
    Generates a high-quality photorealistic AI image from a text prompt.
    Returns the image URL and metadata.
    """
    logger.info("generate_image_start", prompt=prompt)
    clean_prompt = prompt.strip()
    encoded = urllib.parse.quote(clean_prompt)
    seed = random.randint(100000, 999999)
    # High quality Pollinations FLUX image URL
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
    
    return {
        "status": "success",
        "type": "image",
        "prompt": clean_prompt,
        "media_url": image_url,
        "width": width,
        "height": height,
        "description": f"AI Generated Image for: '{clean_prompt}'"
    }

def generate_video_tool(prompt: str, width: int = 1280, height: int = 720) -> dict:
    """
    Generates a high-definition AI video (MP4) from a text prompt.
    E.g. 'dog is cooking food in the kitchen'
    """
    logger.info("generate_video_start", prompt=prompt)
    clean_prompt = prompt.strip()
    encoded = urllib.parse.quote(clean_prompt)
    seed = random.randint(100000, 999999)
    
    # High Quality AI Video Generator URL (HD MP4 / Pollinations Video / Animated GIF Video player)
    video_url = f"https://video.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"
    # Fallback HD video animation preview for reliable player playback
    fallback_preview = f"https://image.pollinations.ai/prompt/{encoded}%20cinematic%20hd%20video%20animation?width={width}&height={height}&seed={seed}&nologo=true"

    return {
        "status": "success",
        "type": "video",
        "prompt": clean_prompt,
        "media_url": video_url,
        "preview_url": fallback_preview,
        "width": width,
        "height": height,
        "description": f"HD AI Video Generated for: '{clean_prompt}'"
    }
