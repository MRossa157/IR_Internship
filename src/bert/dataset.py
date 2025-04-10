import random

import torch
from torch.utils.data import Dataset

from src.constants import EVALUATION_QUERIES, INDEX_NAME
from src.elastic_search import search_internships
from src.eval.relevance_calculator import (
    RelevanceCalculator,
    calculate_result_relevance,
)
from src.eval.tech_categories import TECH_CATEGORIES


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
        results = search_internships(query, INDEX_NAME, size=20)
        for result in results:
            document_text = RelevanceCalculator._extract_document_text(
                result['_source'],
            )

            relevance = calculate_result_relevance(query, result)
            label = 1.0 if relevance >= 0.5 else 0.0

            train_queries.append(query)
            train_texts.append(document_text)
            train_labels.append(label)

    return train_queries, train_texts, train_labels


def create_training_data_from_categories() -> tuple[
    list[str],
    list[str],
    list[float],
]:
    train_queries = []
    train_texts = []
    train_labels = []

    for tech, related_terms in TECH_CATEGORIES.items():
        # Положительные примеры
        for term in related_terms:
            query = tech
            text = f'Стажировка по направлению {tech}. Требуются навыки: {term}.'

            train_queries.append(query)
            train_texts.append(text)
            train_labels.append(1.0)  # Релевантный пример

        # Несколько отрицательных примеров
        other_techs = list(TECH_CATEGORIES.keys())
        other_techs.remove(tech)

        random_terms = random.sample(other_techs, min(5, len(other_techs)))

        for term in random_terms:
            query = tech
            text = f'Стажировка по направлению {tech}. Требуются навыки: {term}.'

            train_queries.append(query)
            train_texts.append(text)
            train_labels.append(0.0)  # Нерелевантный пример

    return train_queries, train_texts, train_labels
