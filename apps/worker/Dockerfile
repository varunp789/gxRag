FROM python:3.12-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr ffmpeg && rm -rf /var/lib/apt/lists/*
COPY apps/api /workspace/apps/api
COPY apps/worker /workspace/apps/worker
RUN pip install --no-cache-dir /workspace/apps/api /workspace/apps/worker \
    && useradd --system --uid 10001 gxrag && mkdir -p /var/lib/gxrag && chown gxrag /var/lib/gxrag
ENV GXRAG_ARTIFACT_ROOT=/var/lib/gxrag/artifacts
USER gxrag
CMD ["python", "-m", "worker.main"]
