# Deploy en Railway

## Variables

Configura estas variables en Railway:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
CHECK_INTERVAL_MINUTES=5
DATABASE_URL=sqlite+aiosqlite:////data/pokemon_go_feed.db
```

## Notas

- No subas `.env`; Railway debe recibir las variables desde su panel.
- Railway debe ejecutar el `Dockerfile` del proyecto.
- Crea un Railway Volume montado en `/data` para que SQLite no se pierda en redeploys.
- La app debe responder en `/health`.
- El scheduler corre dentro de la app y revisa feeds cada `CHECK_INTERVAL_MINUTES`.

## Primer arranque

Despues del deploy, abre la URL publica de Railway y ejecuta una vez:

```powershell
Invoke-RestMethod -Method Post -Uri "https://TU-APP.up.railway.app/seed-feeds"
```

Luego publica manualmente las infografias recientes que quieras recuperar:

```powershell
Invoke-RestMethod -Method Post -Uri "https://TU-APP.up.railway.app/publish-recent-infographics?days=9&limit=10&force=true"
```
