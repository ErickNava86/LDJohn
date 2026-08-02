import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-before-deploy")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "john")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "dance2026")
