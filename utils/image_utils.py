from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np, cv2, math

class ImageUtils:
    def __init__(self):
        self.snap_distance = 20
        self.snap_lines = []

    def compose_scene(self, app, upscale=False):
        if not app.background:
            return None
        bg = app.background.copy()
        if upscale:
            bg = bg.resize((bg.width * 2, bg.height * 2), Image.LANCZOS)
        draw = ImageDraw.Draw(bg)

        for ov in app.overlays:
            if not ov.get("visible", True):
                continue
            overlay = ov["image"].copy()
            s = ov.get("scale", 1.0)
            if upscale: s *= 2
            new_size = (max(1, int(overlay.width * s)), max(1, int(overlay.height * s)))
            overlay = overlay.resize(new_size, Image.LANCZOS)
            if ov.get("angle", 0) != 0:
                overlay = overlay.rotate(ov["angle"], expand=True)
            pos = (int(ov["x"] * (2 if upscale else 1)), int(ov["y"] * (2 if upscale else 1)))
            if overlay.mode != "RGBA":
                overlay = overlay.convert("RGBA")
            bg.paste(overlay, pos, overlay)

        for tx in app.text_layers:
            if not tx.get("visible", True) or not tx.get("text"):
                continue
            try:
                f = ImageFont.truetype("arial.ttf", tx["font_size"] * (2 if upscale else 1))
            except Exception:
                f = ImageFont.load_default()
            x, y = tx["x"] * (2 if upscale else 1), tx["y"] * (2 if upscale else 1)
            bold = max(1, tx["bold"] * (2 if upscale else 1))
            for dx in range(-bold, bold + 1, bold):
                for dy in range(-bold, bold + 1, bold):
                    if dx == 0 and dy == 0: continue
                    draw.text((x + dx, y + dy), tx["text"], font=f, fill="black")
            draw.text((x, y), tx["text"], font=f, fill=tx["color"])

        if upscale:
            bg = ImageEnhance.Sharpness(bg).enhance(1.5)
        return bg

    def gpu_blur(self, pil_img, radius=3):
        arr = np.array(pil_img)
        blurred = cv2.GaussianBlur(arr, (0, 0), radius)
        return Image.fromarray(blurred)

    def snap_position(self, app, x, y, w, h):
        snap_x, snap_y = x, y
        self.snap_lines.clear()
        canvas_w = app.canvas.winfo_width()
        canvas_h = app.canvas.winfo_height()
        center_x = canvas_w / 2
        center_y = canvas_h / 2
        ox = x + w / 2
        oy = y + h / 2
        if abs(ox - center_x) < self.snap_distance:
            snap_x = center_x - w / 2
            self.snap_lines.append(("v", center_x))
        if abs(oy - center_y) < self.snap_distance:
            snap_y = center_y - h / 2
            self.snap_lines.append(("h", center_y))
        return snap_x, snap_y

    def draw_snap_guides(self, app):
        for line in self.snap_lines:
            if line[0] == "v":
                app.canvas.create_line(line[1], 0, line[1], app.canvas.winfo_height(), fill="cyan", dash=(4, 4))
            elif line[0] == "h":
                app.canvas.create_line(0, line[1], app.canvas.winfo_width(), line[1], fill="cyan", dash=(4, 4))
