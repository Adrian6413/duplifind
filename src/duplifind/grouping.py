"""Grupowanie zeskanowanych zdjęć w klastry duplikatów.

Podobieństwo (odległość Hamminga <= próg) nie jest przechodnie: A może
być podobne do B, B do C, ale A i C już niekoniecznie. Mimo to chcemy,
żeby taki "łańcuch" trafił do jednej grupy, więc łączenie robimy
strukturą union-find zamiast osobno pokazywać każdą parę.
"""

from dataclasses import dataclass

from duplifind.hashing import hamming
from duplifind.scanner import ScannedImage


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    """Grupa co najmniej dwóch zdjęć uznanych za duplikaty."""

    images: list[ScannedImage]

    @property
    def largest(self) -> ScannedImage:
        """Plik zajmujący najwięcej miejsca - zwykle ten wart zachowania."""
        return max(self.images, key=lambda img: img.size_bytes)

    @property
    def wasted_bytes(self) -> int:
        """Ile miejsca zajmują kopie poza największą."""
        return sum(img.size_bytes for img in self.images) - self.largest.size_bytes


class _UnionFind:
    """Zbiory rozłączne z kompresją ścieżek (żeby find() nie wolniało)."""

    def __init__(self, n: int) -> None:
        self._parent = list(range(n))

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]  # kompresja ścieżki
            x = self._parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = root_b


def group_duplicates(images: list[ScannedImage], threshold: int) -> list[DuplicateGroup]:
    """Dzieli zeskanowane zdjęcia na grupy duplikatów.

    Porównuje każdą parę zdjęć (O(n^2) - wystarczające dla domowej
    biblioteki zdjęć, patrz "Ograniczenia" w README dla większych zbiorów).
    Zdjęcia bez pary są pomijane w wyniku.
    """
    uf = _UnionFind(len(images))

    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            if hamming(images[i].hash_value, images[j].hash_value) <= threshold:
                uf.union(i, j)

    clusters: dict[int, list[ScannedImage]] = {}
    for index, image in enumerate(images):
        root = uf.find(index)
        clusters.setdefault(root, []).append(image)

    return [
        DuplicateGroup(images=members)
        for members in clusters.values()
        if len(members) >= 2
    ]
