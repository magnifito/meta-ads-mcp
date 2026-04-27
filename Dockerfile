FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_HTTP_PATH=/meta

WORKDIR /app

# Pillow runtime deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY meta_ads_mcp ./meta_ads_mcp

RUN pip install --upgrade pip \
    && pip install .

# Drop privileges
RUN useradd --system --uid 1001 --home /home/mcp mcp \
    && mkdir -p /home/mcp/.config/meta-ads-mcp \
    && chown -R mcp:mcp /home/mcp /app
USER mcp

EXPOSE 8080

# Streamable HTTP, mount path set via MCP_HTTP_PATH (default /meta).
# Override write mode etc. via env at runtime.
CMD ["python", "-m", "meta_ads_mcp", \
     "--transport", "streamable-http", \
     "--host", "0.0.0.0", \
     "--port", "8080"]
