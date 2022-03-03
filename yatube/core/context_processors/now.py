from django.utils import timezone


def now(request):
    """Добавляет переменную с текущим временем относительно часового пояса."""
    now = timezone.now()
    return {
        'now': now
    }
