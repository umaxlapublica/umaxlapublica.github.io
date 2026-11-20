#!/usr/bin/env python3
"""Genera actas/index.html: una página con todas las actas cifradas con contraseña.

Las actas en claro viven en actas-fuente/ (no se sube a git, ver .gitignore):

    actas-fuente/Explicaciones actas.txt
    actas-fuente/2025/2025-05-09 (umaxlapublica).txt
    actas-fuente/2026/2026-10-14 (asamblea provincial).txt
    ...

Se cifran con AES-256-GCM, con la clave derivada de la contraseña (PBKDF2-SHA256).
El descifrado ocurre en el navegador, así que el HTML publicado no contiene las actas legibles.

Uso:  python herramientas/build_actas.py
La contraseña se pide por teclado, o se toma de la variable de entorno ACTAS_PASSWORD.
Requiere:  pip install cryptography
"""
import base64
import getpass
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    sys.exit("Falta la librería 'cryptography'. Instálala con:  pip install cryptography")

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "actas-fuente"
SALIDA = RAIZ / "actas" / "index.html"
PLANTILLA = Path(__file__).with_name("actas_plantilla.html")
INTRO = "Explicaciones actas.txt"
ITERACIONES = 600_000
NOMBRE = re.compile(r"^(\d{4}-\d{2}-\d{2}) \((.+)\)\.txt$")


def leer(ruta):
    return ruta.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip() + "\n"


def cargar_actas():
    actas, ids = [], set()
    for ruta in sorted(FUENTE.rglob("*.txt"), key=lambda p: p.name):
        if ruta.name == INTRO:
            continue
        m = NOMBRE.match(ruta.name)
        if not m:
            sys.exit(f"Nombre no válido (esperado 'aaaa-mm-dd (tipo).txt'): {ruta.name}")
        fecha, tipo = m.group(1), m.group(2).strip().lower()
        base = fecha + "-" + re.sub(r"[^a-z0-9]+", "-", tipo).strip("-")
        id_, n = base, 2
        while id_ in ids:
            id_, n = f"{base}-{n}", n + 1
        ids.add(id_)
        actas.append({"id": id_, "date": fecha, "type": tipo, "text": leer(ruta)})
    actas.sort(key=lambda a: (a["date"], a["id"]))
    return actas


def pedir_contrasena():
    clave = os.environ.get("ACTAS_PASSWORD")
    if clave is None:
        clave = getpass.getpass("Contraseña para las actas: ")
        if clave != getpass.getpass("Repite la contraseña: "):
            sys.exit("Las contraseñas no coinciden.")
    if len(clave) < 8:
        sys.exit("La contraseña es demasiado corta (mínimo 8 caracteres; mejor una frase larga).")
    return unicodedata.normalize("NFC", clave)


def cifrar(datos, clave):
    sal, nonce = os.urandom(16), os.urandom(12)
    k = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, ITERACIONES, 32)
    ct = AESGCM(k).encrypt(nonce, json.dumps(datos, ensure_ascii=False).encode("utf-8"), None)
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return {"iter": ITERACIONES, "salt": b64(sal), "iv": b64(nonce), "ct": b64(ct)}


def main():
    if not (FUENTE / INTRO).exists():
        sys.exit(f"No encuentro {FUENTE / INTRO}")
    actas = cargar_actas()
    if not actas:
        sys.exit(f"No hay actas en {FUENTE}")
    clave = pedir_contrasena()
    carga = cifrar({"intro": leer(FUENTE / INTRO), "actas": actas}, clave)
    html = PLANTILLA.read_text(encoding="utf-8").replace("__PAYLOAD__", json.dumps(carga))
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(html, encoding="utf-8")
    print(f"OK: {len(actas)} actas cifradas en {SALIDA.relative_to(RAIZ)} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
