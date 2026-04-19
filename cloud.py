from flask import Flask, request, redirect, url_for
import os
import psycopg2
import subprocess
from datetime import datetime


def human_readable_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024**3:.1f} GB"



app = Flask(__name__)

UPLOAD_FOLDER = '/home/csn/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Подключение к PostgreSQL
conn = psycopg2.connect(
    host='localhost',
    database='cloud_lab',
    user='cloud_user',
    password='lab123'
)

# Навигация
NAV_BAR = '''
<div style="background: #f0f0f0; padding: 10px; margin-bottom: 20px;">
    <a href="/" style="margin-right: 20px;">☁️ Облако</a>
    <a href="/monitor" style="margin-right: 20px;">📊 Мониторинг</a>
    <a href="/diagnose" style="margin-right: 20px;">🔍 Диагностика</a>

</div>
'''

@app.route('/')
def index():
    cur = conn.cursor()
    cur.execute("SELECT id, name, size_bytes, uploaded_at FROM files ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()

    file_list = ''
    for row in rows:
        file_list += f'<li>{row[1]} ({human_readable_size(row[2])}) - uploaded at {row[3]}</li>'

    return NAV_BAR + f'''
    <h1>Cloud Lab</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <h2>Files:</h2>
    <ul>
        {file_list}
    </ul>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        size = os.path.getsize(filepath)

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO files (name, size_bytes, uploaded_at) VALUES (%s, %s, %s)",
            (filename, size, datetime.now())
        )
        conn.commit()
        cur.close()

        return redirect(url_for('index'))
    return 'No file uploaded'

# ========== СТРАНИЦА МОНИТОРИНГА ==========

@app.route('/monitor')
def monitor():
    page = request.args.get('page', 1, type=int)
    limit = 10
    offset = (page - 1) * limit

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

    return NAV_BAR + f'''
    <h1>Мониторинг сервера</h1>

    <table border="1" cellpadding="5" style="width:100%; border-collapse: collapse;">
        <tr bgcolor="#ddd">
            <th>Время</th> <th>CPU Load</th> <th>RAM Free</th> <th>Disk Free</th> <th>nginx</th> <th>PostgreSQL</th>
        <tr>
        {table_rows}
    </table>

    <div style="margin-top: 15px;">
        {pagination}
    </div>

    <br>
    <a href="/">← Назад в облако</a>
    '''

# ========== СТРАНИЦА ДИАГНОСТИКИ (С КНОПКАМИ) ==========

@app.route('/diagnose')
def diagnose_page():
    import re

    output = []
    output.append(f"<h1>Диагностика сервера</h1>")
    output.append(f"<p><strong>Время:</strong> {datetime.now()}</p>")
    output.append("<p><a href='/monitor'>← Назад к мониторингу</a> | <a href='/diagnose'>🔄 Обновить</a></p>")

    # 1. CPU секция
    output.append("<h2>📊 CPU</h2>")
    nproc = subprocess.run('nproc', capture_output=True, text=True, shell=True).stdout.strip()
    load = subprocess.run('uptime', capture_output=True, text=True, shell=True).stdout
    load_vals = re.findall(r'load average: ([\d.]+), ([\d.]+), ([\d.]+)', load)
    if load_vals:
        load_1 = float(load_vals[0][0])
        if load_1 > int(nproc):
            output.append(f"<p>🔴 КРИТИЧНО: load average {load_1} превышает количество ядер ({nproc})</p>")
        elif load_1 > int(nproc) * 0.7:
            output.append(f"<p>⚠️ ВНИМАНИЕ: load average {load_1} близок к пределу ({nproc} ядер)</p>")
        else:
            output.append(f"<p>✅ НОРМА: load average {load_1} (ядер: {nproc})</p>")
    output.append(f'<p><a href="/diagnose_full/cpu"><button>🔍 Полная диагностика CPU</button></a></p>')
    output.append("<hr>")

    # 2. RAM секция
    output.append("<h2>💾 RAM</h2>")
    free = subprocess.run('free -h', capture_output=True, text=True, shell=True).stdout
    output.append("<pre>")
    output.append(free)
    output.append("</pre>")
    for line in free.split('\n'):
        if 'Mem:' in line:
            parts = line.split()
            total = parts[1]
            available = parts[-1]
            output.append(f"<p>✅ Использовано: всего {total}, доступно {available}</p>")
    output.append(f'<p><a href="/diagnose_full/ram"><button>🔍 Полная диагностика RAM</button></a></p>')
    output.append("<hr>")

        # 3. DISK секция
    output.append("<h2>💿 DISK</h2>")
    df = subprocess.run('df -h', capture_output=True, text=True, shell=True).stdout
    output.append("<pre>")
    output.append(df)
    output.append("</pre>")
    
    # Анализ реальных разделов (исключая виртуальные, но включая /tmp)
    has_problem = False
    critical = False
    
    for line in df.split('\n')[1:]:
        if not line:
            continue
        
        # Исключаем виртуальные разделы, НО оставляем /tmp
        if 'tmpfs' in line and '/tmp' not in line:
            continue
        if 'devtmpfs' in line or 'efivarfs' in line or 'none' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 5:
            use_percent = parts[4].replace('%', '')
            mount = parts[5]
            size = parts[1]
            available = parts[3]
            
            if use_percent.isdigit():
                percent = int(use_percent)
                if percent > 85:
                    output.append(f"<p>🔴 КРИТИЧНО: {mount} - {percent}% использовано (всего: {size}, свободно: {available})</p>")
                    critical = True
                    has_problem = True
                elif percent > 70:
                    output.append(f"<p>⚠️ ВНИМАНИЕ: {mount} - {percent}% использовано (всего: {size}, свободно: {available})</p>")
                    has_problem = True
                else:
                    output.append(f"<p>✅ {mount} - {percent}% использовано (всего: {size}, свободно: {available})</p>")
    
    if not has_problem:
        output.append("<p>✅ Все разделы в норме</p>")
    elif critical:
        output.append("<p>💡 Требуется срочная очистка диска</p>")
    else:
        output.append("<p>💡 Рекомендуется очистить диск</p>")

    output.append(f'<p><a href="/diagnose_full/disk"><button>🔍 Полная диагностика DISK</button></a></p>')
    output.append("<hr>")

    # 4. NGINX секция
    output.append("<h2>🌐 NGINX</h2>")
    status = subprocess.run('systemctl is-active nginx', capture_output=True, text=True, shell=True).stdout.strip()
    if status == 'active':
        output.append("<p>✅ РАБОТАЕТ</p>")
    else:
        output.append(f"<p>🔴 НЕ РАБОТАЕТ (статус: {status})</p>")
    output.append(f'<p><a href="/diagnose_full/nginx"><button>🔍 Полная диагностика NGINX</button></a></p>')
    output.append("<hr>")

    # 5. PostgreSQL секция
    output.append("<h2>🐘 PostgreSQL</h2>")
    status = subprocess.run('systemctl is-active postgresql', capture_output=True, text=True, shell=True).stdout.strip()
    if status == 'active':
        output.append("<p>✅ РАБОТАЕТ</p>")
    else:
        output.append(f"<p>🔴 НЕ РАБОТАЕТ (статус: {status})</p>")
    output.append(f'<p><a href="/diagnose_full/postgres"><button>🔍 Полная диагностика PostgreSQL</button></a></p>')

    return NAV_BAR + "\n".join(output)


# ========== ПОЛНАЯ ДИАГНОСТИКА ==========

@app.route('/diagnose_full/<component>')
def diagnose_full(component):
    import re

    output = []
    output.append(f"<h1>Полная диагностика: {component.upper()}</h1>")
    output.append(f"<p><strong>Время:</strong> {datetime.now()}</p>")
    output.append("<pre>")

    if component == 'cpu':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА CPU")
        output.append("=" * 60 + "\n")

        output.append("[1/5] Проверка общей загрузки CPU...")
        nproc = subprocess.run('nproc', capture_output=True, text=True, shell=True).stdout.strip()
        uptime = subprocess.run('uptime', capture_output=True, text=True, shell=True).stdout.strip()
        output.append(f"      {uptime}")
        output.append(f"      Количество ядер: {nproc}")

        load_vals = re.findall(r'load average: ([\d.]+), ([\d.]+), ([\d.]+)', uptime)
        if load_vals:
            load_1 = float(load_vals[0][0])
            if load_1 > int(nproc):
                output.append(f"      🔴 ПРОБЛЕМА: load average ({load_1}) превышает количество ядер ({nproc})")
                output.append(f"      💡 РЕШЕНИЕ: Проверьте процессы через 'top', увеличьте количество ядер")
            elif load_1 > int(nproc) * 0.7:
                output.append(f"      ⚠️ ВНИМАНИЕ: load average ({load_1}) близок к пределу ({nproc} ядер)")
                output.append(f"      💡 РЕШЕНИЕ: Следите за нагрузкой, возможна оптимизация")
            else:
                output.append(f"      ✅ НОРМА: load average ({load_1}) в пределах нормы")
        output.append("")

        output.append("[2/5] Проверка процессов, потребляющих CPU...")
        ps_output = subprocess.run('ps aux --sort=-%cpu | head -10', capture_output=True, text=True, shell=True).stdout
        output.append("      ТОП-10 ПРОЦЕССОВ ПО CPU:")
        for line in ps_output.split('\n')[1:11]:
            if line.strip():
                parts = line.split()
                if len(parts) > 10:
                    output.append(f"      {parts[10][:40]}... - CPU: {parts[2]}%")
        output.append("")

        output.append("[3/5] Проверка системных прерываний...")
        interrupts = subprocess.run('cat /proc/interrupts | head -5', capture_output=True, text=True, shell=True).stdout
        output.append(f"      {interrupts.strip()}")
        output.append("")

        output.append("[4/5] Проверка логов на ошибки CPU...")
        dmesg = subprocess.run('dmesg -T | grep -i "cpu" | tail -5', capture_output=True, text=True, shell=True).stdout
        if dmesg.strip():
            output.append(f"      ⚠️ Найдены сообщения в логах:")
            for line in dmesg.split('\n')[:5]:
                if line.strip():
                    output.append(f"      {line[:100]}")
        else:
            output.append("      ✅ Ошибок не найдено")
        output.append("")

        output.append("[5/5] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        if load_vals and float(load_vals[0][0]) > int(nproc):
            output.append("      🔴 Сервер перегружен! Что делать:")
            output.append("         1. Запустите 'top' и найдите процессы, потребляющие CPU")
            output.append("         2. Если это PostgreSQL - оптимизируйте запросы")
            output.append("         3. Если это Python - проверьте код на утечки")
            output.append("         4. Рассмотрите увеличение количества ядер")
        else:
            output.append("      ✅ Всё работает нормально")

    elif component == 'ram':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА RAM")
        output.append("=" * 60 + "\n")

        output.append("[1/5] Проверка общего использования RAM...")
        free = subprocess.run('free -h', capture_output=True, text=True, shell=True).stdout
        output.append(f"{free}")

        output.append("[2/5] Проверка процессов, потребляющих память...")
        ps_output = subprocess.run('ps aux --sort=-%mem | head -10', capture_output=True, text=True, shell=True).stdout
        output.append("      ТОП-10 ПРОЦЕССОВ ПО ПАМЯТИ:")
        for line in ps_output.split('\n')[1:11]:
            if line.strip():
                parts = line.split()
                if len(parts) > 10:
                    output.append(f"      {parts[10][:40]}... - MEM: {parts[3]}%")
        output.append("")

        output.append("[3/5] Проверка использования swap...")
        swap = subprocess.run('swapon --show', capture_output=True, text=True, shell=True).stdout
        if swap.strip():
            output.append(f"      Swap используется:")
            output.append(f"      {swap}")
        else:
            output.append("      ✅ Swap не используется")
        output.append("")

        output.append("[4/5] Проверка на возможные утечки памяти...")
        output.append("      Анализ завершён")
        output.append("")

        output.append("[5/5] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        free_m = subprocess.run('free -m', capture_output=True, text=True, shell=True).stdout
        for line in free_m.split('\n'):
            if 'Mem:' in line:
                parts = line.split()
                total = int(parts[1])
                available = int(parts[-1])
                percent = (total - available) / total * 100
                if percent > 90:
                    output.append("      🔴 КРИТИЧЕСКАЯ НЕХВАТКА ПАМЯТИ! Что делать:")
                    output.append("         1. Добавьте оперативной памяти серверу")
                    output.append("         2. Проверьте процессы на утечки памяти")
                elif percent > 75:
                    output.append("      ⚠️ ВНИМАНИЕ: Память под нагрузкой")
                else:
                    output.append("      ✅ Память в норме")

    elif component == 'disk':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА ДИСКА")
        output.append("=" * 60 + "\n")

        output.append("[1/5] Проверка использования дискового пространства...")
        df = subprocess.run('df -h', capture_output=True, text=True, shell=True).stdout
        output.append(df)

        output.append("[2/5] Проверка больших папок в корне...")
        du = subprocess.run('du -sh /* 2>/dev/null | sort -h | tail -10', capture_output=True, text=True, shell=True).stdout
        output.append("      ТОП-10 САМЫХ БОЛЬШИХ ПАПОК:")
        output.append(du)

        output.append("[3/5] Проверка больших лог-файлов...")
        logs = subprocess.run('find /var/log -name "*.log" -size +100M 2>/dev/null', capture_output=True, text=True, shell=True).stdout
        if logs.strip():
            output.append(f"      ⚠️ Найдены большие лог-файлы:")
            for log in logs.split('\n')[:5]:
                if log.strip():
                    output.append(f"      {log}")
        else:
            output.append("      ✅ Больших лог-файлов не найдено")
        output.append("")

        output.append("[4/5] Проверка inode...")
        inode = subprocess.run('df -i /', capture_output=True, text=True, shell=True).stdout
        output.append(f"      {inode.strip()}")
        output.append("")

        output.append("[5/5] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        warning_count = 0
        for line in df.split('\n')[1:]:
            if line and '/dev/' in line:
                parts = line.split()
                if len(parts) >= 5:
                    use_percent = parts[4].replace('%', '')
                    mount = parts[5]
                    if use_percent.isdigit() and int(use_percent) > 85:
                        output.append(f"      🔴 КРИТИЧНО: {mount} заполнен на {use_percent}%")
                        output.append(f"      💡 РЕШЕНИЕ: Очистите {mount}")
                        warning_count += 1
                    elif int(use_percent) > 70:
                        output.append(f"      ⚠️ ВНИМАНИЕ: {mount} заполнен на {use_percent}%")
                        warning_count += 1
        if warning_count == 0:
            output.append("      ✅ Диски в норме")

    elif component == 'nginx':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА NGINX")
        output.append("=" * 60 + "\n")

        warning_count = 0
        error_count = 0

        output.append("[1/5] Проверка статуса NGINX...")
        status = subprocess.run('systemctl is-active nginx', capture_output=True, text=True, shell=True).stdout.strip()
        output.append(f"      Статус: {status}")
        if status != 'active':
            output.append("      🔴 NGINX НЕ РАБОТАЕТ!")
            error_count += 1
        output.append("")

        output.append("[2/5] Проверка конфигурации NGINX...")
        config_test = subprocess.run('nginx -t 2>&1', capture_output=True, text=True, shell=True).stdout
        if 'successful' in config_test and 'error' not in config_test.lower():
            output.append("      ✅ Конфигурация верна")
        elif 'warn' in config_test.lower():
            warn_lines = [line for line in config_test.split('\n') if 'warn' in line.lower()]
            warning_count += len(warn_lines)
            output.append(f"      ⚠️ Есть {len(warn_lines)} предупреждений, но конфиг работает")
            for line in warn_lines[:3]:
                output.append(f"        - {line.strip()[:80]}")
        else:
            error_count += 1
            output.append(f"      ❌ Ошибка в конфигурации")
        output.append("")

        output.append("[3/5] Проверка слушающих портов...")
        ports = subprocess.run('ss -tulpn | grep -E ":80|:443"', capture_output=True, text=True, shell=True).stdout
        if ports.strip():
            output.append(f"      ✅ NGINX слушает порты 80/443")
        else:
            output.append("      ❌ NGINX не слушает порты 80/443!")
            error_count += 1
        output.append("")

        output.append("[4/5] Проверка логов ошибок NGINX...")
        logs = subprocess.run('tail -50 /var/log/nginx/error.log 2>/dev/null', capture_output=True, text=True, shell=True).stdout
        if logs.strip():
            error_lines = [line for line in logs.split('\n') if 'error' in line.lower()]
            output.append(f"      ⚠️ В логах найдено ошибок: {len(error_lines)}")
            for line in error_lines[:3]:
                output.append(f"        - {line.strip()[:80]}")
        else:
            output.append("      ✅ Ошибок в логах не найдено")
        output.append("")

        output.append("[5/5] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        output.append(f"      Статистика: {error_count} ошибок, {warning_count} предупреждений")
        if status != 'active':
            output.append("      🔴 NGINX не запущен. Выполните:")
            output.append("         sudo systemctl start nginx")
        elif error_count > 0:
            output.append("      🔴 Обнаружены ошибки. Что делать:")
            output.append("         1. Проверьте конфигурацию: sudo nginx -t")
            output.append("         2. Посмотрите логи: tail -f /var/log/nginx/error.log")
            output.append("         3. Исправьте ошибки и перезапустите: sudo systemctl restart nginx")
        elif warning_count > 0:
            output.append("      ⚠️ Обнаружены предупреждения. Рекомендации:")
            output.append("         1. Предупреждения не критичны, но их стоит устранить")
            output.append("         2. Запустите sudo nginx -t для деталей")
        else:
            output.append("      ✅ NGINX работает нормально")

    elif component == 'postgres':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА POSTGRESQL")
        output.append("=" * 60 + "\n")

        os.environ['PGPASSWORD'] = 'postgres'

        output.append("[1/6] Проверка статуса PostgreSQL...")
        status = subprocess.run('systemctl is-active postgresql', capture_output=True, text=True, shell=True).stdout.strip()
        output.append(f"      Статус: {status}")
        if status != 'active':
            output.append("      🔴 POSTGRESQL НЕ РАБОТАЕТ!")
        output.append("")

        output.append("[2/6] Проверка порта 5432...")
        ports = subprocess.run('ss -tulpn | grep 5432', capture_output=True, text=True, shell=True).stdout
        if ports.strip():
            output.append(f"      ✅ PostgreSQL слушает порт 5432")
        else:
            output.append("      ❌ PostgreSQL не слушает порт 5432!")
        output.append("")

        output.append("[3/6] Проверка активных соединений...")
        connections = subprocess.run('psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null', capture_output=True, text=True, shell=True).stdout
        output.append(f"      {connections}")
        output.append("")

        output.append("[4/6] Проверка заблокированных процессов...")
        locks = subprocess.run('psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE wait_event IS NOT NULL;" 2>/dev/null', capture_output=True, text=True, shell=True).stdout
        if '0' in locks:
            output.append("      ✅ Блокировок нет")
        else:
            output.append(f"      ⚠️ Есть заблокированные процессы")
        output.append("")

        output.append("[5/6] Проверка логов PostgreSQL...")
        logs = subprocess.run('journalctl -u postgresql -n 10 --no-pager 2>/dev/null', capture_output=True, text=True, shell=True).stdout
        error_lines = [line for line in logs.split('\n') if 'ERROR' in line.upper() or 'FATAL' in line.upper()]
        if error_lines:
            output.append("      ⚠️ Найдены ошибки в логах:")
            for line in error_lines[:3]:
                output.append(f"      {line[:100]}")
        else:
            output.append("      ✅ Критических ошибок не найдено")
        output.append("")

        output.append("[6/6] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        if status != 'active':
            output.append("      🔴 PostgreSQL не запущен. Выполните:")
            output.append("         sudo systemctl start postgresql")
        else:
            output.append("      ✅ PostgreSQL работает нормально")

    output.append("\n" + "=" * 60)
    output.append("Диагностика завершена")
    output.append("</pre>")
    output.append('<br><a href="/diagnose">← Назад к диагностике</a>')

    return NAV_BAR + "\n".join(output)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
# Test comment
# CI/CD test Sun Apr 19 12:30:09 MSK 2026
# CI/CD with systemd works perfectly
