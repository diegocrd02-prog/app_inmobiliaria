from datetime import timedelta
import threading

from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone

from estateAgency.models import ScrapingLog


SCRAPING_LOCK_KEY = "pisos_scraping_running"
SCRAPING_LAST_CHECK_KEY = "pisos_scraping_last_check"


def pisos_com_scraping_group():
    from .services import chartService
    call_command(
            "import_pisos",
            operation="sale",
            limit=15,
            max_duplicates=5,
        )
    chartService.create_market_summary("sale")
    call_command(
        "import_pisos",
        operation="rent",
        rental_type="short",
        limit=15,
        max_duplicates=5,
    )
    chartService.create_market_summary("rent_short")
    call_command(
        "import_pisos",
        operation="rent",
        rental_type="long",
        limit=15,
        max_duplicates=5,
    )
    chartService.create_market_summary("rent_long")
    
def fotocasa_scraping_group():
    call_command(
        "import_fotocasa",
        operation="sale",
        limit=15,
        max_duplicates=5,
    )
    call_command(
        "import_fotocasa",
        operation="rent",
        rental_type="short",
        limit=15,
        max_duplicates=5,
    )
    call_command(
        "import_fotocasa",
        operation="rent",
        rental_type="long",
        limit=15,
        max_duplicates=5,
    )
    
def thinkspain_scraping_group():
    call_command(
        "import_thinkspain",
        operation="sale",
        limit=15,
        max_duplicates=5,
    )
    call_command(
        "import_thinkspain",
        operation="rent",
        rental_type="short",
        limit=15,
        max_duplicates=5,
    )
    call_command(
        "import_thinkspain",
        operation="rent",
        rental_type="long",
        limit=15,
        max_duplicates=5,
    )


def run_scraping():
    try:
        #fotocasa_scraping_group()
        pisos_com_scraping_group()
        #thinkspain_scraping_group()
    finally:
        cache.delete(SCRAPING_LOCK_KEY)

class AutoScrapingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.check_and_launch_scraping()
        return self.get_response(request)

    def check_and_launch_scraping(self):
        # Evita consultar la BD en cada request
        if cache.get(SCRAPING_LAST_CHECK_KEY):
            return

        cache.set(SCRAPING_LAST_CHECK_KEY, True, timeout=60 * 30)

        # Evita lanzar varios scrapings a la vez
        if cache.get(SCRAPING_LOCK_KEY):
            return

        last_log = (
            ScrapingLog.objects
            .filter(source__name="pisos.com")
            .order_by("-created_at")
            .first()
        )

        should_scrape = False

        if not last_log:
            should_scrape = True
        else:
            should_scrape = last_log.created_at <= timezone.now() - timedelta(days=3)

        if not should_scrape:
            return

        cache.set(SCRAPING_LOCK_KEY, True, timeout=60 * 60 * 3)

        thread = threading.Thread(target=run_scraping)
        thread.daemon = True
        thread.start()