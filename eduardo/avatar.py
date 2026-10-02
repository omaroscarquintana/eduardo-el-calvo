"""Servidor local del avatar animado (página web para LIVE Studio)."""
from __future__ import annotations

import asyncio
import itertools
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path

from aiohttp import WSMsgType, web

log = logging.getLogger("eduardo")


_KBPS_V1 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
_KBPS_V2 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160]


def _kbps_mp3(datos: bytes) -> int:
    """Lee el bitrate de la primera trama MP3 (edge-tts = 48 kbps, ElevenLabs = 128 kbps)."""
    i = 0
    if datos[:3] == b"ID3" and len(datos) > 10:  # saltar etiqueta ID3
        i = 10 + ((datos[6] & 0x7F) << 21 | (datos[7] & 0x7F) << 14 | (datos[8] & 0x7F) << 7 | (datos[9] & 0x7F))
    while i + 4 <= len(datos):
        if datos[i] == 0xFF and (datos[i + 1] & 0xE0) == 0xE0:
            version = (datos[i + 1] >> 3) & 0x03   # 3 = MPEG1
            indice = (datos[i + 2] >> 4) & 0x0F
            if 0 < indice < 15:
                return (_KBPS_V1 if version == 3 else _KBPS_V2)[indice]
        i += 1
    return 48


def duracion_mp3(ruta: Path) -> float:
    """Duración aproximada (MP3 de bitrate constante): bytes * 8 / bitrate."""
    try:
        tam = ruta.stat().st_size
        with open(ruta, "rb") as f:
            kbps = _kbps_mp3(f.read(16384))
        return max(0.5, tam * 8 / (kbps * 1000))
    except OSError:
        return 3.0


@dataclass
class ClienteAvatar:
    ws: web.WebSocketResponse
    conectado: float = field(default_factory=time.monotonic)
    puede_sonar: bool = False
    silencio: bool = False
    agente: str = ""


