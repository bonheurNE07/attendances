from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser

import pyttsx3

def text_to_speech(text):
    # Initialize the TTS engine
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    # Set properties (optional)
    engine.setProperty('voice', voices[18].id)  
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 1)  # Volume (0.0 to 1.0)
    
    # Speak the text
    engine.say(text)
    
    # Wait for the speaking to finish
    engine.runAndWait()

# User registration view
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        photo = request.FILES.get('photo')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect(reverse_lazy('core:register'))
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect(reverse_lazy('core:register'))
        
        user = CustomUser.objects.create_user(username=username, password=password1, email=email,
                                              first_name=first_name, last_name=last_name, role=role, photo=photo)
        messages.success(request, 'Account created successfully!')
        return redirect(reverse_lazy('core:login'))
    # Pass role choices to the template
    role_choices = CustomUser.ROLE_CHOICES
    
    return render(request, 'core/register.html', {'role_choices': role_choices})

# User login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect(reverse_lazy('core:home'))
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')

# User logout view
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect(reverse_lazy('core:login'))

# Profile update view
@login_required
def profile_view(request):
    # Get the logged-in user
    user = request.user

    if request.method == 'POST':
        # Get data from the form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        photo = request.FILES.get('photo')

        # Update user's information
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        if photo:
            user.photo = photo
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect(reverse_lazy('core:home'))

    # Render the profile page with the user's existing data
    return render(request, 'core/profile.html', {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'photo': user.photo
    })

def home(request):
    text_to_speech("Welcom!")
    return render(request, 'core/home.html')


def custom_permission_denied_view(request, exception):
    return render(request, '403.html', status=403)
