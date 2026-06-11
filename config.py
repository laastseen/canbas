import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"


class Config:
    POLICY_VERSION = "2026-06-06"
    LEGAL_OPERATOR = {
        "name": "Мамонов Кирилл Александрович",
        "address": "160000, г. Вологда, ул. Бородинская, д. 8",
        "phone": "+7 (921) 680-07-03",
        "email": "kirillmamonov1311@gmail.com",
        "site_url": os.environ.get("SITE_URL", "https://vm4361050.firstbyte.club"),
    }
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'app.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(UPLOAD_DIR))
    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif", "pdf", "doc", "docx", "txt", "zip"
    }
