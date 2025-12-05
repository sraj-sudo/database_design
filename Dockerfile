# Use official slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install system deps for SQLite and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask and Streamlit ports
EXPOSE 5000 8501

# Start both Flask and Streamlit (Flask in background)
CMD bash -lc "python /app/app.py & streamlit run /app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"
