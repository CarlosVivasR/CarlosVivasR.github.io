# PHASE 4 — Arquitectura de información y estructura · WC2026 Pool

Anclado a las decisiones: vida útil incierta (sin refactor profundo) · retención = duelo tú-vs-modelo (cero código) · Datos/News **bajo "Explora"**.

## 1. Modelo de navegación — 4 intenciones + acceso al modelo

La nav deja de ser un "mapa de ficheros" y pasa a 4 intenciones del usuario, + el model card:

```
Inicio · Quiniela · Partidos · Clasificación · Modelo · Explora ▾
                                                         ├ Datos
                                                         ├ Sedes
                                                         ├ Plantillas
                                                         └ Noticias
```

- **Desktop**: barra superior con las 5 primarias + "Modelo" + dropdown "Explora". *(Hecho parcial: `modelo` ya añadido topOnly; el dropdown "Explora" agrupando Datos/Sedes/Plantillas/Noticias queda como paso siguiente — hoy Sedes/Plantillas son top-level y Datos/Noticias huérfanas.)*
- **Móvil**: 5 tabs inferiores (Inicio/Quiniela/Partidos/Clasificación/**Más**▾) → "Más" abre un sheet con Modelo·Datos·Sedes·Plantillas·Noticias. *(Hoy 6 tabs; consolidar a 5+Más.)*
- **Idioma**: toggle global en todas las páginas. ✅ **hecho** (era Home-only).
- `<html lang>` debe seguir al idioma activo (pendiente, ligado a clave unificada ✅).

## 2. Roles de página (mantener / fusionar / recortar)

| Página | Rol en la IA | Acción |
|---|---|---|
| `index.html` | **Portal**: pulso del torneo (match spotlight live) + accesos + el duelo del día | mantener; quitar countdown muerto |
| `pool.html` | **Quiniela** + leaderboard + comparador + 🤖 duelo acumulado | mantener; tejer narrativa del duelo |
| `calendar.html` | **Partidos**: fixtures (3 vistas). Su sub-vista "Clasificación" → **eliminar/redirigir** a teams | mantener fixtures; quitar la clasif. degradada |
| `match.html` | **Centro de partido** (el destino profundo): predicción + duelo + brief (Datos/News contextuales) | mantener; es donde converge todo |
| `teams.html` | **Clasificación ÚNICA** + forecast Monte Carlo | mantener; es la fuente canónica de standings |
| `modelo.html` | **Model card** (honestidad del modelo) | ✅ creado |
| `sedes.html` `plantillas.html` `team.html` `player.html` | **Explora / fichas** (referencia) | mantener bajo Explora; cross-link sedes↔partidos |
| `datos.html` `news.html` | **Explora** (rankings, noticias) | mantener bajo Explora + alimentar el brief de match.html |
| `admin.html` | backoffice (Auth) | ✅ fuera de nav, login |
| `_design-directions.html` | scratch | purgar del deploy |

**Una pregunta → un destino canónico.** "Clasificación" vive solo en `teams.html`; calendar/match enlazan o reusan ese mismo componente, nunca una tabla degradada.

## 3. Los tres journeys mapeados

- **A · "Compito" (quiniela):** Inicio → Quiniela → leaderboard → comparador (tú vs amigo vs 🤖). Cierre del loop: tras puntuar, "¿cómo le fue al modelo?" → match.html / modelo.html.
- **B · "Exploro el modelo":** Inicio → Modelo (model card, ✅) → Clasificación (forecast con banda) → Partido (predicción + atribución). El report-card es **destino**, no módulo enterrado.
- **C · "Sigo un partido en vivo":** Inicio (spotlight) → Partido. Tres estados explícitos pre/live/post; fallo de ESPN = estado con reintento, no void.

## 4. Jerarquía de contenido por página (overview → filtros → resultados → profundidad)

- **Inicio**: pulso (live/próximo) → el duelo del día (tú vs 🤖) → accesos (Quiniela/Modelo/Partidos) → self-test del modelo.
- **Partido (`match.html`)**: marcador/estado → predicción 1X2 (**héroe**) → mercados derivados (degradados, "menos fiables") → atribución (waterfall) → brief (datos+news del partido) → alineaciones/eventos.
- **Clasificación (`teams.html`)**: tabla por grupo → forecast (prob. de pase **con banda**) → report-card de calibración.
- **Modelo (`modelo.html`)** ✅: RPS honesto (héroe) → calibración (reliability) → cómo funciona → lo que NO es → tres incertidumbres.

## 5. Qué se fusiona / recorta

- **Fusionar**: Datos+News como contexto en el brief de `match.html` (además de existir bajo Explora — decisión: conservarlas).
- **Una sola clasificación** (las 3 colapsan a teams).
- **Recortar**: countdown muerto, sub-vista clasificación de calendar, `_design-directions.html`, body-map de lesiones al 41% (ocultar hasta llenar), estado post-torneo tras 19-jul.

---

*Estado a 20-jun:* nav con `modelo` (desktop) ✅, toggle de idioma global ✅, clave de idioma unificada ✅. Pendientes de mayor calado (dropdown Explora, 5+Más móvil, una-sola-clasificación vía `standings.js`, el duelo tejido) → implementación incremental con verificación, según la prioridad del plan.
