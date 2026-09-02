"""Liczenie dHash obrazów i porównywanie ich odległości Hamminga.

dHash opisuje wygląd obrazu, a nie jego bajty, więc dwa zdjęcia różniące
się kompresją albo rozdzielczością mogą dalej dostać ten sam hash.
Zwykły MD5/SHA-1 tak nie działa - zmiana jednego piksela zmienia go
całkowicie, więc do porównywania "podobnych" zdjęć się nie nadaje.
"""

from pathlib import Path

from PIL import Image

# 9 kolumn x 8 wierszy -> 8 porównań w wierszu -> 64 bity hasha.
_HASH_WIDTH = 9
_HASH_HEIGHT = 8


def dhash(path: str | Path) -> int:
    """Liczy 64-bitowy difference hash obrazu.

    Obraz jest zamieniany na skalę szarości i mocno pomniejszany (9x8),
    a potem dla każdego wiersza porównujemy sąsiednie piksele - jaśniejszy
    po lewej daje bit 1, w przeciwnym razie 0.
    """
    with Image.open(path) as img:
        small = img.convert("L").resize(
            (_HASH_WIDTH, _HASH_HEIGHT), Image.Resampling.LANCZOS
        )
        pixels = list(small.get_flattened_data())

    bits = 0
    for row in range(_HASH_HEIGHT):
        row_start = row * _HASH_WIDTH
        for col in range(_HASH_WIDTH - 1):
            left = pixels[row_start + col]
            right = pixels[row_start + col + 1]
            bits = (bits << 1) | int(left > right)

    return bits


def hamming(a: int, b: int) -> int:
    """Liczba różniących się bitów między dwoma hashami. Im mniej, tym podobniejsze."""
    return (a ^ b).bit_count()
