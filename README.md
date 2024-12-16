# Python API Converter

This project is a simple Flask web application that allows users to upload BMP image files, which are then converted to JPEG format and returned to the user.

## Project Structure

```
python-api-converter
├── src
│   ├── app.py           # Main application file
│   ├── requirements.txt # Dependencies for the project
├── Dockerfile           # Dockerfile to build the Docker image
├── .dockerignore        # Files to ignore when building the Docker image
└── README.md            # Project documentation
```

## Requirements

- Python 3.x
- Docker

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd python-api-converter
   ```

2. Navigate to the `src` directory:
   ```
   cd src
   ```

3. Build the Docker image:
   ```
   docker build -t python-api-converter .
   ```

## Running the Application

To run the application, use the following command:
```
docker run -p 5001:5001 python-api-converter
```

The application will be accessible at `http://localhost:5001`.

## API Usage

### Upload BMP File

- **Endpoint:** `/upload`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`

#### Request

- Form-data key: `file`
- Value: BMP file to upload

#### Response

- Content-Type: `image/jpeg`
- Returns the converted JPEG image.

## License

This project is licensed under the MIT License.