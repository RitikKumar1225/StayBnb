import os
import shutil
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "staybnb.settings")

# When running in serverless environment (Vercel) without external DB, prepare /tmp/db.sqlite3
if os.environ.get("VERCEL") and not os.environ.get("DATABASE_URL"):
    base_dir = Path(__file__).resolve().parent.parent
    tmp_db = Path("/tmp/db.sqlite3")
    source_db = base_dir / "db.sqlite3"
    if not tmp_db.exists() and source_db.exists():
        try:
            shutil.copyfile(source_db, tmp_db)
        except Exception as e:
            print(f"Error copying SQLite database to /tmp: {e}")

    try:
        import django
        django.setup()
        from reviews.models import Review
        if not Review.objects.exists():
            from django.core.management import call_command
            call_command("migrate", interactive=False)
            call_command("seed_sample_data")
    except Exception as e:
        print(f"Auto-migration/seed note: {e}")

application = get_wsgi_application()
app = application
