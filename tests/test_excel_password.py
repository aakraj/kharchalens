from __future__ import annotations

import pandas as pd
import pytest

from kharchalens.parser import HdfcParser, SbiParser
from kharchalens.parser.hdfc_base import (
    ExcelIncorrectPassword,
    ExcelPasswordRequired,
    _is_encrypted_container,
    read_excel_like,
)

FIXTURE = "tests/fixtures/xlsx_encrypted.xlsx"
PASSWORD = "Password1234_"


def test_plain_xlsx_reads_without_password(tmp_path) -> None:
    path = tmp_path / "plain.xlsx"
    pd.DataFrame({"Date": ["01/01/2024"], "Narration": ["NABZ"]}).to_excel(
        path, index=False, header=False
    )
    frame = read_excel_like(str(path))
    assert frame.shape == (1, 2)


def test_plain_xlsx_reads_when_password_ignored(tmp_path) -> None:
    path = tmp_path / "plain.xlsx"
    pd.DataFrame({"Date": ["01/01/2024"], "Narration": ["NABZ"]}).to_excel(
        path, index=False, header=False
    )
    frame = read_excel_like(str(path), password="ignored")
    assert frame.shape == (1, 2)


def test_encrypted_detected() -> None:
    assert _is_encrypted_container(FIXTURE) is True


def test_encrypted_requires_password() -> None:
    with pytest.raises(ExcelPasswordRequired):
        read_excel_like(FIXTURE)


def test_encrypted_wrong_password() -> None:
    with pytest.raises(ExcelIncorrectPassword):
        read_excel_like(FIXTURE, password="wrong")


def test_encrypted_correct_password() -> None:
    frame = read_excel_like(FIXTURE, password=PASSWORD)
    assert not frame.empty


def test_parser_raises_password_required() -> None:
    with pytest.raises(ExcelPasswordRequired):
        HdfcParser().parse(FIXTURE)


def test_sbi_parser_raises_password_required() -> None:
    with pytest.raises(ExcelPasswordRequired):
        SbiParser().parse(FIXTURE)