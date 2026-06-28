FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# IMPORTANT: A .dockerignore file MUST be present in the build context alongside this Dockerfile.
# Without it, `COPY . .` would bake local secrets (.dlt/secrets.toml, .env, *.duckdb, etc.)
# into the image layers, where they are inspectable. See templates/.dockerignore.
# Secrets are provided at runtime via environment variables — never baked into the image.
CMD ["python", "pipeline.py"]
