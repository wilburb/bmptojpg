from flask import Flask, request, send_file, abort, jsonify
from PIL import Image
import io
import logging
import os
import requests

app = Flask(__name__)

# Configure logging
debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
logging.basicConfig(level=logging.DEBUG if debug_mode else logging.INFO)

# Directory to save converted images
SAVE_DIR = "./converted_images"
os.makedirs(SAVE_DIR, exist_ok=True)  # Ensure the directory exists

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
        app.logger.info(f'Converted JPEG saved to disk at {save_path}')

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

        app.logger.info(f'Serving latest image from {latest_image_path}')
        return send_file(latest_image_path, mimetype='image/jpeg', as_attachment=True, download_name='converted_image.jpg')

if __name__ == '__main__':
    app.logger.debug('Starting the Flask application')
    app.run(host='0.0.0.0', port=5001)