from image_processor import process_image

from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import os
import uuid
from pathlib import Path
import shutil
import asyncio

app = FastAPI(title="Image Processor Web App", description="A web application for image processing")

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Templates setup
templates = Jinja2Templates(directory="templates")


# Thread pool for CPU-intensive image processing
executor = ThreadPoolExecutor(max_workers=4)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    light: bool = Form(False),
    heavy: bool = Form(False)
):
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload an image file."
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > MAX_CONTENT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_CONTENT_LENGTH // (1024*1024)}MB"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Get processing options
    if not light and not heavy:
        raise HTTPException(
            status_code=400,
            detail="Please select at least one processing option"
        )
    
    try:
        # Save uploaded file
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = Path(UPLOAD_FOLDER) / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process image in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        processed_path = await loop.run_in_executor(
            executor, 
            process_image_with_custom_path, 
            file_path, 
            light, 
            heavy
        )
        
       #TODO: Save to DB
        
        # Clean up original file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            'success': True,
            'message': 'Image processed successfully!'
        }
        
    except Exception as e:
        # Clean up files on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f'Processing failed: {str(e)}')

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Image Processor API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# Helper
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image_with_custom_path(image_path: Path, light: bool = False, heavy: bool = False) -> Path:
    """Wrapper function to process image and save to custom location"""
    # Generate unique filename for processed image
    unique_id = str(uuid.uuid4())[:8]
    suffix = []
    if light:
        suffix.append("light")
    if heavy:
        suffix.append("heavy")
    
    suffix_str = "_".join(suffix) if suffix else "original"
    processed_filename = f"{image_path.stem}_{suffix_str}_{unique_id}{image_path.suffix}"
    processed_path = Path(PROCESSED_FOLDER) / processed_filename
    
    # Use the original process_image function from processing module
    temp_processed = process_image(image_path, light=light, heavy=heavy)
    
    # Move the processed file to our custom location
    os.rename(temp_processed, processed_path)
    
    return processed_path