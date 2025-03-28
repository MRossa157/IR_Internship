from eval.tech_categories import (
    COMMON_TERMS,
    RELEVANCE_WEIGHTS,
    TECH_CATEGORIES,
    TERM_WEIGHTS,
)
from utils import make_query_variants


class RelevanceCalculator:
    @classmethod
    def calculate_relevance(cls, query: str, result: dict) -> float:
        """
        Оценивает релевантность результата поиска для данного запроса
        с фокусом на позиции.

        Args:
            query: Поисковый запрос
            result: Результат поиска

        Returns:
            Оценка релевантности (от 0.0 до 1.0)
        """
        query_lower = query.lower().strip()
        source = result.get('_source', {})
        query_parts = query_lower.split()

        query_categories = {}
        for tech, categories in TECH_CATEGORIES.items():
            if (
                tech == query_lower
                or tech in query_lower
                or any(term in query_lower for term in categories)
            ):
                query_categories[tech] = categories

        positions_score = cls._evaluate_positions(
            query=query_lower,
            query_parts=query_parts,
            source=source,
        )

        if positions_score < RELEVANCE_WEIGHTS['sphere_match']:
            title_description_score = cls._evaluate_title_description(
                query_lower,
                source,
            )
            score = max(positions_score, title_description_score)
        else:
            score = positions_score

        # Если запрос связан с технической категорией, но документ не содержит
        # ни одного термина из этой категории, снижаем оценку
        if (
            score < RELEVANCE_WEIGHTS['category_match'] * 0.8
            and query_categories
        ):
            document_text = cls._extract_document_text(source)

            category_found = False
            for categories in query_categories.values():
                if any(category in document_text for category in categories):
                    category_found = True
                    break

            # Если документ не содержит ни одного термина из категории запроса,
            # и оценка низкая, еще больше снижаем её
            if (
                not category_found
                and score < RELEVANCE_WEIGHTS['category_match'] * 0.5
            ):
                score *= 0.5

        normalized_score = min(score / RELEVANCE_WEIGHTS['max_score'], 1.0)

        return normalized_score

    @classmethod
    def _extract_document_text(cls, source: dict) -> str:
        """
        Извлекает весь текст из документа для комплексного анализа.

        Args:
            source: Исходный документ

        Returns:
            Весь текст документа в нижнем регистре
        """
        text_parts = []

        if 'title' in source:
            text_parts.append(source['title'].lower())

        if 'description' in source:
            text_parts.append(source['description'].lower())

        if 'positions' in source and source['positions']:
            for position in source['positions']:
                if 'name' in position:
                    text_parts.append(position['name'].lower())

                if (
                    'description' in position
                    and position['description']
                    and 'blocks' in position['description']
                ):
                    for block in position['description']['blocks']:
                        if 'data' in block:
                            if 'text' in block['data']:
                                text_parts.append(block['data']['text'].lower())
                            if 'items' in block['data'] and isinstance(
                                block['data']['items'],
                                list,
                            ):
                                for item in block['data']['items']:
                                    if isinstance(item, str):
                                        text_parts.append(item.lower())

        return ' '.join(text_parts)

    @classmethod
    def _evaluate_positions(
        cls,
        query: str,
        query_parts: list[str],
        source: dict,
    ) -> float:
        """
        Оценивает релевантность на основе позиций в документе.

        Args:
            query: Поисковый запрос (в нижнем регистре)
            query_parts: Запрос, разбитый на слова
            source: Исходный документ

        Returns:
            Оценка релевантности позиций (от 0.0 до max_score)
        """
        if 'positions' not in source or not source['positions']:
            return 0.0

        position_scores = []

        for position in source['positions']:
            position_score = cls._evaluate_single_position(
                query=query,
                query_parts=query_parts,
                position=position,
            )
            position_scores.append(position_score)

        return max(position_scores) if position_scores else 0.0

    @classmethod
    def _evaluate_single_position(
        cls,
        query: str,
        query_parts: list[str],
        position: dict,
    ) -> float:
        """
        Оценивает релевантность отдельной позиции.

        Args:
            query: Поисковый запрос (в нижнем регистре)
            query_parts: Запрос, разбитый на слова
            position: Данные позиции

        Returns:
            Оценка релевантности позиции (от 0.0 до max_score)
        """
        position_score = 0.0

        if 'name' in position:
            position_name = position['name'].lower()
            position_score = cls._evaluate_position_name(
                query=query,
                query_parts=query_parts,
                position_name=position_name,
            )

        if (
            position_score < RELEVANCE_WEIGHTS['exact_position_match']
            and 'spheres' in position
        ):
            spheres_score = cls._evaluate_position_spheres(query, position)
            position_score = max(position_score, spheres_score)

        return position_score

    @classmethod
    def _evaluate_position_name(
        cls,
        query: str,
        query_parts: list[str],
        position_name: str,
    ) -> float:
        """
        Оценивает релевантность названия позиции.

        Args:
            query: Поисковый запрос (в нижнем регистре)
            query_parts: Запрос, разбитый на слова
            position_name: Название позиции (в нижнем регистре)

        Returns:
            Оценка релевантности названия позиции
        """
        if query in position_name:
            return RELEVANCE_WEIGHTS['exact_position_match']

        matched_query_parts = [
            part
            for part in query_parts
            if part in position_name and len(part) > 2
        ]
        if matched_query_parts:
            term_weights = []
            for part in matched_query_parts:
                weight = (
                    TERM_WEIGHTS['common_term_position']
                    if part in COMMON_TERMS
                    else TERM_WEIGHTS['specific_term_position']
                )
                term_weights.append(weight)

            partial_score = RELEVANCE_WEIGHTS['partial_position_match'] * (
                sum(term_weights) / len(query_parts)
            )

            category_score = cls._check_tech_category_match(query, position_name)

            return max(partial_score, category_score)

        return cls._check_tech_category_match(query, position_name)

    @classmethod
    def _check_tech_category_match(cls, query: str, text: str) -> float:
        """
        Проверяет соответствие запроса и текста через категории технологий.

        Args:
            query: Поисковый запрос (в нижнем регистре)
            text: Текст для проверки (в нижнем регистре)

        Returns:
            Оценка релевантности на основе категорий
        """
        query = query.strip()
        text = text.strip()

        query_variants = make_query_variants(query)

        for tech, categories in TECH_CATEGORIES.items():
            tech_match = any(
                variant == tech or tech in variant for variant in query_variants
            )

            if tech_match:
                if any(category in text for category in categories):
                    return RELEVANCE_WEIGHTS['category_match']

                if tech in text:
                    return RELEVANCE_WEIGHTS['category_match']

        return 0.0

    @classmethod
    def _evaluate_position_spheres(cls, query: str, position: dict) -> float:
        """
        Оценивает релевантность сфер позиции.

        Args:
            query: Поисковый запрос (в нижнем регистре)
            position: Данные позиции

        Returns:
            Оценка релевантности сфер позиции
        """
        if 'spheres' not in position or not position['spheres']:
            return 0.0

        for sphere in position['spheres']:
            if 'caption' in sphere:
                sphere_caption = sphere['caption'].lower()

                # Проверка на соответствие технической категории в сферах
                for tech, categories in TECH_CATEGORIES.items():
                    if tech in query and any(
                        category in sphere_caption for category in categories
                    ):
                        return RELEVANCE_WEIGHTS['sphere_match']

        return 0.0

    @classmethod
    def _evaluate_title_description(cls, query: str, source: dict) -> float:
        """
        Оценивает релевантность на основе названия и описания стажировки.

        Args:
            query: Поисковый запрос (в нижнем регистре)
            source: Исходный документ

        Returns:
            Оценка релевантности названия и описания
        """
        score = 0.0

        if 'title' in source:
            title = source['title'].lower()

            # Если запрос полностью содержится в названии
            if query in title:
                # Убедимся, что это не случайное совпадение
                # Напр., запрос "front" может быть частью слова "confrontation"
                words = title.split()
                if query in words or any(
                    query == word or query + 's' == word for word in words
                ):
                    score = max(score, RELEVANCE_WEIGHTS['title_match'])
                else:
                    # Проверка на соответствие техническим категориям
                    tech_score = cls._check_tech_category_match(query, title)
                    # Уменьшаем вес для частичных совпадений
                    score = max(score, tech_score * 0.5)

        if 'description' in source:
            description = source['description'].lower()

            if query in description:
                words = description.split()
                if query in words or any(query + 's' == word for word in words):
                    score = max(score, RELEVANCE_WEIGHTS['description_match'])
                else:
                    tech_score = cls._check_tech_category_match(
                        query,
                        description,
                    )
                    score = max(score, tech_score * 0.3)

        return score


def calculate_result_relevance(query: str, result: dict) -> float:
    """
    Оценивает релевантность результата поиска для данного запроса.
    Функция-обертка для сохранения обратной совместимости.

    Args:
        query: Поисковый запрос
        result: Результат поиска

    Returns:
        Оценка релевантности (от 0.0 до 1.0)
    """
    return RelevanceCalculator.calculate_relevance(query, result)
