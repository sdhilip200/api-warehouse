FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Secrets are provided at runtime via environment variables — never baked into the image.
CMD ["python", "pipeline.py"]
