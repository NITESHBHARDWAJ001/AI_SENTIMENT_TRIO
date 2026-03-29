from __future__ import annotations

import sys
from pathlib import Path


def _load_create_app():
    # Support both execution styles:
    # 1) python -m backend.app   (package context)
    # 2) python app.py           (direct script inside backend/)
    try:
        from . import create_app as factory
        return factory
    except ImportError:
        project_root = Path(__file__).resolve().parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from backend import create_app as factory
        return factory


create_app = _load_create_app()
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
