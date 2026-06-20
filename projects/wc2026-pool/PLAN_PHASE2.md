Voy a consolidar los 6 planes en el documento de PHASE 2. No necesito leer código; trabajo solo sobre los planes provistos, como pide la tarea.

# PLAN DE MEJORA — PHASE 2 · WC2026 Pool (FootAnalytics)

Lead de producto+ingeniería. Consolidación de las 6 voces especialistas. Todo lo que sigue se basa **solo** en los planes; lo no resuelto va marcado `[INCIERTO]`. Anchor de archivos: `/Users/carlosvivas/personal-website/projects/wc2026-pool/`.

---

## 1. RESUMEN POR ROL

### 1.1 Estadístico (modelo)
- **Propagar incertidumbre, no el punto.** El Monte Carlo (`simAll`, `teams.html:152`) trata atk/def como fijos → prob. de campeón sobre-confiadas. Fix: bootstrap paramétrico o SE de Fisher diagonal en `fit_ratings.py`, samplear 1×/torneo, serializar `atk_sd`/`def_sd`. Tras el cambio el spread del top-5 al título **debe** ensancharse (test de sanidad).
- **Exponer números que ya existen.** `rps_major=0.164` (slice mundialista) oculto tras el `rps` overall diluido (0.169); el Elo (`elo.ratings`) se serializa y **ningún HTML lo lee**; `logloss_mat` calculado y no expuesto. Activar Elo como fallback en pairings TBD ("Brasil vs 2º Grupo F").
- **Reemplazar el `SPREAD=1.10` ad-hoc** (parche mágico, ΔRPS no significativo) por temperature-scaling sobre el 1X2, auditable (T óptimo + ΔECE/Δlog-loss OOS).
- **Comparaciones que faltan:** panel Modelo vs Mercado(de-vig Shin) vs Blend; tabla ablation (decay, ρ Dixon-Coles, spread, blend) con skill score marginal + CI pareado; log-loss como métrica primaria de discriminación junto al RPS.
- **Estructural:** banda de incertidumbre en prob. de campeón; degradar jerárquicamente outputs blandos (BTTS/Over/CS/scoreline) frente al 1X2; unificar `MAXG` (8 cliente vs 10 fitter); separar scoreline (λ DC puros) del 1X2 (blend) — hoy `fitSupremacy` re-deriva λ desde el 1X2 blendeado. ECE/reliability **sobre los partidos WC ya jugados**, no solo histórico.

### 1.2 Data Scientist (legibilidad y exposición del modelo)
- **El problema no es rigor, es legibilidad.** El backbone ya es honesto; tres activos de primera están ocultos o crudos. Coincide con el estadístico en surfacing de `rps_major`, banda de campeón y Elo muerto.
- **Separar tres niveles de incertidumbre** que hoy se mezclan bajo "confianza": (A) resultado/aleatoria = entropía del partido (ya existe, badge ⚖️); (B) calibración del modelo = ECE 0.0287 (existe, oculto); (C) parámetro/epistémica = **no propagada** (cierra con el bootstrap). No llamar "confianza" a las tres.
- **Crear un model card navegable** (`modelo.html`, ES/EN/TR): qué hace, cómo funciona, rendimiento validado (con `rps_major` titular), out-of-scope/known-failures, honestidad/accountability, fecha. Consolida disclaimers hoy dispersos en 3 páginas.
- **Explicabilidad barata y exacta** (el modelo es lineal en log-λ): waterfall de atribución por partido (`mu + atk − def + host + value_tilt`); hacer visible el value-tilt (hoy 100% invisible pese a estar validado); blend en 3 columnas (Modelo / Mercado / Blend) + edge por partido.
- **Visualizaciones que faltan** (priorizadas por impacto narrativo × coste): scatter modelo-vs-mercado, calibración en vivo (backtest + WC superpuesto), banda en prob. de campeón, waterfall, tracker de RPS acumulado. Regla de copy basada en evidencia: **número para el forecast, palabra para el consejo/lectura.**

