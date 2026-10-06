# Use an official lightweight Python base image
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to benefit from layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code into the container
COPY assistant_cli.py /app/
COPY app/ /app/app/

# Run as an unprivileged user
RUN useradd --create-home --uid 1000 lumina
USER 1000

EXPOSE 8000

# Serve the FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
