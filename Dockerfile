# Base image
FROM python:3.11-slim

# Env vars
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Workdir
WORKDIR /app

# Install system dependencies & uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libssl-dev \
    && pip install --no-cache-dir uv==0.4.22 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install project dependencies
RUN uv pip install --system .

# Copy app source
COPY src/ ./src
COPY scripts/ ./scripts
COPY .streamlit/ ./.streamlit

# Expose Streamlit port
EXPOSE 8501

# Optional: security – run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Run the app
CMD ["streamlit", "run", "src/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