### 1.3 Product Strategist
- **Diagnóstico nuclear que el audit no hace:** la quiniela es de **entrega única** con deadline **ya pasado (11-jun)**; durante los 38 días que importan no hay **motor de retorno**. La decisión nº1 es: ¿por qué un amigo abre la app un martes de julio?
- **El moat es el modelo como rival honesto** (🤖 concursante fantasma), no la quiniela en sí. Elevarlo de "un concursante más en la tabla" a **narrativa por partido** (tú X · modelo Y · resultado Z · puntos).
- **Fusionar** Datos+News en "el brief del partido" dentro de `match.html` (darles trabajo, no rescatarlos a la nav). **Recortar** sedes/datos/news como páginas autónomas, countdown muerto, body-map al 41%, globo y estadios como "portal del Mundial" (no producto). **Una sola clasificación.**
- **Reordena la prioridad del audit por valor de retención**, no por riesgo técnico — salvo seguridad/correctness arriba porque rompen la confianza (el leaderboard *es* el producto).
- **Opción de motor de retorno** (decisión estratégica): (a) cero-código — narrar el duelo tú-vs-modelo; (b) mini pick diario / Daily Double sobre la quiniela congelada, sin tocar el schema de `picks`. Recomendación: (a) ya, (b) si hay apetito. `[INCIERTO]` — esta es una decisión de producto abierta, no un cambio especificado.

### 1.4 Design Director
- **Tesis de marca:** no SaaS-glassmorphism genérico ("slop de IA"), sino editorial de datos (The Athletic / FiveThirtyEight) sobre chasis oscuro+dorado. **Confianza > efecto.** Rebaja el HUD/orbes del `DESIGN_STUDY.md` a acento, nunca tema; glass solo para chrome, nunca sobre datos densos.
- **Arreglo estructural = un solo `assets/theme.css`** que todas las páginas importan: elimina los 4 `:root` fragmentados y 3 nomenclaturas; escala de superficies (elevación por capas, no manchas); `@font-face` en theme.css **carga las fuentes y mata el flicker** de `--mono`/`--disp` fantasma. Capa de compat (aliases) para migrar pool.html sin Big Bang. Orden: calendar+player (rotos) → index → pool.
- **Tipografía semántica:** toda cifra comparable en mono tabular (alinea columnas); escala fija (hero/h1/h2/body/label). Retirar `.gradient-text` de los H1 → reservarlo a **un** `.stat-hero` por página (el número héroe).
- **Motion con propósito** (Emil Kowalski): solo transform/opacity, <300ms, ease-out; cablear `.reveal` (hoy CSS muerto) con un IntersectionObserver; `prefers-reduced-motion` global; quitar el glow cian de hover (tell de IA) → elevación real. Skeletons con shimmer (no spinners), error-card con reintento.
- **Charts premium** (lenguaje 538, no librería nueva): título+subtítulo de lectura + firma editorial de procedencia; heatmap monocromo cálido (no arcoíris); reliability diagram como héroe visual; banda de incertidumbre visible en prob. campeón; gridlines finos sin verticales/spines; color **solo semántico** (win/draw=gris/loss). Jerarquía de confianza codificada en el peso visual (1X2 grande, derivados pequeños + chip).

