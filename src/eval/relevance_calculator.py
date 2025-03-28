from eval.tech_categories import (
    COMMON_TERMS,
    RELEVANCE_WEIGHTS,
    TECH_CATEGORIES,
    TERM_WEIGHTS,
)


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

        normalized_score = min(score / RELEVANCE_WEIGHTS['max_score'], 1.0)

        return normalized_score

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
        for tech, categories in TECH_CATEGORIES.items():
            if tech in query:
                if any(category in text for category in categories):
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

        if 'title' in source and query in source['title'].lower():
            score = max(score, RELEVANCE_WEIGHTS['title_match'])

        if 'description' in source and query in source['description'].lower():
            score = max(score, RELEVANCE_WEIGHTS['description_match'])

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
