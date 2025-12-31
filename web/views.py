from django.shortcuts import render

# UI-only views (no business logic)

def login_view(request):
    return render(request, 'web/login.html')


def chat_view(request):
    return render(request, 'web/chat.html')

def register_view(request):
    return render(request, 'web/register.html')
