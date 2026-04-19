from flask import Blueprint, request, redirect, url_for, send_file, flash, get_flashed_messages, Response, current_app
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import zipfile
import io
from utils.db import get_db_connection
from utils.helpers import human_readable_size

cloud_bp = Blueprint('cloud', __name__, url_prefix='')

def get_nav_bar():
    return '''
    <div style="background: #f0f0f0; padding: 10px; margin-bottom: 20px;">
        <a href="/">☁️ Облако</a>
        <a href="/monitor">📊 Мониторинг</a>
        <a href="/diagnose">🔍 Диагностика</a>
    </div>
    '''

@cloud_bp.route('/')
def index():
    nav_bar = get_nav_bar()
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    sort_by = request.args.get('sort', 'date_desc')
    sort_map = {
        'name_asc': 'name ASC',
        'name_desc': 'name DESC',
        'date_asc': 'uploaded_at ASC',
        'date_desc': 'uploaded_at DESC',
        'size_asc': 'size_bytes ASC',
        'size_desc': 'size_bytes DESC'
    }
    order_by = sort_map.get(sort_by, 'uploaded_at DESC')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM files")
    total = cur.fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    cur.execute(f"""
        SELECT id, name, size_bytes, uploaded_at
        FROM files
        ORDER BY {order_by}
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    file_list = ''
    for row in rows:
        file_list += f'''
        <li>
            <input type="checkbox" class="file-checkbox" value="{row[0]}">
            {row[1]} ({human_readable_size(row[2])}) - {row[3]}
            - <a href="/download/{row[0]}">📥 Скачать</a>
            - <a href="#" onclick="confirmDelete({row[0]})">🗑️ Удалить</a>
        </li>'''

    pagination = ''
    if page > 1:
        pagination += f'<a href="?sort={sort_by}&page={page-1}">◀ Предыдущая</a> '
    pagination += f'Страница {page} из {total_pages} '
    if page < total_pages:
        pagination += f'<a href="?sort={sort_by}&page={page+1}">Следующая ▶</a>'

    sort_buttons = f'''
    <div style="margin: 10px 0;">
        <strong>📂 Сортировать:</strong>
        <a href="?sort=name_asc&page={page}">📝 Имя А-Я</a> |
        <a href="?sort=name_desc&page={page}">📝 Имя Я-А</a> |
        <a href="?sort=date_desc&page={page}">📅 Новые</a> |
        <a href="?sort=date_asc&page={page}">📅 Старые</a> |
        <a href="?sort=size_desc&page={page}">📊 Большие</a> |
        <a href="?sort=size_asc&page={page}">📊 Маленькие</a>
    </div>
    '''

    js_script = '''
    <script>
    function selectAll() {
        document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = true);
    }
    function deselectAll() {
        document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = false);
    }
    function deleteSelected() {
        const checkboxes = document.querySelectorAll('.file-checkbox:checked');
        if (checkboxes.length === 0) {
            alert('Выберите файлы для удаления');
            return;
        }
        if (confirm(`Удалить ${checkboxes.length} файл(ов)?`)) {
            const ids = Array.from(checkboxes).map(cb => cb.value);
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/delete_multiple';
            ids.forEach(id => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'file_ids';
                input.value = id;
                form.appendChild(input);
            });
            document.body.appendChild(form);
            form.submit();
        }
    }
    function downloadSelected() {
        const checkboxes = document.querySelectorAll('.file-checkbox:checked');
        if (checkboxes.length === 0) {
            alert('Выберите файлы для скачивания');
            return;
        }
        const ids = Array.from(checkboxes).map(cb => cb.value);
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/download_multiple';
        ids.forEach(id => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'file_ids';
            input.value = id;
            form.appendChild(input);
        });
        document.body.appendChild(form);
        form.submit();
    }
    function confirmDelete(file_id) {
        if (confirm('Удалить этот файл?')) {
            window.location.href = '/delete/' + file_id;
        }
    }
    </script>
    '''

    flash_html = ''
    flashes = get_flashed_messages(with_categories=True)
    for category, message in flashes:
        color = '#d4edda' if category == 'success' else '#fff3cd'
        flash_html += f'<div style="background:{color}; padding:10px; margin:10px 0;">{message}</div>'

    return nav_bar + js_script + f'''
    <h1>Cloud Lab - Multiple Upload & Select</h1>
    {flash_html}
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="files" multiple>
        <input type="submit" value="Upload Files (multiple)">
    </form>
    <div style="margin: 15px 0;">
        <button onclick="selectAll()">✅ Выделить всё</button>
        <button onclick="deselectAll()">❌ Снять выделение</button>
        <button onclick="deleteSelected()">🗑️ Удалить выбранные</button>
        <button onclick="downloadSelected()">📦 Скачать выбранные (ZIP)</button>
    </div>
    <h2>Files:</h2>
    {sort_buttons}
    <ul>{file_list}</ul>
    <div>{pagination}</div>
    '''

@cloud_bp.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist('files')
    if not uploaded_files or uploaded_files[0].filename == '':
        flash('No files selected', 'warning')
        return redirect(url_for('cloud.index'))
    
    saved_count = 0
    errors = []
    
    for file in uploaded_files:
        if file and file.filename:
            safe_filename = secure_filename(file.filename)
            if not safe_filename:
                errors.append(f"Invalid: {file.filename}")
                continue
            
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
            if os.path.exists(filepath):
                errors.append(f"{safe_filename} (exists)")
                continue
            
            file.save(filepath)
            size = os.path.getsize(filepath)
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO files (name, size_bytes, uploaded_at) VALUES (%s, %s, %s)",
                (safe_filename, size, datetime.now())
            )
            conn.commit()
            cur.close()
            conn.close()
            saved_count += 1
    
    if saved_count > 0:
        flash(f'✅ Uploaded {saved_count} file(s)', 'success')
    if errors:
        flash(f'⚠️ Errors: {", ".join(errors[:3])}', 'warning')
    
    return redirect(url_for('cloud.index'))

@cloud_bp.route('/delete_multiple', methods=['POST'])
def delete_multiple():
    file_ids = request.form.getlist('file_ids')
    deleted_count = 0
    errors = []
    
    conn = get_db_connection()
    for file_id in file_ids:
        cur = conn.cursor()
        cur.execute("SELECT name FROM files WHERE id = %s", (file_id,))
        row = cur.fetchone()
        if row:
            filename = row[0]
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            cur.execute("DELETE FROM files WHERE id = %s", (file_id,))
            conn.commit()
            deleted_count += 1
        else:
            errors.append(f"ID {file_id} not found")
        cur.close()
    conn.close()
    
    if deleted_count > 0:
        flash(f'✅ Deleted {deleted_count} file(s)', 'success')
    if errors:
        flash(f'⚠️ Errors: {", ".join(errors)}', 'warning')
    
    return redirect(url_for('cloud.index'))

@cloud_bp.route('/download_multiple', methods=['POST'])
def download_multiple():
    file_ids = request.form.getlist('file_ids')
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        conn = get_db_connection()
        for file_id in file_ids:
            cur = conn.cursor()
            cur.execute("SELECT name FROM files WHERE id = %s", (file_id,))
            row = cur.fetchone()
            cur.close()
            if row:
                filename = row[0]
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    zip_file.write(filepath, filename)
        conn.close()
    
    zip_buffer.seek(0)
    return Response(
        zip_buffer,
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename=cloud_files_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'}
    )

@cloud_bp.route('/download/<int:file_id>')
def download(file_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM files WHERE id = %s", (file_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        filename = row[0]
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=filename)
    return "File not found", 404

@cloud_bp.route('/delete/<int:file_id>')
def delete_file(file_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM files WHERE id = %s", (file_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return "File not found", 404
    filename = row[0]
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    cur.execute("DELETE FROM files WHERE id = %s", (file_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash(f'✅ Deleted: {filename}', 'success')
    return redirect(url_for('cloud.index'))
