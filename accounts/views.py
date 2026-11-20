from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignUpForm


def signup(request):
    """
    User registration taking Full Name, Email, Phone Number, and Password.
    """
    next_url = request.GET.get('next') or request.POST.get('next') or 'event_list'
    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome to EventHub Campus, {user.first_name or user.username}!")
            return redirect(next_url)
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form, 'next_url': next_url})


# ==========================================================
# Google OAuth sign-in temporarily commented out as requested.
# To re-enable later, un-comment the routes in accounts/urls.py
# and the function below.
# ==========================================================
# def google_login(request):
#     pass
# def google_callback(request):
#     pass
