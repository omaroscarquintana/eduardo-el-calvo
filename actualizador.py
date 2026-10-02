"""Actualizador automático de Eduardo el Calvo (no necesita git, solo Python).

Se ejecuta al abrir iniciar.bat / iniciar_con_enlace.bat (y a mano con actualizar.bat):
  1. Pregunta a GitHub cuál es la última versión (rama main del repositorio público).
  2. Si es más nueva que la instalada, descarga el zip, lo revisa y reemplaza SOLO los
     archivos del programa. Nunca toca: config.toml, ia_local.toml, voz_local.toml,
     memoria.json, enlace_avatar.txt, las carpetas .venv, audios y herramientas.
  3. Si algo falla (sin internet, GitHub no responde, descarga rota...), deja todo como
     estaba y Eduardo arranca con la versión actual.

Uso:  python actualizador.py            (respeta [actualizaciones] automaticas en config.toml)
      python actualizador.py --forzar   (busca la actualización aunque estén desactivadas)
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

REPO = "omaroscarquintana/eduardo-el-calvo"
RAMA = "main"
CARPETA = Path(__file__).resolve().parent

ARCHIVO_VERSION = ".version_instalada"          # SHA del commit instalado
ARCHIVO_MANIFIESTO = ".archivos_programa.json"  # archivos del programa y su huella (sha256)
CARPETA_TRABAJO = ".actualizacion"              # descargas temporales y respaldo de la última versión

TIEMPO_CONSULTA = 5      # segundos máximos para preguntar a GitHub
TIEMPO_DESCARGA = 20     # segundos máximos sin recibir datos durante la descarga
TAMANO_MAXIMO = 60 * 1024 * 1024

# Archivos y carpetas del usuario: el actualizador JAMÁS los escribe ni los borra.
PROTEGIDOS = {"config.toml", "config.toml.respaldo", "ia_local.toml", "voz_local.toml", "memoria.json",
              "enlace_avatar.txt", ARCHIVO_VERSION, ARCHIVO_MANIFIESTO}
CARPETAS_PROTEGIDAS = {".venv", "venv", "env", "audios", "herramientas", "__pycache__", ".git", ".github",
                       CARPETA_TRABAJO}
# Textos que el usuario puede haber editado a mano: si los cambió, no se pisan (la versión
# nueva se deja al lado como "<nombre>.nuevo").
EDITABLES = {"personalidad.txt", "respuestas.txt", "palabras_prohibidas.txt"}
OBLIGATORIOS = {"bot.py", "actualizador.py", "requirements.txt", "config.ejemplo.toml", "eduardo/__init__.py"}


class ErrorActualizacion(Exception):
    pass


def decir(texto: str) -> None:
    print(texto, flush=True)


def es_protegido(rel: str, extra: set[str] = frozenset()) -> bool:
    partes = PurePosixPath(rel).parts
    if not partes or any(p in CARPETAS_PROTEGIDAS for p in partes[:-1]):
        return True
    nombre = partes[-1]
    if len(partes) == 1 and (nombre in PROTEGIDOS or nombre in extra):
        return True
    return (nombre.endswith(("_local.toml", ".respaldo", ".pyc")) or
            (nombre.startswith("memoria") and nombre.endswith(".json")) or
            nombre.startswith("cloudflared"))


def huella(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def leer_texto(ruta: Path) -> str:
    try:
        return ruta.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return ""


def leer_manifiesto() -> dict:
    try:
        datos = json.loads((CARPETA / ARCHIVO_MANIFIESTO).read_text(encoding="utf-8"))
        return datos.get("archivos", {}) if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def leer_config() -> dict:
    for nombre in ("config.toml", "config.ejemplo.toml"):
        try:
            with open(CARPETA / nombre, "rb") as f:
                return tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            continue
    return {}


def contexto_ssl() -> ssl.SSLContext:
    try:
        import certifi  # viene con httpx (si está instalado)
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def pedir(url: str, tiempo: float, aceptar: str = "application/vnd.github+json"):
    req = urllib.request.Request(url, headers={"User-Agent": "eduardo-el-calvo-actualizador",
                                               "Accept": aceptar})
    return urllib.request.urlopen(req, timeout=tiempo, context=contexto_ssl())


def ultima_version() -> tuple[str, str]:
    """Devuelve (sha, mensaje del commit) de la última versión publicada.

    Primero pregunta a la API de GitHub; si pide esperar (límite de 60 consultas por hora) o
    falla, prueba con el feed público de commits (no tiene ese límite).
    """
    try:
        return _ultima_por_api()
    except ErrorActualizacion as ex_api:
        if "sin internet" in str(ex_api):
            raise
        try:
            return _ultima_por_feed()
        except ErrorActualizacion:
            raise ex_api from None


def _ultima_por_feed() -> tuple[str, str]:
    url = f"https://github.com/{REPO}/commits/{RAMA}.atom"
    try:
        with pedir(url, TIEMPO_CONSULTA, aceptar="application/atom+xml") as r:
            texto = r.read(2_000_000).decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        raise ErrorActualizacion("sin internet o GitHub no responde") from ex
    entrada = texto.split("<entry>", 1)[1] if "<entry>" in texto else ""
    m = re.search(r"Grit::Commit/([0-9a-f]{40})", entrada)
    if not m:
        raise ErrorActualizacion("GitHub devolvió una respuesta rara")
    t = re.search(r"<title>\s*(.*?)\s*</title>", entrada, re.DOTALL)
    return m.group(1), html.unescape(t.group(1)) if t else ""


def _ultima_por_api() -> tuple[str, str]:
    url = f"https://api.github.com/repos/{REPO}/commits/{RAMA}"
    try:
        with pedir(url, TIEMPO_CONSULTA) as r:
            datos = json.loads(r.read(2_000_000).decode("utf-8"))
    except urllib.error.HTTPError as ex:
        if ex.code in (403, 429):
            raise ErrorActualizacion("GitHub pidió esperar un rato (límite de consultas)")
        if ex.code == 404:
            raise ErrorActualizacion("no encontré el repositorio de Eduardo en GitHub")
        raise ErrorActualizacion(f"GitHub respondió con error {ex.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        raise ErrorActualizacion("sin internet o GitHub no responde") from ex
    except ValueError as ex:
        raise ErrorActualizacion("GitHub devolvió una respuesta rara") from ex
    sha = str(datos.get("sha") or "")
    if len(sha) != 40:
        raise ErrorActualizacion("GitHub devolvió una respuesta rara")
    mensaje = str((datos.get("commit") or {}).get("message") or "").strip()
    return sha, mensaje


def descargar(sha: str) -> bytes:
    url = f"https://codeload.github.com/{REPO}/zip/{sha}"   # descarga directa (sin límite de la API)
    try:
        with pedir(url, TIEMPO_DESCARGA, aceptar="*/*") as r:
            datos = r.read(TAMANO_MAXIMO + 1)
    except urllib.error.HTTPError as ex:
        raise ErrorActualizacion(f"la descarga falló (error {ex.code})")
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        raise ErrorActualizacion("la descarga se cortó") from ex
    if len(datos) > TAMANO_MAXIMO:
        raise ErrorActualizacion("la descarga es demasiado grande")
    return datos


def abrir_paquete(datos: bytes) -> dict[str, bytes]:
    """Revisa el zip descargado y devuelve {ruta relativa: contenido} de los archivos del programa."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(datos))
        if zf.testzip() is not None:
            raise ErrorActualizacion("el zip descargado está dañado")
    except zipfile.BadZipFile as ex:
        raise ErrorActualizacion("el zip descargado está dañado") from ex
    archivos: dict[str, bytes] = {}
    raices = {PurePosixPath(n).parts[0] for n in zf.namelist() if n.strip("/")}
    if len(raices) != 1:
        raise ErrorActualizacion("el zip descargado no tiene el formato esperado")
    for info in zf.infolist():
        if info.is_dir():
            continue
        partes = PurePosixPath(info.filename).parts[1:]
        if not partes or any(p in ("", ".", "..") for p in partes) or ":" in info.filename:
            continue
        rel = "/".join(partes)
        if es_protegido(rel):
            continue
        archivos[rel] = zf.read(info)
    faltan = OBLIGATORIOS - set(archivos)
    if faltan:
        raise ErrorActualizacion("al zip descargado le faltan archivos: " + ", ".join(sorted(faltan)))
    for rel, contenido in archivos.items():   # que el código nuevo al menos se pueda leer
        if rel.endswith(".py"):
            try:
                compile(contenido, rel, "exec")
            except (SyntaxError, ValueError) as ex:
                raise ErrorActualizacion(f"la versión nueva tiene un error en {rel}") from ex
    try:
        tomllib.loads(archivos["config.ejemplo.toml"].decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as ex:
        raise ErrorActualizacion("la versión nueva tiene un error en config.ejemplo.toml") from ex
    for rel in list(archivos):   # los .bat de Windows necesitan saltos de línea CRLF
        if rel.lower().endswith((".bat", ".cmd")):
            archivos[rel] = archivos[rel].replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return archivos


def python_del_bot() -> str:
    for candidato in (CARPETA / ".venv" / "Scripts" / "python.exe", CARPETA / ".venv" / "bin" / "python"):
        if candidato.exists():
            return str(candidato)
    return sys.executable


def instalar_librerias(requisitos: bytes, trabajo: Path) -> None:
    ruta = trabajo / "requirements.txt"
    ruta.write_bytes(requisitos)
    decir("📦 La versión nueva necesita librerías nuevas. Instalando (puede tardar un minuto)...")
    try:
        res = subprocess.run([python_del_bot(), "-m", "pip", "install", "--disable-pip-version-check",
                              "-q", "-r", str(ruta)], timeout=600)
    except (OSError, subprocess.TimeoutExpired) as ex:
        raise ErrorActualizacion("no pude instalar las librerías nuevas") from ex
    if res.returncode != 0:
        raise ErrorActualizacion("no pude instalar las librerías nuevas (revisa tu internet)")


def escribir_atomico(destino: Path, contenido: bytes) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".nuevo_tmp")
    tmp.write_bytes(contenido)
    os.replace(tmp, destino)


