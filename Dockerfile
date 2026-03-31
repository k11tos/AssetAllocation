# Multi-stage build for optimized image size
FROM python:3.12-alpine AS build

# Set working directory
WORKDIR /py_app

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    wget \
    tar \
    make \
    g++

# Build and install TA-Lib from source
RUN wget --timeout=30 --tries=3 https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz/download -O ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr --build="$(uname -m)-unknown-linux-gnu" && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy project files and install Python dependencies
COPY pyproject.toml uv.lock README.md ./
COPY strategies ./strategies/
COPY services ./services/
COPY utils ./utils/
COPY *.py ./
RUN pip install --no-cache-dir -e .

# Runtime stage
FROM python:3.12-alpine

# Set working directory
WORKDIR /py_app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies only
RUN apk add --no-cache \
    libffi \
    openssl \
    && adduser -D -s /bin/sh app

# Copy Python packages from build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy TA-Lib shared library from build stage
COPY --from=build /usr/lib/libta_lib.so* /usr/lib/

# Copy project files
COPY . .

# Change ownership to non-root user
RUN chown -R app:app /py_app
USER app

# Entry point and command
ENTRYPOINT ["python"]
CMD ["main.py"]
