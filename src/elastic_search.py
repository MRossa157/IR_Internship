from elasticsearch import Elasticsearch

es = Elasticsearch('http://localhost:9200')


def create_index(index_name: str) -> None:
    """Создание индекса в Elasticsearch"""
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
        print('Индекс создан.')
    else:
        print('Индекс уже существует.')


def index_internships(json_data: dict, index_name: str) -> None:
    """Индексирование данных о стажировках"""
    for idx, internship in enumerate(json_data):
        es.index(index=index_name, id=idx, document=internship)
    print(f'{len(json_data)} документов проиндексировано.')


def search_internships(query, index_name: str):
    """Поиск стажировок по запросу"""
    body = {
        'query': {
            'multi_match': {
                'query': query,
                'fields': ['title', 'company', 'description'],
            }
        }
    }
    response = es.search(index=index_name, body=body)
    return response['hits']['hits']
