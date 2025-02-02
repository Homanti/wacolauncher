import os
import shutil
import zipfile
from cx_Freeze import setup, Executable
import sys

def zip_directory_contents(folder_path, zip_filename):
    folder_path = folder_path.rstrip(os.sep)
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            relative_path = os.path.relpath(root, folder_path)
            for file in files:
                file_path = os.path.join(root, file)
                if relative_path == '.':
                    arcname = file
                else:
                    arcname = os.path.join(relative_path, file)
                zipf.write(file_path, arcname)

choice = int(input("1 - Wacolauncher, 2 - update "))

if choice == 1:
    base = None
    if sys.platform == "win32":
        base = "Win32GUI"

    build_exe_options = {
        "packages": ["keyring", "keyrings.alt"],
        "excludes": ["tkinter"],
        "build_exe": "build/wacolauncher"
    }

    setup(
        name="WacoLauncher",
        version="3.0.0",
        description="Лаунчер для WacoRP",
        options={"build_exe": build_exe_options},
        executables=[Executable("src/wacolauncher.py", base=base, icon="gitignore/setup/icon.ico")],
    )

    zip_directory_contents("build/wacolauncher", "build_launcher/wacolauncher.zip")
    shutil.rmtree("build/wacolauncher")

else:
    base = None
    if sys.platform == "win32":
        base = "Win32GUI"

    build_exe_options = {
        "build_exe": "build/update"
    }

    setup(
        name="Update",
        version="3.0.0",
        description="Лаунчер для WacoRP",
        options={"build_exe": build_exe_options},
        executables=[Executable("src/update.py", base=base, icon="gitignore/setup/icon.ico")],
    )

    zip_directory_contents("build/update", "build_launcher/update.zip")
    shutil.rmtree("build/update")