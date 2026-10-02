# 👨‍🦲 Eduardo el Calvo — compañero simpático con voz y avatar para tu TikTok LIVE

Eduardo es un "compañero" para tu LIVE. Cuando alguien del chat escribe **`!Edu`**
(o `!edu`, da igual mayúsculas o minúsculas), Eduardo le contesta **en voz alta**: le echa
bromas con cariño, cuenta chistes, imita animales y presume sin parar de su **calva brillante**.
Además, aparece en pantalla como un **avatar animado** (una caricatura de un señor calvo con barba blanca, ojos grandes y camisa casual)
que mueve la boca al hablar y al que **le brilla la calva cuando se ríe**.

Ejemplos en el chat:

| Alguien escribe | Eduardo hace |
|---|---|
| `!Edu qué onda pelón` | Le contesta con una broma y presumiendo su calva |
| `!Edu chiste` | Cuenta un chiste (y se ríe con brillo extra) |
| `!Edu animal` | Imita a un animal: ¡Muuuuuuu!, ¡Guau, guau!, ¡Cuac, cuac!... |
| `!Edu ¿cómo estás?` | Le contesta y le pregunta cómo está él |
| `!Edu calvo feo` | Le devuelve la broma con sarcasmo elegante (solo a quien se lo busca) |
| `!Edu` (otra vez, otro día) | Lo recuerda: "¡Otra vez tú! Ya van 5 veces..." |
| `!Edu ruleta` | Gira la **Ruleta de Eduardo** en pantalla: elige a alguien del chat y le toca reto, piropo, burla, chiste o animal |
| `!Edu disfraz sombrero` | Se pone un **disfraz** (sombrero mexicano, corona, lentes de sol...) · `!Edu quitar` se lo quita |
| `!Edu baila` / `!Edu saluda` | Hace un **gesto**: baila, saluda con la mano, se sorprende, guiña, se "enoja" o llora de drama |

> 💡 Para que Eduardo conteste **de verdad** a cualquier comentario, activa la **IA gratis**: doble clic en
> **`configurar_ia.bat`**, pegas tu clave gratis una vez y listo (unos 2 minutos, ver "Paso 5").

> ⚠️ **Importante:** TikTok no permite que los bots *escriban* en el chat del LIVE.
> Eduardo **lee** el chat y **responde con voz** (y con su avatar) en tu transmisión.
> `!Eduardo` **no** activa al bot: el comando es `!Edu` (si quieres, puedes agregar más en `config.toml`).

Escucha cómo suena: abre **`eduardo_ejemplo_voz.mp3`**.

---

## ✅ Lo que necesitas

- Una PC con **Windows 10 u 11** (la misma donde usas TikTok LIVE Studio).
- **Internet** (para leer el chat y para la voz).
- **Python 3.12 o 3.13** (gratis, te explico cómo instalarlo abajo).
- Recomendado: **audífonos**, para que tu micrófono no vuelva a captar la voz de Eduardo.

No necesitas pagar nada. Para la IA gratis (recomendada) solo creas una cuenta gratis en Groq, sin tarjeta.

---

## 🛠️ Instalación (solo la primera vez)

### Paso 1 — Instalar Python
1. Entra a **https://www.python.org/downloads/** y pulsa el botón amarillo **"Download Python 3.x"**.
2. Abre el archivo descargado.
3. **MUY IMPORTANTE:** abajo, marca la casilla **"Add python.exe to PATH"**.
4. Pulsa **"Install Now"** y espera a que termine. Cierra la ventana.

### Paso 2 — Poner la carpeta del bot en tu PC
1. Descarga **`el calvo.zip`** y descomprímelo (clic derecho → **"Extraer todo..."**).
   Es la **única vez** que descargas algo: después Eduardo se actualiza solo (ver
   "🔄 Actualizaciones automáticas").
2. Te quedará una carpeta **`el calvo`**. Déjala en un lugar fácil, por ejemplo en **Documentos**.

### Paso 3 — Instalar el bot
1. Entra a la carpeta y haz **doble clic en `instalar.bat`**.
2. Se abre una ventana negra que instala todo (1 a 3 minutos). Al final dice **"LISTO!"**.
3. Pulsa cualquier tecla para cerrar.

> Si Windows muestra "Windows protegió su PC", pulsa **"Más información" → "Ejecutar de todas formas"**.
> Son archivos de texto simples; puedes abrirlos con el Bloc de notas para ver lo que hacen.
> Si Windows pregunta si Python puede usar la red, pulsa **Permitir** (solo red privada): es para el avatar.

### Paso 4 — Poner tu usuario de TikTok
1. Abre **`config.toml`** con el **Bloc de notas** (clic derecho → "Abrir con" → Bloc de notas).
   (Lo crea `instalar.bat`. Es **tu** archivo: las actualizaciones nunca lo cambian.
   `config.ejemplo.toml` es la copia de fábrica, no hace falta tocarlo.)
2. Busca esta línea y cambia `tu_usuario_aqui` por tu usuario de TikTok:
   ```toml
   usuario = "@tu_usuario_aqui"
   ```
   Por ejemplo: `usuario = "@tu_nombre_de_tiktok"` (con las comillas).
3. Guarda (**Ctrl + G** o Archivo → Guardar).

### Paso 5 — Activar la IA gratis (recomendado, 2 minutos)
Con esto Eduardo **entiende** cada comentario y contesta de verdad, con coherencia.
1. Doble clic en **`configurar_ia.bat`**.
2. Pulsa **Enter** (elige la opción 1, **Groq**, gratis y sin tarjeta). Se abre la página de Groq en tu navegador.
3. Entra con tu correo o tu cuenta de Google → **Create API Key** → nombre "Eduardo" → **copia la clave**
   (empieza con `gsk_`).
4. Vuelve a la ventana negra, **pega la clave** (clic derecho o Ctrl+V) y pulsa **Enter**.
5. El programa la prueba solo. Si dice **"✅ ¡Funciona!"**, listo para siempre. 🎉

