import json


def load_json(file_path) -> dict:
    """Загрузка данных из JSON-файла"""
    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path, data: dict) -> None:
    """Сохранение данных в JSON-файл"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
