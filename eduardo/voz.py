"""Texto a voz: Microsoft Edge (edge-tts, gratis, sin cuenta), Azure Speech (gratis hasta
500 mil caracteres al mes, con estilo alegre) o ElevenLabs (la más natural; plan gratis pequeño).
Siempre con respaldo: si falla la elegida, Edge; si falla Edge, la voz del sistema."""
from __future__ import annotations

import asyncio
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import time
import random
import uuid
from pathlib import Path
from xml.sax.saxutils import escape as _xml

from .texto_voz import MARCA_RISA, RISA_VISIBLE, piezas, preparar_para_voz, sin_marcas

log = logging.getLogger("eduardo")

ES_WINDOWS = sys.platform.startswith("win")
ES_MAC = sys.platform == "darwin"


# --------------------------------------------------------------- reproducción
def _reproducir_windows(ruta: Path) -> None:
    """Reproduce un MP3 con el reproductor integrado de Windows (MCI), sin instalar nada."""
    import ctypes

    winmm = ctypes.windll.winmm
    alias = "eduardo" + uuid.uuid4().hex[:8]

    def mci(cmd: str) -> None:
        err = winmm.mciSendStringW(cmd, None, 0, None)
        if err:
            buf = ctypes.create_unicode_buffer(256)
            winmm.mciGetErrorStringW(err, buf, 255)
            raise RuntimeError(f"MCI error {err}: {buf.value}")

    mci(f'open "{ruta}" type mpegvideo alias {alias}')
    try:
        mci(f"play {alias} wait")
    finally:
        winmm.mciSendStringW(f"close {alias}", None, 0, None)


def _reproducir_otro_sistema(ruta: Path) -> None:
    candidatos = []
    if ES_MAC:
        candidatos.append(["afplay", str(ruta)])
    candidatos += [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(ruta)],
        ["mpv", "--no-video", "--really-quiet", str(ruta)],
        ["mpg123", "-q", str(ruta)],
    ]
    for cmd in candidatos:
        if shutil.which(cmd[0]):
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                raise RuntimeError(f"{cmd[0]} falló: {(r.stderr or '').strip()[:200]}")
            return
    raise RuntimeError("No encontré un reproductor de audio (instala ffmpeg o mpv).")


def reproducir_mp3(ruta: Path) -> None:
    if ES_WINDOWS:
        _reproducir_windows(ruta)
    else:
        _reproducir_otro_sistema(ruta)


# ------------------------------------------------------------- voz del sistema
_PS_SCRIPT = (
    "Add-Type -AssemblyName System.Speech;"
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
    "$v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'es*' } | Select-Object -First 1;"
    "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) };"
    "$s.Speak($env:EDUARDO_TEXTO)"
)


def hablar_con_voz_del_sistema(texto: str) -> None:
    if ES_WINDOWS:
        env = dict(os.environ, EDUARDO_TEXTO=texto)  # el texto va por variable: nada de inyección
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_SCRIPT],
                           env=env, capture_output=True, text=True, timeout=120,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError(f"Voz de Windows falló: {r.stderr.strip()[:200]}")
        return
    if ES_MAC and shutil.which("say"):
        subprocess.run(["say", texto], check=True, timeout=120)
        return
    for prog in ("espeak-ng", "espeak"):
        if shutil.which(prog):
            subprocess.run([prog, "-v", "es-419", texto], check=True, capture_output=True, timeout=120)
            return
    raise RuntimeError("No hay voz del sistema disponible en este equipo.")


# ----------------------------------------------------------- pausas naturales
# La voz de Edge entrega MP3 de 24 kHz, 48 kbps, mono: cada "trama" mide 144 bytes y dura 24 ms.
# Eso permite recortar y unir frases sin decodificar el audio (no hace falta instalar nada).
_TRAMA_BYTES = 144
_TRAMA_SEG = 0.024
_CABECERA_EDGE = b"\xff\xf3\x64"
_FIN_FRASE = re.compile(r"(?<=[.!?…])\s+(?=\S)")


