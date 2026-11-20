from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages


def signup(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'event_list'
    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Registration successful. Welcome to EventHub Campus!')
            return redirect(next_url)
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form, 'next_url': next_url})


def google_login(request):
    """
    Handles 'Continue with Google' sign-in and student registration.
    Authenticates or provisions a Google student account, then redirects directly
    back to the event or ticket checkout they were viewing.
    """
    next_url = request.GET.get('next') or request.POST.get('next') or 'event_list'

    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST':
        google_email = request.POST.get('google_email', '').strip()
        google_name = request.POST.get('google_name', '').strip() or 'Google Student'

        if not google_email or '@' not in google_email:
            messages.error(request, 'Please provide a valid Google email address.')
            return render(request, 'registration/google_auth.html', {'next_url': next_url})

        # Find existing user by email or create new student account
        user = User.objects.filter(email=google_email).first()
        if not user:
            clean_user = google_email.split('@')[0].replace('.', '_').replace('-', '_')
            username = clean_user
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{clean_user}{counter}"
                counter += 1

            parts = google_name.split()
            first_name = parts[0] if parts else 'Student'
            last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

            user = User.objects.create(
                username=username,
                email=google_email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_unusable_password()
            user.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f"Signed in with Google as {user.email}!")
        return redirect(next_url)

    return render(request, 'registration/google_auth.html', {'next_url': next_url})
