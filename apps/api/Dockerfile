FROM python:3.12-slim
WORKDIR /workspace
COPY apps/api /workspace/apps/api
RUN pip install --no-cache-dir /workspace/apps/api \
    && useradd --system --uid 10001 gxrag && mkdir -p /var/lib/gxrag && chown gxrag /var/lib/gxrag
ENV GXRAG_ARTIFACT_ROOT=/var/lib/gxrag/artifacts
USER gxrag
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/v1/health').status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
