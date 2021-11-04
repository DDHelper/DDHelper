from celery import shared_task
from django.utils import timezone
from django.db import transaction, DatabaseError
from . import dsync
from . import models


@shared_task(ignore_result=True)
def call_full_sync(chunk_size):
    """
    请求一次全动态同步，实际上是发出一个链式请求，包含所有需要更新的成员
    :return:
    """


@shared_task(ignore_result=True)
def add_member(mid: int, initial_sync=True):
    """
    添加一个需要同步的成员
    :param mid: 成员的id
    :param initial_sync: 是否自动创建初始化同步任务
    :return:
    """
    member = dsync.get_member(mid)
    if member is None:
        member = models.Member(mid=mid)
        msg = dsync.update_member_profile(member)
        if msg:
            # 更新信息失败
            return
        member.save()

        if initial_sync:
            sync_member.delay(mid)


@shared_task(ignore_result=True)
def sync_member(mid: int, min_interval=30):
    """
    同步某个成员最近的动态
    :param mid: 成员
    :param min_interval: 最小更新间隔，如果离上次更新小于这个间隔会直接跳过这次更新
    :return:
    """
    member = dsync.get_member(mid)
    if member is not None:
        if member.last_dynamic_update is not None and \
                (timezone.now() - member.last_profile_update).seconds <= min_interval:
            # 如果离上次更新小于这个间隔会直接跳过这次更新
            return

        latest_dynamic = dsync.get_saved_latest_dynamic(mid)
        did = latest_dynamic.dynamic_id if latest_dynamic is not None else 0
        dynamics, msg = dsync.get_all_dynamic_since(member, did)
        if dynamics is None:  # 拉取动态失败了
            return  # TODO: 添加retry机制

        member.last_dynamic_update = timezone.now()
        if len(dynamics) != 0:
            dynamics.sort(key=lambda d: d.dynamic_id)  # 强制从小到大的顺序进行提交

        try:
            with transaction.atomic():
                for dy in dynamics:
                    dy.save()
                member.save()
        except DatabaseError:
            # 更新失败
            return  # TODO: 添加retry机制

