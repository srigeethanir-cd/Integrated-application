import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from agents.agent0_wireframe.wireframe_agent import Agent0Wireframe

router = APIRouter()

@router.post("/generate")
async def generate_code(
    user_story: str = Form(...),
    framework_type: str = Form(...), # 'jsx' or 'tsx'
    image: UploadFile = File(...)
):
    """Integrated Code-Gene code generation endpoint routing entirely through Agent 0."""
    try:
        # Initialize Agent 0
        agent0 = Agent0Wireframe()
        
        # Read uploaded image bytes
        image_bytes = await image.read()
        
        # Run visual generation pipeline in Agent 0
        result = agent0.generate_from_story_and_image(
            user_story=user_story,
            framework_type=framework_type,
            image_bytes=image_bytes,
            content_type=image.content_type or "image/png"
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

