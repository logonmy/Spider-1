from django.shortcuts import render
from django.shortcuts import HttpResponse

# Create your views here.

# 根据API 返回 内容
def home (request):

    return render(request, "index.html",)