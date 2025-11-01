import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageEnhance, ImageFilter, ImageTk
import io, threading, numpy as np, cv2
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except Exception:
    REMBG_AVAILABLE = False

class ProTools:
    def __init__(self, app):
        self.app = app
        self.theme = app.theme
        self.window = None
        self.working_image = None
        self.use_gpu = False
        self.current_preset = None

    def update_theme(self, theme):
        self.theme = theme
        if self.window:
            self.window.configure(fg_color=theme["sidebar"])

    def open_window(self):
        if not self.app.background:
            messagebox.showinfo("Pro Tools", "Load a background first.")
            return
        if self.window and ctk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            return

        self.window = ctk.CTkToplevel(self.app)
        self.window.title("Pro Tools")
        self.window.geometry("950x700")
        self.window.configure(fg_color=self.theme["sidebar"])
        self.window.grab_set()

        self.left = ctk.CTkFrame(self.window, width=350, fg_color=self.theme["sidebar"])
        self.left.pack(side="left", fill="y", padx=10, pady=10)
        self.right = ctk.CTkFrame(self.window, fg_color=self.theme["fg"])
        self.right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.preview_canvas = ctk.CTkCanvas(self.right, bg=self.theme["fg"], highlightthickness=0)
        self.preview_canvas.pack(fill="both", expand=True)

        self.build_controls()
        self.load_working_image()

    def build_controls(self):
        ctk.CTkLabel(self.left, text="Image Adjustments", text_color=self.theme["text"]).pack(pady=(10,5))
        self.brightness = self.make_slider("Brightness", 0.2, 2.0, 1.0)
        self.contrast = self.make_slider("Contrast", 0.2, 2.0, 1.0)
        self.color = self.make_slider("Color", 0.0, 2.0, 1.0)
        self.sharp = self.make_slider("Sharpness", 0.0, 4.0, 1.0)
        self.blur = self.make_slider("Blur", 0.0, 10.0, 0.0)
        self.build_thumbnails()

        ctk.CTkLabel(self.left, text="Style Presets", text_color=self.theme["text"]).pack(pady=(15,5))
        for name in ["Cinematic","Bright","Gaming","Warm","Cold"]:
            ctk.CTkButton(self.left, text=name, width=140, fg_color=self.theme["accent"],
                          command=lambda n=name: self.apply_preset(n)).pack(pady=3)

        ctk.CTkSwitch(self.left, text="Use GPU (OpenCV)", command=self.toggle_gpu).pack(pady=(15,10))
        ctk.CTkButton(self.left, text="Remove Background", fg_color="#e91e63",
                      command=self.remove_background_thread).pack(pady=(10,5), fill="x")
        ctk.CTkButton(self.left, text="Apply Changes", fg_color=self.theme["accent"],
                      command=self.apply_to_main).pack(pady=(15,5), fill="x")
        ctk.CTkButton(self.left, text="Close", command=self.window.destroy).pack(pady=5, fill="x")

    def make_slider(self, name, from_, to, start):
        s = ctk.CTkSlider(self.left, from_=from_, to=to, number_of_steps=100, command=lambda v=None:self.update_preview())
        s.set(start)
        s.pack(fill="x", pady=(3,0))
        ctk.CTkLabel(self.left, text=name, text_color=self.theme["text"]).pack(pady=(0,5))
        return s

    def build_thumbnails(self):
        frame = ctk.CTkFrame(self.left, fg_color=self.theme["sidebar"])
        frame.pack(pady=5)
        ctk.CTkLabel(frame, text="Preview Thumbnails", text_color=self.theme["text"]).pack()
        self.thumb_labels = []
        for i in range(5):
            l = ctk.CTkLabel(frame, text=f"#{i+1}", width=50)
            l.pack(side="left", padx=2, pady=2)
            self.thumb_labels.append(l)

    def load_working_image(self):
        self.working_image = self.app.background.copy()
        self.update_preview()

    def toggle_gpu(self):
        self.use_gpu = not self.use_gpu
        self.update_preview()

    def update_preview(self):
        if not self.working_image: return
        img = self.apply_filters(self.working_image)
        w, h = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        if w < 10 or h < 10: return
        r = min(w/img.width, h/img.height, 1.0)
        disp = img.resize((int(img.width*r), int(img.height*r)))
        tk = ImageTk.PhotoImage(disp)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image((w - disp.width)//2, (h - disp.height)//2, anchor="nw", image=tk)
        self.preview_canvas._tkimg = tk
        self.update_thumbnails(img)

    def apply_filters(self, img):
        if self.use_gpu:
            arr = np.array(img)
            if arr.ndim == 3:
                if self.blur.get() > 0:
                    arr = cv2.GaussianBlur(arr, (0,0), self.blur.get())
                arr = cv2.convertScaleAbs(arr, alpha=self.contrast.get(), beta=0)
            img = Image.fromarray(arr)
        else:
            img = ImageEnhance.Brightness(img).enhance(self.brightness.get())
            img = ImageEnhance.Contrast(img).enhance(self.contrast.get())
            img = ImageEnhance.Color(img).enhance(self.color.get())
            img = ImageEnhance.Sharpness(img).enhance(self.sharp.get())
            if self.blur.get() > 0:
                img = img.filter(ImageFilter.GaussianBlur(radius=self.blur.get()))
        return img

    def update_thumbnails(self, base_img):
        try:
            thumbs = []
            for i in range(5):
                factor = 0.5 + i * 0.25
                img = base_img.copy().resize((80, 50))
                img = ImageEnhance.Contrast(img).enhance(factor)
                tki = ImageTk.PhotoImage(img)
                self.thumb_labels[i].configure(image=tki, text="")
                self.thumb_labels[i].image = tki
        except:
            pass

    def apply_preset(self, name):
        presets = {
            "Cinematic": (1.1, 1.4, 0.8, 2.0, 1.0),
            "Bright": (1.4, 1.2, 1.2, 1.0, 0.0),
            "Gaming": (1.2, 1.5, 1.3, 2.5, 0.0),
            "Warm": (1.1, 1.0, 1.5, 1.5, 0.0),
            "Cold": (0.9, 1.3, 0.7, 1.5, 0.0)
        }
        if name in presets:
            b, c, col, s, bl = presets[name]
            self.brightness.set(b)
            self.contrast.set(c)
            self.color.set(col)
            self.sharp.set(s)
            self.blur.set(bl)
            self.update_preview()
            self.current_preset = name

    def remove_background_thread(self):
        if not REMBG_AVAILABLE:
            messagebox.showinfo("rembg", "Please install rembg to use this feature.")
            return
        threading.Thread(target=self._do_rembg, daemon=True).start()

    def _do_rembg(self):
        img = self.working_image
        messagebox.showinfo("Background Removal", "Removing background... please wait.")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = rembg_remove(buf.getvalue())
        out = Image.open(io.BytesIO(data)).convert("RGBA")
        self.working_image = out
        self.update_preview()
        messagebox.showinfo("Done", "Background removed successfully.")

    def apply_to_main(self):
        if not self.working_image: return
        img = self.apply_filters(self.working_image)
        self.app.background = img.convert("RGB")
        self.app.update_canvas()
        messagebox.showinfo("Pro Tools", "Edits applied successfully.")
