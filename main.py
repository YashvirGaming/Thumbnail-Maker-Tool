import os, threading, json, time
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from tools.textpanel import TextPanel
from tools.layermanager import LayerManager
from tools.protools import ProTools
from utils.image_utils import ImageUtils
from utils.autosave import AutoSaver

class ProThumbnailStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pro Thumbnail Tool | Yashvir Gaming")
        self.geometry("1600x900")
        self.minsize(1400, 800)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.supported_themes = {
            "Dark": {
                "fg": "#0f1116", "sidebar": "#1a1c20", "accent": "#1e88e5", "text": "white"
            },
            "Light": {
                "fg": "#f5f5f5", "sidebar": "#e5e5e5", "accent": "#0078d7", "text": "black"
            },
            "Neon": {
                "fg": "#050505", "sidebar": "#0f0f0f", "accent": "#ff00ff", "text": "#00ffff"
            }
        }

        self.theme_name = "Dark"
        self.theme = self.supported_themes[self.theme_name]
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.configure(fg_color=self.theme["fg"])

        self.background = None
        self.overlays = []
        self.text_layers = []
        self.selected_layer = None

        self.image_utils = ImageUtils()
        self.autosaver = AutoSaver(self)
        self.project_path = None
        self._overlay_tks = {}
        self._preview_ratio = 1.0
        self.snap_enabled = True

        self.build_ui()
        self.update_canvas()

        self.autosaver.start_autosave_loop()

    def build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_left = ctk.CTkFrame(self, width=320, corner_radius=10, fg_color=self.theme["sidebar"])
        self.sidebar_left.grid(row=0, column=0, sticky="nswe", padx=(10, 5), pady=10)
        self.sidebar_right = ctk.CTkFrame(self, width=280, corner_radius=10, fg_color=self.theme["sidebar"])
        self.sidebar_right.grid(row=0, column=2, sticky="nswe", padx=(5, 10), pady=10)

        self.canvas_frame = ctk.CTkFrame(self, fg_color=self.theme["fg"])
        self.canvas_frame.grid(row=0, column=1, sticky="nswe", pady=10)
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg=self.theme["fg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.build_left_sidebar()
        self.text_panel = TextPanel(self.sidebar_left, self)
        self.layer_manager = LayerManager(self.sidebar_right, self)
        self.protools = ProTools(self)

    def build_left_sidebar(self):
        ctk.CTkLabel(self.sidebar_left, text="Theme", text_color=self.theme["text"]).pack(pady=(10, 2))
        theme_box = ctk.CTkOptionMenu(
            self.sidebar_left, values=list(self.supported_themes.keys()),
            command=self.change_theme, fg_color=self.theme["accent"]
        )
        theme_box.set(self.theme_name)
        theme_box.pack(pady=(0, 10), fill="x")

        ctk.CTkButton(self.sidebar_left, text="Load Background", fg_color=self.theme["accent"],
                      command=self.load_background).pack(pady=5, fill="x")
        ctk.CTkButton(self.sidebar_left, text="Add Overlay PNG", fg_color=self.theme["accent"],
                      command=self.add_overlay).pack(pady=5, fill="x")
        ctk.CTkButton(self.sidebar_left, text="Open Pro Tools", fg_color=self.theme["accent"],
                      command=self.open_protools).pack(pady=5, fill="x")
        ctk.CTkButton(self.sidebar_left, text="Export", fg_color=self.theme["accent"],
                      command=self.export_thumbnail).pack(pady=(15, 5), fill="x")

    def change_theme(self, name):
        self.theme_name = name
        self.theme = self.supported_themes[name]
        self.configure(fg_color=self.theme["fg"])
        self.sidebar_left.configure(fg_color=self.theme["sidebar"])
        self.sidebar_right.configure(fg_color=self.theme["sidebar"])
        self.canvas.config(bg=self.theme["fg"])
        self.text_panel.update_theme(self.theme)
        self.layer_manager.update_theme(self.theme)
        self.protools.update_theme(self.theme)

    def load_background(self):
        path = filedialog.askopenfilename(title="Select Background", filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if not path:
            return
        self.background = Image.open(path).convert("RGB")
        self.project_path = os.path.dirname(path)
        self.layer_manager.refresh_layers()
        self.update_canvas()

    def add_overlay(self):
        path = filedialog.askopenfilename(title="Select Overlay", filetypes=[("Images", "*.png *.jpg")])
        if not path:
            return
        img = Image.open(path).convert("RGBA")
        ov = {"image": img, "x": 100, "y": 100, "scale": 1.0, "angle": 0, "visible": True, "locked": False, "name": os.path.basename(path)}
        self.overlays.append(ov)
        self.layer_manager.refresh_layers()
        self.update_canvas()

    def update_canvas(self):
        self.canvas.delete("all")

        # When no background is loaded
        if not self.background:
            # Measure only the visible canvas area (excluding sidebar)
            self.canvas.update_idletasks()
            cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
            text = "Load a Background to Begin"

            # Compute center coordinates (within the canvas itself)
            cx, cy = cw // 2, ch // 2

            # Dynamic glow color per theme
            if self.theme_name == "Dark":
                glow_color = "#1e88e5"
            elif self.theme_name == "Light":
                glow_color = "#aaaaaa"
            else:
                glow_color = "#ff00ff"

            # Glow layers
            for radius in range(6, 0, -1):
                self.canvas.create_text(
                    cx, cy + 30,
                    text=text,
                    fill=glow_color,
                    font=("Arial", 28, "bold"),
                    anchor="center"
                )

            # Fade text layer (top layer)
            self.canvas.create_text(
                cx, cy + 30,
                text=text,
                fill=self.theme["text"],
                font=("Arial", 28, "bold"),
                anchor="center",
                tags="fadeText"
            )

            self.animate_fade_text()
            return

        # Draw composed scene when background exists
        composed = self.image_utils.compose_scene(self)
        if not composed:
            return

        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        w, h = composed.size
        ratio = min(cw / w, ch / h, 1.0)
        self._preview_ratio = ratio
        display = composed.resize((int(w * ratio), int(h * ratio)))
        self._bg_tk = ImageTk.PhotoImage(display)
        # Always anchor relative to the canvas (not global window)
        self.canvas.create_image(
            cw // 2 - display.width // 2,
            ch // 2 - display.height // 2,
            anchor="nw",
            image=self._bg_tk
        )

    def animate_fade_text(self, alpha=0):
        try:
            text_item = self.canvas.find_withtag("fadeText")
            if not text_item:
                return

            if alpha <= 255:
                r, g, b = (255, 255, 255) if self.theme_name == "Light" else (180, 220, 255)
                color = f"#{max(0, min(255, int(r * alpha / 255))):02x}" \
                        f"{max(0, min(255, int(g * alpha / 255))):02x}" \
                        f"{max(0, min(255, int(b * alpha / 255))):02x}"
                self.canvas.itemconfig(text_item, fill=color)
                self.after(20, lambda: self.animate_fade_text(alpha + 15))
            else:
                self.canvas.itemconfig(text_item, fill=self.theme["text"])
        except Exception:
            pass

    def open_protools(self):
        self.protools.open_window()

    def export_thumbnail(self):
        if not self.background:
            messagebox.showinfo("Export", "Load a background first.")
            return
        export_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")],
            initialfile="Thumbnail_Export.jpg"
        )
        if not export_path:
            return
        final_img = self.image_utils.compose_scene(self, upscale=True)
        final_img.save(export_path)
        messagebox.showinfo("Export", f"Saved: {os.path.basename(export_path)}")

    def on_close(self):
        self.autosaver.stop()
        self.destroy()

if __name__ == "__main__":
    app = ProThumbnailStudio()
    app.mainloop()