def aplicar(archivos: dict[str, bytes], trabajo: Path) -> list[str]:
    """Reemplaza los archivos del programa. Si algo falla, vuelve todo atrás. Devuelve avisos."""
    manifiesto_viejo = leer_manifiesto()
    extra = {str(leer_config().get("memoria", {}).get("archivo", "memoria.json"))}
    respaldo = trabajo / "respaldo"
    if respaldo.exists():
        shutil.rmtree(respaldo, ignore_errors=True)
    respaldo.mkdir(parents=True)
    cambios: list[tuple[Path, Path | None]] = []   # (destino, copia de respaldo o None si era nuevo)
    avisos: list[str] = []

    def respaldar(destino: Path) -> None:
        if destino.exists():
            copia = respaldo / destino.relative_to(CARPETA)
            copia.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destino, copia)
            cambios.append((destino, copia))
        else:
            cambios.append((destino, None))

    try:
        for rel, contenido in sorted(archivos.items()):
            if es_protegido(rel, extra):
                continue
            destino = CARPETA / rel
            actual = destino.read_bytes() if destino.exists() else None
            if actual == contenido:
                continue
            if (rel in EDITABLES and actual is not None and rel in manifiesto_viejo
                    and huella(actual) != manifiesto_viejo[rel]):
                nuevo = CARPETA / (rel + ".nuevo")
                respaldar(nuevo)
                escribir_atomico(nuevo, contenido)
                avisos.append(f"Tú editaste {rel}: lo dejé como estaba y puse la versión nueva en {rel}.nuevo")
                continue
            respaldar(destino)
            escribir_atomico(destino, contenido)
        # Archivos que la versión nueva ya no trae (solo si eran del programa y nadie los editó)
        for rel, huella_vieja in manifiesto_viejo.items():
            destino = CARPETA / rel
            if rel in archivos or es_protegido(rel, extra) or not destino.is_file():
                continue
            if huella(destino.read_bytes()) == huella_vieja:
                respaldar(destino)
                destino.unlink()
    except Exception as ex:
        for destino, copia in reversed(cambios):
            try:
                if copia is None:
                    destino.unlink(missing_ok=True)
                else:
                    escribir_atomico(destino, copia.read_bytes())
            except Exception:
                pass
        raise ErrorActualizacion(f"no pude reemplazar los archivos ({type(ex).__name__}: {ex})") from ex
    return avisos


