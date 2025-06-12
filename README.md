## 🖼️ PicFilter FullStack App

A full-stack application built with **FastAPI** and **Supabase** that allows users to:

* Sign up / log in securely
* Upload multiple images (max 10MB each)
* Choose processing options: `light`, `heavy`, or `both`
* View original and processed images
* Track processing status live
* Store images in **Supabase Storage**
* Queue and process tasks asynchronously

---

### 🛠️ Tech Stack

* 🐍 FastAPI (backend)
* 🐘 Supabase (Auth, PostgreSQL, Storage)
* 🖼️ Pillow (image processing)
* 🗅️ HTML + Jinja2 + JS (frontend) - HTML Generated using AI

---

## 📦 Setup Guide

### 1. Clone the Repository

```bash
git clone
cd project directory
```
---

### 2. Create `.env` File

Create a `.env` file in the root with:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_anon_or_service_key
BUCKET_NAME=your_storage_bucket_name
```

Ensure Store Bucket is Public and has access for upload, Read

---

### 3. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, you can create it:

```txt
fastapi
uvicorn
python-multipart
pillow
python-dotenv
storage3
supabase
jinja2
```

---

### 4. Set Up Supabase

* Go to [supabase.com](https://supabase.com)
* Create a project
* Enable:

  * Authentication
  * Storage bucket (e.g., `images`)
  * PostgreSQL table `images` with fields:

```sql
CREATE TABLE images (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_email text,
  original_path text,
  processed_path text,
  option_selected text,
  status text,
  created_at timestamp with time zone DEFAULT now()
);
```

Enable Row Level Security (RLS) and set appropriate policies if needed.

---

### 5. Run the App

```bash
uvicorn main:app --reload

background worker
celery -A celery_worker.celery_app worker --loglevel=info

View worker in Flower
celery -A celery_worker.celery_app flower --port=5555
```

Visit: `http://localhost:8000`

---

## ✅ Features

### 🔐 Authentication

* Sign up / login using Supabase Auth
* Session stored via cookies

### 📄 Upload

* Upload multiple images
* Max file size: 10MB
* Choose processing: light / heavy / both

### ⚙️ Processing

* Light = fast blur filter
* Heavy = simulated long operation
* Asynchronous background task queue

### 🗓️ Storage

* Original & processed images saved in Supabase Storage
* Paths saved to Supabase PostgreSQL

### 📊 Dashboard

* View original + processed images
* See status: `queued`, `processing`, `done`, `failed`
* Live auto-refresh every 10 seconds

---

## 🧐 How Processing Works

1. Image is uploaded to `temp_uploads/`
2. File is saved to Supabase Storage
3. A DB record is inserted with `status='queued'`
4. Celery task:
 - Downloads file from storage
 - Applies light/heavy filters (via Pillow)
 - Uploads processed image to storage
 - Updates DB with processed_path + status='done'
---

## 📸 Processing Script (image\_processing.py)

```python
from PIL import Image, ImageFilter
import time

def light_processing(image):
    return image.filter(ImageFilter.BLUR)

def heavy_processing(image):
    time.sleep(60)
    return image.filter(ImageFilter.CONTOUR)

def process_image(path, light=False, heavy=False) -> Path:
    image = Image.open(path)
    if light:
        image = light_processing(image)
    if heavy:
        image = heavy_processing(image)
    processed_path = path.with_stem(path.stem + "_Processed")
    image.save(processed_path)
    return processed_path
```

---

## 📜 Future Enhancements
* 📱 Mobile-responsive design
* ✅ Progress bar / status spinner
* ✅ Upload limit + client-side validation
* ⏳ Advanced queue viewer using Flower
* 🗒️ Admin tools / retry failed jobs
---

Docker
- Docker Compose up -d