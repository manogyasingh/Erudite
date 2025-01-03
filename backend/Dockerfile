# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with uv
RUN uv pip install --system -r requirements.txt

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p data/graphs data/vector_store

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
