# Use Python 3.10
FROM python:3.10-slim

# 1. Install System Deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 3. Install Dependencies
# Copy both config files first
COPY pyproject.toml .
COPY README.md .

# Create venv and install
RUN uv venv && uv pip install .

# 4. BAKE THE DATABASE
COPY build_db.py .
ENV BRIGHTWAY2_DIR=/app/bw_data
RUN uv run python build_db.py

# 5. Copy Application Code
COPY main.py .

# 6. Run
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "main.py", "--server.address=0.0.0.0"]
