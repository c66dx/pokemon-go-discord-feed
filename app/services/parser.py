import re
from typing import Dict, Optional
from datetime import datetime

class Parser:
    MONTH_TRANSLATIONS = {
        'ene': 'Jan', 'enero': 'Jan',
        'feb': 'Feb', 'febrero': 'Feb',
        'mar': 'Mar', 'marzo': 'Mar',
        'abr': 'Apr', 'abril': 'Apr',
        'may': 'May',
        'jun': 'Jun', 'junio': 'Jun',
        'jul': 'Jul', 'julio': 'Jul',
        'ago': 'Aug', 'agosto': 'Aug',
        'sep': 'Sep', 'sept': 'Sep', 'septiembre': 'Sep',
        'oct': 'Oct', 'octubre': 'Oct',
        'nov': 'Nov', 'noviembre': 'Nov',
        'dic': 'Dec', 'diciembre': 'Dec'
    }

    @staticmethod
    def parse_post(post: Dict) -> Dict:
        date_value = post.get('date')
        if isinstance(date_value, str):
            post['date'] = Parser.parse_date_string(date_value) or datetime.utcnow()
        elif date_value is None:
            post['date'] = datetime.utcnow()
        return post

    @staticmethod
    def parse_date_string(value: str) -> Optional[datetime]:
        if not value:
            return None

        normalized = Parser.normalize_month_names(value.strip())
        patterns = [
            '%b %d, %Y',
            '%B %d, %Y',
            '%d %b %Y',
            '%d %B %Y',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d'
        ]

        for pattern in patterns:
            try:
                return datetime.strptime(normalized, pattern)
            except ValueError:
                continue

        return None

    @staticmethod
    def normalize_month_names(value: str) -> str:
        normalized = value.lower()
        for spanish, english in Parser.MONTH_TRANSLATIONS.items():
            normalized = re.sub(rf'\b{spanish}\b', english, normalized, flags=re.IGNORECASE)
        return normalized
