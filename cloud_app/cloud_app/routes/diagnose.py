from flask import Blueprint, request
from datetime import datetime
import subprocess
import re
import os

diagnose_bp = Blueprint('diagnose', __name__, url_prefix='')

def get_nav_bar():
    return '''
    <div style="background: #f0f0f0; padding: 10px; margin-bottom: 20px;">
        <a href="/">☁️ Облако</a>
        <a href="/monitor">📊 Мониторинг</a>
        <a href="/diagnose">🔍 Диагностика</a>
    </div>
    '''

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, executable='/bin/bash')
        return result.stdout.strip() if result.stdout else result.stderr.strip() or "Нет данных"
    except Exception as e:
        return f"Ошибка: {str(e)}"

@diagnose_bp.route('/diagnose')
def diagnose_page():
    nav_bar = get_nav_bar()
    output = []
    output.append(f"<h1>Диагностика сервера</h1>")
    output.append(f"<p><strong>Время:</strong> {datetime.now()}</p>")
    output.append("<p><a href='/monitor'>← Назад к мониторингу</a> | <a href='/diagnose'>🔄 Обновить</a></p>")

    output.append("<h2>📊 CPU</h2>")
    nproc = run_cmd('/usr/bin/nproc')
    uptime = run_cmd('/usr/bin/uptime')
    output.append(f"<p>Ядер: {nproc}</p>")
    output.append(f"<p>Uptime: {uptime}</p>")
    output.append(f'<p><a href="/diagnose_full/cpu"><button>🔍 Полная диагностика CPU</button></a></p>')
    output.append("<hr>")

    output.append("<h2>💾 RAM</h2>")
    free = run_cmd('/usr/bin/free -h')
    output.append(f"<pre>{free}</pre>")
    output.append(f'<p><a href="/diagnose_full/ram"><button>🔍 Полная диагностика RAM</button></a></p>')
    output.append("<hr>")

    output.append("<h2>💿 DISK</h2>")
    df = run_cmd('/usr/bin/df -h')
    output.append(f"<pre>{df}</pre>")
    output.append(f'<p><a href="/diagnose_full/disk"><button>🔍 Полная диагностика DISK</button></a></p>')
    output.append("<hr>")

    output.append("<h2>🌐 NGINX</h2>")
    status = run_cmd('/usr/bin/systemctl is-active nginx')
    output.append(f"<p>✅ {status}</p>" if 'active' in status else f"<p>🔴 {status}</p>")
    output.append(f'<p><a href="/diagnose_full/nginx"><button>🔍 Полная диагностика NGINX</button></a></p>')
    output.append("<hr>")

    output.append("<h2>🐘 PostgreSQL</h2>")
    status = run_cmd('/usr/bin/systemctl is-active postgresql')
    output.append(f"<p>✅ {status}</p>" if 'active' in status else f"<p>🔴 {status}</p>")
    output.append(f'<p><a href="/diagnose_full/postgres"><button>🔍 Полная диагностика PostgreSQL</button></a></p>')

    return nav_bar + "\n".join(output)

@diagnose_bp.route('/diagnose_full/<component>')
def diagnose_full(component):
    nav_bar = get_nav_bar()
    output = []
    output.append(f"<h1>Полная диагностика: {component.upper()}</h1>")
    output.append(f"<p><strong>Время:</strong> {datetime.now()}</p>")
    output.append("<pre>")

    if component == 'cpu':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА CPU")
        output.append("=" * 60 + "\n")
        nproc = run_cmd('/usr/bin/nproc')
        uptime = run_cmd('/usr/bin/uptime')
        output.append(f"Количество ядер: {nproc}")
        output.append(f"Uptime: {uptime}")
        output.append("\nТОП-10 процессов по CPU:")
        ps_output = run_cmd('/usr/bin/ps aux --sort=-%cpu | /usr/bin/head -10')
        output.append(ps_output)

    elif component == 'ram':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА RAM")
        output.append("=" * 60 + "\n")
        free = run_cmd('/usr/bin/free -h')
        output.append(free)
        output.append("\nТОП-10 процессов по памяти:")
        ps_output = run_cmd('/usr/bin/ps aux --sort=-%mem | /usr/bin/head -10')
        output.append(ps_output)

    elif component == 'disk':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА ДИСКА")
        output.append("=" * 60 + "\n")
        df = run_cmd('/usr/bin/df -h')
        output.append(df)
        output.append("\nСамые большие папки в /home:")
        du = run_cmd('/usr/bin/du -sh /home/* 2>/dev/null | /usr/bin/sort -h | /usr/bin/tail -5')
        output.append(du)

    elif component == 'nginx':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА NGINX")
        output.append("=" * 60 + "\n")
        status = run_cmd('/usr/bin/systemctl status nginx --no-pager | /usr/bin/head -15')
        output.append(status)

    elif component == 'postgres':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА POSTGRESQL")
        output.append("=" * 60 + "\n")
        os.environ['PGPASSWORD'] = 'postgres'
        status = run_cmd('/usr/bin/systemctl status postgresql --no-pager | /usr/bin/head -15')
        output.append(status)

    output.append("</pre>")
    output.append('<br><a href="/diagnose">← Назад к диагностике</a>')
    return nav_bar + "\n".join(output)
