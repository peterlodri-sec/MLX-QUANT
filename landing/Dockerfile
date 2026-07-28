# Use official Python 3.13 image with JIT and Free-Threaded (nogil) support
FROM python:3.13-slim

WORKDIR /app

# Enable Python 3.13+ JIT Compiler & free-threaded execution flags
ENV PYTHONUNBUFFERED=1
ENV PYTHON_JIT=1
ENV PYTHON_NOGIL=1

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy quantitative application files
COPY . .

# Expose Cloud Run default port 8080
ENV PORT 8080
EXPOSE 8080

# Execute server with JIT enabled
CMD ["python", "-X", "jit", "api_server.py"]
