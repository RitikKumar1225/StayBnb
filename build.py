import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "staybnb.settings")
django.setup()

from django.core.management import call_command

print("Running migrations...")
call_command("migrate", interactive=False)

print("Seeding sample data...")
try:
    call_command("seed_sample_data")
except Exception as e:
    print(f"Sample data seed note: {e}")

print("Build script finished.")
