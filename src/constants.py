INTERNSHIP_LIST_PATH = 'https://fut.ru/api/cms/api/publications'
EVENTS_LIST_PATH = 'https://fut.ru/api/forms/api/events'

INDEX_NAME = 'internships'

BAD_WORDS = {
    '&nbsp;',
    '<br>',
    '</b>',
    '<b>',
    '&amp; ',
    '<i>',
    '</i>',
    '<a>',
    '</a>',
}

PARSER_RESULT_FILENAME = 'parser_result.json'

EVALUATION_QUERIES = [
    'Python',
    'python разработчик',
    'HR',
    'data science',
    'devops',
    'front end',
    'front end mobile',
    'android',
    'ios',
    'QA',
]


BERT_TRAINING_BATCH_SIZE = 4
BERT_TRAINING_EPOCHS = 5
BERT_PRETRAINED_MODEL_NAME = 'sberbank-ai/sbert_large_mt_nlu_ru'
