from pathlib import Path

from duplifind.grouping import group_duplicates
from duplifind.scanner import ScannedImage


def _img(name: str, hash_value: int, size: int) -> ScannedImage:
    return ScannedImage(path=Path(name), hash_value=hash_value, size_bytes=size)


def test_similar_images_form_one_group():
    images = [
        _img("a.jpg", 0b0000, size=100),
        _img("b.jpg", 0b0001, size=200),
        _img("c.jpg", 0b1111_1111_1111, size=50),  # daleko od reszty
    ]

    groups = group_duplicates(images, threshold=1)

    assert len(groups) == 1
    names = {img.path.name for img in groups[0].images}
    assert names == {"a.jpg", "b.jpg"}


def test_lone_image_is_not_a_group():
    images = [_img("solo.jpg", 0, size=100)]

    groups = group_duplicates(images, threshold=5)

    assert groups == []


def test_transitive_chain_merges_into_single_group():
    # a~b (distance 1), b~c (distance 1), ale a~c (distance 2) przekracza
    # próg 1 -- mimo to a, b, c powinny trafić do jednej grupy przez union-find.
    images = [
        _img("a.jpg", 0b00, size=10),
        _img("b.jpg", 0b01, size=10),
        _img("c.jpg", 0b11, size=10),
    ]

    groups = group_duplicates(images, threshold=1)

    assert len(groups) == 1
    assert len(groups[0].images) == 3


def test_largest_property_picks_biggest_file():
    images = [_img("small.jpg", 0, size=100), _img("big.jpg", 1, size=900)]
    group = group_duplicates(images, threshold=5)[0]

    assert group.largest.path.name == "big.jpg"


def test_wasted_bytes_excludes_largest():
    images = [_img("small.jpg", 0, size=100), _img("big.jpg", 1, size=900)]
    group = group_duplicates(images, threshold=5)[0]

    assert group.wasted_bytes == 100


def test_no_groups_when_all_images_differ():
    images = [_img("a.jpg", 0b0000, size=10), _img("b.jpg", 0b1111, size=10)]

    groups = group_duplicates(images, threshold=1)

    assert groups == []
