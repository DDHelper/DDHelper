from django.shortcuts import render
from django.views.generic import FormView


class LoginView(FormView):
    """
    请求参数
    Body:
      参数名称	参数类型	是否必须	示例	    备注
      username	T文本	是	    pawn
      password	T文本	是	    123456

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	number	必须
    msg	    string	非必须
    data	object	必须
     - uid	string	必须

    使用账号名和密码进行登录。
    如果登录成功，返回用户信息，通过Set-Cookies返回认证信息
    如果登录失败，code设置为403，不返回data
    """
    pass


class RegisterView(FormView):
    """
    请求参数
    Body:
    参数名称	    参数类型	是否必须	示例	       备注
    username	T文本	是	    user_abcd
    password	T文本	是	    123456abcd

    返回数据
    名称	     类型	是否必须	默认值	备注	其他信息
    code	integer	必须
    msg	    string	非必须

    注册一个账号。
    如果注册成功，正常返回
    如果注册失败，code设置为403，msg为注册失败的原因
    """
    pass
