from flask import Flask, request, send_file
from PIL import Image, UnidentifiedImageError
import io
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set maximum allowed payload to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/upload', methods=['POST'])
def upload_file():
    if not request.data:
        app.logger.error('No data in the request')
        return 'No data in the request', 400
    try:
        img = Image.open(io.BytesIO(request.data))
        img = img.convert('RGB')
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='converted_image.jpg')
    except UnidentifiedImageError:
        app.logger.error('Cannot identify image file')
        return 'Cannot identify image file', 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)