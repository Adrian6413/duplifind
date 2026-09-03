"""Interfejs wiersza poleceń dla duplifind."""

import argparse
import json
import sys
from pathlib import Path

from duplifind.grouping import DuplicateGroup, group_duplicates
from duplifind.scanner import scan_directory

# Wartość dobrana na oko po testach - do 5 bitów różnicy to zwykle
# to samo zdjęcie po przeskalowaniu/rekompresji, a nie dwa różne ujęcia.
DEFAULT_THRESHOLD = 5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="duplifind",
        description="Znajduje zduplikowane i podobne zdjęcia w katalogu.",
    )
    parser.add_argument("directory", type=Path, help="Katalog do przeszukania (rekurencyjnie)")
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Maksymalna odległość Hamminga uznawana za duplikat (domyślnie {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Wypisz wynik jako JSON zamiast czytelnego dla człowieka raportu",
    )
    parser.add_argument(
        "--delete-dry-run",
        action="store_true",
        help="Pokaż, które pliki zostałyby usunięte (wszystkie poza największym "
        "w każdej grupie), bez faktycznego usuwania niczego",
    )
    return parser


def format_size(num_bytes: int) -> str:
    """Formatuje bajty do czytelnej postaci (KB/MB/GB)."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def groups_to_json(groups: list[DuplicateGroup]) -> list[dict]:
    return [
        {
            "images": [
                {"path": str(img.path), "size_bytes": img.size_bytes}
                for img in group.images
            ],
            "largest": str(group.largest.path),
            "wasted_bytes": group.wasted_bytes,
        }
        for group in groups
    ]


def print_human_report(groups: list[DuplicateGroup], delete_dry_run: bool) -> None:
    if not groups:
        print("Nie znaleziono duplikatów.")
        return

    total_wasted = sum(group.wasted_bytes for group in groups)
    print(
        f"Znaleziono {len(groups)} grup(y) duplikatów. "
        f"Do odzyskania: {format_size(total_wasted)}\n"
    )

    for i, group in enumerate(groups, start=1):
        largest = group.largest
        wasted = format_size(group.wasted_bytes)
        print(f"Grupa {i} ({len(group.images)} plików, marnowane: {wasted}):")
        for img in sorted(group.images, key=lambda x: x.size_bytes, reverse=True):
            marker = " [NAJWIĘKSZY - zachować]" if img is largest else ""
            deletion_note = ""
            if delete_dry_run and img is not largest:
                deletion_note = "  <- zostałby usunięty (--delete-dry-run)"
            print(f"  - {img.path} ({format_size(img.size_bytes)}){marker}{deletion_note}")
        print()


def main(argv: list[str] | None = None) -> int:
    # Bez tego print() z polskimi znakami wywala się na Windows (cp1252
    # nie zna np. "Ę"). Wymuszamy UTF-8 na wyjściu.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.directory.is_dir():
        print(f"Błąd: {args.directory} nie jest katalogiem", file=sys.stderr)
        return 1

    images, errors = scan_directory(args.directory)
    groups = group_duplicates(images, threshold=args.threshold)

    if args.json:
        print(json.dumps(groups_to_json(groups), ensure_ascii=False, indent=2))
    else:
        print_human_report(groups, delete_dry_run=args.delete_dry_run)

    if errors:
        print(
            f"\nPominięto {len(errors)} plik(ów), których nie dało się odczytać:",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  - {error.path}: {error.reason}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
