from __future__ import annotations

import math
from typing import Any, Callable

import pandas as pd

from eval.relevance_calculator import calculate_result_relevance


class SearchEvaluator:
    """Класс для автоматической оценки качества поисковой выдачи."""

    @staticmethod
    def calculate_precision(
        relevance_scores: list[float],
        threshold: float = 0.5,
    ) -> float:
        """
        Вычисляет precision - долю релевантных результатов в выдаче.

        Args:
            relevance_scores: Список оценок релевантности (от 0.0 до 1.0)
            threshold: Минимальный порог релевантности (по умолчанию 0.5)

        Returns:
            Значение precision
        """
        if not relevance_scores:
            return 0

        relevant = sum(1 for score in relevance_scores if score >= threshold)
        return relevant / len(relevance_scores)

    @staticmethod
    def calculate_dcg(relevance_scores: list[float]) -> float:
        """
        Вычисляет DCG (Discounted Cumulative Gain).

        Args:
            relevance_scores: Список оценок релевантности (от 0.0 до 1.0)

        Returns:
            Значение DCG
        """
        if not relevance_scores:
            return 0

        dcg = 0
        for i, rel in enumerate(relevance_scores, 1):
            dcg += rel / max(1, math.log2(i + 1))
        return dcg

    @staticmethod
    def calculate_idcg(relevance_scores: list[float]) -> float:
        """
        Вычисляет IDCG (Ideal DCG) - максимально возможное значение DCG.

        Args:
            relevance_scores: Список оценок релевантности (от 0.0 до 1.0)

        Returns:
            Значение IDCG
        """
        sorted_relevance = sorted(relevance_scores, reverse=True)
        return SearchEvaluator.calculate_dcg(sorted_relevance)

    @staticmethod
    def calculate_ndcg(relevance_scores: list[float]) -> float:
        """
        Вычисляет NDCG (Normalized DCG).

        Args:
            relevance_scores: Список оценок релевантности (от 0.0 до 1.0)

        Returns:
            Значение NDCG
        """
        idcg = SearchEvaluator.calculate_idcg(relevance_scores)
        if idcg == 0:
            return 0

        return SearchEvaluator.calculate_dcg(relevance_scores) / idcg

    @staticmethod
    def evaluate_search_results(
        results: list[dict[str, Any]],
        query: str,
    ) -> dict[str, Any]:
        """
        Оценивает результаты поиска.

        Args:
            results: Результаты поиска из Elasticsearch
            query: Поисковый запрос
            relevance_function: Функция для оценки релевантности результата

        Returns:
            Словарь с метриками оценки
        """
        relevance_scores = [
            calculate_result_relevance(query, result) for result in results
        ]

        precision = SearchEvaluator.calculate_precision(relevance_scores)
        dcg = SearchEvaluator.calculate_dcg(relevance_scores)
        idcg = SearchEvaluator.calculate_idcg(relevance_scores)
        ndcg = SearchEvaluator.calculate_ndcg(relevance_scores)

        return {
            'query': query,
            'precision': precision,
            'dcg': dcg,
            'idcg': idcg,
            'ndcg': ndcg,
            'evaluated_results': len(results),
            'relevance_scores': relevance_scores,
        }

    @staticmethod
    def evaluate_multiple_queries(
        queries_results: dict[str, list[dict[str, Any]]],
        relevance_function: Callable | None = None,
    ) -> dict[str, Any]:
        """
        Оценивает результаты поиска для нескольких запросов.

        Args:
            queries_results: Словарь с результатами поиска для каждого запроса
            relevance_function: Функция для оценки релевантности результата

        Returns:
            Словарь с метриками оценки для каждого запроса и средними значениями
        """
        evaluations = {}
        avg_precision = 0
        avg_ndcg = 0

        for query, results in queries_results.items():
            eval_result = SearchEvaluator.evaluate_search_results(
                results,
                query,
            )
            evaluations[query] = eval_result

            avg_precision += eval_result['precision']
            avg_ndcg += eval_result['ndcg']

        num_queries = len(queries_results)
        avg_precision /= num_queries if num_queries > 0 else 1
        avg_ndcg /= num_queries if num_queries > 0 else 1

        return {
            'evaluations': evaluations,
            'avg_precision': avg_precision,
            'avg_ndcg': avg_ndcg,
        }

    @staticmethod
    def create_report_dataframe(evaluations: dict[str, Any]) -> pd.DataFrame:
        """
        Создает DataFrame с результатами оценки.

        Args:
            evaluations: Результаты оценки от метода evaluate_multiple_queries

        Returns:
            DataFrame с результатами
        """
        data = []

        for query, eval_result in evaluations['evaluations'].items():
            data.append({
                'Запрос': query,
                'Precision': round(eval_result['precision'], 3),
                'DCG': round(eval_result['dcg'], 3),
                'IDCG': round(eval_result['idcg'], 3),
                'NDCG': round(eval_result['ndcg'], 3),
                'Кол-во результатов': eval_result['evaluated_results'],
            })

        data.append({
            'Запрос': 'СРЕДНЕЕ',
            'Precision': round(evaluations['avg_precision'], 3),
            'DCG': '',
            'IDCG': '',
            'NDCG': round(evaluations['avg_ndcg'], 3),
            'Кол-во результатов': '',
        })

        return pd.DataFrame(data)

    @staticmethod
    def parse_relevance_scores(text_data: str) -> dict[str, list[int]]:
        """
        Парсит данные оценки из текстового формата.

        Args:
            text_data: Текст с данными об оценке релевантности

        Returns:
            Словарь с запросами и оценками релевантности
        """
        query_blocks = {}
        current_query = None

        lines = text_data.strip().split('\n')

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if '\t' in line and line.split('\t')[0].strip().isdigit():
                parts = line.split('\t')
                if len(parts) > 3 and parts[0].strip() and parts[3].strip():
                    current_query = parts[1].strip()
                    relevance = int(parts[3].strip())

                    if current_query not in query_blocks:
                        query_blocks[current_query] = []

                    query_blocks[current_query].append(relevance)

        return query_blocks
