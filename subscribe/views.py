import requests
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import JsonResponse

from account.models import Userinfo
from subscribe.models import SubscribeList, UserGroup, SubscribeMember


@login_required
def search(request):
    """
    请求参数
    Body:
    参数名称	参数类型	是否必须	示例	备注
    search_name	T文本	是	嘉然今天吃什么

    返回数据
    名称	类型	是否必须	默认值	备注	其他信息
    search_result	object	非必须
     - search_result_mid    num  非必须 up主B站uid
     - search_result_name	string	非必须 up主姓名	
     - search_result_fannum	num	非必须 up主粉丝数	
     - search_result_sign	string	非必须 up主签名
     - search_result_icon   string  非必须 up主头像地址	
    code	integer	必须
    """
    name = request.GET.get('search_name')
    search_result = []
    try:
        for result in search_user_name(name).json()["data"]["result"]:
            search_result.append({
                "search_result_mid": result["mid"],
                "search_result_name": result["uname"],
                "search_result_fannum": result["fans"],
                "search_result_sign": result["usign"],
                "search_result_icon": result["upic"]
            })
            rsp = JsonResponse({"search_result": search_result})
            rsp.status_code = 200
        return rsp
    except KeyError:
        # 搜索目标没有找到
        rsp = JsonResponse({"search_result": search_result})
        rsp.status_code = 200
        return rsp


@login_required
def showlist(request):
    # URL形式传入需要切换的分组名
    # 传入gid，若无gid传入则显示默认全部分组
    # 传回显示分组的用户信息以及分组列表
    query_result = list(SubscribeList.objects.filter(
        group__gid=request.GET.get('gid',
                                   default=UserGroup.objects.get_or_create(group_name='all', user=request.user)[0].gid)
    ).values('mem__mid'))  # 若无gid传入，则选择默认全体分组
    mem_list = []
    group_list = []
    for mem in query_result:
        mem_information = SubscribeMember.objects.get(pk=mem['mem__mid'])
        mem_list.append({'mid': mem_information.mid, 'face': mem_information.face, 'name': mem_information.name})
    for group in UserGroup.objects.filter(user__uid=request.user.uid):
        group_list.append({'gid': group.gid, 'group_name': group.group_name})
    rsp = JsonResponse({'member_data': mem_list, 'group_list': group_list})
    rsp.status_code = 200
    return rsp


@login_required
def mem_subscribe(request):
    # POST形式提交需要关注的up主的mid以及需要加入的分组的gid(以list形式)
    # 返回是否关注成功的结果result(success/fail)
    try:
        obj_mid = request.POST.get('mid')  # 需要关注的对象，以mid传递
        obj_mem = SubscribeMember.objects.get(mid=obj_mid)
    except ObjectDoesNotExist:  # 需要关注的对象还不在Member中，尝试加入
        if not add_new_member(obj_mid):
            return JsonResponse({'result': 'fail'})
        else:
            obj_mem = SubscribeMember.objects.get(mid=obj_mid)
    for obj_gid in request.POST.getlist('gid'):
        obj_group = UserGroup.objects.get(gid=obj_gid)
        if obj_group.user == request.user:
            SubscribeList.objects.update_or_create(mem=obj_mem, group=obj_group)
    SubscribeList.objects.update_or_create(mem=obj_mem,
                                           group=UserGroup.objects.get_or_create(group_name='all', user=request.user)[
                                               0])
    return JsonResponse({'result': 'success'})


@login_required
def add_group(request):
    # POST提交新增分组的名称group_name
    # 返回是否关注成功的结果result(success/fail)
    UserGroup.objects.create(user=Userinfo.objects.get(uid=request.user.uid),
                             group_name=request.POST.get('group_name'))
    return JsonResponse({'result': 'success'})


@login_required
def update_group(request):
    # POST中指名修改类型type(rename/delete)，要修改的分组gid，重命名时还要传递重命名的名称group_name
    # 返回是否关注成功的结果result(success/fail)
    try:
        obj_group = UserGroup.objects.get(gid=request.POST.get('gid'), user=Userinfo.objects.get(uid=request.user.uid))
    except UserGroup.DoesNotExist:
        return JsonResponse({'result': 'fail'})
    if request.POST.get('type') == 'rename':
        obj_group.group_name = request.POST.get('group_name')
        obj_group.save()
        return JsonResponse({'result': 'success'})
    elif request.POST.get('type') == 'delete':
        SubscribeList.objects.filter(group=obj_group).delete()
        obj_group.delete()
        return JsonResponse({'result': 'success'})
    else:
        return JsonResponse({'result': 'fail'})


@login_required
def mem_move(request):
    # POST中指名需要移动的up主的mid以及修改后所属分组的gid(以list形式)
    # 返回是否关注成功的结果result(success/fail)
    obj_mid = request.POST.get('mid')  # 需要移动的对象，以mid传递
    obj_mem = SubscribeMember.objects.get(mid=obj_mid)
    new_group = request.POST.getlist('gid')
    new_group.append(str(UserGroup.objects.get_or_create(group_name='all', user=request.user)[0].gid))
    cur_group = list(
        SubscribeList.objects.filter(group__user=request.user, mem=obj_mem).values_list('group__gid', flat=True))
    cur_group = list(map(str, cur_group))
    gid_add = list(set(new_group).difference(set(cur_group)))
    gid_del = list(set(cur_group).difference(set(new_group)))
    for temp_gid in gid_add:
        SubscribeList.objects.create(mem=obj_mem, group=UserGroup.objects.get(gid=temp_gid))
    for temp_gid in gid_del:
        SubscribeList.objects.get(mem=obj_mem, group=UserGroup.objects.get(gid=temp_gid)).delete()
    return JsonResponse({'result': 'success'})


def add_new_member(Memmid):
    # 成功添加up主到up主数据库则返回True，否则返回False
    search_result = search_user_id(Memmid).json()["data"]["result"]
    # 判断添加的用户是否符合添加条件
    for result in search_result:
        if result["result_type"] == 'user' and len(result["data"]) == 1:
            object_member = result["data"][0]
            if object_member["fans"] > 1000 and object_member["is_upuser"] == 1:
                SubscribeMember.objects.update_or_create(mid=Memmid, name=object_member["uname"],
                                                         face=object_member["upic"])
                return True
            else:
                return False


def search_user_name(name):
    rsp = requests.get("http://api.bilibili.com/x/web-interface/search/type",
                       params={
                           "search_type": "bili_user",
                           "keyword": name
                       },
                       timeout=2)
    return rsp


def search_user_id(mid):
    rsp = requests.get("http://api.bilibili.com/x/web-interface/search/all/v2",
                       params={
                           "keyword": f'uid:{mid}'
                       },
                       timeout=2)
    return rsp
