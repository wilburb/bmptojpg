FROM python:3.12-slim

COPY . .

# Set the working directory in the container
WORKDIR /src

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]