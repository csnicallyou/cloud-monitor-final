from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, id, username, password_hash, folder_name):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.folder_name = folder_name
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get_by_id(user_id):
        from utils.db import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash, folder_name FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return User(row[0], row[1], row[2], row[3])
        return None
    
    @staticmethod
    def get_by_username(username):
        from utils.db import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash, folder_name FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return User(row[0], row[1], row[2], row[3])
        return None
    
    @staticmethod
    def create(username, password):
        from utils.db import get_db_connection
        import os
        password_hash = generate_password_hash(password)
        folder_name = f"user_{username}_{os.urandom(4).hex()}"
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, folder_name) VALUES (%s, %s, %s) RETURNING id",
            (username, password_hash, folder_name)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        # Создаём папку пользователя
        user_folder = os.path.join('/home/csn/cloud_app/static/uploads', folder_name)
        os.makedirs(user_folder, exist_ok=True)
        
        return user_id
