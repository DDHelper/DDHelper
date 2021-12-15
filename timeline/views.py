import json
import datetime
from timeline.models import TimelineEntry
from subscribe.models import MemberGroup
from account.decorators import login_required
from django.http.response import JsonResponse


# Create your views here.
@login_required
def show_timeline(request):
    # 以post方式输入需要时效性的日期范围time_region，为两个元素的列表(必须返回)，
    # 每个元素有year,month,day,hour,minute,second6个属性
    # 还可以输入需要筛选的标签类型dynamic_type(含有'ST','RE','LO'三个元素中任意几个的列表)
    # 必须返回，不筛选则需要返回空列表
    # 还可以输入需要筛选的分组标签member_group(gid列表)
    # 必须返回，不筛选则需要返回空列表
    # 返回json，包含了搜索范围内的所有时效性动态对象及这些对象的全部信息
    time_region_list = request.POST.getlist('time_region')
    start_time = datetime.time(
        year=time_region_list[0].year,
        month=time_region_list[0].month,
        day=time_region_list[0].day,
        hour=time_region_list[0].hour,
        minute=time_region_list[0].minute,
        second=time_region_list[0].second
    )
    end_time = datetime.time(
        year=time_region_list[1].year,
        month=time_region_list[1].month,
        day=time_region_list[1].day,
        hour=time_region_list[1].hour,
        minute=time_region_list[1].minute,
        second=time_region_list[1].second
    )
    result_dynamic = TimelineEntry.objects.\
        filter(event_time__range=(start_time, end_time))
    dynamic_type = request.POST.getlist('dynamic_type')
    if dynamic_type != []:
        result_dynamic = result_dynamic.\
            filter(type__in=dynamic_type)
    selected_group = request.POST.getlist('member_group')
    if selected_group != []:
        selected_member = MemberGroup.objects.\
            filter(gid__in=selected_group).order_by('members').values_list(
                'members').distinct()
        result_dynamic = result_dynamic.\
            filter(dynamic__member__in=selected_member)
    dynamic_data = []
    for dynamic in result_dynamic:
        each_dynamic_data = {
            'event_time': dynamic.event_time.strftime("%Y-%m-%d %H:%M:%S"),
            'text': json.dumps(dynamic.text),
            'type': dynamic.type,
            'member': {
                'mid': dynamic.dynamic.member.mid,
                'name': dynamic.dynamic.member.name,
                'face': dynamic.dynamic.member.face
            }}
        dynamic_data.append(each_dynamic_data)
    return JsonResponse(dynamic_data)
