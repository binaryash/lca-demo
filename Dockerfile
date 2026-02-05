# Use Python 3.10
FROM python:3.10-slim

# 1. Install System Deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install uv (The magic tool)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 3. Install Dependencies
# Copy configuration first
COPY pyproject.toml .

# Create a virtual environment (.venv) and install dependencies
# We use 'uv pip install' here to ensure it works without a lockfile if needed,
# but 'uv sync' is preferred if you have a uv.lock.
RUN uv venv && uv pip install .

# 4. BAKE THE DATABASE
# Copy the build script
COPY build_db.py .
# Define where the baked DB lives
ENV BRIGHTWAY2_DIR=/app/bw_data
# CRITICAL: Use 'uv run' so it uses the installed libraries in .venv
RUN uv run python build_db.py

# 5. Copy Application Code
COPY main.py .

# 6. Run
EXPOSE 8501
# Use 'uv run' to launch Streamlit within the environment
CMD ["uv", "run", "streamlit", "run", "main.py", "--server.address=0.0.0.0"]