La clave queda guardada **solo en tu PC**, en el archivo `ia_local.toml`. **No compartas ese archivo** ni lo
mandes a nadie. Si te saltas este paso, Eduardo funciona igual, pero con frases ya escritas.

---

## 🔄 Actualizaciones automáticas

Eduardo vive en GitHub: **https://github.com/omaroscarquintana/eduardo-el-calvo** (público).
Cada vez que abres **`iniciar.bat`** o **`iniciar_con_enlace.bat`**, Eduardo revisa en unos segundos
si hay una versión nueva y, si la hay, se actualiza solo y dice **"🎉 Eduardo se actualizó: ..."**.
No tienes que descargar nada más ni volver a instalar.

- **Nunca toca tus cosas:** `config.toml`, `ia_local.toml`, `voz_local.toml`, `memoria.json`,
  `enlace_avatar.txt`, ni las carpetas `.venv`, `audios` y `herramientas`.
- Si una versión nueva trae opciones nuevas, se **agregan solas** al final de su sección en tu
  `config.toml` (con su explicación), sin cambiar lo que ya escribiste. Antes guarda una copia
  en `config.toml.respaldo`.
- Si editaste `personalidad.txt`, `respuestas.txt` o `palabras_prohibidas.txt`, se respetan tus cambios
  y la versión nueva queda al lado como `....nuevo`.
- Sin internet, o si GitHub no responde, o si la descarga sale mal: Eduardo arranca igual con la
  versión que ya tienes (nada se rompe a medias: primero descarga y revisa, y solo después reemplaza).
- Si la versión nueva necesita librerías nuevas, las instala sola (puede tardar un minuto esa vez).
- **Actualizar a mano:** doble clic en **`actualizar.bat`**.
- **Apagar las actualizaciones automáticas:** en `config.toml` → `[actualizaciones]` →
  `automaticas = false` (y usa `actualizar.bat` cuando quieras).

---

## 🧪 Probar antes del LIVE

| Archivo | Para qué sirve |
|---|---|
| `probar_voz.bat` | Eduardo cuenta un chiste e imita una vaca. Si lo escuchas, la voz funciona. |
| `configurar_ia.bat` | Pega tu clave de IA gratis una sola vez (ver Paso 5). |
| `configurar_voz.bat` | (Opcional) Voz con más emoción: Azure gratis o ElevenLabs. Dice una frase de prueba con risa. |
| `probar_ia.bat` | Comprueba que la IA (las respuestas inteligentes) funciona con tu clave. |
| `probar_avatar.bat` | Abre el avatar en tu navegador, Eduardo saluda, y puedes escribir mensajes de prueba. |
| `simular.bat` | Escribes mensajes falsos como si fueras el chat y Eduardo responde con voz. |
| `probar_conexion.bat` | Intenta conectarse a tu LIVE una sola vez (tienes que estar en LIVE). |

**Cómo escribir en la simulación:** escribe algo así y pulsa Enter:

```
Pepito: !Edu qué onda pelón
Maria: !edu chiste
Carlos: !EDU animal
Ana: !Edu ¿cómo estás?
Luis: !Edu eres el mejor
Pedro: !Edu calvo feo
Sofi: !Edu ¿te gusta la pizza?
Ana: hola a todos
Leo: !Edu ruleta
Pepe: !Edu disfraz corona
Caro: !Edu baila
Caro: !Edu quitar
```
(Para la ruleta, escribe antes algunos mensajes normales con otros nombres: así tiene a quién elegir.)

Si no pones nombre, usa "Espectador". Escribe `salir` para terminar.

> En `probar_avatar.bat`, si el navegador muestra **"Haz clic aquí para activar el sonido"**, haz clic
> en la página: los navegadores no dejan sonar una página hasta que la tocas. (Mientras tanto Eduardo
> suena por la PC, nunca se queda callado.)

---

## 🔴 Usarlo en tu LIVE

1. Haz doble clic en **`iniciar_con_enlace.bat`** si usas el avatar con la fuente Enlace (Opción A, recomendada),
   o en **`iniciar.bat`** si no usas avatar o usas la Opción B. Déjalo abierto todo el LIVE.
2. Abre **TikTok LIVE Studio** (si usas el enlace, pega el enlace NUEVO en la fuente Enlace; ver abajo) e inicia tu LIVE.
3. En la ventana negra verás `✅ ¡Conectado al LIVE de @tu_usuario!`. Desde ahí Eduardo escucha el chat.
   - Si aún no estás en LIVE, el bot espera y lo vuelve a intentar solo cada 30 segundos.
4. Para apagarlo: cierra la ventana negra o pulsa **Ctrl + C**.

En la ventana verás cada comando, a quién recuerda Eduardo y qué responde:

```
💬 Pepito: !Edu chiste   → en cola (modo chiste)
   🧠 Pepito: 3ª vez, 2 live(s), racha 2
   🗣️  Eduardo (frase, se ríe): Pepito, ¿qué le dice un pez a otro pez? ¡Nada! ¡Ja, ja, ja!
   🔊 sonó en el avatar
```

---

## 🖼️ El avatar animado en pantalla

Mientras `iniciar.bat` está abierto, el avatar vive en esta dirección (solo funciona en tu PC; para
LIVE Studio mira la Opción A o B más abajo):

```
http://localhost:8765/avatar
```

Tiene **fondo transparente**: solo se ve a Eduardo de los hombros para arriba (y la burbuja con lo que dice).
Es una caricatura con proporciones normales (cabeza, hombros y camisa), con sombras suaves.
- Parpadea y se balancea cuando está tranquilo, y la calva le brilla con reflejos.
- Mueve la boca **sincronizada con su voz**.
- Cuando se ríe (chistes, "ja, ja, ja") cierra los ojos de felicidad, rebota, y le sale un
  **destello enorme de la calva con chispas**, y levanta el pulgar. 👍
