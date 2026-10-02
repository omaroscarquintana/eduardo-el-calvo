"""Enlace público https para el avatar (TikTok LIVE Studio NO acepta http://localhost en la fuente "Enlace").

Usa un "Quick Tunnel" GRATIS de Cloudflare (cloudflared): sin cuenta, sin tarjeta.
- El enlace (https://algo.trycloudflare.com) CAMBIA cada vez que abres Eduardo: hay que pegarlo de nuevo.
- El enlace lleva una clave secreta (/e/<clave>/avatar); sin la clave, el túnel responde "no encontrado".
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import sys
from pathlib import Path

log = logging.getLogger("eduardo")

URL_DESCARGA_WINDOWS = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
_RE_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def ruta_cloudflared(carpeta: Path) -> Path | None:
    nombre = "cloudflared.exe" if sys.platform.startswith("win") else "cloudflared"
    local = carpeta / "herramientas" / nombre
    if local.exists() and local.stat().st_size > 5_000_000:
        return local
    en_path = shutil.which("cloudflared")
    return Path(en_path) if en_path else None


async def descargar_cloudflared(carpeta: Path) -> Path | None:
    """Descarga cloudflared.exe (programa oficial de Cloudflare, ~60 MB) a la carpeta 'herramientas'."""
    if not sys.platform.startswith("win"):
        print("   ⚠️  Instala cloudflared (https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/"
              "downloads/) o ponlo en la carpeta 'herramientas'.", flush=True)
        return None
    import httpx
    destino = carpeta / "herramientas" / "cloudflared.exe"
    destino.parent.mkdir(exist_ok=True)
    tmp = destino.with_suffix(".tmp")
    print("   ⬇️  Descargando cloudflared de Cloudflare (solo la primera vez, ~60 MB)...", flush=True)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=httpx.Timeout(30, read=60)) as cliente:
            async with cliente.stream("GET", URL_DESCARGA_WINDOWS) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length") or 0)
                hecho, aviso = 0, 0
                with open(tmp, "wb") as f:
                    async for trozo in r.aiter_bytes(1 << 16):
                        f.write(trozo)
                        hecho += len(trozo)
                        if total and hecho * 10 // total > aviso:
                            aviso = hecho * 10 // total
                            print(f"      {aviso * 10}%", end="\r", flush=True)
        if tmp.stat().st_size < 5_000_000:
            raise RuntimeError("el archivo descargado es demasiado pequeño")
        os.replace(tmp, destino)
        print("   ✅ cloudflared descargado.          ", flush=True)
        return destino
    except Exception as ex:
        print(f"   ❌ No pude descargar cloudflared ({type(ex).__name__}: {str(ex)[:120]}).", flush=True)
        print(f"      Descárgalo a mano desde {URL_DESCARGA_WINDOWS}", flush=True)
        print(f"      y guárdalo como: {destino}", flush=True)
        try:
            tmp.unlink()
        except OSError:
            pass
        return None


class Tunel:
    def __init__(self, carpeta: Path, puerto: int):
        self.carpeta = carpeta
        self.puerto = puerto
        self.proc: asyncio.subprocess.Process | None = None
        self.url = ""
        self._lector: asyncio.Task | None = None

    async def abrir(self, espera: float = 45) -> str | None:
        exe = ruta_cloudflared(self.carpeta) or await descargar_cloudflared(self.carpeta)
        if not exe:
            return None
        args = [str(exe), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{self.puerto}"]
        # Comparte la ventana de Eduardo (no abre otra): al cerrar esa ventana o pulsar Ctrl+C,
        # Windows también cierra cloudflared, así no quedan túneles abiertos.
        try:
            self.proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE,
                                                             stderr=asyncio.subprocess.STDOUT,
                                                             stdin=asyncio.subprocess.DEVNULL)
        except OSError as ex:
            print(f"   ❌ No pude abrir cloudflared ({ex}).", flush=True)
            return None
        encontrado: asyncio.Future = asyncio.get_running_loop().create_future()

        async def leer() -> None:
            assert self.proc and self.proc.stdout
            async for linea in self.proc.stdout:
                texto = linea.decode("utf-8", "replace")
                m = _RE_URL.search(texto)
                if m and not encontrado.done():
                    encontrado.set_result(m.group(0))
                if "ERR" in texto and "trycloudflare" in texto and not encontrado.done():
                    log.debug("cloudflared: %s", texto.strip())
            if not encontrado.done():
                encontrado.set_result("")

        self._lector = asyncio.create_task(leer())
        try:
            self.url = await asyncio.wait_for(encontrado, timeout=espera)
        except asyncio.TimeoutError:
            self.url = ""
        if not self.url:
            print("   ❌ Cloudflare no me dio un enlace (¿sin internet o firewall?). Uso solo el avatar local.", flush=True)
            await self.cerrar()
            return None
        return self.url

    async def listo(self, ruta: str, intentos: int = 45) -> bool:
        """Espera a que el enlace nuevo funcione de verdad (Cloudflare tarda unos segundos)."""
        import httpx
        for _ in range(intentos):
            try:
                async with httpx.AsyncClient(timeout=6) as c:
                    r = await c.get(self.url + ruta)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(2)
        return False

    async def cerrar(self) -> None:
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.terminate()
                await asyncio.wait_for(self.proc.wait(), timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        if self._lector:
            self._lector.cancel()
