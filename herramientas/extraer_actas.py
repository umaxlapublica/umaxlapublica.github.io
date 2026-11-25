#!/usr/bin/env python3
"""Recupera en actas-fuente/ las actas que están en actas/index.html pero no en txt.

Descifra la página publicada con la contraseña y escribe un txt por cada acta que
no tenga ya su archivo 'aaaa-mm-dd (tipo).txt' (no sobrescribe nada). Sirve para
tener en txt todas las actas antes de regenerar la web con build_actas.py.

Uso:  python herramientas/extraer_actas.py
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
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    sys.exit("Falta la librería 'cryptography'. Instálala con:  pip install cryptography")

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "actas-fuente"
PAGINA = RAIZ / "actas" / "index.html"


def main():
    m = re.search(r"const P = (\{.*?\});", PAGINA.read_text(encoding="utf-8"), re.S)
    if not m:
        sys.exit(f"No encuentro los datos cifrados en {PAGINA}")
    carga = json.loads(m.group(1))

    clave = os.environ.get("ACTAS_PASSWORD") or getpass.getpass("Contraseña de las actas: ")
    clave = unicodedata.normalize("NFC", clave)
    b = base64.b64decode
    k = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), b(carga["salt"]), carga["iter"], 32)
    try:
        datos = json.loads(AESGCM(k).decrypt(b(carga["iv"]), b(carga["ct"]), None))
    except InvalidTag:
        sys.exit("Contraseña incorrecta.")

    existentes = {p.name for p in FUENTE.rglob("*.txt")}
    nuevas = 0
    for a in datos["actas"]:
        nombre = f"{a['date']} ({a['type']}).txt"
        if nombre in existentes:
            continue
        destino = FUENTE / a["date"][:4] / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(a["text"], encoding="utf-8")
        print("Recuperada:", destino.relative_to(RAIZ))
        nuevas += 1
    print(f"{nuevas} actas recuperadas de {len(datos['actas'])} en la web.")


if __name__ == "__main__":
    main()
