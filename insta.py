#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
import textwrap
import json
import argparse
import time

from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel

console = Console()

# Default config
DEFAULT_OUT_DIR = Path("/sdcard/DCIM/Instagram/")
DEFAULT_WATERMARK = Path("/data/data/com.termux/files/home/storage/dcim/instagram/Watermark/watermark.png")
COOKIES = Path.home() / ".config/gallery-dl/cookies.txt"
ARCHIVE = Path.home() / ".config/gallery-dl/archive.txt"

DEFAULT_FONTSIZE = 42
DEFAULT_FONTFILE = "/system/fonts/RobotoCondensed-Bold.ttf"
DEFAULT_TEXT = "kata kata hai ini..."
DEFAULT_TEXT_COLOR = "white"
DEFAULT_TEXT_POS = "center"
DEFAULT_WATERMARK_POS = "center"
DEFAULT_WATERMARK_SIZE = 0.2
DEFAULT_WATERMARK_OPACITY = 0.5

ASCII_BANNER = r"""
  ___           _        _             _             
 |_ _|_ __  ___| |_ __ _(_)_ __   __ _| |_ ___  _ __ 
  | || '_ \/ __| __/ _` | | '_ \ / _` | __/ _ \| '__|
  | || | | \__ \ || (_| | | | | | (_| | || (_) | |   
 |___|_| |_|___/\__\__,_|_|_| |_|\__,_|\__\___/|_|   
   Download & Watermark Instagram Reels - by becakjowo
"""

def print_banner():
    console.print(Panel(Text(ASCII_BANNER, style="bold magenta"), title="InstaReels Watermarker", style="green"))

def run_cmd(cmd, capture_output=False):
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode().strip()
        else:
            result = subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error saat menjalankan perintah:[/red] [yellow]{cmd}[/yellow]")
        console.print(f"[red]Rincian error:[/red] {e}")
        sys.exit(1)

def get_video_width(path: Path) -> int:
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width -of json "{path}"'
    out = run_cmd(cmd, capture_output=True)
    try:
        info = json.loads(out)
        return info["streams"][0]["width"]
    except Exception as e:
        console.print(f"[red]❌ Tidak bisa membaca lebar video:[/red] {path.name}")
        console.print(f"[red]Rincian error:[/red] {e}")
        sys.exit(2)

def wrap_text_dynamic(text: str, video_width: int, fontsize: int) -> list[str]:
    avg_char_px = fontsize * 0.6
    max_chars = int((video_width * 0.7) / avg_char_px)
    return textwrap.wrap(text, max_chars)

