FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY requirements.txt /srv/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /srv

# Flask looks for templates/ by default in CWD (/srv)

EXPOSE 8001
CMD ["gunicorn","-w","2","-b","0.0.0.0:8001","app:app"]
