from DDHelper.util import load_params
from account.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, BadRequest
from django.db.models import Count
from django.http import QueryDict
from django.http.response import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET

from subscribe import models
from subscribe.models import MemberGroup, SubscribeMember
from dynamic import tasks as dynamic_task
from biliapi.tasks import search_user_name, user_profile, user_stat, get_data_if_valid


@require_GET
@login_required
def search(request):
    """
    根据搜索关键字查找b站up主
    :param request: GET型request
    请求参数
        search_name	string 必要 搜索关键字
    :return: Response
    返回数据
        data object_array 查询到的信息
        - mid num up主B站uid
        - name string up主姓名
        - fans num up主粉丝数
        - usign string up主签名
        - upic string up主头像地址
        - raw object 原始查询结果
        code integer 状态码
    """
    with load_params():
        name = request.GET['search_name']

    if len(name) == 0:
        return JsonResponse({
            'code': 200,
            'data': []
        })

    search_result = []
    data, msg, = get_data_if_valid(search_user_name.delay(name).get())
    if data is None:
        raise BadRequest(msg)

    aid = request.user.uid
    for result in data.get("result", []):
        search_result.append({
            "mid": result["mid"],
            "uname": result["uname"],
            "fans": result["fans"],
            "usign": result["usign"],
            "upic": result["upic"],
            "subscribed": MemberGroup.is_subscribed(aid, result["mid"]),
            "raw": result
        })
    return JsonResponse({
        'code': 200,
        'data': search_result
    })


@require_GET
@login_required
def group_list(request):
    """
    查找用户的全部分组的信息以及某个up主是否在某个分组中(可选)
    :param request: GET型request
    请求参数
        mid	num 非必要 待查询的up主id
    :return: Response
    返回数据
        data object_array 查到分组的详细信息
        - gid num 分组id
        - group_name string 分组名称
        - count num 某分组成员数
        - in_this_group string 查找的up主是否在此分组
        code integer 状态码
    """
    with load_params():
        mid = int(request.GET.get("mid", 0))

    groups = MemberGroup.select_groups_by_account(request.user.uid).annotate(Count("members"))
    mid_groups = {}
    if mid != 0 and MemberGroup.is_subscribed(request.user.uid, mid):
        mid_groups = set(MemberGroup.select_groups_by_account_and_member(request.user.uid, mid).values_list('gid', flat=True))

    data = []
    for group in groups:
        entry = {
            'gid': group.gid,
            'group_name': group.group_name,
            'count': group.members__count
        }
        if mid != 0:
            entry['in_this_group'] = group.gid in mid_groups
        data.append(entry)
    return JsonResponse({
        'code': 200,
        'data': data
    })


@require_GET
@login_required
def group_members(request):
    """
    根据分组id查询分组内的成员
    :param request: GET型request
    请求参数
        gid	num 非必要 需要查询的分组id,不传入时显示当前用户默认分组
        page num 非必要 当前所在页数-1
        size num 非必要 当前页可容纳条目数量，默认为20条每页
    :return: Response
    返回数据
        data object
        - has_more bool 是否还有未加载的成员
        - gid num 分组id
        - group_name 分组名称
        - count num 该分组下成员总数
        - page num 当前所在页数-1
        - pages num 总共页数
        - data object_array 各成员原始查询结果
        code integer 状态码
        msg string 出错信息
    """
    with load_params():
        gid = int(request.GET.get('gid', 0))
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 20))

    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        members = group.members.all()
        members_count = members.count()
        page_start = page * size
        page_end = page_start + size
        paged = members[page_start:page_end]
        return JsonResponse({
            'code': 200,
            'data': {
                'has_more': page_end < members_count,
                'gid': group.gid,
                'group_name': group.group_name,
                'count': members_count,
                'page': page,
                'pages': -(-members_count // size),
                'data': [member.as_dict() for member in paged]
            }
        })
    else:
        return JsonResponse({
            'code': 404,
            'msg': "分组不存在"
        }, status=404)


@require_POST
@login_required
def subscribe(request):
    """
    根据提交的mid和gid来关注某个up主并加入若干个分组
    :param request: POST型request
    请求参数
        mid	num 必要 需要查询的分组id,不传入时显示当前用户默认分组
        gid num_array 必要 需要加入的分组id列表
    :return: Response
    返回数据
        code integer 状态码
        msg string 出错信息
    """
    with load_params():
        mid = int(request.POST['mid'])  # 需要关注的对象，以mid传递
        groups = [int(gid) for gid in request.POST.getlist('gid')]

    if not SubscribeMember.objects.filter(mid=mid).exists():
        if not add_new_member(mid):
            return JsonResponse({
                'code': 404,
                'msg': "添加的up主不存在或不符合要求（至少需要1000粉丝）"
            }, status=404)
    MemberGroup.set_groups_by_account_and_member(aid=request.user.uid, mid=mid, groups=groups)
    return JsonResponse({'code': 200})


@require_POST
@login_required
def add_group(request):
    """
    增加新的分组
    :param request: POST型request
    请求参数
        group_name string 必要 新增分组的名称
    :return: Response
    返回数据
        code integer 状态码
        success bool 是否成功创建(同名会失败)
        data object
        - gid num 创建的分组id(失败时为同名分组id)
        - group_name 分组名称(失败时为同名分组名称)
    """
    # POST提交新增分组的名称group_name
    # 返回是否关注成功的结果result(success/fail)
    with load_params():
        group_name = request.POST['group_name']

    group, create = MemberGroup.objects.get_or_create(user_id=request.user.uid,
                                                      group_name=group_name)
    return JsonResponse({
        'code': 200,
        'success': create,
        'data': {
            'gid': group.gid,
            'group_name': group.group_name
        }
    })


@require_POST
@login_required
def update_group(request):
    """
    修改已有的分组
    :param request: POST型request
    请求参数
        gid	num 必要 需要修改的分组id
        group_name string 必要 修改后新分组的名称
    :return: Response
    返回数据
        data object
        - gid num 修改了的分组id
        - group_name 修改后新分组名称
        code integer 状态码
        msg string 出错信息
    """
    with load_params():
        gid = int(request.POST['gid'])
        group_name = request.POST.get('group_name')

    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        if group_name:
            if group.group_name == models.DEFAULT_GROUP_NAME:
                return JsonResponse({
                    'code': 403,
                    'msg': "默认分组无法改名"
                }, status=403)
            if MemberGroup.objects.filter(user=request.user.uid, group_name=group_name).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': "分组名重复"
                }, status=400)
            group.group_name = group_name
            group.save()
            return JsonResponse({
                'code': 200,
                'data': {
                    'gid': group.gid,
                    'group_name': group.group_name
                }
            })
        else:
                return JsonResponse({
                    'code': 400,
                    'msg': "新分组名为空"
                }, status=400)
    else:
        return JsonResponse({
            'code': 404,
            'msg': "分组不存在"
        }, status=404)