- Hace **gestos** (baile, saludo, sorpresa, guiño, enojo de broma, tristeza de telenovela), se pone
  **disfraces** y muestra la **Ruleta de Eduardo** (ver la sección "🎡" más abajo).
- En la carpeta `imagenes/` tienes fotos de Eduardo (tranquilo, hablando, riendo, con disfraces, gestos y
  la ruleta) con fondo transparente, por si las quieres usar en tus miniaturas o en el LIVE.

### ⚠️ Importante: LIVE Studio NO acepta `http://localhost...`
Si pegaste `http://localhost:8765/avatar` en la fuente **Enlace** y LIVE Studio dice **"inválida"**, es normal:
la fuente Enlace de LIVE Studio solo acepta direcciones **https de internet** (no acepta `localhost`, ni `http`).
Por eso hay dos caminos:

### Opción A (recomendada): enlace https con `iniciar_con_enlace.bat`
Eduardo crea solo un **enlace público gratis** de Cloudflare (sin cuenta y sin tarjeta) que apunta a tu avatar.
1. Haz doble clic en **`iniciar_con_enlace.bat`** (en vez de `iniciar.bat`). La primera vez descarga
   `cloudflared.exe` (programa oficial de Cloudflare, ~60 MB) en la carpeta `herramientas`.
2. En la ventana negra aparece un recuadro: **`🔗 PEGA ESTE ENLACE EN LIVE STUDIO`** con algo como
   `https://palabras-al-azar.trycloudflare.com/e/AbC123xyz/avatar`. (También queda guardado en `enlace_avatar.txt`.)
3. Espera el mensaje **`✅ El enlace público ya funciona`** (10 a 60 segundos).
4. En LIVE Studio: **Agregar fuente → Enlace** (en inglés **Link**) → pega el enlace completo → tamaño
   **480 × 640** (o cualquier tamaño vertical) → Aceptar. Colócalo en una esquina.
5. En el mezclador de LIVE Studio, que el audio de esa fuente **no esté silenciado**.
6. En la ventana negra debe salir `🖼️ Avatar conectado` y `🔊 El avatar puede reproducir el sonido.`

Ten en cuenta:
- **El enlace cambia cada vez que abres Eduardo.** En cada LIVE: abre `iniciar_con_enlace.bat`, copia el
  enlace nuevo, y en LIVE Studio haz doble clic en la fuente Enlace (o clic derecho → Propiedades) y pégalo.
- Es **secreto**: lleva una clave (`/e/AbC123xyz/`). Sin esa clave, el enlace responde "no encontrado".
  No lo compartas. Lo único que muestra es el avatar (nadie puede controlar a Eduardo con él).
- Si el avatar **se ve pero no suena** después de empezar el LIVE o cambiar de escena: **oculta y vuelve a
  mostrar la fuente** (el ojito) en LIVE Studio. Es un fallo conocido de las fuentes Enlace de LIVE Studio
  (también les pasa a TikFinity y otras alertas). Si sigue sin sonar, pon `modo_audio = "pc"`.
- Si quieres el enlace siempre (sin usar el .bat especial): en `config.toml` → `[avatar]` → `enlace_publico = true`.

### Opción B: ventana del avatar + Chroma Key (`abrir_avatar_ventana.bat`)
Si el enlace no funciona en tu PC (firewall, sin internet estable...), captura una ventana:
1. Abre `iniciar.bat` (normal).
2. Doble clic en **`abrir_avatar_ventana.bat`**: se abre una ventana sola de Edge/Chrome con Eduardo sobre
   **fondo verde**, tamaño vertical 540 × 960. Haz clic una vez dentro de la ventana (por si pide activar sonido).
3. En LIVE Studio: **Agregar fuente → Captura de ventana** → elige **"Eduardo el Calvo - Avatar"**.
4. Clic derecho en esa fuente → **Filtro avanzado** → **Agregar** → **Chroma Key** → color **verde**.
   Ajusta **Similitud** y **Suavidad** hasta que el verde desaparezca sin borrar a Eduardo.
   (Si Eduardo se ve con borde verde, sube un poco "Similitud". Si alguna vez usas ropa verde en el LIVE,
   usa fondo magenta: abre una ventana de comandos y escribe `abrir_avatar_ventana.bat magenta`.)
5. **No minimices** esa ventana (puede quedar detrás de otras, eso sí funciona).
6. El sonido sale **por la PC**: para que el público lo escuche, LIVE Studio tiene que capturar el
   **audio del sistema** (ver la sección "🎧" más abajo). Si escuchas a Eduardo doble, pon `modo_audio = "pc"`.

### ¿Por dónde suena la voz? (nunca suena doble)
- **Opción A (Enlace)** → la voz sale **desde el avatar** y LIVE Studio la manda al LIVE con la fuente Enlace
  (como hacen los widgets de alertas y TTS de otras apps).
- **Opción B (ventana)** o sin avatar → la voz sale **por la PC** y LIVE Studio la toma como **audio del sistema**.
- Si no hay avatar abierto (o la página no puede sonar), Eduardo suena por la PC: nunca se queda callado.
- Si abres varias ventanas del avatar, solo **la primera** que se abrió hace sonido; las demás solo animan.
  (Para una vista previa siempre muda usa `http://localhost:8765/avatar?silencio=1`.)
- Si prefieres que la voz salga **siempre por la PC**, pon `modo_audio = "pc"` en `config.toml`.

> **Honestidad:** no pude probar dentro de TikTok LIVE Studio (no hay Windows aquí). Lo que sí probé:
> el enlace de Cloudflare se crea, la página del avatar y su conexión (wss) funcionan por el enlace https, y
> sin la clave secreta responde "no encontrado". La regla de "LIVE Studio no acepta localhost / pide https"
> la confirman guías de otras herramientas para LIVE Studio. Si tu LIVE Studio rechaza el enlace, usa la Opción B.

