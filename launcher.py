import os
import sys
from pathlib import Path


def _resolve_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main():
    root = _resolve_root()
    os.chdir(root)
    sys.path.insert(0, str(root))

    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        from app.main import main as cli_main
        cli_main()
    else:
        from app.web_desktop import main as web_main
        web_main()


if __name__ == "__main__":
    main()
