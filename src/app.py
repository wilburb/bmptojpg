from flask import Flask, request, send_file
from PIL import Image
import os
import io

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and file.filename.endswith('.bmp'):
        img = Image.open(file.stream)
        img = img.convert('RGB')
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='converted_image.jpg')
    return 'Invalid file format', 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)