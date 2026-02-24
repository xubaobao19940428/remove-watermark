# Use official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies (especially ffmpeg for yt-dlp)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy project files
COPY . .

# Create downloads directory and set permissions
RUN mkdir -p downloads && chmod 777 downloads

# Expose port
EXPOSE 7860

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
