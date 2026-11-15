"""K.I.D local desktop application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
        from kid.ui.main_window import MainWindow
    except ImportError as exc:
        print(f"K.I.D desktop dependencies are missing: {exc}. Install with: pip install -e .", file=sys.stderr)
        return 2
    app = QApplication(sys.argv)
    app.setApplicationName("K.I.D — Key Intelligence Driver")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
