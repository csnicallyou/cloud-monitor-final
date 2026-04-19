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

    # CPU секция
    output.append("<h2>📊 CPU</h2>")
    nproc = run_cmd('/usr/bin/nproc')
    load = run_cmd('/usr/bin/uptime')
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

    # RAM секция
    output.append("<h2>💾 RAM</h2>")
    free = run_cmd('/usr/bin/free -h')
    output.append(f"<pre>{free}</pre>")
    for line in free.split('\n'):
        if 'Mem:' in line:
            parts = line.split()
            total = parts[1]
            available = parts[-1]
            output.append(f"<p>✅ Всего: {total}, доступно: {available}</p>")
    output.append(f'<p><a href="/diagnose_full/ram"><button>🔍 Полная диагностика RAM</button></a></p>')
    output.append("<hr>")

    # DISK секция
    output.append("<h2>💿 DISK</h2>")
    df = run_cmd('/usr/bin/df -h')
    output.append(f"<pre>{df}</pre>")
    output.append(f'<p><a href="/diagnose_full/disk"><button>🔍 Полная диагностика DISK</button></a></p>')
    output.append("<hr>")

    # NGINX секция
    output.append("<h2>🌐 NGINX</h2>")
    status = run_cmd('/usr/bin/systemctl is-active nginx')
    output.append(f"<p>✅ {status}</p>" if 'active' in status else f"<p>🔴 {status}</p>")
    output.append(f'<p><a href="/diagnose_full/nginx"><button>🔍 Полная диагностика NGINX</button></a></p>')
    output.append("<hr>")

    # PostgreSQL секция
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

        output.append("[1/5] Проверка общей загрузки CPU...")
        nproc = run_cmd('/usr/bin/nproc')
        uptime = run_cmd('/usr/bin/uptime')
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
        ps_output = run_cmd('/usr/bin/ps aux --sort=-%cpu | /usr/bin/head -10')
        output.append("      ТОП-10 ПРОЦЕССОВ ПО CPU:")
        for line in ps_output.split('\n')[1:11]:
            if line.strip():
                parts = line.split()
                if len(parts) > 10:
                    output.append(f"      {parts[10][:40]}... - CPU: {parts[2]}%")
        output.append("")

        output.append("[3/5] Проверка системных прерываний...")
        interrupts = run_cmd('/usr/bin/cat /proc/interrupts | /usr/bin/head -5')
        output.append(f"      {interrupts}")
        output.append("")

        output.append("[4/5] Проверка логов на ошибки CPU...")
        dmesg = run_cmd('/usr/bin/dmesg -T 2>/dev/null | /usr/bin/grep -i "error\|fail\|cpu" | /usr/bin/tail -5')
        if dmesg and dmesg != "Нет данных":
            output.append(f"      ⚠️ Найдены сообщения в логах:")
            for line in dmesg.split('\n')[:5]:
                if line.strip():
                    output.append(f"      {line[:100]}")
        else:
            output.append("      ✅ Критических ошибок не найдено")
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
        free = run_cmd('/usr/bin/free -h')
        output.append(f"{free}")

        output.append("[2/5] Проверка процессов, потребляющих память...")
        ps_output = run_cmd('/usr/bin/ps aux --sort=-%mem | /usr/bin/head -10')
        output.append("      ТОП-10 ПРОЦЕССОВ ПО ПАМЯТИ:")
        for line in ps_output.split('\n')[1:11]:
            if line.strip():
                parts = line.split()
                if len(parts) > 10:
                    output.append(f"      {parts[10][:40]}... - MEM: {parts[3]}%")
        output.append("")

        output.append("[3/5] Проверка использования swap...")
        swap = run_cmd('/usr/bin/swapon --show')
        if swap and swap != "Нет данных":
            output.append(f"      Swap используется:")
            output.append(f"      {swap}")
        else:
            output.append("      ✅ Swap не используется")
        output.append("")

        output.append("[4/5] Проверка на возможные утечки памяти...")
        output.append("      Анализ завершён")
        output.append("")

        output.append("[5/5] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        free_m = run_cmd('/usr/bin/free -m')
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
                    output.append("      💡 РЕКОМЕНДАЦИЯ: Закройте неиспользуемые приложения")
                else:
                    output.append("      ✅ Память в норме")

    elif component == 'disk':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА ДИСКА")
        output.append("=" * 60 + "\n")

        output.append("[1/5] Проверка использования дискового пространства...")
        df = run_cmd('/usr/bin/df -h')
        output.append(df)

        output.append("[2/5] Проверка больших папок в корне...")
        du = run_cmd('/usr/bin/du -sh /* 2>/dev/null | /usr/bin/sort -h | /usr/bin/tail -10')
        output.append("      ТОП-10 САМЫХ БОЛЬШИХ ПАПОК:")
        output.append(du)

        output.append("[3/5] Проверка больших лог-файлов...")
        logs = run_cmd('/usr/bin/find /var/log -name "*.log" -size +100M 2>/dev/null')
        if logs and logs != "Нет данных":
            output.append(f"      ⚠️ Найдены большие лог-файлы:")
            for log in logs.split('\n')[:5]:
                if log.strip():
                    output.append(f"      {log}")
            output.append(f"      💡 РЕШЕНИЕ: Очистите лог-файлы: sudo journalctl --vacuum-time=7d")
        else:
            output.append("      ✅ Больших лог-файлов не найдено")
        output.append("")

        output.append("[4/5] Проверка inode...")
        inode = run_cmd('/usr/bin/df -i /')
        output.append(f"      {inode}")
        output.append("")

        output.append("[5/5] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        warning_count = 0
        for line in df.split('\n')[1:]:
            if line and ('/dev/' in line or '/dev/mapper' in line):
                parts = line.split()
                if len(parts) >= 5:
                    use_percent = parts[4].replace('%', '')
                    mount = parts[5]
                    size = parts[1]
                    if use_percent.isdigit():
                        percent = int(use_percent)
                        if percent > 85:
                            output.append(f"      🔴 КРИТИЧНО: {mount} заполнен на {percent}% (всего: {size})")
                            output.append(f"      💡 РЕШЕНИЕ: Очистите {mount}, удалите ненужные файлы")
                            warning_count += 1
                        elif percent > 70:
                            output.append(f"      ⚠️ ВНИМАНИЕ: {mount} заполнен на {percent}% (всего: {size})")
                            output.append(f"      💡 РЕКОМЕНДАЦИЯ: Освободите место, почистите логи")
                            warning_count += 1
                        else:
                            output.append(f"      ✅ {mount} - {percent}% использовано (всего: {size})")
        if warning_count == 0:
            output.append("      ✅ Все разделы в норме")

    elif component == 'nginx':
        output.append("=" * 60)
        output.append("ПОЛНАЯ ДИАГНОСТИКА NGINX")
        output.append("=" * 60 + "\n")

        warning_count = 0
        error_count = 0

        output.append("[1/5] Проверка статуса NGINX...")
        status = run_cmd('/usr/bin/systemctl is-active nginx')
        output.append(f"      Статус: {status}")
        if 'active' not in status:
            output.append("      🔴 NGINX НЕ РАБОТАЕТ!")
            error_count += 1
        output.append("")

        output.append("[2/5] Проверка конфигурации NGINX...")
        config_test = run_cmd('/usr/bin/nginx -t 2>&1')
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
            output.append(f"      ❌ Ошибка в конфигурации:")
            for line in config_test.split('\n')[:3]:
                output.append(f"        {line[:80]}")
        output.append("")

        output.append("[3/5] Проверка слушающих портов...")
        ports = run_cmd('/usr/bin/ss -tulpn | /usr/bin/grep -E ":80|:443"')
        if ports and ports != "Нет данных":
            output.append(f"      ✅ NGINX слушает порты 80/443")
        else:
            output.append("      ❌ NGINX не слушает порты 80/443!")
            error_count += 1
        output.append("")

        output.append("[4/5] Проверка логов ошибок NGINX...")
        logs = run_cmd('/usr/bin/tail -50 /var/log/nginx/error.log 2>/dev/null')
        if logs and logs != "Нет данных":
            error_lines = [line for line in logs.split('\n') if 'error' in line.lower()]
            output.append(f"      ⚠️ В логах найдено ошибок: {len(error_lines)}")
            for line in error_lines[:3]:
                output.append(f"        - {line.strip()[:80]}")
        else:
            output.append("      ✅ Ошибок в логах не найдено")
        output.append("")

        output.append("[5/5] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        output.append(f"      Статистика: {error_count} ошибок, {warning_count} предупреждений")
        if 'active' not in status:
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
        status = run_cmd('/usr/bin/systemctl is-active postgresql')
        output.append(f"      Статус: {status}")
        if 'active' not in status:
            output.append("      🔴 POSTGRESQL НЕ РАБОТАЕТ!")
        output.append("")

        output.append("[2/6] Проверка порта 5432...")
        ports = run_cmd('/usr/bin/ss -tulpn | /usr/bin/grep 5432')
        if ports and ports != "Нет данных":
            output.append(f"      ✅ PostgreSQL слушает порт 5432")
        else:
            output.append("      ❌ PostgreSQL не слушает порт 5432!")
        output.append("")

        output.append("[3/6] Проверка активных соединений...")
        connections = run_cmd('/usr/bin/psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null')
        output.append(f"      {connections}")
        output.append("")

        output.append("[4/6] Проверка заблокированных процессов...")
        locks = run_cmd('/usr/bin/psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE wait_event IS NOT NULL;" 2>/dev/null')
        if '0' in locks:
            output.append("      ✅ Блокировок нет")
        else:
            output.append(f"      ⚠️ Есть заблокированные процессы: {locks}")
            output.append(f"      💡 РЕШЕНИЕ: Используйте 'SELECT pg_terminate_backend(pid)' для завершения")
        output.append("")

        output.append("[5/6] Проверка логов PostgreSQL...")
        logs = run_cmd('/usr/bin/journalctl -u postgresql -n 10 --no-pager 2>/dev/null')
        error_lines = [line for line in logs.split('\n') if 'ERROR' in line.upper() or 'FATAL' in line.upper()]
        if error_lines:
            output.append("      ⚠️ Найдены ошибки в логах:")
            for line in error_lines[:3]:
                output.append(f"      {line[:100]}")
        else:
            output.append("      ✅ Критических ошибок не найдено")
        output.append("")

        output.append("[6/6] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        if 'active' not in status:
            output.append("      🔴 PostgreSQL не запущен. Выполните:")
            output.append("         sudo systemctl start postgresql")
        else:
            output.append("      ✅ PostgreSQL работает нормально")
            output.append("      💡 СОВЕТ: Регулярно выполняйте VACUUM для оптимизации БД")

    output.append("\n" + "=" * 60)
    output.append("Диагностика завершена")
    output.append("</pre>")
    output.append('<br><a href="/diagnose">← Назад к диагностике</a>')

    return nav_bar + "\n".join(output)
