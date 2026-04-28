import asyncio
import sys
sys.path.insert(0, 'e:\\Proyectos informaticos\\Discord\\pokemon-go-discord-feed')

from app.services.fetcher import Fetcher

async def test_sync():
    output = []
    output.append("🔄 Iniciando sincronización de fuentes...")
    output.append("-" * 60)
    
    try:
        fetcher = Fetcher()
        output.append(f"✅ Fuentes cargadas: {len(fetcher.sources)}")
        for source in fetcher.sources:
            output.append(f"  - {source['name']} ({source['type']})")
        
        output.append("\n📡 Obteniendo posts de todas las fuentes...")
        posts = await fetcher.fetch_all_sources()
        output.append(f"✅ Total de posts obtenidos: {len(posts)}")
        
        if posts:
            output.append("\n📰 Primeros 3 posts:")
            for i, post in enumerate(posts[:3], 1):
                output.append(f"\n{i}. {post['title']}")
                output.append(f"   URL: {post['url']}")
                output.append(f"   Fuente: {post['source']}")
                output.append(f"   Fecha: {post['date']}")
        else:
            output.append("⚠️  No se obtuvieron posts")
        
        output.append("\n" + "=" * 60)
    except Exception as e:
        output.append(f"❌ Error: {str(e)}")
        import traceback
        output.append(traceback.format_exc())
    
    # Write to file
    with open('test_output.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    # Also print
    print('\n'.join(output))

asyncio.run(test_sync())
