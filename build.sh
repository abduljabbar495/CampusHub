#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt

# Safety net: if migrations were never generated/committed, create them now.
if ! ls accounts/migrations/0*.py >/dev/null 2>&1; then
  python manage.py makemigrations accounts academics campus security --no-input
fi

python manage.py collectstatic --no-input
python manage.py migrate --no-input

if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]]; then
  python manage.py createsuperuser --no-input || true
fi
