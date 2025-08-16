FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Download NLTK resource needed by g2p
RUN python3 -m nltk.downloader averaged_perceptron_tagger_eng

# Copy the rest of the application
COPY . .

EXPOSE 8000

# Start FastAPI
CMD ["python3", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
