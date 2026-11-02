#!/usr/bin/env python3
import json
import hashlib
import re
import shutil
import sys
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".build" / "site"
ORIGIN = "https://octavam.com"
STORE_HOME = "https://apps.apple.com/"
LANGUAGES = ("pl", "en", "de", "fr", "uk", "ru")


def html_files(directory):
    return sorted(list(directory.glob("*.html")) + [path for language in LANGUAGES[1:]
                  for path in (directory / language).glob("*.html")])


def page_url(path, directory):
    relative = path.relative_to(directory).as_posix()
    return ORIGIN + "/" + (relative[:-10] if relative.endswith("index.html") else relative)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.refs = []
        self.errors = []
        self.h1s = 0
        self.language = ""
        self.title_count = 0
        self.title = ""
        self.in_title = False
        self.meta = {}
        self.links = []
        self.store_links = []
        self.schemas = []
        self.in_schema = False
        self.schema_text = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identifier = attrs.get("id")
        if identifier:
            if identifier in self.ids:
                self.errors.append(f"duplicate id: {identifier}")
            self.ids.add(identifier)
        if tag == "html":
            self.language = attrs.get("lang", "")
        if tag == "title":
            self.title_count += 1
            self.in_title = True
        if tag == "h1":
            self.h1s += 1
        if tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.meta.setdefault(key, []).append(attrs.get("content", ""))
        if tag == "link":
            self.links.append(attrs)
        if tag == "img" and "alt" not in attrs:
            self.errors.append("image is missing an alt attribute")
        if tag == "a" and "data-app-store" in attrs:
            self.store_links.append(attrs.get("href", ""))
        for attr in ("href", "src", "aria-controls"):
            if attrs.get(attr):
                self.refs.append("#" + attrs[attr] if attr == "aria-controls" else attrs[attr])
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_schema = True
            self.schema_text = ""

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_schema:
            self.schema_text += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_schema:
            try:
                self.schemas.append(json.loads(self.schema_text))
            except ValueError as error:
                self.errors.append(f"invalid structured data: {error}")
            self.in_schema = False

    def metadata(self, name):
        values = self.meta.get(name, [])
        return values[0] if len(values) == 1 else ""

    def alternates(self):
        return {link.get("hreflang"): link.get("href") for link in self.links
                if link.get("rel") == "alternate"}


def language_urls(privacy=False):
    urls = {language: ORIGIN + ("/" if language == "pl" else f"/{language}/")
            + ("privacy.html" if privacy else "") for language in LANGUAGES}
    return dict(urls, **{"x-default": urls["pl"]})


def check(directory, store_url=None, app_id=None):
    pages = {}
    errors = []
    titles = set()
    descriptions = set()
    for path in html_files(directory):
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        page.close()
        expected_url = page_url(path, directory)
        notfound = path.name == "404.html"
        is_home = path.name == "index.html"
        if page.h1s != 1:
            page.errors.append(f"expected one h1, found {page.h1s}")
        if page.title_count != 1 or not page.title.strip() or page.title in titles:
            page.errors.append("expected one unique, nonempty title")
        titles.add(page.title)
        description = page.metadata("description")
        if not description or description in descriptions:
            page.errors.append("missing, repeated or duplicate meta description")
        descriptions.add(description)
        expected_language = path.parent.name if path.parent.name in LANGUAGES[1:] else "pl"
        if page.language != expected_language:
            page.errors.append(f"expected HTML language {expected_language}")
        for name in ("og:type", "og:site_name", "og:title", "og:description", "og:url",
                     "og:image", "og:image:width", "og:image:height", "og:image:alt",
                     "og:locale", "twitter:card", "twitter:title", "twitter:description",
                     "twitter:image", "twitter:image:alt"):
            if not page.metadata(name):
                page.errors.append(f"missing or duplicate {name}")
        if page.metadata("og:url") != expected_url:
            page.errors.append("Open Graph URL must match the page URL")
        if "noindex" in page.metadata("robots") and not notfound:
            page.errors.append("indexable page has noindex")
        if notfound:
            if "noindex" not in page.metadata("robots"):
                page.errors.append("404 page must have noindex")
        else:
            canonicals = [link.get("href") for link in page.links if link.get("rel") == "canonical"]
            if canonicals != [expected_url]:
                page.errors.append(f"expected self canonical {expected_url}")
            if page.alternates() != language_urls(path.name == "privacy.html"):
                page.errors.append("hreflang must include every translation and Polish x-default")
            nodes = [node for schema in page.schemas for node in schema.get("@graph", [])]
            types = {node.get("@type") for node in nodes}
            required = {"Person", "WebPage", "WebSite"} | ({"SoftwareApplication"} if is_home else set())
            if not required.issubset(types):
                page.errors.append(f"missing structured data: {sorted(required - types)}")
            if store_url is not None:
                expected_banner = f"app-id={app_id}" if app_id else ""
                if page.metadata("apple-itunes-app") != expected_banner:
                    page.errors.append("Smart App Banner does not match site-config.json")
                if is_home:
                    if len(page.store_links) != 5 or any(link != store_url for link in page.store_links):
                        page.errors.append("all five App Store buttons must use the configured URL")
                    app = next((node for node in nodes if node.get("@type") == "SoftwareApplication"), {})
                    if app.get("downloadUrl") != (store_url if app_id else None):
                        page.errors.append("app download metadata must match the published App Store ID")
        pages[path.resolve()] = page
        errors.extend(f"{path.relative_to(directory)}: {error}" for error in page.errors)

    for path, page in pages.items():
        refs = page.refs + [page.metadata("og:image"), page.metadata("twitter:image")]
        for ref in refs:
            url = urlsplit(ref)
            if (url.scheme or url.netloc) and not ref.startswith(ORIGIN + "/"):
                continue
            target = (directory / unquote(url.path).lstrip("/") if url.path.startswith("/")
                      else path.parent / unquote(url.path)) if url.path else path
            target = target.resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file() or directory.resolve() not in target.parents:
                errors.append(f"{path.relative_to(directory)}: missing local resource {ref}")
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                errors.append(f"{path.relative_to(directory)}: missing anchor {ref}")

    for css in (directory / "assets").glob("*.css"):
        for ref in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", css.read_text(encoding="utf-8")):
            if not urlsplit(ref).scheme and not ref.startswith("#"):
                target = directory / ref.lstrip("/") if ref.startswith("/") else css.parent / ref
                if not target.is_file():
                    errors.append(f"{css.relative_to(directory)}: missing asset {ref}")

    sitemap = ElementTree.parse(directory / "sitemap.xml")
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
    expected_urls = {page_url(path, directory.resolve()) for path in pages if path.name != "404.html"}
    sitemap_urls = []
    for entry in sitemap.findall("s:url", ns):
        loc = entry.findtext("s:loc", namespaces=ns)
        sitemap_urls.append(loc)
        alternates = {link.get("hreflang"): link.get("href") for link in entry.findall("x:link", ns)}
        if alternates != language_urls("privacy.html" in (loc or "")):
            errors.append(f"sitemap.xml: incorrect language alternates for {loc}")
    if set(sitemap_urls) != expected_urls or len(sitemap_urls) != len(expected_urls):
        errors.append("sitemap.xml must contain every indexable page exactly once and exclude 404")
    if f"Sitemap: {ORIGIN}/sitemap.xml" not in (directory / "robots.txt").read_text():
        errors.append("robots.txt must reference the canonical sitemap")
    if errors:
        sys.exit("Website validation failed:\n" + "\n".join(errors))
    print(f"Validated {len(pages)} pages: SEO, social metadata, hreflang, sitemap, links and structured data.")


