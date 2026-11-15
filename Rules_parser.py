import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE_URL = "https://yandex.ru/dev/games/doc/ru/requirements/1/2"
OUTPUT_DIR = Path("yandex_games_tech_requirements")

EXPECTED_SECTIONS = [
    "Авторизация",
    "Звук вне игры",
    "Системный плеер",
    "Активное поле на десктопе",
    "Адаптация для ТВ",
    "Сохранение прогресса",
    "Корректное отображение",
    "Монетизация",
    "Инап-покупки",
    "Технические ошибки",
    "Завершенный вид",
    "Методы SDK",
]


class YfmMarkdownConverter(MarkdownConverter):
    """Кастомный конвертер для сохранения языков в блоках кода YFM."""

    def convert_pre(self, el, text, *args, **kwargs):
        code = el.find("code")
        lang = ""
        if code and code.get("class"):
            for cls in code["class"]:
                if cls.startswith("language-"):
                    lang = cls.removeprefix("language-")
                    break
        code_text = code.get_text() if code else el.get_text()
        return f"\n```{lang}\n{code_text.strip()}\n```\n\n"


def sanitize_filename(name: str) -> str:
    """Очищает название раздела для использования в имени файла."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return re.sub(r"\s+", "_", cleaned)


def html_to_clean_markdown(html: str, base_uri: str) -> str:
    """Очищает HTML-разметку Diplodoc и преобразует её в Markdown."""
    soup = BeautifulSoup(html, "html.parser")

    selectors_to_remove = [
        "a.yfm-anchor",
        ".yfm-clipboard-button",
        ".dc-doc-page__toc",
        ".dc-doc-page__controls",
        ".dc-breadcrumbs",
        ".dc-feedback",
        "nav",
        "button",
        "svg",
    ]
    for selector in selectors_to_remove:
        for tag in soup.select(selector):
            tag.decompose()

    for tag in soup.find_all(["a", "img"]):
        attr = "href" if tag.name == "a" else "src"
        if tag.get(attr):
            tag[attr] = urljoin(base_uri, tag[attr])

    for note in soup.select("div.yfm-note"):
        title = note.select_one(".yfm-note-title")
        if title:
            strong = soup.new_tag("strong")
            strong.string = f"{title.get_text(strip=True)}: "
            title.replace_with(strong)
        note.name = "blockquote"

    converter = YfmMarkdownConverter(heading_style="ATX", bullets="-")
    md_text = converter.convert_soup(soup)

    md_text = re.sub(r"\n{3,}", "\n\n", md_text).strip()
    return md_text + "\n"


def get_article_html(page) -> str:
    """Находит основной контейнер статьи на странице Diplodoc и возвращает его HTML."""
    content_selectors = [
        ".dc-doc-page__body",
        ".dc-doc-page__main",
        "article",
        "main .yfm:visible",
        ".yfm:visible",
        "main",
    ]
    for selector in content_selectors:
        locator = page.locator(selector).first
        if locator.count() > 0:
            html = locator.inner_html()
            if html.strip():
                return html

    raise RuntimeError(f"Не удалось найти контейнер с текстом статьи на {page.url}")


def parse_technical_requirements():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="ru-RU",
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        print(f"Открываю страницу: {BASE_URL}")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)

        if "showcaptcha" in page.url:
            browser.close()
            raise RuntimeError(
                "Яндекс показал SmartCaptcha. Запустите скрипт с headless=False и пройдите проверку вручную."
            )

        tech_btn = page.locator('button[aria-label="Выпадающий список Технические"]').first
        try:
            tech_btn.wait_for(state="visible", timeout=30000)
        except PlaywrightTimeoutError:
            browser.close()
            raise RuntimeError(
                f"Не удалось дождаться меню. Текущий URL: {page.url}. Попробуйте запустить с headless=False."
            )

        if tech_btn.get_attribute("aria-expanded") != "true":
            tech_btn.click()
            page.wait_for_timeout(500)

        parent_item = tech_btn.locator("xpath=..")
        link_elements = parent_item.locator("ul a").all()

        sections = []
        seen_urls = set()
        for link in link_elements:
            title = link.inner_text().strip()
            raw_href = link.get_attribute("href")
            if not title or not raw_href or raw_href.startswith("#"):
                continue
            # Берём el.href из браузера, чтобы корректно учитывался тег <base>
            full_url = link.evaluate("el => el.href").split("#")[0]
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                sections.append((title, full_url))

        print(f"Найдено подразделов: {len(sections)}")

        for idx, (title, url) in enumerate(sections, start=1):
            print(f"[{idx}/{len(sections)}] Парсинг: {title} -> {url}")
            response = page.goto(url, wait_until="domcontentloaded", timeout=60000)

            if response and response.status >= 400:
                browser.close()
                raise RuntimeError(f"Ошибка HTTP {response.status} при открытии {url}")

            if "showcaptcha" in page.url:
                browser.close()
                raise RuntimeError(
                    f"Яндекс показал SmartCaptcha при переходе на {url}. Запустите с headless=False."
                )

            h1_locator = page.locator("main h1:visible, article h1:visible, h1:visible").first
            try:
                h1_locator.wait_for(state="visible", timeout=20000)
            except PlaywrightTimeoutError:
                page_title = page.title()
                browser.close()
                raise RuntimeError(
                    f"Не дождались заголовка статьи на {url} (title: '{page_title}', current_url: '{page.url}')"
                )

            page.wait_for_timeout(300)

            base_uri = page.evaluate("() => document.baseURI")
            raw_html = get_article_html(page)
            markdown_content = html_to_clean_markdown(raw_html, base_uri)

            if not markdown_content.startswith("# "):
                markdown_content = f"# {title}\n\n{markdown_content}"

            filename = f"{idx:02d}_{sanitize_filename(title)}.md"
            filepath = OUTPUT_DIR / filename
            filepath.write_text(markdown_content, encoding="utf-8")

        parsed_titles = {t for t, _ in sections}
        missing = [s for s in EXPECTED_SECTIONS if s not in parsed_titles]
        if missing:
            print(f"Внимание! Не найдены разделы: {', '.join(missing)}")
        else:
            print(f"Готово! Все файлы сохранены в папку: {OUTPUT_DIR.resolve()}")

        browser.close()


if __name__ == "__main__":
    parse_technical_requirements()