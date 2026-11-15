from pathlib import Path
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from playwright.sync_api import Page, sync_playwright

BASE_URL = "https://yandex.ru/dev/games/doc/ru/sdk/sdk-about"
OUTPUT_DIR = Path("yandex_games_html5_sdk")

SECTIONS = [
    "Подключение и использование",
    "Загрузка игры и разметка геймплея",
    "Данные игрока",
    "Удаленная конфигурация",
    "Реклама",
    "Инап-покупки",
    "Лидерборды",
    "Асинхронный мультиплеер",
    "Оценка игры",
    "Ярлык на рабочий стол",
    "Переменные окружения",
    "Серверное время",
    "События",
    "Ссылки на другие игры",
    "Другие объекты и параметры SDK",
    "Пример",
]


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def clean_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("button, nav, footer, .dc-feedback, .dc-doc-page__controls"):
        tag.decompose()
    raw_md = md(
        str(soup),
        heading_style="ATX",
        code_language_callback=lambda el: el.get("data-lang", ""),
    )
    return re.sub(r"\n{3,}", "\n\n", raw_md).strip()


def find_toc_item(page: Page, target_title: str):
    items = page.locator(".dc-toc-item__text")
    for i in range(items.count()):
        item = items.nth(i)
        if item.is_visible() and normalize_text(item.inner_text()) == target_title:
            return item
    return None


def ensure_expanded(page: Page, parent_title: str, child_title: str) -> None:
    if find_toc_item(page, child_title) is not None:
        return
    parent_item = find_toc_item(page, parent_title)
    if parent_item is not None:
        parent_item.scroll_into_view_if_needed()
        parent_item.click()
        page.wait_for_timeout(500)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_selector(".dc-toc-item__text", timeout=10000)

        ensure_expanded(page, "SDK", "HTML5")
        ensure_expanded(page, "HTML5", SECTIONS[0])

        for idx, title in enumerate(SECTIONS, start=1):
            toc_item = find_toc_item(page, title)
            if toc_item is None:
                print(f"Не найден пункт меню: {title}")
                continue

            prev_url = page.url
            toc_item.scroll_into_view_if_needed()
            toc_item.click()

            try:
                page.wait_for_function(
                    "prev => window.location.href !== prev",
                    arg=prev_url,
                    timeout=5000,
                )
            except Exception:
                pass

            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(400)

            container = page.locator("main").first
            html_content = (
                container.inner_html() if container.count() else page.content()
            )
            markdown_content = (
                f"# {title}\n\nИсточник: {page.url}\n\n"
                f"{clean_markdown(html_content)}\n"
            )

            file_path = OUTPUT_DIR / f"{idx:02d}_{sanitize_filename(title)}.md"
            file_path.write_text(markdown_content, encoding="utf-8")
            print(f"Сохранено: {file_path}")

        browser.close()


if __name__ == "__main__":
    main()
