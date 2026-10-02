"""Disfraces, gestos y ruleta de Eduardo (nombres, palabras que los activan y etiquetas de la IA)."""
from __future__ import annotations

import random
import re
import unicodedata


def plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c)).strip(" .,;:!?¡¿")


# clave (la usa el avatar) -> (cómo se dice, palabras que lo piden)
DISFRACES: dict[str, tuple[str, list[str]]] = {
    "fiesta":   ("gorro de fiesta",   ["fiesta", "cumple", "cumpleanos", "party", "gorrito", "gorro de fiesta"]),
    "sombrero": ("sombrero mexicano", ["sombrero", "mexicano", "charro", "mariachi", "sombrero mexicano"]),
    "lentes":   ("lentes de sol",     ["lentes", "gafas", "anteojos", "lentes de sol", "gafas de sol"]),
    "corona":   ("corona de rey",     ["corona", "rey", "reina", "realeza"]),
    "peluca":   ("peluca chistosa",   ["peluca", "pelo", "payaso", "afro", "cabello", "peluca chistosa"]),
    "bigote":   ("bigote falso",      ["bigote", "mostacho", "bigotes", "bigote falso"]),
    "gorra":    ("gorra",             ["gorra", "cachucha", "visera", "gorra de beisbol"]),
    "santa":    ("gorro de Santa",    ["santa", "navidad", "navideno", "papa noel", "santa claus", "gorro de santa"]),
}

# clave -> (cómo se dice, sub-comandos que lo activan, duración en segundos)
GESTOS: dict[str, tuple[str, list[str], float]] = {
    "enojo":    ("enojo fingido",    ["enojate", "enojado", "enojo", "bravo", "furioso", "enfadate", "enfadado"], 3.5),
    "sorpresa": ("sorpresa",         ["sorpresa", "sorprendete", "sorprendido", "asombro", "asombrate"], 3.0),
    "guino":    ("guiño",            ["guino", "guina", "guinale", "guiname", "guinanos", "guinar"], 2.5),
    "baile":    ("baile",            ["baila", "bailar", "baile", "bailecito", "bailate", "danza"], 6.0),
    "saludo":   ("saludo con la mano", ["saluda", "saludo", "saludame", "saludanos", "saludar"], 3.5),
    "triste":   ("triste dramático", ["triste", "llora", "llorar", "drama", "dramatico", "lloron"], 4.5),
}

# Lo que la IA puede escribir: [gesto:sorpresa]  (también acepta variantes con tilde, etc.)
ALIAS_GESTO_IA = {"enojo": "enojo", "enojado": "enojo", "enfado": "enojo", "sorpresa": "sorpresa",
                  "sorprendido": "sorpresa", "guino": "guino", "guinar": "guino", "baile": "baile",
                  "bailar": "baile", "saludo": "saludo", "saludar": "saludo", "triste": "triste",
                  "tristeza": "triste", "llorar": "triste"}
_ETIQUETA_GESTO = re.compile(r"\[\s*(?:gesto|gesture|accion)\s*[:=]\s*([^\]\n]{1,24})\]", re.I)
_OTRAS_ETIQUETAS = re.compile(r"\[\s*(?!risa\b|laughs?\b)[a-záéíóúñ]{2,12}\s*(?:[:=][^\]\n]{0,24})?\]", re.I)

# Ruleta: clave -> nombre en la rueda
CATEGORIAS_RULETA: dict[str, str] = {
    "reto": "Reto",
    "piropo": "Piropo calvo",
    "burla": "Burla amistosa",
    "chiste": "Chiste dedicado",
    "animal": "Imitación de animal",
}


def buscar_disfraz(texto: str) -> str | None:
    """'sombrero mexicano' -> 'sombrero'.  '' -> None."""
    t = plano(texto)
    if not t:
        return None
    if t in DISFRACES:
        return t
    for clave, (_, palabras) in DISFRACES.items():
        if t in palabras:
            return clave
    for clave, (_, palabras) in DISFRACES.items():   # "ponte la corona porfa"
        if any(re.search(rf"\b{re.escape(p)}\b", t) for p in palabras):
            return clave
    return None


def disfraz_al_azar(evitar: str = "") -> str:
    return random.choice([k for k in DISFRACES if k != evitar] or list(DISFRACES))


def buscar_gesto(palabra: str) -> str | None:
    p = plano(palabra)
    for clave, (_, palabras, _) in GESTOS.items():
        if p == clave or p in palabras:
            return clave
    return None


def extraer_gesto(texto: str) -> tuple[str, str]:
    """Quita las etiquetas [gesto:x] del texto. Devuelve (texto limpio, gesto o '')."""
    gesto = ""
    for m in _ETIQUETA_GESTO.finditer(texto or ""):
        g = ALIAS_GESTO_IA.get(plano(m.group(1)).split()[0] if plano(m.group(1)) else "", "")
        if g and not gesto:
            gesto = g
    t = _ETIQUETA_GESTO.sub(" ", texto or "")
    t = _OTRAS_ETIQUETAS.sub(" ", t)          # cualquier otra etiqueta rara que no se debe leer
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    return re.sub(r"\s{2,}", " ", t).strip(), gesto


def duracion_gesto(gesto: str) -> float:
    return GESTOS.get(gesto, ("", [], 3.0))[2]
