from http.client import HTTPException
from fastapi import FastAPI, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from supabase import create_client, Client
from fastapi import UploadFile, File
from typing import List
import uuid
from pathlib import Path

from fastapi import BackgroundTasks
import uvicorn
from celery_worker import process_image_task

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024  # in bytes

# temp dictry 
TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_images(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    option: str = Form(...),
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)

    user = supabase.auth.get_user(token)
    email = user.user.email if user and user.user else "Unknown"

    
    for file in files:
        # Generate unique filename
        unique_name = f"{uuid.uuid4()}_{file.filename}"

        temp_file_path = TEMP_DIR / unique_name

        # Save file temporarily
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        # Upload using file path
        supabase.storage.from_(BUCKET_NAME).upload(
            str(unique_name),  # This is the object path in storage
            file=temp_file_path,  # FileIO or Path is accepted
            file_options={"content-type": "image/*"}
        )

        # Build public URL
        original_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{unique_name}"

        # Insert DB record with status 'queued'
        insert_result = supabase.table("images").insert({
            "user_email": email,
            "original_path": original_url,
            "option_selected": option,
            "processed_path": None,
            "status": "queued"
        }).execute()

        record_id = insert_result.data[0]["id"]

        # queue async processing using Celery
        process_image_task.delay(record_id, str(temp_file_path), option)


    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/api/images")
def get_user_images(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401)

    user = supabase.auth.get_user(token)
    email = user.user.email if user and user.user else "Unknown"

    result = supabase.table("images").select("*").eq("user_email", email).order("created_at", desc=True).execute()
    return result.data

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(...)):
    result = supabase.auth.sign_up({"email": email, "password": password})
    if result.user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/signup", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(response: Response, email: str = Form(...), password: str = Form(...)):
    result = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if result.session:
        # Save access token in cookie (simplified)
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie("access_token", result.session.access_token)
        return response
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token: # if no token, redirect to home
        return RedirectResponse(url="/")

    user = supabase.auth.get_user(token)
    email = user.user.email if user and user.user else "Unknown"

    # Fetch user’s image records
    result = supabase.table("images").select("*").eq("user_email", email).order("created_at", desc=True).execute()
    user_images = result.data if result.data else []

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "email": email,
        "user_images": user_images
    })

@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)