### 1.5 UX Researcher
- **La nav es un mapa de ficheros, no de tareas.** Reagrupar 6+2 destinos en 4 intenciones: **Quiniela / Partidos / Clasificación / Explora▾** (Datos·Sedes·Plantillas·Noticias bajo "Explora"; en móvil 5ª tab "Más" → sheet). News/Datos dejan de ser cul-de-sac: filas enlazables a fichas + módulo "últimas sobre [selección]" en `team.html`.
- **Toggle de idioma global** (mover a `nav.js`, único componente en las 13 páginas); **pre-requisito de correctness:** unificar la clave localStorage (`wc26-lang` vs `wc2026-lang`) antes de globalizar. `<html lang>` debe seguir al idioma activo.
- **Una pregunta → un destino canónico:** las 3 clasificaciones colapsan a `teams.html`; calendar/match enlazan o renderizan el mismo componente (nunca una versión degradada que mis-ordene empates).
- **Tres journeys con sus fricciones:** A "compito" (onboarding contextual + empty state + estado de deadline honesto + cierre del loop al grafo); B "exploro datos" (jerarquía de confianza visual + report-card como destino + storytelling suave con `.reveal`, no scrolljacking); C "sigo en vivo" (los **tres estados** del match center pre/live/post + fallo de ESPN = estado con reintento, no void en blanco).
- **Sistema de estados faltante** (skeleton/error+reintento/empty/pre-post-torneo) como módulo único; accesibilidad bajo el listón (focus-visible site-wide, reduced-motion global, contraste de badges `#7a5e00`, pins SVG operables por teclado). **Hueco propio:** falta investigación con usuarios reales — 5 tests de pasillo validarían la priorización en una tarde.

### 1.6 Full-Stack (estructura/ingeniería)
- **Correcciones verificadas al audit:** los backups **no están desplegados** (`.gitignore` los excluye, Pages sirve desde git) → riesgo de filtración de anon key vía backup = nulo; el blindaje de seguridad **ya está a medio camino** (`schema_hardening.sql`, `admin.html` con Auth, backup a repo privado) — falta **ejecutar el SQL** + deshabilitar sign-ups, no rediseñar; `logError`→tabla `errors` ya existe, falta **cablear** los `catch(e){}` vacíos.
- **De-duplicar motores triplicados en ES modules nativos (sin build):** `assets/aliases.js` (un solo `normTeam` — arregla bug real: Bosnia/Costa de Marfil/Cabo Verde renderizan 0-0-0 en match; + bug "Türkiye"/"Korea" en `computeScore`); `standings.js` (motor único por profundidad de render — arregla mis-ordenado de empates y bug de clave `results.json`); `model.js` (λ DC, Poisson, sim — unifica `MAXG`); `bracket.js` (terceros FIFA, la lógica más difícil de depurar). Orden: aliases → standings → bracket → model.
- **Monolito `pool.html` (3.784 líneas): NO trocear ahora.** Producto efímero, deadline pasado; riesgo de romper el scoring de 201 pts en vivo supera el beneficio. La extracción de módulos ya lo adelgaza (80% del valor, 20% del riesgo). Troceo diferido a Phase 3 con **gate explícito**: solo si sobrevive a 2026.
- **Estados + logging:** promover `logError` a `assets/log.js` (con rate-limit), cablear los catches mudos de ESPN, helpers `renderSkeleton`/`renderError(retry)`/IntersectionObserver en `assets/ui.js`.
- **PWA/SRI:** SW híbrido por tipo de recurso (HTML network-first, assets cache-first+precache, JSON stale-while-revalidate, APIs ESPN no cachear) → offline real del shell sin Workbox; centralizar registro en `sw-register.js`. SRI **bloqueado por version-floating** (`@supabase/supabase-js@2` es rango) → pinear versión exacta primero, luego `integrity`+`crossorigin`; **recomendación: vendorizar** supabase-js y confetti, Three.js en CDN con SRI. **Veredicto build step: NO** — ES modules cubren la modularidad; un build se interpone entre editor y Pages en vivo. Concesión opcional: script Python de codegen (SRI + array PRECACHE), no un build.

---

## 2. TEMAS TRANSVERSALES (consenso = prioridad)

