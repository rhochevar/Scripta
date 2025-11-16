'''Scripta App'''
import io
import os
import json
import string
import tkinter as tk
from PIL import Image, ImageGrab, ImageTk
from google.cloud import vision
from credential_dialog import CredentialDialog

class ScriptaApp:
    """Uses the Google Cloud Vision API for OCR to more efficiently transcribe documents"""
    root: tk.Tk
    api_key: str
    canvas_visible : bool = True
    config_file = "config.json"
    photo : ImageTk.PhotoImage

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Scripta - OCR Transcription Helper")
        self.root.geometry("500x865")
        self.root.resizable(False,True)
        root.configure(bg="#202225")

        # Button to enter the Google Cloud Vision API key
        self.api_key_button = tk.Button(
            root,
            text="Configure API Key",
            command=self.configure_api_key
        )
        self.api_key_button.pack(anchor=tk.NE, padx=0, pady=5)

        # Button to toggle image preview for users with lower resolutions
        self.toggle_preview_button = tk.Button(
            root,
            text="Toggle Image Preview",
            command=self.toggle_preview
        )
        self.toggle_preview_button.pack(anchor=tk.NE, padx=0, pady=0)

        # Label to show instructions
        self.label = tk.Label(root, text="Press Ctrl+V to paste an image from clipboard")
        self.label.configure(bg="#202225", foreground="white")
        self.label.pack(pady=20)

        # Canvas to display the pasted image
        self.canvas = tk.Canvas(root, width=450, height=300, bg="#111111")
        self.canvas.pack(pady=10)


        # Confidence level key
        key_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2,
                            bg="lightgrey")
        key_frame.pack(pady=5, padx=10, fill=tk.X)

        tk.Label(key_frame, text="Confidence Key:",
                font=("Arial", 10, "bold"), bg="lightgrey").pack(side=tk.LEFT, padx=10)

        tk.Label(key_frame, text="● High (≥95%)",
                foreground="#2C7A7B", bg="lightgrey",
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        tk.Label(key_frame, text="● Medium (85-94%)",
                foreground="#B7791F", bg="lightgrey",
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        tk.Label(key_frame, text="● Low (<85%)",
                foreground="#B91C1C", bg="lightgrey",
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        # Text widget for results & editing
        self.text = tk.Text(
            root,
            wrap='word',
            undo=True,
            width=60,
            height=20,
            selectbackground="black"
        )
        self.text.pack(padx=10, pady=10)

        # Text tags for confidence level colors
        self.text.tag_configure("high", foreground="#2C7A7B")
        self.text.tag_configure("medium", foreground="#B7791F")
        self.text.tag_configure("low", foreground="#B91C1C")

        # Button to copy text widget's content to clipboard
        self.copy_button = tk.Button(root, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(pady=(5, 10))

        # Bind Ctrl+V
        self.root.bind('<Control-v>', self.paste_image)

        # Load configuration file on start
        self.load_config()

    def load_config(self):
        """Loads an API key from json file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding="utf-8") as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key')
        except Exception: # pylint: disable=broad-exception-caught
            pass # Proceed without configuration if config.json is not found or api_key is missing

    def configure_api_key(self):
        """Opens the API key menu"""
        dialog = CredentialDialog(self.root)
        new_api_key = dialog.show()
        self.api_key = new_api_key

    def toggle_preview(self):
        """Toggles visibility of the canvas"""
        if self.canvas_visible:
            self.canvas.pack_forget()
            self.canvas_visible = False
        else:
            self.canvas.pack(after=self.label)
            self.canvas_visible = True

    def paste_image(self, _event):
        """Uses pillow ImageGrab to paste, and send the data to process_image()"""
        try:
            # Attempt to get image from clipboard
            image = ImageGrab.grabclipboard()

            if image is None:
                self.label.config(text="No image in clipboard!")
                return

            # Ensure clipboard data is a valid image, if true send for processing
            if isinstance(image, Image.Image):
                self.process_image(image)
            else:
                self.label.config(text="Clipboard doesn't contain a valid image")

        except Exception as e: # pylint: disable=broad-exception-caught
            self.label.config(text=f"Error: {str(e)}")

    def process_image(self, image: Image.Image):
        """Displays the image preview of the provided screenshot, 
        and displays results of the Google Cloud Vision API response"""
        # Get image dimensions
        width, height = image.size
        self.label.config(text=f"Image pasted, Size: {width}x{height}")

        # Display the image (resized to fit canvas)
        image.thumbnail((400, 300), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(250, 150, image=self.photo)

        # Store API response and clear the text widget
        processed_text = get_ocr_from_image(image, self.api_key)
        self.text.delete("1.0", tk.END)

        word_index = 0

        # Write returned OCR data to the text widget
        for word in processed_text:

            text = word['text']
            conf = word['confidence']

            # Color code by confidence
            if conf >= 0.95:
                tag = "high"
            elif conf >= 0.85:
                tag = "medium"
            else:
                tag = "low"

            # Check for punctuation and adjust space accordingly
            if text in string.punctuation or word_index <= 0:
                line = f"{text}"
            else:
                line = f" {text}"

            start_idx = self.text.index(tk.INSERT)
            self.text.insert(tk.INSERT, line)
            end_idx = self.text.index(tk.INSERT)
            self.text.tag_add(tag, start_idx, end_idx)

            word_index += 1

    def copy_to_clipboard(self):
        """Copies all text currently in the text widget to the users clipboard"""
        content = self.text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()
        self.label.config(text="Text copied to clipboard!")


def get_ocr_from_image(image: Image.Image, api_key: str):
    """Sends image data to the Google Cloud Vision API for text detection"""
    client_options = {"api_key": api_key}
    client = vision.ImageAnnotatorClient(client_options=client_options)

    # Convert PIL Image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')  # or 'JPEG'
    img_byte_arr = img_byte_arr.getvalue()

    # Create Vision API image from bytes
    image = vision.Image(content=img_byte_arr)

    # Use DOCUMENT_TEXT_DETECTION for OCR
    response = client.document_text_detection(image=image) # pylint: disable=no-member

    words_data = []

    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])

                    words_data.append({
                        'text': word_text,
                        'confidence': word.confidence
                    })

    return words_data

if __name__ == "__main__":
    _root = tk.Tk()
    app = ScriptaApp(_root)
    _root.mainloop()
