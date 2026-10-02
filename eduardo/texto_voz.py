"""Prepara el texto para que la voz suene natural (sin emojis, sin cifras, sin abreviaturas,
risas como risa de verdad) y lo divide en trozos de voz y de risa."""
from __future__ import annotations

import re
import unicodedata

MARCA_RISA = "[risa]"
RISA_VISIBLE = "¡Ja, ja, ja!"   # cómo se escribe la risa en la burbuja y en la consola

# ------------------------------------------------------------------ risas
_RISA_PATRONES = [
    r"\[\s*(?:risas?|r[ií]e|se r[ií]e|carcajadas?|laughs?|laughing|chuckles?)\s*\]",
    r"\(\s*(?:risas?|r[ií]e|se r[ií]e|carcajadas?)\s*\)",
    r"\*\s*(?:risas?|r[ií]e|se r[ií]e|carcajadas?)\s*\*",
    # ¡Ja, ja, ja!  / ja ja ja / JAJAJA / jajaja / jeje / jsjsjs / jiji (al menos 2 "ja")
    r"¡*\s*\b(?:j[aeiu]h?)(?:[\s,.!¡-]*j[aeiu]h?\b)+[\s!.]*",
    r"¡*\s*\bj+[aeiu]+(?:j+[aeiu]+)+j*\b[\s!.]*",
    r"\bj+s+(?:j+s+)+j*\b",
    r"\bx+d+\b",
    r"\b(?:lol|lmao|lmfao)\b",
]
_RISA_RE = re.compile("|".join(f"(?:{p})" for p in _RISA_PATRONES), re.I)
_MARCAS_JUNTAS = re.compile(r"(?:\[risa\][\s,.!¡?¿]*){2,}")


def marcar_risas(texto: str, maximo: int = 2) -> str:
    """Convierte cualquier forma de risa ('jajaja', '[risa]', '(risas)', 'xD'...) en [risa]."""
    t = _RISA_RE.sub(f" {MARCA_RISA} ", texto)
    t = _MARCAS_JUNTAS.sub(f"{MARCA_RISA} ", t)
    if t.count(MARCA_RISA) > maximo:
        partes = t.split(MARCA_RISA)
        t = MARCA_RISA.join(partes[:maximo]) + MARCA_RISA + "".join(partes[maximo:])
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    t = re.sub(r"[¡¿]\s*(?=\[risa\])", "", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def risas_visibles(texto: str) -> str:
    """Para mostrar: '[risa]' y 'jajaja' -> '¡Ja, ja, ja!' (así también lo entiende el avatar)."""
    t = marcar_risas(texto)
    t = t.replace(MARCA_RISA, RISA_VISIBLE)
    t = re.sub(r"(¡Ja, ja, ja!)\s*[.!]+", r"\1", t)
    return re.sub(r"\s{2,}", " ", t).strip()


# ---------------------------------------------------------------- números
_UNIDADES = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
             "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho",
             "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco",
             "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_DECENAS = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta", 70: "setenta",
            80: "ochenta", 90: "noventa"}
_CENTENAS = {100: "ciento", 200: "doscientos", 300: "trescientos", 400: "cuatrocientos",
             500: "quinientos", 600: "seiscientos", 700: "setecientos", 800: "ochocientos",
             900: "novecientos"}


def numero_a_palabras(n: int) -> str:
    if n < 0:
        return "menos " + numero_a_palabras(-n)
    if n < 30:
        return _UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _DECENAS[d * 10] + ("" if u == 0 else " y " + _UNIDADES[u])
    if n == 100:
        return "cien"
    if n < 1000:
        c, r = divmod(n, 100)
        return _CENTENAS[c * 100] + ("" if r == 0 else " " + numero_a_palabras(r))
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        pre = "mil" if m == 1 else numero_a_palabras(m).replace("uno", "un") + " mil"
        pre = re.sub(r"veintiun mil$", "veintiún mil", pre)
        return pre + ("" if r == 0 else " " + numero_a_palabras(r))
    if n < 1_000_000_000:
        m, r = divmod(n, 1_000_000)
        pre = "un millón" if m == 1 else numero_a_palabras(m).replace("uno", "un") + " millones"
        return pre + ("" if r == 0 else " " + numero_a_palabras(r))
    return " ".join(numero_a_palabras(int(c)) for c in str(n))


def _numeros(t: str) -> str:
    t = re.sub(r"\b(\d{1,2}):(\d{2})\b",
               lambda m: numero_a_palabras(int(m[1])) + ("" if m[2] == "00" else " y " + numero_a_palabras(int(m[2]))), t)
    t = re.sub(r"(\d+)\s*%", lambda m: m[1] + " por ciento", t)
    t = re.sub(r"\$\s*(\d[\d.,]*)", lambda m: m[1] + " dólares", t)
    t = re.sub(r"\b(\d+)[ºª°]\s*", lambda m: {"1": "primero ", "2": "segundo ", "3": "tercero "}.get(m[1], m[1] + " "), t)
    t = re.sub(r"\b(\d{1,3}(?:[.,]\d{3})+)\b(?![.,]\d)", lambda m: re.sub(r"[.,]", "", m[1]), t)  # 1.000 -> 1000
    t = re.sub(r"\b(\d+)[.,](\d+)\b", lambda m: numero_a_palabras(int(m[1])) + " punto " +
               " ".join(numero_a_palabras(int(c)) for c in m[2]) if len(m[2]) > 2 else
               numero_a_palabras(int(m[1])) + " punto " + numero_a_palabras(int(m[2])), t)
    t = re.sub(r"(?<![\w])(\d{1,12})(?![\w])", lambda m: numero_a_palabras(int(m[1])), t)
    return t


