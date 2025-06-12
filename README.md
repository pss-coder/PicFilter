## 🖼️ PicFilter FullStack App

A full-stack image upload and processing web app powered by **FastAPI**, **Supabase**, **Celery**, and **Docker** — deployed on **AWS EC2**.
---

## Architecture
![PicFilter-Arch](https://github.com/user-attachments/assets/5b0ed6dd-cf09-4a94-97f8-e78210e2fb02)


## 🌐 Live Demo
🎥 **Demo Video:** [Watch here](https://github.com/user-attachments/assets/47bc1391-0e6e-4d54-a10b-e3070b694c3e)

🔗 **App**: [ec2-47-130-127-208.ap-southeast-1.compute.amazonaws.com:8000](http://ec2-47-130-127-208.ap-southeast-1.compute.amazonaws.com:8000)

🔍 **Queue Dashboard (Flower)**: [ec2-47-130-127-208.ap-southeast-1.compute.amazonaws.com:5555](http://ec2-47-130-127-208.ap-southeast-1.compute.amazonaws.com:5555)

### Demo Account: 
- Email: docker@hello.com
- Password: 12345678

---
## ✨ Features

- 🔐 Supabase Auth for sign-up/login
- 📤 Multi-image upload (frontend max 10MB)
- 🧠 Choose `light`, `heavy`, or `both` processing
- 🚀 Async processing via Celery + Redis
- 🧺 Real-time status queue dashboard (Flower)
- ☁️ Supabase Storage for image hosting
- 🖥️ Deployed on AWS EC2 using Docker + Elastic IP

---

## 🛠️ Tech Stack
- 🐍 FastAPI
- 🐘 Supabase (Auth, DB, Storage)
- 📦 Docker & Docker Compose
- 🧵 Celery + Redis for background jobs
- 📊 Flower for queue monitoring
- ☁️ AWS EC2 w/ Elastic IP
- 🎨 HTML + Jinja2 + Vanilla JS - AI Assisted
---

## 📂 Project Structure

```bash
.
├── main.py                  # FastAPI app
├── celery_worker.py         # Celery config + tasks
├── image_processing.py      # Light/Heavy processing
├── templates/               # Jinja2 HTML
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
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
REDIS_URL=your_redis_url # development: redis://redis:6379/0
```
---

### 3. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

### 4. Set Up Supabase

* Go to [supabase.com](https://supabase.com)
* Create a project
* Enable:

  * Authentication
  * Storage bucket (e.g., `images`) - Ensure Store Bucket is Public and has access for upload, Read
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

- Visit: `http://localhost:8000` - for the web app
- Visit: `http://localhost:5555` - for flower dashboard

---

## 🧐 How Processing Works

1. Image is uploaded to `temp_uploads/` as temp directory
2. Image is saved to Supabase Storage
3. A DB record is inserted with `status='queued'`
4. Celery task:
 - Downloads file from storage
 - Applies light/heavy filters (via Pillow)
 - Uploads processed image to storage
 - Updates DB with processed_path + status='done'
---

## 📸 Processing Script (image\_processing.py)

```python
def main(image_data, light=False, heavy=False) -> Path:
    image = Image.open(io.BytesIO(image_data))
    if light:
        image = light_processing(image)
    if heavy:
        image = heavy_processing(image)
        
    new_path = Path(f"processed_image_{uuid.uuid4()}_{int(time.time())}.png")
    image.save(new_path)
    return new_path
```

---

## 📜 Future Enhancements
* 📱 Mobile-responsive design
* 📱 Improve authentication flow - wrong email, password entered/email already exists workflows
* ✅ Progress bar / status spinner
* ✅ Upload limit + client-side validation
* ⏳ Advanced queue viewer using Flower
* 🗒️ Admin tools / retry failed jobs
---

## 💡 Resources
https://medium.com/@hitorunajp/celery-and-background-tasks-aebb234cae5d
https://supabase.com/docs/reference/python/storage-from-upload
https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html


## Known Issues: 
https://github.com/encode/httpx/issues/1433

https://github.com/supabase/supabase/issues/16857

## AI Usage
- Initial README.MD
- Frontend Jinja 2 UI Setup
- Initial FastAPI Project Setup
