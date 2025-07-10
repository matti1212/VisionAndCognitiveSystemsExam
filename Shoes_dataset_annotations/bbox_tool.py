import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import json

IMAGE_FOLDER = "shoes_data/shoeTypeClassifierDataset/training/soccer_shoes"  # replace with your folder path
OUTPUT_JSON = f"annotations_{IMAGE_FOLDER.split('/')[-1]}.json"
MAX_SCREEN_FRACTION = 0.5  # Max image display size as a fraction of screen

class BoundingBoxAnnotator:
    def __init__(self, master):
        self.master = master
        self.master.title("Bounding Box Annotator")
        self.master.protocol("WM_DELETE_WINDOW", self.quit)

        # Canvas
        self.canvas = tk.Canvas(master, cursor="tcross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Image management
        self.image_files = sorted([
            f for f in os.listdir(IMAGE_FOLDER)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        self.index = 0
        self.annotations = self.load_annotations()
        self.buffer = []

        # For bounding box drawing
        self.start_x = self.start_y = 0
        self.rect = None

        # Screen size
        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        self.max_width = int(self.screen_width * MAX_SCREEN_FRACTION)
        self.max_height = int(self.screen_height * MAX_SCREEN_FRACTION)

        # Event bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.master.bind("<BackSpace>", self.undo)

        self.repeat_current = False  # flag to stay on current image
        self.master.bind("<plus>", self.repeat_image)  # '+' key
        self.master.bind("<KP_Add>", self.repeat_image)  # Numpad '+'

        self.load_image()

    def load_annotations(self):
        if os.path.exists(OUTPUT_JSON):
            with open(OUTPUT_JSON, "r") as f:
                return json.load(f)
        return {}

    def resize_image(self, image):
        w, h = image.size
        scale = min(self.max_width / w, self.max_height / h, 1.0)
        return image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    def draw_grid(self, image, spacing=50):
        """Draw a semi-transparent grid over the image."""
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = image.size
        for x in range(0, w, spacing):
            draw.line((x, 0, x, h), fill=(255, 255, 255, 80))
        for y in range(0, h, spacing):
            draw.line((0, y, w, y), fill=(255, 255, 255, 80))
        return Image.alpha_composite(image.convert("RGBA"), overlay)

    def load_image(self):
        while self.index < len(self.image_files) and self.image_files[self.index] in self.annotations:
            self.index += 1
        if self.index >= len(self.image_files):
            self.quit()
            return

        filename = self.image_files[self.index]
        image_path = os.path.join(IMAGE_FOLDER, filename)
        original = Image.open(image_path)
        resized = self.resize_image(original)
        with_grid = self.draw_grid(resized)

        self.current_image = with_grid.convert("RGB")
        self.tk_image = ImageTk.PhotoImage(self.current_image)
        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.rect = None

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        bbox = [int(self.start_x), int(self.start_y), int(end_x), int(end_y)]
        filename = self.image_files[self.index]
        if filename not in self.annotations:
            self.annotations[filename] = []
        self.annotations[filename].append(bbox)

        self.buffer.append((self.index, self.annotations[filename][-1], filename))
        if len(self.buffer) > 5:
            self.buffer.pop(0)

        if not self.repeat_current:
            self.index += 1
        else:
            self.repeat_current = False  # reset flag

        self.canvas.delete("all")
        self.load_image()


    def undo(self, event):
        if not self.buffer:
            return
        self.index, _, filename = self.buffer.pop()
        if filename in self.annotations:
            self.annotations[filename].pop()
            if not self.annotations[filename]:
                del self.annotations[filename]

        self.canvas.delete("all")
        self.load_image()

    def save_annotations(self):
        with open(OUTPUT_JSON, "w") as f:
            json.dump(self.annotations, f, indent=4)
        print(f"[✓] Saved annotations to {OUTPUT_JSON}")

    def quit(self, event=None):
        self.save_annotations()
        self.master.destroy()
        
    def repeat_image(self, event = None):
        self.repeat_current = True

if __name__ == "__main__":
    root = tk.Tk()
    app = BoundingBoxAnnotator(root)
    root.mainloop()
    
    
