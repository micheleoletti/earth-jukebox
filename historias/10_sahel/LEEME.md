# 10. Sahel: la lluvia que volvió
Sahel (Senegal–Sudán). Tras la gran sequía de los 80 la lluvia regresó y la franja reverdece; una tendencia amplia, con sus disonancias.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (9)
- `aod_sahel.csv` (solo por correlación en bruto) — dimensionless · 2001-01 → 2025-12 · 300 valores · textura (cuerdas con sordina / ruido filtrado) · NASA POWER mensual (AOD_55), media de 5 puntos
- `evap_sahel.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · armonía (fagot) · NASA POWER mensual (EVLAND), media de 5 puntos
- `gbif_aves_sahel.csv` — registros/año · 1980 → 2025 · 46 valores · ornamento (flautín (canto de aves)) · GBIF (observaciones humanas; sesgo de esfuerzo, NO abundancia)
- `humidity_sahel.csv` — % · 1981-01 → 2025-12 · 540 valores · armonía (clarinete) · NASA POWER mensual (RH2M), media de 5 puntos
- `lights_sahel.csv` — índice (1992 = 100) · 1992 → 2024 · 33 valores · pedal (contrabajo) · Li et al. NTL armonizado DMSP/VIIRS 1992–2024 (figshare 9828827)
- `north_atlantic_0_60N.csv` (solo por correlación en bruto) — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · director (metales) · NASA GISTEMP v4 grid 2deg box 0,-80,60,0
- `precip_sahel.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 5 puntos
- `soil_root_sahel.csv` — 1 · 1981-01 → 2025-12 · 540 valores · armonía (violonchelos) · NASA POWER mensual (GWETROOT), media de 5 puntos
- `tmax_sahel.csv` — C · 1981-01 → 2025-12 · 540 valores · melodía (violines) · NASA POWER mensual (T2M_MAX), media de 5 puntos

## Pares con |r| ≥ 0.5 (20)
- precip_sahel ↔ soil_root_sahel: r = +0.97 (anual); en bruto 0.973
- precip_sahel ↔ evap_sahel: r = +0.94 (anual); en bruto 0.974
- evap_sahel ↔ soil_root_sahel: r = +0.94 (anual); en bruto 0.946
- soil_root_sahel ↔ humidity_sahel: r = +0.88 (anual); en bruto 0.908
- precip_sahel ↔ humidity_sahel: r = +0.88 (anual); en bruto 0.882
- evap_sahel ↔ humidity_sahel: r = +0.88 (anual); en bruto 0.9
- precip_sahel ↔ tmax_sahel: r = -0.83 (anual); en bruto -0.511
- soil_root_sahel ↔ tmax_sahel: r = -0.83 (anual); en bruto -0.441
- evap_sahel ↔ soil_root_sahel: r = +0.81 (mensual); en bruto 0.963
- soil_root_sahel ↔ humidity_sahel: r = +0.80 (mensual); en bruto 0.875
- evap_sahel ↔ humidity_sahel: r = +0.78 (mensual); en bruto 0.949
- tmax_sahel ↔ humidity_sahel: r = -0.78 (anual); en bruto -0.526
- evap_sahel ↔ tmax_sahel: r = -0.78 (anual); en bruto -0.506
- precip_sahel ↔ soil_root_sahel: r = +0.73 (mensual, desfase +1 m); en bruto 0.597
- lights_sahel ↔ gbif_aves_sahel: r = +0.71 (anual); en bruto 0.974
- soil_root_sahel ↔ tmax_sahel: r = -0.60 (mensual); en bruto -0.657
- precip_sahel ↔ humidity_sahel: r = +0.55 (mensual); en bruto 0.847
- precip_sahel ↔ evap_sahel: r = +0.54 (mensual, desfase +1 m); en bruto 0.727
- tmax_sahel ↔ humidity_sahel: r = -0.53 (mensual); en bruto -0.365
- evap_sahel ↔ tmax_sahel: r = -0.52 (mensual); en bruto -0.513

## Disruptores puntuales y cambios de rumbo (5)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 5 de 77 comparaciones lo superan; por azar se esperarían ~4. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Exceso de lluvia 1987 (1987-07) → precip_sahel: cambio de tendencia (de subir a bajar); +1.6 → -0.996 mm/day por década
- Exceso de lluvia 1987 (1987-07) → evap_sahel: cambio de tendencia (de subir a bajar); +0.918 → -0.639 mm/day por década
- Exceso de lluvia 1987 (1987-07) → soil_root_sahel: cambio de tendencia (de subir a bajar); +0.0638 → -0.0532 1 por década
- Exceso de lluvia 1988 (1988-08) → soil_root_sahel: cambio de tendencia (de subir a bajar); +0.0839 → -0.0369 1 por década
- Sequía 2011–12 (2011-06) → aod_sahel: aceleración (arranca una tendencia); -0.0459 → +0.207 dimensionless por década

## Voces que no llegan a 0,5 con ninguna otra, ni en bruto ni en secundario (no incluidas)
`oni`

## Pares que solo superan 0.5 en bruto (9)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.

## Sin datos en esta extracción
ndvi_sahel
