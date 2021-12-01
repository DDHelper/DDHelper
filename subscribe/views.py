from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, BadRequest
from django.http.response import JsonResponse
from django.views.decorators.http import require_http_methods

from subscribe import models
from subscribe.models import MemberGroup, SubscribeMember
from biliapi.tasks import search_user_name, user_profile, user_stat, get_data_if_valid


@login_required
def search(request):
    """
    请求参数
    Body:
    参数名称	参数类型	是否必须	示例	备注
    search_name	T文本	是	嘉然今天吃什么

    返回数据
    名称         	类型	     是否必须	默认值	备注	其他信息
    data         	object	 非必须
     - mid          num      必须     up主B站uid
     - name	        string   必须     up主姓名
     - fans	        num	     必须     up主粉丝数
     - usign	    string	 必须     up主签名
     - upic         string   必须     up主头像地址
     - raw          object   必须     原始查询结果
    code	integer	必须
    """
    name = request.GET.get('search_name')
    search_result = []
    for result in search_user_name.delay(name).get()["data"]["result"]:
        search_result.append({
            "mid": result["mid"],
            "uname": result["uname"],
            "fans": result["fans"],
            "usign": result["usign"],
            "upic": result["upic"],
            "raw": result
        })
    return JsonResponse({
        'code': 200,
        'data': search_result
    })


@login_required
def group_members(request):
    # URL形式传入需要切换的分组名
    # 传入gid，若无gid传入则显示默认全部分组
    # 传回显示分组的用户信息以及分组列表
    try:
        gid = int(request.GET.get('gid', 0))
        page = int(request.GET.get('page', 0))
        size = int(request.GET.get('size', 20))
    except KeyError or ValueError:
        raise BadRequest()
    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        members = group.first().members.all()
        members_count = members.count()
        page_start = page * size
        page_end = page_start + size
        paged = members[page_start:page_end]
        return JsonResponse({
            'code': 200,
            'data': {
                'has_more': page_end < members_count,
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


@login_required
def subscribe(request):
    # POST形式提交需要关注的up主的mid以及需要加入的分组的gid(以list形式)
    # 返回是否关注成功的结果result(success/fail)
    try:
        mid = int(request.POST['mid'])  # 需要关注的对象，以mid传递
        groups = [int(gid) for gid in request.POST.getlist('gid')]
    except KeyError or ValueError:  # 需要关注的对象还不在Member中，尝试加入
        raise BadRequest()
    if not SubscribeMember.objects.filter(mid=mid).exists():
        if not add_new_member(mid):
            return JsonResponse({
                'code': 404,
                'msg': "添加的up主不存在或不符合要求"
            }, status=404)
    MemberGroup.set_groups_by_account_and_member(aid=request.user.uid, mid=mid, groups=groups)
    return JsonResponse({'code': 200})


@login_required
def add_group(request):
    # POST提交新增分组的名称group_name
    # 返回是否关注成功的结果result(success/fail)
    try:
        group_name = request.POST['group_name']
    except KeyError:
        raise BadRequest()
    _, create = MemberGroup.objects.get_or_create(user_id=request.user.uid,
                                                  group_name=group_name)
    return JsonResponse({
        'code': 200,
        'success': create
    })


@login_required
def update_group(request):
    """
    更新分组信息
    :param request:
    :return:
    """
    try:
        gid = int(request.POST['gid'])
        group_name = request.POST.get('group_name')
    except KeyError or ValueError:
        raise BadRequest()

    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        if group_name:
            if group.group_name == models.DEFAULT_GROUP_NAME:
                return JsonResponse({
                    'code': 403,
                    'msg': "默认分组无法改名"
                })
            if MemberGroup.objects.filter(aid=request.user.uid, group_name=group_name).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': "分组名重复"
                })
            group.group_name = group_name
            group.save()
            return JsonResponse({
                'code': 200,
            })
    else:
        return JsonResponse({
            'code': 404,
            'msg': "分组不存在"
        }, status=404)


@require_http_methods(['DELETE'])
@login_required
def delete_group(request):
    try:
        gid = int(request.POST['gid'])
    except KeyError or ValueError:
        raise BadRequest()
    group = MemberGroup.get_group(aid=request.user.uid, gid=gid)
    if group is not None:
        if group.group_name == models.DEFAULT_GROUP_NAME:
            return JsonResponse({
                'code': 403,
                'msg': "默认分组无法被删除"
            })
        group.delete()
        return JsonResponse({
            'code': 200
        })
    else:
        return JsonResponse({
            'code': 404,
            'msg': "分组不存在"
        }, status=404)


@login_required
def mem_move(request):
    """
    移动一批成员到另一个分组里
    :param request:
    :return:
    """
    try:
        mid_list = [int(mid) for mid in request.POST.getlist('mid')]
        old_group = int(request.POST['old_group'])
        new_group = int(request.POST['new_group'])
        remove_old = request.POST.get('remove_old', 1)  # 是否从旧分组里删除
    except KeyError or ValueError:
        raise BadRequest()

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
    # 成功添加up主到up主数据库则返回True，否则返回False
    profile, msg = get_data_if_valid(user_profile.delay(mid).get())
    stat, s_msg = get_data_if_valid(user_stat.delay(mid).get())
    if profile is None or stat is None:
        return False

    # 判断添加的用户是否符合添加条件
    if stat["follower"] > 1000:
        member, _ = SubscribeMember.objects.update_or_create(mid=mid, name=profile["name"],
                                                              face=profile["face"])
        return member is not None
    else:
        return False

