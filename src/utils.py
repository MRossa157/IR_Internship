import json
import re
from datetime import datetime


def load_json(file_path) -> dict:
    """Загрузка данных из JSON-файла"""
    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path, data: dict) -> None:
    """Сохранение данных в JSON-файл"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def convert_to_iso_format(date_str):
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
