"""Configuración en dos capas: config.ejemplo.toml (de fábrica) + config.toml (del usuario).

- config.ejemplo.toml viene con el programa y se reemplaza en cada actualización.
- config.toml es SOLO del usuario: se crea la primera vez copiando el de fábrica y las
  actualizaciones nunca lo reemplazan. Si una versión nueva trae opciones nuevas, se agregan
  (con su explicación) al final de su sección, sin tocar lo que el usuario ya escribió.
- Al cargar, lo que falte en config.toml se toma de config.ejemplo.toml.
Solo usa la librería estándar (lo usa también actualizador.py).
"""
from __future__ import annotations

import re
import shutil
import time
import tomllib
from pathlib import Path

ARCHIVO_USUARIO = "config.toml"
ARCHIVO_FABRICA = "config.ejemplo.toml"

_AVISO_FABRICA = re.compile(r"#  OJO: este archivo \(config\.ejemplo\.toml\).*?(?=# =+)", re.DOTALL)
_AVISO_USUARIO = ("#  Este es TU archivo de configuración. Las actualizaciones de Eduardo NUNCA lo\n"
                  "#  reemplazan (si sale una opción nueva, se agrega sola al final de su sección).\n")
_CABECERA = re.compile(r"^\s*\[\s*([A-Za-z0-9_.\-]+)\s*\]\s*(#.*)?$")
_CLAVE = re.compile(r"^\s*([A-Za-z0-9_\-]+)\s*=")


def leer_toml(ruta: Path) -> dict:
    with open(ruta, "rb") as f:
        return tomllib.load(f)


def asegurar_config_usuario(carpeta: Path, avisar=print) -> Path | None:
    """Crea config.toml desde la de fábrica si no existe. Devuelve la ruta (o None si no hay de fábrica)."""
    usuario, fabrica = carpeta / ARCHIVO_USUARIO, carpeta / ARCHIVO_FABRICA
    if usuario.exists():
        return usuario
    if not fabrica.exists():
        return None
    texto = fabrica.read_text(encoding="utf-8")
    texto = _AVISO_FABRICA.sub(_AVISO_USUARIO, texto, count=1)
    usuario.write_text(texto, encoding="utf-8")
    if avisar:
        avisar(f"📝 Creé tu archivo de configuración: {ARCHIVO_USUARIO} (escribe ahí tu usuario de TikTok).")
    return usuario


def combinar(fabrica: dict, usuario: dict) -> dict:
    """Lo del usuario manda. Las secciones se combinan clave por clave (un nivel)."""
    final = {k: (dict(v) if isinstance(v, dict) else v) for k, v in fabrica.items()}
    for k, v in usuario.items():
        if isinstance(v, dict) and isinstance(final.get(k), dict):
            final[k].update(v)
        else:
            final[k] = v
    return final


def cargar_config(carpeta: Path, ruta: Path | None = None) -> dict:
    """Carga la configuración combinada. Lanza tomllib.TOMLDecodeError si config.toml tiene errores."""
    fabrica_ruta = carpeta / ARCHIVO_FABRICA
    if ruta is None:
        ruta = asegurar_config_usuario(carpeta) or (carpeta / ARCHIVO_USUARIO)
    fabrica = {}
    if fabrica_ruta.exists():
        try:
            fabrica = leer_toml(fabrica_ruta)
        except tomllib.TOMLDecodeError:
            fabrica = {}
    if not ruta.exists():
        if fabrica:
            return fabrica
        raise FileNotFoundError(ruta)
    return combinar(fabrica, leer_toml(ruta))


# ----------------------------------------------------------------- agregar opciones nuevas
def _bloques_fabrica(texto: str) -> dict[str, dict]:
    """{seccion: {"texto": bloque completo, "claves": {clave: texto con sus comentarios}}}"""
    secciones: dict[str, dict] = {}
    actual, lineas_sec = None, []
    pendientes: list[str] = []      # comentarios justo encima de la próxima clave
    clave_abierta, buffer, profundidad = None, [], 0

    def cerrar_seccion():
        if actual is not None:
            secciones[actual]["texto"] = "".join(lineas_sec).rstrip() + "\n"

    for linea in texto.splitlines(keepends=True):
        if clave_abierta is None:
            m = _CABECERA.match(linea)
            if m:
                cerrar_seccion()
                actual, lineas_sec, pendientes = m.group(1), [linea], []
                secciones[actual] = {"texto": "", "claves": {}}
                continue
        if actual is None:
            continue
        lineas_sec.append(linea)
        if clave_abierta is not None:   # valor de varias líneas (listas largas)
            buffer.append(linea)
            profundidad += _balance(linea)
            if profundidad <= 0:
                secciones[actual]["claves"][clave_abierta] = "".join(buffer)
                clave_abierta, buffer = None, []
            continue
        limpia = linea.strip()
        if not limpia:
            pendientes = []
        elif limpia.startswith("#"):
            pendientes.append(linea)
        else:
            m = _CLAVE.match(linea)
            if m:
                buffer = pendientes + [linea]
                pendientes = []
                profundidad = _balance(linea.split("=", 1)[1])
                if profundidad > 0:
                    clave_abierta = m.group(1)
                else:
                    secciones[actual]["claves"][m.group(1)] = "".join(buffer)
                    buffer = []
    cerrar_seccion()
    return secciones


