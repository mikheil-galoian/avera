"""AVERA REST API — FastAPI application.

.. deprecated::
    This package (``avera.api``) is the legacy REST API and is **not** wired
    into the project: the ``avera-api`` console script points to
    ``avera_api.main:main``, the README documents ``uvicorn avera_api.main:app``,
    and the test-suite imports ``avera_api.main``. Nothing imports ``avera.api``
    except itself.

    The canonical API lives in the top-level package ``avera_api`` (see
    ``src/avera_api/main.py``). Use that. This module is kept only as a
    compatibility stub and is a candidate for removal.
"""

from .app import create_app

__all__ = ["create_app"]
