import uuid
from celery import Celery
import requests
from image_processing import main as process_image_main
from supabase import create_client
import os
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
REDIS_URL = os.getenv("REDIS_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,  # Update if your Redis is elsewhere
    backend=REDIS_URL
)

@celery_app.task
def process_image_task(record_id, original_url, option):
    print(f"[INFO] Processing task for record {record_id} with option '{option}'")
    print(f"[INFO] Downloading image from URL: {original_url}")
    try:

         # Download the image from Supabase Storage
        response = requests.get(original_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download image. Status code: {response.status_code}")
        if not response.content:
            raise Exception("Downloaded image is empty.")
        
        image_data = response.content

        supabase.table("images").update({"status": "processing"}).eq("id", record_id).execute()

        light = option in ["light", "both"]
        heavy = option in ["heavy", "both"]

        processed_path = process_image_main(image_data, light=light, heavy=heavy)

        processed_filename = f"processed_{uuid.uuid4()}_{Path(original_url).name}"

        # Upload processed image
        with open(processed_path, "rb") as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                path=processed_filename,
                file=f,
                file_options={"content-type": "image/png"}
            )

        processed_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{processed_filename}"

        supabase.table("images").update({
            "processed_path": processed_url,
            "status": "done"
        }).eq("id", record_id).execute()

        # file_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)

    except Exception as e:
        print(f"[ERROR] Processing failed for {record_id}: {e}")
        supabase.table("images").update({"status": "failed"}).eq("id", record_id).execute()