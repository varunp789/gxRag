FROM python:3.12-slim
WORKDIR /workspace
COPY apps/api /workspace/apps/api
RUN pip install --no-cache-dir /workspace/apps/api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
