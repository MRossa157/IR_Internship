import json
import re
from datetime import datetime
from typing import Any

from eval.tech_categories import TECH_CATEGORIES


def load_json(file_path: str) -> dict:
    """Загрузка данных из JSON-файла"""
    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path: str, data: dict) -> None:
    """Сохранение данных в JSON-файл"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def convert_to_iso_format(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

    return date_obj.isoformat()


def remove_bad_words(data: list[dict], bad_words: set[str]) -> list[dict]:
    # Преобразуем bad_words в регулярное выражение для ускоренной замены
    bad_words_pattern = re.compile('|'.join(map(re.escape, bad_words)))

    if isinstance(data, dict):
        return {
            key: remove_bad_words(value, bad_words)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [remove_bad_words(item, bad_words) for item in data]
    if isinstance(data, str):
        # Применяем регулярное выражение для удаления плохих слов
        return bad_words_pattern.sub('', data)
    return data


def make_query_variants(query: str) -> set[str]:
    return {
        # Оригинальный запрос
        query,
        # Без пробелов
        query.replace(' ', ''),
        # Пробелы вместо дефисов
        query.replace('-', ' '),
        # Дефисы вместо пробелов
        query.replace(' ', '-'),
    }


def detect_tech_category(query: str) -> dict[str, list[str]]:
    """
    Определяет техническую категорию запроса для настройки поиска.

    Args:
        query: Поисковый запрос

    Returns:
        Словарь категорий и связанных с ними терминов
    """
    query_lower = query.lower()
    query_variants = make_query_variants(query_lower)

    result = {}

    for category, terms in TECH_CATEGORIES.items():
        if any(variant == category for variant in query_variants):
            result[category] = terms
            continue

        if any(variant in terms for variant in query_variants):
            result[category] = terms
            continue

        if any(category in variant for variant in query_variants):
            result[category] = terms
            continue

        if any(term in query_lower for term in terms):
            result[category] = terms
            continue

    return result


def print_search_result(result: dict[str, Any], verbose: bool = False) -> None:
    company_data = result['_source']['company']

    positions_raw = result['_source'].get('positions')
    if positions_raw is not None:
        positions = [position['name'] for position in positions_raw]
    else:
        positions = []

    if not verbose:
        print(
            f'- {result["_source"]["title"]} '
            f'в компании {company_data["caption"]}. '
            f'\nДоступны вакансии в: {", ".join(positions)} '
            f'\nURL: https://fut.ru/internship/{company_data["alias"]}/{result["_source"]["alias"]}'
            '\n',
        )
    else:
        title = result['_source']['title']
        description = result['_source']['description']
        slogan = result['_source']['slogan']
        published_at = result['_source']['published_at']
        unpublished_at = result['_source']['unpublished_at']

        company_caption = company_data['caption']
        company_description = (
            company_data['description']['blocks'][0]['data']['text']
            if company_data['description']['blocks']
            else 'Описание не указано.'
        )

        external_link = (
            positions_raw[0]['external_link']
            if positions_raw is not None and len(positions_raw) > 0
            else None
        )

        internship_url = f'https://fut.ru/internship/{company_data["alias"]}/{result["_source"]["alias"]}'

        print(
            f'Название стажировки: {title}\n'
            f'Компания: {company_caption}\n'
            f'Описание стажировки: {description}\n'
            f'Слоган: {slogan}\n'
            f'Дата публикации: {published_at}\n'
            f'Дата завершения: {unpublished_at}\n'
            f'Описание компании: {company_description}\n'
            f'Вакансии доступны в следующих направлениях: {", ".join(positions)}\n'
            f'Ссылка на вакансии: {external_link if external_link else "Нет ссылок на вакансии."}\n'
            f'Ссылка на стажировку: {internship_url}\n',
        )
