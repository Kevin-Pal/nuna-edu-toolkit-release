FROM python:3.11-slim

WORKDIR /service

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ARG PIP_EXTRA_INDEX_URL=

COPY requirements.txt .
RUN pip install -i "${PIP_INDEX_URL}" \
    ${PIP_EXTRA_INDEX_URL:+--extra-index-url "${PIP_EXTRA_INDEX_URL}"} \
    -r requirements.txt

COPY . .

EXPOSE 8100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
