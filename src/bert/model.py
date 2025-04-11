from __future__ import annotations

from typing import Any

import torch
from transformers import AutoModel, AutoTokenizer

from src.constants import BERT_PRETRAINED_MODEL_NAME
from src.elastic_search import search_internships
from src.eval.relevance_calculator import RelevanceCalculator


class BERTSearchEngineFitter(torch.nn.Module):
    """Модель для обучения ранжированию с BERT"""

    def __init__(
        self,
        model_name: str = BERT_PRETRAINED_MODEL_NAME,
    ) -> None:
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)

        # Определяем размерность BERT динамически
        with torch.no_grad():
            # Создаем тестовый тензор для определения размерности
            test_input = torch.zeros((1, 10), dtype=torch.long)
            test_mask = torch.ones((1, 10), dtype=torch.long)

            test_output = self.bert(
                input_ids=test_input,
                attention_mask=test_mask,
            )
            hidden_size = test_output.last_hidden_state.shape[-1]

        self.dropout = torch.nn.Dropout(0.2)
        self.similarity_layer = torch.nn.Linear(hidden_size * 2, 1)

    def forward(
        self,
        query_input_ids,
        query_attention_mask,
        text_input_ids,
        text_attention_mask,
    ):
        query_outputs = self.bert(
            input_ids=query_input_ids,
            attention_mask=query_attention_mask,
        )

        text_outputs = self.bert(
            input_ids=text_input_ids,
            attention_mask=text_attention_mask,
        )

        query_embeddings = query_outputs.last_hidden_state[:, 0, :]
        text_embeddings = text_outputs.last_hidden_state[:, 0, :]

        query_embeddings = self.dropout(query_embeddings)
        text_embeddings = self.dropout(text_embeddings)

        # Конкатенируем эмбеддинги и вычисляем релевантность
        concatenated = torch.cat([query_embeddings, text_embeddings], dim=1)
        similarity = self.similarity_layer(concatenated)
        return torch.sigmoid(similarity)


class BERTSearchEngine:
    """Класс-обертка для использования BERT модели в поиске"""

    def __init__(
        self,
        model: torch.nn.Module,
        pretrained_model_name: str = BERT_PRETRAINED_MODEL_NAME,
    ) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name)
        self.model = model
        self.device = torch.device(
            'cuda' if torch.cuda.is_available() else 'cpu',
        )
        self.model.to(self.device)
        self.model.eval()

    @staticmethod
    def serialize_model_from_checkpoint(
        checkpoint_path: str | None = None,
        pretrained_model_name: str = BERT_PRETRAINED_MODEL_NAME,
    ) -> torch.nn.Module:
        """Интерфейс для загрузки модели в BERTSearchEngine через чекпоинт

        Args:
            checkpoint_path (str | None, optional):
                Путь до чекпоинта. Defaults to None.
            pretrained_model_name (str):
                Название модели, которую дообучали.
                Defaults to BERT_PRETRAINED_MODEL_NAME.
        Returns:
            torch.nn.Module: Дообученная модель
        """
        model = BERTSearchEngineFitter(model_name=pretrained_model_name)
        if checkpoint_path is not None:
            model.load_state_dict(torch.load(checkpoint_path))
        return model

    def find_internships(
        self,
        query: str,
        index_name: str,
        elastic_size: int = 50,
        rerank_size: int = 10,
    ) -> list[dict[str, Any]]:
        """Поиск стажировок с переранжированием результатов с помощью BERT

        Args:
            query (str): Поисковый запрос пользователя
            index_name (str):
                Название индекса ElasticSearch для поиска стажировок
            elastic_size (int, optional):
                Количество результатов, запрашиваемых из ElasticSearch.
                Defaults to 50.
            rerank_size (int, optional):
                Количество результатов,
                возвращаемых после переранжирования BERT моделью.
                Defaults to 10.

        Returns:
            list[dict[str, Any]]:
                Отсортированный по релевантности список стажировок
                после переранжирования BERT моделью
        """
        es_results = search_internships(query, index_name, size=elastic_size)
        return self.rerank_results(
            query,
            es_results.copy(),
            top_n=rerank_size,
        )

    def rerank_results(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_n: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Переранжирует результаты на основе дообученной модели BERT.
        """
        if not results:
            return results

        for result in results:
            full_text = RelevanceCalculator._extract_document_text(
                result['_source'],
            )

            if len(full_text) > 5000:
                full_text = full_text[:5000]

            result['_score'] = self._compute_relevance(query, full_text)

        results.sort(key=lambda x: x['_score'], reverse=True)

        if top_n is not None:
            return results[:top_n]
        return results

    def _compute_relevance(self, query: str, text: str) -> float:
        query_encoding = self.tokenizer(
            query,
            truncation=True,
            max_length=512,
            padding='max_length',
            return_tensors='pt',
        )

        text_encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=512,
            padding='max_length',
            return_tensors='pt',
        )

        query_input_ids = query_encoding['input_ids'].to(self.device)
        query_attention_mask = query_encoding['attention_mask'].to(self.device)
        text_input_ids = text_encoding['input_ids'].to(self.device)
        text_attention_mask = text_encoding['attention_mask'].to(self.device)

        with torch.no_grad():
            relevance = self.model(
                query_input_ids=query_input_ids,
                query_attention_mask=query_attention_mask,
                text_input_ids=text_input_ids,
                text_attention_mask=text_attention_mask,
            )

        return relevance.item()