| Tema | Voces que coinciden | Lectura |
|---|---|---|
| **Surface `rps_major` (el número honesto WC) como titular** | Estadístico, Data Scientist, UX | Consenso fuerte. Trivial, alto valor de honestidad. Hoy se muestra el RPS overall diluido. |
| **Activar el Elo muerto** para pairings TBD | Estadístico, Data Scientist, Product (bajo), UX | Cómputo ya pagado, cero lectores HTML. Cierra un gap funcional. |
| **Banda de incertidumbre en prob. de campeón** (Monte Carlo sub-disperso) | Estadístico (origen), Data Scientist, Design | El cambio de **rigor** más importante; precomputar en `fit_ratings.py`, no en cliente. |
| **Jerarquía de confianza: degradar outputs blandos (BTTS/Over/CS) frente al 1X2** | Estadístico, Data Scientist, Product, Design, UX | **Consenso de las 5 voces de modelo+diseño.** Codificar la fiabilidad en el peso visual, no en un disclaimer textual. |
| **Una sola "Clasificación" (engine único)** | Product, Design, UX, Full-Stack | **Consenso casi total.** No es dedup técnica: dos tablas contradictorias erosionan la marca "rigor". `standings.js` es el vehículo. |
| **Fusionar/recolocar Datos+News** (no dejarlas huérfanas) | Product (disolver en brief), UX (Explora + cross-link) | Coinciden en el problema; **divergen en la solución** → ver §3. |
| **Sistema de estados (skeleton/error+reintento/empty)** + cablear catches vacíos | Design, UX, Full-Stack | **Consenso fuerte.** Módulo único, no copy-paste. Liga UX con telemetría (tabla `errors`). |
| **`theme.css` único** (mata 4 `:root`, flicker, contraste) | Design (origen), Full-Stack, UX (a11y depende de él) | Habilitador transversal: focus-visible y reduced-motion globales **dependen** de esta migración. |
| **Cablear `.reveal`** (CSS muerto) | Design, UX, Full-Stack | Un IntersectionObserver compartido; respeta reduced-motion. |
| **Toggle de idioma global + clave localStorage unificada** | Product (coste social), UX (IA), Full-Stack (`wc26`/`wc2026` divergen) | Trivial técnico, caro socialmente (grupo trilingüe). Unificar clave **antes** de globalizar. |
| **Modelo como rival / honestidad como marca; preservar el backbone** | Las 6 | Nadie toca la MLE Dixon-Coles / walk-forward / live self-test / value-tilt. **Toda mejora va por encima, nunca reescribe el núcleo.** |
| **Seguridad Supabase (RLS, PII, admin key)** | Product (P0 de confianza), Full-Stack (ejecutar, no diseñar) | Full-Stack aclara que está a medio camino; falta **correr el SQL** + view `leaderboard_users` sin email + quitar `?key=` redundante + verificación con curl. |

**Divergencias a resolver (no consenso):**
- **Datos+News:** Product quiere **disolverlas** en el brief del partido; UX quiere **conservarlas** bajo "Explora" + cross-links. → §4 las trata como complementarias (subsunción en match + cross-link), pero la decisión "¿siguen existiendo como página?" queda para Carlos. `[INCIERTO]`
- **Motor de retorno diario** (Product): es la tesis más fuerte de una voz y **no la mencionan las otras 5**. Alta palanca, pero es una **decisión de producto abierta**, no un cambio especificado. `[INCIERTO]`
- **Backups como riesgo P0:** Product/audit lo ponen P0; Full-Stack lo **rebaja a higiene** (no desplegados). Prevalece Full-Stack (verificado en código).

---

## 3. PLAN DE MEJORA UNIFICADO Y PRIORIZADO

Agrupado por carril. Prioridad **P0** (rompe/define el producto o la confianza) → **P3** (pulido). Cada ítem indica voz(es) de origen y, cuando aplica, el archivo/módulo.

