"""Скрипт для создания резервных копий приложения Historical Display."""
import os
import shutil
import zipfile
from datetime import datetime

BACKUP_DIR = "backups"
APP_FILES = [
    "historical_display_gui.py",
    "logging_config.py",
]

def create_backup():
    """Создать резервную копию приложения."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"historical_display_backup_{timestamp}"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(backup_path, exist_ok=True)
    
    for file_name in APP_FILES:
        if os.path.exists(file_name):
            shutil.copy2(file_name, backup_path)
            print(f"  + {file_name}")
    
    settings_dir = "settings"
    if os.path.exists(settings_dir):
        settings_backup = os.path.join(backup_path, settings_dir)
        shutil.copytree(settings_dir, settings_backup)
        print(f"  + {settings_dir}/")
    
    mascot_dir = "Маскот"
    if os.path.exists(mascot_dir):
        mascot_backup = os.path.join(backup_path, mascot_dir)
        shutil.copytree(mascot_dir, mascot_backup)
        print(f"  + {mascot_dir}/")
    
    archive_path = f"{backup_path}.zip"
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(backup_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BACKUP_DIR)
                zipf.write(file_path, arcname)
    
    shutil.rmtree(backup_path)
    
    print(f"\nBackup created: {archive_path}")
    return archive_path

def list_backups():
    """Показать список доступных резервных копий."""
    if not os.path.exists(BACKUP_DIR):
        print("No backups found.")
        return
    
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.zip')], reverse=True)
    
    if not backups:
        print("No backups found.")
        return
    
    print("\nAvailable backups:")
    for i, backup in enumerate(backups, 1):
        size = os.path.getsize(os.path.join(BACKUP_DIR, backup))
        size_mb = size / (1024 * 1024)
        print(f"  {i}. {backup} ({size_mb:.2f} MB)")

def restore_backup(backup_name):
    """Восстановить приложение из резервной копии."""
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    if not os.path.exists(backup_path):
        print(f"Backup not found: {backup_name}")
        return False
    
    extract_dir = backup_path + "_temp"
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(backup_path, 'r') as zipf:
        zipf.extractall(extract_dir)
    
    for item in os.listdir(extract_dir):
        item_path = os.path.join(extract_dir, item)
        dest_path = os.path.join(os.getcwd(), item)
        
        if os.path.isdir(item_path):
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(item_path, dest_path)
            print(f"  Restored: {item}/")
        else:
            shutil.copy2(item_path, dest_path)
            print(f"  Restored: {item}")
    
    shutil.rmtree(extract_dir)
    print(f"\nBackup restored from: {backup_name}")
    return True

def auto_backup():
    """Создать автоматическую резервную копию перед важными операциями."""
    try:
        return create_backup()
    except Exception as e:
        print(f"Auto-backup failed: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            create_backup()
        elif command == "list":
            list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("Usage:")
            print("  python backup.py create    - Create backup")
            print("  python backup.py list     - List backups")
            print("  python backup.py restore <name> - Restore backup")
    else:
        create_backup()
