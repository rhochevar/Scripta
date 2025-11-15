import io
import os
import json
import string
import tkinter as tk
from credential_dialog import CredentialDialog
from PIL import Image, ImageGrab, ImageTk
from google.cloud import vision
from google.cloud.vision_v1 import types

class ScriptaApp:
    root: tk.Tk
    api_key: str

    def __init__(self, root: tk.Tk):
        self.config_file = "config.json"
        self.root = root
        self.root.title("Scripta - OCR Transcription Helper")
        self.root.geometry("500x850")
        self.root.resizable(False,False)
        root.configure(bg="#202225")

        # Button to enter the Google Cloud Vision API key
        self.api_key_button = tk.Button(root, text="Configure API Key", command=self.configure_api_key)
        self.api_key_button.pack(anchor=tk.NE, padx=0, pady=5)

        # Label to show instructions
        self.label = tk.Label(root, text="Press Ctrl+V to paste an image from clipboard")
        self.label.configure(bg="#202225", foreground="white")
        self.label.pack(pady=20)
        
        # Canvas to display the pasted image
        self.canvas = tk.Canvas(root, width=450, height=300, bg="#111111")
        self.canvas.pack(pady=10)


        #label for confidence level key
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
        self.text = tk.Text(root, wrap='word', undo=True, width=60, height=20, selectbackground="black")
        self.text.pack(padx=10, pady=10)

        # Text tags for confidence levels
        self.text.tag_configure("high", foreground="#2C7A7B")
        self.text.tag_configure("medium", foreground="#B7791F")
        self.text.tag_configure("low", foreground="#B91C1C")

        # Button to copy text widget's content to clipboard
        self.copy_button = tk.Button(root, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(pady=(5, 10))

        # Bind Ctrl+V
        self.root.bind('<Control-v>', self.paste_image)

        self.load_config()

    def load_config(self):
        """Load API key from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key')
                    if self.api_key:
                        print("API key loaded from config")
                    else:
                        print("No API key found in config")
            else:
                print("No config file found")
        except Exception as e:
            print(e)

    def configure_api_key(self):
        dialog = CredentialDialog(self.root)
        new_api_key = dialog.show()
        self.api_key = new_api_key
        

    def paste_image(self, event=None):
        try:
            # Get image from clipboard
            image = ImageGrab.grabclipboard()
            
            if image is None:
                self.label.config(text="No image in clipboard!")
                return
            
            # Check if it's an image, if true send for processing
            if isinstance(image, Image.Image):
                self.process_image(image)
            else:
                self.label.config(text="Clipboard doesn't contain a valid image")
                
        except Exception as e:
            self.label.config(text=f"Error: {str(e)}")

    def process_image(self, image: Image.Image):
        """Send image to Google API for OCR processing & display results"""
        # Get image info
        width, height = image.size
        self.label.config(text=f"Image pasted, Size: {width}x{height}")
        
        # Display the image (resized to fit canvas)
        image.thumbnail((400, 300), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(250, 150, image=self.photo)

        processed_text = get_ocr_from_image(image, self.api_key)
        self.text.delete("1.0", tk.END)
        
        word_index = 0

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
        content = self.text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()
        self.label.config(text="Text copied to clipboard!")


def get_ocr_from_image(image: Image.Image, api_key: str):
    client_options = {"api_key": api_key}
    client = vision.ImageAnnotatorClient(client_options=client_options)


    # Convert PIL Image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')  # or 'JPEG'
    img_byte_arr = img_byte_arr.getvalue()
    
    # Create Vision API image from bytes
    image = vision.Image(content=img_byte_arr)
    
    # Create a Feature object for DOCUMENT_TEXT_DETECTION
    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    # Create AnnotateImageRequest
    request = vision.AnnotateImageRequest(
        image=image,
        features=[feature],
    )

    # Use document text detection for OCR
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
    root = tk.Tk()
    app = ScriptaApp(root)
    root.mainloop()