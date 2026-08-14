FROM python:3.12-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr ffmpeg && rm -rf /var/lib/apt/lists/*
COPY apps/api /workspace/apps/api
COPY apps/worker /workspace/apps/worker
RUN pip install --no-cache-dir /workspace/apps/api /workspace/apps/worker
CMD ["python", "-m", "worker.main"]
