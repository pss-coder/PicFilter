from celery import Celery
from image_processing import main as process_image_main
from supabase import create_client
import os
from dotenv import load_dotenv
from pathlib import Path

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
def process_image_task(record_id, file_path_str, option):
    print(f"[INFO] Processing task for record {record_id} with option '{option}'")
    file_path = Path(file_path_str)
    try:
        supabase.table("images").update({"status": "processing"}).eq("id", record_id).execute()

        light = option in ["light", "both"]
        heavy = option in ["heavy", "both"]

        processed_path = process_image_main(file_path, light=light, heavy=heavy)

        # Upload processed image
        with open(processed_path, "rb") as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                path=processed_path.name,
                file=f,
                file_options={"content-type": "image/png"}
            )

        processed_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{processed_path.name}"

        supabase.table("images").update({
            "processed_path": processed_url,
            "status": "done"
        }).eq("id", record_id).execute()

        file_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)

    except Exception as e:
        print(f"[ERROR] Processing failed for {record_id}: {e}")
        supabase.table("images").update({"status": "failed"}).eq("id", record_id).execute()