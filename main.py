import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk

class ImageProcessorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("View and Delete Aligned_Debug Images")

        # Variables
        self.curr_dir = tk.StringVar()
        self.aligned_path = tk.StringVar()
        self.max_image_number = tk.IntVar()
        self.start_number = tk.IntVar(value=1)
        self.end_number = tk.IntVar()
        self.current_image_number = tk.IntVar()
        self.warning_message = tk.StringVar()
        self.current_image_path = tk.StringVar()

        # GUI Layout
        self.create_widgets()

        # Placeholder for images and image number
        self.images = []
        self.curr_image = None

    def create_widgets(self):
        # Create a frame on the left side for the controls
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Directory selection
        tk.Button(control_frame, text="Select Image Directory", command=self.select_directory).pack(pady=5)

        # Image number settings
        tk.Label(control_frame, text="Max Image Number:").pack()
        tk.Entry(control_frame, textvariable=self.max_image_number, state="readonly").pack(pady=5)

        tk.Label(control_frame, text="Start Number:").pack()
        start_entry = tk.Entry(control_frame, textvariable=self.start_number)
        start_entry.pack(pady=5)
        start_entry.bind("<FocusOut>", lambda event: self.adjust_current_image_number())
        start_entry.bind("<Return>", lambda event: self.adjust_current_image_number())  # Update on Enter key press

        tk.Label(control_frame, text="End Number:").pack()
        end_entry = tk.Entry(control_frame, textvariable=self.end_number)
        end_entry.pack(pady=5)
        end_entry.bind("<FocusOut>", lambda event: self.adjust_current_image_number())
        end_entry.bind("<Return>", lambda event: self.adjust_current_image_number())  # Update on Enter key press

        tk.Label(control_frame, text="Current Image Number:").pack()
        current_entry = tk.Entry(control_frame, textvariable=self.current_image_number)
        current_entry.pack(pady=5)
        current_entry.bind("<FocusOut>", lambda event: self.validate_current_image_number())
        current_entry.bind("<Return>", lambda event: self.validate_current_image_number())  # Update on Enter key press

        # Warning label
        tk.Label(control_frame, textvariable=self.warning_message, fg="red", wraplength=200).pack(pady=5)

        # Current image path label
        tk.Label(control_frame, text="Current Image Path:").pack()
        tk.Label(control_frame, textvariable=self.current_image_path, fg="blue", wraplength=200).pack(pady=5)

        # Image display canvas on the right side
        self.canvas = tk.Canvas(self)
        self.canvas.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        # Frame for buttons directly below the canvas
        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.TOP, fill=tk.X)

        # Navigation buttons on the left
        self.prev_button = tk.Button(button_frame, text="Previous Image", command=self.previous_image)
        self.prev_button.pack(side=tk.LEFT, padx=20, pady=10)

        self.next_button = tk.Button(button_frame, text="Next Image", command=self.next_image)
        self.next_button.pack(side=tk.LEFT, padx=20, pady=10)

        # Progress bar to the right of the Next Image button
        self.progress = Progressbar(button_frame, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(side=tk.LEFT, padx=20, pady=10, expand=True)

        # Delete button on the right
        self.delete_button = tk.Button(button_frame, text="Delete Image", command=self.delete_image)
        self.delete_button.pack(side=tk.RIGHT, padx=20, pady=10)

        # Bind canvas click
        self.canvas.bind("<Button-1>", lambda event: self.next_image())

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.curr_dir.set(directory)
            self.aligned_path.set(os.path.join(directory, "..", "aligned"))
            self.load_images()

    def load_images(self):
        # Get all image files in the selected directory
        all_files = [f for f in os.listdir(self.curr_dir.get()) if f.endswith('.jpg')]
        if not all_files:
            messagebox.showerror("Error", "No images found in the directory.")
            return

        # Convert filenames to integers and find the max image number
        self.images = sorted([int(os.path.splitext(f)[0]) for f in all_files])
        if self.images:
            self.max_image_number.set(max(self.images))

        self.start_number.set(1)
        self.end_number.set(self.max_image_number.get())
        self.current_image_number.set(self.start_number.get())

        # Load the first image
        self.load_image(self.start_number.get())

    def load_image(self, image_number):
        # Load the image corresponding to the given image number
        filename = os.path.join(self.curr_dir.get(), str(image_number).zfill(5) + ".jpg")
        aligned_filename_0 = os.path.join(self.aligned_path.get(), str(image_number).zfill(5) + "_0.jpg")
        aligned_filename_1 = os.path.join(self.aligned_path.get(), str(image_number).zfill(5) + "_1.jpg")

        if not os.path.isfile(filename):
            self.warning_message.set(f"Image {filename} does not exist.")
            self.next_image()  # Skip missing images
            return

        if not (os.path.isfile(aligned_filename_0) or os.path.isfile(aligned_filename_1)):
            self.warning_message.set(f"Warning: {filename} does not exist in aligned directory.")
        else:
            self.warning_message.set("")  # Clear any previous warnings

        # Display the current image path
        self.current_image_path.set(filename)

        # Open image using PIL and display on the canvas
        image = Image.open(filename)
        image_width, image_height = image.size
        self.canvas.config(width=image_width, height=image_height)
        self.curr_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.curr_image)

        # Update the progress bar
        self.update_progress_bar()

        # Adjust the window size dynamically to fit the canvas and buttons
        self.update_idletasks()  # Ensure all geometry updates have been processed
        self.geometry("")  # Empty string resizes the window to fit all content

    def next_image(self):
        # Increment the current image number and load the next image
        next_image_num = self.current_image_number.get() + 1
        if next_image_num > self.end_number.get():
            messagebox.showinfo("End of Range", "Reached the end of the specified range.")
            return
        self.current_image_number.set(next_image_num)
        self.load_image(next_image_num)

    def previous_image(self):
        # Decrement the current image number and load the previous image
        prev_image_num = self.current_image_number.get() - 1
        while prev_image_num >= self.start_number.get():
            if os.path.isfile(os.path.join(self.curr_dir.get(), str(prev_image_num).zfill(5) + ".jpg")):
                self.current_image_number.set(prev_image_num)
                self.load_image(prev_image_num)
                return
            prev_image_num -= 1
        messagebox.showinfo("Start of Range", "Reached the start of the specified range.")

    def delete_image(self):
        # Delete the current image and move to the next one
        image_number = self.current_image_number.get()
        filename = os.path.join(self.curr_dir.get(), str(image_number).zfill(5) + ".jpg")
        if os.path.isfile(filename):
            os.remove(filename)
            self.warning_message.set(f"Image {filename} deleted.")
        self.next_image()

    def adjust_current_image_number(self):
        """Adjust the current image number based on the start number."""
        if self.current_image_number.get() < self.start_number.get():
            self.current_image_number.set(self.start_number.get())
        self.validate_current_image_number()
        self.load_image(self.current_image_number.get())

    def validate_current_image_number(self):
        """Ensure the current image number is within the start and end range."""
        if self.current_image_number.get() < self.start_number.get():
            self.current_image_number.set(self.start_number.get())
        elif self.current_image_number.get() > self.end_number.get():
            self.current_image_number.set(self.end_number.get())
        self.load_image(self.current_image_number.get())

    def update_progress_bar(self):
        """Update the progress bar based on the current image position."""
        total_images = self.end_number.get() - self.start_number.get() + 1
        current_progress = self.current_image_number.get() - self.start_number.get() + 1
        self.progress['value'] = (current_progress / total_images) * 100


if __name__ == "__main__":
    app = ImageProcessorApp()
    app.mainloop()
