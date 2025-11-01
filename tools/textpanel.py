import customtkinter as ctk
from tkinter import colorchooser, messagebox
from PIL import ImageFont
import copy

class TextPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=10)
        self.app = app
        self.text_history = []
        self.current_layer = None
        self.fg_color = app.theme["sidebar"]
        self.text_color = app.theme["text"]
        self.pack(fill="x", pady=(10, 10))
        self.build_panel()

    def build_panel(self):
        ctk.CTkLabel(self, text="Text Layers", text_color=self.text_color).pack(pady=(5, 3))
        self.layer_box = ctk.CTkOptionMenu(self, values=["No Text"], command=self.switch_text_layer)
        self.layer_box.pack(fill="x", pady=(0, 5))

        ctk.CTkButton(self, text="Add Text Layer", fg_color=self.app.theme["accent"],
                      command=self.add_text_layer).pack(pady=(5, 5), fill="x")
        ctk.CTkButton(self, text="Undo Text", fg_color="#444",
                      command=self.undo_text).pack(pady=(0, 10), fill="x")

        self.text_entry = ctk.CTkEntry(self, placeholder_text="Enter text here")
        self.text_entry.pack(fill="x", pady=3)
        self.text_entry.bind("<KeyRelease>", lambda e: self.update_text_content())

        self.font_slider = ctk.CTkSlider(self, from_=20, to=180, number_of_steps=160, command=self.update_text_style)
        self.font_slider.set(80)
        self.font_slider.pack(fill="x", pady=(10, 3))
        ctk.CTkLabel(self, text="Font Size", text_color=self.text_color).pack(pady=(0, 5))

        self.bold_slider = ctk.CTkSlider(self, from_=1, to=10, number_of_steps=9, command=self.update_text_style)
        self.bold_slider.set(2)
        self.bold_slider.pack(fill="x", pady=(5, 3))
        ctk.CTkLabel(self, text="Boldness", text_color=self.text_color).pack(pady=(0, 5))

        self.color_button = ctk.CTkButton(self, text="Pick Color", command=self.pick_color)
        self.color_button.pack(pady=(5, 10), fill="x")

        ctk.CTkLabel(self, text="Move Position", text_color=self.text_color).pack()
        move_frame = ctk.CTkFrame(self)
        move_frame.pack(pady=5)
        ctk.CTkButton(move_frame, text="↑", width=40, command=lambda: self.move_text(0, -10)).grid(row=0, column=1)
        ctk.CTkButton(move_frame, text="↓", width=40, command=lambda: self.move_text(0, 10)).grid(row=2, column=1)
        ctk.CTkButton(move_frame, text="←", width=40, command=lambda: self.move_text(-10, 0)).grid(row=1, column=0)
        ctk.CTkButton(move_frame, text="→", width=40, command=lambda: self.move_text(10, 0)).grid(row=1, column=2)

    def add_text_layer(self):
        layer = {
            "text": "New Text",
            "font_size": 80,
            "bold": 2,
            "color": "white",
            "x": 200,
            "y": 300,
            "visible": True,
            "locked": False
        }
        self.push_history()
        self.app.text_layers.append(layer)
        self.current_layer = layer
        self.refresh_layer_list()
        self.update_panel_from_layer()
        self.app.layer_manager.refresh_layers()
        self.app.update_canvas()

    def refresh_layer_list(self):
        names = [f"Text {i+1}" for i in range(len(self.app.text_layers))] or ["No Text"]
        self.layer_box.configure(values=names)
        if self.current_layer:
            idx = self.app.text_layers.index(self.current_layer)
            self.layer_box.set(f"Text {idx+1}")
        else:
            self.layer_box.set("No Text")

    def switch_text_layer(self, name):
        if not name.startswith("Text"): return
        idx = int(name.split()[1]) - 1
        if 0 <= idx < len(self.app.text_layers):
            self.current_layer = self.app.text_layers[idx]
            self.update_panel_from_layer()

    def update_text_content(self):
        if not self.current_layer: return
        self.push_history()
        self.current_layer["text"] = self.text_entry.get()
        self.app.update_canvas()

    def update_text_style(self, val=None):
        if not self.current_layer: return
        self.push_history()
        self.current_layer["font_size"] = int(self.font_slider.get())
        self.current_layer["bold"] = int(self.bold_slider.get())
        self.app.update_canvas()

    def pick_color(self):
        if not self.current_layer: return
        self.push_history()
        color = colorchooser.askcolor()[1]
        if color:
            self.current_layer["color"] = color
            self.app.update_canvas()

    def move_text(self, dx, dy):
        if not self.current_layer: return
        self.push_history()
        self.current_layer["x"] += dx
        self.current_layer["y"] += dy
        self.app.update_canvas()

    def push_history(self):
        snap = copy.deepcopy(self.app.text_layers)
        self.text_history.append(snap)
        if len(self.text_history) > 15:
            self.text_history.pop(0)

    def undo_text(self):
        if not self.text_history:
            messagebox.showinfo("Undo", "No undo history.")
            return
        state = self.text_history.pop()
        self.app.text_layers = copy.deepcopy(state)
        self.current_layer = self.app.text_layers[-1] if self.app.text_layers else None
        self.refresh_layer_list()
        self.app.layer_manager.refresh_layers()
        self.app.update_canvas()

    def update_panel_from_layer(self):
        if not self.current_layer: return
        self.text_entry.delete(0, "end")
        self.text_entry.insert(0, self.current_layer["text"])
        self.font_slider.set(self.current_layer["font_size"])
        self.bold_slider.set(self.current_layer["bold"])

    def update_theme(self, theme):
        self.fg_color = theme["sidebar"]
        self.text_color = theme["text"]
        self.configure(fg_color=self.fg_color)
