# Instagram Reels Downloader & Watermark Tool for Termux

This tool allows you to easily download Instagram Reels—either from a specific user or a single post—and automatically add a custom text watermark and image watermark using FFmpeg.  
Tailored for use on Termux (Android terminal emulator).

---

## Features

- Download all reels from a user, or a single reel by URL
- Add custom text watermark (centered, multi-line)
- Add image watermark (customizable PNG)
- Uses FFmpeg for video processing
- Works seamlessly on Termux

---

## Requirements

- Python 3
- FFmpeg (installed in Termux)
- gallery-dl (installed in Termux)
- Access to Termux’s storage (run `termux-setup-storage`)
- The Python packages listed in `requirements.txt`

---

## Installation

1. **Install Termux dependencies:**
    ```sh
    pkg install python ffmpeg
    pip install gallery-dl
    termux-setup-storage
    ```

2. **Clone this repository and install Python requirements:**
    ```sh
    git clone https://github.com/becakjowo/instagram-botter.git
    cd instagram-botter
    pip install -r requirements.txt
    ```

3. **Prepare configuration:**
    - Make sure you have a valid `gallery-dl` cookies file at:  
      `~/.config/gallery-dl/cookies.txt`
    - Make sure you have a watermark PNG image at:  
      `/data/data/com.termux/files/home/storage/dcim/instagram/Watermark/watermark.png`

---

## Usage

### Download all reels from a user:

```sh
python insta.py user <instagram_username>
```

### Download a specific reel by URL:

```sh
python insta.py reel <reel_url>
```

- After download, you will be prompted to enter the watermark text (press Enter for default).

---

## Output Location

Downloaded and watermarked videos are saved to:  
`/sdcard/DCIM/Instagram/`

---

## Example

```sh
python insta.py user natgeo
python insta.py reel https://www.instagram.com/reel/XXXXXXXXX/
```

---

## Notes

- If download fails, check your Instagram cookies!
- The font used for watermark is `/system/fonts/RobotoCondensed-Bold.ttf` (Termux default).
- You can customize watermark image and font in the script.

---

## License

MIT
