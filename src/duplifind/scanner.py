"""Szukanie zdjęć w katalogu i liczenie ich hashy."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from duplifind.hashing import dhash

# Rozszerzenia, które próbujemy otworzyć jako obrazy - reszta plików
# w katalogu (logi, .DS_Store itp.) jest po prostu pomijana.
SUPPORTED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"})


@dataclass(frozen=True, slots=True)
class ScannedImage:
    """Wynik udanego przetworzenia jednego pliku."""

    path: Path
    hash_value: int
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ScanError:
    """Plik, którego nie dało się przetworzyć — i dlaczego."""

    path: Path
    reason: str


def _iter_candidate_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def scan_directory(root: str | Path) -> tuple[list[ScannedImage], list[ScanError]]:
    """Rekurencyjnie skanuje katalog i liczy dhash każdego zdjęcia.

    Zepsuty plik nie przerywa całego skanowania - trafia do listy błędów
    i skanowanie idzie dalej.
    """
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"{root} nie jest katalogiem")

    results: list[ScannedImage] = []
    errors: list[ScanError] = []

    for path in _iter_candidate_files(root):
        try:
            size_bytes = path.stat().st_size
            hash_value = dhash(path)
        except UnidentifiedImageError:
            errors.append(ScanError(path, "nierozpoznany format obrazu"))
        except (OSError, Image.DecompressionBombError) as exc:
            errors.append(ScanError(path, str(exc)))
        else:
            results.append(ScannedImage(path=path, hash_value=hash_value, size_bytes=size_bytes))

    return results, errors
