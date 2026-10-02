# Novedades de Eduardo el Calvo

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
