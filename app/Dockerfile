FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Use build arguments to switch pip mirror (default is Aliyun)
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
# Optional: if you need extra sources
ARG PIP_EXTRA_INDEX_URL=

COPY requirements.txt .
RUN pip install -i "${PIP_INDEX_URL}" \
    ${PIP_EXTRA_INDEX_URL:+--extra-index-url "${PIP_EXTRA_INDEX_URL}"} \
    -r requirements.txt

# Copy backend code
COPY backend ./backend
# Copy frontend code
COPY frontend ./frontend

# Expose ports
EXPOSE 8000
EXPOSE 9000

# Run uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
