from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import Experiment, SessionBooking
from .forms import SignUpForm, ExperimentForm
import logging
import os
import threading
import subprocess

logger = logging.getLogger(__name__)

# Map experiment keys to their target UI URL and local restart script (relative to BASE_DIR)
_SERVICE_MAP = {
    "exp1": {"url": "http://10.7.43.10", "script": "scripts/restart_oai_core.sh"},
    "exp2": {"url": "http://10.7.43.11", "script": "scripts/restart_gnb.sh"},
    "exp3": {"url": "http://10.7.43.12", "script": "scripts/restart_ue.sh"},
    "exp4": {"url": "http://10.7.43.13", "script": "scripts/restart_open5gs.sh"},
    "exp5": {"url": "http://10.7.43.14", "script": "scripts/restart_free5gc.sh"},
}

def _run_script_async(script_path):
    """Run restart script in background thread."""
    def runner():
        try:
            subprocess.run(['bash', script_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("Restart script succeeded: %s", script_path)
        except Exception:
            logger.exception("Restart script failed: %s", script_path)
    t = threading.Thread(target=runner, daemon=True)
    t.start()

# ✅ Publicly accessible Intro Page (default landing)
def intro_view(request): 
    print("Intro page accessed.")
    return render(request, 'intro.html')
    
# ✅ Home Page - Requires login
# ✅ Home Page - Requires login
@login_required
def home(request):
    """Home page after login with booking context."""
    now = timezone.now()
    
    # Get all experiments
    experiments = Experiment.objects.all()
    
    # Get user's active bookings
    user_bookings = request.user.bookings.filter(
        status='active',
        start_time__lte=now,
        end_time__gt=now
    )
    
    # Get other users' active bookings
    other_bookings_qs = SessionBooking.objects.filter(
        status='active',
        start_time__lte=now,
        end_time__gt=now
    ).exclude(user=request.user)
    
    # Create lookup dicts
    user_bookings_map = {b.experiment.exp_key: b for b in user_bookings}
    other_bookings_map = {b.experiment.exp_key: b for b in other_bookings_qs}
    
    # Attach booking info to experiments
    for exp in experiments:
        exp.current_booking = user_bookings_map.get(exp.exp_key)
        exp.other_booking = other_bookings_map.get(exp.exp_key)
    
    context = {
        'experiments': experiments,
    }
    
    return render(request, 'home.html', context)


# ✅ Signup View
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

# ✅ Login View
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            return redirect('accounts:home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')


# ✅ Logout View
def logout_view(request):
    logout(request)
    messages.info(request, 'Successfully logged out.')
    return redirect('intro')  # Redirect to intro page on logout

# Optional: Profile Page (Protected)
@login_required
def profile_view(request):
    return render(request, 'registration/profile.html')

@login_required
def booking_dashboard(request):
    """Show a table of experiments and their availability for a specific date."""
    # Get date from query param or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.now().date()
    else:
        target_date = timezone.now().date()

    now = timezone.now()
    experiments = Experiment.objects.all()
    
    # Get user's upcoming bookings
    user_bookings = request.user.bookings.filter(
        status='active',
        start_time__gte=now
    ).order_by('start_time')
    
    # Build context with experiments and their availability
    context = {
        'experiments': experiments,
        'target_date': target_date,
        'user_bookings': user_bookings,
    }
    
    return render(request, 'booking_dashboard.html', context)

@login_required
def start_experiment(request, booking_id):
    """Allow user to start an active experiment session and trigger restart."""
    booking = get_object_or_404(SessionBooking, id=booking_id, user=request.user)
    now = timezone.now()
    
    # Verify session is active and within time window
    if not (booking.start_time <= now < booking.end_time) or booking.status != 'active':
        return HttpResponseBadRequest("Booking is not currently active.")
    
    # Trigger restart script asynchronously
    exp = booking.experiment
    script_rel = _SERVICE_MAP.get(exp.exp_key, {}).get('script')
    if script_rel:
        script_path = os.path.join(settings.BASE_DIR, script_rel)
        if os.path.exists(script_path) and os.access(script_path, os.X_OK):
            _run_script_async(script_path)
            logger.info("Restart triggered for booking %s (user: %s)", booking_id, request.user.username)
    
    # Redirect to experiment UI
    return redirect(exp.full_url)


@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking (before it starts)."""
    booking = get_object_or_404(SessionBooking, id=booking_id, user=request.user)
    now = timezone.now()
    
    # Only allow cancellation before the session starts
    if booking.start_time <= now:
        return HttpResponseBadRequest("Cannot cancel an active or past session.")
    
    booking.status = 'cancelled'
    booking.save()
    logger.info("Booking %s cancelled by user %s", booking_id, request.user.username)
    
    return redirect('accounts:booking_dashboard')


@login_required
def get_available_slots(request):
    """API endpoint to return available slots for an experiment (JSON)."""
    exp_key = request.GET.get('exp')
    date_str = request.GET.get('date')
    duration = int(request.GET.get('duration', 60))
    
    if not exp_key:
        return JsonResponse({'error': 'Missing experiment'}, status=400)
    
    experiment = get_object_or_404(Experiment, exp_key=exp_key)
    
    # Parse target date
    if date_str:
        try:
            target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            # Start from beginning of target date or now, whichever is later
            start_of_day = timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.min.time()))
            current = max(start_of_day, timezone.now())
        except ValueError:
            current = timezone.now()
    else:
        current = timezone.now()
    
    # Round up to nearest 5 minutes for cleaner slots
    current = current + timedelta(minutes=5 - (current.minute % 5))
    
    # Generate available slots
    slots = []
    max_iterations = 50  # Prevent infinite loops
    
    for _ in range(max_iterations):
        slot_end = current + timedelta(minutes=duration)
        
        # Check if slot overlaps with existing bookings
        conflict = experiment.bookings.filter(
            status='active',
            start_time__lt=slot_end,
            end_time__gt=current
        ).exists()
        
        # Check if it's the user's own booking
        user_booking = experiment.bookings.filter(
            user=request.user,
            status='active',
            start_time__lt=slot_end,
            end_time__gt=current
        ).first()
        
        if user_booking:
            slots.append({
                'start': current.isoformat(),
                'end': slot_end.isoformat(),
                'display': timezone.localtime(current).strftime('%H:%M'),
                'status': 'my_booking'
            })
        elif conflict:
            slots.append({
                'start': current.isoformat(),
                'end': slot_end.isoformat(),
                'display': timezone.localtime(current).strftime('%H:%M'),
                'status': 'booked'
            })
        else:
            slots.append({
                'start': current.isoformat(),
                'end': slot_end.isoformat(),
                'display': timezone.localtime(current).strftime('%H:%M'),
                'status': 'available'
            })
        
        # Move to next slot
        current = current + timedelta(minutes=30)
        
        # Stop if we have enough slots or moved to next day
        if len(slots) >= 20:
            break
    
    return JsonResponse({'slots': slots})

@login_required
@require_POST
def trigger_service(request):
    """Trigger restart for a mapped experiment (only via POST)."""
    exp = request.POST.get("exp")
    if not exp or exp not in _SERVICE_MAP:
        return HttpResponseBadRequest("Invalid experiment selection.")

    entry = _SERVICE_MAP[exp]
    script_rel = entry.get("script")
    script_path = os.path.join(settings.BASE_DIR, script_rel) if script_rel else None

    if script_path and os.path.exists(script_path) and os.access(script_path, os.X_OK):
        logger.info("User %s triggered restart for %s (script: %s)", request.user.username, exp, script_path)
        _run_script_async(script_path)
    else:
        logger.warning("Restart script missing or not executable for %s: %s", exp, script_path)

    return redirect(entry["url"])

@login_required
@require_POST
def book_session(request):
    """Book a session for an experiment with custom duration."""
    exp_key = request.POST.get('exp')
    start_time_str = request.POST.get('start_time')
    duration = int(request.POST.get('duration', 60))
    
    if not exp_key or not start_time_str:
        return HttpResponseBadRequest("Missing experiment or start_time.")
    
    experiment = get_object_or_404(Experiment, exp_key=exp_key)
    
    try:
        logger.info(f"Received start_time_str: {start_time_str}")
        start_time = timezone.datetime.fromisoformat(start_time_str)
        logger.info(f"Parsed start_time: {start_time}, is_naive: {timezone.is_naive(start_time)}, tzinfo: {start_time.tzinfo}")
        # Only make aware if the datetime is truly naive (no timezone info)
        # fromisoformat() returns timezone-aware datetime if the string includes timezone
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
            logger.info(f"After make_aware: {start_time}, tzinfo: {start_time.tzinfo}")
    except ValueError as e:
        logger.error(f"Failed to parse start_time: {start_time_str}, error: {e}")
        return HttpResponseBadRequest("Invalid start_time format.")
    
    end_time = start_time + timedelta(minutes=duration)
    logger.info(f"Booking: start={start_time}, end={end_time}, duration={duration}min")
    now = timezone.now()
    
    # Validate: cannot book in the past
    if start_time < now:
        return HttpResponseBadRequest("Cannot book in the past.")
    
    # Validate: no overlap with existing bookings
    conflict = experiment.bookings.filter(
        status='active',
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists()
    
    if conflict:
        return HttpResponseBadRequest("Time slot is already booked.")
    
    # Create booking
    booking = SessionBooking.objects.create(
        user=request.user,
        experiment=experiment,
        start_time=start_time,
        end_time=end_time,
        status='active'
    )
    
    logger.info("User %s booked %s from %s to %s (%d min)", 
                request.user.username, exp_key, start_time, end_time, duration)
    
    return redirect('accounts:booking_dashboard')


@staff_member_required
@require_POST
def add_experiment(request):
    """Add a new experiment (admin only)."""
    form = ExperimentForm(request.POST)
    
    if form.is_valid():
        experiment = form.save(commit=False)
        experiment.created_by = request.user
        experiment.save()
        
        messages.success(request, f'Experiment "{experiment.name}" added successfully!')
        logger.info("Admin %s created new experiment: %s", request.user.username, experiment.name)
    else:
        messages.error(request, 'Failed to add experiment. Please check the form.')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    return redirect('accounts:home')
