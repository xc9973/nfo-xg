FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY nfo_editor/ ./nfo_editor/
COPY tmdb_search/ ./tmdb_search/
COPY web/ ./web/

# Create session directory
RUN mkdir -p /tmp/flask_session

# Expose port
EXPOSE 5000

# Run Flask with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "web.app:app"]
