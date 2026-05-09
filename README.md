
# IMAGE STEGANOGRAPHY + AES Encryption

A Streamlit web application that hides encrypted messages inside images
using **LSB steganography** and **AES-GCM encryption**.

## Features

-   Hide secret messages inside PNG images
-   AES-GCM encryption with PBKDF2 key derivation
-   Password strength checking
-   Face detection (rejects images with faces)
-   Image quality analysis (sharpness, brightness, resolution)
-   Extract & decrypt hidden messages
-   Modern UI with custom CSS

## Installation

### 1. Install required packages:

```
pip install streamlit pillow pycryptodome opencv-python numpy
```

If OpenCV fails:

```
pip install opencv-python-headless
```

### 2. Run the app:

> **Important:** your file name contains a space. Use quotes around the filename when running Streamlit.

```
streamlit run "FC313 Code.py"
```

## How It Works

### Encryption

-   User enters a secret key
-   Key derived using PBKDF2 (200,000 iterations)
-   AES-GCM encrypts & authenticates message
-   Output encoded in Base64

### Steganography (Hiding)

-   Convert Base64 text → bits
-   Insert bits into image pixel LSB
-   Rejects images with faces
-   Performs image quality checks

### Extraction (Unhiding)

-   Reads LSB bits
-   Decodes Base64
-   AES-GCM decrypts back to message

## Restrictions

The app rejects:
- Images containing faces
- Low‑quality images (too small, blurry, dark, overexposed)
- Weak passwords
- Messages too large for the image

## Technologies Used

-   Python
-   Streamlit
-   OpenCV
-   Pillow
-   NumPy
-   PyCryptodome

## Notes

- If you prefer, rename the file to **FC313_Code.py** (without spaces) and then run:
```
streamlit run FC313_Code.py
```
- On macOS, you can open Terminal in the folder containing the file and run the command above.
- If you get errors related to OpenCV on servers or CI, try `opencv-python-headless`.