def dividir_frases(texto: str, maximo: int = 8) -> list[str]:
    """'¡Hola, Ana! ¿Cómo estás?' -> ['¡Hola, Ana!', '¿Cómo estás?'] (las muy cortas se juntan)."""
    partes: list[str] = []
    for p in _FIN_FRASE.split(texto.strip()):
        p = p.strip()
        if not p:
            continue
        if partes and len(re.sub(r"\W", "", p)) < 2:
            partes[-1] += " " + p
        else:
            partes.append(p)
    if len(partes) > maximo:
        partes = partes[:maximo - 1] + [" ".join(partes[maximo - 1:])]
    return partes


def pausa_para(frase: str, base: float) -> float:
    """Pausa después de una frase según cómo termina (pregunta y puntos suspensivos, un poco más)."""
    fin = frase.rstrip()[-1:] if frase.strip() else "."
    if frase.rstrip().endswith(("...", "…")):
        return base + 0.12
    return base + {"?": 0.06, "!": 0.0, ".": 0.03}.get(fin, 0.0)


def _es_mp3_edge(audio: bytes) -> bool:
    return (len(audio) >= _TRAMA_BYTES and len(audio) % _TRAMA_BYTES == 0
            and all(audio[i:i + 3] == _CABECERA_EDGE for i in range(0, len(audio), _TRAMA_BYTES * 25)))


# ------------------------------------------------------- clave local de la voz
ARCHIVO_VOZ_LOCAL = "voz_local.toml"   # lo crea configurar_voz.bat (nunca se comparte)


def leer_voz_local(carpeta: Path) -> dict:
    ruta = carpeta / ARCHIVO_VOZ_LOCAL
    if not ruta.exists():
        return {}
    try:
        import tomllib
        with ruta.open("rb") as f:
            datos = tomllib.load(f)
        return {k: str(v).strip() for k, v in datos.items() if isinstance(v, (str, int, float))}
    except Exception as ex:
        log.warning("No pude leer %s (%s). Lo ignoro.", ARCHIVO_VOZ_LOCAL, ex)
        return {}


def guardar_voz_local(carpeta: Path, datos: dict) -> Path:
    ruta = carpeta / ARCHIVO_VOZ_LOCAL
    lineas = ["# Creado por configurar_voz.bat. NO compartas este archivo: contiene tu clave de voz.",
              "# Para volver a la voz gratis de Edge, borra este archivo o usa configurar_voz.bat (opción 3)."]
    for k, v in datos.items():
        v = str(v).replace("\\", "").replace('"', "").strip()
        lineas.append(f'{k} = "{v}"')
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta


def _cargar_risas(carpeta: Path) -> list[bytes]:
    risas = []
    for ruta in sorted((carpeta / "sonidos").glob("risa_*.mp3")):
        try:
            datos = ruta.read_bytes()
        except OSError:
            continue
        if _es_mp3_edge(datos):
            risas.append(datos)
        else:
            log.info("La risa %s no está en MP3 24 kHz 48 kbps mono; la salto.", ruta.name)
    return risas


