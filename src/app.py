from flask import Flask, request, send_file, abort, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import logging
import os
import requests
import numpy as np
from matplotlib import colormaps
import matplotlib.colors as mcolors

app = Flask(__name__)

# Configure logging
debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
logging.basicConfig(level=logging.DEBUG if debug_mode else logging.INFO)

# Directory to save converted images
SAVE_DIR = "./converted_images"
os.makedirs(SAVE_DIR, exist_ok=True)  # Ensure the directory exists

def add_rgb_key(image, min_temp, max_temp, width=640, height=480, key_height=40, padding=10):
    """
    Add a color gradient key at the bottom of an RGB image.

    Parameters:
        image (PIL.Image.Image): The original RGB image.
        min_temp (float): The minimum temperature in the data.
        max_temp (float): The maximum temperature in the data.
        width (int): The width of the image.
        height (int): The height of the image.
        key_height (int): The height of the color key.
        padding (int): Padding around the labels.

    Returns:
        PIL.Image.Image: The image with the color key at the bottom.
    """
    # Create a blank image for the key
    key_image = Image.new('RGB', (width, key_height), (255, 255, 255))  # White background

    # Create the gradient
    colormap = colormaps['jet']  # Same colormap used for thermal mapping
    gradient = np.linspace(0, 1, width, endpoint=True)  # Gradient from 0 to 1
    colors = (colormap(gradient)[:, :3] * 255).astype(np.uint8)  # Convert to RGB
    gradient_image = Image.fromarray(colors[np.newaxis, :, :], mode='RGB')
    gradient_image = gradient_image.resize((width, key_height))

    # Draw the gradient on the key image
    key_image.paste(gradient_image, (0, 0))

    # Add temperature labels
    draw = ImageDraw.Draw(key_image)
    try:
        # Attempt to load a TTF font
        font = ImageFont.truetype("Arial Black.ttf", 24)
    except IOError:
        # Fallback to default font (not resizable)
        app.logger.info("TTF font not found. Using default font.")
        font = ImageFont.load_default()

    # Define positions for min, mid, and max labels
    positions = [padding, width // 2, width - padding]
    labels = [
        f"{min_temp:.1f}°C",  # Min temperature
        f"{(min_temp + max_temp) / 2:.1f}°C",  # Mid temperature
        f"{max_temp:.1f}°C",  # Max temperature
    ]

    for x, label in zip(positions, labels):
        # Get the dimensions of the label
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Ensure the label is centered vertically and horizontally at the position
        label_x = max(0, min(width - text_width, x - text_width // 2))  # Prevent out-of-bounds
        label_y = (key_height - text_height) // 2
        draw.text(
            (label_x, label_y),
            label,
            fill="black",
            font=font,
        )

    # Combine the original image and the key
    combined_image = Image.new('RGB', (width, height + key_height))
    combined_image.paste(image, (0, 0))
    combined_image.paste(key_image, (0, height))

    return combined_image

def map_thermal_to_rgb(thermal_data):
    """
    Convert raw thermal data to RGB values using a colormap.
    """
    width, height = 32, 24  # Dimensions of the thermal data
    rgb_data = bytearray(width * height * 3)

    # Validate input size
    if len(thermal_data) != width * height:
        raise ValueError(f"thermal_data must have {width * height} values")

    # Normalize thermal data to range [0, 255]
    min_temp = min(thermal_data)
    max_temp = max(thermal_data)
    range_temp = max_temp - min_temp

    if range_temp == 0:
        range_temp = 1  # Prevent division by zero

    # Use a colormap for RGB mapping
    colormap = colormaps['jet'] 
    norm = mcolors.Normalize(vmin=min_temp, vmax=max_temp)

    for i in range(width * height):
        normalized_temp = norm(thermal_data[i])  # Normalize to [0, 1]
        color = colormap(normalized_temp)  # Get (R, G, B, A)

        rgb_data[i * 3] = int(color[0] * 255)  # R
        rgb_data[i * 3 + 1] = int(color[1] * 255)  # G
        rgb_data[i * 3 + 2] = int(color[2] * 255)  # B

    return bytes(rgb_data)

@app.route('/upload-raw-thermal', methods=['POST'])
def upload_raw_thermal():
    app.logger.debug('Received request to /upload-raw-thermal endpoint')
    
    if not request.is_json:
        app.logger.error('Request does not contain JSON')
        return 'Request does not contain JSON', 400
    
    data = request.get_json()
    app.logger.debug(f'Received JSON data: {data}')
    
    # Assuming the JSON data is a list of thermal values
    if not isinstance(data, list):
        app.logger.error('Invalid data format, expected a list')
        return 'Invalid data format, expected a list', 400
    
    thermal_data = data
    if not thermal_data:
        app.logger.error('No thermal data found in the request')
        return 'No thermal data found', 400
    
    try:
        # Convert thermal data to RGB
        rgb_data = map_thermal_to_rgb(thermal_data)
        app.logger.debug('Thermal data converted to RGB successfully')

        # Convert RGB data to an image and save it
        width, height = 32, 24  # Example dimensions, adjust as needed
        img = Image.frombytes('RGB', (width, height), rgb_data)
        img = img.resize((640, 480), Image.BICUBIC)

        key_img = add_rgb_key(img, min(thermal_data), max(thermal_data))

        img_io = io.BytesIO()
        key_img.save(img_io, 'JPEG')
        img_io.seek(0)
        save_path = os.path.join(SAVE_DIR, 'converted_image.jpg')
        key_img.save(save_path, 'JPEG')
        app.logger.debug(f'Converted JPEG saved to disk at {save_path}')
        upload_image_to_connect(img_io, "thermal-prusa-xl", "gXa9ZsygqrKJRc7IMGjS")

        return jsonify({'message': 'Success'}), 200

    except Exception as e:
        app.logger.error(f'Error processing thermal data: {e}')
        return f'Error processing thermal data: {e}', 400

@app.route('/upload-raw-rgb', methods=['POST'])
def upload_raw_rgb():
    app.logger.debug('Received request to /upload endpoint')
    
    if 'file' not in request.files:
        app.logger.error('No file part in the request')
        return 'No file part', 400
    
    file = request.files['file']
    app.logger.debug(f'File part found in the request: {file.filename}')
    
    if file.filename == '':
        app.logger.error('No selected file')
        return 'No selected file', 400
    
    try:
        # Parse raw RGB data (32x24 dimensions as an example, adjust to your case)
        width, height = 32, 24
        app.logger.debug('Attempting to process raw RGB data')

        # Read raw RGB data from the uploaded file
        raw_data = file.read()
        if len(raw_data) != width * height * 3:
            app.logger.error('Invalid RGB data size')
            return 'Invalid RGB data size', 400

        # Convert raw RGB data into a PIL Image
        img = Image.frombytes('RGB', (width, height), raw_data)
        app.logger.debug('RGB image created successfully')

        # Scale up the image (optional)
        img = img.resize((640, 480), Image.BICUBIC)
        app.logger.debug('Image scaled up successfully')

        # Convert to JPEG and save it to a BytesIO stream
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        app.logger.debug('Image saved as JPEG')

        # Save the JPEG to disk
        save_path = os.path.join(SAVE_DIR, 'converted_image.jpg')
        img.save(save_path, 'JPEG')
        app.logger.debug(f'Converted JPEG saved to disk at {save_path}')

        upload_image_to_connect(img_io, "thermal-prusa-xl", "gXa9ZsygqrKJRc7IMGjS")

        # Return the JPEG as a response
        return jsonify({'message': 'Success'}), 200
        #return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='converted_image.jpg')

    except Exception as e:
        app.logger.error(f'Error processing RGB data: {e}')
        return f'Error processing RGB data: {e}', 400

def upload_image_to_connect(image, fingerprint, token):
    headers = {
                'accept': '*/*',
                'content-type': 'image/jpg',
                'fingerprint': fingerprint,
                'token': token
            }
    response = requests.request('PUT', 'https://webcam.connect.prusa3d.com/c/snapshot', headers=headers, data=image)
    return response

@app.route('/connect-upload-test', methods=['POST'])
def connect_upload_test():
    # Read the image file as binary
    with open("./test.jpg", "rb") as image_file:
        # Prepare the PUT request with the image data
        response = upload_image_to_connect(image_file, "thermal-prusa-xl", "gXa9ZsygqrKJRc7IMGjS")
    return jsonify({'message': 'Success'}), 200

# Endpoint to retrieve the latest saved image (DEBUG only)
if debug_mode:
    @app.route('/getLatestImage', methods=['GET'])
    def get_latest_image():
        app.logger.debug('Received request to /getLatestImage endpoint')
        latest_image_path = os.path.join(SAVE_DIR, 'converted_image.jpg')

        if not os.path.exists(latest_image_path):
            app.logger.error('No latest image available')
            return 'No latest image available', 404

        app.logger.debug(f'Serving latest image from {latest_image_path}')
        return send_file(latest_image_path, mimetype='image/jpeg', as_attachment=True, download_name='converted_image.jpg')

if __name__ == '__main__':
    app.logger.debug('Starting the Flask application')
    app.run(host='0.0.0.0', port=5001)