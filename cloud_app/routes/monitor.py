from flask import Blueprint, request, render_template
from utils.db import get_db_connection

monitor_bp = Blueprint('monitor', __name__, url_prefix='/monitor')

@monitor_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    limit = 10
    offset = (page - 1) * limit

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM metrics")
    total = cur.fetchone()[0]
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    cur.execute("""
        SELECT timestamp, cpu_load, ram_free_mb, disk_free_gb, nginx_status, postgres_status
        FROM metrics
        ORDER BY timestamp DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))
    metrics = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('monitor.html', 
                         metrics=metrics,
                         page=page,
                         total_pages=total_pages)
