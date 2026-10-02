"""Memoria local de espectadores (se guarda en memoria.json, nunca sale de tu PC)."""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("eduardo")


def _ahora() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Recuerdo:
    """Lo que Eduardo sabe de un espectador ANTES de responderle."""
    nuevo: bool                 # nunca había usado el comando
    veces: int                  # veces que ha usado el comando (contando esta)
    lives: int                  # lives distintos en los que se le ha visto
    racha: int                  # lives seguidos en los que se le ha visto
    ultimo_mensaje: str         # lo último que le dijo a Eduardo (antes de este)
    ultima_respuesta: str       # lo último que Eduardo le respondió
    mensajes_chat: int          # mensajes normales del chat (sin comando)
    historial: list = field(default_factory=list)  # últimas charlas: [[lo que dijo, lo que respondió Eduardo], ...]

    def resumen_para_ia(self) -> str:
        if self.nuevo:
            partes = ["Es la PRIMERA vez que este espectador te habla: dale una bienvenida cálida."]
            if self.mensajes_chat > 5:
                partes.append(f"Aunque ya ha escrito {self.mensajes_chat} mensajes en el chat sin llamarte.")
            return " ".join(partes)
        partes = [f"Este espectador ya te conoce: es la vez número {self.veces} que te llama."]
        if self.lives > 1:
            partes.append(f"Ha estado en {self.lives} lives" + (f", {self.racha} seguidos" if self.racha > 1 else "") + ".")
        charlas = [h for h in self.historial if isinstance(h, (list, tuple)) and len(h) == 2][-3:]
        if charlas:
            partes.append("Lo último que hablaron (de más viejo a más nuevo):")
            for dijo, resp in charlas:
                partes.append(f'él/ella: "{dijo or "(solo te llamó)"}" / tú: "{resp}".')
            partes.append("No repitas esos chistes; si viene al caso, puedes retomar la conversación.")
        else:
            if self.ultimo_mensaje:
                partes.append(f'La última vez te dijo: "{self.ultimo_mensaje}".')
            if self.ultima_respuesta:
                partes.append(f'Y tú le respondiste: "{self.ultima_respuesta}". No repitas ese chiste.')
        return " ".join(partes)


class Memoria:
    def __init__(self, ruta: Path, activar: bool = True, recordar_chat: bool = True,
                 max_historial: int = 5, max_espectadores: int = 5000):
        self.ruta = ruta
        self.activar = activar
        self.recordar_chat = recordar_chat
        self.max_historial = max(1, int(max_historial))
        self.max_espectadores = max(50, int(max_espectadores))
        self.datos: dict = {"version": 1, "sesion_actual": 0, "espectadores": {}}
        self._sucio = False
        if activar:
            self._cargar()

    # --------------------------------------------------------------- archivo
    def _cargar(self) -> None:
        if not self.ruta.exists():
            return
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
            if isinstance(datos, dict) and isinstance(datos.get("espectadores"), dict):
                self.datos = datos
        except Exception as ex:
            respaldo = self.ruta.with_suffix(".danado.json")
            log.warning("memoria.json estaba dañado (%s). Lo guardo como %s y empiezo de cero.", ex, respaldo.name)
            try:
                os.replace(self.ruta, respaldo)
            except OSError:
                pass

    def guardar(self, forzar: bool = False) -> None:
        if not self.activar or (not self._sucio and not forzar):
            return
        self._recortar()
        tmp = self.ruta.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(self.datos, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.ruta)  # escritura atómica: no se corrompe si se cierra a la mitad
            self._sucio = False
        except OSError as ex:
            log.error("No pude guardar la memoria: %s", ex)

    def _recortar(self) -> None:
        esp = self.datos["espectadores"]
        if len(esp) <= self.max_espectadores:
            return
        # Se olvidan primero los que hace más tiempo que no aparecen
        orden = sorted(esp.items(), key=lambda kv: kv[1].get("ultima_vez", ""))
        for clave, _ in orden[: len(esp) - self.max_espectadores]:
            del esp[clave]

    @staticmethod
    def borrar_archivo(ruta: Path) -> bool:
        borrado = False
        for p in (ruta, ruta.with_suffix(".tmp")):
            if p.exists():
                p.unlink()
                borrado = True
        return borrado

    # --------------------------------------------------------------- sesiones
    def nueva_sesion(self) -> int:
        """Llamar una vez por cada LIVE (o simulación)."""
        if not self.activar:
            return 0
        self.datos["sesion_actual"] = int(self.datos.get("sesion_actual", 0)) + 1
        self._sucio = True
        self.guardar()
        return self.datos["sesion_actual"]

    @property
    def sesion(self) -> int:
        return int(self.datos.get("sesion_actual", 0))

    @property
    def total(self) -> int:
        return len(self.datos["espectadores"])

    # ---------------------------------------------------------- espectadores
    def _ficha(self, uid: str, nombre: str, crear: bool = True) -> dict | None:
        esp = self.datos["espectadores"]
        f = esp.get(uid)
        if f is None:
            if not crear:
                return None
            f = esp[uid] = {"nombre": nombre, "primera_vez": _ahora(), "ultima_vez": _ahora(),
                            "veces_comando": 0, "mensajes_chat": 0, "lives_vistos": 0,
                            "racha_lives": 0, "ultima_sesion": 0, "mensajes": [], "respuestas": []}
        f["nombre"] = nombre or f.get("nombre", "")
        f["ultima_vez"] = _ahora()
        sesion = self.sesion
        if f.get("ultima_sesion", 0) != sesion:
            f["racha_lives"] = f.get("racha_lives", 0) + 1 if f.get("ultima_sesion", 0) == sesion - 1 else 1
            f["lives_vistos"] = f.get("lives_vistos", 0) + 1
            f["ultima_sesion"] = sesion
        self._sucio = True
        return f

    def vio_chat(self, uid: str, nombre: str) -> None:
        """Mensaje normal (sin comando). Registro ligero."""
        if not (self.activar and self.recordar_chat):
            return
        f = self._ficha(uid, nombre)
        f["mensajes_chat"] = f.get("mensajes_chat", 0) + 1

    def recordar(self, uid: str, nombre: str) -> Recuerdo:
        """Devuelve lo que se sabe del espectador y cuenta este nuevo uso del comando."""
        if not self.activar:
            return Recuerdo(True, 1, 1, 1, "", "", 0)
        f = self._ficha(uid, nombre)
        antes = f.get("veces_comando", 0)
        f["veces_comando"] = antes + 1
        return Recuerdo(
            nuevo=antes == 0,
            veces=antes + 1,
            lives=f.get("lives_vistos", 1),
            racha=f.get("racha_lives", 1),
            ultimo_mensaje=(f["mensajes"][-1] if f.get("mensajes") else ""),
            ultima_respuesta=(f["respuestas"][-1] if f.get("respuestas") else ""),
            mensajes_chat=f.get("mensajes_chat", 0),
            historial=list(f.get("historial", [])),
        )

    def anotar(self, uid: str, mensaje: str, respuesta: str) -> None:
        """Guarda lo que dijo el espectador y lo que respondió Eduardo."""
        if not self.activar:
            return
        f = self.datos["espectadores"].get(uid)
        if f is None:
            return
        if mensaje:
            f["mensajes"] = (f.get("mensajes", []) + [mensaje])[-self.max_historial:]
        f["respuestas"] = (f.get("respuestas", []) + [respuesta])[-self.max_historial:]
        f["historial"] = (f.get("historial", []) + [[mensaje, respuesta]])[-self.max_historial:]
        self._sucio = True
        self.guardar()