Opciones de la dirección (puedes combinarlas con `&`): `?burbuja=0` (sin burbuja de texto),
`?silencio=1` (nunca suena), `?fondo=verde` o `?fondo=magenta` (fondo para el Chroma Key).

---

## 🎧 Hacer que tu público escuche a Eduardo por el audio del sistema

Esto aplica cuando la voz sale **por la PC** (sin avatar, Opción B o `modo_audio = "pc"`):

1. En **Windows**: Configuración → Sistema → **Sonido** → en **Salida**, elige los audífonos/bocinas que usas.
2. En **TikTok LIVE Studio**, abre el **mezclador de audio**.
3. Asegúrate de que existe y **no está silenciada** la fuente de **audio del sistema / altavoz**
   (puede aparecer como "Audio del sistema", "Altavoz" o con el nombre de tus audífonos),
   y que está en el **mismo dispositivo** que elegiste en Windows.
4. Ejecuta `probar_voz.bat` y mira que **se mueva la barrita de volumen** del audio del sistema.
   **Si tú lo escuchas y la barrita se mueve, tu público también lo escucha.**

Consejos:
- Usa **audífonos**. Con bocinas, tu micrófono también capta a Eduardo y se escucha doble o con eco.
- El audio del sistema manda **todo** lo que suena en tu PC (música, videos, notificaciones).

---

## 🎡 Ruleta, disfraces y gestos

### Ruleta de Eduardo — `!Edu ruleta`
En el avatar aparece una **ruleta** que gira; arriba van pasando los nombres de quienes escribieron en el chat
hace poco, hasta quedarse en uno. La ruleta cae en una categoría y Eduardo lo anuncia con su voz:

| Categoría | Qué hace Eduardo |
|---|---|
| **Reto** | Le pone un reto divertido y **seguro, para hacer en el chat** (un trabalenguas, 3 emojis de su calva...). Nunca retos peligrosos, físicos, de datos personales, de dinero ni de regalos. |
| **Piropo calvo** | Un cumplido tierno y gracioso de calvo orgulloso. |
| **Burla amistosa** | Una broma suave con cariño (nunca sobre el físico ni nada personal). |
| **Chiste dedicado** | Un chiste dedicado a esa persona (y se ríe). |
| **Imitación de animal** | Imita un animal dedicado a esa persona. |

- Con IA, Eduardo inventa el anuncio; sin IA usa las frases de `respuestas.txt` (secciones `[ruleta_reto]`,
  `[ruleta_piropo]`, `[ruleta_burla]`, `[ruleta_chiste]`, `[ruleta_animal]`).
- Solo entran quienes escribieron en los **últimos 10 minutos**. Normalmente **no** elige a quien la pidió.
- La ruleta **descansa 90 segundos** entre una y otra (para todo el chat).
- Se configura en `config.toml` → `[ruleta]`: `categorias`, `pesos` (más número = sale más seguido; 0 = nunca),
  `espera_segundos`, `excluir_quien_pide`, `ventana_minutos`.
- Funciona también sin avatar (solo con voz), pero lo bonito es verla girar.

### Disfraces — `!Edu disfraz ...`
| Escribe | Disfraz |
|---|---|
| `!Edu disfraz fiesta` | gorro de fiesta |
| `!Edu disfraz sombrero` | sombrero mexicano |
| `!Edu disfraz lentes` | lentes de sol |
| `!Edu disfraz corona` | corona de rey |
| `!Edu disfraz peluca` | peluca chistosa de payaso |
| `!Edu disfraz bigote` | bigote falso |
| `!Edu disfraz gorra` | gorra |
| `!Edu disfraz santa` | gorro de Santa |
| `!Edu disfraz` | uno al azar |
| `!Edu quitar` | se quita el disfraz |

- El disfraz se queda puesto **10 minutos** y luego se lo quita solo (`[disfraces]` → `duracion_minutos`;
  `0` = hasta que alguien escriba `!Edu quitar`). También entiende "sombrero mexicano", "gafas", "navidad", etc.

### Gestos — `!Edu baila`, `!Edu saluda`...
| Escribe | Gesto |
|---|---|
| `!Edu baila` | baila (se mueve al ritmo y salen notas musicales) |
| `!Edu saluda` | saluda con la mano |
| `!Edu sorpresa` | ojos enormes, cejas arriba, boca en "O" y signos de exclamación |
| `!Edu guiña` | guiña un ojo con destello |
| `!Edu enójate` | "enojo" de broma: cejas fruncidas, calva roja y vapor por las orejas |
| `!Edu triste` | tristeza de telenovela: cejas caídas y lagrimitas |

- **Con IA, Eduardo también hace gestos solo** cuando encajan: la IA escribe una etiqueta como
  `[gesto:sorpresa]` al principio de su respuesta; el bot la quita (no se lee en voz alta) y el avatar hace el gesto.
- Con IA, si escriben algo más (`!Edu baila que ganamos`), Eduardo contesta de verdad **y** baila.
- Para apagar disfraces o gestos: `[disfraces]` → `activar = false` / `gestos = false`.
- Todos estos comandos respetan los tiempos de espera normales (`[limites]`), para evitar spam.

---

## 🧠 La memoria de Eduardo

Eduardo **recuerda a los espectadores entre un LIVE y otro**:
- La **primera vez** que alguien lo llama, le da la bienvenida.
- A los que vuelven los reconoce: "¡Otra vez tú! Ya van 5 veces", "La última vez me dijiste...",
  "Llevas 3 lives seguidos viniendo".
- También cuenta (sin guardar el texto) cuántos mensajes escribe cada quien en el chat sin usar `!Edu`.

