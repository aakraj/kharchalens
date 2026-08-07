"""Diagnose encrypted-Excel decryption on a real local SBI file.

Usage:
    uv run python scripts/debug_excel.py <path-to-xlsx> [password]

The password is only used in memory here and is never written anywhere.
No cell contents are printed.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: uv run python scripts/debug_excel.py <path> [password]")
        return

    path = Path(sys.argv[1])
    password = sys.argv[2] if len(sys.argv) > 2 else None

    import io

    import msoffcrypto

    print(f"file: {path.name}  ({path.stat().st_size} bytes, magic={path.read_bytes()[:8]!r})")

    with open(path, "rb") as handle:
        office = msoffcrypto.OfficeFile(handle)
        print(f"format: {office.format}")
        print(f"type:   {office.type}")
        print(f"is_encrypted: {office.is_encrypted()}")
        if not password:
            print("(no password supplied to test against)")
            return

        # Mirror the app: decrypt without verification, then check bytes parse.
        content = io.BytesIO()
        try:
            office.load_key(password=password)
            office.decrypt(content)
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            print(f"load_key/decrypt: {type(exc).__module__}.{type(exc).__name__}: {exc}")
            return

        content.seek(0)
        head = content.read(8)
        try:
            import pandas as pd

            content.seek(0)
            frame = pd.read_excel(content, engine="openpyxl", header=None, dtype=object)
            print(f"OK: decrypted #{content.getbuffer().nbytes} bytes -> pandas read {frame.shape}")
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            print(f"decrypted but not a valid workbook: {type(exc).__name__}: {exc}")
            print(f"  (body magic={head!r} — wrong key or non-Excel payload)")


if __name__ == "__main__":
    main()