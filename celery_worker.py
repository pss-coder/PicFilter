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
    broker="redis://localhost:6379/0",  # Update if your Redis is elsewhere
    backend="redis://localhost:6379/0"
)

@celery_app.task
def process_image_task(record_id, original_url, option):
    id = record_id
    print(f"[INFO] Processing task for record {record_id} with option '{option}'")
    print(f"[INFO] Downloading image from URL: {original_url}")
    try:

         # Download the image from Supabase Storage
        try:
            response = requests.get(original_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download image. Status code: {response.status_code}")
            if not response.content:
                raise Exception("Downloaded image is empty.")
        except Exception as e:
            print("Error GETTING ORIGINAL URL:", e)
        
        image_data = response.content

        # ISSUE: Expecting value: line 1 column 1 (char 0)
        try:
            response = supabase.table("images").update({"status": "processing"}).eq("id", record_id).execute()
            print(response)
        except Exception as e:
            print("Error UPDATING IMAGES TO PROCESSING:", e)


        light = option in ["light", "both"]
        heavy = option in ["heavy", "both"]

        processed_path = process_image_main(image_data, light=light, heavy=heavy)

        # Upload processed image
        with open(processed_path, "rb") as f:
            try:
                print(processed_path)
                result = supabase.storage.from_(BUCKET_NAME).upload(
                    str(processed_path.name),
                    file=f,
                    file_options={"content-type": "image/*"}
                )
                print("[DEBUG] Upload result:", result)
            except Exception as e:
                print(f"[ERROR] Failed to upload processed image to Supabase Storage: {e}")
                # Optionally, mark the image as failed in the DB if upload is critical
                supabase.table("images").update({"status": "failed"}).eq("id", record_id).execute()
                return  # exit the function early if upload fails

        processed_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{str(processed_path.name)}"

        try:
            response = supabase.table("images").update({
                "processed_path": processed_url,
                "status": "done"
            }).eq("id", record_id).execute()
            print(response)
        except Exception as e:
            print("Error UPDATING IMAGES to STATUS DONE:", e)

        # file_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)


    except Exception as e:
        print(f"[ERROR] Processing failed for {record_id}: {e}")
        supabase.table("images").update({"status": "failed"}).eq("id", record_id).execute()