**Privacidad:** todo se guarda **solo en tu PC**, en el archivo **`memoria.json`** dentro de la carpeta.
No se sube a ningún lado. Se guarda por espectador: su nombre, número de TikTok, primera y última vez
que lo vio, cuántas veces usó `!Edu`, en cuántos lives estuvo, y sus **últimos 5 mensajes a Eduardo**
con las respuestas. (Solo si activas la IA opcional, ese pequeño resumen se manda a tu servicio de IA
junto con el mensaje, para que pueda recordar.)

- **Borrar toda la memoria:** doble clic en **`borrar_memoria.bat`** (te pide confirmación).
- **Apagar la memoria:** en `config.toml`, sección `[memoria]`, pon `activar = false`.
- No recordar a quien no usa el comando: `recordar_chat_sin_comando = false`.
- Cuántos mensajes guardar por persona: `max_historial = 5`.

---

## ⚙️ Personalizar a Eduardo

Todo se cambia con el **Bloc de notas**. Después de guardar, **cierra y vuelve a abrir** `iniciar.bat`.

### Cambiar o agregar comandos
En `config.toml`, sección `[comando]`:
```toml
activadores = ["!Edu"]
palabras_chiste = ["chiste", "chistes", "broma", "bromas"]
palabras_animal = ["animal", "animales", "imita", "imitacion", "imitación"]
```
- Para que también funcione `!Eduardo`: `activadores = ["!Edu", "!Eduardo"]`.
- Mayúsculas y minúsculas no importan. El mensaje tiene que **empezar** con el comando.

### Cambiar la voz
En `config.toml`, sección `[voz]`:
```toml
nombre_voz = "es-US-AlonsoNeural"
velocidad = "+2%"
tono = "-4Hz"
```
- De fábrica: **Alonso** (voz masculina latina neutra), un poquito más grave y a un ritmo ágil, para que
  suene natural, alegre y con energía. En las pruebas fue de las voces más graves y con más "vida"
  (sube y baja el tono al hablar, en vez de sonar plana) y se entiende perfecto.
- Otras voces de hombre: `es-DO-EmilioNeural` (la más grave, muy expresiva), `es-MX-JorgeNeural` (grave
  y cálida), `es-PR-VictorNeural` (Puerto Rico), `es-CO-GonzaloNeural` (Colombia), `es-AR-TomasNeural`
  (Argentina), `es-ES-AlvaroNeural` (España).
- Para ver **todas** las voces en español: doble clic en **`listar_voces.bat`**.
- Más grave: `tono = "-8Hz"`. Más rápido: `velocidad = "+8%"`. Más lento: `velocidad = "-8%"`.
  No conviene subir el tono (`+Hz`): suena más infantil y robótica.
- Después de cambiar algo, prueba con **`probar_voz.bat`**.
- Las voces gratis de Edge no tienen "estilos" de emoción (alegre, emocionado...). La energía sale del
  texto: por eso las frases y la IA usan muchos signos de exclamación. (Con Azure sí hay estilo alegre, ver abajo.)
- **Pausas naturales** (`pausas_naturales = true`): Eduardo genera cada frase por separado y las une con
  una pausa corta (~0,35 a 0,45 s), en lugar del silencio de casi 1 segundo que deja la voz de Edge entre
  frases. Ajusta la duración con `pausa_entre_frases_ms`.
- Seamos honestos: aun así, una voz gratis no suena 100 % humana. Para más emoción mira `configurar_voz.bat` abajo.

### Texto preparado para la voz y risas de verdad
- Antes de hablar, Eduardo **limpia el texto**: quita emojis, lee los números con letras ("20" → "veinte",
  "3:30" → "tres y media", "50%" → "cincuenta por ciento"), cambia las abreviaturas del chat ("xq" → "porque",
  "tqm" → "te quiero mucho"), pronuncia en español palabras como "live" o "nice", y no deletrea los GRITOS.
  (`preparar_texto = true` en `[voz]`.)
- Con IA, la personalidad pide frases **cortas y habladas** (de 12 palabras o menos) con muletillas naturales
  ("¡Uy!", "¡Mira!", "pues", "¿eh?"), que es lo que más ayuda a que suene natural.
- **Risas de verdad:** cuando Eduardo se ríe ("jaja", "¡Ja, ja, ja!" o `[risa]`), en vez de leer "ja ja ja"
  suena una **carcajada grabada** de un señor (carpeta `sonidos/`, 5 risas distintas), y el avatar se ríe justo
  en ese momento. Para volver a la risa leída: `risas_grabadas = false`.
- **Licencia de las risas:** son grabaciones de **Freesound.org** con licencia **CC0 1.0 (dominio público)**:
  se pueden usar gratis, también en lives con ingresos, sin dar crédito. Fuentes: "Laughing (male)" de
  dastudiospr (freesound.org/s/529818), "Male Laugh" de cchenail (freesound.org/s/611480) y "Man laughing
  various" de SPAudiobooks (freesound.org/s/859265). Detalle en `sonidos/LICENCIAS.txt`.

### Voz con más emoción (opcional): `configurar_voz.bat`
La voz gratis de Edge no tiene emociones ("estilos"). Si quieres una voz más alegre y natural:

| Opción | Cómo suena | Gratis | Ojo |
|---|---|---|---|
| **Edge** (la de siempre) | Buena, pero plana | Sí, sin clave | Nada que configurar |
| **Azure Speech** ⭐ recomendada | La voz de **Jorge (México)** en estilo **alegre** (`cheerful`) | **500.000 letras al mes** (≈ 5.000 respuestas) en el plan Free F0 | Para crear la cuenta pide tarjeta o débito **solo para verificar** (puede hacer una retención temporal de 1 USD); el plan F0 no cobra |
| **ElevenLabs** | La más humana, con **risa real** (modelo v3) | 10.000 letras al mes (≈ 100 respuestas) | Plan gratis **solo uso NO comercial** y hay que dar crédito ("elevenlabs.io" en el título o descripción del live). Con ingresos: plan Starter (~5-6 USD/mes) |

