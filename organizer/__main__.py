"""Dependency-free command line interface; preview is the default action."""

import argparse
from pathlib import Path
import sqlite3

from organizer.core import scan
from organizer.history import History


def main():
    parser = argparse.ArgumentParser(description="Preview, organize, and undo local file moves.")
    parser.add_argument("folder", nargs="?", help="Folder to preview or organize")
    parser.add_argument("--apply", action="store_true", help="Apply moves after confirmation")
    parser.add_argument("--undo", action="store_true", help="Undo latest available batch")
    parser.add_argument("--history", action="store_true", help="Show operation history")
    args = parser.parse_args()
    history = History(Path(__file__).resolve().parent.parent / ".organizer" / "history.sqlite")
    try:
        history.reconcile()
        if args.undo:
            history.undo_latest()
        elif not args.history:
            if not args.folder:
                parser.error("Provide a folder, --history, or --undo.")
            plan = scan(args.folder)
            for move in plan:
                print(f"{move.source.name} -> {move.destination}")
            print(f"{len(plan)} eligible files.")
            if args.apply and plan:
                if input("Type APPLY to organize these files: ") != "APPLY":
                    print("Cancelled.")
                    return
                history.apply(plan)
                history.reconcile()
        if args.apply or args.undo or args.history:
            for row in history.rows():
                print(f"{row['state']}: {row['source']} -> {row['destination']} {row['error']}")
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Error: {error}\n")
    finally:
        history.close()


if __name__ == "__main__":
    main()