def app_store_settings():
    settings = json.loads((ROOT / "site-config.json").read_text(encoding="utf-8"))
    app_id = settings.get("app_store_id")
    if app_id is not None:
        if not isinstance(app_id, str) or not re.fullmatch(r"[1-9][0-9]{5,}", app_id):
            sys.exit("app_store_id must be null or the numeric Apple ID as a string, not a bundle ID or URL.")
    return app_id, f"https://apps.apple.com/app/id{app_id}" if app_id else STORE_HOME


def render(html, app_id, store_url, show_banner=True):
    banner = f'<meta name="apple-itunes-app" content="app-id={app_id}">' if app_id else ""
    if banner and show_banner:
        html = html.replace("</head>", banner + "\n</head>", 1)

    def store_link(match):
        return re.sub(r'href="[^"]*"', f'href="{escape(store_url, quote=True)}"', match[0])

    html = re.sub(r'<a\b[^>]*\bdata-app-store\b[^>]*>', store_link, html)

    def schema(match):
        data = json.loads(match[2])
        for node in data.get("@graph", []):
            if node.get("@type") == "SoftwareApplication":
                for key in ("downloadUrl", "installUrl"):
                    if app_id:
                        node[key] = store_url
                    else:
                        node.pop(key, None)
        return match[1] + "\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n" + match[3]

    html = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', schema, html, flags=re.S)

    def asset(match):
        digest = hashlib.sha256((ROOT / match[2].lstrip("/")).read_bytes()).hexdigest()[:12]
        return match[1] + match[2] + "?v=" + digest + match[3]

    return re.sub(r'((?:href|src)=")(/assets/[^"?]+\.(?:css|js))(")', asset, html)


def build():
    app_id, store_url = app_store_settings()
    check(ROOT)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    for name in ("robots.txt", "sitemap.xml", "CNAME", ".nojekyll"):
        shutil.copy2(ROOT / name, OUTPUT / name)
    shutil.copytree(ROOT / "assets", OUTPUT / "assets")
    for path in html_files(ROOT):
        target = OUTPUT / path.relative_to(ROOT)
        target.parent.mkdir(exist_ok=True)
        target.write_text(render(path.read_text(encoding="utf-8"), app_id, store_url,
                                 show_banner=path.name != "404.html"), encoding="utf-8")
    check(OUTPUT, store_url, app_id)
    print(f"App Store buttons: {store_url}")
    print("Safari Smart App Banner: " + (f"app-id={app_id}" if app_id else "ready; waiting for app_store_id"))
    print(f"GitHub Pages artifact: {OUTPUT}")


if __name__ == "__main__":
    build()