@require_http_methods(['DELETE'])
@login_required
def delete_group(request):
    """
    删除已有的分组
    :param request: DELETE型request
    请求参数
        gid	num 必要 需要删除的分组id
    :return: Response
    返回数据
        code integer 状态码
        msg string 出错信息
    """
    with load_params():
        body = QueryDict(request.body.decode("utf-8"),encoding="utf-8")
        gid = int(body['gid'])

    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        if group.group_name == models.DEFAULT_GROUP_NAME:
            return JsonResponse({
                'code': 403,
                'msg': "默认分组无法被删除"
            }, status=403)
        group.delete()
        return JsonResponse({
            'code': 200
        })
    else:
        return JsonResponse({
            'code': 404,
            'msg': "分组不存在"
        }, status=404)


@require_POST
@login_required
def member_move(request):
    """
    将一个分组内的一批成员移动到另一分组
    :param request: POST型request
    请求参数
        mid	num_array 必要 需要移动的成员的id列表
        old_group num 必要 需要移动的成员所在分组id
        new_group num 必要 成员将要移往的分组id
        remove_old num 非必要 是否要将移动成员从旧分组删除
    :return: Response
    返回数据
        code integer 状态码
        msg string 出错信息
    """
    with load_params():
        mid_list = [int(mid) for mid in request.POST.getlist('mid')]
        old_group = int(request.POST['old_group'])
        new_group = int(request.POST['new_group'])
        remove_old = int(request.POST.get('remove_old', 1))  # 是否从旧分组里删除

    old_group = MemberGroup.get_group(aid=request.user.uid, gid=old_group)
    new_group = MemberGroup.get_group(aid=request.user.uid, gid=new_group)
    if old_group is None or new_group is None:
        return JsonResponse({
            'code': 404,
            'msg': "分组不存在"
        }, status=404)
    if remove_old:
        old_group.members.remove(*mid_list)
    new_group.members.add(*mid_list)
    return JsonResponse({
        'code': 200,
    })


def add_new_member(mid):
    """
    添加新的up主到数据库
    :param mid: 待添加的up主的id
    :return: Bool 成功为True，失败为False
    """
    # 成功添加up主到up主数据库则返回True，否则返回False
    pf_call = user_profile.delay(mid, use_proxy=False)
    stat_call = user_stat.delay(mid, use_proxy=False)
    profile, msg = get_data_if_valid(pf_call.get())
    stat, s_msg = get_data_if_valid(stat_call.get())
    if profile is None or stat is None:
        return False

    # 判断添加的用户是否符合添加条件
    if stat["follower"] > 1000:
        member, create = SubscribeMember.objects.update_or_create(mid=mid, name=profile["name"],
                                                              face=profile["face"])
        if create:
            dynamic_task.add_member.delay(mid)
        return member is not None
    else:
        return False

