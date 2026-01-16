FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY nfo_editor/ ./nfo_editor/
COPY web/ ./web/

# Expose port
EXPOSE 8111

# Run
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8111"]
