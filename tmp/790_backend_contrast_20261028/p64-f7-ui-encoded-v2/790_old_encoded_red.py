"""Reproduce the old candidate's uncounted outer-base64 UI cost, without execution."""

import base64
from pathlib import Path

import pytest

OLD=Path(__file__).resolve().parent.parent/'p64-f7-window1600'


@pytest.mark.parametrize('index',[1,2,3,4])
def test_original_complete_outer_encoded_plus_description_fits_UI(index):
    raw=(OLD/f'install-part{index:02}.PUBLIC.txt').read_bytes()
    assert len(base64.b64encode(raw))+300<18000
