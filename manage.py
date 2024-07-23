#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
from django.core.management.commands.runserver import Command as runserver
from dotenv import load_dotenv
import os
import sys
load_dotenv()

try:
    runserver.default_port = int(os.getenv("DJANGO_DEFAULT_PORT", 8000))
except ValueError:
    runserver.default_port = 8000
# runserver.default_port = 8010


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', "core.settings")
    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', "core.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("nel")  # from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
