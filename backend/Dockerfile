# syntax=docker/dockerfile:1.6

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    KICAD9_3DMODEL_DIR=/usr/share/kicad/3dmodels

# Base system packages + Python runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        gnupg \
        software-properties-common \
        python3 \
        python3-venv \
        python3-pip \
        python3-dev \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# KiCad CLI tools (via official PPA for KiCad 9) + official 3D model libraries
RUN add-apt-repository -y ppa:kicad/kicad-9.0-releases && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        kicad \
        kicad-packages3d && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

# Install backend dependencies first for better layer caching
COPY pyproject.toml uv.lock /app/
COPY app /app/app
RUN pip install --no-cache-dir .

# Copy application code
COPY . /app

# Storage directory for generated previews
RUN mkdir -p /app/var/storage

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