### Carril A — Ingeniería / seguridad (habilita todo lo demás)
| P | Acción | Origen | Notas |
|---|---|---|---|
| **P0** | Ejecutar `schema_hardening.sql` en Supabase + deshabilitar sign-ups + endurecer Option A a UUID admin + **verificar con curl** (POST official_results / DELETE users → 401/403) | Full-Stack, Product | Cero código. El agujero sigue abierto hasta correrlo. |
| **P0** | View `leaderboard_users` (id, name, joined_at — **sin email**) + dropear `public read users`; quitar admin `?key=` redundante (ya hay Auth) | Full-Stack | PII hoy pública. |
| **P0** | `assets/aliases.js` (`normTeam` único) cableado en las 3 páginas y en **ambos lados** de `computeScore` | Full-Stack, UX | Arregla bug Bosnia/CdI/CV (0-0-0) + bug "Türkiye"/"Korea" (puntos perdidos en silencio). |
| **P1** | `assets/log.js` (promover `logError`, rate-limit) + cablear los `catch(e){}` mudos de ESPN | Full-Stack, UX, Design | Un fallo de ESPN en vivo hoy es invisible. |
| **P1** | `assets/standings.js` (motor único por profundidad) | Full-Stack, UX, Product, Design | Resuelve mis-ordenado de empates + bug clave `results.json` + las 3 clasificaciones. |
| **P2** | `assets/model.js` (λ DC, Poisson, sim; unifica `MAXG`→10) + `assets/bracket.js` (terceros FIFA, testeable) | Full-Stack, Estadístico | No tocar `fit_ratings.py`; model.js consume su JSON. |
| **P2** | Pinear versiones CDN + SRI + **vendorizar** supabase-js/confetti; Three.js CDN con SRI | Full-Stack | SRI imposible sobre rango `@2`. |
| **P2** | SW híbrido por recurso + `sw-register.js` centralizado | Full-Stack | Offline real del shell, sin build. |
| **P3 (gate 2026)** | Trocear `pool.html` con tests al scoring | Full-Stack, Product | **Solo si sobrevive al torneo.** |
| — | **Build step: NO.** Concesión opcional: script Python codegen (SRI + PRECACHE) | Full-Stack | No es build. |

### Carril B — Analítica / modelo (→ input directo a PHASE 3)
| P | Acción | Origen | Archivo |
|---|---|---|---|
| **P1** | Surface `rps_major` como número titular + RPS Skill Score (% mejora vs climatología) | Estadístico, Data Scientist, UX | `teams.html` / model card |
| **P1** | Exponer `logloss_mat` como métrica primaria de discriminación (paneles internos) | Estadístico | `fit_ratings.py:377` |
| **P1** | Activar Elo (`R.elo.ratings`+`s/tau`, portar `elo_probs()` a JS) como fallback en pairings TBD | Estadístico, Data Scientist, UX | `match.html` |
| **P1** | Calibración **en vivo** (ECE + reliability sobre partidos WC jugados; backtest frío + WC caliente superpuestos) | Estadístico, Data Scientist | live self-test |
| **P2** | Bootstrap paramétrico / Fisher-SE de ratings → `atk_sd`/`def_sd`; samplear 1×/torneo; **banda** en prob. campeón (percentiles); semilla fija serializada | Estadístico, Data Scientist, Design | `fit_ratings.py` + `teams.html:152`; precomputar, no en cliente |
| **P2** | Reemplazar `SPREAD=1.10` por temperature-scaling sobre 1X2; reportar T + ΔECE/Δlog-loss OOS | Estadístico | `fit_ratings.py:92` |
| **P2** | Panel Modelo vs Mercado(Shin) vs Blend (log-loss/RPS_major/ECE); elegir w por log-loss OOS | Estadístico, Data Scientist | nueva sección |
| **P2** | Tabla ablation (decay, ρ, spread, blend) con skill score marginal + CI pareado | Estadístico | `fit_ratings.py` |
| **P2** | Explicabilidad: waterfall de atribución por partido (`mu+atk−def+host+value_tilt`) + visibilizar value-tilt + blend 3 columnas + edge vs mercado | Data Scientist | `match.html` (`predMatchLambdas`, `valTilt`) |
| **P3** | Corregir `fitSupremacy`: scoreline desde **λ DC puros**, 1X2 desde blend (hoy mezclados → copy/lógica deshonesta) | Estadístico, Data Scientist | `teams.html`/`match.html` |

