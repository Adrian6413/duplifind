import pytest
from PIL import Image

from duplifind.scanner import scan_directory


def _save_dummy_image(path, color=(255, 0, 0)):
    img = Image.new("RGB", (32, 32), color=color)
    img.save(path)


def test_finds_images_recursively(tmp_path):
    _save_dummy_image(tmp_path / "top.png")
    nested = tmp_path / "nested" / "deeper"
    nested.mkdir(parents=True)
    _save_dummy_image(nested / "inner.jpg", color=(0, 255, 0))

    results, errors = scan_directory(tmp_path)

    assert errors == []
    found_names = {r.path.name for r in results}
    assert found_names == {"top.png", "inner.jpg"}


def test_ignores_non_image_files(tmp_path):
    _save_dummy_image(tmp_path / "photo.png")
    (tmp_path / "notes.txt").write_text("to nie jest zdjecie", encoding="utf-8")

    results, errors = scan_directory(tmp_path)

    assert len(results) == 1
    assert errors == []


def test_broken_image_is_reported_not_raised(tmp_path):
    _save_dummy_image(tmp_path / "good.png")
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"to nie jest prawdziwy jpeg")

    results, errors = scan_directory(tmp_path)

    assert len(results) == 1
    assert len(errors) == 1
    assert errors[0].path == broken


def test_raises_for_missing_directory(tmp_path):
    missing = tmp_path / "nie_istnieje"

    with pytest.raises(NotADirectoryError):
        scan_directory(missing)


def test_scanned_image_has_size_in_bytes(tmp_path):
    path = tmp_path / "photo.png"
    _save_dummy_image(path)

    results, _errors = scan_directory(tmp_path)

    assert results[0].size_bytes == path.stat().st_size
