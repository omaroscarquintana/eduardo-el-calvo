"""Reacciones de Eduardo a los regalos del LIVE.

- Regalos en racha (combo): se espera al final de la racha y se agradece UNA vez con el total.
- Los regalos pequeños que llegan seguidos se juntan en una sola frase (no satura el live).
- Según el valor (en monedas) la reacción es pequeña, mediana (con gesto) o GRANDE (baile, brillo
  de calva y confeti en el avatar).
- Los totales de cada espectador se guardan en la memoria de Eduardo.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

PEQUENO, MEDIANO, GRANDE = "pequeño", "mediano", "grande"

# Monedas aproximadas de regalos comunes (solo para la simulación: en el LIVE las da TikTok).
MONEDAS_SIMULACION = {
    "rosa": 1, "rose": 1, "tiktok": 1, "gg": 1, "corazon": 5, "corazón": 5, "finger heart": 5, "helado": 1,
    "dona": 30, "donut": 30, "sombrero": 99, "gorra": 99, "perfume": 20, "corgi": 299, "pistola de dinero": 500,
    "money gun": 500, "galaxia": 1000, "galaxy": 1000, "leon": 29999, "león": 29999, "lion": 29999,
    "universo": 44999, "universe": 44999,
}

PLANTILLAS = {
    PEQUENO: [
        "¡Gracias, {nombre}, por {cosas}! Mi calva brilla un poquito más.",
        "¡Uy, {nombre}! {Cosas}. Con eso me compro media peluca. ¡Gracias!",
        "¡{nombre}, gracias por {cosas}! Te mando un reflejo de calva.",
        "¡Mira nada más, {nombre}! {Cosas}. ¡Así sí dan ganas de seguir!",
    ],
    "grupo": [
        "¡Gracias, {nombres}, por los regalitos! Mi calva está encantada.",
        "¡Lluvia de regalos! Gracias, {nombres}. ¡Los quiero más que a mi peine!",
        "¡{nombres}, gracias! Con tanto cariño mi calva ya parece espejo.",
    ],
    MEDIANO: [
        "¡Oigan, oigan! {nombre} mandó {cosas}. ¡Eso ya es amor del bueno!",
        "¡No puede ser, {nombre}! {Cosas}. ¡Me voy a pulir la calva en tu honor!",
        "¡{nombre}, qué generosidad! {Cosas}. ¡Mi calva te hace una reverencia!",
    ],
    GRANDE: [
        "¡ALTO TODO! ¡{nombre} mandó {cosas}! ¡Esto merece un baile de calvo profesional!",
        "¡Señoras y señores, {nombre} acaba de mandar {cosas}! ¡Mi calva está brillando de emoción!",
        "¡{nombre}, eres leyenda! {Cosas}. ¡Que suene la música, que este calvo va a bailar!",
    ],
}
GESTOS_MEDIANO = ["sorpresa", "guino", "saludo"]


@dataclass
class Regalo:
    uid: str
    nombre: str
    regalo: str
    monedas_unidad: int
    cantidad: int

    @property
    def monedas(self) -> int:
        return max(0, self.monedas_unidad) * max(1, self.cantidad)


@dataclass
class Reaccion:
    nivel: str                       # pequeño / mediano / grande / grupo
    nombres: list[str]
    uids: list[str]
    regalos: list[Regalo] = field(default_factory=list)

    @property
    def monedas(self) -> int:
        return sum(r.monedas for r in self.regalos)

    @property
    def nombre(self) -> str:
        return self.nombres[0] if self.nombres else "amigo"

    def descripcion(self) -> str:
        """'5 Rosas y 1 GG' (para la frase y la IA)."""
        juntos: dict[str, int] = {}
        for r in self.regalos:
            juntos[r.regalo] = juntos.get(r.regalo, 0) + max(1, r.cantidad)
        partes = [f"{n} {plural(regalo)}" if n > 1 else f"el regalo {regalo}"
                  for regalo, n in sorted(juntos.items(), key=lambda kv: -kv[1])]
        if len(partes) > 3:
            partes = partes[:3] + ["más cositas"]
        return partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " y " + partes[-1]


def plural(regalo: str) -> str:
    """'Rosa' -> 'Rosas', 'Dona' -> 'Donas'; lo demás se deja igual ('GG', 'León', 'Corazón')."""
    return regalo + "s" if " " not in regalo and len(regalo) > 2 and regalo[-1] in "aeiou" else regalo


def lista_nombres(nombres: list[str], maximo: int = 4) -> str:
    n = list(dict.fromkeys(nombres))
    if len(n) > maximo:
        n = n[:maximo - 1] + [f"{len(n) - maximo + 1} más"]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " y " + n[-1]


class Regalos:
    """Junta los eventos de regalo y decide CUÁNDO y CÓMO agradecer (sin asyncio: fácil de probar)."""

    def __init__(self, cfg: dict):
        r = cfg.get("regalos", {})
        self.activar = bool(r.get("activar", True))
        self.mediano_desde = int(r.get("mediano_desde_monedas", 100))
        self.grande_desde = int(r.get("grande_desde_monedas", 1000))
        self.minimo = int(r.get("minimo_monedas_para_hablar", 1))
        self.ventana = float(r.get("juntar_pequenos_segundos", 6))
        self.fin_racha = float(r.get("fin_de_racha_segundos", 8))
        self.efectos = bool(r.get("efectos_en_avatar", True))
        self._rachas: dict[tuple[str, str], tuple[Regalo, float]] = {}
        self._pendientes: list[Regalo] = []
        self._desde = 0.0       # cuándo llegó el primer regalo pendiente

    def nivel_de(self, monedas: int) -> str:
        if monedas >= self.grande_desde:
            return GRANDE
        if monedas >= self.mediano_desde:
            return MEDIANO
        return PEQUENO

    def recibir(self, uid: str, nombre: str, regalo: str, monedas_unidad: int, cantidad: int,
                en_racha: bool, ahora: float | None = None) -> Regalo | None:
        """Llega un evento de TikTok. Devuelve el regalo TERMINADO (o None si la racha sigue)."""
        if not self.activar:
            return None
        ahora = time.monotonic() if ahora is None else ahora
        clave = (uid, regalo)
        g = Regalo(uid, nombre or "amigo", regalo or "regalo", int(monedas_unidad or 0), max(1, int(cantidad or 1)))
        if en_racha:
            self._rachas[clave] = (g, ahora)       # TikTok manda el total acumulado en cada evento
            return None
        self._rachas.pop(clave, None)
        return self._terminar(g, ahora)

    def _terminar(self, g: Regalo, ahora: float) -> Regalo:
        if not self._pendientes:
            self._desde = ahora
        self._pendientes.append(g)
        return g

    def tick(self, ahora: float | None = None) -> list[Reaccion]:
        """Llamar cada medio segundo. Devuelve las reacciones listas para decir."""
        ahora = time.monotonic() if ahora is None else ahora
        for clave, (g, t) in list(self._rachas.items()):   # rachas que nunca avisaron su final
            if ahora - t >= self.fin_racha:
                del self._rachas[clave]
                self._terminar(g, ahora)
        if not self._pendientes:
            return []
        hay_importante = any(self.nivel_de(self._total_de(g.uid)) != PEQUENO for g in self._pendientes)
        # Los regalos grandes/medianos se agradecen enseguida (1 s para juntar el resto de su combo);
        # los pequeños esperan un poco para juntarse en una sola frase.
        espera = 1.0 if hay_importante else self.ventana
        if ahora - self._desde < espera:
            return []
        pendientes, self._pendientes = self._pendientes, []
        return self._agrupar(pendientes)

    def _total_de(self, uid: str) -> int:
        return sum(g.monedas for g in self._pendientes if g.uid == uid)

    def _agrupar(self, regalos: list[Regalo]) -> list[Reaccion]:
        por_uid: dict[str, list[Regalo]] = {}
        for g in regalos:
            por_uid.setdefault(g.uid, []).append(g)
        reacciones, pequenos = [], []
        for uid, lista in por_uid.items():
            total = sum(g.monedas for g in lista)
            if total < self.minimo:
                continue
            nivel = self.nivel_de(total)
            if nivel == PEQUENO:
                pequenos.append(Reaccion(PEQUENO, [lista[-1].nombre], [uid], lista))
            else:
                reacciones.append(Reaccion(nivel, [lista[-1].nombre], [uid], lista))
        reacciones.sort(key=lambda r: -r.monedas)
        if len(pequenos) == 1:
            reacciones.append(pequenos[0])
        elif pequenos:
            reacciones.append(Reaccion("grupo", [p.nombre for p in pequenos], [p.uids[0] for p in pequenos],
                                       [g for p in pequenos for g in p.regalos]))
        return reacciones

    # ------------------------------------------------------------------ frases
    @staticmethod
    def frase_plantilla(reac: Reaccion) -> str:
        cosas = reac.descripcion()
        plantilla = random.choice(PLANTILLAS.get(reac.nivel, PLANTILLAS[PEQUENO]))
        return (plantilla.replace("{nombres}", lista_nombres(reac.nombres)).replace("{nombre}", reac.nombre)
                .replace("{Cosas}", cosas[:1].upper() + cosas[1:]).replace("{cosas}", cosas))

    @staticmethod
    def gesto_de(reac: Reaccion) -> str:
        if reac.nivel == GRANDE:
            return "baile"
        if reac.nivel == MEDIANO:
            return random.choice(GESTOS_MEDIANO)
        return ""

    @staticmethod
    def pedido_ia(reac: Reaccion, memoria_txt: str, reglas: str) -> str:
        tono = {
            PEQUENO: "Agradece RÁPIDO (una o dos frases cortas) con un chiste pequeño.",
            "grupo": "Agradece a TODOS juntos en una o dos frases cortas, nombrándolos.",
            MEDIANO: "Haz una reacción GRANDE y emocionada, con un chiste de calvo.",
            GRANDE: "¡Es un MOMENTO ESPECIAL! Reacciona exageradamente feliz, anuncia que vas a bailar y "
                    "que tu calva brilla de emoción. Empieza con [gesto:baile].",
        }[reac.nivel]
        quien = lista_nombres(reac.nombres) if reac.nivel == "grupo" else reac.nombre
        partes = [f"REGALO EN EL LIVE: {quien} te mandó {reac.descripcion()} "
                  f"(en total {reac.monedas} monedas de TikTok; nivel {reac.nivel})."]
        if memoria_txt:
            partes.append(memoria_txt)
        partes.append(tono + " Nunca pidas más regalos ni hables de dinero.")
        partes.append(reglas)
        return "\n".join(partes)

    # --------------------------------------------------------------- memoria
    @staticmethod
    def anotar_en_memoria(memoria, reac: Reaccion) -> str:
        """Suma los regalos a la ficha de cada espectador. Devuelve un resumen para la IA (si es uno solo)."""
        if not getattr(memoria, "activar", False):
            return ""
        resumen = ""
        por_uid: dict[str, list[Regalo]] = {}
        for g in reac.regalos:
            por_uid.setdefault(g.uid, []).append(g)
        for uid, lista in por_uid.items():
            ficha = memoria._ficha(uid, lista[-1].nombre)
            antes = int(ficha.get("regalos_monedas", 0))
            ficha["regalos_monedas"] = antes + sum(g.monedas for g in lista)
            ficha["regalos_cantidad"] = int(ficha.get("regalos_cantidad", 0)) + sum(g.cantidad for g in lista)
            ficha["ultimo_regalo"] = lista[-1].regalo
            ficha["ultimo_regalo_fecha"] = time.strftime("%Y-%m-%d %H:%M:%S")
            if len(por_uid) == 1:
                resumen = ("MEMORIA: es su PRIMER regalo para ti, hazlo sentir especial." if antes == 0 else
                           f"MEMORIA: ya te había regalado antes (en total {antes} monedas): agradécele que siga apoyando.")
        memoria.guardar()
        return resumen
