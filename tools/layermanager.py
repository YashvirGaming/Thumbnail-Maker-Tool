import customtkinter as ctk
from tkinter import messagebox

class LayerManager(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=10)
        self.app = app
        self.layers_ui = []
        self.fg_color = app.theme["sidebar"]
        self.text_color = app.theme["text"]
        self.pack(fill="both", expand=True, pady=(10, 10))
        self.build_panel()

    def build_panel(self):
        ctk.CTkLabel(self, text="Layer Manager", text_color=self.text_color).pack(pady=(5, 5))
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=self.fg_color)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_layers()

    def refresh_layers(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        self.layers_ui.clear()
        idx = 0

        if self.app.background:
            self.add_layer_row("Background", "BG", idx)
            idx += 1

        for i, ov in enumerate(self.app.overlays):
            self.add_layer_row(ov.get("name", f"Overlay {i+1}"), "OV", idx, layer_obj=ov)
            idx += 1

        for i, tx in enumerate(self.app.text_layers):
            self.add_layer_row(f"Text {i+1}", "TX", idx, layer_obj=tx)
            idx += 1

    def add_layer_row(self, name, typ, index, layer_obj=None):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="#222" if typ != "BG" else "#333", corner_radius=5)
        row.pack(fill="x", pady=3, padx=4)

        lbl = ctk.CTkLabel(row, text=name, width=140, anchor="w", text_color="white")
        lbl.pack(side="left", padx=5)

        eye = ctk.CTkButton(row, text="👁️", width=30, fg_color="#555",
                            command=lambda obj=layer_obj: self.toggle_visibility(obj))
        eye.pack(side="left", padx=2)

        lock = ctk.CTkButton(row, text="🔒", width=30, fg_color="#555",
                             command=lambda obj=layer_obj: self.toggle_lock(obj))
        lock.pack(side="left", padx=2)

        up_btn = ctk.CTkButton(row, text="↑", width=25, command=lambda obj=layer_obj: self.move_up(obj))
        up_btn.pack(side="left", padx=1)
        down_btn = ctk.CTkButton(row, text="↓", width=25, command=lambda obj=layer_obj: self.move_down(obj))
        down_btn.pack(side="left", padx=1)

        select_btn = ctk.CTkButton(row, text="Select", width=60, fg_color=self.app.theme["accent"],
                                   command=lambda obj=layer_obj, tp=typ: self.select_layer(obj, tp))
        select_btn.pack(side="right", padx=3)

        self.layers_ui.append(row)

    def toggle_visibility(self, obj):
        if not obj: return
        if "visible" in obj:
            obj["visible"] = not obj["visible"]
            self.app.update_canvas()

    def toggle_lock(self, obj):
        if not obj: return
        if "locked" in obj:
            obj["locked"] = not obj["locked"]
            self.app.update_canvas()

    def move_up(self, obj):
        if obj in self.app.overlays:
            i = self.app.overlays.index(obj)
            if i < len(self.app.overlays) - 1:
                self.app.overlays[i], self.app.overlays[i+1] = self.app.overlays[i+1], self.app.overlays[i]
        elif obj in self.app.text_layers:
            i = self.app.text_layers.index(obj)
            if i < len(self.app.text_layers) - 1:
                self.app.text_layers[i], self.app.text_layers[i+1] = self.app.text_layers[i+1], self.app.text_layers[i]
        self.refresh_layers()
        self.app.update_canvas()

    def move_down(self, obj):
        if obj in self.app.overlays:
            i = self.app.overlays.index(obj)
            if i > 0:
                self.app.overlays[i], self.app.overlays[i-1] = self.app.overlays[i-1], self.app.overlays[i]
        elif obj in self.app.text_layers:
            i = self.app.text_layers.index(obj)
            if i > 0:
                self.app.text_layers[i], self.app.text_layers[i-1] = self.app.text_layers[i-1], self.app.text_layers[i]
        self.refresh_layers()
        self.app.update_canvas()

    def select_layer(self, obj, typ):
        if typ == "TX":
            self.app.text_panel.current_layer = obj
            self.app.text_panel.update_panel_from_layer()
        self.app.selected_layer = obj
        self.app.update_canvas()

    def update_theme(self, theme):
        self.fg_color = theme["sidebar"]
        self.text_color = theme["text"]
        self.configure(fg_color=self.fg_color)
        self.scroll_frame.configure(fg_color=self.fg_color)