def build_drawtext_filters(wrapped_lines, fontsize, fontfile, text_color, text_pos, video_height):
    filters = []
    line_spacing = 10
    prev = "[bg]"
    for i, line in enumerate(wrapped_lines):
        # y_offset logic for position
        if text_pos == "top":
            y_offset = 50 + i * (fontsize + line_spacing)
        elif text_pos == "center":
            y_offset = (video_height // 2) - (len(wrapped_lines)//2 * (fontsize + line_spacing)) + i * (fontsize + line_spacing)
        elif text_pos == "bottom":
            y_offset = video_height - 180 + i * (fontsize + line_spacing)
        else:
            y_offset = 120 + i * (fontsize + line_spacing)
        label = f"[t{i+1}]" if i < len(wrapped_lines)-1 else ""
        drawtext = (
            f"{prev}drawtext=text='{line}':"
            f"fontcolor={text_color}:fontsize={fontsize}:fontfile={fontfile}:"
            f"x=(w-text_w)/2:y={y_offset}:"
            f"shadowcolor=black:shadowx=2:shadowy=2{label}"
        )
        filters.append(drawtext)
        prev = label if label else ""
    return "; ".join(filters)

def build_overlay_position(pos, video_w, video_h, wm_w, wm_h):
    # Return x, y based on pos string
    positions = {
        "top-left": ("0", "0"),
        "top-right": (f"(main_w-overlay_w)", "0"),
        "bottom-left": ("0", f"(main_h-overlay_h)"),
        "bottom-right": (f"(main_w-overlay_w)", f"(main_h-overlay_h)"),
        "center": (f"(main_w-overlay_w)/2", f"(main_h-overlay_h)/2"),
    }
    return positions.get(pos, positions["center"])

def download(url, out_dir):
    console.print(f"[cyan]⬇️ Download: {url}[/cyan]")
    cmd = f'gallery-dl --cookies "{COOKIES}" --download-archive "{ARCHIVE}" -d "{out_dir}" "{url}"'
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        console.print("[red]❌ Download gagal. Bisa jadi cookies expired/invalid.[/red]")
        console.print(f"   Coba manual: {cmd}")
        sys.exit(3)

def countdown(secs, process_text=""):
    for i in range(secs, 0, -1):
        console.print(f"[yellow]⏳ {process_text}... {i} detik[/yellow]", end="\r")
        time.sleep(1)
    console.print(f"[yellow]⏳ {process_text}... processing please wait!!!!!      [/yellow]")

def watermark_videos(
        text_watermark: str,
        out_dir: Path,
        watermark: Path,
        fontsize: int,
        fontfile: str,
        text_color: str,
        text_pos: str,
        watermark_pos: str,
        watermark_size: float,
        watermark_opacity: float
    ):
    files = [f for f in out_dir.rglob("*.mp4") if not f.name.endswith("_wm.mp4")]
    total_files = len(files)
    if not total_files:
        console.print("[red]❌ Tidak ada file video untuk di-watermark![/red]")
        sys.exit(4)
    for idx, f in enumerate(files, 1):
        wm_file = f.with_name(f.stem + "_wm.mp4")
        if wm_file.exists():
            continue

        console.print(f"[green]🎬 [{idx}/{total_files}] Watermark: {f.name}[/green]")

        countdown(2, process_text="Menambahkan watermark dan teks")

        width = get_video_width(f)
        # Assume height is similar way
        cmd_h = f'ffprobe -v error -select_streams v:0 -show_entries stream=height -of json "{f}"'
        out_h = run_cmd(cmd_h, capture_output=True)
        video_height = json.loads(out_h)["streams"][0]["height"]

        wrapped_lines = wrap_text_dynamic(text_watermark, width, fontsize)
        drawtext_filters = build_drawtext_filters(wrapped_lines, fontsize, fontfile, text_color, text_pos, video_height)

        # Watermark scale/opacity
        scale_expr = f"iw*{watermark_size}:-1"
        opacity_expr = watermark_opacity

        # Get overlay position
        x, y = build_overlay_position(watermark_pos, "main_w", "main_h", "overlay_w", "overlay_h")

        cmd = (
            f'ffmpeg -i "{f}" -i "{watermark}" '
            f'-filter_complex "'
            f'[1]scale={scale_expr}[wm]; '
            f'[wm]format=rgba,colorchannelmixer=aa={opacity_expr}[wm2]; '
            f'[0][wm2]overlay={x}:{y}[bg]; '
            f'{drawtext_filters}" '
            f'-codec:a copy "{wm_file}" -y -loglevel quiet'
        )
        try:
            run_cmd(cmd)
            f.unlink()
        except Exception as e:
            console.print(f"[red]❌ Error watermark video: {f.name}[/red]\n{e}")

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Download & watermark Instagram Reels")

    # Mode
    subparsers = parser.add_subparsers(dest="mode", required=True)
    user_parser = subparsers.add_parser("user", help="Download semua reels dari user")
    user_parser.add_argument("username", help="Username Instagram")
    reel_parser = subparsers.add_parser("reel", help="Download satu reels")
    reel_parser.add_argument("url", help="URL reels Instagram")

    # Custom options
    parser.add_argument("--output-folder", type=str, default=str(DEFAULT_OUT_DIR), help="Folder output video (default: /sdcard/DCIM/Instagram/)")
    parser.add_argument("--watermark", type=str, default=str(DEFAULT_WATERMARK), help="Path watermark image")
    parser.add_argument("--watermark-pos", type=str, choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"], default=DEFAULT_WATERMARK_POS, help="Posisi watermark (default: center)")
    parser.add_argument("--watermark-size", type=float, default=DEFAULT_WATERMARK_SIZE, help="Ukuran watermark (default: 0.2)")
    parser.add_argument("--watermark-opacity", type=float, default=DEFAULT_WATERMARK_OPACITY, help="Opacity watermark (default: 0.5)")
    parser.add_argument("--text-color", type=str, default=DEFAULT_TEXT_COLOR, help="Warna teks watermark (default: white)")
    parser.add_argument("--text-font", type=str, default=DEFAULT_FONTFILE, help="Font file teks watermark")
    parser.add_argument("--text-pos", type=str, choices=["top", "center", "bottom"], default=DEFAULT_TEXT_POS, help="Posisi teks watermark")
    parser.add_argument("--fontsize", type=int, default=DEFAULT_FONTSIZE, help="Ukuran font teks (default: 42)")

    args = parser.parse_args()

    if args.mode == "user":
        url = f"https://www.instagram.com/{args.username}/reels/"
    elif args.mode == "reel":
        url = args.url
    else:
        console.print("[red]❌ Argumen tidak valid[/red]")
        sys.exit(5)

    out_dir = Path(args.output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)

    download(url, out_dir)

    # Custom watermark text
    console.print("\n[bold magenta]📌 Tulis watermark text manual (Enter untuk default):[/bold magenta]")
    user_text = Prompt.ask("→", default=DEFAULT_TEXT)
    text_to_use = user_text if user_text else DEFAULT_TEXT

    console.print(f"[cyan]📝 Dipakai teks:[/cyan] [bold]{text_to_use}[/bold]")

    watermark_videos(
        text_to_use,
        out_dir,
        Path(args.watermark),
        args.fontsize,
        args.text_font,
        args.text_color,
        args.text_pos,
        args.watermark_pos,
        args.watermark_size,
        args.watermark_opacity,
    )

    console.print("[bold green]✅ Selesai download + watermark[/bold green]")

if __name__ == "__main__":
    main()
