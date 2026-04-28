from typing import Dict


class Classifier:
    CATEGORY_MAPPING = {
        "EVENTO": "📅",
        "RAID": "⚔️",
        "COMMUNITY_DAY": "🌟",
        "SHINY": "✨",
        "INVESTIGACION": "🎯",
        "PVP": "🧪",
        "ANUNCIO_OFICIAL": "📢",
        "INFOGRAFIA": "🖼️",
        "OTRO": "📌",
    }

    @staticmethod
    def classify_post(post: Dict, keywords: Dict[str, str]) -> str:
        parts = [
            post.get('title', ''),
            post.get('summary', '') or '',
            ' '.join(post.get('sections', []) or []),
            ' '.join(post.get('highlights', []) or []),
            ' '.join(post.get('article_preview', []) or []),
        ]
        text = ' '.join(parts).lower()
        for keyword, category in keywords.items():
            if keyword.lower() in text:
                return category
        return "OTRO"

    @staticmethod
    def get_emoji(category: str) -> str:
        return Classifier.CATEGORY_MAPPING.get(category, "📌")

    @staticmethod
    def get_color(category: str) -> int:
        colors = {
            "EVENTO": 0xFF0000,
            "RAID": 0x00FF00,
            "COMMUNITY_DAY": 0xFFFF00,
            "SHINY": 0xFF00FF,
            "INVESTIGACION": 0x00FFFF,
            "PVP": 0xFFA500,
            "ANUNCIO_OFICIAL": 0x800080,
            "INFOGRAFIA": 0x008000,
            "OTRO": 0x808080,
        }
        return colors.get(category, 0x808080)