class ServidorAvatar:
    def __init__(self, carpeta: Path, carpeta_audios: Path, puerto: int = 8765,
                 burbuja: bool = True, modo_audio: str = "auto", clave_enlace: str = ""):
        self.carpeta = carpeta
        self.carpeta_audios = carpeta_audios
        self.puerto = puerto
        self.burbuja = burbuja
        self.modo_audio = (modo_audio or "auto").lower()
        self.clientes: list[ClienteAvatar] = []
        self._ids = itertools.count(1)
        self._esperas: dict[int, asyncio.Future] = {}
        self._empezo: dict[int, asyncio.Event] = {}
        self._runner: web.AppRunner | None = None
        self.primer_cliente = asyncio.Event()
        # Clave secreta para el enlace público (túnel): https://xxx.trycloudflare.com/e/<clave>/avatar
        self.clave_enlace = clave_enlace or secrets.token_urlsafe(9).replace("-", "a").replace("_", "b")
        self.disfraz_actual = ""
        self._quitar_disfraz: asyncio.TimerHandle | None = None

    # -------------------------------------------------------------- servidor
    @property
    def url(self) -> str:
        return f"http://localhost:{self.puerto}/avatar"

    async def iniciar(self) -> bool:
        app = web.Application(middlewares=[self._solo_con_clave])
        app.router.add_get("/", lambda r: web.HTTPFound("/avatar"))
        app.router.add_get("/avatar", self._pagina)
        app.router.add_get("/ws", self._websocket)
        app.router.add_get("/audio/{nombre}", self._audio)
        # Mismo contenido, con la clave secreta delante (para el enlace público https del túnel)
        app.router.add_get("/e/{clave}/avatar", self._pagina)
        app.router.add_get("/e/{clave}/ws", self._websocket)
        app.router.add_get("/e/{clave}/audio/{nombre}", self._audio)
        self._runner = web.AppRunner(app, access_log=None)
        await self._runner.setup()
        try:
            # Solo escucha en esta PC (127.0.0.1): nadie de fuera puede entrar.
            await web.TCPSite(self._runner, "127.0.0.1", self.puerto).start()
        except OSError as ex:
            log.error("No pude abrir el avatar en el puerto %s (%s). ¿Hay otro Eduardo abierto?"
                      " Cambia [avatar] puerto en config.toml.", self.puerto, ex)
            await self._runner.cleanup()
            self._runner = None
            return False
        return True

    @staticmethod
    def _viene_de_internet(request: web.Request) -> bool:
        h = request.headers
        return bool(h.get("Cf-Ray") or h.get("Cf-Connecting-Ip") or h.get("X-Forwarded-For") or h.get("Forwarded"))

    @web.middleware
    async def _solo_con_clave(self, request: web.Request, handler):
        """Desde esta PC se entra sin clave. Desde internet (túnel) SOLO con /e/<clave correcta>/..."""
        clave = request.match_info.get("clave")
        if clave is not None:
            if not secrets.compare_digest(clave, self.clave_enlace):
                raise web.HTTPNotFound()
        elif self._viene_de_internet(request):
            raise web.HTTPNotFound()
        return await handler(request)

    def ruta_publica(self) -> str:
        return f"/e/{self.clave_enlace}/avatar"

    async def detener(self) -> None:
        for c in list(self.clientes):
            try:
                await c.ws.close()
            except Exception:
                pass
        if self._runner:
            await self._runner.cleanup()

    async def _pagina(self, request: web.Request) -> web.StreamResponse:
        return web.FileResponse(self.carpeta / "avatar" / "avatar.html",
                                headers={"Cache-Control": "no-store"})

    async def _audio(self, request: web.Request) -> web.StreamResponse:
        nombre = request.match_info["nombre"]
        if "/" in nombre or "\\" in nombre or not nombre.endswith(".mp3"):
            raise web.HTTPNotFound()
        ruta = self.carpeta_audios / nombre
        if not ruta.exists():
            raise web.HTTPNotFound()
        return web.FileResponse(ruta, headers={"Cache-Control": "no-store", "Content-Type": "audio/mpeg"})

    async def _websocket(self, request: web.Request) -> web.StreamResponse:
        ws = web.WebSocketResponse(heartbeat=20)
        await ws.prepare(request)
        cliente = ClienteAvatar(ws, agente=request.headers.get("User-Agent", "")[:80])
        self.clientes.append(cliente)
        print(f"🖼️  Avatar conectado ({len(self.clientes)} ventana(s) abierta(s)).", flush=True)
        self.primer_cliente.set()
        await self._enviar(cliente, {"tipo": "config", "burbuja": self.burbuja, "disfraz": self.disfraz_actual})
        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                try:
                    datos = json.loads(msg.data)
                except ValueError:
                    continue
                tipo = datos.get("tipo")
                if tipo == "estado":
                    antes = cliente.puede_sonar
                    cliente.puede_sonar = bool(datos.get("puede_sonar"))
                    cliente.silencio = bool(datos.get("silencio"))
                    if cliente.puede_sonar and not antes:
                        print("🔊 El avatar puede reproducir el sonido.", flush=True)
                elif tipo == "empezo":
                    ev = self._empezo.get(datos.get("id"))
                    if ev:
                        ev.set()
                elif tipo == "fin":
                    fut = self._esperas.get(datos.get("id"))
                    if fut and not fut.done():
                        fut.set_result(bool(datos.get("ok")))
                    if datos.get("ok") is False:
                        cliente.puede_sonar = False
                        log.info("El avatar no pudo sonar (%s); suena en la PC.", str(datos.get("error", "?"))[:80])
        finally:
            if cliente in self.clientes:
                self.clientes.remove(cliente)
            print(f"🖼️  Avatar desconectado ({len(self.clientes)} ventana(s) abierta(s)).", flush=True)
        return ws

    # --------------------------------------------------------------- hablar
    def cliente_de_sonido(self) -> ClienteAvatar | None:
        """La ventana que reproduce el sonido: la PRIMERA que se conectó y puede sonar.
        (Así, si abres una vista previa después de LIVE Studio, no le roba el audio)."""
        if self.modo_audio == "pc":
            return None
        candidatos = [c for c in self.clientes if c.puede_sonar and not c.silencio and not c.ws.closed]
        return min(candidatos, key=lambda c: c.conectado) if candidatos else None

    async def _enviar(self, cliente: ClienteAvatar, datos: dict) -> None:
        try:
            await cliente.ws.send_str(json.dumps(datos, ensure_ascii=False))
        except Exception:
            pass

    async def hablar(self, ruta: Path | None, texto: str, reir: bool, reir_desde: float = 0.6,
                     permitir_sonido: bool = True, gesto: str = "") -> bool:
        """Manda la frase a todas las ventanas del avatar.
        Devuelve True si una ventana reprodujo el sonido (entonces la PC NO debe sonar)."""
        if not self.clientes:
            return False
        ident = next(self._ids)
        sonido = self.cliente_de_sonido() if (ruta and permitir_sonido) else None
        duracion = duracion_mp3(ruta) if ruta else max(1.5, len(texto) / 14)
        base = {"tipo": "hablar", "id": ident, "texto": texto, "reir": reir, "reir_desde": reir_desde,
                "burbuja": self.burbuja, "duracion": duracion,
                "audio": f"/audio/{ruta.name}" if ruta else None, "gesto": gesto or None}
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        empezo = asyncio.Event()
        if sonido:
            self._esperas[ident] = fut
            self._empezo[ident] = empezo
        await asyncio.gather(*(self._enviar(c, {**base, "sonar": c is sonido}) for c in list(self.clientes)))
        if not sonido:
            return False
        try:
            # 1) ¿Empezó a sonar en la página? (si no, sonará en la PC)
            espera_inicio = asyncio.ensure_future(empezo.wait())
            hecho, _ = await asyncio.wait({espera_inicio, fut}, timeout=4, return_when=asyncio.FIRST_COMPLETED)
            espera_inicio.cancel()
            if fut.done() and not fut.result():
                return False
            if not empezo.is_set() and not fut.done():
                await self._enviar(sonido, {"tipo": "cancelar", "id": ident})  # que no suene doble
                return False
            # 2) Esperar a que termine de hablar
            return await asyncio.wait_for(fut, timeout=duracion + 6)
        except asyncio.TimeoutError:
            return True  # empezó a sonar pero no avisó del final: asumimos que sonó
        finally:
            self._esperas.pop(ident, None)
            self._empezo.pop(ident, None)

    # ------------------------------------------------- disfraces, gestos, ruleta
    async def a_todos(self, datos: dict) -> None:
        await asyncio.gather(*(self._enviar(c, datos) for c in list(self.clientes)))

    async def poner_disfraz(self, nombre: str, minutos: float = 0) -> None:
        """nombre='' quita el disfraz. minutos > 0: se lo quita solo después de ese tiempo."""
        self.disfraz_actual = nombre or ""
        if self._quitar_disfraz:
            self._quitar_disfraz.cancel()
            self._quitar_disfraz = None
        if nombre and minutos > 0:
            loop = asyncio.get_running_loop()
            self._quitar_disfraz = loop.call_later(
                minutos * 60, lambda: asyncio.ensure_future(self.poner_disfraz("")))
        await self.a_todos({"tipo": "disfraz", "nombre": self.disfraz_actual})

    async def gesto(self, nombre: str, segundos: float = 0) -> None:
        datos = {"tipo": "gesto", "nombre": nombre}
        if segundos > 0:
            datos["ms"] = int(segundos * 1000)
        await self.a_todos(datos)

    async def ruleta(self, nombres: list[str], ganador: str, categorias: list[str], indice: int,
                     duracion: float = 4.6) -> None:
        await self.a_todos({"tipo": "ruleta", "nombres": nombres, "ganador": ganador, "categorias": categorias,
                            "indice": indice, "duracion": duracion})

    async def fin_ruleta(self) -> None:
        await self.a_todos({"tipo": "ruleta_fin"})

