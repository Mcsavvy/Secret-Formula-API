#!/usr/bin/env python
import click
from flask.cli import FlaskGroup

from cookgpt import create_app_wsgi


@click.group(cls=FlaskGroup, create_app=create_app_wsgi)
def main():
    """Management script for the cookgpt application."""


if __name__ == "__main__":  # pragma: no cover
    main()