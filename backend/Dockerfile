# syntax=docker/dockerfile:1.6

FROM ubuntu:24.04

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv

ENV DEBIAN_FRONTEND=noninteractive \
    # Python/uv settings
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    # App settings
    KICAD9_3DMODEL_DIR=/usr/share/kicad/3dmodels \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        software-properties-common \
        gpg-agent && \
    add-apt-repository -y ppa:kicad/kicad-9.0-releases && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        kicad \
        kicad-packages3d \
        gosu && \
    # Remove KiCad GUI binaries (keep kicad-cli)
    rm -f /usr/bin/kicad \
          /usr/bin/pcbnew \
          /usr/bin/eeschema \
          /usr/bin/gerbview \
          /usr/bin/pl_editor \
          /usr/bin/bitmap2component \
          /usr/bin/pcb_calculator && \
    # Remove heavy data: demos, templates, docs, man pages
    rm -rf /usr/share/kicad/demos \
           /usr/share/kicad/template \
           /usr/share/doc \
           /usr/share/man \
           /usr/share/icons && \
    # Cleanup build deps
    apt-get remove -y \
        software-properties-common \
        gpg-agent && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --create-home app

WORKDIR /app

# Install dependencies
# Copy only lock files first for caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev && \
    uv cache clean

# Copy application code
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Install the project itself
RUN uv sync --frozen --no-dev && \
    uv cache clean

# Storage directory for generated previews
RUN mkdir -p /app/var/storage && chown -R app:app /app/var/storage

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
