# EasyDownloader

_A robust, fast, and reliable content downloader_

![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/RaufMasoumi/easydownloader?style=flat&logo=python&logoColor=orange&label=Python&labelColor=gray&color=orange)
![GitHub Pipenv locked dependency version](https://img.shields.io/github/pipenv/locked/dependency-version/RaufMasoumi/easydownloader/django?logo=Django&logoColor=white&label=Django&labelColor=gray&color=orange)
![GitHub Pipenv locked dependency version](https://img.shields.io/github/pipenv/locked/dependency-version/RaufMasoumi/easydownloader/djangorestframework?style=flat&logo=DRF&logoColor=white&label=DjangoRestFramework&labelColor=gray&color=orange)

![Celery](https://img.shields.io/badge/Celery-Enabled-%2338b000?logo=celery&logoColor=white)

---

## 📑 Table of Contents
- [About](#-about)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Project](#-running-the-project)
- [Docker Setup](#-docker-setup)
- [Testing](#-testing)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📖 About
EasyDownloader is a robust and extensible content downloader service for both audio and video contents. It supports popular sources like YouTube, YouTube Music, and Instagram. It provides RESTful endpoints for seamless integration with modern frontend frameworks.

EasyDownloader is continuously evolving, with ongoing efforts to support more content sources. Thanks to its plugin-based architecture, extending the system to cover new platforms is simple and efficient.

If you’re interested in contributing — whether by adding new features, improving existing functionality, or extending support to additional sources — check out the [Contributing](#-contributing)
 section to get started.

The project is based on Django and Django Rest Framework and uses the [yt-dlp Python package](https://github.com/yt-dlp/yt-dlp/) as its core.

---

## 🚀 Features
- High-quality content downloading  
- Robust content format selection system  
- Specially designed for downloading music content  
- Asynchronous and optimized downloading process  
- Well-documented, easy-to-use RESTful API endpoints  
- Dockerized and ready for production  
- Comprehensive unit testing  
- Plugin-based system architecture using OOP for easy extension and support for new sources  
- Clean and maintainable code  

---

## 🛠 Tech Stack
- Language: Python 3.13  
- Framework: Django, Django REST Framework  
- Database: PostgreSQL / SQLite  
- Task Queue: Celery  
- Cache & Queue: Redis / RabbitMQ  
- Deployment: Docker, Docker Compose, Gunicorn  

---

## 📂 Project Structure
````
easydownloader/
├── .idea/
├── api/                    # REST API logic
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── downloader/             # Core downloading logic and tasks
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── downloaders_tests.py
│   ├── downloaders.py
│   ├── main_downloader.py
│   ├── migrations/
│   ├── tasks.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── home/                   # Homepage app (template based)
├── config/                 # Django project configuration
├── templates/              # HTML templates
├── docker-compose-prod.yml # Production Docker Compose file
├── Dockerfile              # Docker build file
├── .gitignore              # Git ignore rules
├── manage.py               # Django management script
├── Pipfile                 # Pipenv dependencies
├── Pipfile.lock            # Locked dependencies
└── schema.yml              # API schema definition
````

---

## 📌 Prerequisites
Make sure you have the following installed:
- Python **3.13+**  
- Docker & Docker Compose (for containerized setup)  

---

## ⚡️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/RaufMasoumi/easydownloader.git
cd easydownloader
```

### 2️⃣ Create and activate virtual environment
```bash
python -m pip install pipenv
pipenv shell
```

### 3️⃣ Install dependencies
```bash
pipenv install
```

### 4️⃣ Run migrations
Before running migrations, make sure you’ve set up the [Configuration](#-configuration)
```bash
python manage.py migrate
```

### 5️⃣ Create superuser
```bash
python manage.py createsuperuser
```

---

## 🔑 Configuration
First, create a Django secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then add environment variables to a `.env` file:
```
DJANGO_SECRET_KEY="your-django-secret-key"
```

---

## ▶️ Running the Project
```bash
python manage.py runserver
```

---

## 🐳 Docker Setup
```bash
docker compose -f docker-compose-prod.yml up
```

---

## ✅ Testing
```bash
python manage.py test --pattern="*tests.py"
```

---

## 📌 API Documentation
- Schema file → `/api/schema/`  
- Swagger UI → `/api/schema/swagger-ui/`  
- Redoc → `/api/schema/redoc/`


---

## 🤝 Contributing
1. Fork the repo  
2. Create a branch (`git checkout -b feature/your-feature`)  
3. Commit changes (`git commit -m "Add feature"`)  
4. Push (`git push origin feature/your-feature`)  
5. Open a Pull Request  

---

## 📜 License
Distributed under the **MIT License**. See the [```LICENSE file```](./LICENSE) for more information.

Developed with ❤️ by Rauf Masoumi  
