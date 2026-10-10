"""Checks on the text files in content/."""

from pathlib import Path

import yaml

from components import layout

ROOT = Path(__file__).parent.parent
PAGES = yaml.safe_load((ROOT / "content" / "pages.yaml").read_text())


def test_every_page_has_a_title_and_intro():
    for page_id, _, _ in layout.PAGES:
        assert PAGES[page_id]["title"] and PAGES[page_id]["intro"], page_id


def test_page_text_avoids_the_two_reworded_phrases():
    text = yaml.safe_dump(PAGES).lower()
    assert "mixed state" not in text
    assert "experiencing a mix" not in text


def test_no_content_file_names_newfos():
    for path in (ROOT / "content").rglob("*"):
        if path.is_file():
            assert "newfos" not in path.read_text().lower(), path.name


def test_every_page_file_exists():
    for _, file, _ in layout.PAGES:
        assert (ROOT / file).is_file(), file
