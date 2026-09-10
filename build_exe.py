"""Build script for compiling FWD Data Converter Pro standalone Windows executable."""

import os
import subprocess
import sys


def build():
    print("=" * 65)
    print("Building 'FWD Data Converter Pro.exe' Standalone Application")
    print("=" * 65)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")

    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=FWD Data Converter Pro",
        "--windowed",              # Windowed mode (no console pop-up)
        "--onedir",
        "--clean",
        "--noconfirm",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        "--hidden-import=openpyxl",
        "--hidden-import=docx",
        "--hidden-import=pypdf",
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
        exe_path = os.path.join(dist_dir, "FWD Data Converter Pro", "FWD Data Converter Pro.exe")
        print("\n" + "=" * 65)
        print("BUILD SUCCESSFUL!")
        print(f"Executable created at:\n{exe_path}")
        print("=" * 65)
    else:
        print("\n" + "=" * 65)
        print(f"BUILD FAILED with exit code {result.returncode}")
        print("=" * 65)
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
