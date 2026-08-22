FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Render sets $PORT at runtime; uvicorn reads it in app.py's __main__,
# but we call uvicorn directly here for the container CMD instead.
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}