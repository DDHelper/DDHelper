from django.contrib.auth.forms import UserCreationForm
from .models import Userinfo

class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Userinfo
        fields = ("username", "email", "uid")