"""Shared rate-limiter singleton.

Imported by main.py (to attach to app.state) and by router modules that
use @limiter.limit() decorators. Kept in its own module to avoid circular
imports between main.py and the auth package.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
