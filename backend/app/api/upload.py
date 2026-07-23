import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/upload", tags=["Upload"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """
    Handles file & image uploads (images, PDFs, text, code files).
    Saves file to local disk and returns metadata + accessible URL.
    """
    try:
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_type = "document"
        if file.content_type and file.content_type.startswith("image/"):
            file_type = "image"
        elif file.content_type and file.content_type.startswith("audio/"):
            file_type = "audio"
        elif file.content_type and file.content_type.startswith("video/"):
            file_type = "video"

        file_url = f"/uploads/{unique_filename}"
        
        return JSONResponse({
            "status": "success",
            "filename": file.filename,
            "unique_name": unique_filename,
            "content_type": file.content_type,
            "file_type": file_type,
            "url": file_url,
            "size": os.path.getsize(file_path),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
