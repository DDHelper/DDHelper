from celery import shared_task, chord
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import transaction, DatabaseError
import logging
from . import dsync
from . import models

logger: logging.Logger = get_task_logger(__name__)


@shared_task
def call_full_sync(chunk_size=5):
    """
    请求一次全动态同步。
    同步耗时可以估计为：
    成员数*每个成员预计时间（0.5s） / 有效worker数量
    :param chunk_size: 每一块请求的成员数量
    :return:
    """
    # TODO: 加锁，防止重复发送
    all_mid = list(models.Member.objects.values_list("mid", flat=True))
    chunked = sync_member.chunks(zip(all_mid), chunk_size).group()
    chunked.apply_async()
    logger.info(f"执行全动态同步，发出{len(chunked)}个任务")


@shared_task
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
            logger.warning(f"更新信息失败: mid={mid} msg={msg}")
            raise Exception(f"更新信息失败: mid={mid} msg={msg}")
        member.save()
        logger.info(f"添加新成员: mid={mid}")

        if initial_sync:
            sync_member.delay(mid)


@shared_task
def sync_member(mid: int, min_interval=600):
    """
    同步某个成员最近的动态
    :param mid: 成员
    :param min_interval: 最小更新间隔，如果离上次更新小于这个间隔会直接跳过这次更新
    :return:
    """
    logger.info(f"开始执行成员{mid}的动态同步")
    member = dsync.get_member(mid)
    if member is None:
        logger.warning(f"成员{mid}不存在")
        raise Exception()

    if member.last_dynamic_update is not None and \
            (timezone.now() - member.last_profile_update).seconds <= min_interval:
        # 如果离上次更新小于这个间隔会直接跳过这次更新
        logger.info(f"成员{mid}在{min_interval}s内进行过同步，跳过此任务")
        return

    latest_dynamic = dsync.get_saved_latest_dynamic(mid)
    did = latest_dynamic.dynamic_id if latest_dynamic is not None else 0
    dynamics, msg = dsync.get_all_dynamic_since(member, did)
    if dynamics is None:  # 拉取动态失败了
        logger.warning(f"拉取动态失败: mid={mid} msg={msg}")
        raise Exception(f"拉取动态失败: mid={mid} msg={msg}")  # TODO: 添加retry机制

    member.last_dynamic_update = timezone.now()
    if len(dynamics) != 0:
        dynamics.sort(key=lambda d: d.dynamic_id)  # 强制从小到大的顺序进行提交

    try:
        with transaction.atomic():
            logger.info(f"成员{mid}的{len(dynamics)}条动态正在写入")
            for dy in dynamics:
                dy.save()
            member.save()
            logger.info(f"成员{mid}动态同步完成")
    except DatabaseError as e:
        # 更新失败
        logger.warning(f"更新数据库失败: mid={mid} msg={str(e)}")
        raise e  # TODO: 添加retry机制

