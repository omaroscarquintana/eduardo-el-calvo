"""Filtro de seguridad para mensajes del chat y respuestas generadas."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
                       "7": "t", "@": "a", "$": "s", "!": "i", "|": "i"})

_URL_RE = re.compile(r"(https?://|www\.|\b[\w-]+\.(com|net|org|ly|gg|io|me|tv|link|xyz|co)\b)", re.I)
_MENCION_RE = re.compile(r"@\w+")
# Emojis y símbolos raros (se quitan para que la voz no lea cosas extrañas)
_RARO_RE = re.compile(r"[^\w\s¿?¡!.,;:'\"()\-áéíóúüñÁÉÍÓÚÜÑ]", re.UNICODE)


# Emojis con connotación sexual u ofensiva que se bloquean tal cual.
EMOJIS_PROHIBIDOS = set("🔞🍆🍑💦👅🖕🤬💩🔫🔪💊💉🍌")


def _sin_acentos(texto: str) -> str:
    # Conservamos la ñ como "n" (suficiente para comparar)
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, sin 'leet speak', solo letras y espacios."""
    t = _sin_acentos(texto.lower()).translate(_LEET)
    t = re.sub(r"[^a-z\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _colapsar(texto: str, maximo: int) -> str:
    """'puuuuto' -> 'puuto' (maximo=2) o 'puto' (maximo=1)."""
    return re.sub(r"(.)\1{%d,}" % maximo, lambda m: m.group(1) * maximo, texto)


class FiltroSeguridad:
    def __init__(self, ruta_lista: Path | None = None, bloquear_enlaces: bool = True):
        self.bloquear_enlaces = bloquear_enlaces
        self._patrones: list[re.Pattern] = []
        if ruta_lista and ruta_lista.exists():
            for linea in ruta_lista.read_text(encoding="utf-8").splitlines():
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                self.agregar(linea)

    def agregar(self, palabra: str) -> None:
        prefijo = palabra.endswith("*")
        base = normalizar(palabra.rstrip("*"))
        if not base:
            return
        cuerpo = r"\s+".join(re.escape(p) for p in base.split())
        patron = r"\b" + cuerpo + (r"" if prefijo else r"\b")
        self._patrones.append(re.compile(patron))

    @property
    def cantidad(self) -> int:
        return len(self._patrones)

    def es_ofensivo(self, texto: str) -> bool:
        if not texto:
            return False
        if any(c in EMOJIS_PROHIBIDOS for c in texto):
            return True
        n = normalizar(texto)
        variantes = {n, _colapsar(n, 2), _colapsar(n, 1)}
        variantes |= {v.replace("v", "u") for v in list(variantes)}  # "pvto" -> "puto"
        return any(p.search(v) for p in self._patrones for v in variantes)

    def tiene_enlace(self, texto: str) -> bool:
        return bool(_URL_RE.search(texto or ""))

    def es_seguro(self, texto: str) -> bool:
        if self.es_ofensivo(texto):
            return False
        if self.bloquear_enlaces and self.tiene_enlace(texto):
            return False
        return True


def limpiar_para_cita(texto: str, largo_maximo: int) -> str:
    """Prepara el mensaje del espectador para citarlo en voz alta."""
    t = _MENCION_RE.sub("", texto or "")
    t = _RARO_RE.sub(" ", t)
    t = t.replace('"', "'")
    t = re.sub(r"\s+", " ", t).strip(" .,;:¿?¡!")
    if len(t) > largo_maximo:
        t = t[:largo_maximo].rsplit(" ", 1)[0] + "..."
    return t


def limpiar_nombre(nombre: str) -> str:
    """Quita emojis y símbolos del apodo para que la voz lo pueda decir."""
    t = _RARO_RE.sub(" ", nombre or "")
    t = re.sub(r"[_\.]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:30].strip()
