from django.contrib.auth.models import Group, User
from django.http.response import HttpResponseForbidden, HttpResponseServerError, JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import requests
from account.models import Userinfo
from subscribe.models import SubscribeList, UserGroup
from dynamic.models import Member
from django.core.exceptions import ObjectDoesNotExist


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
    name = request.GET.get("search_name")
    search_result = []
    try:
        for result in search_user(name).json()["data"]["result"]:
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
    except KeyError:# 搜索目标没有找到
        rsp = JsonResponse({"search_result": search_result})
        rsp.status_code = 200
        return rsp
    except Exception:
        return HttpResponseServerError


@login_required
def showlist(request):
    # URL形式传入需要切换的分组名
    # 传入gid，若无gid传入则显示默认全部分组
    # 传回显示分组的用户信息以及分组列表
    try:
        query_result = list(SubscribeList.objects.filter(group__gid = request.GET.get('gid')).values('mem__mid'))
    except KeyError:
        # GET中没有分组名，访问默认分组即全体关注列表
        all_group = UserGroup.objects.get(group_name = 'all', user__uid = request.user.uid)#当前用户的默认全体分组
        query_result = list(SubscribeList.objects.filter(group = all_group).values('mem__mid'))
    finally:
        mem_list = []
        group_list = []
        for mem in query_result:
            mem_information = Member.objects.get(pk=mem['mem_id'])
            mem_list.append({'mid': mem_information.mid, 'face': mem_information.face, 'name': mem_information.name})
        for group in UserGroup.objects.filter(user__uid = request.user.uid):
            group_list.append({'gid':group.gid, 'group_name':group.group_name})
        rsp = JsonResponse({'member_data': mem_list, 'group_list': group_list})
        rsp.status_code = 200
        return rsp


@login_required
def mem_subscribe(request):
    #POST形式提交需要关注的up主的mid以及需要加入的分组的gid(以list形式)
    #返回是否关注成功的结果result(success/fail)
    try:
        obj_mid = request.POST.get('mid')    #需要关注的对象，以mid传递
        obj_mem = Member.objects.get(mid = obj_mid)
    except ObjectDoesNotExist:  #需要关注的对象还不在Member中，尝试加入
        if not add_new_member(obj_mid):
            return JsonResponse({'result': 'fail'})
        else:
            obj_mem = Member.objects.get(mid = obj_mid)    
    for obj_gid in request.POST.get('gid')
        SubscribeList.objects.create(mem = obj_mem, group = UserGroup.objects.get(gid=obj_gid))
    SubscribeList.objects.create(mem = obj_mem, group = UserGroup.objects.get(group_name = 'all', user = request.user))        
    return JsonResponse({'result': 'success'})


@login_required
def add_group(request):
    #POST提交新增分组的名称group_name
    #返回是否关注成功的结果result(success/fail)
    try:
        UserGroup.objects.create(user = UserGroup.objects.filter(user__uid = request.user.uid), 
                                group_name = request.POST.get('group_name'))
        return JsonResponse({'result': 'success'})
    except:
        return JsonResponse({'result': 'fail'})


@login_required
def update_group(request):
    #POST中指名修改类型type(rename/delete)，要修改的分组gid，重命名时还要传递重命名的名称group_name
    #返回是否关注成功的结果result(success/fail)
    if request.POST.get('type') == 'rename':
        try:
            obj_group = UserGroup.objects.get(gid = request.POST.get('gid'))
            obj_group.group_name = request.POST.get('group_name')
            obj_group.save()
            return JsonResponse({'result': 'success'})
        except:
            return JsonResponse({'result': 'fail'})
    elif request.POST.get('type') == 'delete':
        try:
            obj_group = UserGroup.objects.get(gid = request.POST.get('gid'))
            SubscribeList.objects.filter(group = obj_group).delete()
            obj_group.delete()
            return JsonResponse({'result': 'success'})
        except:
            return JsonResponse({'result': 'fail'})
    else:
        return HttpResponseServerError("wrong type of updating")


@login_required
def mem_move(request):
    #POST中指名需要移动的up主的mid以及修改后所属分组的gid(以list形式)
    #返回是否关注成功的结果result(success/fail)
    obj_mid = request.POST.get('mid')    #需要移动的对象，以mid传递
    obj_mem = Member.objects.get(mid = obj_mid)
    new_group = request.POST.get('gid')
    new_group = new_group.append(UserGroup.objects.get(group_name = 'all', user = request.user).gid)
    cur_group = list(SubscribeList.objects.filter(group__user = request.user, mem = obj_mem).values('group__gid'))
    gid_add = list(set(new_group).difference(set(cur_group)))
    gid_del = list(set(cur_group).difference(set(new_group)))
    for temp_gid in gid_add
        SubscribeList.objects.create(mem = obj_mem, group = UserGroup.objects.get(gid=temp_gid))
    for temp_gid in gid_del
        SubscribeList.objects.get(mem = obj_mem, group = UserGroup.objects.get(gid=temp_gid)).delete()    
    return JsonResponse({'result': 'success'})



def add_new_member(mid):
    #成功添加up主到up主数据库则返回True，否则返回False
    return


def search_user(name):
    rsp = requests.get("http://api.bilibili.com/x/web-interface/search/type",
                       params={
                           "search_type": "bili_user",
                           "keyword": name
                       },
                       timeout=2)
    return rsp
