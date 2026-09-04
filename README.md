# duplifind

[![CI](https://github.com/Adrian6413/duplifind/actions/workflows/ci.yml/badge.svg)](https://github.com/Adrian6413/duplifind/actions/workflows/ci.yml)

CLI, które znajduje duplikaty zdjęć — nie tylko identyczne pliki, ale też
przeskalowane, przekompresowane i lekko przycięte wersje tego samego obrazu.

```
$ duplifind ~/Zdjecia --delete-dry-run
Znaleziono 2 grup(y) duplikatów. Do odzyskania: 14.3 MB

Grupa 1 (3 plików, marnowane: 9.8 MB):
  - ~/Zdjecia/wakacje_2023/plaza.jpg (10.2 MB) [NAJWIĘKSZY - zachować]
  - ~/Zdjecia/eksport_whatsapp/plaza.jpg (6.1 MB)  <- zostałby usunięty (--delete-dry-run)
  - ~/Zdjecia/backup_stary/plaza_small.jpg (3.7 MB)  <- zostałby usunięty (--delete-dry-run)
```

## Problem

Mam po latach folder ze zdjęciami, w którym to samo zdjęcie siedzi kilka
razy: oryginał, kopia wyeksportowana przez WhatsAppa w gorszej jakości,
wersja z jakiegoś backupu po przenoszeniu telefonu. Bajty tych plików są
różne, ale dla oka to to samo zdjęcie - więc zwykłe porównanie sum
kontrolnych (MD5) nic tu nie wykryje, trzeba porównywać jak zdjęcie
*wygląda*, a nie jak jest zapisane na dysku.

## Instalacja

Wymaga Pythona 3.11+.

```bash
git clone <adres-repo>
cd duplifind
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Użycie

```bash
duplifind /sciezka/do/zdjec
duplifind /sciezka/do/zdjec --threshold 8     # luźniejsze dopasowanie
duplifind /sciezka/do/zdjec --json            # wynik jako JSON
duplifind /sciezka/do/zdjec --delete-dry-run  # pokaż, co zostałoby usunięte
```

`duplifind` nigdy nic nie usuwa samodzielnie — `--delete-dry-run` tylko
pokazuje, które pliki program uznałby za zbędne kopie. Decyzję i faktyczne
usuwanie zawsze podejmuje użytkownik.

## Jak to działa (w skrócie)

Dla każdego zdjęcia liczony jest **dHash** (difference hash) - odcisk
palca opisujący, jak zdjęcie wygląda, a nie jak jest zapisane w bajtach:

1. Zdjęcie ląduje w skali szarości, mocno pomniejszone do siatki 9×8 pikseli.
2. W każdym z 8 wierszy porównywane są sąsiednie piksele: jaśniejszy po
   lewej daje bit `1`, w przeciwnym razie `0`. W sumie 64 bity.
3. Dwa zdjęcia są duplikatami, gdy różnica między ich hashami (odległość
   Hamminga) jest mała - domyślny próg to `5` z 64 bitów.
4. Podobne zdjęcia łączone są w grupy (A~B, B~C -> A, B, C razem), nawet
   gdy A i C same w sobie przekraczają próg.

Dlaczego akurat tak, a nie np. porównanie pikseli piksel-po-pikselu -
opisałem sobie osobno, żeby móc to wytłumaczyć na głos.

## Ograniczenia

- **Złożoność O(n²).** Program porównuje każde zdjęcie z każdym. Dla
  kilku tysięcy zdjęć jest to błyskawiczne, ale dla setek tysięcy plików
  potrzebny byłby indeks przybliżonego wyszukiwania (np. BK-tree) zamiast
  pełnego porównania parami.
- **Jednolite kolory się mylą.** dHash patrzy tylko na *różnice* jasności
  między sąsiednimi pikselami. Dwa całkowicie jednokolorowe obrazy (np. czysta
  czerwień i czysta zieleń) dostają identyczny hash, mimo że wyglądają
  zupełnie inaczej — bo różnica jasności między sąsiadami wynosi zero
  w obu przypadkach. W praktyce prawdziwe zdjęcia rzadko są jednolite,
  więc to rzadko problem, ale warto o tym wiedzieć.
- **Silne przycięcie myli hash.** dHash jest odporny na przeskalowanie
  i rekompresję, ale nie na przycięcie kadru — usunięcie sporego fragmentu
  zdjęcia przesuwa siatkę porównań i może dać zupełnie inny hash.
- **Obrócone zdjęcia to inne hashe.** Obrót o 90°/180° zmienia hash,
  bo dHash porównuje piksele w konkretnym kierunku (lewo-prawo). Nie ma tu
  wykrywania obrotów.

## Rozwój

```bash
pip install -e . pytest ruff
pytest        # testy
ruff check .  # lint
```