**Pasos con Azure (recomendado, unos 5 minutos, solo una vez):**
1. Doble clic en **`configurar_voz.bat`** → pulsa **Enter** (opción 1, Azure). Se abre el portal de Azure.
2. Entra con tu cuenta Microsoft o crea la **cuenta gratis de Azure** (te pide teléfono y tarjeta para verificar).
3. En el formulario "Speech service": **Grupo de recursos** → "Crear nuevo" → `eduardo`. **Región**: `East US`.
   **Nombre**: cualquiera (ej. `eduardo-voz-123`). **Plan de tarifa**: **Free F0**. → **Revisar y crear** → **Crear**.
4. Cuando termine: **Ir al recurso** → **Claves y punto de conexión** → copia la **CLAVE 1**.
5. Vuelve a la ventana negra, pega la clave → Enter → escribe la región (Enter = `eastus`).
6. Eduardo dice una frase de prueba con risa. Si sale **"✅ ¡Funciona! Sonó con Azure"**, listo para siempre.

**ElevenLabs:** `configurar_voz.bat` → opción 2 → pega tu clave (`sk_...`) y el **Voice ID** de una voz en
español de la **Voice Library** (filtra Spanish + Male → "Add to my voices" → "Copy voice ID").

- Las claves se guardan **solo en tu PC** en `voz_local.toml`. **No compartas ese archivo.**
- Para volver a Edge: `configurar_voz.bat` → opción 3.
- Si Azure o ElevenLabs fallan (sin saldo, sin internet, clave mala), Eduardo usa **automáticamente** la voz
  gratis de Edge: nunca se queda callado.
- Ajustes de Azure en `config.toml` → `[voz]`: `azure_estilo` (`cheerful` alegre, `excited` emocionado, `chat`),
  `azure_intensidad` (0.5 a 2), `azure_voz`.
- **Honestidad:** no tengo claves de Azure ni de ElevenLabs, así que no pude escuchar esas voces aquí. Sí probé
  que el bot arma bien los pedidos (con una clave falsa, Azure y ElevenLabs contestan "clave inválida" y Eduardo
  pasa solo a la voz de Edge). La voz Jorge con estilo alegre es la misma familia que la de Edge, pero con emoción.

### Cambiar las frases, chistes y animales (sin IA)
Abre **`respuestas.txt`**. Está dividido en secciones según el **tipo de comentario**: `[saludo]`,
`[despedida]`, `[cumplido]`, `[gracias]`, `[troll]` (provocaciones: aquí sí es sarcástico), `[risa]`,
varias de preguntas (`[pregunta_estado]` "¿cómo estás?", `[pregunta_calva]`, `[pregunta_edad]`,
`[pregunta_quien]`, `[pregunta_gusto]` "¿te gusta...?", `[pregunta]`...), `[general]` (lo demás),
`[nuevo]` (primera vez), `[regular]` (los que vuelven), `[chiste]` y `[animal]`.
Una frase por línea. Palabras especiales: `{nombre}`, `{mensaje}`, `{cosa}`, `{veces}`, `{ultimo_mensaje}`,
`{lives}`, `{racha}` (el archivo explica cada una). Sin IA, Eduardo también entiende pedidos escritos
normalmente, como "cuéntame un chiste" o "imita un perro" (y elige el sonido de ese animal).

**Sonidos de animales que suenan bien con la voz** (probados con Alonso): ¡Muuuuuuu! ¡Guau, guau! ¡Cuac, cuac!
¡Miauuu! ¡Kikirikí! ¡Oinc, oinc! ¡Croac, croac! ¡Pío, pío, pío! ¡Auuuuuu! ¡Groaaar! ¡Ji-joo, ji-joo!
¡Currucucú! ¡Uuu, uuu!. Evita "grrr", "bzzz" o "beee": la voz los deletrea o no se entienden.

Si una frase tiene "ja, ja, ja", suena una carcajada grabada y el avatar se ríe con brillo extra en ese momento.

### Cambiar la personalidad (cuando usas IA)
Abre **`personalidad.txt`** y escribe cómo quieres que sea Eduardo.

### Evitar spam (tiempos de espera)
En `config.toml`, sección `[limites]`:
- `espera_por_usuario_segundos = 60` → cada persona puede usar el comando una vez por minuto.
- `espera_global_segundos = 8` → mínimo 8 segundos entre respuestas.
- `cola_maxima = 5` → máximo 5 respuestas esperando turno (las demás se ignoran).

Las respuestas **nunca se enciman**: Eduardo termina una frase antes de empezar la siguiente.

---

## 🤖 Respuestas con Inteligencia Artificial (RECOMENDADO, hay opción GRATIS)

**Seamos honestos:** sin IA, Eduardo elige una frase ya escrita de `respuestas.txt`. Adivina qué tipo
de comentario es (saludo, pregunta, cumplido, provocación, pedido de chiste o de animal...) y usa una
frase de ese tipo, así que suele encajar, **pero no puede contestar de verdad** a cualquier cosa
(por ejemplo, "¿qué hora es en España?" o "¿viste el partido?").

**Con IA**, Eduardo lee el comentario, ve los últimos mensajes del chat y lo que recuerda de esa persona,
y contesta **de verdad**, siguiendo la conversación. Es cariñoso con quien es amable y sarcástico solo con
quien se lo busca. Por eso es la forma **recomendada** de usarlo.

### Opción gratis recomendada: Groq (sin tarjeta)
Groq tiene un plan **Free** sin tarjeta de crédito. Con el modelo que usa Eduardo (`openai/gpt-oss-120b`),
el plan gratis da hasta **30 respuestas por minuto y 1.000 al día**, más que suficiente para un LIVE, y es
muy rápido. (Límites del plan gratis según la documentación de Groq a octubre de 2026; pueden cambiar.)

