import sys

from django.core.management.base import BaseCommand, CommandError
from dynamic.models import Dynamic
from DDHelper import settings
from timeline.tasks import process_timeline
from timeline.models import TimelineDynamicProcessInfo


class Command(BaseCommand):
    help = '重新更新timeline'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        all_dynamic = Dynamic.objects\
            .exclude(timelinedynamicprocessinfo__process_version__gte=TimelineDynamicProcessInfo.VERSION)\
            .values_list('dynamic_id', flat=True)
        self.stdout.write(f"共{len(all_dynamic)}条需要更新")
        for i, did in enumerate(all_dynamic):
            process_timeline(did)
            if i % 200 == 0:
                self.stdout.write(f'\r{i}/{len(all_dynamic)}')
                self.stdout.flush()
        self.stdout.write(self.style.SUCCESS("成功调用"))
