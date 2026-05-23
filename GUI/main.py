"""GUI entry point. Run from the repo root: `python GUI/main.py`."""

from main_window import MainWindow


def main() -> None:
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
