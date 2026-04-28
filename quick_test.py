#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.getcwd())

print("=" * 60)
print("Prueba de carga de módulos...")
print("=" * 60)

try:
    print("\n1. Importando Fetcher...")
    from app.services.fetcher import Fetcher
    print("   ✅ Fetcher importado correctamente")
    
    print("\n2. Creando instancia de Fetcher...")
    fetcher = Fetcher()
    print(f"   ✅ {len(fetcher.sources)} fuentes cargadas")
    
    for i, source in enumerate(fetcher.sources, 1):
        print(f"   {i}. {source['name']} - {source['type']}")
    
    print("\n3. Script ejecutado con éxito")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
