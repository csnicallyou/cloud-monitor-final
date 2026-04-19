from flask import Flask
from flask_login import LoginManager
from config import SECRET_KEY, UPLOAD_FOLDER
from routes.cloud import cloud_bp
from routes.monitor import monitor_bp
from routes.diagnose import diagnose_bp
from routes.auth import auth_bp
from models import User

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please login to access this page'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

app.register_blueprint(cloud_bp)
app.register_blueprint(monitor_bp)
app.register_blueprint(diagnose_bp)
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
