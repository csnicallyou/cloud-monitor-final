import os
import re

def human_readable_size(size):
    """Convert bytes to human readable format"""
    if size == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def get_file_icon(filename):
    """Return emoji icon based on file extension"""
    ext = os.path.splitext(filename)[1].lower()
    
    icons = {
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', 
        '.svg': '🖼️', '.webp': '🖼️', '.bmp': '🖼️', '.ico': '🖼️',
        '.pdf': '📄', '.txt': '📝', '.md': '📝', '.rtf': '📝',
        '.doc': '📘', '.docx': '📘', '.xls': '📊', '.xlsx': '📊',
        '.ppt': '📙', '.pptx': '📙',
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', 
        '.gz': '📦', '.bz2': '📦',
        '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
        '.json': '📋', '.xml': '📋', '.sql': '🗄️', '.sh': '⚡',
        '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬',
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
        'default': '📎'
    }
    
    return icons.get(ext, icons['default'])

def safe_folder_path(folder):
    """Validate and sanitize folder path"""
    if not folder:
        return '/'
    
    # Запрещаем выход за пределы корня
    if '..' in folder or folder.startswith('../'):
        return '/'
    
    # Убираем множественные слеши
    folder = re.sub(r'/+', '/', folder)
    
    # Убеждаемся, что путь начинается с /
    if not folder.startswith('/'):
        folder = '/' + folder
    
    # Убираем слеш в конце
    if folder.endswith('/') and folder != '/':
        folder = folder[:-1]
    
    return folder

def get_parent_folder(folder):
    """Get parent folder path"""
    if folder == '/':
        return '/'
    return os.path.dirname(folder) or '/'

def get_folder_name(folder):
    """Get display name of folder"""
    if folder == '/':
        return 'Корень'
    return os.path.basename(folder)
