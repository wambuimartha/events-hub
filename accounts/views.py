import urllib.parse
import secrets
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse
from decouple import config


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
    Initiates real Google OAuth2 sign-in.
    If GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are configured,
    redirects directly to Google's official accounts.google.com sign-in page.
    Otherwise, displays the setup helper and fallback form.
    """
    next_url = request.GET.get('next') or request.POST.get('next') or 'event_list'

    if request.user.is_authenticated:
        return redirect(next_url)

    client_id = config('GOOGLE_CLIENT_ID', default='').strip()
    client_secret = config('GOOGLE_CLIENT_SECRET', default='').strip()

    callback_uri = request.build_absolute_uri(reverse('google_callback'))
    if not request.is_secure() and ('onrender.com' in request.get_host() or 'vercel.app' in request.get_host()):
        callback_uri = callback_uri.replace('http://', 'https://')

    # If credentials are configured and this is a GET request, redirect directly to Google OAuth2
    if client_id and client_secret and request.method == 'GET':
        state = secrets.token_urlsafe(24)
        request.session['google_oauth_state'] = state
        request.session['google_oauth_next'] = next_url

        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': callback_uri,
            'scope': 'openid email profile',
            'state': state,
            'prompt': 'select_account',
            'access_type': 'offline',
        }
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
        return redirect(google_auth_url)

    # Fallback / manual handling when credentials not yet set or manual POST
    if request.method == 'POST':
        google_email = request.POST.get('google_email', '').strip()
        google_name = request.POST.get('google_name', '').strip() or 'Google Student'

        if not google_email or '@' not in google_email:
            messages.error(request, 'Please provide a valid Google email address.')
            return render(request, 'registration/google_auth.html', {
                'next_url': next_url,
                'callback_uri': callback_uri,
                'missing_credentials': not (client_id and client_secret)
            })

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
        messages.success(request, f"Signed in as {user.email}!")
        return redirect(next_url)

    return render(request, 'registration/google_auth.html', {
        'next_url': next_url,
        'callback_uri': callback_uri,
        'missing_credentials': not (client_id and client_secret),
    })


def google_callback(request):
    """
    Handles the redirect callback from Google OAuth2.
    Exchanges the authorization code for the student's real Google profile info.
    """
    error = request.GET.get('error')
    if error:
        messages.error(request, f"Google sign-in was cancelled: {error}")
        return redirect('login')

    code = request.GET.get('code')
    state = request.GET.get('state')
    saved_state = request.session.get('google_oauth_state')
    next_url = request.session.get('google_oauth_next') or 'event_list'

    if not code or not state or state != saved_state:
        messages.error(request, "Google authentication state mismatch. Please try again.")
        return redirect('login')

    client_id = config('GOOGLE_CLIENT_ID', default='').strip()
    client_secret = config('GOOGLE_CLIENT_SECRET', default='').strip()

    callback_uri = request.build_absolute_uri(reverse('google_callback'))
    if not request.is_secure() and ('onrender.com' in request.get_host() or 'vercel.app' in request.get_host()):
        callback_uri = callback_uri.replace('http://', 'https://')

    # Exchange code for access token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': callback_uri,
        'grant_type': 'authorization_code',
    }

    try:
        token_resp = requests.post(token_url, data=token_data, timeout=12)
        token_json = token_resp.json()
        access_token = token_json.get('access_token')

        if not access_token:
            err = token_json.get('error_description') or token_json.get('error') or 'Token exchange failed'
            messages.error(request, f"Google sign-in error: {err}")
            return redirect('login')

        # Retrieve user profile from Google UserInfo endpoint
        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={'Authorization': f"Bearer {access_token}"},
            timeout=12
        )
        userinfo = userinfo_resp.json()

        google_email = userinfo.get('email', '').strip()
        google_name = userinfo.get('name', '').strip()
        first_name = userinfo.get('given_name', '')
        last_name = userinfo.get('family_name', '')

        if not google_email:
            messages.error(request, "Could not retrieve email from your Google account.")
            return redirect('login')

        # Find existing user or create a new student account
        user = User.objects.filter(email=google_email).first()
        if not user:
            clean_user = google_email.split('@')[0].replace('.', '_').replace('-', '_')
            username = clean_user
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{clean_user}{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=google_email,
                first_name=first_name or (google_name.split()[0] if google_name else 'Student'),
                last_name=last_name or (' '.join(google_name.split()[1:]) if google_name and len(google_name.split()) > 1 else '')
            )
            user.set_unusable_password()
            user.save()
        else:
            updated = False
            if not user.first_name and first_name:
                user.first_name = first_name
                updated = True
            if not user.last_name and last_name:
                user.last_name = last_name
                updated = True
            if updated:
                user.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f"Signed in with Google as {user.email}!")
        return redirect(next_url)

    except Exception as e:
        messages.error(request, f"Failed to connect to Google OAuth: {e}")
        return redirect('login')
