import httpx
from app.core.config import settings
from app.services.classifier import Classifier
from typing import Dict
import logging
from datetime import datetime
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

async def send_embed(post: Dict):
    if not settings.discord_webhook_url or not settings.discord_webhook_url.startswith(("http://", "https://")):
        logger.warning("Discord webhook URL is not configured; skipping notification")
        return

    if post.get('category') == 'INFOGRAFIA':
        await send_infographic(post)
        return

    description = post.get('summary') or post.get('title', '')
    description = truncate_text(description, 900)

    embed = {
        "title": f"{Classifier.get_emoji(post['category'])} {post['title']}",
        "description": description,
        "url": post['url'],
        "color": Classifier.get_color(post['category']),
        "fields": build_embed_fields(post),
        "footer": {
            "text": f"Pokemon GO Feed | {post.get('source', 'Fuente desconocida')}"
        }
    }
    if post.get('image_url'):
        embed["image"] = {"url": post['image_url']}
    if post.get('official_image_url') and post.get('infographic'):
        embed["thumbnail"] = {"url": post['official_image_url']}

    payload = {"embeds": [embed]}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(settings.discord_webhook_url, json=payload)
        response.raise_for_status()

async def send_infographic(post: Dict):
    image_url = post.get('image_url')
    if not image_url:
        embed = build_infographic_embed(post)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.discord_webhook_url, json={"embeds": [embed]})
            response.raise_for_status()
        return

    content = build_infographic_content(post)
    filename = image_filename_from_url(image_url)

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        try:
            image_response = await client.get(image_url)
            image_response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning("Could not download infographic image %s: %s", image_url, exc)
            embed = build_infographic_embed(post)
            response = await client.post(settings.discord_webhook_url, json={"embeds": [embed]})
            response.raise_for_status()
            return

        payload = {
            "content": content,
            "allowed_mentions": {"parse": []},
            "flags": 4,
        }
        files = {
            "files[0]": (
                filename,
                image_response.content,
                image_response.headers.get("content-type", "image/png"),
            )
        }
        response = await client.post(
            settings.discord_webhook_url,
            data={"payload_json": json.dumps(payload)},
            files=files,
        )
        response.raise_for_status()

def build_infographic_content(post: Dict) -> str:
    infographic = post.get('infographic') or {}
    source_url = infographic.get('url') or post['url']
    author = infographic.get('author')

    lines = [f"**{post['title']}**"]
    if author:
        lines.append(f"Fuente: r/TheSilphRoad por {author}")
    else:
        lines.append("Fuente: r/TheSilphRoad")
    lines.append(f"Post original: {source_url}")
    return "\n".join(lines)

def image_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    filename = path.rsplit("/", 1)[-1] or "infographic.png"
    if "." not in filename:
        filename += ".png"
    return filename

def build_infographic_embed(post: Dict) -> Dict:
    infographic = post.get('infographic') or {}
    author = infographic.get('author')
    source_url = infographic.get('url') or post['url']

    description_parts = []
    if author:
        description_parts.append(f"Fuente: r/TheSilphRoad por {author}")
    else:
        description_parts.append("Fuente: r/TheSilphRoad")
    description_parts.append(f"[Ver post original]({source_url})")

    embed = {
        "title": f"{Classifier.get_emoji('INFOGRAFIA')} {post['title']}",
        "description": "\n".join(description_parts),
        "url": source_url,
        "color": Classifier.get_color('INFOGRAFIA'),
        "fields": [
            {
                "name": "Publicado",
                "value": format_discord_datetime(post.get('date')),
                "inline": True,
            }
        ],
        "footer": {
            "text": "Pokemon GO Feed | Infografia comunitaria"
        },
    }

    if post.get('image_url'):
        embed["image"] = {"url": post['image_url']}

    return embed

def build_embed_fields(post: Dict) -> list[Dict]:
    fields = [
        {
            "name": "Categoria",
            "value": post.get('category', 'OTRO'),
            "inline": True
        },
        {
            "name": "Publicado",
            "value": format_discord_datetime(post.get('date')),
            "inline": True
        }
    ]

    if post.get('date_modified'):
        fields.append({
            "name": "Actualizado",
            "value": format_discord_datetime(post['date_modified']),
            "inline": True
        })

    sections = post.get('sections') or []
    if sections:
        fields.append({
            "name": "Secciones principales",
            "value": truncate_text('\n'.join(f"- {section}" for section in sections), 1024),
            "inline": False
        })

    highlights = post.get('highlights') or []
    if highlights:
        fields.append({
            "name": "Puntos clave",
            "value": truncate_text('\n'.join(f"- {item}" for item in highlights), 1024),
            "inline": False
        })

    infographic = post.get('infographic')
    if infographic:
        source_text = infographic.get('source', 'Fuente externa')
        author = infographic.get('author')
        title = infographic.get('title')
        url = infographic.get('url')
        label = f"{source_text}"
        if author:
            label += f" por {author}"
        if title and url:
            label += f"\n[{truncate_text(title, 180)}]({url})"
        fields.append({
            "name": "Infografia",
            "value": truncate_text(label, 1024),
            "inline": False
        })

    return fields[:6]

def format_discord_datetime(value) -> str:
    if isinstance(value, datetime):
        return f"<t:{int(value.timestamp())}:F>"
    if value:
        return str(value)
    return "Sin fecha"

def truncate_text(value: str, limit: int) -> str:
    value = (value or '').strip()
    if len(value) <= limit:
        return value
    return value[:limit - 3].rstrip() + "..."

async def send_test_embed():
    if not settings.discord_webhook_url or not settings.discord_webhook_url.startswith(("http://", "https://")):
        logger.warning("Discord webhook URL is not configured; skipping test notification")
        return

    embed = {
        "title": "🧪 Prueba de Webhook",
        "description": "Este es un mensaje de prueba para verificar que el webhook de Discord funciona correctamente.",
        "color": 0x00FF00,
        "footer": {
            "text": "Pokémon GO Discord Feed"
        }
    }
    payload = {"embeds": [embed]}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(settings.discord_webhook_url, json=payload)
        response.raise_for_status()
