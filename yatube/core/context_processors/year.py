from django.utils import timezone


def year(request) -> int:
    """Добавляет переменную с текущим годом."""
    now_year = timezone.now()
    return {
        'year': now_year.year,
    }
