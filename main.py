import io
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
        self.root.title("Image Paste Example")
        self.root.geometry("600x400")
        
        # Label to show instructions
        self.label = tk.Label(root, text="Press Ctrl+V to paste an image from clipboard")
        self.label.pack(pady=20)
        
        # Canvas to display the pasted image
        self.canvas = tk.Canvas(root, width=500, height=300, bg="gray")
        self.canvas.pack(pady=10)
        
        # Create Text widget
        self.text = tk.Text(root, wrap='word', undo=True, width=60, height=20)
        self.text.pack(padx=10, pady=10)

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
            
            # Check if it's an image
            if isinstance(image, Image.Image):
                self.process_image(image)
            else:
                self.label.config(text="Clipboard doesn't contain a valid image")
                
        except Exception as e:
            self.label.config(text=f"Error: {str(e)}")

    def process_image(self, image: Image.Image):
        """Send image to Google API for OCR processing"""
        # Get image info
        width, height = image.size
        self.label.config(text=f"Image pasted, Size: {width}x{height}")
        
        # Display the image (resized to fit canvas)
        image.thumbnail((500, 300), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(250, 150, image=self.photo)

        processed_text = get_ocr_from_image(image, self.api_key)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", processed_text)


def get_ocr_from_image(image: Image.Image, api_key: str):
    client_options = {"api_key": api_key}
    client = vision.ImageAnnotatorClient(client_options=client_options)


    # Convert PIL Image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')  # or 'JPEG'
    img_byte_arr = img_byte_arr.getvalue()
    
    # Create Vision API image
    image = vision.Image(content=img_byte_arr)
    
    # Create a Feature object for TEXT_DETECTION
    feature = vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)

    # Create AnnotateImageRequest
    request = vision.AnnotateImageRequest(
        image=image,
        features=[feature],
    )

    # Use batch_annotate_images even for one image
    response = client.batch_annotate_images(requests=[request])

    # Check for errors
    if response.responses[0].error.message:
        raise Exception(f"API Error: {response.responses[0].error.message}")

    # Extract text annotations (OCR results)
    annotations = response.responses[0].text_annotations
    if annotations:
        return annotations[0].description  # Usually the concatenated result
    else:
        return ""

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptaApp(root)
    root.mainloop()