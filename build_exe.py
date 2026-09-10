"""Build script for creating standalone Windows .EXE with PyInstaller."""

import os
import subprocess
import sys


def build():
    print("=" * 60)
    print("Building WordToXLSX.exe Standalone Application")
    print("=" * 60)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")

    # PyInstaller command arguments
    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=WordToXLSX",
        "--windowed",              # No console window pop-up
        "--onedir",                # Start with onedir for fast launch and easy packaging
        "--clean",
        "--noconfirm",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        "--hidden-import=openpyxl",
        "--hidden-import=docx",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        os.path.join(project_dir, "app.py")
    ]

    print("Executing PyInstaller command:")
    print(" ".join(pyinstaller_args))

    result = subprocess.run(pyinstaller_args, cwd=project_dir)

    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "WordToXLSX", "WordToXLSX.exe")
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Executable created at:\n{exe_path}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("BUILD FAILED with exit code:", result.returncode)
        print("=" * 60)
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
