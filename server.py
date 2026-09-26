# -*- coding: utf-8 -*-
"""
Unified Server bootstrap.

The original server was split into ordered modules under server_modules/.
They are executed in this module's global namespace so existing Flask route
registration, shared globals, and legacy socket behavior remain unchanged.
"""
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent
_SERVER_MODULES = [
    "core.py",
    "socket_tool_routes.py",
    "web_routes.py",
    "ai_routes.py",
    "tcp_server.py",
]


def _load_server_module(module_name):
    module_path = _SERVER_DIR / "server_modules" / module_name
    source = module_path.read_text(encoding="utf-8")
    code = compile(source, str(module_path), "exec")
    exec(code, globals(), globals())


for _module_name in _SERVER_MODULES:
    _load_server_module(_module_name)


del _module_name
