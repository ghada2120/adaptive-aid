import os
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

DATABASE_FILE = "app.db"
UPLOADS_FOLDER = "uploads"
BACKUP_FOLDER = "backups"

# Set your timezone (Saudi Arabia example)
TIMEZONE = ZoneInfo("Asia/Riyadh")


def create_backup():
    now = datetime.now(TIMEZONE)

    # Format: dd-mm-yyyy_HH-MM-SS
    timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")

    backup_path = os.path.join(BACKUP_FOLDER, f"backup_{timestamp}")

    os.makedirs(backup_path, exist_ok=True)

    # Backup database
    if os.path.exists(DATABASE_FILE):
        shutil.copy2(DATABASE_FILE, os.path.join(backup_path, DATABASE_FILE))
    else:
        print("Warning: app.db not found.")

    # Backup uploads folder
    if os.path.exists(UPLOADS_FOLDER):
        shutil.copytree(
            UPLOADS_FOLDER,
            os.path.join(backup_path, UPLOADS_FOLDER)
        )
    else:
        print("Warning: uploads folder not found.")

    print(f"Backup created at: {backup_path}")


if __name__ == "__main__":
    create_backup()