import os

SECRET_KEY = 'supersecretkey12345_for_cloud_lab_project_2026'
UPLOAD_FOLDER = "/home/csn/cloud_app/static/uploads"
DB_HOST = 'localhost'
DB_NAME = 'cloud_lab'
DB_USER = 'cloud_user'
DB_PASSWORD = 'lab123'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
