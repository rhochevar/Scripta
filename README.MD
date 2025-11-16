# Scripta - OCR Transcription Helper

A Python application built with tkinter to make transcribing documents more efficient using the [Google Cloud Vision API](https://console.cloud.google.com/marketplace/product/google/vision.googleapis.com) for OCR.  

OCR data is returned to a text window which can be used to make edits and corrections to words that were returned with a low confidence level.  

This data can then be copied with the press of a button to be used anywhere.

![Scripta-example](./Scripta-example.png)

Scripta requires a valid Google Cloud Vision API key in order to function.  
Google Cloud offers free credits to new users, and Cloud Vision is free for the first 1000 units per month.  
More details on Cloud Vision pricing can be found [here](https://cloud.google.com/vision/pricing).  

To setup a Cloud Vision API key, once you are logged into the [Google Cloud Console](https://console.cloud.google.com/):
1. Create a new project, or select an existing one
2. Navigate to APIs & Services -> Library
3. Search for and enable the [Cloud Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com?)
4. Navigate to APIs & Services -> Credentials
5. Select Create Credentials -> API Key

## Using Scripta
- First, press the Configure API Key button and enter your Google Cloud Vision API key (this will be stored locally in a config.json file).  
- Next, simply take a screenshot (Win+Shift+S on Windows), then paste this into the Scripta Window.  

Scripta will automatically send this image to the Cloud Vision API and return OCR data with color coded confidence levels. 

## Installation

### Windows
Windows executable available [in the releases section](https://github.com/rhochevar/Scripta/releases/latest).

### Linux
```
git clone https://github.com/rhochevar/Scripta  
cd scripta  
pip3 install -r requirements.txt  
python3 scripta.py  
```