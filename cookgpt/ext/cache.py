"""
Application cache.
"""

from typing import TYPE_CHECKING

import click
from flask import request
from flask_caching import Cache
from flask_jwt_extended import get_current_user

from cookgpt import logging

if TYPE_CHECKING:
    from cookgpt.app import App

cache = Cache(with_jinja2_ext=False)


@click.group()
def cache_cli():
    """Cache commands."""
    pass


@cache_cli.command("clear")
def clear_cache():
    """Clear the cache."""
    cache.clear()
    logging.info("🚮 Cleared cache.")


def thread_cache_key(*args, **kwargs) -> str:
    """get the cache key for a thread"""
    thread_id = kwargs.get("thread_id")
    return f"thread:{thread_id}"


def threads_cache_key(*args, **kwargs) -> str:
    """get the cache key for a user's threads"""
    user_id = kwargs.get("user_id")
    if user_id is None:
        user_id = get_current_user().pk
    return f"threads:{user_id}"


def chat_cache_key(*args, **kwargs) -> str:
    """get the cache key for a chat"""
    chat_id = kwargs.get("chat_id")
    return f"chat:{chat_id}"


def chats_cache_key(*args, **kwargs) -> str:
    """get the cache key for a thread's chats"""
    thread_id = kwargs.get("thread_id")
    if thread_id is None:
        thread_id = request.args["thread_id"]
    return f"chats:{thread_id}"


def init_app(app: "App"):
    """Initialize Flask-Caching."""

    app.cli.add_command(cache_cli, "cache")
    cache.init_app(
        app,
        config={
            "CACHE_TYPE": "flask_caching.backends.RedisCache",
            "CACHE_REDIS_URL": app.config["REDIS_URL"],
            "CACHE_DEFAULT_TIMEOUT": app.config["CACHE_DEFAULT_TIMEOUT"],
        },
    )
