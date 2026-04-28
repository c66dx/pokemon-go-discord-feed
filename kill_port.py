import os
import subprocess

# Kill all Python processes on Windows
result = subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True, text=True)
print("Procesos Python detenidos")
print(result.stdout)
