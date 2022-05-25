import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showerror

import cv2
import numpy as np
from PIL import Image, ImageTk


class MainGUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Pixel Chooser")
        self.geometry("900x600")

        self.canvas_color = (255, 255, 255)

        self.original_image = None
        self.left_image = None
        self.processed_image = None
        self.resized_image = None
        self.zoomed_image = None
        self.zoomed_processed_image = None

        self.second_zoom = tk.BooleanVar()
        self.second_zoom.set(True)

        self.image_state = tk.StringVar()
        self.image_state.set(None)

        self.open_btn = tk.Button(text="OPEN", command=self.open_btn_command)
        self.open_btn.place(anchor=tk.NE, relx=0.475, rely=0.05, relwidth=0.075, relheight=0.05)
        self.save_btn = tk.Button(text="SAVE", command=self.save_btn_command, state="disabled")
        self.save_btn.place(anchor=tk.NW, relx=0.525, rely=0.05, relwidth=0.075, relheight=0.05)

        self.edit_color_btn = tk.Button(master=self, text="EDIT COLOR", command=self.edit_color_btn_command)
        self.edit_color_btn.place(anchor=tk.NW, relx=0.625, rely=0.05, relwidth=0.1, relheight=0.05)
        self.color_frame = tk.Frame(master=self, bg=self._from_rgb(self.canvas_color), highlightbackground="black",
                                    highlightthickness=2)
        self.color_frame.place(anchor=tk.NW, relx=0.75, rely=0.05, relwidth=0.05, relheight=0.05)

        self.zoom_out_btn = tk.Button(text="ZOOM OUT", command=self.zoom_out_btn_command, state="disabled")
        self.zoom_out_btn.place(anchor=tk.NW, relx=0.025, rely=0.05, relwidth=0.1, relheight=0.05)
        self.picker_radio = tk.Radiobutton(text="PIXEL PICKER", value="PICKER", variable=self.image_state,
                                           command=self.picker_radio_command, state="disabled")
        self.picker_radio.place(anchor=tk.NW, relx=0.2, rely=0.025)
        self.zoom_in_radio = tk.Radiobutton(text="ZOOM IN", value="ZOOM", variable=self.image_state,
                                            command=self.zoom_in_radio_command, state="disabled")
        self.zoom_in_radio.place(anchor=tk.NW, relx=0.2, rely=0.075)

        self.second_zoom_checkbox = tk.Checkbutton(text="Zoom-In 2nd Canvas", variable=self.second_zoom,
                                                   command=self.second_zoom_checkbox_command, state="disabled")
        self.second_zoom_checkbox.place(anchor=tk.NE, relx=0.975, rely=0.05)

        self.image_viewer = ImageViewer(master=self)
        self.image_viewer.place(anchor=tk.N, relx=0.5, rely=0.15, relwidth=1, relheight=0.8)

    def open_btn_command(self):
        open_path = askopenfilename()
        if open_path == '':
            return
        image = cv2.imread(open_path)
        if image is None:
            showerror("Pixel Chooser", "Unable to Read Image File...")
            return
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.original_image = image.copy()
        self.left_image = image.copy()
        self.processed_image = np.full(image.shape, self.canvas_color, dtype=np.uint8)
        self.resized_image = image.copy()
        self.zoomed_image = None
        self.zoomed_processed_image = None
        self.zoom_in_radio['state'] = "normal"
        self.picker_radio['state'] = "normal"
        self.zoom_out_btn['state'] = "normal"
        self.save_btn['state'] = "normal"
        self.second_zoom_checkbox['state'] = "normal"
        self.image_viewer.show_image()

    def save_btn_command(self):
        save_path = asksaveasfilename()
        if save_path == '':
            return
        if self.zoomed_processed_image is not None and self.second_zoom.get():
            cv2.imwrite(save_path, cv2.cvtColor(self.zoomed_processed_image, cv2.COLOR_RGB2BGR))
        else:
            cv2.imwrite(save_path, cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2BGR))

    def edit_color_btn_command(self):
        color = askcolor()[0]
        if color is None:
            return
        self.color_frame.configure(background=self._from_rgb(color))
        bool_mask = np.logical_and.reduce(self.left_image == self.canvas_color, axis=-1)
        self.left_image[bool_mask] = color
        bool_mask = np.logical_and.reduce(self.processed_image == self.canvas_color, axis=-1)
        self.processed_image[bool_mask] = color
        self.canvas_color = color
        self.image_viewer.resize()

    def zoom_out_btn_command(self):
        self.zoomed_image = None
        self.zoomed_processed_image = None
        self.image_viewer.resize()

    def picker_radio_command(self):
        self.image_viewer.deactivate_zoom()
        self.image_viewer.activate_pick()

    def zoom_in_radio_command(self):
        self.image_viewer.deactivate_pick()
        self.image_viewer.activate_zoom()

    def second_zoom_checkbox_command(self):
        self.image_viewer.resize()

    @staticmethod
    def _from_rgb(rgb):
        r, g, b = rgb
        return f'#{r:02x}{g:02x}{b:02x}'