def guardar_version(sha: str, archivos: dict[str, bytes]) -> None:
    manifiesto = {"repo": REPO, "sha": sha, "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
                  "archivos": {rel: huella(c) for rel, c in sorted(archivos.items())}}
    escribir_atomico(CARPETA / ARCHIVO_MANIFIESTO,
                     json.dumps(manifiesto, ensure_ascii=False, indent=1).encode("utf-8"))
    escribir_atomico(CARPETA / ARCHIVO_VERSION, (sha + "\n").encode("ascii"))


def preparar_config() -> None:
    """Crea config.toml si falta y le agrega las opciones nuevas (sin tocar las del usuario)."""
    try:
        if str(CARPETA) not in sys.path:
            sys.path.insert(0, str(CARPETA))
        import importlib
        import eduardo.configuracion as conf
        conf = importlib.reload(conf)
        conf.asegurar_config_usuario(CARPETA, avisar=decir)
        conf.agregar_opciones_nuevas(CARPETA, avisar=decir)
    except Exception as ex:   # nunca impedir que Eduardo arranque por esto
        decir(f"   (No pude revisar config.toml: {type(ex).__name__}. Sigo igual.)")


def actualizar(forzar: bool = False) -> int:
    """0 = al día o actualizado; 1 = no se pudo (Eduardo sigue con la versión actual)."""
    if not forzar and leer_config().get("actualizaciones", {}).get("automaticas", True) is False:
        decir("ℹ️  Actualizaciones automáticas desactivadas (config.toml → [actualizaciones]).")
        return 0
    if (CARPETA / ".git").exists() and not forzar:
        decir("ℹ️  Esta carpeta es una copia de desarrollo (git): no la actualizo sola.")
        return 0
    trabajo = CARPETA / CARPETA_TRABAJO
    trabajo.mkdir(exist_ok=True)
    candado = trabajo / "en_curso.lock"
    try:
        if candado.exists() and time.time() - candado.stat().st_mtime < 600:
            decir("ℹ️  Ya hay otra ventana actualizando a Eduardo; sigo sin buscar actualizaciones.")
            return 0
        candado.write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        pass
    try:
        instalada = leer_texto(CARPETA / ARCHIVO_VERSION)
        decir("🔎 Buscando actualizaciones de Eduardo...")
        sha, mensaje = ultima_version()
        if sha == instalada:
            decir(f"✅ Eduardo está al día (versión {sha[:7]}).")
            return 0
        archivos = abrir_paquete(descargar(sha))
        req_actual = (CARPETA / "requirements.txt").read_bytes() if (CARPETA / "requirements.txt").exists() else b""
        if archivos["requirements.txt"].replace(b"\r\n", b"\n") != req_actual.replace(b"\r\n", b"\n"):
            instalar_librerias(archivos["requirements.txt"], trabajo)
        avisos = aplicar(archivos, trabajo)
        guardar_version(sha, archivos)
        titulo = mensaje.splitlines()[0] if mensaje else "versión nueva"
        decir(f"🎉 Eduardo se actualizó: {titulo} ({sha[:7]})")
        for aviso in avisos:
            decir(f"   ⚠️  {aviso}")
        return 0
    except ErrorActualizacion as ex:
        decir(f"⚠️  No pude buscar/instalar actualizaciones ({ex}). Eduardo arranca con la versión actual.")
        return 1
    except Exception as ex:   # cualquier cosa rara: no bloquear el arranque
        decir(f"⚠️  La actualización falló ({type(ex).__name__}). Eduardo arranca con la versión actual.")
        return 1
    finally:
        try:
            candado.unlink(missing_ok=True)
        except OSError:
            pass
        preparar_config()


def main() -> None:
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    codigo = actualizar(forzar="--forzar" in sys.argv[1:])
    sys.exit(codigo if "--codigo-salida" in sys.argv[1:] else 0)


if __name__ == "__main__":
    main()
