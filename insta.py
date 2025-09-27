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
from rich.panel import Panel
from rich.text import Text

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
DEFAULT_WATERMARK_SIZE = 0.2
DEFAULT_WATERMARK_OPACITY = 0.5
DEFAULT_TEXT_OFFSET = 80  # pixel jarak teks dari watermark, bisa diubah

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

def get_video_height(path: Path) -> int:
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=height -of json "{path}"'
    out = run_cmd(cmd, capture_output=True)
    try:
        info = json.loads(out)
        return info["streams"][0]["height"]
    except Exception as e:
        console.print(f"[red]❌ Tidak bisa membaca tinggi video:[/red] {path.name}")
        console.print(f"[red]Rincian error:[/red] {e}")
        sys.exit(2)

def wrap_text_dynamic(text: str, video_width: int, fontsize: int) -> list[str]:
    avg_char_px = fontsize * 0.6
    max_chars = int((video_width * 0.7) / avg_char_px)
    return textwrap.wrap(text, max_chars)

def build_drawtext_filters(wrapped_lines, fontsize, fontfile, text_color, text_pos, video_height, text_offset):
    filters = []
    line_spacing = 10
    prev = "[bg]"
    for i, line in enumerate(wrapped_lines):
        # y_offset logic for position + offset agar tidak nempel watermark
        if text_pos == "top":
            y_offset = 50 + i * (fontsize + line_spacing)
        elif text_pos == "center":
            y_offset = (video_height // 2) + text_offset + i * (fontsize + line_spacing)
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

def build_overlay_position(pos):
    positions = {
        "top-left": ("0", "0"),
        "top-right": ("(main_w-overlay_w)", "0"),
        "bottom-left": ("0", "(main_h-overlay_h)"),
        "bottom-right": ("(main_w-overlay_w)", "(main_h-overlay_h)"),
        "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
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

def pilih_posisi_watermark():
    posisi_list = [
        ("1", "top-left"),
        ("2", "top-right"),
        ("3", "bottom-left"),
        ("4", "bottom-right"),
        ("5", "center")
    ]
    console.print("\n[bold magenta]Pilih letak watermark:[/bold magenta]")
    for kode, label in posisi_list:
        console.print(f"[cyan]{kode}[/cyan]. {label}")
    pilihan = Prompt.ask("Masukkan nomor posisi", choices=[x[0] for x in posisi_list], default="5")
    return posisi_list[int(pilihan)-1][1]

def pilih_posisi_teks():
    posisi_list = [
        ("1", "top"),
        ("2", "center"),
        ("3", "bottom"),
    ]
    console.print("\n[bold magenta]Pilih letak teks watermark:[/bold magenta]")
    for kode, label in posisi_list:
        console.print(f"[cyan]{kode}[/cyan]. {label}")
    pilihan = Prompt.ask("Masukkan nomor posisi", choices=[x[0] for x in posisi_list], default="2")
    return posisi_list[int(pilihan)-1][1]

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
        watermark_opacity: float,
        text_offset: int
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
        height = get_video_height(f)

        wrapped_lines = wrap_text_dynamic(text_watermark, width, fontsize)
        drawtext_filters = build_drawtext_filters(
            wrapped_lines, fontsize, fontfile, text_color, text_pos, height, text_offset
        )

        # Watermark scale/opacity
        scale_expr = f"iw*{watermark_size}:-1"
        opacity_expr = watermark_opacity

        # Get overlay position
        x, y = build_overlay_position(watermark_pos)

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
    parser.add_argument("--watermark-size", type=float, default=DEFAULT_WATERMARK_SIZE, help="Ukuran watermark (default: 0.2)")
    parser.add_argument("--watermark-opacity", type=float, default=DEFAULT_WATERMARK_OPACITY, help="Opacity watermark (default: 0.5)")
    parser.add_argument("--text-color", type=str, default=DEFAULT_TEXT_COLOR, help="Warna teks watermark (default: white)")
    parser.add_argument("--text-font", type=str, default=DEFAULT_FONTFILE, help="Font file teks watermark")
    parser.add_argument("--fontsize", type=int, default=DEFAULT_FONTSIZE, help="Ukuran font teks (default: 42)")
    parser.add_argument("--text-offset", type=int, default=DEFAULT_TEXT_OFFSET, help="Jarak teks dari watermark (px, default: 80)")

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

    # Pilihan interaktif posisi watermark
    watermark_pos = pilih_posisi_watermark()
    console.print(f"[green]Letak watermark yang dipilih: [bold]{watermark_pos}[/bold][/green]")
    # Pilihan interaktif posisi teks
    text_pos = pilih_posisi_teks()
    console.print(f"[green]Letak teks watermark yang dipilih: [bold]{text_pos}[/bold][/green]")

    watermark_videos(
        text_to_use,
        out_dir,
        Path(args.watermark),
        args.fontsize,
        args.text_font,
        args.text_color,
        text_pos,
        watermark_pos,
        args.watermark_size,
        args.watermark_opacity,
        args.text_offset,
    )

    console.print("[bold green]✅ Selesai download + watermark[/bold green]")

if __name__ == "__main__":
    main() 
