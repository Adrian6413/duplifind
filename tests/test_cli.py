import json

from PIL import Image

from duplifind.cli import format_size, main


def _save_image(path, color, size=(64, 64)):
    Image.new("RGB", size, color=color).save(path)


def _save_pattern_image(path, seed, size=(64, 64)):
    # Jednolite kolory dają ten sam dhash niezależnie od koloru (dHash
    # patrzy na różnice jasności między sąsiednimi pikselami, a w płaskim
    # kolorze wszystkie są równe) — do testu "różne zdjęcia" potrzebny jest
    # obraz z jakąś strukturą, inaczej test fałszywie wykryłby duplikat.
    img = Image.new("RGB", size)
    pixels = img.load()
    width, height = size
    for x in range(width):
        for y in range(height):
            pixels[x, y] = ((x * 5 + seed) % 256, (y * 5 + seed) % 256, seed % 256)
    img.save(path)


def test_format_size_bytes():
    assert format_size(500) == "500 B"


def test_format_size_kilobytes():
    assert format_size(2048) == "2.0 KB"


def test_format_size_megabytes():
    assert format_size(5 * 1024 * 1024) == "5.0 MB"


def test_main_reports_no_duplicates_for_distinct_images(tmp_path, capsys):
    _save_pattern_image(tmp_path / "one.png", seed=10)
    _save_pattern_image(tmp_path / "two.png", seed=200)

    exit_code = main([str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Nie znaleziono duplikatów" in captured.out


def test_main_finds_identical_copies(tmp_path, capsys):
    _save_image(tmp_path / "original.png", (10, 20, 30))
    _save_image(tmp_path / "copy.png", (10, 20, 30))

    exit_code = main([str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Znaleziono 1 grup" in captured.out
    assert "NAJWIĘKSZY" in captured.out


def test_main_json_output_is_valid_json(tmp_path, capsys):
    _save_image(tmp_path / "original.png", (10, 20, 30))
    _save_image(tmp_path / "copy.png", (10, 20, 30))

    exit_code = main([str(tmp_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    data = json.loads(captured.out)
    assert len(data) == 1
    assert len(data[0]["images"]) == 2


def test_main_delete_dry_run_marks_extra_copies(tmp_path, capsys):
    _save_image(tmp_path / "original.png", (10, 20, 30))
    _save_image(tmp_path / "copy.png", (10, 20, 30))

    main([str(tmp_path), "--delete-dry-run"])

    captured = capsys.readouterr()
    assert "zostałby usunięty" in captured.out


def test_main_returns_error_for_missing_directory(tmp_path, capsys):
    missing = tmp_path / "brak"

    exit_code = main([str(missing)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Błąd" in captured.err


def test_main_reports_broken_files_on_stderr(tmp_path, capsys):
    _save_image(tmp_path / "good.png", (1, 2, 3))
    (tmp_path / "broken.jpg").write_bytes(b"not a real jpeg")

    main([str(tmp_path)])

    captured = capsys.readouterr()
    assert "broken.jpg" in captured.err
