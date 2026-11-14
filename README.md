# Yandex Games HTML5 SDK Documentation Scraper

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Chromium-2EAD33?logo=playwright&logoColor=white)
![BeautifulSoup4](https://img.shields.io/badge/Parser-BeautifulSoup4-orange)
![Markdown](https://img.shields.io/badge/Output-Markdown-lightgrey?logo=markdown&logoColor=white)

A Python scraper built with **Playwright**, **BeautifulSoup4**, and **Markdownify** that extracts the official [Yandex Games HTML5 SDK Documentation](https://yandex.ru/dev/games/doc/ru/sdk/sdk-about) (in Russian) and converts each section into clean, structured Markdown files.

> **Note:** Pre-scraped Markdown files are already included in the `yandex_games_html5_sdk/` directory, so you can browse or feed them into an LLM/RAG pipeline right away without running the scraper first.

---

## Features

- **SPA & Dynamic TOC Navigation:** Uses headless Chromium via Playwright to expand nested sidebar menus (`SDK → HTML5`) and wait for client-side route transitions.
- **Noise Removal:** Strips navigation bars, footers, buttons, feedback widgets (`.dc-feedback`), and page controls (`.dc-doc-page__controls`) before conversion.
- **Clean Markdown Output:** Converts documentation HTML into ATX-style Markdown (`#`, `##`, `###`), preserves syntax-highlighting language tags (`data-lang`), normalizes excessive blank lines, and includes the source URL at the top of every file.
- **Ordered File Naming:** Saves each SDK section with a zero-padded numeric prefix (`01_` through `16_`) matching the official documentation hierarchy.

---

## Project Structure

```text
.
├── yandex_games_html5_sdk/                 # Pre-parsed SDK documentation (.md)
│   ├── 01_Подключение и использование.md
│   ├── 02_Загрузка игры и разметка геймплея.md
│   ├── ...
│   └── 16_Пример.md
├── parser.py                               # Main scraper script
├── requirements.txt                        # Python dependencies
└── README.md
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # macOS / Linux
   .venv\Scripts\activate           # Windows
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the Chromium browser for Playwright:**
   ```bash
   playwright install chromium
   ```

---

## Usage

If you only need the documentation text, open the pre-generated files in `yandex_games_html5_sdk/`.

To re-scrape and update the documentation with the latest changes from Yandex:

```bash
python parser.py
```

The script will launch headless Chromium, iterate through all 16 configured documentation sections, and overwrite/save the updated `.md` files into `yandex_games_html5_sdk/`.

---

## Included Documentation Sections

Each generated file contains a level-1 heading, a `Источник:` (Source) link pointing to the original page, and the cleaned Markdown body:

| File | Original Title (RU) | Topic (EN) |
| :--- | :--- | :--- |
| `01_Подключение и использование.md` | Подключение и использование | SDK Integration & Usage |
| `02_Загрузка игры и разметка геймплея.md` | Загрузка игры и разметка геймплея | Game Loading & Gameplay Markup |
| `03_Данные игрока.md` | Данные игрока | Player Data |
| `04_Удаленная конфигурация.md` | Удаленная конфигурация | Remote Configuration |
| `05_Реклама.md` | Реклама | Advertising |
| `06_Инап-покупки.md` | Инап-покупки | In-App Purchases |
| `07_Лидерборды.md` | Лидерборды | Leaderboards |
| `08_Асинхронный мультиплеер.md` | Асинхронный мультиплеер | Asynchronous Multiplayer |
| `09_Оценка игры.md` | Оценка игры | Game Rating & Reviews |
| `10_Ярлык на рабочий стол.md` | Ярлык на рабочий стол | Desktop Shortcut |
| `11_Переменные окружения.md` | Переменные окружения | Environment Variables |
| `12_Серверное время.md` | Серверное время | Server Time |
| `13_События.md` | События | Events |
| `14_Ссылки на другие игры.md` | Ссылки на другие игры | Links to Other Games |
| `15_Другие объекты и параметры SDK.md` | Другие объекты и параметры SDK | Other SDK Objects & Parameters |
| `16_Пример.md` | Пример | Complete Example |

---

## Configuration

You can customize the scraper behavior by editing the constants at the top of `parser.py`:

- **`BASE_URL`** — Entry point URL for the Yandex Games documentation (can be switched to `/en/` if targeting English sidebar items).
- **`OUTPUT_DIR`** — Target directory where Markdown files are saved (defaults to `yandex_games_html5_sdk`).
- **`SECTIONS`** — Ordered list of sidebar menu titles to locate, click, and export.
