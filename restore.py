import os
import shutil

DATABASE_FILE = "app.db"
UPLOADS_FOLDER = "uploads"
BACKUP_FOLDER = "backups"


def list_backups():
    if not os.path.exists(BACKUP_FOLDER):
        print("No backups folder found.")
        return []

    backups = [
        folder for folder in os.listdir(BACKUP_FOLDER)
        if folder.startswith("backup_")
    ]

    backups.sort(reverse=True)
    return backups


def restore_backup():
    backups = list_backups()

    if not backups:
        print("No backups available.")
        return

    print("Available backups:")
    for index, backup in enumerate(backups, start=1):
        print(f"{index}. {backup}")

    choice = input("Enter the number of the backup you want to restore: ")

    try:
        choice = int(choice)
        selected_backup = backups[choice - 1]
    except (ValueError, IndexError):
        print("Invalid choice.")
        return

    backup_path = os.path.join(BACKUP_FOLDER, selected_backup)

    confirm = input(
        "This will replace your current app.db and uploads folder. Continue? yes/no: "
    )

    if confirm.lower() != "yes":
        print("Restore cancelled.")
        return

    # Restore database
    backup_db = os.path.join(backup_path, DATABASE_FILE)
    if os.path.exists(backup_db):
        shutil.copy2(backup_db, DATABASE_FILE)
    else:
        print("Warning: No app.db found in selected backup.")

    # Restore uploads folder
    backup_uploads = os.path.join(backup_path, UPLOADS_FOLDER)

    if os.path.exists(backup_uploads):
        if os.path.exists(UPLOADS_FOLDER):
            shutil.rmtree(UPLOADS_FOLDER)

        shutil.copytree(backup_uploads, UPLOADS_FOLDER)
    else:
        print("Warning: No uploads folder found in selected backup.")

    print(f"Restore completed from: {selected_backup}")


if __name__ == "__main__":
    restore_backup()