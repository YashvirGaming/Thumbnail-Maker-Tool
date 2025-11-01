import os, json, threading, time
from PIL import Image

class AutoSaver:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.interval = 30
        self.thread = None
        self.autosave_path = os.path.join(os.getcwd(), ".ytproj_autosave.json")

    def start_autosave_loop(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            time.sleep(self.interval)
            try:
                self.save_state()
            except Exception as e:
                print("Autosave error:", e)

    def save_state(self):
        data = {
            "background_path": self.app.project_path,
            "theme": self.app.theme_name,
            "overlays": [],
            "text_layers": self.app.text_layers
        }
        for ov in self.app.overlays:
            entry = {
                "path": ov.get("path"),
                "x": ov.get("x", 0),
                "y": ov.get("y", 0),
                "scale": ov.get("scale", 1.0),
                "angle": ov.get("angle", 0),
                "visible": ov.get("visible", True)
            }
            data["overlays"].append(entry)
        with open(self.autosave_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_state(self):
        if not os.path.exists(self.autosave_path):
            return False
        try:
            with open(self.autosave_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("background_path") and os.path.exists(data["background_path"]):
                from PIL import Image
                self.app.background = Image.open(data["background_path"]).convert("RGB")
                self.app.project_path = data["background_path"]
            self.app.overlays.clear()
            for e in data.get("overlays", []):
                if e["path"] and os.path.exists(e["path"]):
                    img = Image.open(e["path"]).convert("RGBA")
                    self.app.overlays.append({
                        "image": img,
                        "path": e["path"],
                        "x": e.get("x", 0),
                        "y": e.get("y", 0),
                        "scale": e.get("scale", 1.0),
                        "angle": e.get("angle", 0),
                        "visible": e.get("visible", True)
                    })
            self.app.text_layers = data.get("text_layers", [])
            theme = data.get("theme")
            if theme:
                self.app.change_theme(theme)
            self.app.layer_manager.refresh_layers()
            self.app.text_panel.refresh_layer_list()
            self.app.update_canvas()
            return True
        except Exception as e:
            print("Autosave load failed:", e)
            return False

    def stop(self):
        self.running = False