**Cómo activarlo:** doble clic en **`configurar_ia.bat`** → Enter (opción 1) → copia tu clave de la página
que se abre → pégala → Enter. Los pasos detallados están en el **Paso 5** de la instalación.
Para comprobarlo cuando quieras: **`probar_ia.bat`**. En `simular.bat` verás `Eduardo (IA): ...`.

### Otra opción gratis: Google Gemini
La API de Gemini tiene un **nivel gratuito** (con límites diarios por modelo, que se ven en Google AI Studio).
Abre **`configurar_ia.bat`**, escribe **2** y pulsa Enter: se abre Google AI Studio → **Create API key** →
copia la clave (empieza con `AIza`) → pégala en la ventana → Enter.
> Ojo: en el plan gratis, Google puede usar lo que se envía para mejorar sus productos. Eduardo solo le
> manda los últimos mensajes del chat y los nombres que se ven en el LIVE.

Para **quitar** la clave: `configurar_ia.bat` → opción **3** (o borra `ia_local.toml`).

### Otras opciones (para usuarios avanzados)
Se configuran en `config.toml`, sección `[ia]`, y la clave en una variable de entorno de Windows
(Menú Inicio → **cmd** → `setx NOMBRE_VARIABLE "tu-clave"` → cierra y vuelve a abrir el bot):
- **OpenRouter** (`proveedor = "openrouter"`, variable `OPENROUTER_API_KEY`): modelos gratis, pero solo
  ~50 respuestas al día si no compras créditos.
- **OpenAI** (`proveedor = "openai"`, variable `OPENAI_API_KEY`): de pago, muy bueno.
- **Ollama** (`proveedor = "ollama"`): gratis en tu propia PC, sin internet, pero necesita una PC potente.
- **Otro** servicio compatible con OpenAI: `proveedor = "otro"`, pon `url_base` y `modelo`, y la clave en
  `EDUARDO_IA_KEY`.
- Groq y Gemini también aceptan variables (`GROQ_API_KEY`, `GEMINI_API_KEY`) en vez de `configurar_ia.bat`.
  Si usas las dos cosas, manda la clave guardada con `configurar_ia.bat`.

### Si `probar_ia.bat` da error
| Mensaje | Qué hacer |
|---|---|
| `Todavía no pegaste tu clave gratis` | Abre `configurar_ia.bat` y sigue los pasos. |
| `La clave no es válida` | Abre `configurar_ia.bat` otra vez y pega la clave completa. Si la perdiste, crea otra en la página. |
| `Llegaste al límite gratis` | Espera unos minutos (o hasta el día siguiente), o usa la otra opción gratis (Gemini). |
| `El modelo ... no está disponible` | Escribe otro modelo en `modelo = ""` (mira la lista de modelos de tu proveedor). |
| `No hubo respuesta a tiempo` | Revisa tu internet, o sube `tiempo_maximo_segundos` en `[ia]`. |

En todos los casos Eduardo **sigue funcionando** con sus frases de respaldo: nunca se queda callado.

### Qué ve la IA (para que la conversación tenga sentido)
- Los **últimos 8 mensajes del chat** (puedes cambiarlo con `contexto_chat_mensajes`), incluidas las
  respuestas de Eduardo. Los mensajes que no pasan el filtro de seguridad nunca se envían.
- Lo que Eduardo **recuerda** de esa persona (cuántas veces vino y lo último que hablaron).
- La personalidad de **`personalidad.txt`** (reglas de tono y ejemplos). Puedes editarla con el Bloc de notas.

Si la IA falla, tarda más de 10 segundos o dice algo que no pasa el filtro, Eduardo usa una frase de
`respuestas.txt`. El LIVE nunca se queda sin respuesta.

---

## 🛡️ Filtro de seguridad

- Si alguien escribe groserías, odio, contenido sexual, violencia o enlaces junto con `!Edu`,
  **Eduardo no repite su mensaje**: lo esquiva con una frase segura (o lo ignora con
  `responder_a_mensajes_bloqueados = false`).
- Si el **nombre** del espectador es ofensivo, Eduardo le dice "amigo".
- Las respuestas de la IA también pasan por el filtro. Los emojis no se leen en voz alta.
- La lista está en **`palabras_prohibidas.txt`**; puedes agregar las palabras que quieras.

Ningún filtro es perfecto. Si alguien encuentra la forma de colarse, agrega esa palabra a la lista.

---

## ❓ Problemas comunes

| Lo que ves | Qué hacer |
|---|---|
| `No encuentro Python` al instalar | Reinstala Python marcando **"Add python.exe to PATH"**. Reinicia la PC. |
| `⏳ ... no está en LIVE ahora mismo` | Normal si no has empezado el LIVE. El bot reintenta solo. |
| `❓ TikTok dice que ... no existe` | Revisa tu usuario en `config.toml` (sin espacios, entre comillas). |
| `🚦 límite gratuito del servidor de firmas` | Espera unos minutos, o crea una cuenta gratis en eulerstream.com y pega tu clave en `clave_euler_stream`. |
| `No pude abrir el avatar en el puerto 8765` | Ya hay otro Eduardo abierto, o cambia `puerto` en `[avatar]` (y la dirección en LIVE Studio). |
| LIVE Studio dice que el enlace es **inválido** | No acepta `http://localhost`. Usa `iniciar_con_enlace.bat` y pega el enlace `https://...trycloudflare.com/e/.../avatar` (Opción A). |
| El enlace https no abre | Espera el mensaje `✅ El enlace público ya funciona`. Cada vez que abres Eduardo el enlace cambia: pega el nuevo. Si no funciona, usa la Opción B. |
| El avatar no aparece en LIVE Studio | ¿Está abierto Eduardo? ¿Pegaste el enlace de HOY? Si sigue sin verse, usa la Opción B (ventana + Chroma Key). |
| El avatar se ve pero no suena en el LIVE | Oculta y vuelve a mostrar la fuente Enlace (el ojito). Si sigue, `modo_audio = "pc"` + audio del sistema. |
| `ignorado: la ruleta descansa...` | Normal: la ruleta espera 90 s entre giros (`[ruleta]` → `espera_segundos`). |
| `configurar_voz` dice que Azure no funcionó | Revisa la clave (CLAVE 1) y la región (la "Ubicación" del recurso, ej. `eastus`). Mientras tanto suena Edge. |
| Eduardo responde en la ventana pero no se oye | Prueba `probar_voz.bat`. Revisa la salida de sonido de Windows. |
| Yo lo oigo pero el público no | Revisa el audio de la fuente Enlace o el **audio del sistema** en LIVE Studio. |
| `La voz de Edge falló` | Sin internet o problema temporal de Microsoft. Eduardo usa la voz de Windows. |
| El bot no responde a algunos | Seguramente están en tiempo de espera; la ventana muestra el motivo (`ignorado: ...`). |
| Error en `config.toml` | Revisa que los textos estén entre comillas y no hayas borrado un `=` o un `[ ]`. |

