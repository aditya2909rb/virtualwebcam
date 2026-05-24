from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tkinter import Tk, messagebox


OBS_PACKAGE_ID = "OBSProject.OBSStudio"
OBS_START_ARGS = ["--startvirtualcam", "--minimize-to-tray"]


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _relaunch_as_admin() -> None:
    params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)


def _obs_candidates() -> list[Path]:
    candidates: list[Path] = []
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    candidates.append(Path(program_files) / "obs-studio" / "bin" / "64bit" / "obs64.exe")
    candidates.append(Path(program_files_x86) / "obs-studio" / "bin" / "64bit" / "obs64.exe")
    which_obs = shutil.which("obs64.exe")
    if which_obs:
        candidates.insert(0, Path(which_obs))
    return candidates


def _find_obs_executable() -> Path | None:
    for candidate in _obs_candidates():
        if candidate.exists():
            return candidate
    return None


def _show_error(title: str, message: str) -> None:
    root = Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()


def _show_info(title: str, message: str) -> None:
    root = Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()


def _install_obs() -> None:
    winget = shutil.which("winget")
    if not winget:
        raise RuntimeError(
            "winget was not found on this system. Install the App Installer from Microsoft Store, then run the setup again."
        )

    command = [
        winget,
        "install",
        "-e",
        "--id",
        OBS_PACKAGE_ID,
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--disable-interactivity",
    ]
    subprocess.run(command, check=True)


def _start_obs_virtual_camera(obs_exe: Path) -> subprocess.Popen[str]:
    return subprocess.Popen([str(obs_exe), *OBS_START_ARGS], cwd=str(obs_exe.parent))


def _launch_app() -> None:
    import main as webcam_main

    webcam_main.main(default_backend="usb camera 2909", backend_locked=True)


def main() -> None:
    if not _is_admin():
        _relaunch_as_admin()
        return

    try:
        obs_exe = _find_obs_executable()
        if obs_exe is None:
            _show_info("Virtual Web Camera", "OBS Studio is required for the virtual camera backend. Installing it now.")
            _install_obs()
            obs_exe = _find_obs_executable()

        if obs_exe is None:
            raise RuntimeError("OBS Studio was installed, but obs64.exe could not be found.")

        _start_obs_virtual_camera(obs_exe)
        _launch_app()
    except Exception as exc:
        _show_error("Virtual Web Camera Setup", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()