# ------------------------------------------------------- abreviaturas y otros
_ABREVIATURAS = {
    "q": "que", "k": "que", "xq": "porque", "pq": "porque", "porq": "porque", "tb": "también",
    "tmb": "también", "tbn": "también", "x": "por", "xfa": "por favor", "xfavor": "por favor",
    "pls": "por favor", "plis": "por favor", "dnd": "donde", "bn": "bien", "msj": "mensaje",
    "slds": "saludos", "ntp": "no te preocupes", "tqm": "te quiero mucho", "tkm": "te quiero mucho",
    "bb": "bebé", "d": "de", "ok": "okey", "okay": "okey", "omg": "¡Dios mío!", "vs": "contra",
    "etc": "etcétera", "sr": "señor", "sra": "señora", "srta": "señorita", "dr": "doctor",
    "aprox": "aproximadamente", "info": "información", "admin": "administrador",
}
# Palabras en inglés frecuentes en un live, escritas como suenan en español.
_INGLES = {
    "live": "laiv", "lives": "laivs", "bye": "bai", "cool": "cul", "nice": "nais", "sorry": "sori",
    "wow": "guau", "please": "plis", "crack": "crac", "random": "rándom", "stream": "estrim",
    "streamer": "estrímer", "gg": "ge ge", "fan": "fan", "fans": "fans", "like": "laik",
    "likes": "laiks", "hello": "jelou", "hi": "jai", "love": "lov", "baby": "beibi", "cringe": "crinch",
    "tiktok": "tiktok", "tiktoker": "tiktóker", "selfie": "selfi", "youtube": "yutub", "bro": "bro",
}
_PALABRA = re.compile(r"\b[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+\b\.?")


def _palabras(t: str) -> str:
    def cambiar(m: re.Match) -> str:
        w = m[0]
        punto = w.endswith(".")
        base = w[:-1] if punto else w
        low = base.lower()
        if low in _ABREVIATURAS and (len(low) > 1 or low in ("q", "k", "x", "d")):
            nueva = _ABREVIATURAS[low]
            return nueva + ("." if punto and low not in ("etc", "sr", "sra", "srta", "dr", "aprox") else "")
        if low in _INGLES:
            return _INGLES[low] + ("." if punto else "")
        if len(base) > 3 and base.isupper():   # GRITOS -> gritos (si no, la voz deletrea)
            return base.capitalize() + ("." if punto else "")
        return w
    return _PALABRA.sub(cambiar, t)


def _sin_emojis(t: str) -> str:
    fuera = []
    for ch in t:
        cat = unicodedata.category(ch)
        if cat in ("So", "Sk", "Cs", "Co") or ch in "\u200d\ufe0f\ufe0e\u20e3":
            fuera.append(" ")
        else:
            fuera.append(ch)
    return "".join(fuera)


def preparar_para_voz(texto: str) -> str:
    """Texto que lee la voz. Las risas quedan como [risa] (se cambian por una risa grabada)."""
    t = texto or ""
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)
    t = re.sub(r"@(\w+)", r"\1", t)
    t = re.sub(r"#(\w+)", r"\1", t)
    t = marcar_risas(t)
    t = _sin_emojis(t)
    t = re.sub(r"[*_`~|<>{}\\^=]+", " ", t)
    # Letras repetidas: vocales hasta 7 (¡Muuuuuuu! de la vaca suena larga), consonantes hasta 3
    t = re.sub(r"([aeiouáéíóúAEIOU])\1{7,}", lambda m: m[1] * 7, t)
    t = re.sub(r"([^\W\daeiouáéíóúAEIOU])\1{3,}", lambda m: m[1] * 3, t)
    t = t.replace("&", " y ").replace("+", " más ")
    t = _numeros(t)
    t = _palabras(t)
    t = re.sub(r"([!?¡¿])\1+", r"\1", t)            # !!! -> !
    t = re.sub(r"\.{4,}", "...", t)
    t = re.sub(r"\s*([,.;:!?])", r"\1", t)
    t = re.sub(r"([,;:])(?=\S)", r"\1 ", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def piezas(texto_preparado: str) -> list[tuple[str, str]]:
    """'Hola. [risa] Chao.' -> [('voz', 'Hola.'), ('risa', ''), ('voz', 'Chao.')]"""
    out: list[tuple[str, str]] = []
    for i, trozo in enumerate(texto_preparado.split(MARCA_RISA)):
        trozo = trozo.strip(" ,")
        if i > 0:
            out.append(("risa", ""))
        if re.search(r"\w", trozo):
            out.append(("voz", trozo))
    return out


def sin_marcas(texto_preparado: str, risa_hablada: str = "¡Ja, ja, ja!") -> str:
    """Para voces sin risa grabada: [risa] -> lo que se lea en voz alta."""
    t = texto_preparado.replace(MARCA_RISA, f" {risa_hablada} " if risa_hablada else " ")
    return re.sub(r"\s{2,}", " ", t).strip()
