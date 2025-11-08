"""
Crear repositorio en GitHub usando la API

NOTA: Este archivo es un TEMPLATE
Para usarlo:
1. Copia este archivo: cp create_github_repo.template.py create_github_repo.py
2. Edita create_github_repo.py y añade tu token real
3. NO hagas commit de create_github_repo.py (está en .gitignore)
"""
import requests
import json
import os

# Credenciales - USAR VARIABLES DE ENTORNO
GITHUB_USER = os.getenv("GITHUB_USER", "tu_usuario")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "ghp_TU_TOKEN_AQUI")
REPO_NAME = "tradeplus-python"

if GITHUB_TOKEN == "ghp_TU_TOKEN_AQUI":
    print("⚠️  ERROR: Debes configurar tu GITHUB_TOKEN")
    print("Opción 1: Variable de entorno")
    print("  export GITHUB_TOKEN=ghp_tu_token_real")
    print("Opción 2: Editar este archivo (NO hacer commit)")
    exit(1)

# Crear el repo
url = "https://api.github.com/user/repos"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

data = {
    "name": REPO_NAME,
    "description": "TradePlus - Sistema de trading multi-broker con journal en tiempo real",
    "private": False,
    "has_issues": True,
    "has_projects": True,
    "has_wiki": False
}

print(f"Creando repositorio: {REPO_NAME}")
response = requests.post(url, headers=headers, json=data)

if response.status_code == 201:
    repo_data = response.json()
    print(f"✅ Repositorio creado: {repo_data['html_url']}")
    print(f"Clone URL: {repo_data['clone_url']}")
elif response.status_code == 422:
    print(f"⚠️  El repositorio ya existe")
else:
    print(f"❌ Error {response.status_code}: {response.text}")
