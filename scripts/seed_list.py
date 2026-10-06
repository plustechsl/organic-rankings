import argparse
import os
import re
import sys

import requests
from ddgs import DDGS


def load_env(path=".env"):
    config = {}
    if not os.path.exists(path):
        return config
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config


ENV = load_env()
API_URL = ENV.get("API_URL", "http://localhost:8000")


def login():
    username = ENV.get("ADMIN_USERNAME")
    password = ENV.get("ADMIN_PASSWORD")

    if not username or not password:
        print("Error: falta ADMIN_USERNAME o ADMIN_PASSWORD en .env")
        sys.exit(1)

    response = requests.post(
        f"{API_URL}/auth/login",
        json={"username": username, "password": password},
    )

    if response.status_code != 200:
        print(f"Error al hacer login: {response.status_code} {response.text}")
        sys.exit(1)

    return response.json()["access_token"]


def api_get(token, path):
    r = requests.get(f"{API_URL}{path}", headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json()


def api_post(token, path, payload):
    r = requests.post(
        f"{API_URL}{path}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if r.status_code >= 400:
        print(f"  ! Error en POST {path}: {r.status_code} {r.text}")
        return None
    return r.json()


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[àáâãäå]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ñ]", "n", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def search_topic(topic, max_results=8):
    print(f"Buscando resultados para '{topic}'...")
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(topic, max_results=max_results):
            title = r.get("title", "").strip()
            url = r.get("href", "").strip()
            body = r.get("body", "").strip()

            if not title or not url:
                continue

            results.append({
                "title": title[:200],
                "url": url[:1000],
                "description": body[:500] if body else None,
            })

    return results


def build_list_description(topic, results, max_length=280):
    sentences = []
    for r in results:
        if not r["description"]:
            continue
        first_sentence = re.split(r"(?<=[.!?])\s", r["description"])[0]
        first_sentence = first_sentence.strip()
        if len(first_sentence) > 15:
            sentences.append(first_sentence)

    if not sentences:
        return (
            f"Una seleccion de recursos sobre {topic}, "
            f"recopilados automaticamente para que la comunidad los valore."
        )

    summary = ""
    for s in sentences:
        candidate = (summary + " " + s).strip() if summary else s
        if len(candidate) > max_length:
            break
        summary = candidate

    if not summary:
        summary = sentences[0][:max_length]

    return summary


def find_or_create_category(token, category_name):
    categories = api_get(token, "/categories")

    def search_tree(nodes):
        for node in nodes:
            if node["name"].lower() == category_name.lower():
                return node
            found = search_tree(node.get("children", []))
            if found:
                return found
        return None

    found = search_tree(categories)
    if found:
        print(f"Categoria existente: {found['name']} (id={found['id']})")
        return found["id"]

    print(f"Creando categoria nueva: {category_name}")
    created = api_post(token, "/categories", {"name": category_name})
    if not created:
        print("No se pudo crear la categoria.")
        sys.exit(1)

    return created["id"]


def derive_tags_from_topic(topic):
    stopwords = {"de", "la", "el", "los", "las", "en", "con", "para", "y", "a"}
    words = re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9]+", topic.lower())
    tags = [w for w in words if w not in stopwords and len(w) > 2]
    return tags[:5]

def create_list_with_links(token, topic, category_id, max_results):
    results = search_topic(topic, max_results=max_results)

    if not results:
        print("No se encontraron resultados para ese tema.")
        sys.exit(1)

    description = build_list_description(topic, results)

    print(f"Creando lista '{topic}'...")
    new_list = api_post(token, "/lists", {
        "title": topic,
        "description": description,
        "category_id": category_id,
    })

    if not new_list:
        print("No se pudo crear la lista.")
        sys.exit(1)

    print(f"  Lista creada: {new_list['title']} (slug={new_list['slug']})")

    tags = derive_tags_from_topic(topic)
    created_count = 0
    for r in results:
        link = api_post(token, "/links", {
            "list_id": new_list["id"],
            "title": r["title"],
            "url": r["url"],
            "description": r["description"],
        })

        if link:
            created_count += 1
            print(f"  + {link['title']}")

            if tags:
                api_post(token, f"/links/{link['id']}/tags", {"tags": tags})

    print(f"\nListo. {created_count}/{len(results)} enlaces creados en '{topic}'.")
    print(f"Ver en: http://localhost:3000/lists/{new_list['slug']}")


def main():
    parser = argparse.ArgumentParser(
        description="Crea una lista con enlaces encontrados automaticamente sobre un tema."
    )
    parser.add_argument("topic", help="Tema de la lista, ej: 'herramientas de ia'")
    parser.add_argument(
        "--category",
        required=True,
        help="Nombre de la categoria (se crea si no existe)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=8,
        help="Numero maximo de enlaces a crear (por defecto 8)",
    )

    args = parser.parse_args()

    token = login()
    category_id = find_or_create_category(token, args.category)
    create_list_with_links(token, args.topic, category_id, args.max_results)


if __name__ == "__main__":
    main()
