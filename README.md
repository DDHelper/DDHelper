# DDHelper

[![Django CI](https://github.com/DDHelper/DDHelper/actions/workflows/django.yml/badge.svg)](https://github.com/DDHelper/DDHelper/actions/workflows/django.yml)

这是DDHelper的后端仓库

[前端代码仓库](https://github.com/DDHelper/DDHelper-frontend)

## 部署

### 配置管理

在运行此项目前，你需要按照[DDHelper/settings.py]()配置好数据库、CeleryBroker、
邮箱服务器账号密码、代理池服务。

所有的配置都可以通过环境变量进行配置，如果使用docker镜像的话可以通过 --env-file 来进行配置

### 运行部署
本项目使用Celery来实现分布式任务执行。

#### Django服务器
主要业务逻辑
```shell
python manage.py runserver 0.0.0.0:8000
```

#### Celery Worker
执行外站api调用、动态同步等工作。worker可以横向扩展
```shell
# 处理动态同步相关任务
celery -A DDHelper worker -Q dynamic -l info -P solo -E -n dynamic_w1@%h
# 处理外站api调用
celery -A DDHelper worker -Q biliapi -l info -E -n biliapi_w1@%h
```