Para comprobar que el bot lee tu chat: abre una ventana de comandos en la carpeta y ejecuta
`.venv\Scripts\python.exe bot.py --ver-chat` (muestra todos los mensajes del chat).

---

## 📌 Limitaciones (para que no haya sorpresas)

- **No es una herramienta oficial de TikTok.** Usa la librería libre **TikTokLive** (Python), que lee el chat
  igual que lo haría un navegador. Si TikTok cambia algo, puede dejar de funcionar hasta que la librería
  se actualice. Para actualizar: abre `instalar.bat` otra vez.
- Para conectarse, TikTokLive usa el **servidor de firmas de Euler Stream** (un servicio externo) con un
  **límite gratuito**. Para un streamer normal suele alcanzar; si ves avisos de límite, pon una clave gratuita.
- La voz usa el servicio de voz en línea de **Microsoft Edge** (gratis, sin clave, no oficial para este uso).
  Si un día falla, Eduardo usa la voz de Windows (más robótica).
- Las voces gratis de Edge suenan bien, pero **no son 100 % humanas**: no tienen emociones reales ni
  respiración. Las pausas naturales, el texto preparado y las risas grabadas ayudan mucho; para más emoción
  está Azure (gratis con límite) o ElevenLabs (`configurar_voz.bat`).
- El **enlace público** (Opción A) depende del servicio gratis "Quick Tunnel" de Cloudflare: no tiene garantía
  y el enlace cambia en cada arranque. Si un día falla, usa la Opción B (ventana + Chroma Key).
- **Sin IA**, las respuestas son frases ya escritas: encajan con el tipo de comentario, pero no contestan
  cualquier cosa. Con la IA gratis (Groq o Gemini) sí; esos planes gratis tienen límites diarios.
- Eduardo **no puede escribir** en el chat de TikTok; solo habla en tu LIVE.

---

## 📁 Archivos de la carpeta

| Archivo | Qué es |
|---|---|
| `instalar.bat` | Instala todo (solo la primera vez). |
| `actualizar.bat` | Busca e instala la última versión de Eduardo a mano (normalmente no hace falta: se actualiza solo). |
| `iniciar.bat` | Arranca a Eduardo para tu LIVE (con avatar). |
| `iniciar_con_enlace.bat` | Igual, pero además crea el **enlace https** para la fuente Enlace de LIVE Studio (Opción A). |
| `abrir_avatar_ventana.bat` | Abre el avatar en una ventana con fondo verde para "Captura de ventana" + Chroma Key (Opción B). |
| `configurar_voz.bat` | Asistente para una voz con más emoción (Azure gratis / ElevenLabs) o volver a Edge. |
| `configurar_ia.bat` | Guarda tu clave de IA gratis (Groq o Gemini) una sola vez, o la quita. |
| `probar_avatar.bat`, `simular.bat`, `probar_voz.bat`, `probar_ia.bat`, `probar_conexion.bat`, `listar_voces.bat` | Pruebas. |
| `borrar_memoria.bat` | Borra lo que Eduardo recuerda de los espectadores. |
| `config.toml` | **Tu** configuración (usuario, comando, voz, memoria, avatar, IA, ruleta, disfraces). Las actualizaciones nunca la reemplazan. |
| `config.ejemplo.toml` | Configuración de fábrica (se actualiza sola; `config.toml` se crea copiándola). |
| `actualizador.py`, `.version_instalada`, `.archivos_programa.json` | El actualizador automático y qué versión tienes instalada. |
| `CAMBIOS.md` | Lista de novedades de cada versión. |
| `respuestas.txt` | Frases de respaldo por tipo de comentario, chistes, animales, ruleta, disfraces y gestos. |
| `personalidad.txt` | Personalidad de Eduardo para la IA (reglas de tono y ejemplos). |
| `palabras_prohibidas.txt` | Lista del filtro de seguridad. |
| `eduardo_ejemplo_voz.mp3` | Ejemplo de cómo suena Eduardo. |
| carpeta `imagenes/` | Imágenes PNG del avatar (tranquilo, hablando, riendo, disfraces, gestos, ruleta). |
| `memoria.json` | Memoria de espectadores (se crea sola; solo en tu PC). |
| `ia_local.toml` | Tu clave de IA (lo crea `configurar_ia.bat`). **Privado: no lo compartas.** |
| `voz_local.toml` | Tu clave de voz (lo crea `configurar_voz.bat`). **Privado: no lo compartas.** |
| carpeta `sonidos/` | Las 5 risas grabadas (CC0) y `LICENCIAS.txt`. |
| carpeta `herramientas/` | Aquí se descarga `cloudflared.exe` (para el enlace https) la primera vez. |
| `enlace_avatar.txt` | El último enlace https del avatar (se crea solo con `iniciar_con_enlace.bat`). |
| `bot.py`, carpetas `eduardo/` y `avatar/` | El programa y el avatar (no hace falta tocarlos). |
| carpeta `audios/` | Audios temporales (se borran solos). |
