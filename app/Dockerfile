# syntax=docker/dockerfile:1

FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create folders (in case not present)
RUN mkdir -p /app/input /app/output

# Run the extractor
CMD ["python", "main.py"]
