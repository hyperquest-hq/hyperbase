from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import mwparserfromhell
import requests
from mwparserfromhell.wikicode import Wikicode

from hyperbase.readers.reader import Reader, register_reader


def _load_discard_sections() -> dict[str, set]:
    """Load language-specific section names to discard from the data file.

    Returns:
        dict: A dictionary mapping language codes (ISO-639-1) to sets of section names
              to ignore.
    """
    discard_sections = {}
    current_lang = None

    data_file = (
        Path(__file__).parent.parent / "data" / "wikipedia" / "discard_sections.txt"
    )

    with open(data_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Check for language header
            if line.startswith("+ LANGUAGE (ISO-639-1):"):
                current_lang = line.split(":")[-1].strip()
                discard_sections[current_lang] = set()
            elif current_lang:
                # Add section name to current language
                discard_sections[current_lang].add(line)

    return discard_sections


# Load discard sections once at module level
_DISCARD_SECTIONS = _load_discard_sections()


def _url2title_and_lang(url: str) -> tuple[str, str]:
    p = urlparse(url)

    netloc = p.netloc.split(".")
    if len(netloc) < 3 or "wikipedia" not in netloc:
        raise RuntimeError(f"{url} is not a valid wikipedia url.")
    lang = netloc[0]

    path = [part for part in p.path.split("/") if part != ""]
    if len(path) != 2 or path[0] != "wiki":
        raise RuntimeError(f"{url} is not a valid wikipedia url.")
    title = path[1]

    return title, lang


def read_wikipedia(url: str) -> Wikicode:
    title, lang = _url2title_and_lang(url)
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "rvlimit": 1,
        "titles": title,
        "format": "json",
        "formatversion": "2",
    }
    headers = {"User-Agent": "hyperquest/1.0"}
    api_url = f"https://{lang}.wikipedia.org/w/api.php"

    try:
        req = requests.get(api_url, headers=headers, params=params, timeout=30)
        req.raise_for_status()
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f"Request to Wikipedia API timed out after 30 seconds. URL: {url}"
        ) from e
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Failed to connect to Wikipedia API at {api_url}. "
            f"Please check your internet connection."
        ) from e
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"Wikipedia API returned HTTP error {e.response.status_code}: "
            f"{e.response.reason}. URL: {url}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Network error while fetching Wikipedia page: {e!s}. URL: {url}"
        ) from e

    try:
        res = req.json()
    except ValueError as e:
        raise RuntimeError(
            f"Failed to parse Wikipedia API response as JSON: {e!s}. URL: {url}"
        ) from e

    try:
        pages = res.get("query", {}).get("pages", [])
        if not pages:
            raise RuntimeError(f"No pages found in Wikipedia API response. URL: {url}")

        page = pages[0]
        if "missing" in page:
            raise RuntimeError(f"Wikipedia page does not exist: {title}. URL: {url}")

        revisions = page.get("revisions", [])
        if not revisions:
            raise RuntimeError(
                f"No revisions found for Wikipedia page: {title}. URL: {url}"
            )

        revision = revisions[0]
        slots = revision.get("slots", {})
        if "main" not in slots:
            raise RuntimeError(
                f"No main content slot found in Wikipedia page: {title}. URL: {url}"
            )

        text = slots["main"].get("content")
        if not text:
            raise RuntimeError(
                f"No content found in Wikipedia page: {title}. URL: {url}"
            )

    except (KeyError, IndexError) as e:
        raise RuntimeError(
            f"Unexpected Wikipedia API response : {e!s}. URL: {url}. Response: {res}"
        ) from e

    return mwparserfromhell.parse(text)


