FROM python:3.7-alpine
WORKDIR /app
COPY . .
RUN sed -i '2c\https://mirror.tuna.tsinghua.edu.cn/alpine/latest-stable/community/' /etc/apk/repositories && \
sed -i '1c\https://mirror.tuna.tsinghua.edu.cn/alpine/latest-stable/main/' /etc/apk/repositories && \
apk add --no-cache libxml2-dev libxslt-dev gcc musl-dev mariadb-connector-c-dev && \
pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
apk del gcc musl-dev libxml2-dev
VOLUME ["/app/ddhelper/private"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8008"]