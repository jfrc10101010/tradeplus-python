"""
Crear repositorio en GitHub usando la API
"""
import requests
import json

# Credenciales
GITHUB_USER = "jfrc10101010"
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN_HERE"  # ⚠️ NO COMMITEAR TOKEN REAL
REPO_NAME = "tradeplus-python"

# Crear el repo
url = "https://api.github.com/user/repos"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

data = {
    "name": REPO_NAME,
    "description": "TradePlus - Dual broker trading API hub (Coinbase + Schwab)",
    "private": False,
    "auto_init": False
}

print(f"Creando repositorio: {REPO_NAME}")
print(f"URL: https://api.github.com/user/repos")

response = requests.post(url, headers=headers, json=data)

print(f"Status: {response.status_code}")

if response.status_code == 201:
    repo_data = response.json()
    print(f"\n✅ Repositorio creado exitosamente!")
    print(f"   URL: {repo_data['html_url']}")
    print(f"   Clone URL: {repo_data['clone_url']}")
    print(f"   SSH URL: {repo_data['ssh_url']}")
    
    # Guardar en archivo
    with open("github_repo_info.json", "w") as f:
        json.dump({
            "name": repo_data["name"],
            "url": repo_data["html_url"],
            "clone_url": repo_data["clone_url"],
            "ssh_url": repo_data["ssh_url"]
        }, f, indent=2)
    
    print(f"\n✅ Información guardada en github_repo_info.json")
else:
    print(f"\n❌ Error creando repositorio:")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
