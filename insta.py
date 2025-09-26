#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
import textwrap
import json
import argparse
import time

# Konfigurasi edit jika perlu
OUT_DIR = Path("/sdcard/DCIM/Instagram/")
WATERMARK = Path("/data/data/com.termux/files/home/storage/dcim/instagram/Watermark/watermark.png")
COOKIES = Path.home() / ".config/gallery-dl/cookies.txt"
ARCHIVE = Path.home() / ".config/gallery-dl/archive.txt"

FONTSIZE = 42
FONTFILE = "/system/fonts/RobotoCondensed-Bold.ttf"
DEFAULT_TEXT = "kata kata hai ini..."

ASCII_BANNER = r"""
  ___           _        _             _             
 |_ _|_ __  ___| |_ __ _(_)_ __   __ _| |_ ___  _ __ 
  | || '_ \/ __| __/ _` | | '_ \ / _` | __/ _ \| '__|
  | || | | \__ \ || (_| | | | | | (_| | || (_) | |   
 |___|_| |_|___/\__\__,_|_|_| |_|\__,_|\__\___/|_|   
   Download & Watermark Instagram Reels - by becakjowo
"""

def print_banner():
    print(ASCII_BANNER)

def run_cmd(cmd, capture_output=False):
    # Hide ffmpeg debug output by redirecting stderr to DEVNULL unless capturing output
    if "ffmpeg" in cmd and not capture_output:
        cmd += " -loglevel quiet"
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode().strip()
        else:
            result = subprocess.run(cmd, shell=True, check=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def get_video_width(path: Path) -> int:
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width -of json "{path}"'
    out = run_cmd(cmd, capture_output=True)
    info = json.loads(out)
    return info["streams"][0]["width"]

def wrap_text_dynamic(text: str, video_width: int, fontsize: int) -> list[str]:
    avg_char_px = fontsize * 0.6
    max_chars = int((video_width * 0.7) / avg_char_px)
    return textwrap.wrap(text, max_chars)

def build_drawtext_filters(wrapped_lines, fontsize, fontfile):
    filters = []
    line_spacing = 10
    prev = "[bg]"
    for i, line in enumerate(wrapped_lines):
        y_offset = 120 + i * (fontsize + line_spacing)
        label = f"[t{i+1}]" if i < len(wrapped_lines)-1 else ""
        drawtext = (
            f"{prev}drawtext=text='{line}':"
            f"fontcolor=white:fontsize={fontsize}:fontfile={fontfile}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2+{y_offset}:"
            f"shadowcolor=black:shadowx=2:shadowy=2{label}"
        )
        filters.append(drawtext)
        prev = label if label else ""
    return "; ".join(filters)

def download(url):
    print(f"⬇️ Download: {url}")
    cmd = f'gallery-dl --cookies "{COOKIES}" --download-archive "{ARCHIVE}" -d "{OUT_DIR}" "{url}"'
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ Download gagal. Bisa jadi cookies expired/invalid.")
        print(f"   Coba manual: {cmd}")
        sys.exit(1)

def countdown(secs, process_text=""):
    for i in range(secs, 0, -1):
        print(f"⏳ {process_text}... {i} detik", end="\r")
        time.sleep(1)
    print(f"⏳ {process_text}... selesai!      ")

def watermark_videos(text_watermark: str):
    files = [f for f in OUT_DIR.rglob("*.mp4") if not f.name.endswith("_wm.mp4")]
    total_files = len(files)
    for idx, f in enumerate(files, 1):
        wm_file = f.with_name(f.stem + "_wm.mp4")
        if wm_file.exists():
            continue

        print(f"🎬 [{idx}/{total_files}] Watermark: {f.name}")

        # Hitungan mundur sebelum proses watermark dimulai
        countdown(3, process_text="Menambahkan watermark dan teks")

        width = get_video_width(f)
        wrapped_lines = wrap_text_dynamic(text_watermark, width, FONTSIZE)

        drawtext_filters = build_drawtext_filters(wrapped_lines, FONTSIZE, FONTFILE)

        cmd = (
            f'ffmpeg -i "{f}" -i "{WATERMARK}" '
            f'-filter_complex "'
            f'[1]scale=iw*0.2:-1[wm]; '
            f'[wm]format=rgba,colorchannelmixer=aa=0.5[wm2]; '
            f'[0][wm2]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2-100[bg]; '
            f'{drawtext_filters}" '
            f'-codec:a copy "{wm_file}"'
        )
        run_cmd(cmd)
        f.unlink()

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Download & watermark Instagram Reels")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    user_parser = subparsers.add_parser("user", help="Download semua reels dari user")
    user_parser.add_argument("username", help="Username Instagram")

    reel_parser = subparsers.add_parser("reel", help="Download satu reels")
    reel_parser.add_argument("url", help="URL reels Instagram")

    args = parser.parse_args()

    if args.mode == "user":
        url = f"https://www.instagram.com/{args.username}/reels/"
    elif args.mode == "reel":
        url = args.url
    else:
        print("❌ Argumen tidak valid")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)

    download(url)

    # konfigurasi manual
    print("\n📌 Tulis watermark text manual (Enter untuk default):")
    user_text = input("→ ").strip()
    text_to_use = user_text if user_text else DEFAULT_TEXT

    print(f"📝 Dipakai teks: {text_to_use}")
    watermark_videos(text_to_use)

    print("✅ Selesai download + watermark")

if __name__ == "__main__":
    main()
