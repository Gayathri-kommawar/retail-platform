FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN useradd --create-home appuser
USER appuser

EXPOSE 8081

CMD ["python", "app.py"]

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/health')"