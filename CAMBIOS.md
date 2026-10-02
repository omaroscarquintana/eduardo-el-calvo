# Novedades de Eduardo el Calvo

## 2026-10-02 — Regalos con reacción, batallas del chat y arreglo de la ruleta
- **Regalos:** Eduardo agradece cada regalo por el nombre de quien lo manda. Los combos se agradecen
  una sola vez al final con el total y los regalitos seguidos se juntan en una frase. Regalo mediano:
  reacción más grande con gesto. Regalo grande: baila, le brilla la calva y cae confeti en el avatar.
  Van antes que los `!Edu` normales y se guardan en la memoria de cada espectador.
  Opciones nuevas en `[regalos]`.
- **Batallas del chat:** `!Edu batalla tacos pizza` (solo tú o tus moderadores). El chat vota
  escribiendo el equipo o 1 / 2 (un voto por persona; si vuelve a votar, cuenta el último), barra con
  puntos y cuenta atrás en el avatar, Eduardo narra la mitad, los cambios de líder y al ganador.
  `!Edu batalla parar` la cancela. Opciones nuevas en `[batalla]` (duración, moderadores, puntos por regalos).
- **Ruleta:** el confeti ya no tapa el nombre de la categoría ganadora (por ejemplo "Reto").
- Simulación: nuevos `/regalo Rosa 5`, `/esperar 30` y el nombre `Streamer:` para probar todo sin estar en LIVE.

## 2026-10-02 — Actualizador más resistente
- Si GitHub limita las consultas, el actualizador pregunta directo al repositorio y descarga
  directo, así Eduardo se sigue actualizando igual.
- Si editaste `personalidad.txt`, `respuestas.txt` o `palabras_prohibidas.txt`, solo se deja un
  archivo `.nuevo` al lado cuando la versión nueva de verdad cambió ese archivo.

## 2026-10-02 — Actualizaciones automáticas
- Eduardo ahora se actualiza solo desde GitHub al abrir `iniciar.bat` o `iniciar_con_enlace.bat`.
- Nuevo `actualizar.bat` para actualizar a mano.
- Tu configuración ahora vive en `config.toml` (tuyo, nunca se reemplaza) y la de fábrica en
  `config.ejemplo.toml`. Las opciones nuevas se agregan solas a tu `config.toml`.
- Nueva opción `[actualizaciones] automaticas` para apagar las actualizaciones automáticas.