### Carril C — Producto / IA del modelo (→ input a PHASE 4 y PHASE 3)
| P | Acción | Origen | Notas |
|---|---|---|---|
| **P0/decisión** | **Definir el motor de retorno** (duelo tú-vs-modelo narrado / mini pick diario) | Product | `[INCIERTO]` — decisión estratégica, no cambio especificado. Bloquea el "por qué vuelvo en julio". |
| **P1** | Elevar el modelo 🤖 de "concursante en tabla" a **narrativa por partido** | Product, Data Scientist | Es el moat. |
| **P1** | **Una sola clasificación** canónica (`teams.html`); calendar/match enlazan o reusan el mismo componente | Product, UX, Design, Full-Stack | Coincide con `standings.js` (Carril A). |
| **P1** | Model card navegable (`modelo.html`, ES/EN/TR): qué hace, cómo funciona, rendimiento, out-of-scope, honestidad, fecha | Data Scientist, UX | Consolida disclaimers dispersos; report-card como destino, no módulo enterrado. |
| **P2** | Fusionar Datos+News en "el brief del partido" en `match.html` (subsunción) **y/o** cross-link a fichas | Product (disolver) ↔ UX (conservar+linkear) | Divergencia §2 → decisión de Carlos. `[INCIERTO]` |
| **P2** | Comparador "tu pick vs el de un amigo" elevado a primer nivel; ancla de identidad "tú" persistente | Product, UX | Convierte visitas en retorno. |
| **P3** | Recortar/esconder body-map al 41%, countdown muerto; sedes/globo fuera de nav primaria | Product | Estado post-torneo también (tras 19-jul). |

### Carril D — Diseño / UX / accesibilidad (→ input a PHASE 4)
| P | Acción | Origen | Notas |
|---|---|---|---|
| **P1** | `assets/theme.css` único: un `:root`, escala de superficies, **cargar fuentes** (mata flicker), tokens spacing/motion, capa de compat | Design, Full-Stack | Habilita focus-visible + reduced-motion globales. Orden: calendar+player→index→pool. |
| **P1** | Sistema de estados como módulo único: `renderSkeleton`/`renderError(retry)`/IntersectionObserver para `.reveal` | Design, UX, Full-Stack | `assets/ui.js`. |
| **P1** | Abrir la nav a 4 intenciones (Quiniela/Partidos/Clasificación/Explora▾; móvil "Más"→sheet) + toggle idioma global en `nav.js` + clave localStorage unificada + `<html lang>` dinámico | UX, Product | Unificar clave **antes** de globalizar. |
| **P1** | Jerarquía de confianza visual: 1X2 grande/héroe, derivados pequeños bajo "Mercados derivados (menos fiables)" + chip | Design, UX, Estadístico, Data Scientist, Product | Consenso de 5 voces. |
| **P2** | Lenguaje de charts (título+subtítulo de lectura + firma editorial; heatmap monocromo; reliability como héroe; banda de incertidumbre; gridlines 538; color solo semántico) | Design, Data Scientist | Sobre los SVG existentes, sin librería nueva. |
| **P2** | Tres estados del match center (pre/live/post) + fallo ESPN = estado con reintento/fallback al modelo; bracket real en KO; indicador "LIVE" honesto | UX | `match.html`. |
| **P2** | Retirar `.gradient-text` de H1 → un `.stat-hero` por página; mono tabular en toda cifra; motion con propósito (quitar glow cian) | Design | |
| **P2** | Onboarding contextual de la quiniela (empty state + progressive disclosure + estado de deadline honesto + cierre del loop al grafo) | UX | Journey A. |
| **P3** | Pase de accesibilidad: focus-visible site-wide, reduced-motion global, contraste badges `#7a5e00`→AA, pins SVG operables por teclado, `aria-hidden` en emoji decorativo | UX, Design | Depende de theme.css único. |
| **P3** | Cross-link sedes↔partidos; responsive táctil del grid de 104 picks (patrón móvil propio); **5 tests de pasillo** | UX | El test de usuarios reordenaría con datos; subir si se puede esta semana. |

