# Use and official lightweight Python base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies if required 
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

    # Install required Python packages
    RUN pip install --no-cache-dir psutil requests

# Copy project code into the container
COPY assistant_cli.py /app/

# Set the default command to execute the Python script
CMD ["python", "assistant_cli.py"]