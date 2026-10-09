FROM python:3.14-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app

RUN useradd --system --uid 10001 guideforge && mkdir /data && chown guideforge /data
USER guideforge
ENV DATA_DIR=/data PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

# One worker on purpose: the scheduler, the sync lock and the rebuild debounce live in this process.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
