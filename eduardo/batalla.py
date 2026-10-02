"""Batallas del chat por equipos: "!Edu batalla tacos pizza".

- Solo la cuenta del LIVE (usuario de config.toml) y los moderadores pueden empezarla o pararla.
- Se vota escribiendo el nombre del equipo (o 1 / 2) en el chat. Un voto por persona: si alguien
  vuelve a votar, cuenta su ÚLTIMO voto (puede cambiar de equipo).
- Opcional: los regalos de quien ya votó suman puntos a su equipo.
- Eduardo narra el inicio, la mitad, los cambios de líder y anuncia al ganador.
"""
from __future__ import annotations

import random
import re
import time
import unicodedata


def plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9ñ ]+", " ", t).strip()


def _cuenta(usuario) -> str:
    """'@Omar_En_Vivo ' -> 'omar_en_vivo' (así se compara el @usuario de TikTok)."""
    return re.sub(r"\s+", "", str(usuario or "")).lstrip("@").lower()


def _lista(valor, defecto: list[str]) -> list[str]:
    if valor is None:
        valor = defecto
    if isinstance(valor, str):
        valor = [valor]
    return [str(v).strip() for v in valor if str(v).strip()]


FRASES = {
    "inicio": ["¡BATALLA! {e1} contra {e2}. Escriban {e1} o {e2} en el chat, o 1 o 2. ¡Tienen {segundos} segundos!",
               "¡Que empiece la pelea! {e1} contra {e2}. Voten escribiendo {e1} o {e2}, o 1 o 2. ¡{segundos} segundos!"],
    "mitad": ["¡Vamos a la mitad! {lider} gana {p_lider} a {p_otro}. ¡{otro}, despierten!",
              "¡Mitad de la batalla! {lider} va arriba, {p_lider} a {p_otro}. ¡Esto no se ha terminado!"],
    "mitad_empate": ["¡Mitad de la batalla y van empatados, {p1} a {p2}! ¡Mi calva no aguanta la tensión!"],
    "lider": ["¡Cambio de líder! Ahora gana {lider}. ¡{otro}, eso les pasa por confiados!",
              "¡Uy! {lider} pasa al frente. ¡{otro}, mi calva los está mirando con decepción!"],
    "fin": ["¡Se acabó! ¡Gana {lider}, {p_lider} a {p_otro}! ¡{otro}, mejor suerte para la próxima!",
            "¡Tenemos ganador! ¡{lider}, con {p_lider} contra {p_otro}! ¡Mi calva brilla por ustedes!"],
    "fin_empate": ["¡Se acabó y quedó EMPATE, {p1} a {p2}! ¡Ni mi calva puede decidir esto!"],
    "fin_sin_votos": ["¡Se acabó la batalla y nadie votó! ¿Hola? ¿Hay alguien aquí además de mi calva?"],
    "parada": ["¡Batalla cancelada! Guarden las espadas, que mi calva necesita descansar."],
}


