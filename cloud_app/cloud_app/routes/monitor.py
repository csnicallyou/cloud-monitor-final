from flask import Blueprint, request
from utils.db import get_db_connection

monitor_bp = Blueprint('monitor', __name__, url_prefix='')

def get_nav_bar():
    return '''
    <div style="background: #f0f0f0; padding: 10px; margin-bottom: 20px;">
        <a href="/">☁️ Облако</a>
        <a href="/monitor">📊 Мониторинг</a>
        <a href="/diagnose">🔍 Диагностика</a>
    </div>
    '''

@monitor_bp.route('/monitor')
def monitor():
    nav_bar = get_nav_bar()
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
    rows = cur.fetchall()
    cur.close()
    conn.close()

    table_rows = ''
    for row in rows:
        table_rows += f'''
        <tr>
            <td>{row[0]}</td>
            <td>{row[1]}%</td>
            <td>{row[2]} MB</td>
            <td>{row[3]} GB</td>
            <td>{row[4]}</td>
            <td>{row[5]}</td>
        </tr>
        '''

    pagination = ''
    if page > 1:
        pagination += f'<a href="?page={page-1}">◀ Предыдущая</a> '
    pagination += f'Страница {page} из {total_pages} '
    if page < total_pages:
        pagination += f'<a href="?page={page+1}">Следующая ▶</a>'

    return nav_bar + f'''
    <h1>Мониторинг сервера</h1>
    <table border="1" cellpadding="5" style="width:100%; border-collapse: collapse;">
        <tr bgcolor="#ddd">
            <th>Время</th> <th>CPU Load</th> <th>RAM Free</th> <th>Disk Free</th> <th>nginx</th> <th>PostgreSQL</th>
        </tr>
        {table_rows}
    </table>
    <div style="margin-top: 15px;">{pagination}</div>
    <br><a href="/">← Назад в облако</a>
    '''
