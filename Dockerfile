FROM python:3.7-alpine
WORKDIR /app
COPY . .
RUN apk add --no-cache libxml2-dev libxslt-dev gcc musl-dev build-base mariadb-connector-c-dev && \
pip install --no-cache-dir -r requirements.txt && \
apk del gcc musl-dev libxml2-dev build-base
VOLUME ["/app/ddhelper/private"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]