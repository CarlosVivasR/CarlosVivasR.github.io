# PHASE 3 — Diseño del backbone analítico · WC2026 Pool

Anclado a las decisiones de Carlos (20-jun-2026):
- **Vida útil incierta** → priorizar honestidad + bajo riesgo, sin refactor profundo. Split explícito *esencial ahora* / *futuro*.
- **Retención = duelo tú-vs-modelo (cero código)** → el modelo como rival honesto es la espina narrativa.
- **Datos/News bajo "Explora"** → fuera del core analítico.

Regla rectora (las 6 voces, unánime): **el backbone Dixon-Coles + walk-forward sin fuga + live self-test + value-tilt NO se toca. Toda mejora va por encima.**

---

## 1. Qué análisis debe realizar la app

**Núcleo (ya existe, se conserva):** Dixon-Coles 1X2 + scorelines · value-tilt (β=0.06, validado) · blend de mercado (de-vig Shin + log-opinion-pool, w=0.3) · Monte Carlo del torneo · walk-forward backtest · live self-test congelado.

**Añadidos ESENCIALES AHORA (baratos, alta honestidad, sin refactor):**
1. **Surface `rps_major` (0.164)** — el RPS del slice mundialista — como número titular, + **RPS Skill Score** (% mejora vs climatología) y comparación vs mercado. Hoy se muestra el RPS overall diluido (0.169).
2. **Calibración EN VIVO** — ECE + reliability diagram sobre los partidos del Mundial ya jugados (no solo el backtest histórico).
3. **El duelo tú-vs-modelo** — por partido: tu pick · pick del modelo · resultado · puntos; y acumulado (tú vs modelo vs media del grupo). Es la mecánica de retención y la narrativa.
4. **Activar el Elo** (ya computado, ningún HTML lo lee) como fallback en emparejamientos "TBD" ("Brasil vs 2º Grupo F").

**Añadidos IMPORTANTES (medio esfuerzo, cambian dato/modelo pero no arquitectura):**
5. **Banda de incertidumbre en la prob. de campeón** — bootstrap paramétrico / Fisher-SE de los ratings en `fit_ratings.py` → `atk_sd`/`def_sd` → samplear parámetros 1×/torneo en el Monte Carlo. El Monte Carlo hoy es sobre-confiado (trata atk/def como fijos).
6. **Panel Modelo vs Mercado vs Blend** + edge por partido.
7. **Waterfall de atribución por partido** (`μ + atk − def + host + value_tilt`) — el modelo es lineal en log-λ, así que la explicación es exacta y barata. Hace visible el value-tilt (hoy 100% invisible).

**FUTURO (gate: solo si el proyecto vive tras 2026):**
8. Reemplazar `SPREAD=1.10` ad-hoc por temperature-scaling auditable. 9. Tabla de ablation (decay/ρ/spread/blend). 10. Separar scoreline (λ DC puros) del 1X2 (blend) en `fitSupremacy`. 11. Unificar `MAXG` (8 cliente / 10 fitter).

## 2. Inputs necesarios

- **`ratings.json`** (regenerar con `fit_ratings.py`): añadir `atk_sd`/`def_sd` y `champion.{p10,p50,p90}`; **exponer** lo ya calculado pero oculto (`rps_major`, `logloss_mat`, `elo.ratings`+`s`/`tau`).
- **ESPN** (runtime, ya integrado): resultados WC → calibración en vivo + puntuación del duelo.
- **Supabase `picks`** (ya): el pick del usuario para el duelo tú-vs-modelo.
- **`ratings_baseline.json`** (snapshot pre-torneo, ya): el lado "congelado" del self-test.

## 3. Outputs a mostrar

| Output | Dónde | Esencial |
|---|---|---|
| Métrica honesta titular (`rps_major` + skill vs mercado) | model card / teams.html | ✅ ahora |
| Prob. de campeón **con banda** | teams.html | importante |
| Por partido: 1X2 (héroe) + mercados derivados (degradados) + modelo-vs-mercado + atribución | match.html | mixto |
| **Duelo** por partido + acumulado (tú/modelo/grupo) | match.html + pool.html | ✅ ahora |
| Calibración en vivo (reliability backtest+WC superpuestos) | model card | ✅ ahora |
| Model card (honestidad consolidada) | `modelo.html` nuevo | ✅ ahora |

## 4. Charts / tablas / interpretaciones más útiles

- **Prob. de campeón con banda** (percentiles, no barras puntuales).
- **Reliability diagram** (backtest frío + WC caliente superpuestos) como héroe visual.
- **Scatter modelo-vs-mercado** (dónde el modelo discrepa del mercado → las "apuestas de valor").
- **Waterfall de atribución** por partido.
- **Tracker de RPS acumulado** (modelo vs mercado vs climatología a lo largo del torneo).
- **Marcador del duelo** (tú vs 🤖).
- Lenguaje editorial (538): título+subtítulo de lectura, color **solo semántico** (win/draw=gris/loss), cifras en **mono tabular**, sin arcoíris, gridlines finos. *(detalle visual → PHASE 4)*

## 5. Comunicación de incertidumbre (el núcleo del diseño)

**Tres niveles, nombrados y SEPARADOS** — hoy se mezclan bajo "confianza":
- **(A) Aleatoria / del partido** = entropía del marcador. Ya existe (badge ⚖️). "Partido parejo".
- **(B) Calibración del modelo** = ECE 0.0287. Existe, **oculta**. "Cuando digo 60%, ¿pasa el 60%?".
- **(C) Paramétrica / epistémica** = incertidumbre de los ratings. **No propagada** → la cierra el bootstrap (#5). "Cuánto sé que sé".

Principios (con evidencia, del research):
- **Número para el forecast, palabra para el consejo/lectura.** ("65%", no "probable").
- **Ninguna viz captura toda la incertidumbre** → usar un *conjunto* de gráficos, no un único "índice de confianza".
- **Jerarquía de fiabilidad = peso visual**: 1X2 grande/héroe; BTTS/Over/CS/scoreline pequeños bajo "Mercados derivados (menos fiables)" + chip. No un disclaimer textual.
- **Un número sin su incertidumbre es tergiversación** — banda en la prob. de campeón es obligatoria, no opcional.
- **El model card** (`modelo.html`) como artefacto único de honestidad: qué hace · cómo funciona · rendimiento validado (`rps_major` titular) · out-of-scope / fallos conocidos · fecha. Consolida los disclaimers hoy dispersos en 3 páginas.

## 6. Esencial ahora vs futuro (gate: vida útil incierta)

- **AHORA** (alto impacto, bajo riesgo, sin refactor): `rps_major` titular · calibración en vivo · **el duelo** · activar Elo · jerarquía de confianza (degradar mercados blandos) · model card. → *quick wins de honestidad.*
- **PRONTO** (medio; cambia dato/modelo, no arquitectura): banda de campeón (bootstrap) · panel modelo/mercado · waterfall de atribución.
- **FUTURO** (gate 2026): temperature-scaling · ablation · fix `fitSupremacy` · `MAXG`.

---

*Puente a PHASE 4:* la presentación de todo esto (model card como destino, jerarquía de confianza, lenguaje de charts, el duelo en match.html y pool.html) entra en la arquitectura de información y el rediseño visual.
