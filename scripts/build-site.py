#!/usr/bin/env python3
"""Check the static website and assemble the GitHub Pages artifact. No dependencies."""

import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT
OUTPUT = ROOT / ".build" / "site"


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = set()
        self.refs = []
        self.errors = []
        self.h1s = 0
        self.in_schema = False
        self.schema = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identifier = attrs.get("id")
        if identifier:
            if identifier in self.ids:
                self.errors.append(f"duplicate id: {identifier}")
            self.ids.add(identifier)
        if tag == "h1":
            self.h1s += 1
        if tag == "img" and "alt" not in attrs:
            self.errors.append("image is missing an alt attribute")
        for attr in ("href", "src", "aria-controls"):
            if attrs.get(attr):
                value = "#" + attrs[attr] if attr == "aria-controls" else attrs[attr]
                self.refs.append(value)
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_schema = True
            self.schema = ""

    def handle_data(self, data):
        if self.in_schema:
            self.schema += data

    def handle_endtag(self, tag):
        if tag == "script" and self.in_schema:
            try:
                json.loads(self.schema)
            except ValueError as error:
                self.errors.append(f"invalid structured data: {error}")
            self.in_schema = False


def check():
    pages = {}
    errors = []
    for path in sorted(list(SOURCE.glob("*.html")) + list((SOURCE / "en").glob("*.html"))):
        page = Page(path)
        page.feed(path.read_text(encoding="utf-8"))
        page.close()
        if page.h1s != 1:
            page.errors.append(f"expected one h1, found {page.h1s}")
        pages[path.resolve()] = page
        errors.extend(f"{path.relative_to(ROOT)}: {error}" for error in page.errors)

    for path, page in pages.items():
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            target = (SOURCE / unquote(url.path).lstrip("/") if url.path.startswith("/")
                      else path.parent / unquote(url.path)) if url.path else path
            target = target.resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file() or SOURCE.resolve() not in target.parents:
                errors.append(f"{path.relative_to(ROOT)}: missing local resource {ref}")
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                errors.append(f"{path.relative_to(ROOT)}: missing anchor {ref}")

    # CSS assets and sitemap URLs must resolve to the same deployable source tree.
    for css in (SOURCE / "assets").glob("*.css"):
        for ref in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", css.read_text(encoding="utf-8")):
            if not urlsplit(ref).scheme and not ref.startswith("#"):
                target = SOURCE / ref.lstrip("/") if ref.startswith("/") else css.parent / ref
                if not target.is_file():
                    errors.append(f"{css.relative_to(ROOT)}: missing asset {ref}")
    sitemap = ElementTree.parse(SOURCE / "sitemap.xml")
    for loc in sitemap.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        target = SOURCE / urlsplit(loc.text).path.lstrip("/")
        if target.is_dir():
            target /= "index.html"
        if not target.is_file():
            errors.append(f"sitemap.xml: missing page {loc.text}")
    if errors:
        sys.exit("Website validation failed:\n" + "\n".join(errors))
    print(f"Validated {len(pages)} HTML pages, local links, assets and structured data.")


def build():
    check()
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    # Publish only public website files, excluding project/release documentation.
    for name in ("index.html", "privacy.html", "404.html", "robots.txt", "sitemap.xml", "CNAME", ".nojekyll"):
        shutil.copy2(SOURCE / name, OUTPUT / name)
    shutil.copytree(SOURCE / "assets", OUTPUT / "assets")
    (OUTPUT / "en").mkdir()
    for path in (SOURCE / "en").glob("*.html"):
        shutil.copy2(path, OUTPUT / "en" / path.name)
    print(f"GitHub Pages artifact: {OUTPUT}")


if __name__ == "__main__":
    build()