class ImageViewer(tk.Frame):
    def __init__(self, master: MainGUI):
        tk.Frame.__init__(self, master=master)
        self.shown_image_left = None
        self.shown_image_right = None
        self.zoom_start_x = 0
        self.zoom_start_y = 0
        self.zoom_end_x = 0
        self.zoom_end_y = 0
        self.zoom_rectangle = None
        self.ratio = 0

        self.left_frame = tk.Frame(master=self, background="darkgray")
        self.left_frame.place(anchor=tk.N, relx=0.25, rely=0, relwidth=0.45, relheight=1)
        self.right_frame = tk.Frame(master=self, background="darkgray")
        self.right_frame.place(anchor=tk.N, relx=0.75, rely=0, relwidth=0.45, relheight=1)

        self.left_canvas = tk.Canvas(master=self.left_frame, background="darkgray", width=500, height=500, bd=0)
        self.left_canvas.place(anchor=tk.CENTER, relx=0.5, rely=0.5)
        self.right_canvas = tk.Canvas(master=self.right_frame, background="darkgray", width=500, height=500, bd=0)
        self.right_canvas.place(anchor=tk.CENTER, relx=0.5, rely=0.5)

    def show_image(self):
        self.clear_canvases()

        if self.master.zoomed_image is not None:
            image = self.master.zoomed_image.copy()
        else:
            image = self.master.left_image.copy()

        if self.master.zoomed_processed_image is not None and self.master.second_zoom.get():
            processed_image = self.master.zoomed_processed_image.copy()
        else:
            processed_image = self.master.processed_image.copy()

        canvas_height = self.left_frame.winfo_height()
        canvas_width = self.left_frame.winfo_width()

        new_left_width, new_left_height, left_height = self._calculate_new_size(image, canvas_height, canvas_width)
        new_right_width, new_right_height, right_height = self._calculate_new_size(processed_image, canvas_height,
                                                                                   canvas_width)

        self.ratio = left_height / new_left_height

        self.shown_image_left = cv2.resize(image, (new_left_width, new_left_height),
                                           interpolation=cv2.INTER_NEAREST_EXACT)
        self.master.resized_image = self.shown_image_left.copy()
        self.shown_image_left = ImageTk.PhotoImage(Image.fromarray(self.shown_image_left))

        self.shown_image_right = cv2.resize(processed_image, (new_right_width, new_right_height))
        self.shown_image_right = ImageTk.PhotoImage(Image.fromarray(self.shown_image_right))

        self.left_canvas.configure(height=new_left_height, width=new_left_width)
        self.left_canvas.create_image(self.left_canvas.winfo_width() / 2, self.left_canvas.winfo_height() / 2,
                                      anchor=tk.CENTER, image=self.shown_image_left)
        self.right_canvas.configure(height=new_right_height, width=new_right_width)
        self.right_canvas.create_image(self.right_canvas.winfo_width() / 2, self.right_canvas.winfo_height() / 2,
                                       anchor=tk.CENTER, image=self.shown_image_right)

        self.master.bind("<Configure>", self.resize)

    @staticmethod
    def _calculate_new_size(image, canvas_height, canvas_width):
        height, width, channels = image.shape
        ratio = height / width

        new_width = width
        new_height = height

        if height > canvas_height or width > canvas_width:
            if ratio < 1:
                new_width = canvas_width
                new_height = int(new_width * ratio)
                if new_height > canvas_height:
                    new_height = canvas_height
                    new_width = int(new_height * (1 / ratio))
            else:
                new_height = canvas_height
                new_width = int(new_height * (1 / ratio))
                if new_width > canvas_width:
                    new_width = canvas_width
                    new_height = int(new_width * ratio)
        return new_width, new_height, height

    def activate_pick(self):
        self.left_canvas.bind("<ButtonPress>", self.pick_pixel)

    def deactivate_pick(self):
        self.left_canvas.unbind("<ButtonPress>")

    def activate_zoom(self):
        self.left_canvas.bind("<ButtonPress>", self.start_zoom)
        self.left_canvas.bind("<B1-Motion>", self.zoom)
        self.left_canvas.bind("<ButtonRelease>", self.end_zoom)

    def deactivate_zoom(self):
        self.left_canvas.unbind("<ButtonPress>")
        self.left_canvas.unbind("<B1-Motion>")
        self.left_canvas.unbind("<ButtonRelease>")

    def pick_pixel(self, event):
        picked_color = self.master.resized_image[event.y][event.x - 1]
        bool_mask = np.logical_and.reduce(self.master.original_image == picked_color, axis=-1)
        self.master.processed_image[bool_mask] = picked_color
        self.master.left_image[bool_mask] = self.master.canvas_color
        self.resize()

    def start_zoom(self, event):
        self.zoom_start_x = event.x
        self.zoom_start_y = event.y

    def zoom(self, event):
        if self.zoom_rectangle:
            self.left_canvas.delete(self.zoom_rectangle)

        self.zoom_end_x = event.x
        self.zoom_end_y = event.y

        self.zoom_rectangle = self.left_canvas.create_rectangle(self.zoom_start_x, self.zoom_start_y, self.zoom_end_x,
                                                                self.zoom_end_y, width=1, outline="white")

    def end_zoom(self, event):
        if self.zoom_start_x <= self.zoom_end_x and self.zoom_start_y <= self.zoom_end_y:
            start_x = int(self.zoom_start_x * self.ratio)
            start_y = int(self.zoom_start_y * self.ratio)
            end_x = int(self.zoom_end_x * self.ratio)
            end_y = int(self.zoom_end_y * self.ratio)
        elif self.zoom_start_x > self.zoom_end_x and self.zoom_start_y <= self.zoom_end_y:
            start_x = int(self.zoom_end_x * self.ratio)
            start_y = int(self.zoom_start_y * self.ratio)
            end_x = int(self.zoom_start_x * self.ratio)
            end_y = int(self.zoom_end_y * self.ratio)
        elif self.zoom_start_x <= self.zoom_end_x and self.zoom_start_y > self.zoom_end_y:
            start_x = int(self.zoom_start_x * self.ratio)
            start_y = int(self.zoom_end_y * self.ratio)
            end_x = int(self.zoom_end_x * self.ratio)
            end_y = int(self.zoom_start_y * self.ratio)
        else:
            start_x = int(self.zoom_end_x * self.ratio)
            start_y = int(self.zoom_end_y * self.ratio)
            end_x = int(self.zoom_start_x * self.ratio)
            end_y = int(self.zoom_start_y * self.ratio)

        x = slice(start_x, end_x, 1)
        y = slice(start_y, end_y, 1)

        if self.master.zoomed_image is not None:
            self.master.zoomed_image = self.master.zoomed_image[y, x]
        else:
            self.master.zoomed_image = self.master.left_image[y, x]

        if self.master.zoomed_processed_image is not None:
            self.master.zoomed_processed_image = self.master.zoomed_processed_image[y, x]
        else:
            self.master.zoomed_processed_image = self.master.processed_image[y, x]

        self.show_image()

    def resize(self, event=None):
        self.show_image()
        self.update_idletasks()

    def clear_canvases(self):
        self.left_canvas.delete("all")
        self.right_canvas.delete("all")


if __name__ == '__main__':
    root = MainGUI()
    root.mainloop()
