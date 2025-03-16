FROM gdssingapore/airbase:python-3.13

# Ensure Python does not buffer output
ENV PYTHONUNBUFFERED=TRUE

# Install system dependencies required for building Python packages
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    g++ \
    clang \
    make \
    libffi-dev \
    libssl-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*  # Clean up package lists

# Upgrade pip, setuptools, and wheel
RUN python3 -m pip install --upgrade pip setuptools wheel

# Copy and install Python dependencies
COPY --chown=app:app requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=app:app . ./

# Switch back to app user (required for Airbase)
USER app

# Command to run the application
CMD ["python3", "app.py"]
