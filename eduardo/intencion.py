"""Clasificador sencillo de intención (sin IA): ¿qué quiso decir el espectador?

Se usa para elegir frases que encajen con el comentario cuando NO hay IA, y como pista
de tono para la IA cuando sí la hay. Son reglas simples con palabras clave: acierta en
lo común (saludos, preguntas típicas, cumplidos, provocaciones, pedidos), no en todo.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Intenciones posibles
SALUDO, DESPEDIDA, CUMPLIDO, GRACIAS, TROLL, RISA = "saludo", "despedida", "cumplido", "gracias", "troll", "risa"
PIDE_CHISTE, PIDE_ANIMAL, ALEATORIO, VACIO = "pide_chiste", "pide_animal", "aleatorio", "vacio"
PREGUNTA, P_ESTADO, P_CALVA, P_EDAD, P_ORIGEN, P_QUIEN = (
    "pregunta", "pregunta_estado", "pregunta_calva", "pregunta_edad", "pregunta_origen", "pregunta_quien")
P_GUSTO, P_OPINION = "pregunta_gusto", "pregunta_opinion"

# Para la IA: cómo conviene contestar cada cosa
TONO_PARA_IA = {
    SALUDO: "te está saludando: salúdalo con alegría y cariño",
    DESPEDIDA: "se está despidiendo: despídete con cariño e invítalo a volver",
    CUMPLIDO: "te dijo algo bonito: agradécelo con calidez (y presume un poco tu calva)",
    GRACIAS: "te está dando las gracias: responde con calidez",
    TROLL: "parece una provocación, burla o comentario pesado: aquí SÍ puedes ser sarcástico, ingenioso y con chispa, sin insultar ni humillar",
    RISA: "se está riendo: ríete con él y sigue la buena vibra",
    PIDE_CHISTE: "te pide un chiste: cuéntale uno corto y limpio",
    PIDE_ANIMAL: "te pide que imites a un animal: hazlo",
    PREGUNTA: "te hizo una pregunta: contéstala DE VERDAD (corto) y agrega un toque de humor",
    P_ESTADO: "te pregunta cómo estás: contéstale con entusiasmo y pregúntale cómo está",
    P_CALVA: "pregunta por tu calva: presúmela con orgullo y humor",
    P_EDAD: "pregunta tu edad: contesta con humor (no tienes edad fija, eres un personaje)",
    P_ORIGEN: "pregunta de dónde eres: eres el compañero del LIVE de Omar, vives en su pantalla",
    P_QUIEN: "pregunta quién o qué eres: eres Eduardo el Calvo, el compañero virtual del LIVE de Omar",
    P_GUSTO: "pregunta si te gusta algo: contesta de verdad sobre eso, con humor",
    P_OPINION: "pide tu opinión sobre algo: da una opinión corta y simpática sobre eso",
    ALEATORIO: "comentario general: respóndele a lo que dijo, juguetón y con buena onda",
    VACIO: "solo te llamó sin decir nada: salúdalo con energía",
}

# Animales que Eduardo sabe imitar (palabra clave -> sonido aprobado para la voz)
ANIMALES = {
    "vaca": "¡Muuuuuuu!", "toro": "¡Muuuuuuu!", "perro": "¡Guau, guau!", "perrito": "¡Guau, guau!",
    "pato": "¡Cuac, cuac!", "gato": "¡Miauuu!", "gatito": "¡Miauuu!", "gallo": "¡Kikirikí!",
    "cerdo": "¡Oinc, oinc!", "cerdito": "¡Oinc, oinc!", "chancho": "¡Oinc, oinc!", "puerco": "¡Oinc, oinc!",
    "marrano": "¡Oinc, oinc!", "rana": "¡Croac, croac!", "sapo": "¡Croac, croac!", "pollito": "¡Pío, pío, pío!",
    "pollo": "¡Pío, pío, pío!", "lobo": "¡Auuuuuu!", "leon": "¡Groaaar!", "burro": "¡Ji-joo, ji-joo!",
    "paloma": "¡Currucucú!", "buho": "¡Uuu, uuu!", "lechuza": "¡Uuu, uuu!",
}


@dataclass
class Intencion:
    tipo: str
    cosa: str = ""     # de qué habla ("la pizza" en "¿te gusta la pizza?")
    animal: str = ""   # sonido pedido, si nombró un animal

    @property
    def es_pregunta(self) -> bool:
        return self.tipo.startswith("pregunta")


def normalizar(texto: str) -> str:
    """minúsculas, sin acentos, sin letras repetidas de más ('holaaaa' -> 'hola')."""
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"(.)\1{2,}", r"\1", t)
    t = re.sub(r"\bq\b", "que", t)
    t = re.sub(r"\bxq\b|\bpq\b", "por que", t)
    return re.sub(r"\s+", " ", t).strip()


def _r(*partes: str) -> re.Pattern:
    return re.compile("|".join(partes))


_RISA = re.compile(r"^(?:[\s!.¡]*(?:ja|je|ji|ha|xd|lol|jsj|lmao|jaj|jej)+[\s!.]*)+$")
_PIDE_CHISTE = _r(r"\bchistes?\b", r"\bbromas?\b", r"\balgo (?:gracioso|chistoso)\b", r"\bhazme reir\b",
                  r"\bhaznos reir\b", r"\bcuenta(?:me|nos)? algo\b")
_PIDE_ANIMAL = _r(r"\bimita", r"\bimitacion", r"\bsonido de\b", r"\bruido de\b", r"\bcomo hace (?:el|la|un|una)\b",
                  r"\bhaz (?:de |como |el sonido de )?(?:un|una|el|la) (?:vaca|perro|pato|gato|gallo|cerdo|rana|lobo|leon|burro|buho)")
_TROLL = _r(
    r"\bfe[oa]s?\b", r"\btont[oa]s?\b", r"\bbob[oa]\b", r"\bmens[oa]\b", r"\baburrid[oa]\b", r"\baburres\b",
    r"\bcallate\b", r"\bya calla", r"\bno sirves\b", r"\bno sirve[ns]? para nada\b", r"\bhorrible\b",
    r"\bdas pena\b", r"\bdas asco\b", r"\bque asco\b", r"\bcringe\b", r"\bbasura\b", r"\binutil\b", r"\bpayaso\b",
    r"\bridicul[oa]\b", r"\bapestas\b", r"\bpesad[oa]\b", r"\bnadie te (?:quiere|soporta|pregunto)\b",
    r"\bte odio\b", r"\bodio a eduardo\b", r"\bfuera\b", r"\blargate\b", r"\bpelon\b", r"\bpelad[oa]\b",
    r"\bcabeza de (?:huevo|rodilla|bola|foco)\b", r"\bbola de billar\b", r"\bbombillo\b", r"\bfoco\b",
    r"\bcalvo (?:feo|tonto|bobo|aburrido)\b", r"\bmal[oa] (?:bot|chiste)\b", r"\bpesimo\b", r"\bmalisim[oa]\b",
    r"\bno das risa\b", r"\bno das gracia\b", r"\bsin gracia\b", r"\bfrances?\b.*\bmalo\b", r"\blento\b",
    r"\bviejo\b", r"\bpelele\b", r"\bzopenco\b", r"\bburro\b(?! ?(?:simpatico|imita))",
)
_NEGACION_CUMPLIDO = re.compile(r"\bno (?:eres|me caes|me gustas|me gusta tu|das)\b")
_CUMPLIDO = _r(
    r"\bte (?:quiero|amo|adoro)\b", r"\bme encanta(?:s| tu| como)\b", r"\bme caes (?:muy |super )?bien\b",
    r"\beres (?:el |la |un |una |muy |super |tan )*(?:mejor|grande|genial|crack|maximo|amor|bonito|lindo|guapo|"
    r"chistoso|gracioso|divertido|buena onda|top|idolo|leyenda|hermoso|tierno|simpatico|lo maximo)",
    r"\bque (?:bonit|lind|guap|hermos|chistos|gracios|divertid|tiern)", r"\bcrack\b", r"\bidolo\b",
    r"\bleyenda\b", r"\bgenio\b", r"\bmaestro\b", r"\bbrillas\b", r"\bme haces reir\b", r"\bme alegras\b",
    r"\bbuena onda\b", r"\bhermosa calva\b", r"\bbonita calva\b", r"\bque calva tan\b", r"\blo maximo\b",
    r"\bte luciste\b", r"\bbuenisimo\b", r"\bexcelente\b",
)
_GRACIAS = re.compile(r"\bgracias\b|\bthank|\bgrax\b|\bmuchas gracias\b")
_SALUDO = re.compile(r"^(?:hola|holi|holis|ola|buenas|buenos dias|buenas tardes|buenas noches|hey|ey|que onda|"
                     r"que tal|saludos|wenas|hi|hello|que hubo|quiubo|que pasa|que mas|epa|alo|aloha|hello)\b")
_DESPEDIDA = re.compile(r"\badios\b|\bchao\b|\bchau\b|\bbye\b|\bme voy\b|\bnos vemos\b|\bhasta (?:luego|manana|pronto)\b|"
                        r"\bme despido\b|\bya me tengo que ir\b")
_PALABRA_PREGUNTA = re.compile(r"^(?:y )?(?:que|como|cuando|donde|por que|porque|quien|cual|cuanto|cuantos|cuantas|"
                               r"sabes|puedes|tienes|te gusta|eres|has|hay|crees|vas|estas|me (?:das|dices|cuentas))\b")
_P_ESTADO = re.compile(r"\bcomo (?:estas|te va|andas|amaneciste|te sientes|vas|te encuentras|sigues)\b|"
                       r"\bque tal (?:estas|tu dia|todo|te va)\b|\btodo bien\b|\bcomo te trata la vida\b")
_P_CALVA = re.compile(r"\bcalv|\bpelo\b|\bcabello\b|\bpelon|\bpeluca|\bchampu|\bshampoo|\bbrill|\bcabeza\b|\bpeine")
_P_EDAD = re.compile(r"\bcuantos anos\b|\bque edad\b|\bedad tienes\b|\banos tienes\b|\btu edad\b")
_P_ORIGEN = re.compile(r"\bde donde (?:eres|sos|vienes)\b|\bdonde vives\b|\bde que pais\b|\bdonde naciste\b")
_P_QUIEN = re.compile(r"\bquien eres\b|(?<!por )\bque eres\b|\beres (?:un |una )?(?:bot|robot|ia|inteligencia|real|humano|persona|"
                      r"maquina|programa)\b|\bcomo te llamas\b|\btu nombre\b|\bquien te (?:hizo|creo|programo)\b")
_P_GUSTO = re.compile(r"\bte gusta(?:n)?\s+(.+)", re.I)
_P_OPINION = re.compile(r"\bqu[eé] (?:opinas|piensas|dices|te parece[ns]?) (?:del|de|sobre)?\s*(.+)", re.I)


def _cosa(regex: re.Pattern, original: str) -> str:
    m = regex.search(original)
    if not m:
        return ""
    cosa = re.split(r"[?!.,;]", m.group(1))[0].strip()
    palabras = cosa.split()
    return " ".join(palabras[:5])[:40]


def animal_en(mensaje: str) -> str:
    """Si el mensaje nombra un animal que Eduardo sabe imitar, devuelve su sonido."""
    t = normalizar(mensaje)
    for clave, sonido in ANIMALES.items():
        if re.search(rf"\b{clave}s?\b", t):
            return sonido
    return ""


def clasificar(mensaje: str) -> Intencion:
    original = (mensaje or "").strip()
    t = normalizar(original)
    if not re.search(r"[a-z0-9]", t):
        return Intencion(VACIO)

    animal = animal_en(original)

    if _RISA.match(t):
        return Intencion(RISA)
    if _PIDE_CHISTE.search(t):
        return Intencion(PIDE_CHISTE)
    if _PIDE_ANIMAL.search(t) or (animal and re.search(r"\b(?:haz|hace|has|imita|suena|sonido)\b", t)):
        return Intencion(PIDE_ANIMAL, animal=animal)

    es_pregunta = "?" in original or "¿" in original or bool(_PALABRA_PREGUNTA.match(t))
    troll = bool(_TROLL.search(t)) or bool(_NEGACION_CUMPLIDO.search(t))
    if troll:
        return Intencion(TROLL)
    if _GRACIAS.search(t):
        return Intencion(GRACIAS)
    if _CUMPLIDO.search(t):
        return Intencion(CUMPLIDO)
    if _P_ESTADO.search(t):
        return Intencion(P_ESTADO)
    if _DESPEDIDA.search(t):
        return Intencion(DESPEDIDA)
    if es_pregunta or _P_QUIEN.search(t) or _P_EDAD.search(t) or _P_ORIGEN.search(t):
        if _P_QUIEN.search(t):
            return Intencion(P_QUIEN)
        if _P_EDAD.search(t):
            return Intencion(P_EDAD)
        if _P_ORIGEN.search(t):
            return Intencion(P_ORIGEN)
        cosa = _cosa(_P_OPINION, original)
        if cosa:
            return Intencion(P_OPINION, cosa=cosa)
        cosa = _cosa(_P_GUSTO, original)
        if cosa:
            return Intencion(P_GUSTO, cosa=cosa)
        if _P_CALVA.search(t):
            return Intencion(P_CALVA)
        if es_pregunta:
            return Intencion(PREGUNTA)
    if _SALUDO.match(t):
        # "hola" solo, o "hola Eduardo", o "buenas noches a todos"
        return Intencion(SALUDO)
    return Intencion(ALEATORIO)