### Mapeo a las fases siguientes
- **→ PHASE 3 (backbone analítico):** Carril B completo + de Carril C el model card y la narrativa del modelo + de Carril D el lenguaje de charts y la comunicación de incertidumbre (banda, número-vs-palabra, jerarquía de confianza, reliability en vivo).
  - *Qué análisis:* bootstrap de ratings, temperature-scaling, ablation, panel modelo/mercado/blend, ECE en vivo.
  - *Inputs:* `ratings.json` (añadir `atk_sd`/`def_sd`, `champion.{p50,p10,p90}`), `fit_ratings.py`.
  - *Outputs/charts:* prob. campeón con banda, reliability backtest+live, scatter modelo-vs-mercado, waterfall de atribución, tracker RPS acumulado, heatmap monocromo.
  - *Comunicación de incertidumbre:* tres niveles A/B/C nombrados y separados; número para forecast / palabra para lectura; "un número sin su incertidumbre es tergiversación".
- **→ PHASE 4 (IA + estructura de páginas):** Carril D (theme.css, nav 4-intenciones, estados, match center, a11y) + de Carril C la clasificación única, el model card como destino, la recolocación de Datos/News, identidad "tú". Mapa de IA propuesto por UX (topbar global de 4 + Explora + deep pages con breadcrumbs).

---

## 4. RESEARCH ÚTIL (best-practices que aplican de verdad, con fuente)

