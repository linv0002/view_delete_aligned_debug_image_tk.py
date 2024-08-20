import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk

class ImageProcessorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image Viewer and Scanner")

        # Variables
        self.curr_dir = tk.StringVar()
        self.max_image_number = tk.IntVar()
        self.start_number = tk.IntVar(value=1)
        self.end_number = tk.IntVar()
        self.current_image_number = tk.IntVar()
        self.warning_message = tk.StringVar()
        self.current_image_path = tk.StringVar()
        self.scan_delay = tk.IntVar(value=100)  # Default delay of 100 ms
        self.is_advancing = False  # For continuous scanning
        self.show_merged = tk.BooleanVar()  # Checkbox for showing merged images
        self.make_backup = tk.BooleanVar()  # Checkbox for making backups

        # Determine if the merged directory exists
        self.merged_dir_exists = False

        # GUI Layout
        self.create_widgets()

        # Placeholder for images and image number
        self.images = []
        self.curr_image = None
        self.merged_image = None  # Placeholder for merged image

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

        # Checkbox for showing merged images
        self.show_merged_checkbox = tk.Checkbutton(
            control_frame, text="Show Merged", variable=self.show_merged, command=self.toggle_merged_options)
        self.show_merged_checkbox.pack(pady=5)

        # "Use Original" button
        self.use_original_button = tk.Button(control_frame, text="Use Original", command=self.use_original)
        self.use_original_button.pack(pady=5)
        self.use_original_button.pack_forget()  # Hide initially

        # "Make Backup" checkbox
        self.make_backup_checkbox = tk.Checkbutton(
            control_frame, text="Make Backup", variable=self.make_backup)
        self.make_backup_checkbox.pack(pady=5)
        self.make_backup_checkbox.pack_forget()  # Hide initially

        # Image display canvas on the right side
        self.canvas = tk.Canvas(self)
        self.canvas.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        # Frame for buttons directly below the canvas
        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.TOP, fill=tk.X)

        # Navigation buttons
        self.prev_scan_button = tk.Button(button_frame, text="Previous Scan")
        self.prev_scan_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.prev_scan_button.bind("<ButtonPress-1>", self.start_previous_image_loop)
        self.prev_scan_button.bind("<ButtonRelease-1>", self.stop_image_loop)

        self.prev_button = tk.Button(button_frame, text="Previous Image", command=self.previous_image)
        self.prev_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.next_button = tk.Button(button_frame, text="Next Image", command=self.next_image)
        self.next_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.next_scan_button = tk.Button(button_frame, text="Forward Scan")
        self.next_scan_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.next_scan_button.bind("<ButtonPress-1>", self.start_next_image_loop)
        self.next_scan_button.bind("<ButtonRelease-1>", self.stop_image_loop)

        # Time delay input box and speed label
        tk.Label(button_frame, text="Speed (ms):").pack(side=tk.LEFT, padx=5)
        delay_entry = tk.Entry(button_frame, textvariable=self.scan_delay, width=5)
        delay_entry.pack(side=tk.LEFT, padx=5)

        # Current image number / end number and progress bar
        self.image_number_label = tk.Label(button_frame, text="0/0")
        self.image_number_label.pack(side=tk.LEFT, padx=10)

        self.progress = Progressbar(button_frame, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

        # Delete button
        self.delete_button = tk.Button(button_frame, text="Delete Debug Image", command=self.delete_image)
        self.delete_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # Bind canvas click
        self.canvas.bind("<Button-1>", lambda event: self.next_image())

    def toggle_merged_options(self):
        if self.show_merged.get():
            self.use_original_button.pack(pady=5)
            self.make_backup_checkbox.pack(pady=5)
        else:
            self.use_original_button.pack_forget()
            self.make_backup_checkbox.pack_forget()

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.curr_dir.set(directory)
            # Check for the merged directory one level up
            merged_dir = os.path.join(os.path.dirname(directory), "merged")
            if os.path.exists(merged_dir):
                self.merged_dir_exists = True
                self.show_merged_checkbox.pack(pady=5)  # Show checkbox if merged directory exists
            else:
                self.merged_dir_exists = False
                self.show_merged_checkbox.pack_forget()  # Hide checkbox if merged directory does not exist
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

    def load_image(self, image_number=None):
        if image_number is None:
            image_number = self.current_image_number.get()

        # Load the image corresponding to the given image number
        filename = os.path.join(self.curr_dir.get(), str(image_number).zfill(5) + ".jpg")
        merged_filename = os.path.join(os.path.dirname(self.curr_dir.get()), "merged", str(image_number).zfill(5) + ".png")

        if not os.path.isfile(filename):
            self.warning_message.set(f"Image {filename} does not exist.")
            self.next_image()  # Skip missing images
            return

        if self.show_merged.get() and self.merged_dir_exists and os.path.isfile(merged_filename):
            # Load both images side by side
            self.warning_message.set("")  # Clear any previous warnings
            debug_image = Image.open(filename)
            merged_image = Image.open(merged_filename)
            self.display_side_by_side(debug_image, merged_image)
        else:
            # Load only the debug image
            self.warning_message.set("")  # Clear any previous warnings
            image = Image.open(filename)
            self.display_single_image(image)

        # Display the current image path
        self.current_image_path.set(filename)

        # Update the progress bar and image number label
        self.update_progress()

    def display_side_by_side(self, debug_image, merged_image):
        # Get the canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Resize images to fit side by side on the canvas while maintaining aspect ratios
        debug_image = self.resize_image_to_fit(debug_image, canvas_width // 2, canvas_height)
        merged_image = self.resize_image_to_fit(merged_image, canvas_width // 2, canvas_height)

        # Combine images side by side
        combined_image = Image.new('RGB', (debug_image.width + merged_image.width, max(debug_image.height, merged_image.height)))
        combined_image.paste(debug_image, (0, 0))
        combined_image.paste(merged_image, (debug_image.width, 0))

        # Display the combined image on the canvas
        self.curr_image = ImageTk.PhotoImage(combined_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.curr_image)

    def display_single_image(self, image):
        # Get the canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Resize the image to fit the canvas while maintaining aspect ratio
        image = self.resize_image_to_fit(image, canvas_width, canvas_height)

        # Display the image on the canvas
        self.curr_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.curr_image)

    def resize_image_to_fit(self, image, max_width, max_height):
        """Resize the image to fit within the given width and height while maintaining aspect ratio."""
        img_width, img_height = image.size
        scale = min(max_width / img_width, max_height / img_height)
        new_size = (int(img_width * scale), int(img_height * scale))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def update_progress(self):
        """Update the progress bar and image number label."""
        total_images = self.end_number.get() - self.start_number.get() + 1
        current_progress = self.current_image_number.get() - self.start_number.get() + 1
        self.progress['value'] = (current_progress / total_images) * 100
        self.image_number_label.config(text=f"{self.current_image_number.get()}/{self.end_number.get()}")

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
            filename = os.path.join(self.curr_dir.get(), str(prev_image_num).zfill(5) + ".jpg")
            if os.path.isfile(filename):
                self.current_image_number.set(prev_image_num)
                self.load_image(prev_image_num)
                return
            prev_image_num -= 1
        messagebox.showinfo("Start of Range", "Reached the start of the specified range.")

    def start_next_image_loop(self, event):
        """Start continuously advancing images forward."""
        self.is_advancing = True
        self.advance_images("next")

    def start_previous_image_loop(self, event):
        """Start continuously advancing images backward."""
        self.is_advancing = True
        self.advance_images("previous")

    def stop_image_loop(self, event=None):
        """Stop continuous image advancement."""
        self.is_advancing = False

    def advance_images(self, direction):
        if self.is_advancing:
            if direction == "next":
                self.next_image()
            elif direction == "previous":
                self.previous_image()
            self.after(self.scan_delay.get(), lambda: self.advance_images(direction))

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

    def use_original(self):
        image_number = str(self.current_image_number.get()).zfill(5)
        parent_dir = os.path.dirname(self.curr_dir.get())
        original_image_path = os.path.join(parent_dir, image_number + ".png")
        merged_image_path = os.path.join(parent_dir, "merged", image_number + ".png")
        aligned_dir = os.path.join(parent_dir, "aligned")

        # Backup the merged file if "Make Backup" is checked
        if self.make_backup.get() and os.path.exists(merged_image_path):
            backup_path = merged_image_path + ".bak"
            shutil.copy2(merged_image_path, backup_path)
            print(f"Backup of {merged_image_path} saved as {backup_path}")

        # Copy the original image to the merged directory
        shutil.copy2(original_image_path, merged_image_path)
        print(f"Copied {original_image_path} to {merged_image_path}")

        # Delete corresponding files in the aligned directory
        for file in os.listdir(aligned_dir):
            if file.startswith(image_number) and file.endswith(".jpg"):
                aligned_file_path = os.path.join(aligned_dir, file)
                if self.make_backup.get():
                    backup_aligned_path = aligned_file_path + ".bak"
                    shutil.copy2(aligned_file_path, backup_aligned_path)
                    print(f"Backup of {aligned_file_path} saved as {backup_aligned_path}")
                os.remove(aligned_file_path)
                print(f"Deleted {aligned_file_path}")

        # Advance to the next image
        self.next_image()


if __name__ == "__main__":
    app = ImageProcessorApp()
    app.mainloop()
