#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
from django.core.management.commands.runserver import Command as runserver
import os
import sys

runserver.default_port = 8010


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', "core.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("nel")  # from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