class Batalla:
    def __init__(self, cfg: dict, sin_esperas: bool = False):
        b = cfg.get("batalla", {})
        self.activar = bool(b.get("activar", True))
        self.duracion = max(10.0, float(b.get("duracion_segundos", 60)))
        self.streamer = _cuenta(cfg.get("tiktok", {}).get("usuario", ""))
        self.moderadores = {_cuenta(m) for m in _lista(b.get("moderadores"), [])} - {""}
        self.mods_de_tiktok = bool(b.get("moderadores_de_tiktok", True))
        self.puntos_por_moneda = max(0.0, float(b.get("puntos_por_moneda", 0)))
        self.palabras = {plano(x) for x in _lista(b.get("palabras"), ["batalla", "pelea", "duelo"])}
        self.palabras_parar = {plano(x) for x in _lista(b.get("palabras_parar"), ["parar", "stop", "cancelar", "terminar"])}
        self.burlas = bool(b.get("narrar_cambios_de_lider", True))
        self.espera_burlas = 0.0 if sin_esperas else float(b.get("espera_entre_burlas_segundos", 12))
        self.activa = False
        self.equipos: list[str] = []
        self.votos: dict[str, int] = {}
        self.puntos_regalo = [0.0, 0.0]
        self.inicio = self.fin = 0.0
        self._mitad_dicha = False
        self._lider_anterior = -1
        self._ultima_burla = -1e9
        self.cambios = 0          # sube con cada voto (para refrescar la barra del avatar)

    # ------------------------------------------------------------- permisos
    def puede_mandar(self, usuario: str, nombre: str = "", es_moderador: bool = False) -> bool:
        # Se compara el @usuario EXACTO (no el apodo visible: cualquiera podría ponerse tu apodo).
        u = _cuenta(usuario)
        if u and (u == self.streamer or u in self.moderadores):
            return True
        return self.mods_de_tiktok and es_moderador

    def es_comando(self, resto: str) -> bool:
        partes = plano(resto).split()
        return self.activar and bool(partes) and partes[0] in self.palabras

    def interpretar(self, resto: str) -> tuple[str, list[str]]:
        """'batalla tacos pizza' -> ('iniciar', ['tacos', 'pizza']); 'batalla parar' -> ('parar', [])."""
        palabras = (resto or "").split()[1:]
        if palabras and plano(palabras[0]) in self.palabras_parar:
            return "parar", []
        texto = " ".join(palabras)
        if re.search(r"\s(?:vs\.?|contra|o)\s", f" {texto} ", re.IGNORECASE):
            equipos = re.split(r"\s+(?:vs\.?|contra|o)\s+", texto, maxsplit=1, flags=re.IGNORECASE)
        else:
            equipos = palabras[:2]
        equipos = [re.sub(r"[^\w\sáéíóúñü]", "", e, flags=re.IGNORECASE).strip()[:18] for e in equipos]
        if len(equipos) != 2 or not all(equipos) or plano(equipos[0]) == plano(equipos[1]):
            return "error", []
        return "iniciar", equipos

    # --------------------------------------------------------------- partida
    def iniciar(self, equipos: list[str], ahora: float | None = None) -> None:
        ahora = time.monotonic() if ahora is None else ahora
        self.activa = True
        self.equipos = equipos[:2]
        self.votos = {}
        self.puntos_regalo = [0.0, 0.0]
        self.inicio, self.fin = ahora, ahora + self.duracion
        self._mitad_dicha = False
        self._lider_anterior = -1
        self._ultima_burla = ahora
        self.cambios += 1

    def parar(self) -> bool:
        estaba = self.activa
        self.activa = False
        self.cambios += 1
        return estaba

    def votar(self, uid: str, texto: str) -> bool:
        """Si el mensaje es un voto, lo anota (el último voto de cada persona es el que cuenta)."""
        if not self.activa:
            return False
        t = plano(texto)
        if not t:
            return False
        idx = -1
        if t in ("1", "2"):
            idx = int(t) - 1
        else:
            nombres = [plano(e) for e in self.equipos]
            if t in nombres:
                idx = nombres.index(t)
            elif len(t.split()) <= 4:
                presentes = [i for i, n in enumerate(nombres) if re.search(rf"\b{re.escape(n)}\b", t)]
                if len(presentes) == 1:
                    idx = presentes[0]
        if idx < 0:
            return False
        if self.votos.get(uid) != idx:
            self.votos[uid] = idx
            self.cambios += 1
        return True

    def regalo(self, uid: str, monedas: int) -> bool:
        if not self.activa or self.puntos_por_moneda <= 0 or uid not in self.votos:
            return False
        self.puntos_regalo[self.votos[uid]] += monedas * self.puntos_por_moneda
        self.cambios += 1
        return True

    def marcador(self) -> list[int]:
        p = [0, 0]
        for idx in self.votos.values():
            p[idx] += 1
        return [int(p[i] + self.puntos_regalo[i]) for i in range(2)]

    def restante(self, ahora: float | None = None) -> float:
        ahora = time.monotonic() if ahora is None else ahora
        return max(0.0, self.fin - ahora) if self.activa else 0.0

    def lider(self) -> int:
        p = self.marcador()
        return -1 if p[0] == p[1] else (0 if p[0] > p[1] else 1)

    def tick(self, ahora: float | None = None) -> list[str]:
        """Devuelve los momentos para narrar: 'mitad', 'lider', 'fin'."""
        if not self.activa:
            return []
        ahora = time.monotonic() if ahora is None else ahora
        eventos = []
        lider = self.lider()
        if ahora >= self.fin:
            self.activa = False
            self.cambios += 1
            return ["fin"]
        if not self._mitad_dicha and ahora - self.inicio >= self.duracion / 2:
            self._mitad_dicha = True
            self._ultima_burla = ahora
            eventos.append("mitad")
        elif (self.burlas and lider >= 0 and self._lider_anterior >= 0 and lider != self._lider_anterior
              and ahora - self._ultima_burla >= self.espera_burlas and self.fin - ahora > 6
              # justo antes de la mitad no: la frase de la mitad ya cuenta quién va ganando
              and (self._mitad_dicha or ahora - self.inicio < self.duracion / 2 - 5)):
            self._ultima_burla = ahora
            eventos.append("lider")
        # _lider_anterior = el último líder que el chat ya "conoce" (primer líder, mitad o burla);
        # así un cambio durante la espera entre burlas no se pierde: se narra cuando toca.
        if lider >= 0 and (eventos or self._lider_anterior < 0):
            self._lider_anterior = lider
        return eventos

    # ---------------------------------------------------------------- frases
    def valores(self) -> dict[str, str]:
        p = self.marcador()
        lider = self.lider()
        v = {"e1": self.equipos[0] if self.equipos else "", "e2": self.equipos[1] if len(self.equipos) > 1 else "",
             "p1": str(p[0]), "p2": str(p[1]), "segundos": str(int(self.duracion))}
        if lider >= 0:
            v.update({"lider": self.equipos[lider], "otro": self.equipos[1 - lider],
                      "p_lider": str(p[lider]), "p_otro": str(p[1 - lider])})
        return v

    def seccion_para(self, evento: str) -> str:
        if evento in ("mitad", "fin") and self.lider() < 0:
            if evento == "fin" and sum(self.marcador()) == 0:
                return "fin_sin_votos"
            return evento + "_empate"
        return evento

    def frase(self, evento: str) -> str:
        seccion = self.seccion_para(evento)
        texto = random.choice(FRASES.get(seccion, FRASES["parada"]))
        for k, v in self.valores().items():
            texto = texto.replace("{" + k + "}", v)
        return texto

    def pedido_ia(self, evento: str, reglas: str) -> str:
        v = self.valores()
        seccion = self.seccion_para(evento)
        hechos = f"BATALLA DEL CHAT: {v['e1']} ({v['p1']} puntos) contra {v['e2']} ({v['p2']} puntos)."
        pedido = {
            "mitad": f"Vamos por la MITAD de la batalla y gana {v.get('lider')}. Narra como comentarista "
                     f"deportivo y provoca con cariño a {v.get('otro')} para que voten.",
            "mitad_empate": "Vamos por la MITAD y están EMPATADOS. Narra la tensión como comentarista deportivo.",
            "lider": f"¡CAMBIO DE LÍDER! Ahora gana {v.get('lider')}. Burla amistosa a {v.get('otro')}.",
            "fin": f"La batalla TERMINÓ. GANÓ {v.get('lider')} con {v.get('p_lider')} contra {v.get('p_otro')}. "
                   f"Anuncia al ganador con mucha emoción y consuela con humor a {v.get('otro')}.",
            "fin_empate": "La batalla TERMINÓ EMPATADA. Anúncialo con humor.",
        }.get(seccion)
        if not pedido:
            return ""
        return "\n".join([hechos, pedido + " Di los números exactos que te doy, no inventes otros.",
                          reglas.replace(" por su nombre", "")])

    def estado_avatar(self, ahora: float | None = None, final: bool = False) -> dict:
        p = self.marcador()
        datos = {"tipo": "batalla", "equipos": self.equipos, "puntos": p,
                 "restante": round(self.restante(ahora), 1), "duracion": self.duracion,
                 "votantes": len(self.votos)}
        if final:
            datos.update({"estado": "fin", "ganador": self.lider()})
        else:
            datos["estado"] = "activa" if self.activa else "oculta"
        return datos
