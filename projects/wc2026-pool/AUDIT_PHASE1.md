AUDIT — PHASE 1 · WC2026 Pool (web app)

Lead técnico. Consolidación de las 6 auditorías (A1 IA/landing, A2 pool, A3 schedule/match/teams, A4 contenido/venues, A5 backbone analítico, A6 frontend). Solo se reporta lo presente en ellas; lo no verificado se marca como [INCIERTO].

Ruta: `/Users/carlosvivas/personal-website/projects/wc2026-pool/`. Marca: FootAnalytics. Stack: PWA estática client-side, 13 HTML que hidratan desde `data/*.json` + Supabase para la quiniela. Sin build step, sin backend propio (salvo Supabase).

---

## 1. PROPÓSITO Y USER JOURNEY ACTUAL

**Propósito.** Hub del Mundial 2026 (11 jun – 19 jul, USA/MEX/CAN) que fusiona cuatro productos:
1. **Quiniela social** (`pool.html`) — producto estrella, CTA primaria.
2. **Centro de datos / live** — calendario de 104 partidos, marcadores en vivo (ESPN API sin clave), spotlight de partido, fichas de selección/jugador/estadio.
3. **Modelo predictivo propio** — Dixon-Coles + tilt por valor de plantilla, con auto-evaluación en vivo sin fuga (backtest congelado pre-torneo). Es el ángulo "analytics" de la marca.
4. **Contenido editorial ligero** — noticias (RSS Google News vía proxies CORS) y rankings/curiosidades.

**User journey feliz (móvil, durante torneo).** Index → Match Spotlight en vivo → tap a la tarjeta → `match.html` (predicción del modelo + datos) **o** CTA dorada → `pool.html` a competir. La bottom-tab da salto lateral a Standings/Calendar/Venues/Squads. Búsqueda global (`/` o FAB 🔍) lleva directo a selección o jugador.

**Fricciones reales del journey (transversales a varias auditorías):**
- **News y Datos son ciudadanos de segunda**: fuera de la nav global y de las tabs. News solo accesible por una CTA ghost del héroe; Datos por un "Ver todos →" lateral. Salir del index = perder acceso a ambas. Son dos páginas con contenido sustancial tratadas como callejones sin salida.
- **Cambio de idioma atrapado en el Home**: el toggle EN/ES/TR solo aparece en index; dentro de cualquier otra página no se puede cambiar idioma sin volver.
- **`sedes.html` es cul-de-sac**: no conecta estadios con sus partidos pese a ser la relación natural.
- **Countdown muerto**: el torneo ya empezó; el héroe ahora muestra Match Spotlight (buena adaptación), pero queda código del path pre-torneo.

---

## 2. PÁGINAS, RUTAS, COMPONENTES Y FLUJOS DE DATOS

### 13 páginas HTML

| Página | Rol | En nav | Reachabilidad |
|---|---|---|---|
| `index.html` | Landing 3D / hub (globo Three.js, Match Spotlight) | ✅ Home | Raíz |
| `teams.html` | **Clasificación + forecast** (12 tablas live + Monte Carlo 8.000 sims + report-card de calibración) | ✅ Standings | Nav |
| `calendar.html` | Hub de fixtures, 3 vistas: Partidos / Clasificación / Cuadro | ✅ Calendar | Nav + CTAs |
| `pool.html` | **Quiniela** (producto estrella, 199 KB / 3.777 líneas) | ✅ Pool | Nav + CTA primaria + admin |
| `sedes.html` | 16 estadios (SVG-map con pins + acordeón) | ✅ Venues | Nav |
| `plantillas.html` | Índice de 48 plantillas | ✅ Squads | Nav |
| `team.html` | Ficha de selección (`?code=`) | ❌ deep | Cross-links |
| `player.html` | Ficha de jugador (`?id=`) | ❌ deep | Cross-links |
| `match.html` | **Centro de partido** (`?m=`) — la página más profunda | ❌ deep | Home/calendar/team |
| `datos.html` | Rankings y curiosidades | ❌ **huérfana de nav** | 1 link lateral en home |
| `news.html` | Noticias RSS | ❌ **huérfana de nav** | 1 CTA en home |
| `admin.html` | Backoffice resultados (auth por `?key=`) | ❌ **huérfana total** | URL + key |
| `_design-directions.html` | Scratch de diseño | ❌ | Artefacto de dev |

