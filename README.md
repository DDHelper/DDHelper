# DDHelper

[![Django CI](https://github.com/DDHelper/DDHelper/actions/workflows/django.yml/badge.svg)](https://github.com/DDHelper/DDHelper/actions/workflows/django.yml)  [![Docker Image CI](https://github.com/DDHelper/DDHelper/actions/workflows/docker-image.yml/badge.svg)](https://github.com/DDHelper/DDHelper/actions/workflows/docker-image.yml)

这是DDHelper的后端仓库

[前端代码仓库](https://github.com/DDHelper/ddhelper-frontend)

## 部署

### 配置管理

在运行此项目前，你需要按照[DDHelper/settings.py]()配置好数据库、CeleryBroker、
邮箱服务器账号密码、代理池服务。

所有的配置都可以通过环境变量进行配置，如果使用docker镜像的话可以通过 --env-file 来进行配置

### 部署各个服务
可以选择使用docker compose一键部署或者手动部署各个服务
#### 1. Docker compose
在Deploy文件夹中有docker-compose.yml配置文件，

在您的工作目录里通过envfile.txt配置好环境变量后，使用一些指令即可在本机上开启所有需要的服务

envfile.txt的示例：
```txt
CELERY_BROKER_URL=amqp://user:pwd@ip:port/vhost
MYSQL_NAME=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_HOST=
MYSQL_PORT=
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_SSL=True
PIN_EMAIL=

```

#### 2. 手动部署
本项目使用Celery来实现分布式任务执行。

##### Django服务器
主要业务逻辑
```shell
python manage.py runserver 0.0.0.0:8000
```

##### Celery Worker
执行外站api调用、动态同步等工作。worker可以横向扩展
```shell
# 处理动态同步相关任务
celery -A DDHelper worker -Q dynamic -l info -E -n dynamic_w1@%h
# 处理timeline相关任务
celery -A DDHelper worker -Q timeline -l info -E -n dynamic_w1@%h
# 处理外站api调用
celery -A DDHelper worker -Q biliapi -l info -E -n biliapi_w1@%h
```


