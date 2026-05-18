from __future__ import annotations

import importlib.util
import os
import platform
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
ADAS_SHOWCASE = ROOT_DIR / "docs" / "AVERA_ADAS_SHOWCASE.html"


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    version = sys.version_info
    runtime = Path(sys.executable).resolve()
    using_project_venv = runtime == DEFAULT_VENV_PYTHON.resolve() if DEFAULT_VENV_PYTHON.exists() else False
    streamlit_available = has_module("streamlit")

    print("AVERA Runtime Doctor")
    print(f"Python executable: {runtime}")
    print(f"Python version: {platform.python_version()}")
    print(f"Using project .venv: {'yes' if using_project_venv else 'no'}")
    print(f"Streamlit available: {'yes' if streamlit_available else 'no'}")
    print(f"ADAS static showcase present: {'yes' if ADAS_SHOWCASE.exists() else 'no'}")

    warnings: list[str] = []
    errors: list[str] = []

    if version < (3, 11):
        errors.append("AVERA requires Python 3.11 or newer.")

    if version >= (3, 14):
        warnings.append(
            "Python 3.14 is usable for core/test work, but the Streamlit demo shell may cold-start slowly in this runtime."
        )

    if not using_project_venv:
        warnings.append(
            "The recommended runtime path for AVERA is the project .venv. External interpreters may not have matching demo dependencies."
        )

    if not streamlit_available:
        warnings.append(
            "Streamlit is not available in the current runtime. Core CLI work can continue, but the demo shell will not launch from this interpreter."
        )

    if os.environ.get("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION") == "python":
        print("protobuf runtime override: enabled")
    else:
        print("protobuf runtime override: disabled")

    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"- {item}")

    if errors:
        print("\nErrors:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("\nResult: runtime is acceptable for AVERA work.")
    if warnings:
        print("Use the warnings above to choose the safest shell/demo path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
