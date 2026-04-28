# Pokémon GO Discord Feed

Un backend profesional en Python con FastAPI para automatizar publicaciones de noticias y eventos de Pokémon GO en un canal de Discord usando webhooks.

## Características

- **Scraping automático**: Revisa fuentes configurables de noticias de Pokémon GO.
- **Categorización inteligente**: Clasifica automáticamente las publicaciones por tipo (Evento, Raid, Community Day, etc.).
- **Anti-duplicados**: Evita publicar la misma noticia dos veces.
- **Embeds bonitos**: Envía mensajes formateados con emojis y colores según la categoría.
- **Scheduler**: Revisa fuentes periódicamente.
- **API REST**: Endpoints para health check y pruebas manuales.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <url-del-repo>
   cd pokemon-go-discord-feed
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno:
   - Copia `.env.example` a `.env`
   - Edita `.env` con tus valores reales

5. Configura las fuentes en `config/sources.yaml`

## Configuración

### Crear Webhook en Discord

1. Ve a tu servidor de Discord.
2. Ve a Configuración del Servidor > Integraciones > Webhooks.
3. Crea un nuevo webhook para el canal deseado.
4. Copia la URL del webhook y pégala en `.env` como `DISCORD_WEBHOOK_URL`.

### Archivo .env

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
CHECK_INTERVAL_MINUTES=30
DATABASE_URL=sqlite+aiosqlite:///./pokemon_go_feed.db
```

### Agregar Nuevas Fuentes

Edita `config/sources.yaml` para agregar nuevas fuentes. Ejemplo:

```yaml
sources:
  - name: "Nueva Fuente"
    url: "https://ejemplo.com/rss"
    type: "rss"  # o "html"
    category_keywords:
      evento: "EVENTO"
      raid: "RAID"
```

Para fuentes HTML, agrega selectores CSS. Si la fuente usa enlaces directos a noticias, no siempre es necesario un `title_selector` o `url_selector`:
```yaml
selector: "main a[href^='/news/']"
# title_selector y url_selector son opcionales cuando el elemento seleccionado ya es el enlace
# summary_selector y image_selector también son opcionales
```

## Ejecución

### Localmente

```bash
python -m app.main
```

La API estará disponible en `http://localhost:8000`.

### Endpoints

- `GET /health`: Health check
- `POST /test-discord`: Envía un embed de prueba al webhook
- `POST /sync-feeds`: Fuerza una sincronización manual de todas las fuentes configuradas

### Docker (Opcional)

Crea un `Dockerfile` y `docker-compose.yml` si deseas.

## Pruebas

Ejecuta las pruebas:
```bash
pytest
```

## Estructura del Proyecto

```
pokemon-go-discord-feed/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   └── post.py
│   ├── services/
│   │   ├── fetcher.py
│   │   ├── parser.py
│   │   ├── classifier.py
│   │   ├── discord_webhook.py
│   │   ├── scheduler.py
│   │   └── feed_processor.py
│   ├── repositories/
│   │   └── post_repository.py
│   └── routers/
│       ├── health.py
│       └── test_discord.py
├── config/
│   └── sources.yaml
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Despliegue Futuro

- Cambia `DATABASE_URL` a PostgreSQL.
- Usa Docker para contenedorización.
- Despliega en servicios como Heroku, Railway o AWS.

## Contribuir

1. Fork el repo
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push y crea un PR

## Licencia

MIT