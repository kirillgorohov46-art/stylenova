#!/usr/bin/env python3
"""
Парсер цен и характеристик для магазина StyleNova.

Что делает:
  1. Читает список страниц (ссылок) из файла targets.json.
  2. Для каждой страницы с помощью ИИ (ScrapeGraphAI + OpenAI) вытаскивает
     структурированные данные: название, цену, состояние, характеристики,
     наличие, продавца.
  3. Складывает всё в один CSV-файл в папке results/ — его удобно открыть
     в Excel или Google Таблицах для сравнения цен.

Запуск:
    python scrape_prices.py                 # берёт targets.json
    python scrape_prices.py --file my.json  # другой файл со ссылками
    python scrape_prices.py --url https://... "iPhone 13"   # разовая проверка одной ссылки

Перед первым запуском смотрите README.md в этой же папке.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Папка, где лежит этот скрипт (чтобы пути работали из любого места)
BASE_DIR = Path(__file__).resolve().parent

# Что именно ИИ должен извлечь с каждой страницы.
# Меняйте формулировку под свои задачи — она на естественном языке.
EXTRACTION_PROMPT = (
    "Извлеки данные о товаре с этой страницы. Верни JSON с полями: "
    "product_name (полное название товара), "
    "price (цена в рублях, только число), "
    "currency (валюта), "
    "condition (состояние: новый / б/у / на запчасти и т.п.), "
    "specs (ключевые характеристики: процессор, ОЗУ, накопитель, видеокарта, экран — "
    "коротким текстом), "
    "availability (в наличии или нет), "
    "seller (имя или название продавца, если есть). "
    "Если какого-то поля нет — поставь null. Не выдумывай данные."
)

# Порядок колонок в итоговом CSV
CSV_FIELDS = [
    "scraped_at",
    "source_name",
    "url",
    "product_name",
    "price",
    "currency",
    "condition",
    "specs",
    "availability",
    "seller",
    "error",
]


def build_config() -> dict:
    """Собирает настройки для ScrapeGraphAI из переменных окружения (.env)."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini").strip()

    if not api_key or api_key.startswith("sk-ваш"):
        sys.exit(
            "❌ Не найден OPENAI_API_KEY.\n"
            "   1) Скопируйте .env.example в .env\n"
            "   2) Впишите туда свой настоящий ключ OpenAI\n"
            "   Подробнее — в README.md"
        )

    return {
        "llm": {
            "api_key": api_key,
            "model": model,
        },
        "verbose": False,   # поставьте True, чтобы видеть подробный лог
        "headless": True,   # браузер работает в фоне, без окна
    }


def scrape_one(url: str, config: dict) -> dict:
    """Парсит одну страницу и возвращает словарь с данными (или с ошибкой)."""
    # Импорт внутри функции, чтобы понятная подсказка об установке
    # показывалась только при реальном запуске парсинга.
    try:
        from scrapegraphai.graphs import SmartScraperGraph
    except ImportError:
        sys.exit(
            "❌ Библиотека scrapegraphai не установлена.\n"
            "   Выполните:  pip install -r requirements.txt  &&  playwright install\n"
            "   Подробнее — в README.md"
        )

    graph = SmartScraperGraph(prompt=EXTRACTION_PROMPT, source=url, config=config)
    result = graph.run()

    # ИИ обычно возвращает dict; иногда — строку с JSON внутри.
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            result = {"raw": result}
    if not isinstance(result, dict):
        result = {"raw": str(result)}
    return result


def to_row(source_name: str, url: str, data: dict, error: str = "") -> dict:
    """Приводит результат к единой строке для CSV."""
    return {
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_name": source_name,
        "url": url,
        "product_name": data.get("product_name"),
        "price": data.get("price"),
        "currency": data.get("currency"),
        "condition": data.get("condition"),
        "specs": data.get("specs"),
        "availability": data.get("availability"),
        "seller": data.get("seller"),
        "error": error,
    }


def load_targets(file_path: Path) -> list[dict]:
    """Загружает список ссылок из targets.json."""
    if not file_path.exists():
        sys.exit(
            f"❌ Файл со ссылками не найден: {file_path}\n"
            "   Скопируйте targets.example.json в targets.json и впишите свои ссылки."
        )
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    targets = data.get("targets", [])
    # выбрасываем строки-примеры без настоящей ссылки
    targets = [t for t in targets if t.get("url") and "example" not in t["url"]]
    if not targets:
        sys.exit(
            "❌ В targets.json нет ни одной настоящей ссылки "
            "(примеры с 'example' в адресе пропускаются). Добавьте свои ссылки."
        )
    return targets


def save_results(rows: list[dict]) -> Path:
    """Сохраняет результаты в CSV с датой в имени файла."""
    results_dir = BASE_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    out_path = results_dir / f"prices_{stamp}.csv"
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Парсер цен StyleNova (ScrapeGraphAI + OpenAI)"
    )
    parser.add_argument(
        "--file",
        default=str(BASE_DIR / "targets.json"),
        help="Путь к JSON-файлу со ссылками (по умолчанию targets.json)",
    )
    parser.add_argument(
        "--url",
        help="Разово спарсить одну ссылку, не используя targets.json",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default="Разовая проверка",
        help="Название для разовой ссылки (необязательно)",
    )
    args = parser.parse_args()

    # Загружаем ключи из .env
    load_dotenv(BASE_DIR / ".env")
    config = build_config()

    # Формируем список целей
    if args.url:
        targets = [{"name": args.name, "url": args.url}]
    else:
        targets = load_targets(Path(args.file))

    print(f"🔍 К обработке: {len(targets)} страниц(ы). Начинаю...\n")

    rows: list[dict] = []
    for i, target in enumerate(targets, start=1):
        name = target.get("name", "без названия")
        url = target["url"]
        print(f"[{i}/{len(targets)}] {name}\n    {url}")
        try:
            data = scrape_one(url, config)
            rows.append(to_row(name, url, data))
            price = data.get("price")
            print(f"    ✅ Готово. Цена: {price if price is not None else '—'}\n")
        except Exception as exc:  # noqa: BLE001 — хотим продолжить остальные ссылки
            rows.append(to_row(name, url, {}, error=str(exc)))
            print(f"    ⚠️  Ошибка: {exc}\n")

    out_path = save_results(rows)
    ok = sum(1 for r in rows if not r["error"])
    print("─" * 50)
    print(f"Готово: {ok} из {len(rows)} успешно.")
    print(f"📄 Результаты сохранены в: {out_path}")
    print("   Откройте этот файл в Excel или Google Таблицах.")


if __name__ == "__main__":
    main()
