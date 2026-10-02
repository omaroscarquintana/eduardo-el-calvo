"""
Eduardo el Calvo - Bot simpático y sarcástico con voz y avatar para TikTok LIVE.

Uso:
    python bot.py                    -> se conecta a tu LIVE (usuario en config.toml)
    python bot.py --simular          -> modo prueba: escribes mensajes falsos en la consola
    python bot.py --avatar-prueba    -> abre el avatar en el navegador + modo simulación
    python bot.py --probar-conexion  -> intenta conectarse una sola vez y dice qué pasó
    python bot.py --prueba-voz       -> Eduardo dice un chiste para probar el audio
    python bot.py --borrar-memoria   -> borra lo que Eduardo recuerda de los espectadores
    python bot.py --enlace           -> además crea un enlace https público para LIVE Studio (túnel gratis)
    python bot.py --configurar-voz   -> asistente para una voz más natural (Azure gratis / ElevenLabs)

Opciones extra:
    --usuario NOMBRE   usa otro usuario de TikTok (ignora el de config.toml)
    --sin-voz          genera los audios pero no los reproduce (se guardan en "audios")
    --sin-esperas      desactiva los tiempos de espera (solo para pruebas)
    --sin-avatar       no abre el servidor del avatar
    --ver-chat         muestra todos los mensajes del chat (no solo los comandos)
    --config RUTA      usa otro archivo de configuración
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import random
import re
import sys
import time
import unicodedata
import webbrowser
from collections import deque
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    print("Necesitas Python 3.11 o más nuevo. Instala Python 3.12 desde https://www.python.org")
    sys.exit(1)

from eduardo import escena as E
from eduardo.filtro import FiltroSeguridad, limpiar_nombre, limpiar_para_cita
from eduardo.memoria import Memoria
from eduardo.respuestas import (MODO_ANIMAL, MODO_CHISTE, MODO_NORMAL, GeneradorRespuestas, Respuesta,
                                detectar_risa)
from eduardo.respuestas import _RISA_RE as RISA_RE
from eduardo.voz import Voz

CARPETA = Path(__file__).resolve().parent
log = logging.getLogger("eduardo")

FRASE_DEMO = ("¡Hola, hola, amigos! ¡Soy Eduardo el Calvo! ¿Saben por qué nunca gano a las escondidas? "
              "¡Porque mi calva me delata desde lejos! ¡Ja, ja, ja! ¡Y ahora, una vaca! ¡Muuuuuuu!")


def configurar_consola() -> None:
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    for ruidoso in ("httpx", "aiohttp", "aiohttp.access", "TikTokLive"):
        logging.getLogger(ruidoso).setLevel(logging.WARNING)


def cargar_config(ruta: Path | None = None) -> dict:
    """config.toml (tuyo, nunca lo tocan las actualizaciones) + config.ejemplo.toml (de fábrica)."""
    from eduardo.configuracion import cargar_config as cargar_combinada
    try:
        return cargar_combinada(CARPETA, ruta)
    except FileNotFoundError:
        print(f"No encuentro el archivo de configuración: {ruta or CARPETA / 'config.toml'}")
        sys.exit(1)
    except tomllib.TOMLDecodeError as ex:
        print("Hay un error de escritura en config.toml (revisa comillas y signos =).")
        print(f"Detalle: {ex}")
        sys.exit(1)


def _plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _lista(valor, defecto: list[str]) -> list[str]:
    if valor is None:
        valor = defecto
    if isinstance(valor, str):
        valor = [valor]
    return [str(v).strip() for v in valor if str(v).strip()]


@dataclass
class Pedido:
    uid: str
    nombre: str
    mensaje: str
    modo: str = MODO_NORMAL
    bloqueado: bool = False
    texto_fijo: str = ""
    id_contexto: int = -1
    accion: str = ""     # "", "ruleta", "disfraz", "quitar", "gesto"
    extra: str = ""      # nombre del disfraz o del gesto


class Eduardo:
    """Cerebro del bot: detecta el comando, aplica esperas/filtro/memoria y encola respuestas."""

    def __init__(self, cfg: dict, reproducir: bool = True, sin_esperas: bool = False):
        self.cfg = cfg
        lim = cfg.get("limites", {})
        seg = cfg.get("seguridad", {})
        arch = cfg.get("archivos", {})
        com = cfg.get("comando", {})
        mem = cfg.get("memoria", {})

        self.activadores = _lista(com.get("activadores"), ["!Edu"])
        alternativas = "|".join(re.escape(a) for a in sorted(self.activadores, key=len, reverse=True))
        # El mensaje debe EMPEZAR con el comando, y el comando no puede seguir con letras
        # (así "!Edu" no se activa con "!Eduardo").
        self._re_comando = re.compile(rf"^\s*(?:{alternativas})(?![\w])[\s,.:;!?-]*(.*)$",
                                      re.IGNORECASE | re.DOTALL)
        self.palabras_chiste = {_plano(p) for p in _lista(com.get("palabras_chiste"), ["chiste", "broma"])}
        self.palabras_animal = {_plano(p) for p in _lista(com.get("palabras_animal"), ["animal", "imita"])}

        self.espera_usuario = 0 if sin_esperas else float(lim.get("espera_por_usuario_segundos", 60))
        self.espera_global = 0 if sin_esperas else float(lim.get("espera_global_segundos", 8))
        self.largo_cita = int(lim.get("largo_maximo_cita", 60))
        self.cola: asyncio.Queue[Pedido] = asyncio.Queue(maxsize=max(1, int(lim.get("cola_maxima", 5))))

        self.responder_bloqueados = bool(seg.get("responder_a_mensajes_bloqueados", True))
        self.filtro = FiltroSeguridad(CARPETA / arch.get("archivo_palabras_prohibidas", "palabras_prohibidas.txt"),
                                      bloquear_enlaces=bool(seg.get("bloquear_enlaces", True)))
        self.generador = GeneradorRespuestas(cfg, CARPETA, self.filtro)
        self.voz = Voz(cfg, CARPETA, reproducir=reproducir)
        self.leer_nombre_antes = bool(cfg.get("voz", {}).get("leer_nombre_antes", False))
        self.memoria = Memoria(CARPETA / mem.get("archivo", "memoria.json"),
                               activar=bool(mem.get("activar", True)),
                               recordar_chat=bool(mem.get("recordar_chat_sin_comando", True)),
                               max_historial=int(mem.get("max_historial", 5)),
                               max_espectadores=int(mem.get("max_espectadores", 5000)))
        self.avatar = None  # ServidorAvatar (opcional)
        # Últimos mensajes del chat del live (para que la IA entienda la conversación)
        self.chat_reciente: deque[tuple[float, str]] = deque(maxlen=max(0, int(cfg.get("ia", {}).get("contexto_chat_mensajes", 8))))
        self._id_ctx = 0

        self._ultimo_por_usuario: dict[str, float] = {}
        self._ultimo_global = 0.0
        self.respuestas_dadas: list[Respuesta] = []

        # ---- Ruleta, disfraces y gestos
        ru = cfg.get("ruleta", {})
        self.ruleta_activa = bool(ru.get("activar", True))
        self.palabras_ruleta = {_plano(x) for x in _lista(ru.get("palabras"), ["ruleta", "gira", "girar"])}
        self.ruleta_espera = 0 if sin_esperas else float(ru.get("espera_segundos", 90))
        self.ruleta_excluir = bool(ru.get("excluir_quien_pide", True))
        self.ruleta_ventana = float(ru.get("ventana_minutos", 10)) * 60
        self.ruleta_categorias, self.ruleta_pesos = self._categorias_ruleta(ru)
        self._ultima_ruleta = -1e9
        di = cfg.get("disfraces", {})
        self.disfraces_activos = bool(di.get("activar", True))
        self.gestos_activos = bool(di.get("gestos", True))
        self.disfraz_minutos = float(di.get("duracion_minutos", 10))
        self.palabras_disfraz = {_plano(x) for x in _lista(di.get("palabras_disfraz"), ["disfraz", "disfrazate", "ponte"])}
        self.palabras_quitar = {_plano(x) for x in _lista(di.get("palabras_quitar"), ["quitar", "quitate", "quita"])}
        # Quién escribió hace poco en el chat (para la ruleta): uid -> (nombre, momento)
        self.activos: dict[str, tuple[str, float]] = {}

    @staticmethod
    def _categorias_ruleta(ru: dict) -> tuple[list[str], list[float]]:
        cats = [_plano(c) for c in _lista(ru.get("categorias"), list(E.CATEGORIAS_RULETA))]
        cats = [c for c in cats if c in E.CATEGORIAS_RULETA] or list(E.CATEGORIAS_RULETA)
        pesos_cfg = ru.get("pesos", {})
        if isinstance(pesos_cfg, dict):
            pesos = [float(pesos_cfg.get(c, 1)) for c in cats]
        else:
            pesos = [float(x) for x in list(pesos_cfg)[:len(cats)]] + [1.0] * (len(cats) - len(list(pesos_cfg)[:len(cats)]))
        if not any(w > 0 for w in pesos):
            pesos = [1.0] * len(cats)
        return cats, [max(0.0, w) for w in pesos]

    def _anotar_activo(self, uid: str, nombre: str) -> None:
        if nombre and nombre != "amigo":
            self.activos[uid] = (nombre, time.monotonic())
            if len(self.activos) > 400:
                for viejo in sorted(self.activos, key=lambda k: self.activos[k][1])[:100]:
                    self.activos.pop(viejo, None)

    def elegir_para_ruleta(self, uid_pide: str, nombre_pide: str) -> tuple[str, list[str]]:
        """Elige a alguien que escribió en el chat hace poco. Devuelve (elegido, nombres para la animación)."""
        ahora = time.monotonic()
        recientes = {u: n for u, (n, t) in self.activos.items() if ahora - t <= self.ruleta_ventana}
        candidatos = {u: n for u, n in recientes.items() if not (self.ruleta_excluir and u == uid_pide)}
        if not candidatos:
            candidatos = recientes or {uid_pide: nombre_pide}
        elegido = random.choice(list(candidatos.values()))
        nombres = list(dict.fromkeys(list(recientes.values()) + [nombre_pide]))
        random.shuffle(nombres)
        nombres = nombres[:10]
        if elegido not in nombres:
            nombres[-1:] = [elegido]
        return elegido, nombres

    def detectar_accion(self, resto: str) -> tuple[str, str]:
        """'ruleta' / 'disfraz corona' / 'quitar' / 'baila' -> (accion, extra). Si no es nada de eso: ('', '')."""
        partes = resto.split(maxsplit=1)
        if not partes:
            return "", ""
        primera = _plano(partes[0]).strip(".,;:!?¡¿")
        sobra = partes[1] if len(partes) > 1 else ""
        if self.ruleta_activa and primera in self.palabras_ruleta:
            return "ruleta", ""
        if self.disfraces_activos and primera in self.palabras_disfraz:
            if _plano(sobra) in ("", "random", "azar", "al azar", "sorpresa", "cualquiera"):
                return "disfraz", ""
            return "disfraz", E.buscar_disfraz(sobra) or "?"
        if self.disfraces_activos and primera in self.palabras_quitar:
            return "quitar", ""
        if self.gestos_activos:
            g = E.buscar_gesto(primera)
            if g:
                return "gesto", g
        return "", ""

    # ------------------------------------------------------------ chat entrante
    def extraer_comando(self, texto: str) -> str | None:
        """Si el texto empieza con el comando devuelve lo que viene después (puede ser ''), si no None."""
        m = self._re_comando.match(texto or "")
        return m.group(1).strip() if m else None

    def detectar_modo(self, resto: str) -> tuple[str, str]:
        """'chiste de perros' -> (chiste, 'de perros'). Si no hay sub-comando: (normal, resto)."""
        partes = resto.split(maxsplit=1)
        if not partes:
            return MODO_NORMAL, ""
        primera = _plano(partes[0]).strip(".,;:!?¡¿")
        sobra = partes[1] if len(partes) > 1 else ""
        if primera in self.palabras_chiste:
            return MODO_CHISTE, sobra
        if primera in self.palabras_animal:
            return MODO_ANIMAL, sobra
        return MODO_NORMAL, resto

    def _anotar_contexto(self, nombre: str, texto: str) -> int:
        """Guarda una línea del chat (solo si es segura) para dar contexto a la IA."""
        texto = re.sub(r"\s+", " ", texto or "").strip()
        if not texto or self.chat_reciente.maxlen == 0 or not self.filtro.es_seguro(texto):
            return -1
        self._id_ctx += 1
        self.chat_reciente.append((self._id_ctx, f"{nombre}: {texto[:120]}"))
        return self._id_ctx

    def contexto_para(self, id_pedido: int = -1) -> list[str]:
        """Lo que se dijo en el chat ANTES de este mensaje (en orden), sin el mensaje mismo."""
        if id_pedido < 0:
            return [linea for _, linea in sorted(self.chat_reciente, key=lambda x: x[0])]
        return [linea for i, linea in sorted(self.chat_reciente, key=lambda x: x[0]) if i < id_pedido]

    def recibir(self, usuario_id: str, nombre: str, texto: str) -> str:
        """Procesa un mensaje del chat. Devuelve qué se hizo (para mostrarlo en consola)."""
        resto = self.extraer_comando(texto)
        if resto is None:
            n = limpiar_nombre(nombre) or "amigo"
            n = "amigo" if self.filtro.es_ofensivo(nombre) else n
            self.memoria.vio_chat(usuario_id, n)
            self._anotar_contexto(n, texto)
            self._anotar_activo(usuario_id, n)
            return "no es comando"

        ahora = time.monotonic()
        accion, extra = self.detectar_accion(resto)
        gesto_forzado = ""
        if accion == "gesto" and len(resto.split()) > 1 and self.generador.usar_ia:
            # "!Edu baila que ganamos" con IA: contesta de verdad y además hace el gesto
            accion, gesto_forzado = "", extra
        if accion == "ruleta" and ahora - self._ultima_ruleta < self.ruleta_espera:
            return f"ignorado: la ruleta descansa {int(self.ruleta_espera - (ahora - self._ultima_ruleta))} s más"
        if accion == "disfraz" and extra == "?":
            return "ignorado: no conozco ese disfraz (" + ", ".join(E.DISFRACES) + ")"
        ultimo = self._ultimo_por_usuario.get(usuario_id)
        if ultimo is not None and ahora - ultimo < self.espera_usuario:
            return f"ignorado: {nombre} debe esperar {int(self.espera_usuario - (ahora - ultimo))} s más"
        if ahora - self._ultimo_global < self.espera_global:
            return "ignorado: espera global (demasiados comandos seguidos)"
        if self.cola.full():
            return "ignorado: la cola está llena"

        nombre_limpio = limpiar_nombre(nombre) or "amigo"
        if self.filtro.es_ofensivo(nombre_limpio) or self.filtro.es_ofensivo(nombre):
            nombre_limpio = "amigo"
        self._anotar_activo(usuario_id, nombre_limpio)

        if accion:
            self._ultimo_por_usuario[usuario_id] = ahora
            self._ultimo_global = ahora
            if accion == "ruleta":
                self._ultima_ruleta = ahora
            self.cola.put_nowait(Pedido(usuario_id, nombre_limpio, "", accion=accion, extra=extra))
            return f"en cola ({accion}{' ' + extra if extra else ''})"

        modo, resto = self.detectar_modo(resto)
        bloqueado = not self.filtro.es_seguro(resto)
        if bloqueado and not self.responder_bloqueados:
            return "ignorado: mensaje bloqueado por el filtro de seguridad"
        mensaje = "" if bloqueado else limpiar_para_cita(resto, self.largo_cita)

        self._ultimo_por_usuario[usuario_id] = ahora
        self._ultimo_global = ahora
        id_ctx = -1 if bloqueado else self._anotar_contexto(nombre_limpio, texto)
        self.cola.put_nowait(Pedido(usuario_id, nombre_limpio, mensaje, modo, bloqueado, id_contexto=id_ctx,
                                    extra=gesto_forzado))
        if bloqueado:
            return "bloqueado por el filtro: Eduardo lo esquivará"
        return "en cola" + ("" if modo == MODO_NORMAL else f" (modo {modo})")

    # ---------------------------------------------------------- trabajador voz
    async def _decir(self, resp: Respuesta) -> str:
        """Genera el audio y lo reproduce en el avatar o en la PC (nunca en los dos)."""
        hablado = resp.texto
        ruta = await self.voz.intentar_generar(hablado)
        if ruta is not None and resp.reir:
            # Con pausas naturales sabemos en qué segundo exacto empieza la risa
            exacto = self.voz.fraccion_de(RISA_RE)
            if exacto is not None:
                resp.reir_desde = exacto
        av = self.avatar if (self.avatar and self.avatar.clientes) else None
        if ruta is None:
            if av:
                asyncio.ensure_future(av.hablar(None, resp.texto, resp.reir, resp.reir_desde, permitir_sonido=False,
                                                gesto=resp.gesto))
            return "voz del sistema" if await self.voz.hablar_sistema(hablado) else "sin voz"
        if not self.voz.reproducir:
            if av:
                await av.hablar(ruta, resp.texto, resp.reir, resp.reir_desde, permitir_sonido=False, gesto=resp.gesto)
            return f"audio generado (sin reproducir): {ruta.name}"
        if av and await av.hablar(ruta, resp.texto, resp.reir, resp.reir_desde, gesto=resp.gesto):
            self.voz.limpiar(ruta)
            return "sonó en el avatar"
        if await self.voz.reproducir_pc(ruta):
            self.voz.limpiar(ruta)
            return "sonó en la PC" + (" (el avatar movió la boca)" if av else "")
        return f"audio generado pero no reproducido: {ruta.name}"

    async def trabajador(self) -> None:
        """Atiende la cola de a uno, para que las voces nunca se encimen."""
        while True:
            pedido = await self.cola.get()
            try:
                if pedido.accion:
                    await self._accion(pedido)
                    continue
                if pedido.texto_fijo:
                    reir, desde = detectar_risa(pedido.texto_fijo, False)
                    resp = Respuesta(pedido.texto_fijo, "demo", reir, desde)
                elif pedido.bloqueado:
                    resp = self.generador.respuesta_esquive(pedido.nombre)
                else:
                    recuerdo = self.memoria.recordar(pedido.uid, pedido.nombre)
                    resp = await self.generador.generar(pedido.nombre, pedido.mensaje, pedido.modo, recuerdo,
                                                        self.contexto_para(pedido.id_contexto))
                    if pedido.extra:
                        resp.gesto = pedido.extra
                    etiqueta = "nuevo" if recuerdo.nuevo else f"{recuerdo.veces}ª vez"
                    print(f"   🧠 {pedido.nombre}: {etiqueta}, {recuerdo.lives} live(s)"
                          + (f", racha {recuerdo.racha}" if recuerdo.racha > 1 else ""), flush=True)
                if self.leer_nombre_antes and not pedido.texto_fijo:
                    resp.texto = f"{pedido.nombre}: {resp.texto}"
                self.respuestas_dadas.append(resp)
                self._mostrar(resp)
                print(f"   🔊 {await self._decir(resp)}", flush=True)
                if not pedido.bloqueado and not pedido.texto_fijo:
                    self.memoria.anotar(pedido.uid, pedido.mensaje, resp.texto)
                    if self.chat_reciente.maxlen:
                        # Se ordena justo después del mensaje al que responde
                        orden = (pedido.id_contexto if pedido.id_contexto >= 0 else self._id_ctx) + 0.5
                        self.chat_reciente.append((orden, f"Eduardo (tú) a {pedido.nombre}: {resp.texto}"))
            except Exception as ex:
                log.error("Error al responder: %s", ex)
            finally:
                self.cola.task_done()

    @staticmethod
    def _mostrar(resp: Respuesta) -> None:
        extras = (", se ríe" if resp.reir else "") + (f", gesto: {resp.gesto}" if resp.gesto else "")
        print(f"   🗣️  Eduardo ({resp.origen}{extras}): {resp.texto}", flush=True)

    async def _accion(self, pedido: Pedido) -> None:
        """Ruleta, disfraces y gestos."""
        av = self.avatar if (self.avatar and self.avatar.clientes) else None
        valores = {"nombre": pedido.nombre}
        if pedido.accion == "ruleta":
            elegido, nombres = self.elegir_para_ruleta(pedido.uid, pedido.nombre)
            i = random.choices(range(len(self.ruleta_categorias)), weights=self.ruleta_pesos)[0]
            cat = self.ruleta_categorias[i]
            print(f"   🎡 Ruleta: le tocó a {elegido} → {E.CATEGORIAS_RULETA[cat]}", flush=True)
            # La frase se prepara MIENTRAS gira la ruleta (así no hay silencio al final)
            tarea = asyncio.ensure_future(self.generador.generar_ruleta(elegido, cat, self.contexto_para()))
            if av:
                duracion = 4.6
                await av.ruleta(nombres, elegido, [E.CATEGORIAS_RULETA[c] for c in self.ruleta_categorias], i, duracion)
                await asyncio.sleep(duracion + 0.7)
            resp = await tarea
            self.respuestas_dadas.append(resp)
            self._mostrar(resp)
            print(f"   🔊 {await self._decir(resp)}", flush=True)
            if self.chat_reciente.maxlen:
                self.chat_reciente.append((self._id_ctx + 0.5, f"Eduardo (tú), en la ruleta, a {elegido}: {resp.texto}"))
            if self.avatar:
                async def cerrar() -> None:
                    await asyncio.sleep(3)
                    await self.avatar.fin_ruleta()
                asyncio.ensure_future(cerrar())
            return
        if pedido.accion == "disfraz":
            actual = self.avatar.disfraz_actual if self.avatar else ""
            nombre = pedido.extra or E.disfraz_al_azar(evitar=actual)
            valores["disfraz"] = ("mis " if nombre == "lentes" else "mi ") + E.DISFRACES[nombre][0]
            if self.avatar:
                await self.avatar.poner_disfraz(nombre, self.disfraz_minutos)
            print(f"   🎩 Disfraz: {E.DISFRACES[nombre][0]}"
                  + (f" (se lo quita en {self.disfraz_minutos:g} min)" if self.disfraz_minutos > 0 else ""), flush=True)
            resp = self.generador.frase_de("disfraz", valores, gesto="guino")
        elif pedido.accion == "quitar":
            if self.avatar:
                await self.avatar.poner_disfraz("")
            resp = self.generador.frase_de("quitar_disfraz", valores, respaldo="¡Listo, {nombre}! Calva al natural.")
        else:  # gesto
            resp = self.generador.frase_de("gesto_" + pedido.extra, valores, gesto=pedido.extra,
                                           respaldo="¡Para ti, {nombre}!")
        self.respuestas_dadas.append(resp)
        self._mostrar(resp)
        print(f"   🔊 {await self._decir(resp)}", flush=True)

    async def guardado_periodico(self) -> None:
        while True:
            await asyncio.sleep(30)
            self.memoria.guardar()

    def resumen_inicio(self) -> None:
        g = self.generador
        print("=" * 66)
        print("  👨‍🦲  EDUARDO EL CALVO - bot simpático y sarcástico para TikTok LIVE")
        print("=" * 66)
        print(f"  Comando(s): {', '.join(self.activadores)}  (da igual mayúsculas o minúsculas)")
        a0 = self.activadores[0]
        print(f"  Sub-comandos: {a0} chiste  |  {a0} animal  |  {a0} ruleta  |  {a0} disfraz [nombre]  |  {a0} quitar")
        print(f"  Gestos: {a0} baila | saluda | sorpresa | guiña | enójate | triste")
        if g.usar_ia:
            print(f"  Respuestas: IA {g.proveedor} ({g.modelo}) — contesta de verdad a cada comentario."
                  f"  Respaldo: {g.total_frases} frases")
        else:
            print(f"  Respuestas: frases de respaldo por tipo de comentario [{g.total_frases} frases]")
            if g.ia_pedida_sin_clave:
                print("  💡 Para que Eduardo conteste DE VERDAD a cada comentario, activa la IA GRATIS:"
                      " abre configurar_ia.bat (2 minutos).")
        print(f"  Voz: {self.voz.descripcion()}   "
              f"Filtro: {self.filtro.cantidad} palabras prohibidas")
        print(f"  Esperas: {int(self.espera_usuario)} s por persona, {int(self.espera_global)} s global")
        if self.memoria.activar:
            print(f"  Memoria: {self.memoria.total} espectador(es) recordados ({self.memoria.ruta.name})")
        else:
            print("  Memoria: apagada")
        if self.avatar:
            print(f"  Avatar: {self.avatar.url}   (sonido: {self.avatar.modo_audio})")
        print("=" * 66, flush=True)


# =================================================================== TikTok
async def conectar_tiktok(bot: Eduardo, usuario: str, reintentar: float, clave_euler: str,
                          solo_una_vez: bool = False, ver_chat: bool = False) -> bool:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.client.errors import SignAPIError, UserNotFoundError, UserOfflineError
    from TikTokLive.client.web.web_settings import WebDefaults
    from TikTokLive.events import CommentEvent, DisconnectEvent, LiveEndEvent

    logging.getLogger("TikTokLive").setLevel(logging.CRITICAL)
    if clave_euler:
        WebDefaults.tiktok_sign_api_key = clave_euler
    sesion_iniciada = False

    while True:
        cliente = TikTokLiveClient(unique_id=usuario)
        cliente.logger.setLevel(logging.CRITICAL)

        async def al_comentar(evento: CommentEvent) -> None:
            u = evento.user
            nombre = (getattr(u, "nickname", "") or getattr(u, "display_id", "") or "alguien") if u else "alguien"
            # El id numérico de TikTok no cambia aunque la persona cambie su nombre o @usuario.
            usuario_id = str(getattr(u, "id", "") or getattr(u, "display_id", "") or nombre) if u else nombre
            texto = evento.comment or ""
            resultado = bot.recibir(usuario_id, nombre, texto)
            if resultado != "no es comando":
                print(f"💬 {nombre}: {texto}   → {resultado}", flush=True)
            elif ver_chat:
                print(f"   · {nombre}: {texto}", flush=True)

        async def al_terminar(evento: LiveEndEvent) -> None:
            print("📴 El LIVE terminó.", flush=True)

        async def al_desconectar(evento: DisconnectEvent) -> None:
            print("🔌 Se perdió la conexión con el LIVE.", flush=True)

        cliente.add_listener(CommentEvent, al_comentar)
        cliente.add_listener(LiveEndEvent, al_terminar)
        cliente.add_listener(DisconnectEvent, al_desconectar)

        espera = reintentar
        try:
            print(f"🔎 Buscando el LIVE de @{usuario.lstrip('@')}...", flush=True)
            # process_connect_events=False: no responder a mensajes viejos del historial
            tarea = await cliente.start(process_connect_events=False, fetch_live_check=True)
            print(f"✅ ¡Conectado al LIVE de @{cliente.unique_id}! Eduardo está escuchando el chat.", flush=True)
            if solo_una_vez:
                print("   (Modo prueba de conexión: me desconecto.)")
                return True
            if not sesion_iniciada:
                sesion_iniciada = True
                print(f"🧠 LIVE número {bot.memoria.nueva_sesion()} en la memoria de Eduardo.", flush=True)
            await tarea
            print(f"🔁 Desconectado. Vuelvo a intentar en {int(espera)} s...", flush=True)
        except UserOfflineError:
            print(f"⏳ @{usuario.lstrip('@')} no está en LIVE ahora mismo."
                  + ("" if solo_una_vez else f" Reintento en {int(espera)} s... (Ctrl+C para salir)"), flush=True)
        except UserNotFoundError:
            espera = max(reintentar, 60)
            print(f"❓ TikTok dice que @{usuario.lstrip('@')} no existe, nunca ha hecho LIVE o no puede hacer LIVE."
                  " Revisa el usuario en config.toml." + ("" if solo_una_vez else f" Reintento en {int(espera)} s..."),
                  flush=True)
        except SignAPIError as ex:
            espera = max(reintentar, 120)
            if ex.reason == SignAPIError.ErrorReason.RATE_LIMIT:
                print("🚦 Se alcanzó el límite gratuito del servidor de firmas (Euler Stream)."
                      " Espera un rato o pon una clave gratuita en config.toml → clave_euler_stream.", flush=True)
            else:
                print(f"⚠️  Problema con el servidor de firmas de Euler Stream ({ex.reason.name}).", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as ex:
            print(f"⚠️  No pude conectarme ({type(ex).__name__}): {str(ex)[:200]}", flush=True)
        finally:
            # Nota: no usamos disconnect(close_client=True) porque en TikTokLive 7.0.1
            # intenta cerrar tareas del bucle de asyncio y puede cancelar a Eduardo.
            try:
                await cliente.disconnect()
            except Exception:
                pass
            try:
                await cliente.web.close()
            except Exception:
                pass

        if solo_una_vez:
            return False
        await asyncio.sleep(espera)


# ================================================================ simulación
_RE_SIM = re.compile(r"^\s*([^:!]{1,30}?)\s*:\s*(.*)$")


async def modo_simulacion(bot: Eduardo) -> None:
    print(f"🧪 MODO SIMULACIÓN: escribe mensajes como si fueras el chat.  (sesión de memoria nº {bot.memoria.nueva_sesion()})")
    print(f"   Formato:  Nombre: mensaje      (ej:  Pepito: {bot.activadores[0]} qué onda pelón)")
    print(f"   Prueba también:  Pepito: {bot.activadores[0]} chiste    y    Pepito: {bot.activadores[0]} animal")
    print("   Si no pones nombre, se usa 'Espectador'. Escribe 'salir' para terminar.\n", flush=True)
    while True:
        try:
            linea = await asyncio.to_thread(input, "> ")
        except (EOFError, KeyboardInterrupt):
            break
        linea = linea.strip()
        if not linea:
            continue
        if linea.lower() in ("salir", "exit", "quit"):
            break
        m = _RE_SIM.match(linea)
        nombre, texto = (m.group(1).strip(), m.group(2)) if m else ("Espectador", linea)
        resultado = bot.recibir("sim:" + nombre.lower(), nombre, texto)
        print(f"💬 {nombre}: {texto}   → {resultado}", flush=True)
        await asyncio.sleep(0.05)
    await bot.cola.join()  # espera a que Eduardo termine de hablar lo pendiente
    print("👋 Fin de la simulación.")


PAGINAS_CLAVE = {
    "groq": ("Groq", "https://console.groq.com/keys", "gsk_"),
    "gemini": ("Google Gemini", "https://aistudio.google.com/apikey", "AIza"),
}


async def configurar_ia(cfg: dict) -> bool:
    """Asistente para pegar la clave de la IA gratis una sola vez (se guarda en ia_local.toml)."""
    from eduardo.respuestas import ARCHIVO_CLAVE_LOCAL, guardar_clave_local

    print("=" * 66)
    print("  🤖  CONFIGURAR LA IA GRATIS DE EDUARDO (solo una vez)")
    print("=" * 66)
    print("  Con IA, Eduardo entiende cada comentario y contesta de verdad.\n")
    print("  1) Groq           - RECOMENDADO: gratis, sin tarjeta, muy rápido")
    print("  2) Google Gemini  - gratis (con tu cuenta de Google)")
    print("  3) Quitar la clave guardada (volver a frases sin IA)\n")
    opcion = (await asyncio.to_thread(input, "  Escribe 1, 2 o 3 y pulsa Enter [1]: ")).strip() or "1"
    if opcion == "3":
        ruta = CARPETA / ARCHIVO_CLAVE_LOCAL
        if ruta.exists():
            ruta.unlink()
        print("  ✅ Listo, se quitó la clave guardada. Eduardo usará frases sin IA.")
        return False
    proveedor = "gemini" if opcion == "2" else "groq"
    nombre, url, prefijo = PAGINAS_CLAVE[proveedor]
    print(f"\n  Voy a abrir la página de {nombre} en tu navegador: {url}")
    if proveedor == "groq":
        print("  → Entra con tu correo o con Google, pulsa 'Create API Key', ponle de nombre 'Eduardo'")
        print("    y copia la clave (empieza con gsk_). Solo se muestra una vez.")
    else:
        print("  → Entra con tu cuenta de Google, pulsa 'Create API key' y copia la clave (empieza con AIza).")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    for _ in range(3):
        clave = (await asyncio.to_thread(input, "\n  Pega aquí tu clave (clic derecho o Ctrl+V) y pulsa Enter: ")).strip()
        clave = clave.strip('"').strip("'").strip()
        if len(clave) >= 20 and " " not in clave:
            break
        print("  ⚠️  Eso no parece una clave completa. Cópiala otra vez, entera.")
    else:
        print("  ❌ No se guardó nada. Vuelve a abrir configurar_ia.bat cuando tengas la clave.")
        return False
    if not clave.startswith(prefijo):
        print(f"  (Aviso: las claves de {nombre} suelen empezar con {prefijo}. La guardo igual y la pruebo.)")
    ruta = guardar_clave_local(CARPETA, proveedor, clave)
    print(f"  💾 Clave guardada en tu PC ({ruta.name}). No compartas ese archivo.\n")
    return True


AZURE_REGIONES = {"eastus": "East US", "eastus2": "East US 2", "westus": "West US", "westus2": "West US 2",
                  "southcentralus": "South Central US", "centralus": "Central US", "brazilsouth": "Brazil South",
                  "westeurope": "West Europe", "northeurope": "North Europe", "francecentral": "France Central"}
FRASE_PRUEBA_VOZ = "¡Hola, Omar! Soy Eduardo con mi voz nueva. ¿Qué tal me escucho? ¡Ja, ja, ja! ¡Mi calva está feliz!"


async def _preguntar(texto: str) -> str:
    return (await asyncio.to_thread(input, texto)).strip().strip('"').strip("'").strip()


async def configurar_voz(cfg: dict) -> int:
    """Asistente para una voz más natural. La clave se guarda en voz_local.toml (nunca se comparte)."""
    from eduardo.voz import ARCHIVO_VOZ_LOCAL, guardar_voz_local

    print("=" * 66)
    print("  🎙️  CONFIGURAR LA VOZ DE EDUARDO (opcional)")
    print("=" * 66)
    print("  Ahora Eduardo usa la voz gratis de Microsoft Edge (no necesita nada).")
    print("  Si quieres una voz con más emoción:\n")
    print("  1) Azure Speech   - RECOMENDADO: gratis 500.000 letras al mes (unas 5.000 respuestas).")
    print("                      Voz Jorge de México en estilo ALEGRE. Pide tarjeta solo para verificar")
    print("                      tu identidad (el plan Free F0 no cobra).")
    print("  2) ElevenLabs     - La voz más natural y con risa real, pero gratis solo 10.000 letras al")
    print("                      mes (unas 100 respuestas), SOLO uso no comercial y hay que dar crédito.")
    print("  3) Volver a la voz gratis de siempre (Edge)\n")
    opcion = await _preguntar("  Escribe 1, 2 o 3 y pulsa Enter [1]: ") or "1"
    if opcion == "3":
        ruta = CARPETA / ARCHIVO_VOZ_LOCAL
        if ruta.exists():
            ruta.unlink()
        print("  ✅ Listo. Eduardo usa otra vez la voz gratis de Edge (con risas grabadas).")
        return 0
    if opcion == "2":
        url = "https://elevenlabs.io/app/settings/api-keys"
        print(f"\n  Voy a abrir ElevenLabs: {url}")
        print("  → Crea tu cuenta gratis, pulsa 'Create API Key' (Crear clave), dale permiso de")
        print("    'Text to Speech' y copia la clave (empieza con sk_).")
        print("  ⚠️  Plan gratis: NO es para uso comercial y debes poner 'elevenlabs.io' en el título")
        print("     o descripción del live. Si ganas dinero con tus lives, usa el plan Starter (5-6 USD/mes).")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        clave = await _preguntar("\n  Pega aquí tu clave de ElevenLabs y pulsa Enter: ")
        if len(clave) < 20 or " " in clave:
            print("  ❌ Eso no parece una clave completa. No se guardó nada.")
            return 1
        print("\n  Ahora elige la voz: en ElevenLabs entra a 'Voices' → 'Voice Library', filtra")
        print("  Idioma: Spanish, Género: Male, escucha y pulsa 'Add to my voices'. Luego en")
        print("  'My Voices' abre la voz → botón '...' → 'Copy voice ID'.")
        voz_id = await _preguntar("  Pega el Voice ID (o deja vacío para una voz de ejemplo): ") or "JBFqnCBsd6RMkjVDRZzb"
        datos = {"proveedor": "elevenlabs", "clave": clave, "voz_id": voz_id}
    else:
        url = "https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices"
        print(f"\n  Voy a abrir el portal de Azure: {url}")
        print("  Pasos (5 minutos, solo una vez):")
        print("   1. Entra con tu cuenta Microsoft (o crea la cuenta gratis de Azure).")
        print("   2. Grupo de recursos: 'Crear nuevo' → escribe eduardo.")
        print("   3. Región: East US (o la más cercana). Nombre: eduardo-voz-" + str(random.randint(100, 999)) + ".")
        print("   4. Plan de tarifa (Pricing tier): Free F0.  → 'Revisar y crear' → 'Crear'.")
        print("   5. 'Ir al recurso' → menú 'Claves y punto de conexión' → copia la CLAVE 1")
        print("      y fíjate en la 'Ubicación/Región' (por ejemplo eastus).")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        clave = await _preguntar("\n  Pega aquí la CLAVE 1 y pulsa Enter: ")
        if len(clave) < 20 or " " in clave:
            print("  ❌ Eso no parece una clave completa. No se guardó nada.")
            return 1
        region = await _preguntar("  Escribe la región (Enter = eastus): ") or "eastus"
        region = re.sub(r"[^a-z0-9]", "", region.lower())
        region = next((k for k, v in AZURE_REGIONES.items() if re.sub(r"[^a-z0-9]", "", v.lower()) == region), region)
        datos = {"proveedor": "azure", "clave": clave, "region": region}
    ruta = guardar_voz_local(CARPETA, datos)
    print(f"  💾 Guardado en tu PC ({ruta.name}). No compartas ese archivo.\n")
    return await probar_voz(cfg, configurando=True)


async def probar_voz(cfg: dict, configurando: bool = False) -> int:
    voz = Voz(cfg, CARPETA, reproducir=True)
    print(f"🎙️  Voz: {voz.descripcion()}")
    print(f"🗣️  {FRASE_PRUEBA_VOZ}")
    ruta = await voz.intentar_generar(FRASE_PRUEBA_VOZ)
    elegido = {"azure": "Azure", "elevenlabs": "ElevenLabs"}.get(voz.proveedor, "Edge")
    if ruta is None:
        print("❌ No se pudo generar la voz (¿hay internet?).")
        return 3
    ok = voz.ultimo_proveedor == elegido
    if ok:
        print(f"✅ ¡Funciona! Sonó con {elegido}.")
    else:
        e = voz.ultimo_error
        if ("401" in e or "403" in e) and voz.proveedor == "elevenlabs":
            pista = "La clave no es válida (o no tiene permiso de Text to Speech). Cópiala otra vez."
        elif "401" in e or "403" in e:
            pista = "La clave no es válida (o es de otra región). Cópiala otra vez."
        elif "429" in e or "quota" in e.lower():
            pista = "Se acabó el saldo gratis de este mes, o vas muy rápido. Mientras tanto se usa Edge."
        elif "404" in e and voz.proveedor == "elevenlabs":
            pista = "Ese Voice ID no existe en tu cuenta. Agrega la voz a 'My Voices' y copia su ID."
        elif "Connect" in e or "getaddrinfo" in e or "Name" in e:
            pista = "No pude conectarme. Revisa la región (por ejemplo eastus) y tu internet."
        else:
            pista = "Revisa la clave y la región."
        print(f"⚠️  {elegido} no funcionó, sonó la voz gratis de Edge. {pista}")
        if e:
            print(f"   Detalle técnico: {e[:200]}")
    await voz.reproducir_pc(ruta)
    voz.limpiar(ruta)
    if ok and configurando:
        print("\n🎉 ¡Listo! Abre iniciar.bat y Eduardo hablará con su voz nueva.")
    elif configurando:
        print("   Puedes volver a abrir configurar_voz.bat cuando quieras.")
    return 0 if ok else 3


def borrar_memoria(cfg: dict, sin_preguntar: bool) -> int:
    ruta = CARPETA / cfg.get("memoria", {}).get("archivo", "memoria.json")
    if not ruta.exists():
        print("No hay memoria guardada. Nada que borrar.")
        return 0
    if not sin_preguntar:
        r = input(f"¿Seguro que quieres que Eduardo olvide a TODOS los espectadores? ({ruta.name})  [s/n]: ")
        if r.strip().lower() not in ("s", "si", "sí", "y", "yes"):
            print("Cancelado. No se borró nada.")
            return 1
    Memoria.borrar_archivo(ruta)
    print("🧽 Memoria borrada. Eduardo ya no recuerda a nadie (pero su calva sigue brillando).")
    return 0


async def abrir_enlace(servidor):
    """Crea el enlace https público (Cloudflare Quick Tunnel, gratis) para la fuente "Enlace" de LIVE Studio."""
    from eduardo.tunel import Tunel

    print("🌐 Creando el enlace público para TikTok LIVE Studio (Cloudflare, gratis)...", flush=True)
    tunel = Tunel(CARPETA, servidor.puerto)
    url = await tunel.abrir()
    if not url:
        print("   Puedes usar el plan B: abrir_avatar_ventana.bat + 'Captura de ventana' (ver README).", flush=True)
        return None
    completo = url + servidor.ruta_publica()
    print("=" * 66)
    print("  🔗 PEGA ESTE ENLACE EN LIVE STUDIO  (Agregar fuente → Enlace / Link):")
    print(f"\n     {completo}\n")
    print("  • Espera el mensaje '✅ El enlace público ya funciona' (10 a 60 segundos) y luego pégalo.")
    print("  • Cambia CADA VEZ que abres Eduardo: vuelve a pegarlo en la fuente.")
    print("  • Es secreto: no lo compartas (quien lo tenga puede ver el avatar).")
    print("  • Si el avatar no suena en LIVE Studio: oculta y vuelve a mostrar la fuente (el ojito).")
    print("=" * 66, flush=True)
    try:
        (CARPETA / "enlace_avatar.txt").write_text(completo + "\n", encoding="utf-8")
    except OSError:
        pass

    async def avisar() -> None:
        if await tunel.listo(servidor.ruta_publica()):
            print("✅ El enlace público ya funciona (también está en enlace_avatar.txt).", flush=True)
        else:
            print("⚠️  El enlace todavía no responde. Espera un minuto más y pruébalo; si sigue sin abrir,"
                  " cierra y vuelve a abrir Eduardo (o usa el plan B: abrir_avatar_ventana.bat).", flush=True)
    asyncio.ensure_future(avisar())
    return tunel


# ===================================================================== main
async def principal(args: argparse.Namespace) -> int:
    cfg = cargar_config(Path(args.config) if args.config else None)
    if args.borrar_memoria:
        return borrar_memoria(cfg, args.si)

    reproducir = not args.sin_voz
    bot = Eduardo(cfg, reproducir=reproducir, sin_esperas=args.sin_esperas)

    if not cfg.get("archivos", {}).get("conservar_audios", False) and reproducir:
        for viejo in bot.voz.carpeta_audios.glob("eduardo_*.mp3"):
            try:
                viejo.unlink()
            except OSError:
                pass

    if args.configurar_ia:
        if not await configurar_ia(cfg):
            return 1
        bot = Eduardo(cfg, reproducir=False, sin_esperas=True)  # recargar con la clave nueva
        args.probar_ia = True

    if args.probar_ia:
        g = bot.generador
        print(f"🤖 Probando la IA: proveedor '{g.proveedor}', modelo '{g.modelo}'...")
        t0 = time.monotonic()
        ok, texto = await g.probar_ia()
        if ok:
            print(f"✅ ¡Funciona! ({time.monotonic() - t0:.1f} s)\n🗣️  Eduardo: {texto}")
            if args.configurar_ia:
                print("\n🎉 ¡Listo! Ya no tienes que hacer nada más: abre iniciar.bat y Eduardo contestará con IA.")
        else:
            print(f"❌ La IA no funcionó. {texto}")
            print("   Tranquilo: mientras tanto Eduardo sigue funcionando con sus frases (sin IA)."
                  + ("\n   Puedes volver a abrir configurar_ia.bat y pegar la clave otra vez." if args.configurar_ia else ""))
        return 0 if ok else 3

    if args.configurar_voz:
        return await configurar_voz(cfg)
    if args.probar_voz_nueva:
        return await probar_voz(cfg)

    if args.prueba_voz:
        print(f"🗣️  {FRASE_DEMO}")
        print(f"🔊 {await bot.voz.decir(FRASE_DEMO)}")
        return 0

    tk = cfg.get("tiktok", {})
    usuario = (args.usuario or tk.get("usuario", "")).strip()

    if args.probar_conexion:
        if not usuario or "tu_usuario_aqui" in usuario:
            print("Primero escribe tu usuario de TikTok en config.toml (sección [tiktok]).")
            return 1
        ok = await conectar_tiktok(bot, usuario, 0, tk.get("clave_euler_stream", ""), solo_una_vez=True)
        return 0 if ok else 2

    if not args.simular and not args.avatar_prueba and (not usuario or "tu_usuario_aqui" in usuario):
        print("⚠️  Primero escribe tu usuario de TikTok en config.toml (sección [tiktok], línea 'usuario').")
        return 1

    # ---- Avatar
    av_cfg = cfg.get("avatar", {})
    if av_cfg.get("activar", True) and not args.sin_avatar:
        from eduardo.avatar import ServidorAvatar
        servidor = ServidorAvatar(CARPETA, bot.voz.carpeta_audios, puerto=int(av_cfg.get("puerto", 8765)),
                                  burbuja=bool(av_cfg.get("burbuja", True)),
                                  modo_audio=str(av_cfg.get("modo_audio", "auto")),
                                  clave_enlace=str(av_cfg.get("clave_enlace", "") or ""))
        if await servidor.iniciar():
            bot.avatar = servidor

    tunel = None
    if bot.avatar and (args.enlace or bool(av_cfg.get("enlace_publico", False))):
        tunel = await abrir_enlace(bot.avatar)

    bot.resumen_inicio()
    if bot.avatar and not tunel and not args.avatar_prueba:
        print("  💡 Para LIVE Studio (no acepta localhost): usa iniciar_con_enlace.bat (enlace https) o"
              " abrir_avatar_ventana.bat + Chroma Key. Ver README.", flush=True)
    tareas = [asyncio.create_task(bot.trabajador()), asyncio.create_task(bot.guardado_periodico())]
    try:
        if args.avatar_prueba:
            if not bot.avatar:
                print("⚠️  El avatar está apagado o no pudo abrirse (revisa [avatar] en config.toml).")
            else:
                url = bot.avatar.url + "?fondo=vista"
                print(f"🌐 Abriendo el avatar en tu navegador: {url}")
                print("   (Haz clic en la página si te pide activar el sonido.)", flush=True)
                if not args.no_abrir_navegador:
                    webbrowser.open(url)
                try:
                    await asyncio.wait_for(bot.avatar.primer_cliente.wait(), timeout=30)
                    await asyncio.sleep(2.5)  # dar tiempo a hacer clic para activar el sonido
                except asyncio.TimeoutError:
                    print("   No se conectó ninguna ventana del avatar todavía; sigo igual.")
                bot.cola.put_nowait(Pedido("demo", "Eduardo", "", texto_fijo=FRASE_DEMO))
            await modo_simulacion(bot)
        elif args.simular:
            await modo_simulacion(bot)
        else:
            await conectar_tiktok(bot, usuario, float(tk.get("reintentar_cada_segundos", 30)),
                                  tk.get("clave_euler_stream", ""), ver_chat=args.ver_chat)
    finally:
        for t in tareas:
            t.cancel()
        bot.memoria.guardar(forzar=True)
        if tunel:
            await tunel.cerrar()
        if bot.avatar:
            await bot.avatar.detener()
    return 0


def main() -> None:
    configurar_consola()
    p = argparse.ArgumentParser(description="Eduardo el Calvo - bot simpático y sarcástico para TikTok LIVE")
    p.add_argument("--simular", action="store_true", help="modo prueba escribiendo mensajes en la consola")
    p.add_argument("--avatar-prueba", action="store_true", help="abre el avatar en el navegador + simulación")
    p.add_argument("--probar-conexion", action="store_true", help="intenta conectarse una vez y termina")
    p.add_argument("--prueba-voz", action="store_true", help="dice un chiste de prueba")
    p.add_argument("--probar-ia", action="store_true", help="prueba la conexión con la IA y termina")
    p.add_argument("--configurar-ia", action="store_true", help="asistente para guardar la clave de la IA gratis")
    p.add_argument("--configurar-voz", action="store_true", help="asistente para una voz más natural (Azure/ElevenLabs)")
    p.add_argument("--probar-voz-nueva", action="store_true", help="prueba la voz configurada y dice si funcionó")
    p.add_argument("--enlace", action="store_true", help="crea un enlace https público del avatar para LIVE Studio")
    p.add_argument("--borrar-memoria", action="store_true", help="borra la memoria de espectadores")
    p.add_argument("--si", action="store_true", help="no preguntar confirmación (con --borrar-memoria)")
    p.add_argument("--usuario", help="usuario de TikTok (reemplaza al de config.toml)")
    p.add_argument("--sin-voz", action="store_true", help="no reproducir audio (solo generar archivos)")
    p.add_argument("--sin-esperas", action="store_true", help="desactiva los tiempos de espera")
    p.add_argument("--sin-avatar", action="store_true", help="no abrir el servidor del avatar")
    p.add_argument("--no-abrir-navegador", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--ver-chat", action="store_true", help="muestra TODOS los mensajes del chat en la consola")
    p.add_argument("--config", help="ruta a otro config.toml")
    args = p.parse_args()
    try:
        codigo = asyncio.run(principal(args))
    except KeyboardInterrupt:
        print("\n👋 Eduardo se fue a pulir su calva. ¡Hasta la próxima!")
        codigo = 0
    sys.exit(codigo)


if __name__ == "__main__":
    main()
