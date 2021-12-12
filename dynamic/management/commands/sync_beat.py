from django.core.management.base import BaseCommand, CommandError
from dynamic.models import DynamicSyncInfo
from DDHelper import settings
from dynamic.tasks import call_full_sync


class Command(BaseCommand):
    help = '请求一次动态同步'

    def add_arguments(self, parser):
        parser.add_argument('--min_interval', type=int, default=settings.DYNAMIC_SYNC_MEMBER_MIN_INTERVAL)
        parser.add_argument('--chunk_size', type=int, default=5)

    def handle(self, *args, **options):
        call_full_sync(chunk_size=options['chunk_size'], min_interval=options['min_interval'])
        self.stdout.write(self.style.SUCCESS("成功调用"))
