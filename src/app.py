from flask import Flask, request, send_file
from PIL import Image, UnidentifiedImageError
import io
import logging
import os

app = Flask(__name__)

# Configure logging
debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
logging.basicConfig(level=logging.DEBUG if debug_mode else logging.INFO)

@app.route('/upload', methods=['POST'])
def upload_file():
    app.logger.debug('Received request to /upload endpoint')
    
    if 'file' not in request.files:
        app.logger.error('No file part in the request')
        return 'No file part', 400
    
    file = request.files['file']
    app.logger.debug(f'File part found in the request: {file.filename}')
    
    if file.filename == '':
        app.logger.error('No selected file')
        return 'No selected file', 400
    
    if file and file.filename.endswith('.bmp'):
        try:
            app.logger.debug('Attempting to open the BMP file')
            img = Image.open(file.stream)
            app.logger.debug('BMP file opened successfully')
            
            img = img.convert('RGB')
            app.logger.debug('Image converted to RGB')
            
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG')
            img_io.seek(0)
            app.logger.debug('Image saved as JPEG')
            
            return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='converted_image.jpg')
        except UnidentifiedImageError:
            app.logger.error('Cannot identify image file')
            return 'Cannot identify image file', 400
    
    app.logger.error('Invalid file format')
    return 'Invalid file format', 400

if __name__ == '__main__':
    app.logger.debug('Starting the Flask application')
    app.run(host='0.0.0.0', port=5001)