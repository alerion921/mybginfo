"""Tkinter GUI configurator for MyBGInfo."""
import platform as _platform
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from src.config import DEFAULT_CONFIG, load_config, save_config
from src.sysinfo import get_info


def _color_to_hex(rgb_list):
    """Convert an [R, G, B] list to a '#rrggbb' hex string."""
    return "#{:02x}{:02x}{:02x}".format(*rgb_list)


def _hex_to_color(hex_str):
    """Convert a '#rrggbb' hex string to an [R, G, B] list."""
    h = hex_str.lstrip("#")
    return [int(h[i : i + 2], 16) for i in (0, 2, 4)]


class BGInfoGUI:
    """Main GUI window for MyBGInfo configuration."""

    def __init__(self, root):
        self.root = root
        self.root.title("MyBGInfo Configurator")
        self.root.resizable(True, True)

        self.cfg = load_config()
        self._auto_thread = None
        self._stop_event = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self._build_appearance_tab(notebook)
        self._build_text_tab(notebook)
        self._build_effects_tab(notebook)
        self._build_fields_tab(notebook)
        self._build_refresh_tab(notebook)

        # Bottom buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btn_frame, text="Preview / Apply", command=self._preview).pack(
            side="left", padx=4
        )
        ttk.Button(btn_frame, text="Save Config", command=self._save).pack(
            side="left", padx=4
        )
        ttk.Button(btn_frame, text="Reset Defaults", command=self._reset).pack(
            side="left", padx=4
        )

        if _platform.system() == "Windows":
            ttk.Button(btn_frame, text="Create Task", command=self._create_service).pack(
                side="left", padx=4
            )
            ttk.Button(btn_frame, text="Remove Task", command=self._remove_service).pack(
                side="left", padx=4
            )
            ttk.Button(btn_frame, text="🔒 Run as Admin", command=self._relaunch_elevated).pack(
                side="left", padx=4
            )
        elif _platform.system() in ("Linux", "Darwin"):
            ttk.Button(btn_frame, text="Enable Autostart", command=self._create_service).pack(
                side="left", padx=4
            )
            ttk.Button(btn_frame, text="Disable Autostart", command=self._remove_service).pack(
                side="left", padx=4
            )

    def _build_appearance_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Appearance")

        # Background image
        ttk.Label(frame, text="Background Image:").grid(row=0, column=0, sticky="w", pady=4)
        self._bg_image_var = tk.StringVar(value=self.cfg.get("background_image", ""))
        ttk.Entry(frame, textvariable=self._bg_image_var, width=40).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(frame, text="Browse…", command=self._pick_bg_image).grid(
            row=0, column=2
        )

        # Output file
        ttk.Label(frame, text="Output File:").grid(row=1, column=0, sticky="w", pady=4)
        self._output_var = tk.StringVar(value=self.cfg.get("output_file", "wallpaper_output.bmp"))
        ttk.Entry(frame, textvariable=self._output_var, width=40).grid(row=1, column=1, padx=4)
        ttk.Button(frame, text="Browse…", command=self._pick_output).grid(row=1, column=2)

        # Background color
        ttk.Label(frame, text="Background Color:").grid(row=2, column=0, sticky="w", pady=4)
        self._bg_color = self.cfg.get("background_color", [0, 0, 40])
        self._bg_color_btn = tk.Button(
            frame,
            bg=_color_to_hex(self._bg_color),
            width=6,
            command=self._pick_bg_color,
        )
        self._bg_color_btn.grid(row=2, column=1, sticky="w", padx=4)

    def _build_text_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Text & Layout")

        row = 0

        # Font path
        ttk.Label(frame, text="Font Path:").grid(row=row, column=0, sticky="w", pady=4)
        self._font_path_var = tk.StringVar(value=self.cfg.get("font_path") or "")
        ttk.Entry(frame, textvariable=self._font_path_var, width=40).grid(
            row=row, column=1, padx=4
        )
        ttk.Button(frame, text="Browse…", command=self._pick_font).grid(row=row, column=2)
        row += 1

        # Font size
        ttk.Label(frame, text="Font Size:").grid(row=row, column=0, sticky="w", pady=4)
        self._font_size_var = tk.IntVar(value=self.cfg.get("font_size", 26))
        ttk.Spinbox(frame, from_=8, to=72, textvariable=self._font_size_var, width=6).grid(
            row=row, column=1, sticky="w", padx=4
        )
        row += 1

        # Title text
        ttk.Label(frame, text="Title Text:").grid(row=row, column=0, sticky="w", pady=4)
        self._title_text_var = tk.StringVar(value=self.cfg.get("title_text", "System Information"))
        ttk.Entry(frame, textvariable=self._title_text_var, width=40).grid(
            row=row, column=1, padx=4
        )
        row += 1

        # Text alignment (radio buttons – legacy "text_alignment")
        ttk.Label(frame, text="Text Alignment:").grid(row=row, column=0, sticky="w", pady=4)
        self._alignment_var = tk.StringVar(value=self.cfg.get("text_alignment", "left"))
        align_frame = ttk.Frame(frame)
        align_frame.grid(row=row, column=1, sticky="w", padx=4)
        for val, lbl in [("left", "Left"), ("center", "Center"), ("right", "Right")]:
            ttk.Radiobutton(
                align_frame, text=lbl, variable=self._alignment_var, value=val
            ).pack(side="left", padx=4)
        row += 1

        # Text Alignment dropdown (new "text_align" key)
        ttk.Label(frame, text="Text Align:").grid(row=row, column=0, sticky="w", pady=4)
        _align_labels = {"Left": "left", "Center": "center", "Right": "right"}
        _align_display = {v: k for k, v in _align_labels.items()}
        current_align = self.cfg.get("text_align", "left")
        self._text_align_var = tk.StringVar(
            value=_align_display.get(current_align, "Left")
        )
        tk.OptionMenu(frame, self._text_align_var, "Left", "Center", "Right").grid(
            row=row, column=1, sticky="w", padx=4
        )
        self._align_labels_map = _align_labels
        row += 1

        # Text margin
        ttk.Label(frame, text="Text Margin (px):").grid(row=row, column=0, sticky="w", pady=4)
        self._margin_var = tk.IntVar(value=self.cfg.get("text_margin", 50))
        ttk.Spinbox(frame, from_=0, to=960, textvariable=self._margin_var, width=6).grid(
            row=row, column=1, sticky="w", padx=4
        )
        row += 1

        # Position Y
        ttk.Label(frame, text="Position Y (px):").grid(row=row, column=0, sticky="w", pady=4)
        self._pos_y_var = tk.IntVar(value=self.cfg.get("position_y", 50))
        ttk.Spinbox(frame, from_=0, to=2160, textvariable=self._pos_y_var, width=6).grid(
            row=row, column=1, sticky="w", padx=4
        )
        row += 1

        # Line spacing
        ttk.Label(frame, text="Line Spacing:").grid(row=row, column=0, sticky="w", pady=4)
        self._spacing_var = tk.IntVar(value=self.cfg.get("line_spacing", 38))
        ttk.Spinbox(frame, from_=10, to=120, textvariable=self._spacing_var, width=6).grid(
            row=row, column=1, sticky="w", padx=4
        )
        row += 1

        # Label color
        ttk.Label(frame, text="Label Color:").grid(row=row, column=0, sticky="w", pady=4)
        self._label_color = self.cfg.get("label_color", [180, 180, 255])
        self._label_color_btn = tk.Button(
            frame, bg=_color_to_hex(self._label_color), width=6,
            command=self._pick_label_color,
        )
        self._label_color_btn.grid(row=row, column=1, sticky="w", padx=4)
        row += 1

        # Value color
        ttk.Label(frame, text="Value Color:").grid(row=row, column=0, sticky="w", pady=4)
        self._value_color = self.cfg.get("value_color", [255, 255, 255])
        self._value_color_btn = tk.Button(
            frame, bg=_color_to_hex(self._value_color), width=6,
            command=self._pick_value_color,
        )
        self._value_color_btn.grid(row=row, column=1, sticky="w", padx=4)
        row += 1

        # Title color
        ttk.Label(frame, text="Title Color:").grid(row=row, column=0, sticky="w", pady=4)
        self._title_color = self.cfg.get("title_color", [0, 220, 255])
        self._title_color_btn = tk.Button(
            frame, bg=_color_to_hex(self._title_color), width=6,
            command=self._pick_title_color,
        )
        self._title_color_btn.grid(row=row, column=1, sticky="w", padx=4)

    def _build_effects_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Effects")

        row = 0

        # Shadow toggle + colour
        self._shadow_var = tk.BooleanVar(value=self.cfg.get("shadow", True))
        ttk.Checkbutton(frame, text="Drop Shadow", variable=self._shadow_var).grid(
            row=row, column=0, sticky="w", pady=4
        )
        self._shadow_color = self.cfg.get("shadow_color", [0, 0, 0])
        self._shadow_color_btn = tk.Button(
            frame, bg=_color_to_hex(self._shadow_color), width=6,
            command=self._pick_shadow_color,
        )
        self._shadow_color_btn.grid(row=row, column=1, sticky="w", padx=4)
        row += 1

        # Text BG panel toggle
        self._panel_var = tk.BooleanVar(value=self.cfg.get("text_bg_panel", False))
        ttk.Checkbutton(frame, text="Text Background Panel", variable=self._panel_var).grid(
            row=row, column=0, sticky="w", pady=4
        )
        row += 1

        # Panel alpha
        ttk.Label(frame, text="Panel Alpha (0-255):").grid(row=row, column=0, sticky="w", pady=4)
        self._panel_alpha_var = tk.IntVar(value=self.cfg.get("text_bg_alpha", 160))
        ttk.Scale(
            frame, from_=0, to=255, variable=self._panel_alpha_var, orient="horizontal", length=160
        ).grid(row=row, column=1, sticky="w", padx=4)
        row += 1

        # Panel colour
        ttk.Label(frame, text="Panel Color:").grid(row=row, column=0, sticky="w", pady=4)
        self._panel_color = self.cfg.get("text_bg_color", [0, 0, 20])
        self._panel_color_btn = tk.Button(
            frame, bg=_color_to_hex(self._panel_color), width=6,
            command=self._pick_panel_color,
        )
        self._panel_color_btn.grid(row=row, column=1, sticky="w", padx=4)
        row += 1

        # Separator line toggle + colour
        self._separator_var = tk.BooleanVar(value=self.cfg.get("separator_line", True))
        ttk.Checkbutton(frame, text="Separator Line", variable=self._separator_var).grid(
            row=row, column=0, sticky="w", pady=4
        )
        self._separator_color = self.cfg.get("separator_color", [0, 220, 255])
        self._separator_color_btn = tk.Button(
            frame, bg=_color_to_hex(self._separator_color), width=6,
            command=self._pick_separator_color,
        )
        self._separator_color_btn.grid(row=row, column=1, sticky="w", padx=4)

    def _build_fields_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Fields")

        ttk.Label(frame, text="Select fields to display:").pack(anchor="w")

        all_fields = list(get_info().keys())
        enabled = set(self.cfg.get("fields", all_fields))
        self._field_vars = {}

        # Scrollable canvas
        canvas = tk.Canvas(frame, borderwidth=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, pady=4)
        scrollbar.pack(side="right", fill="y")

        for field in all_fields:
            var = tk.BooleanVar(value=field in enabled)
            self._field_vars[field] = var
            ttk.Checkbutton(scroll_frame, text=field, variable=var).pack(anchor="w")

    def _build_refresh_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Refresh")

        row = 0

        ttk.Label(frame, text="Refresh Interval (s, 0=disabled):").grid(
            row=row, column=0, sticky="w", pady=4
        )
        self._interval_var = tk.IntVar(value=self.cfg.get("refresh_interval", 60))
        ttk.Spinbox(frame, from_=0, to=86400, textvariable=self._interval_var, width=8).grid(
            row=row, column=1, sticky="w", padx=4
        )
        row += 1

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Button(btn_frame, text="Start Auto-Refresh", command=self._start_auto_refresh).pack(
            side="left", padx=4
        )
        ttk.Button(btn_frame, text="Stop Auto-Refresh", command=self._stop_auto_refresh).pack(
            side="left", padx=4
        )
        row += 1

        self._status_var = tk.StringVar(value="Not running")
        ttk.Label(frame, textvariable=self._status_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=4
        )

    # ------------------------------------------------------------------
    # File / color pickers
    # ------------------------------------------------------------------

    def _pick_bg_image(self):
        path = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")],
        )
        if path:
            self._bg_image_var.set(path)

    def _pick_output(self):
        path = filedialog.asksaveasfilename(
            title="Output File",
            defaultextension=".bmp",
            filetypes=[("BMP files", "*.bmp"), ("PNG files", "*.png"), ("All files", "*.*")],
        )
        if path:
            self._output_var.set(path)

    def _pick_font(self):
        path = filedialog.askopenfilename(
            title="Select Font File",
            filetypes=[("TrueType fonts", "*.ttf"), ("OpenType fonts", "*.otf"), ("All files", "*.*")],
        )
        if path:
            self._font_path_var.set(path)

    def _pick_bg_color(self):
        result = colorchooser.askcolor(color=_color_to_hex(self._bg_color), title="Background Color")
        if result and result[0]:
            self._bg_color = [int(c) for c in result[0]]
            self._bg_color_btn.config(bg=result[1])

    def _pick_label_color(self):
        result = colorchooser.askcolor(color=_color_to_hex(self._label_color), title="Label Color")
        if result and result[0]:
            self._label_color = [int(c) for c in result[0]]
            self._label_color_btn.config(bg=result[1])

    def _pick_value_color(self):
        result = colorchooser.askcolor(color=_color_to_hex(self._value_color), title="Value Color")
        if result and result[0]:
            self._value_color = [int(c) for c in result[0]]
            self._value_color_btn.config(bg=result[1])

    def _pick_title_color(self):
        result = colorchooser.askcolor(color=_color_to_hex(self._title_color), title="Title Color")
        if result and result[0]:
            self._title_color = [int(c) for c in result[0]]
            self._title_color_btn.config(bg=result[1])

    def _pick_shadow_color(self):
        result = colorchooser.askcolor(color=_color_to_hex(self._shadow_color), title="Shadow Color")
        if result and result[0]:
            self._shadow_color = [int(c) for c in result[0]]
            self._shadow_color_btn.config(bg=result[1])

    def _pick_panel_color(self):
        result = colorchooser.askcolor(color=_color_to_hex(self._panel_color), title="Panel Color")
        if result and result[0]:
            self._panel_color = [int(c) for c in result[0]]
            self._panel_color_btn.config(bg=result[1])

    def _pick_separator_color(self):
        result = colorchooser.askcolor(
            color=_color_to_hex(self._separator_color), title="Separator Color"
        )
        if result and result[0]:
            self._separator_color = [int(c) for c in result[0]]
            self._separator_color_btn.config(bg=result[1])

    # ------------------------------------------------------------------
    # Auto-refresh helpers
    # ------------------------------------------------------------------

    def _start_auto_refresh(self):
        """Start the background auto-refresh loop."""
        if self._auto_thread and self._auto_thread.is_alive():
            messagebox.showinfo("Info", "Auto-refresh is already running.")
            return
        interval = self._interval_var.get()
        if interval <= 0:
            messagebox.showwarning("Warning", "Set a refresh interval > 0 first.")
            return
        from src.bginfo import start_auto_refresh  # noqa: PLC0415

        cfg = self._build_config()
        # Save a temp config so the worker thread can reload it
        save_config(cfg)
        # Shared list so the worker can report its actual last-update timestamp
        self._last_update: list = []
        self._auto_thread, self._stop_event = start_auto_refresh(
            interval=interval, _last_update=self._last_update
        )
        self._status_var.set("Running – waiting for first update…")
        self._poll_refresh()

    def _stop_auto_refresh(self):
        """Stop the background auto-refresh loop."""
        if self._stop_event:
            self._stop_event.set()
        self._status_var.set("Stopped")

    def _poll_refresh(self):
        """Poll whether the thread is alive and update the status label."""
        if self._auto_thread and self._auto_thread.is_alive():
            last = getattr(self, "_last_update", [])
            if last:
                self._status_var.set(f"Last updated: {last[-1]}")
            self.root.after(self._interval_var.get() * 1000, self._poll_refresh)
        else:
            self._status_var.set("Not running")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _build_config(self):
        """Read current widget values into a config dict."""
        font_path_value = self._font_path_var.get().strip() or None
        return {
            "background_image": self._bg_image_var.get().strip() or None,
            "output_file": self._output_var.get().strip() or "wallpaper_output.bmp",
            "background_color": self._bg_color,
            "label_color": self._label_color,
            "value_color": self._value_color,
            "title_color": self._title_color,
            "font_path": font_path_value,
            "font_size": self._font_size_var.get(),
            "title_text": self._title_text_var.get().strip() or "System Information",
            "text_alignment": self._alignment_var.get(),
            "text_align": self._align_labels_map.get(self._text_align_var.get(), "left"),
            "text_margin": self._margin_var.get(),
            "position_y": self._pos_y_var.get(),
            "line_spacing": self._spacing_var.get(),
            "shadow": self._shadow_var.get(),
            "shadow_color": self._shadow_color,
            "text_bg_panel": self._panel_var.get(),
            "text_bg_alpha": int(self._panel_alpha_var.get()),
            "text_bg_color": self._panel_color,
            "separator_line": self._separator_var.get(),
            "separator_color": self._separator_color,
            "refresh_interval": self._interval_var.get(),
            "fields": [f for f, var in self._field_vars.items() if var.get()],
        }

    def _preview(self):
        """Generate and apply the wallpaper with current settings."""
        try:
            from src.bginfo import generate_wallpaper  # noqa: PLC0415
            from src.wallpaper import set_wallpaper  # noqa: PLC0415

            cfg = self._build_config()
            out = generate_wallpaper(cfg)
            set_wallpaper(out)
            messagebox.showinfo("Success", f"Wallpaper updated:\n{out}")
        except Exception as exc:
            self._handle_error_with_elevation(exc, self._preview)

    def _save(self):
        """Save the current configuration to config/bginfo.json."""
        try:
            cfg = self._build_config()
            save_config(cfg)
            messagebox.showinfo("Saved", "Configuration saved to config/bginfo.json")
        except Exception as exc:
            self._handle_error_with_elevation(exc, self._save)

    def _create_service(self):
        """Install the autostart mechanism for the current platform."""
        system = _platform.system()
        interval = self.cfg.get("refresh_interval", 300)
        try:
            if system == "Windows":
                from src.service_manager import install_task_scheduler  # noqa: PLC0415
                install_task_scheduler(interval_minutes=max(1, interval // 60))
                messagebox.showinfo("Success", "Scheduled task created successfully.\nIt will run every few minutes.")
            elif system == "Linux":
                from src.service_manager import install_linux_autostart  # noqa: PLC0415
                install_linux_autostart(interval_minutes=max(1, interval // 60))
                messagebox.showinfo("Success", "Autostart enabled.")
            elif system == "Darwin":
                from src.service_manager import install_macos_launchagent  # noqa: PLC0415
                install_macos_launchagent(interval_seconds=interval)
                messagebox.showinfo("Success", "LaunchAgent installed.")
        except Exception as exc:
            self._handle_error_with_elevation(exc, self._create_service)

    def _remove_service(self):
        """Remove the autostart mechanism for the current platform."""
        system = _platform.system()
        try:
            if system == "Windows":
                from src.service_manager import remove_task_scheduler  # noqa: PLC0415
                remove_task_scheduler()
                messagebox.showinfo("Success", "Scheduled task removed.")
            elif system == "Linux":
                from src.service_manager import remove_linux_autostart  # noqa: PLC0415
                remove_linux_autostart()
                messagebox.showinfo("Success", "Autostart disabled.")
            elif system == "Darwin":
                from src.service_manager import remove_macos_launchagent  # noqa: PLC0415
                remove_macos_launchagent()
                messagebox.showinfo("Success", "LaunchAgent removed.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _handle_error_with_elevation(self, exc: Exception, action_fn):
        """Show an error dialog; offer elevation if the error looks permission-related."""
        msg = str(exc)
        needs_elevation = any(
            k in msg.lower()
            for k in ("permission", "access is denied", "elevation", "privilege", "uac")
        )
        if needs_elevation and _platform.system() == "Windows":
            answer = messagebox.askyesno(
                "Elevation Required",
                f"This action requires administrator privileges.\n\nError: {msg}\n\n"
                "Would you like to restart MyBGInfo as Administrator?",
            )
            if answer:
                self._relaunch_elevated()
        else:
            messagebox.showerror("Error", msg)

    def _relaunch_elevated(self):
        """Relaunch the current process with UAC elevation (Windows only)."""
        import ctypes  # noqa: PLC0415
        import sys as _sys  # noqa: PLC0415
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            _sys.executable,
            " ".join(_sys.argv),
            None,
            1,
        )
        self.root.withdraw()
        self.root.after(500, self.root.destroy)

    def _reset(self):
        """Reset all fields to defaults."""
        self.cfg = DEFAULT_CONFIG.copy()
        # Rebuild the whole UI to reflect defaults
        for widget in self.root.winfo_children():
            widget.destroy()
        self._build_ui()


def launch_gui():
    """Create and run the Tkinter GUI."""
    root = tk.Tk()
    BGInfoGUI(root)
    root.mainloop()