# ----------------------------------------------------------------- clase Voz
class Voz:
    def __init__(self, cfg: dict, carpeta: Path, reproducir: bool = True):
        v = cfg.get("voz", {})
        local = leer_voz_local(carpeta)
        self.nombre_voz = v.get("nombre_voz", "es-US-AlonsoNeural")
        self.velocidad = v.get("velocidad", "+2%")
        self.tono = v.get("tono", "-4Hz")
        self.volumen = v.get("volumen", "+0%")
        self.respaldo_sistema = bool(v.get("usar_voz_de_windows_si_falla", True))
        # Pausas naturales: cada frase se genera por separado y se unen con un silencio corto.
        self.pausas_naturales = bool(v.get("pausas_naturales", True))
        self.pausa_base = max(0.1, min(1.2, float(v.get("pausa_entre_frases_ms", 240)) / 1000))
        # Texto preparado para hablar (sin emojis, números en palabras...) y risas grabadas de verdad.
        self.normalizar = bool(v.get("preparar_texto", True))
        self.risas = _cargar_risas(carpeta) if bool(v.get("risas_grabadas", True)) else []
        self._ultima_risa = -1
        self.linea_tiempo: list[tuple[str, float, float]] = []  # (frase, inicio, fin) del último audio
        self.duracion_ultimo = 0.0
        # Proveedor: "edge" (gratis), "azure" (gratis con límite) o "elevenlabs" (plan gratis pequeño)
        self.proveedor = str(local.get("proveedor") or v.get("proveedor", "edge")).strip().lower()
        # ElevenLabs
        self.eleven_voz = str(local.get("voz_id") if self.proveedor == "elevenlabs" and local.get("voz_id")
                              else v.get("elevenlabs_voz_id", "")).strip()
        self.eleven_modelo = str(v.get("elevenlabs_modelo", "eleven_v3")).strip() or "eleven_v3"
        self.eleven_clave = ((local.get("clave") if local.get("proveedor") == "elevenlabs" else "")
                             or os.environ.get("ELEVENLABS_API_KEY", "")).strip()
        # Azure Speech
        self.azure_clave = ((local.get("clave") if local.get("proveedor") == "azure" else "")
                            or os.environ.get("AZURE_SPEECH_KEY", "")).strip()
        self.azure_region = ((local.get("region") if local.get("proveedor") == "azure" else "")
                             or os.environ.get("AZURE_SPEECH_REGION", "") or v.get("azure_region", "")).strip().lower()
        self.azure_voz = str((local.get("voz") if local.get("proveedor") == "azure" else "")
                             or v.get("azure_voz", "es-MX-JorgeNeural")).strip()
        self.azure_estilo = str(v.get("azure_estilo", "cheerful")).strip()
        self.azure_intensidad = max(0.01, min(2.0, float(v.get("azure_intensidad", 1.3))))
        self.azure_velocidad = str(v.get("azure_velocidad", "+0%"))
        self.azure_tono = str(v.get("azure_tono", "-3%"))
        self._avisado: set[str] = set()
        self.ultimo_proveedor = ""   # con qué voz salió el último audio ("ElevenLabs", "Azure", "Edge")
        self.ultimo_error = ""       # por qué falló el proveedor elegido (para configurar_voz)
        self.conservar = bool(cfg.get("archivos", {}).get("conservar_audios", False))
        self.reproducir = reproducir
        self.carpeta_audios = carpeta / "audios"
        self.carpeta_audios.mkdir(exist_ok=True)

    def _avisar_una_vez(self, clave: str, mensaje: str, *args) -> None:
        if clave not in self._avisado:
            self._avisado.add(clave)
            log.warning(mensaje, *args)

    @property
    def usa_elevenlabs(self) -> bool:
        if self.proveedor != "elevenlabs":
            return False
        if not (self.eleven_clave and self.eleven_voz):
            self._avisar_una_vez("eleven", "La voz está en ElevenLabs pero falta %s. Uso la voz gratis de Edge "
                                 "(abre configurar_voz.bat).", "la clave" if not self.eleven_clave else "el Voice ID")
            return False
        return True

    @property
    def usa_azure(self) -> bool:
        if self.proveedor != "azure":
            return False
        if not (self.azure_clave and self.azure_region):
            self._avisar_una_vez("azure", "La voz está en Azure pero falta %s. Uso la voz gratis de Edge "
                                 "(abre configurar_voz.bat).", "la clave" if not self.azure_clave else "la región")
            return False
        return True

    def descripcion(self) -> str:
        risas = f", {len(self.risas)} risas grabadas" if self.risas else ""
        if self.usa_elevenlabs:
            return f"ElevenLabs {self.eleven_voz} ({self.eleven_modelo})"
        if self.usa_azure:
            return f"Azure {self.azure_voz} (estilo {self.azure_estilo or 'normal'}){risas}"
        return f"{self.nombre_voz} ({self.velocidad}, {self.tono}){risas}"

    def _risa(self) -> bytes | None:
        if not self.risas:
            return None
        opciones = [i for i in range(len(self.risas)) if i != self._ultima_risa] or [0]
        self._ultima_risa = random.choice(opciones)
        return self.risas[self._ultima_risa]

    # ------------------------------------------------------------ ElevenLabs
    async def _generar_elevenlabs(self, hablado: str, ruta: Path) -> None:
        import httpx

        v3 = self.eleven_modelo.startswith("eleven_v3")
        # Eleven v3 sabe reírse de verdad con la etiqueta [laughs]
        texto = sin_marcas(hablado, "[laughs]" if v3 else RISA_VISIBLE)
        ajustes = ({"stability": 0.5} if v3 else
                   {"stability": 0.35, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True})
        cuerpo = {"text": texto, "model_id": self.eleven_modelo, "voice_settings": ajustes}
        if v3:
            cuerpo["language_code"] = "es"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.eleven_voz}"
        async with httpx.AsyncClient(timeout=40) as cliente:
            r = await cliente.post(url, params={"output_format": "mp3_44100_128"},
                                   headers={"xi-api-key": self.eleven_clave, "Accept": "audio/mpeg"}, json=cuerpo)
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs respondió {r.status_code}: {' '.join(r.text.split())[:150]}")
        ruta.write_bytes(r.content)

    # ----------------------------------------------------------------- Azure
    def _ssml_azure(self, texto: str, final: bool) -> str:
        locale = "-".join(self.azure_voz.split("-")[:2]) or "es-MX"
        pausa = int(self.pausa_base * 1000) + 40
        cola = 350 if final else 180
        cuerpo = f'<prosody rate="{_xml(self.azure_velocidad)}" pitch="{_xml(self.azure_tono)}">{_xml(texto)}</prosody>'
        if self.azure_estilo:
            cuerpo = (f'<mstts:express-as style="{_xml(self.azure_estilo)}" styledegree="{self.azure_intensidad:.2f}">'
                      f"{cuerpo}</mstts:express-as>")
        return ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
                f'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{locale}">'
                f'<voice name="{_xml(self.azure_voz)}">'
                '<mstts:silence type="Leading-exact" value="60ms"/>'
                f'<mstts:silence type="Tailing-exact" value="{cola}ms"/>'
                f'<mstts:silence type="Sentenceboundary-exact" value="{pausa}ms"/>'
                f"{cuerpo}</voice></speak>")

    async def _azure_trozo(self, cliente, texto: str, final: bool) -> bytes:
        url = f"https://{self.azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        r = await cliente.post(url, content=self._ssml_azure(texto, final).encode("utf-8"), headers={
            "Ocp-Apim-Subscription-Key": self.azure_clave,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "EduardoElCalvo"})
        if r.status_code != 200:
            raise RuntimeError(f"Azure respondió {r.status_code}: {' '.join(r.text.split())[:150]}")
        return r.content

    async def _generar_azure(self, hablado: str) -> bytes:
        import httpx

        trozos = piezas(hablado)
        if not trozos:
            raise RuntimeError("texto vacío")
        voces = [(i, t) for i, (tipo, t) in enumerate(trozos) if tipo == "voz"]
        async with httpx.AsyncClient(timeout=25) as cliente:
            audios = await asyncio.gather(*(self._azure_trozo(cliente, t, i == len(trozos) - 1) for i, t in voces))
        por_indice = dict(zip([i for i, _ in voces], audios))
        hay_risa = any(tipo == "risa" for tipo, _ in trozos)
        if hay_risa and not (self.risas and all(_es_mp3_edge(a) for a in audios)):
            # No se puede unir la risa grabada: una sola petición con la risa hablada
            async with httpx.AsyncClient(timeout=25) as cliente:
                audio = await self._azure_trozo(cliente, sin_marcas(hablado), True)
            return audio
        salida = bytearray()
        linea: list[tuple[str, float, float]] = []
        for i, (tipo, texto) in enumerate(trozos):
            t0 = len(salida) / _TRAMA_BYTES * _TRAMA_SEG
            if tipo == "risa":
                risa = self._risa()
                if risa:
                    salida += risa
                    linea.append((RISA_VISIBLE, t0, len(salida) / _TRAMA_BYTES * _TRAMA_SEG))
                continue
            salida += por_indice[i]
            linea.append((texto, t0, len(salida) / _TRAMA_BYTES * _TRAMA_SEG))
        self.linea_tiempo = linea if all(_es_mp3_edge(a) for a in audios) else []
        return bytes(salida)

    # ------------------------------------------------------------------ Edge
    async def _segmento_edge(self, frase: str) -> tuple[bytes, float | None, float | None]:
        import edge_tts

        com = edge_tts.Communicate(frase, self.nombre_voz, rate=self.velocidad, pitch=self.tono,
                                   volume=self.volumen, boundary="WordBoundary")
        audio = bytearray()
        ini = fin = None
        async for trozo in com.stream():
            if trozo["type"] == "audio":
                audio += trozo["data"]
            elif trozo["type"] == "WordBoundary":
                o, d = trozo["offset"] / 1e7, trozo["duration"] / 1e7
                ini = o if ini is None else min(ini, o)
                fin = o + d if fin is None else max(fin, o + d)
        return bytes(audio), ini, fin

    def _plan(self, hablado: str) -> list[tuple[str, str]]:
        """Lista de ('frase', texto) y ('risa', '') en orden. Sin risas grabadas, la risa se habla."""
        plan: list[tuple[str, str]] = []
        for tipo, texto in piezas(hablado):
            if tipo == "risa":
                if self.risas:
                    plan.append(("risa", ""))
                else:
                    plan.append(("frase", RISA_VISIBLE))
            else:
                plan += [("frase", f) for f in dividir_frases(texto)]
        return plan

    async def _generar_con_pausas(self, hablado: str) -> bytes | None:
        """Genera frase por frase, mete las risas grabadas y une todo con pausas naturales.
        None = mejor hacerlo de una vez."""
        plan = self._plan(hablado)
        frases = [t for tipo, t in plan if tipo == "frase"]
        hay_risa = any(tipo == "risa" for tipo, _ in plan)
        if not frases and hay_risa:   # solo una risa
            salida = b"".join(self._risa() or b"" for _ in plan)
            self.linea_tiempo = [(RISA_VISIBLE, 0.0, len(salida) / _TRAMA_BYTES * _TRAMA_SEG)]
            return salida or None
        if not frases or (len(plan) < 2 and not hay_risa):
            return None
        if not self.pausas_naturales and not hay_risa:
            return None
        trozos = dict(zip(range(len(frases)), await asyncio.gather(*(self._segmento_edge(f) for f in frases))))
        salida = bytearray()
        linea: list[tuple[str, float, float]] = []
        k = 0
        for i, (tipo, frase) in enumerate(plan):
            t0 = len(salida) / _TRAMA_BYTES * _TRAMA_SEG
            if tipo == "risa":
                salida += self._risa() or b""
                linea.append((RISA_VISIBLE, t0, len(salida) / _TRAMA_BYTES * _TRAMA_SEG))
                continue
            audio, ini, fin = trozos[k]
            k += 1
            if not _es_mp3_edge(audio):
                return None
            n = len(audio) // _TRAMA_BYTES
            ultima = i == len(plan) - 1
            if ini is None or fin is None:  # sin marcas de tiempo: se usa la frase entera
                a, b = 0, n
            else:
                desde = max(0.0, ini - (0.12 if i == 0 else 0.05))
                if not self.pausas_naturales:
                    hasta = fin + 0.9
                elif ultima:
                    hasta = fin + 0.35
                elif plan[i + 1][0] == "risa":
                    hasta = fin + 0.12   # la risa sale enseguida, como en la vida real
                else:
                    hasta = fin + max(0.1, pausa_para(frase, self.pausa_base) - 0.05)
                a = int(desde / _TRAMA_SEG)
                b = min(n, max(a + 1, math.ceil(hasta / _TRAMA_SEG)))
            salida += audio[a * _TRAMA_BYTES:b * _TRAMA_BYTES]
            linea.append((frase, t0, len(salida) / _TRAMA_BYTES * _TRAMA_SEG))
        self.linea_tiempo = linea
        return bytes(salida)

    def fraccion_de(self, patron: re.Pattern) -> float | None:
        """En qué parte del último audio (0 a 1) empieza la primera frase que cumple el patrón."""
        if not self.linea_tiempo or self.duracion_ultimo <= 0:
            return None
        for frase, ini, fin in self.linea_tiempo:
            m = patron.search(frase)
            if m:
                pos = ini + (fin - ini) * (m.start() / max(1, len(frase)))
                return max(0.0, min(0.95, pos / self.duracion_ultimo))
        return None

    async def generar_mp3(self, texto: str) -> Path:
        ruta = self.carpeta_audios / f"eduardo_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.mp3"
        self.linea_tiempo, self.duracion_ultimo = [], 0.0
        self.ultimo_proveedor, self.ultimo_error = "", ""
        hablado = preparar_para_voz(texto) if self.normalizar else texto
        if not re.search(r"\w", sin_marcas(hablado, "")) and MARCA_RISA not in hablado:
            hablado = texto
        if self.usa_elevenlabs:
            try:
                await self._generar_elevenlabs(hablado, ruta)
                if ruta.exists() and ruta.stat().st_size > 0:
                    self.ultimo_proveedor = "ElevenLabs"
                    return ruta
            except Exception as ex:
                self.ultimo_error = str(ex)[:300]
                log.warning("ElevenLabs falló (%s). Uso la voz gratis de Edge.", str(ex)[:150])
        if self.usa_azure:
            try:
                audio = await asyncio.wait_for(self._generar_azure(hablado), timeout=25)
                if audio:
                    ruta.write_bytes(audio)
                    if self.linea_tiempo:
                        self.duracion_ultimo = len(audio) / _TRAMA_BYTES * _TRAMA_SEG
                    self.ultimo_proveedor = "Azure"
                    return ruta
            except Exception as ex:
                self.ultimo_error = f"{type(ex).__name__}: {str(ex)[:300]}"
                self.linea_tiempo = []
                log.warning("Azure falló (%s). Uso la voz gratis de Edge.", str(ex)[:150])
        import edge_tts  # importado aquí para que el resto del bot cargue aunque falte

        try:
            audio = await asyncio.wait_for(self._generar_con_pausas(hablado), timeout=25)
            if audio:
                ruta.write_bytes(audio)
                self.duracion_ultimo = len(audio) / _TRAMA_BYTES * _TRAMA_SEG
                self.ultimo_proveedor = "Edge"
                return ruta
        except Exception as ex:
            log.info("Pausas naturales no disponibles (%s); genero el audio de una vez.", type(ex).__name__)
            self.linea_tiempo = []
        comunicador = edge_tts.Communicate(sin_marcas(hablado), self.nombre_voz, rate=self.velocidad,
                                           pitch=self.tono, volume=self.volumen)
        await asyncio.wait_for(comunicador.save(str(ruta)), timeout=20)
        if not ruta.exists() or ruta.stat().st_size == 0:
            raise RuntimeError("edge-tts no generó audio")
        self.ultimo_proveedor = "Edge"
        return ruta

    async def reproducir_pc(self, ruta: Path) -> bool:
        try:
            await asyncio.to_thread(reproducir_mp3, ruta)
            return True
        except Exception as ex:
            log.error("No se pudo reproducir el audio en la PC: %s", ex)
            return False

    async def hablar_sistema(self, texto: str) -> bool:
        if not (self.respaldo_sistema and self.reproducir):
            return False
        try:
            await asyncio.to_thread(hablar_con_voz_del_sistema, texto)
            return True
        except Exception as ex:
            log.error("Tampoco funcionó la voz del sistema: %s", ex)
            return False

    def limpiar(self, ruta: Path | None) -> None:
        if ruta and not self.conservar and self.reproducir and ruta.exists():
            try:
                ruta.unlink()
            except OSError:
                pass

    async def intentar_generar(self, texto: str) -> Path | None:
        try:
            return await self.generar_mp3(texto)
        except Exception as ex:
            log.warning("La voz falló (%s: %s).", type(ex).__name__, str(ex)[:150])
            return None

    async def decir(self, texto: str) -> str:
        """Genera y reproduce en la PC (sin avatar). Devuelve qué pasó."""
        ruta = await self.intentar_generar(texto)
        if ruta is None:
            return "voz del sistema" if await self.hablar_sistema(texto) else "sin voz"
        if not self.reproducir:
            return f"audio generado (sin reproducir): {ruta.name}"
        ok = await self.reproducir_pc(ruta)
        if ok:
            self.limpiar(ruta)
            return "reproducido en la PC"
        return f"audio generado pero no reproducido: {ruta.name}"
