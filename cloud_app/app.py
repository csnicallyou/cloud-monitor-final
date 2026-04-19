from flask import Flask
from config import SECRET_KEY, UPLOAD_FOLDER
from routes.cloud import cloud_bp
from routes.monitor import monitor_bp
from routes.diagnose import diagnose_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(cloud_bp)
app.register_blueprint(monitor_bp)
app.register_blueprint(diagnose_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
