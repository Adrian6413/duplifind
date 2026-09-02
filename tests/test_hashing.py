"""Testy dhash/hamming.

Obrazy testowe generujemy programowo (PIL.ImageDraw), zamiast trzymać
pliki binarne w repo — dzięki temu testy są deterministyczne, szybkie
i nie zaśmiecają historii gita binarkami.
"""

from PIL import Image, ImageDraw

from duplifind.hashing import dhash, hamming


def _gradient_with_circle(size: tuple[int, int], seed: int) -> Image.Image:
    """Tworzy obraz z gradientem tła i kołem — na tyle złożony, żeby dhash
    miał co "zobaczyć", a nie same jednolite piksele."""
    width, height = size
    img = Image.new("RGB", size)
    pixels = img.load()
    for x in range(width):
        for y in range(height):
            pixels[x, y] = ((x * 3 + seed) % 256, (y * 3) % 256, (seed * 7) % 256)

    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2
    r = min(width, height) // 4
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255))
    return img


def test_identical_image_has_zero_distance(tmp_path):
    img = _gradient_with_circle((200, 200), seed=10)
    path_a = tmp_path / "a.png"
    path_b = tmp_path / "b.png"
    img.save(path_a)
    img.save(path_b)

    assert hamming(dhash(path_a), dhash(path_b)) == 0


def test_resized_image_is_close_duplicate(tmp_path):
    original = _gradient_with_circle((400, 400), seed=42)
    resized = original.resize((120, 120), Image.Resampling.LANCZOS)

    path_original = tmp_path / "original.png"
    path_resized = tmp_path / "resized.png"
    original.save(path_original)
    resized.save(path_resized)

    distance = hamming(dhash(path_original), dhash(path_resized))
    # Progu 5 używamy też jako domyślnej wartości --threshold w CLI.
    assert distance <= 5


def test_recompressed_jpeg_is_close_duplicate(tmp_path):
    original = _gradient_with_circle((300, 300), seed=77)

    path_high_quality = tmp_path / "high.jpg"
    path_low_quality = tmp_path / "low.jpg"
    original.save(path_high_quality, quality=95)
    original.save(path_low_quality, quality=20)

    distance = hamming(dhash(path_high_quality), dhash(path_low_quality))
    assert distance <= 5


def test_different_images_have_large_distance(tmp_path):
    img_a = _gradient_with_circle((200, 200), seed=1)

    img_b = Image.new("RGB", (200, 200), color=(0, 0, 0))
    draw = ImageDraw.Draw(img_b)
    draw.rectangle((0, 0, 100, 200), fill=(255, 255, 255))
    draw.rectangle((100, 0, 150, 100), fill=(128, 0, 0))

    path_a = tmp_path / "a.png"
    path_b = tmp_path / "b.png"
    img_a.save(path_a)
    img_b.save(path_b)

    distance = hamming(dhash(path_a), dhash(path_b))
    assert distance > 5


def test_dhash_is_64_bits():
    img = _gradient_with_circle((64, 64), seed=5)
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "img.png"
        img.save(path)
        value = dhash(path)

    assert 0 <= value < 2**64


def test_hamming_is_symmetric():
    assert hamming(0b1010, 0b0101) == hamming(0b0101, 0b1010)


def test_hamming_zero_for_same_value():
    assert hamming(123456789, 123456789) == 0
