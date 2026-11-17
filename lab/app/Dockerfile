# One image for both labs. No OpenTelemetry in here: in the enriched lab the injector
# (LD_PRELOAD) brings the Python agent in from outside the image.
FROM python:3.11.18-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./
ARG APP_NAME=transit
ARG APP_VERSION=0.0.0
ENV APP_NAME=$APP_NAME APP_VERSION=$APP_VERSION PYTHONUNBUFFERED=1
