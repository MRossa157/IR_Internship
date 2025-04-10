from __future__ import annotations

from typing import Any

import torch
from transformers import AutoModel, AutoTokenizer

from src.constants import BERT_PRETRAINED_MODEL_NAME
from src.eval.relevance_calculator import RelevanceCalculator


class BERTRankerFitter(torch.nn.Module):
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

            # Выполняем один проход и смотрим размерность выхода
            test_output = self.bert(
                input_ids=test_input,
                attention_mask=test_mask,
            )
            hidden_size = test_output.last_hidden_state.shape[-1]

        # Создаем слой с правильной размерностью
        self.similarity_layer = torch.nn.Linear(hidden_size * 2, 1)

    def forward(
        self,
        query_input_ids,
        query_attention_mask,
        text_input_ids,
        text_attention_mask,
    ):
        # Получаем эмбеддинги запроса
        query_outputs = self.bert(
            input_ids=query_input_ids,
            attention_mask=query_attention_mask,
        )

        # Получаем эмбеддинги текста
        text_outputs = self.bert(
            input_ids=text_input_ids,
            attention_mask=text_attention_mask,
        )

        # Используем [CLS] токен как эмбеддинг предложения
        query_embeddings = query_outputs.last_hidden_state[:, 0, :]
        text_embeddings = text_outputs.last_hidden_state[:, 0, :]

        # Конкатенируем эмбеддинги и вычисляем релевантность
        concatenated = torch.cat([query_embeddings, text_embeddings], dim=1)
        similarity = self.similarity_layer(concatenated)
        return torch.sigmoid(similarity)


class BERTRanker:
    """Класс-обертка для использования обученной модели в поиске"""

    def __init__(
        self,
        checkpoint_path: str | None = 'best_bert_ranker.pth',
        pretrained_model_name: str = BERT_PRETRAINED_MODEL_NAME,
    ) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name)

        self.model = BERTRankerFitter(model_name=pretrained_model_name)
        if checkpoint_path is not None:
            self.model.load_state_dict(torch.load(checkpoint_path))

        self.device = torch.device(
            'cuda' if torch.cuda.is_available() else 'cpu',
        )
        self.model.to(self.device)
        self.model.eval()

    def compute_relevance(self, query: str, text: str) -> float:
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

    def rerank_results(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_n: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Переранжирует результаты на основе дообученной модели BERT.
        """
        for result in results:
            full_text = RelevanceCalculator._extract_document_text(
                result['_source'],
            )

            if len(full_text) > 5000:
                full_text = full_text[:5000]

            bert_score = self.compute_relevance(query, full_text)

            result['bert_score'] = bert_score

            elastic_weight = 0.3
            bert_weight = 0.7
            result['_score'] = (
                elastic_weight * result['_score'] + bert_weight * bert_score
            )

        results.sort(key=lambda x: x['_score'], reverse=True)

        if top_n is not None:
            return results[:top_n]
        return results
