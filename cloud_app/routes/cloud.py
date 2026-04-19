from flask import Blueprint, request, redirect, url_for, send_file, flash, Response, render_template, current_app
from flask_login import login_required, current_user
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import zipfile
import io
from utils.db import get_db_connection
from utils.helpers import human_readable_size, get_file_icon

cloud_bp = Blueprint('cloud', __name__, url_prefix='')

@cloud_bp.route('/')
@login_required
def index():
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
    cur.execute("SELECT COUNT(*) FROM files WHERE user_id = %s", (current_user.id,))
    total = cur.fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    cur.execute(f"""
        SELECT id, name, size_bytes, uploaded_at
        FROM files
        WHERE user_id = %s
        ORDER BY {order_by}
        LIMIT %s OFFSET %s
    """, (current_user.id, per_page, offset))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    files = []
    for row in rows:
        files.append({
            'id': row[0],
            'name': row[1],
            'size': human_readable_size(row[2]),
            'size_bytes': row[2],
            'date': row[3],
            'icon': get_file_icon(row[1])
        })

    return render_template('cloud.html',
                         files=files,
                         page=page,
                         total_pages=total_pages,
                         sort_by=sort_by)

@cloud_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    uploaded_files = request.files.getlist('files')
    if not uploaded_files or uploaded_files[0].filename == '':
        flash('No files selected', 'warning')
        return redirect(url_for('cloud.index'))

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.folder_name)
    os.makedirs(user_folder, exist_ok=True)
    
    saved_count = 0
    errors = []

    for file in uploaded_files:
        if file and file.filename:
            safe_filename = secure_filename(file.filename)
            if not safe_filename:
                errors.append(f"Invalid: {file.filename}")
                continue

            filepath = os.path.join(user_folder, safe_filename)
            if os.path.exists(filepath):
                errors.append(f"{safe_filename} (exists)")
                continue

            file.save(filepath)
            size = os.path.getsize(filepath)

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO files (name, size_bytes, uploaded_at, user_id) VALUES (%s, %s, %s, %s)",
                (safe_filename, size, datetime.now(), current_user.id)
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
@login_required
def delete_multiple():
    file_ids = request.form.getlist('file_ids')
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.folder_name)
    
    deleted_count = 0
    errors = []

    conn = get_db_connection()
    for file_id in file_ids:
        cur = conn.cursor()
        cur.execute("SELECT name FROM files WHERE id = %s AND user_id = %s", (file_id, current_user.id))
        row = cur.fetchone()
        if row:
            filename = row[0]
            filepath = os.path.join(user_folder, filename)
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
@login_required
def download_multiple():
    file_ids = request.form.getlist('file_ids')
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.folder_name)
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        conn = get_db_connection()
        for file_id in file_ids:
            cur = conn.cursor()
            cur.execute("SELECT name FROM files WHERE id = %s AND user_id = %s", (file_id, current_user.id))
            row = cur.fetchone()
            cur.close()
            if row:
                filename = row[0]
                filepath = os.path.join(user_folder, filename)
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
@login_required
def download(file_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM files WHERE id = %s AND user_id = %s", (file_id, current_user.id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        filename = row[0]
        user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.folder_name)
        filepath = os.path.join(user_folder, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=filename)
    return "File not found", 404

@cloud_bp.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM files WHERE id = %s AND user_id = %s", (file_id, current_user.id))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return "File not found", 404
    filename = row[0]
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.folder_name)
    filepath = os.path.join(user_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    cur.execute("DELETE FROM files WHERE id = %s", (file_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash(f'✅ Deleted: {filename}', 'success')
    return redirect(url_for('cloud.index'))