**Modelo / forecasting (PHASE 3):**
- Propagar la posterior, no el punto, separa un forecast calibrado de uno over-confident — [JRSS-C 2025, state-space EPL](https://academic.oup.com/jrsssc/article/74/3/717/7929974). → bootstrap de ratings.
- El gold-standard a batir es el **mercado de-vig**, no la climatología; el **log/ignorance score discrimina mejor que el RPS** (58.6% vs 56.1% con odds reales) — [penaltyblog 2025](https://pena.lt/y/2025/05/01/better-metrics-for-football-forecasts-moving-beyond-the-ranked-probability-score/), [arXiv 1908.08980](https://arxiv.org/abs/1908.08980). → panel modelo/mercado, log-loss primario.
- Predicción de torneos internacionales (metodología de referencia) — [Groll et al.](https://epub.ub.uni-muenchen.de/31579/1/Groll_Prediction.pdf).

**Comunicación de incertidumbre (PHASE 3 + 4):**
- Para forecasts el usuario prefiere **números**; las palabras sirven para el consejo/lectura — [Cambridge JDM](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/cultivating-credibility-with-probability-words-and-numbers/3CD3BC3EC009661BB60C22F527FC7FC8), [Trends Cogn Sci 2022](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(22)00060-2).
- Ninguna visualización captura toda la incertidumbre → usar un **conjunto** de gráficos, no un único "índice de confianza" — [Hullman Lab / 538](https://www.hullmanlab.northwestern.edu/paper/2020/09/01/election-forecasts.html).
- Model cards como artefacto único de honestidad — [Mitchell et al. 2019](https://aiwiki.ai/wiki/model_card).

**Producto / retención (PHASE 4):**
- El problema de una quiniela de entrega única es **retención estructural**, no alcance; el **Daily Double / pick por jornada** es la mecánica de retorno dominante 2026 — [Riddle whitepaper](https://www.riddle.com/blog/whitepaper/score-predictor-whitepaper-daily-returns-not-day-1-spikes/), [Superbru](https://www.superbru.com/worldcup_predictor/), [bet365 Tournament Challenge](https://www.telecomasia.net/blog/bet365-tournament-challenge-guide/), [easypromos](https://www.easypromosapp.com/blog/en/how-to-organize-world-cup-predictions/). Baseline de la categoría a superar: [BeTeam](https://beteamapp.com/), [Prodefy](https://prodefy.co/en), [GoalPool](https://www.goalpool.app/).

**UX / IA / estados (PHASE 4):**
- Match center = **tres estados** pre/live/post; timeline/heatmap/stats alargan la sesión 1.5→4.3 min — [Sportmonks](https://www.sportmonks.com/blogs/knockout-match-centres-best-ux-patterns-data-requirements/), [MoldStud](https://moldstud.com/articles/p-live-score-updates-key-features-that-make-a-sports-app-stand-out).
- Empty/error states como momentos de onboarding; progressive disclosure contextual, no tour modal — [Raw.Studio](https://raw.studio/blog/empty-states-error-states-onboarding-the-hidden-ux-moments-users-notice/), [UX Design Institute](https://www.uxdesigninstitute.com/blog/ux-onboarding-best-practices-guide/), [Userpilot](https://userpilot.com/blog/onboarding-ux-examples/).
- Storytelling al servicio de la narrativa, evitar scrolljacking — [UI Deploy](https://ui-deploy.com/blog/complete-scrollytelling-guide-how-to-create-interactive-web-narratives-2025).

**Diseño (PHASE 4):**
- Dark mode data-heavy: off-black/off-white, 2–3 acentos, capas de elevación, line-height alto (rebajar el HUD) — [Qodequay](https://www.qodequay.com/dark-mode-dashboards).
- Motion: <300ms, ease-out para entradas, solo transform/opacity, press scale(.97), nunca scale(0) — [Emil Kowalski](https://github.com/leadgenjay/claude-skills/blob/main/skills/design-motion-principles/references/emil-kowalski.md).
- Lenguaje editorial de charts (título+subtítulo, direct labeling, spines removidos, firma de procedencia) — [Lessons from FiveThirtyEight](https://towardsdatascience.com/data-visualization-hack-lessons-from-fivethirtyeight-graphs-e121080725a6/). Contraejemplo (glass sobre datos densos = lo que NO hacer): [Muzli 2026](https://muz.li/blog/best-dashboard-design-examples-inspirations-for-2026/).

**Ingeniería (Carril A):**
- PWA sin build (ES modules + import maps) — [goulet.dev](https://goulet.dev/posts/build-a-pwa-without-a-build-step/), [pure-pwa](https://github.com/mvneerven/pure-pwa).
- SW caching híbrido por recurso — [Workbox/Chrome](https://developer.chrome.com/docs/workbox/caching-strategies-overview).
- RLS + anon key segura client-side si las policies son correctas (no hace falta backend) — [Supabase API keys](https://supabase.com/docs/guides/getting-started/api-keys), [makerkit RLS](https://makerkit.dev/blog/tutorials/supabase-rls-best-practices). SRI imposible sobre rango de versión — [MDN SRI](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity), [OWASP](https://owasp.org/www-community/controls/SubresourceIntegrity).

---

### Notas finales de consolidación
- **Lo que las 6 voces protegen unánimemente:** el backbone Dixon-Coles (MLE + gradiente analítico), time-decay, walk-forward sin fuga, live self-test congelado, value-tilt validado, badge de entropía, de-vig Shin + log-opinion-pool. **Toda mejora va por encima.**
- **`[INCIERTO]` que requieren decisión de Carlos antes de PHASE 3/4:** (1) el motor de retorno diario (tesis de una sola voz, alta palanca); (2) si Datos/News sobreviven como página o se disuelven en el brief; (3) si el proyecto vive más allá de 2026 (gate del troceo de `pool.html` y del esfuerzo de refactor profundo).
- **Quick wins de máximo ratio impacto/esfuerzo** (consenso o coste casi nulo): surface `rps_major`, activar Elo, `aliases.js`, ejecutar el SQL de seguridad, una sola clasificación, cablear catches a `errors`.