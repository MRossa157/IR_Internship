
import torch
from torch.utils.data import Dataset

from src.constants import EVALUATION_QUERIES, INDEX_NAME
from src.elastic_search import search_internships
from src.eval.relevance_calculator import (
    RelevanceCalculator,
    calculate_result_relevance,
)


class InternshipDataset(Dataset):
    def __init__(
        self,
        queries,
        texts,
        labels,
        tokenizer,
        max_length: int = 512,
    ) -> None:
        self.queries = queries
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.queries)

    def __getitem__(self, idx):
        query = self.queries[idx]
        text = self.texts[idx]
        label = self.labels[idx]

        # Токенизация запроса и текста
        query_encoding = self.tokenizer(
            query,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt',
        )

        text_encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt',
        )

        return {
            'query_input_ids': query_encoding['input_ids'].squeeze(),
            'query_attention_mask': query_encoding['attention_mask'].squeeze(),
            'text_input_ids': text_encoding['input_ids'].squeeze(),
            'text_attention_mask': text_encoding['attention_mask'].squeeze(),
            'label': torch.tensor(label, dtype=torch.float),
        }


def create_training_data_from_evaluation() -> tuple[
    list[str],
    list[str],
    list[float],
]:
    queries = EVALUATION_QUERIES

    train_queries = []
    train_texts = []
    train_labels = []

    for query in queries:
        results = search_internships(query, INDEX_NAME, size=50)
        for result in results:
            document_text = RelevanceCalculator._extract_document_text(
                result['_source'],
            )

            label = calculate_result_relevance(query, result)

            train_queries.append(query)
            train_texts.append(document_text)
            train_labels.append(label)

    return train_queries, train_texts, train_labels
