"""Tkinter GUI configurator for MyBGInfo."""
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
        self._build_fields_tab(notebook)

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
        notebook.add(frame, text="Text")

        # Font path
        ttk.Label(frame, text="Font Path:").grid(row=0, column=0, sticky="w", pady=4)
        self._font_path_var = tk.StringVar(value=self.cfg.get("font_path") or "")
        ttk.Entry(frame, textvariable=self._font_path_var, width=40).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(frame, text="Browse…", command=self._pick_font).grid(row=0, column=2)

        # Font size
        ttk.Label(frame, text="Font Size:").grid(row=1, column=0, sticky="w", pady=4)
        self._font_size_var = tk.IntVar(value=self.cfg.get("font_size", 26))
        ttk.Spinbox(frame, from_=8, to=72, textvariable=self._font_size_var, width=6).grid(
            row=1, column=1, sticky="w", padx=4
        )

        # Text color
        ttk.Label(frame, text="Text Color:").grid(row=2, column=0, sticky="w", pady=4)
        self._text_color = self.cfg.get("text_color", [255, 255, 255])
        self._text_color_btn = tk.Button(
            frame,
            bg=_color_to_hex(self._text_color),
            width=6,
            command=self._pick_text_color,
        )
        self._text_color_btn.grid(row=2, column=1, sticky="w", padx=4)

        # Title color
        ttk.Label(frame, text="Title Color:").grid(row=3, column=0, sticky="w", pady=4)
        self._title_color = self.cfg.get("title_color", [0, 220, 255])
        self._title_color_btn = tk.Button(
            frame,
            bg=_color_to_hex(self._title_color),
            width=6,
            command=self._pick_title_color,
        )
        self._title_color_btn.grid(row=3, column=1, sticky="w", padx=4)

        # Position X / Y
        ttk.Label(frame, text="Position X:").grid(row=4, column=0, sticky="w", pady=4)
        self._pos_x_var = tk.IntVar(value=self.cfg.get("position", {}).get("x", 50))
        ttk.Spinbox(frame, from_=0, to=3840, textvariable=self._pos_x_var, width=6).grid(
            row=4, column=1, sticky="w", padx=4
        )

        ttk.Label(frame, text="Position Y:").grid(row=5, column=0, sticky="w", pady=4)
        self._pos_y_var = tk.IntVar(value=self.cfg.get("position", {}).get("y", 50))
        ttk.Spinbox(frame, from_=0, to=2160, textvariable=self._pos_y_var, width=6).grid(
            row=5, column=1, sticky="w", padx=4
        )

        # Line spacing
        ttk.Label(frame, text="Line Spacing:").grid(row=6, column=0, sticky="w", pady=4)
        self._spacing_var = tk.IntVar(value=self.cfg.get("line_spacing", 38))
        ttk.Spinbox(frame, from_=10, to=120, textvariable=self._spacing_var, width=6).grid(
            row=6, column=1, sticky="w", padx=4
        )

    def _build_fields_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Fields")

        ttk.Label(frame, text="Select fields to display:").pack(anchor="w")

        all_fields = list(get_info().keys())
        enabled = set(self.cfg.get("fields", all_fields))
        self._field_vars = {}

        scroll_frame = ttk.Frame(frame)
        scroll_frame.pack(fill="both", expand=True, pady=4)

        for field in all_fields:
            var = tk.BooleanVar(value=field in enabled)
            self._field_vars[field] = var
            ttk.Checkbutton(scroll_frame, text=field, variable=var).pack(anchor="w")

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

    def _pick_text_color(self):
        result = colorchooser.askcolor(color=_color_to_hex(self._text_color), title="Text Color")
        if result and result[0]:
            self._text_color = [int(c) for c in result[0]]
            self._text_color_btn.config(bg=result[1])

    def _pick_title_color(self):
        result = colorchooser.askcolor(color=_color_to_hex(self._title_color), title="Title Color")
        if result and result[0]:
            self._title_color = [int(c) for c in result[0]]
            self._title_color_btn.config(bg=result[1])

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
            "text_color": self._text_color,
            "title_color": self._title_color,
            "font_path": font_path_value,
            "font_size": self._font_size_var.get(),
            "position": {"x": self._pos_x_var.get(), "y": self._pos_y_var.get()},
            "line_spacing": self._spacing_var.get(),
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
            messagebox.showerror("Error", str(exc))

    def _save(self):
        """Save the current configuration to config/bginfo.json."""
        try:
            cfg = self._build_config()
            save_config(cfg)
            messagebox.showinfo("Saved", "Configuration saved to config/bginfo.json")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

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
