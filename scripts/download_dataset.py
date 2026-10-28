"""Descarga y descomprime MovieLens ml-latest-small en data/."""

import io
import zipfile
from pathlib import Path

import httpx

URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    target = DATA_DIR / "ml-latest-small"
    if (target / "ratings.csv").exists():
        print(f"Dataset ya existe en {target}")
        return

    print(f"Descargando {URL} ...")
    resp = httpx.get(URL, follow_redirects=True, timeout=60)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(DATA_DIR)
    print(f"Listo: {target}")


if __name__ == "__main__":
    main()