### Componentes compartidos (`assets/`)
- **`nav.js`** — nav global inyectada en `<div id="site-nav">`: top-bar sticky (desktop, 6 enlaces + FAB búsqueda) y bottom-tab estilo app (móvil ≤720px, safe-area-inset, grayscale→color activo). Pieza app-grade. Toggle de idioma solo en Home.
- **`search.js`** — overlay de búsqueda global (atajo `/` o FAB), jugadores+selecciones desde `search_index.json`, accent-insensitive, navegación por teclado. Buena, infrautilizada.
- **`i18n.js`** — `wcT(dict,key)` EN/ES/TR, fallback es→key, auto-detección por `navigator.language`, default `es`.
- **`theme.css`** — el design system real ("Direction B / HUD": `--gold`, `--cyan`, `--glass`, `--mono`, `--disp`, orbs, glass, `.reveal`).
- **PWA**: `manifest.json` (standalone, 4 iconos incl. maskable), `sw.js` (network-first, cache `wc26-v88` — 88 bumps = iteración intensa). Registro de SW repetido inline en cada página.

### Flujo de datos
Cada `.html` es un cascarón que hidrata client-side desde ~17 ficheros en `data/` (schedule, ratings, ratings_baseline, results, stats, news, value_logV, search_index, host_maps, coaches, numbers, team_xi, teams/*, players/*…) + assets de jugadores (~970 dirs) y estadios (16). APIs externas en runtime: ESPN (scoreboard/standings/summary, sin clave), flagcdn, 4 proxies CORS para RSS, CDN unpkg (Three.js) y textura de threejs.org.

### Scripts (`scripts/`)
- **`fit_ratings.py`** — pipeline analítico offline. `fit_dixon_coles()` (MLE Poisson ponderado, gradiente analítico L-BFGS-B, time-decay, ridge, ρ ajustado, sum-to-zero), `elo_replay()` + `fit_ordered_logit()` (Elo World-Football), `walk_forward_backtest()` (expanding-origin, refit 90 d, sin fuga). Salida → JSON estáticos.

### Supabase (`schema.sql`, 187 líneas)
4 tablas: `users`, `picks` (PK=user_id, una entrega/usuario), `official_results` (singleton id=1), `errors` (log client-side). CHECK constraints decentes (starred=8, goles 0-30, jsonb object). RLS habilitado pero policies efectivamente abiertas (ver §4 seguridad). Deadline `insert picks` bloqueado server-side tras `2026-06-11T19:00:00Z` (cuadra con el JS).

---

## 3. PROCESOS ESTADÍSTICOS / ANALÍTICOS

Backbone **sólido, honesto y bien validado** (consenso A5). Núcleo offline → JSON estático → cliente reconstruye λ y arma el grid. 100% client-side, sin backend.

| Proceso | Dónde | Estado |
|---|---|---|
| **Dixon-Coles core** | `fit_ratings.py` | MLE Poisson ponderado, gradiente analítico, time-decay (half-life 1460 d), ridge 0.03, ρ ajustado = −0.0472, n≈49k partidos. Mostrado: 1X2, scorelines, BTTS/Over2.5/CS. |
| **Spread global 1.10** | `fit_ratings.py` | Parche post-centrado contra under-dispersion. ΔRPS overall no significativo; solo gana en favoritos >0.75. Ad-hoc declarado. |
| **Value tilt** | `value_logV.json` | β=0.06, validado OOS pareado (ΔRPS −0.000877, CI [−0.0015,−0.0003], p=0.0044). |
| **Blend de mercado (runtime)** | `match.html` | De-vig Shin → log-opinion-pool w_model=0.3. Fallback a modelo puro. Tag de fuente por predicción. |
| **Monte Carlo del torneo** | `teams.html` `simAll()` N=8.000 | Semilla fija (mulberry32) → forecast determinista. Prob. de pase + favoritos al título. **No propaga incertidumbre de ratings** (sub-disperso). |
| **Backtest sin fuga** | `walk_forward_backtest()` | RPS/Brier/LogLoss/Acc/ECE + baseline climatología. |
| **Live self-test congelado** | `index.html` / `teams.html` | Puntúa `ratings_baseline.json` (snap 10-jun, datos <11-jun) contra resultados WC reales vía ESPN. Forward-test real, sin fuga. |
| **Scoring de la quiniela** | `pool.html` `computeScore()` | 201 pts verificado (120 grupos + 16 terceros + 65 KO). Final score y golden boot NO puntúan (desempate manual). |

**Comunicación de incertidumbre** — gran fortaleza: report-card "¿Cómo de fiable es el modelo?" (RPS vs baseline, acc, ECE, frase de calibración), diagrama de fiabilidad SVG, predicción pre-match congelada mostrada post-resultado, disclaimers explícitos ("no bate al mercado", "probabilidades no certezas").

---

## 4. DEBILIDADES

### 4.1 Arquitectura de información / UX confusa
- **News y Datos fuera de la nav** (A1, A4 concuerdan) — el fallo de IA más grave; dos features completas con un único punto de entrada.
- **Tres "clasificaciones" distintas para la misma pregunta** (A3, hallazgo central): nav "Standings"=`teams.html` (la más fuerte, con forecast) vs sub-vista "Clasificación" de `calendar.html` (sin forecast, sin badges FIFA) vs tab tabla de `match.html` (sin forecast **y** puede mis-ordenar empates por carecer del rank autoritativo de ESPN). El usuario que pulsa dos "Clasificación" ve dos tablas distintas.
- **Idioma atrapado en Home** (A1, A6).
- **Nombres de fichero solapados** `teams.html` / `team.html` / `plantillas.html` + títulos en idioma mixto (`<title>` unos ES, otros EN); `<html lang="es">` hardcodeado pese a ser trilingüe → malo para SEO/accesibilidad (A1).
- **`sedes.html` y `team.html` con afordances inconsistentes**: la misma entidad-partido es clicable en `team.html` pero inerte en `sedes.html` (A3, A4).

### 4.2 Lógica duplicada (deuda de mayor riesgo de divergencia)
- **Motor de clasificación triplicado** (A3): `buildStandings`+`loadEspnStandings`+normalizadores (`snrm`/`mcSnrm`/`nrm2`) copiados en `teams.html`, `calendar.html` y `match.html`. El propio `match.html` lo documenta: *"DUPLICATED FROM calendar.html. Keep in sync."* **Drift ya real**: los alias-maps han divergido — `match.html` (`MC_SALIAS`) no tiene Bosnia/Costa de Marfil/Cabo Verde → esos grupos pueden renderizar 0-0-0 en el match-center cuando haya datos live.
- **Resolución de bracket / terceros por backtracking triplicada** (A2): bracket del usuario (`assignThirds`) vs scoring en vivo (`lbKoWinners`) vs modelo (`buildModelPicks`). Tres copias; un cambio FIFA obliga a tocar tres sitios.
- **Dos mapas de alias de nombres divergentes** entre `team.html` (`TALIAS`) y `teams.html` (`T_ALIAS`) (A4) — mismo problema resuelto dos veces con cobertura distinta.
- **Datos de bracket hardcodeados** (`R32_SPEC`, `GROUPS`) duplicados entre `pool.html` y `admin.html` (A2) — dos fuentes de verdad.
- **Helpers** (`fmtVal`/`esc`/`norm`) copy-pasted por página (A4).
- **`isPlaceholder` regex divergente** en las tres páginas del cluster fixtures (A3).

### 4.3 Design system bypasseado (deuda visual, A6 + A3)
- `theme.css` existe pero **index, calendar y pool NO lo importan** y definen su propio `:root`. Calendar/pool introducen un **tercer** esquema (`--primary`, `--surface`, `--shadow`) inexistente en theme.css. Cambiar un color de marca exige editar **4 bloques `:root` con 3 nomenclaturas**.
- **Bug concreto del drift**: `calendar.html` usa `var(--mono)` y `var(--disp)` que **nunca define ni carga** (no carga JetBrains Mono ni Space Grotesk) → resuelven a Inter heredado. La tipografía display parpadea entre Space Grotesk (home/teams) e Inter (calendar/pool) al navegar.
- **Dos design systems en el cluster fixtures**: `teams.html` usa `theme.css`; `calendar`/`match` definen color inline → la página que la nav llama "Standings" parece otro producto que la sub-vista "Clasificación" del calendario.
- **`.gradient-text` en cada H1** (A6) — cliché de landing AI; aplicado en todos los H1 aplana la jerarquía.

### 4.4 Estados faltantes (loading / error / empty) — consenso A3, A5, A6
- **Sin skeletons/shimmer en ningún sitio**: todas las páginas data-driven muestran un literal "Cargando…" o "…".
- **Fallo de fetch = void en blanco**: los `catch` del index hacen `innerHTML=''; return;` → columnas que desaparecen sin mensaje ni reintento. No hay UI de fallo de ESPN en ninguna de las 3 páginas del cluster (catch silenciosos).
- **`.reveal` scroll-reveal es código muerto**: theme.css lo define pero ningún `IntersectionObserver` lo activa; el DESIGN_STUDY lo prometía como principio de motion central.
- **`catch(e){}` vacíos** en `buildLiveOfficial`/`loadPoolRatings` (pool) tragan errores de red sin loguear a la tabla `errors` → fallo de ESPN invisible durante el torneo (A2, A5).
- **Sin estado pre-torneo / "próximo partido en N días"** explícito en calendar (A3).

### 4.5 Seguridad — punto débil consciente (A2, documentado en `schema.sql`)
- **Anon key con escritura total**: cualquiera con la anon key (pública en el HTML) puede `insert/update official_results` (`with check (true)`) → **falsificar resultados y reordenar el leaderboard**; y `delete users` (`using(true)`) → **borrar participantes** (cascade a picks). La "admin key" solo oculta el formulario, no protege la BD.
- **Admin key en claro** (`mundial2026-vivas`) comparada en cliente, visible en el source.
- **`official_results` sin restricción temporal** → vector de manipulación siempre abierto (a diferencia de `picks`).
- **PII expuesta**: `public read users/picks` sirve nombre+email de todos vía API pública.
- Asumible para pool de amigos sin dinero; **si se publica abierto, un troll destruye el leaderboard en 30 s**. Mitigación sin backend: Edge Function con secreto server-side para `official_results` write y `users` delete.

### 4.6 Fragilidad de código / correctness latente
- **Scoring acoplado a strings exactos**: `computeScore` compara `ut.name === officialTeamName`; el path admin **no** normaliza (live sí, con `lbnorm`). "Türkiye" vs "turkiye" o "Korea" vs "South Korea" → puntos perdidos en silencio (A2).
- **Bug de clave `results.json`** (A3): README dice key=índice 0-based; `teams.html`/`match.html` lo respetan, pero `calendar.html` prefiere `m.num` (1-based FIFA) cuando existe → lee el resultado equivocado/ninguno para cualquier match con `num`. Enmascarado por el overlay ESPN, pero el fallback file-based está roto en uno de tres lectores.
- **Doble clave de localStorage del idioma** (A1, A6): index escribe `wc26-lang`; nav.js/i18n.js/pool/calendar leen `wc2026-lang` primero. Funciona por fallback; un refactor que lo olvide rompe el idioma. *"Set English but the menu stays Spanish"* latente.
- **Claves i18n huérfanas** (`home.q*`, `home.explore`) de un grid "Explora" eliminado del DOM (A1).
- **Dependencia de ESPN sin contrato**: parsing por regex `Group [A-L]` y `displayValue`; cambio de shape → fallo silencioso (A2, A3).
- **CDN sin SRI** (supabase-js, confetti, QR, Three.js) — riesgo supply-chain bajo pero real (A2, A6).
- **`i18n` inline por página** (diccionario `T={es,en,tr}` no centralizado) → riesgo de claves desincronizadas (A1).

### 4.7 Accesibilidad — bajo el listón de producción (A6)
- `outline:none` sin reemplazo visible en varios sitios (calendar select, pool) → teclado pierde foco.
- `:focus-visible` esencialmente ausente (index/sedes/teams: 0 reglas).
- `prefers-reduced-motion` honrado **solo en index**; calendar/pool/sedes/teams lo ignoran (regresión vestibular).
- Contraste glass dudoso (`--muted:rgba(255,255,255,.66)` sobre glass) — borderline WCAG AA; badges `#7a5e00` dark-on-dark en calendar/match (WCAG fail, copy-paste de tema claro, A3).
- Pins SVG de sedes clicables pero sin teclado/`role`/`tabindex`.
- Emoji decorativos sin `aria-hidden` → lectores anuncian "trophy join the pool".

### 4.8 Deuda técnica / higiene de repo
- **Monolito `pool.html`** 199 KB / 3.777 líneas (≈1.900 style + 530 i18n + 1.900 JS), sin build step, intesteable (A2).
- **Basura de ficheros backup en el directorio de deploy** (A1, A6): `index.html.{editorial,landing-3d,landing-static}-backup`, `calendar.html.light-backup`, `pool.html.light-backup` (157 KB!). ~315 KB de fuente muerta, **públicamente fetchable** en GitHub Pages. `pool.html.light-backup` probablemente filtra anon key / esquema Supabase viejo en una URL adivinable. Esto es control de versiones hecho con sufijos en el filesystem.
- **`_design-directions.html`** scratch en producción.
- **`aggregates.json`** parece huérfano (49 team JSONs vs 48 en index; no usado en las 7 páginas de contenido) (A4).
- **Offline real pobre**: SW network-first sin precache del shell; todo depende de fetch a `data/` + APIs externas (A1).

### 4.9 Backbone analítico — infrautilizado / sobre-confiado (A5)
- **Elo computado pero muerto**: 345 ratings + ordered-logit (s/τ) se ajustan y serializan en `ratings.json`, pero **ningún HTML los lee** (grep cero `R.elo`). El report los prescribía como *coverage layer* para pairings TBD ("Brasil vs 2º Grupo F"). Cómputo desperdiciado + gap funcional.
- **`rps_major` (0.164) y `backtest_major` no se muestran**: el número WC-relevante existe en el JSON; la web enseña solo el RPS overall (0.169), diluido por mismatches fáciles.
- **Mercados derivados sobre-confiados**: BTTS/Over2.5/CS/scoreline (outputs "blandos" de nivel-gol) se muestran con el mismo peso visual que el 1X2; disclaimer textual, no jerárquico.
- **`fitSupremacy` re-deriva λ desde el 1X2 blendeado** → el scoreline post-blend ya no es de nivel-gol puro DC (rompe sutilmente "λ vienen de los datos").
- **MAXG=8 runtime vs 10 fitter** — truncamiento inconsistente cliente/offline.
- **Monte Carlo sub-disperso**: trata atk/def como puntos fijos, no propaga la posterior → prob. de campeón demasiado confiadas.

### 4.10 Cobertura de contenido (A4)
- **Body-map de lesiones del jugador a medio llenar**: solo **453/1.099 jugadores (41%)** tienen datos de lesión; el feature estrella de `player.html` renderiza vacío para ~59%.
- **147/1.246 slots de plantilla (12%) sin `pid`** → cards no clicables.
- `current_club` ausente en 12%; historial de club ausente en 39 jugadores.
- **`news.json` snapshot estático de 2026-06-11**, 9 días viejo, mostrado bajo subtítulo "en vivo" si fallan los proxies → honestidad.
- **`player.html` no adopta `theme.css`** (CSS inline + `flagByNat` hardcodeado de ~13 nacionalidades → jugadores fuera de la lista sin bandera).

---

## 5. QUÉ PRESERVAR / REFACTORIZAR / REEMPLAZAR

### PRESERVAR (los activos diferenciales — no tocar la lógica)
- **Backbone Dixon-Coles + backtest sin fuga + live self-test congelado** (`ratings_baseline.json` separado del operativo). La mejor pieza del sitio; integridad estadística real (A5, A3, A6 concuerdan).
- **`match.html` como centro de partido profundo** — heatmap de scorelines, 1X2, eventos/comentario/stats/alineaciones live desde ESPN, XI predicho pre-match. Justifica el pipeline de datos.
- **Monte Carlo con semilla fija + report-card de calibración** en `teams.html` (forecast determinista, diagrama de fiabilidad SVG).
- **Scoring de la quiniela a 201 pts** verificado, con checklist de submit en vivo, recuperación cross-device, comparador side-by-side, modelo como concursante fantasma 🤖. Ingeniería sólida.
- **`nav.js` bottom-tab + glass topbar** (app-grade, safe-area-inset) y **`search.js`** (accent-insensitive, teclado).
- **Globo Three.js** del index — manejado bien (importmap, reduced-motion, downscale móvil, pause-on-visibilitychange, try/catch).
- **Contenido rico ya poblado**: 16/16 estadios, 48/48 coaches/dorsales/XI probable/FIFA rank, SVG country-maps de sedes.
- **PWA plumbing** (manifest, SW, iconos maskable).
- **i18n EN/ES/TR** y la cobertura trilingüe de todas las páginas.

### REFACTORIZAR (consolidar, no reescribir)
- **Extraer un único `assets/standings.js`** (fetch ESPN + normalizador + builder de tabla) y un **`assets/model.js`** (λ DC, Poisson, sim) consumidos por las 3 páginas → mata el "keep in sync" y los alias-maps divergidos. Diferenciar por *profundidad*, no por re-implementación.
- **Unificar las 3 resoluciones de bracket/terceros** en una función pura compartida (la lógica más difícil de depurar en vivo).
- **Unificar los alias-maps de nombres** en un módulo único (`team.html`/`teams.html`/cluster).
- **Migrar index/calendar/pool a `theme.css`**, borrar sus `:root` fork, colapsar `--primary`→`--gold` etc. → arregla de un golpe el flicker tipográfico, las `var(--mono/--disp)` rotas y el drift de anchura. Migrar también `player.html`.
- **Una sola clave de localStorage** para idioma; quitar el dual-read.
- **Normalizar ambos lados de `computeScore`** (`lbnorm` o claves por código de país) — corrige bug latente de puntos.
- **Centralizar i18n** (un `i18n.json`) en vez de diccionario inline por página.
- **Trocear el monolito `pool.html`** (extraer `app.js`/`styles.css`/i18n + motor scoring/bracket testeable) — *solo si hay vida más allá de 2026*.
- **Datos de bracket** (`R32_SPEC`/`GROUPS`) a fuente única compartida pool/admin.

### REEMPLAZAR (sustituir el enfoque, no parchear)
- **Modelo de seguridad de escrituras sensibles**: sacar `official_results` write y `users` delete de la anon key → Edge Function con secreto server-side (o policy con JWT). Único cambio que evita sabotaje si se publica.
- **Estados loading/error**: sustituir "Cargando…"/`innerHTML=''` por skeletons + mensaje de error con reintento en cada `catch`.
- **Sub-vista "Clasificación" de `calendar.html`**: o eliminarla apuntando a `teams.html`, o igualarla (misma tabla, mismas columnas de forecast).
- **Tab "Bracket" estática de `match.html`** en partidos KO: reemplazar el placeholder por la lógica de bracket ya existente en calendar/teams.
- **`.reveal` muerto**: o cablear el IntersectionObserver, o borrar el CSS.
- **Backups y `_design-directions.html`**: purgar del árbol de deploy (git, no sufijos).
- **`flagByNat` hardcodeado de player.html**: reemplazar por la bandera del equipo desde `index.json`/`search_index.json` que ya carga.

---

## LISTA PRIORIZADA DE OPORTUNIDADES (puente a PHASE 2)

**P0 — Alto impacto, riesgo activo**
1. **Seguridad Supabase**: mover `official_results` write y `users` delete fuera de la anon key (Edge Function / JWT). Sin esto, publicar la app = leaderboard saboteable en 30 s. *(A2)*
2. **Purgar backups del deploy** — `pool.html.light-backup` (157 KB) probablemente filtra anon key/esquema en URL pública adivinable; ~315 KB de fuente muerta servida. *(A1, A6)*
3. **De-duplicar el motor de clasificación** en `assets/standings.js` + unificar alias-maps — el drift Bosnia/Costa de Marfil/Cabo Verde es un bug de correctness ya presente, no hipotético. *(A3)*

**P1 — Alto impacto, corrección/IA**
4. **Surface News y Datos en la nav global** (o bajo "Más") — recupera dos features completas hoy semi-ocultas. *(A1, A4)*
5. **Resolver las "tres clasificaciones"**: una sola tabla/engine, diferenciada por profundidad; elimina la incoherencia de ver dos "Clasificación" distintas. *(A3)*
6. **Normalizar `computeScore`** y **arreglar el bug de clave `results.json`** en calendar (`m.num` vs índice) — dos bugs latentes de puntos/resultados. *(A2, A3)*
7. **Una sola clave de idioma** + **toggle de idioma en todas las páginas** — quita el bug `wc26-lang`/`wc2026-lang` y la fricción de idioma atrapado. *(A1, A6)*

**P2 — Impacto medio, coherencia y confianza**
8. **Migrar index/calendar/pool/player a `theme.css`** — un solo design system; arregla flicker tipográfico, `var(--mono/--disp)` rotas, drift de anchura. *(A6, A3)*
9. **Diseñar estados loading (skeleton) y error (mensaje + reintento)** en todos los fetch; loguear los `catch` vacíos de ESPN/ratings a la tabla `errors`. *(A6, A2, A5)*
10. **Activar el Elo coverage layer** y **mostrar `rps_major`/backtest del slice torneo** — cómputo ya hecho, gap funcional + el número honesto WC-relevante oculto. *(A5)*
11. **Unificar las 3 resoluciones de bracket/terceros** en una función pura. *(A2, A3)*

**P3 — Pulido, accesibilidad y contenido**
12. **Pase de accesibilidad**: `:focus-visible` site-wide, `prefers-reduced-motion` global, `aria-hidden` en emoji, pins SVG operables por teclado, contraste de badges `#7a5e00`. *(A6, A3)*
13. **Jerarquía visual de la confianza del modelo**: degradar BTTS/Over2.5/scoreline frente al 1X2; banda de incertidumbre en prob. de campeón. *(A5)*
14. **Cobertura de contenido**: lesiones de los ~646 jugadores faltantes (feature estrella al 41%), `pid` de los 147 slots, banderas de jugador por equipo, honestidad del `news.json` de fallback. *(A4)*
15. **Cross-linking sedes → partidos** y **`.reveal` muerto** (cablear o borrar). *(A3, A4, A6)*
16. **Trocear el monolito `pool.html`** con tests al motor scoring/bracket — *solo si el proyecto vive más allá de 2026.* *(A2)*

---

**Notas de incertidumbre.** [INCIERTO] estado pre-torneo real de `results.json` (A3 lo ve `{}`, enmascarado por ESPN live). [INCIERTO] si los backups están efectivamente commiteados+desplegados o solo en filesystem local (A6 pide confirmarlo). [INCIERTO] si `pool.html.light-backup` filtra la anon key actual o una vieja. [INCIERTO] no se auditó `_design-directions.html` por contenido. Ninguna auditoría reportó un grid de features "activo/próximamente": A1 confirma que no existe (claves i18n huérfanas de un bloque "Explora" eliminado); todo lo enlazado está activo.