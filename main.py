import io
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
        self.root = root
        self.root.title("Scripta - OCR Transcription Helper")
        self.root.geometry("500x800")

        # Label to show instructions
        self.label = tk.Label(root, text="Press Ctrl+V to paste an image from clipboard")
        self.label.pack(pady=20)
        
        # Canvas to display the pasted image
        self.canvas = tk.Canvas(root, width=450, height=300, bg="gray")
        self.canvas.pack(pady=10)


        #label for confidence level key
        key_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2, 
                            bg="lightgray")
        key_frame.pack(pady=5, padx=10, fill=tk.X)
        
        tk.Label(key_frame, text="Confidence Key:", 
                font=("Arial", 10, "bold"), bg="lightgray").pack(side=tk.LEFT, padx=10)
        
        tk.Label(key_frame, text="● High (≥95%)", 
                foreground="green", bg="lightgray", 
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Label(key_frame, text="● Medium (85-94%)", 
                foreground="orange", bg="lightgray", 
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Label(key_frame, text="● Low (<85%)", 
                foreground="red", bg="lightgray", 
                font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Create Text widget
        self.text = tk.Text(root, wrap='word', undo=True, width=60, height=20)
        self.text.pack(padx=10, pady=10)

        # Configure tags for confidence colors
        self.text.tag_configure("high", foreground="green")
        self.text.tag_configure("medium", foreground="orange")
        self.text.tag_configure("low", foreground="red")


        # Bind Ctrl+V
        self.root.bind('<Control-v>', self.paste_image)

        # Get the user's API key from a dialog box
        dialog = CredentialDialog(root)
        self.api_key = dialog.show()

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