class WikicodeTextExtractor:
    def __init__(self) -> None:
        """Initialize the text extractor."""
        self.cur_section = []
        self.sections = {"": self.cur_section}
        self.section_metadata = {}  # Track ref/link counts per section

    def _extract(self, wikicode: Wikicode, current_section_title: str = "") -> None:
        """Extract text and track reference/link density for each section.

        Args:
            wikicode: The wikicode to parse.
            current_section_title: The title of the current section being processed.
        """
        for node in wikicode.nodes:
            if isinstance(node, mwparserfromhell.nodes.heading.Heading):
                self.cur_section = []
                self._extract(node.title, current_section_title)
                title = "".join(self.cur_section).strip()
                self.cur_section = []
                self.sections[title] = self.cur_section
                # Initialize metadata for new section
                self.section_metadata[title] = {
                    "ref_count": 0,
                    "external_link_count": 0,
                }
                # Continue extracting with the new section title
                current_section_title = title
            elif isinstance(node, mwparserfromhell.nodes.text.Text):
                self.cur_section.append(str(node))
            elif isinstance(node, mwparserfromhell.nodes.tag.Tag):
                tag_name = str(node.tag).lower()
                if tag_name == "ref":
                    # Count <ref> tags but don't include their content
                    if current_section_title in self.section_metadata:
                        self.section_metadata[current_section_title]["ref_count"] += (
                            len(str(node))
                        )
                elif tag_name != "div":
                    _cur_section = self.cur_section
                    self.cur_section = []
                    self._extract(node.contents, current_section_title)
                    text = "".join(self.cur_section).strip()
                    self.cur_section = _cur_section
                    self.cur_section.append(text)
            elif isinstance(node, mwparserfromhell.nodes.wikilink.Wikilink):
                if "File:" not in str(node.title):
                    _wikicode = node.title if node.text is None else node.text
                    _cur_section = self.cur_section
                    self.cur_section = []
                    self._extract(_wikicode, current_section_title)
                    text = "".join(self.cur_section).strip()
                    self.cur_section = _cur_section
                    self.cur_section.append(text)
            elif isinstance(node, mwparserfromhell.nodes.external_link.ExternalLink):
                # Count external links
                if current_section_title in self.section_metadata:
                    self.section_metadata[current_section_title][
                        "external_link_count"
                    ] += len(str(node))
                # Include link text if available
                if node.title:
                    _cur_section = self.cur_section
                    self.cur_section = []
                    self._extract(node.title, current_section_title)
                    text = "".join(self.cur_section).strip()
                    self.cur_section = _cur_section
                    self.cur_section.append(text)
            elif isinstance(node, mwparserfromhell.nodes.template.Template):
                # Check for reference/citation templates
                template_name = str(node.name).strip().lower()
                if (
                    any(
                        keyword in template_name
                        for keyword in [
                            "reflist",
                            "references",
                            "notes",
                            "cite",
                            "citation",
                        ]
                    )
                    and current_section_title in self.section_metadata
                ):
                    self.section_metadata[current_section_title]["ref_count"] += len(
                        str(node)
                    )

    def extract(self, wikicode: Wikicode, lang: str = "en") -> dict[str, str]:
        """Extract text from wikicode, filtering out language-specific sections.

        Args:
            wikicode: The parsed wikicode to extract text from.
            lang: The language code (ISO-639-1) for language-specific section filtering.
                  Defaults to "en" (English).

        Returns:
            dict: A dictionary mapping section titles to extracted text content.
        """
        # Initialize metadata for the root section
        self.section_metadata[""] = {"ref_count": 0, "external_link_count": 0}
        self._extract(wikicode)

        # Get language-specific discard sections, fallback to English if not found
        discard_set = _DISCARD_SECTIONS.get(lang, _DISCARD_SECTIONS.get("en", set()))

        filtered_sections = {}
        for section, texts in self.sections.items():
            text_content = "".join(texts).strip()

            # Skip if section name is in discard list
            if section in discard_set:
                continue

            filtered_sections[section] = text_content

        return filtered_sections


class WikipediaReader(Reader):
    more_general = ("url",)

    def __init__(self) -> None:
        self._blocks: list[str] | None = None

    @staticmethod
    def accepts(source: str) -> bool:
        parsed = urlparse(source)
        if parsed.scheme not in ("http", "https"):
            return False
        return bool(re.match(r"^([a-z\-]+\.)?wikipedia\.org$", parsed.netloc.lower()))

    def _fetch(self, source: str) -> list[str]:
        if self._blocks is None:
            _, lang = _url2title_and_lang(source)
            wikicode = read_wikipedia(source)
            extractor = WikicodeTextExtractor()
            sections = extractor.extract(wikicode, lang=lang)
            self._blocks = [t for t in sections.values() if t]
        return self._blocks

    def block_count(self, source: str) -> int | None:
        return len(self._fetch(source))

    def source_info(self, source: str) -> dict[str, Any]:
        title, _ = _url2title_and_lang(source)
        return {
            "source_type": "wikipedia",
            "source": source,
            "title": unquote(title).replace("_", " "),
        }

    def read(self, source: str) -> Iterator[str]:
        yield from self._fetch(source)


register_reader("wikipedia", WikipediaReader)
