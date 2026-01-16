FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir lxml fastapi uvicorn jinja2

# Copy application
COPY nfo_editor/ ./nfo_editor/
COPY web/ ./web/

# Expose port
EXPOSE 8000

# Run
CMD ["python", "web/app.py"]
