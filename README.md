# MyBGInfo

> A cross-platform BGInfo-like tool written in Python that overlays live system information onto your desktop wallpaper.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![Build Status](https://github.com/alerion921/mybginfo/actions/workflows/build.yml/badge.svg)](https://github.com/alerion921/mybginfo/actions/workflows/build.yml)

---

## Features

- 📊 Displays live system info: hostname, user, OS, CPU, RAM, disk, IP address, boot time, and more
- 🖼️ Renders text directly onto a custom background image (or generates a solid-color canvas)
- 🎨 Fully configurable: colors, font, font size, position, line spacing, and which fields to show
- 🖥️ Cross-platform: Windows, macOS, and Linux (GNOME, KDE, XFCE, and feh fallback)
- 🧰 Tkinter GUI for visual configuration with live preview
- ⚙️ JSON-based configuration (`config/bginfo.json`)
- 📦 Windows installer (Inno Setup), and install scripts for Linux and macOS

---

## Screenshots

> _Screenshots placeholder – run the tool and add your own!_

---

## Installation

### Windows

1. Download `MyBGInfo-Setup.exe` from the [Releases](https://github.com/alerion921/mybginfo/releases) page.
2. Run the installer. MyBGInfo will be placed in `%ProgramFiles%\MyBGInfo` and added to Startup.

### Linux

```bash
bash installer/linux/install.sh
```

This installs dependencies, copies the tool to `~/.local/share/mybginfo/`, and adds a `@reboot` crontab entry.

### macOS

```bash
bash installer/macos/install.sh
```

This installs dependencies, copies the tool to `~/Library/Application Support/MyBGInfo/`, and registers a LaunchAgent for auto-start at login.

### All Platforms (manual)

```bash
# 1. Clone the repository
git clone https://github.com/alerion921/mybginfo.git
cd mybginfo

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the tool
python -m src.bginfo
```

---

## Usage

### Update wallpaper (headless)

```bash
python -m src.bginfo
```

### Launch the GUI configurator

```bash
python -m src.bginfo --gui
```

---

## Configuration

Configuration lives in `config/bginfo.json`. Missing keys automatically fall back to built-in defaults.

| Key | Type | Description |
|---|---|---|
| `background_image` | string | Path to a background image (JPG/PNG). If absent, a solid color is used. |
| `output_file` | string | Path for the generated wallpaper file (`.bmp` recommended on Windows). |
| `background_color` | `[R,G,B]` | Solid background color when no image is specified. |
| `text_color` | `[R,G,B]` | Color of the info text. |
| `title_color` | `[R,G,B]` | Color of the "System Information" title. |
| `font_path` | string\|null | Path to a `.ttf` font. Falls back to PIL default if null. |
| `font_size` | int | Font size in points. |
| `position` | `{"x": N, "y": N}` | Top-left corner of the text block. |
| `line_spacing` | int | Pixels between lines. |
| `fields` | list of strings | Which system info fields to display. |

**Available fields:** `Hostname`, `User`, `OS`, `Version`, `CPU`, `CPU Cores`, `RAM`, `RAM Used`, `Disk Total`, `Disk Used`, `IP Address`, `Boot Time`, `Date/Time`

---

## Building from Source

```bash
# Clone and install build dependencies
git clone https://github.com/alerion921/mybginfo.git
cd mybginfo
pip install pyinstaller pillow psutil

# Build standalone executable
pyinstaller --onefile src/bginfo.py --name bginfo

# (Windows only) Build installer with Inno Setup after pyinstaller
# iscc installer/windows/bginfo.iss
```

---

## GitHub Actions / Auto Release

Pushing a tag matching `v*` (e.g. `v1.0.0`) automatically:

1. Builds a standalone `.exe` for Windows (+ Inno Setup installer)
2. Builds a standalone binary for Linux
3. Builds a standalone binary for macOS
4. Creates a GitHub Release and attaches all artifacts

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push and open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).