def _balance(texto: str) -> int:
    sin_textos = re.sub(r'"(?:\\.|[^"\\])*"|\'[^\']*\'', "", texto.split(" #", 1)[0])
    return sin_textos.count("[") + sin_textos.count("{") - sin_textos.count("]") - sin_textos.count("}")


def agregar_opciones_nuevas(carpeta: Path, avisar=print) -> list[str]:
    """Agrega a config.toml las opciones que trae config.ejemplo.toml y que el usuario todavía no tiene.

    Nunca cambia ni borra valores del usuario. Guarda una copia (config.toml.respaldo) antes de
    escribir y solo escribe si el resultado se puede leer bien. Devuelve la lista de opciones agregadas.
    """
    usuario_ruta, fabrica_ruta = carpeta / ARCHIVO_USUARIO, carpeta / ARCHIVO_FABRICA
    if not usuario_ruta.exists() or not fabrica_ruta.exists():
        return []
    try:
        fabrica_txt = fabrica_ruta.read_text(encoding="utf-8")
        usuario_txt = usuario_ruta.read_text(encoding="utf-8")
        fabrica = tomllib.loads(fabrica_txt)
        usuario = tomllib.loads(usuario_txt)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return []   # si config.toml tiene un error, mejor no tocarlo (el bot avisará del error)

    bloques = _bloques_fabrica(fabrica_txt)
    agregadas: list[str] = []
    nuevo = usuario_txt if usuario_txt.endswith("\n") else usuario_txt + "\n"
    fecha = time.strftime("%Y-%m-%d")
    for seccion, valores in fabrica.items():
        if not isinstance(valores, dict) or seccion not in bloques:
            continue
        if seccion not in usuario:
            nuevo = nuevo.rstrip("\n") + f"\n\n\n# (Sección nueva agregada por la actualización del {fecha})\n" \
                    + bloques[seccion]["texto"]
            agregadas += [f"[{seccion}]"]
            continue
        if not isinstance(usuario[seccion], dict):
            continue
        faltan = [c for c in valores if c not in usuario[seccion] and c in bloques[seccion]["claves"]]
        if not faltan:
            continue
        texto_nuevo = f"\n# (Opciones nuevas agregadas por la actualización del {fecha})\n" + \
                      "".join(bloques[seccion]["claves"][c] for c in faltan)
        nuevo = _insertar_al_final_de_seccion(nuevo, seccion, texto_nuevo)
        if nuevo is None:
            return []
        agregadas += [f"{seccion}.{c}" for c in faltan]
    if not agregadas:
        return []
    try:   # comprobar que quedó bien antes de escribir nada
        revisado = tomllib.loads(nuevo)
        for seccion, valores in usuario.items():
            if isinstance(valores, dict):
                if any(revisado.get(seccion, {}).get(k) != v for k, v in valores.items()):
                    return []
            elif revisado.get(seccion) != valores:
                return []
    except tomllib.TOMLDecodeError:
        return []
    shutil.copy2(usuario_ruta, carpeta / (ARCHIVO_USUARIO + ".respaldo"))
    tmp = usuario_ruta.with_name(ARCHIVO_USUARIO + ".tmp")
    tmp.write_text(nuevo, encoding="utf-8")
    tmp.replace(usuario_ruta)
    if avisar:
        avisar("📝 Agregué a tu config.toml las opciones nuevas: " + ", ".join(agregadas)
               + " (tus ajustes siguen iguales).")
    return agregadas


def _insertar_al_final_de_seccion(texto: str, seccion: str, agregado: str) -> str | None:
    lineas = texto.splitlines(keepends=True)
    inicio = None
    for i, linea in enumerate(lineas):
        m = _CABECERA.match(linea)
        if m and m.group(1) == seccion:
            inicio = i
            break
    if inicio is None:
        return None
    fin = len(lineas)
    for j in range(inicio + 1, len(lineas)):
        if lineas[j].lstrip().startswith("["):
            fin = j
            break
    # retroceder sobre líneas en blanco y comentarios sueltos que pertenecen a la sección siguiente
    corte = fin
    while corte > inicio + 1 and (not lineas[corte - 1].strip() or
                                  (fin < len(lineas) and lineas[corte - 1].lstrip().startswith("#"))):
        corte -= 1
    if corte < len(lineas) and not lineas[corte - 1].endswith("\n"):
        lineas[corte - 1] += "\n"
    if corte == len(lineas) and lineas and not lineas[-1].endswith("\n"):
        lineas[-1] += "\n"
    return "".join(lineas[:corte]) + agregado + "".join(lineas[corte:])
