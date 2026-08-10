# Use the official Python image
FROM python:3.12

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies: PostgreSQL client, Tesseract OCR for image text extraction
RUN apt-get update && apt-get install -y \
    postgresql-client \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


# Copy the application code
COPY . /app/

# Normalize Windows line endings and grant execution permissions
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Run the entrypoint script by default
ENTRYPOINT ["/app/entrypoint.sh"]

# Run Django on 0.0.0.0:8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
