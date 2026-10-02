// ===== Capa de efectos de Eduardo: barra de batalla, carteles de regalos, confeti y brillo de calva =====
// La carga el servidor del avatar junto con avatar.html. Recibe los efectos por /efectos_ws.
(() => {
  "use strict";
  const p = new URLSearchParams(location.search);
  const BASE = location.pathname.replace(/\/avatar\/?$/, "");
  const COLORES = ["#e63946", "#ff9f1c", "#2ec4b6", "#7b2cbf", "#3a86ff", "#06a77d", "#f72585", "#ffd23f"];

  const capa = document.createElement("div");
  capa.id = "efx";
  capa.innerHTML = `
    <div id="efx-batalla" aria-hidden="true">
      <div class="cabecera"><span class="titulo">⚔️ BATALLA DEL CHAT</span><span class="reloj">60</span></div>
      <div class="equipos"><span class="equipo e1"></span><span class="equipo e2"></span></div>
      <div class="barra"><div class="lado1"></div><div class="chispa"></div></div>
      <div class="pie"></div>
      <div class="ganador"></div>
    </div>
    <div id="efx-cartel" aria-hidden="true"></div>`;
  document.body.appendChild(capa);

  const $ = s => capa.querySelector(s);
  const caja = $("#efx-batalla"), reloj = $(".reloj"), e1 = $(".e1"), e2 = $(".e2");
  const lado1 = $(".lado1"), chispa = $(".chispa"), pie = $(".pie"), ganador = $(".ganador");
  const cartel = $("#efx-cartel");
  const esc = t => String(t ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ---------------- Batalla ----------------
  let finBatalla = 0, ocultar = null;
  function pintarReloj() {
    if (!caja.classList.contains("visible") || caja.classList.contains("fin")) return;
    const s = Math.max(0, Math.ceil((finBatalla - performance.now()) / 1000));
    reloj.textContent = `${s}s`;
    reloj.classList.toggle("urgente", s <= 10);
  }
  setInterval(pintarReloj, 200);

  function batalla(m) {
    clearTimeout(ocultar);
    if (m.estado === "oculta" || m.estado === "cancelada") { caja.classList.remove("visible", "fin"); return; }
    const [n1, n2] = m.equipos || ["", ""];
    const [p1, p2] = m.puntos || [0, 0];
    e1.innerHTML = `${esc(n1)}<span class="num">${p1}</span>`;
    e2.innerHTML = `<span class="num">${p2}</span>${esc(n2)}`;
    const total = p1 + p2;
    const pct = total ? Math.max(4, Math.min(96, (p1 / total) * 100)) : 50;
    lado1.style.width = `${pct}%`; chispa.style.left = `${pct}%`;
    caja.classList.add("visible");
    if (m.estado === "fin") {
      caja.classList.add("fin");
      reloj.textContent = "¡FIN!"; reloj.classList.remove("urgente");
      e1.classList.toggle("gana", m.ganador === 0); e2.classList.toggle("gana", m.ganador === 1);
      e1.classList.toggle("pierde", m.ganador === 1); e2.classList.toggle("pierde", m.ganador === 0);
      ganador.textContent = m.ganador === 0 ? `¡GANA ${n1.toUpperCase()}!` : m.ganador === 1 ? `¡GANA ${n2.toUpperCase()}!`
                                            : (total ? "¡EMPATE!" : "Nadie votó…");
      if (m.ganador >= 0) confeti(70);
      ocultar = setTimeout(() => caja.classList.remove("visible", "fin"), (m.mostrar_segundos || 12) * 1000);
      return;
    }
    caja.classList.remove("fin");
    e1.classList.remove("gana", "pierde"); e2.classList.remove("gana", "pierde");
    finBatalla = performance.now() + (m.restante || 0) * 1000;
    pie.textContent = `Escribe ${n1} o ${n2} (o 1 / 2) en el chat · ${m.votantes || 0} voto(s)`;
    pintarReloj();
  }

  // ---------------- Regalos ----------------
  let finCartel = null;
  function regalo(m) {
    cartel.className = "";
    void cartel.offsetWidth;
    cartel.innerHTML = `🎁 ${esc(m.titulo || "")}` + (m.subtitulo ? `<span class="sub">${esc(m.subtitulo)}</span>` : "");
    cartel.classList.add("visible", m.nivel === "grande" ? "grande" : m.nivel === "mediano" ? "mediano" : "pequeno");
    clearTimeout(finCartel);
    finCartel = setTimeout(() => cartel.classList.remove("visible"), (m.segundos || 5) * 1000);
    if (m.nivel === "grande") { brillo(); confeti(120); }
  }

  function brillo() {
    // el cráneo (no todo el grupo de la cabeza: ahí también están disfraces y rayos)
    const cabeza = document.querySelector('#cabeza > use[href="#forma-craneo"]') || document.getElementById("cabeza")
                   || document.getElementById("avatar");
    if (!cabeza) return;
    const r0 = cabeza.getBoundingClientRect();
    const tam = Math.max(r0.width, r0.height) * 1.6;
    const piezas = [];
    for (const clase of ["efx-brillo", "efx-destello"]) {
      const d = document.createElement("div");
      d.className = clase;
      const t = clase === "efx-destello" ? tam * 0.55 : tam;
      Object.assign(d.style, { width: `${t}px`, height: `${t}px` });
      capa.appendChild(d);
      piezas.push([d, t]);
    }
    // El brillo sigue a la calva aunque Eduardo esté bailando
    const hasta = performance.now() + 3400;
    (function seguir() {
      const r = cabeza.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height * 0.28;   // la parte de arriba de la calva
      for (const [d, t] of piezas) { d.style.left = `${cx - t / 2}px`; d.style.top = `${cy - t / 2}px`; }
      if (performance.now() < hasta) requestAnimationFrame(seguir);
      else for (const [d] of piezas) d.remove();
    })();
    setTimeout(() => { for (const [d] of piezas) d.remove(); }, 3600);   // por si la pestaña está oculta
  }

  function confeti(n) {
    for (let k = 0; k < n; k++) {
      const c = document.createElement("div");
      c.className = "efx-confeti";
      c.style.left = `${Math.random() * 100}vw`;
      c.style.background = COLORES[k % COLORES.length];
      c.style.setProperty("--x", `${Math.round((Math.random() - 0.5) * 160)}px`);
      c.style.setProperty("--r", `${Math.round(Math.random() * 1080 - 540)}deg`);
      c.style.setProperty("--t", `${(2.8 + Math.random() * 1.8).toFixed(2)}s`);
      c.style.setProperty("--d", `${(Math.random() * 0.9).toFixed(2)}s`);
      capa.appendChild(c);
      setTimeout(() => c.remove(), 6000);
    }
  }

  // Arreglo de la ruleta: el confeti de la ruleta se borra al terminar (nunca se queda tapando un texto)
  const ruleta = document.getElementById("ruleta");
  if (ruleta && window.MutationObserver) {
    new MutationObserver(lista => lista.forEach(m => m.addedNodes.forEach(n => {
      if (n.classList && n.classList.contains("confeti")) setTimeout(() => n.remove(), 1900);
    }))).observe(ruleta, { childList: true });
  }

  function recibir(m) {
    if (!m || typeof m !== "object") return;
    if (m.tipo === "batalla") batalla(m);
    else if (m.tipo === "regalo") regalo(m);
    else if (m.tipo === "brillo") brillo();
    else if (m.tipo === "confeti") confeti(m.cantidad || 100);
  }
  window.efectosEduardo = recibir;   // para pruebas desde la consola

  // ---------------- Demostración (capturas): ?efectos_demo=... ----------------
  const demo = p.get("efectos_demo");
  if (demo === "batalla") recibir({ tipo: "batalla", estado: "activa", equipos: ["Tacos", "Pizza"], puntos: [14, 9], restante: 27, votantes: 23 });
  if (demo === "batalla_fin") recibir({ tipo: "batalla", estado: "fin", equipos: ["Tacos", "Pizza"], puntos: [21, 16], ganador: 0, mostrar_segundos: 1e6 });
  if (demo === "regalo") recibir({ tipo: "regalo", nivel: p.get("nivel") || "grande", titulo: "Ana mandó León", subtitulo: "¡Gracias, Ana!", segundos: 1e6 });

  // ---------------- Conexión con el bot ----------------
  function conectar() {
    if (location.protocol === "file:" || demo) return;
    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}${BASE}/efectos_ws`);
    ws.onmessage = ev => { try { recibir(JSON.parse(ev.data)); } catch (e) { /* mensaje raro: se ignora */ } };
    ws.onclose = () => setTimeout(conectar, 2000);
  }
  conectar();
})();
