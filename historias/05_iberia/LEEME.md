# 5. Iberia: calor, sequía y fuego
Península Ibérica. Veranos más calientes y suelos más secos preparan el escenario; el fuego entra a destiempo.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (8)
- `evap_iberia.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · armonía (fagot) · NASA POWER mensual (EVLAND), media de 6 puntos
- `fires_iberia.csv` (solo por correlación en bruto) — detecciones/mes · 2001-01 → 2025-12 · 300 valores · percusión (timbales / redoble) · NASA FIRMS MODIS C6.1 (Spain+Portugal, conf≥30, tipo 0)
- `gistemp_iberia.csv` — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · melodía (violines) · NASA GISTEMP v4 grid 2deg
- `humidity_iberia.csv` — % · 1981-01 → 2025-12 · 540 valores · armonía (clarinete) · NASA POWER mensual (RH2M), media de 6 puntos
- `lights_iberia.csv` (solo por correlación en bruto) — índice (1992 = 100) · 1992 → 2024 · 33 valores · pedal (contrabajo) · Li et al. NTL armonizado DMSP/VIIRS 1992–2024 (figshare 9828827)
- `precip_iberia.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 6 puntos
- `soil_root_iberia.csv` — 1 · 1981-01 → 2025-12 · 540 valores · armonía (violonchelos) · NASA POWER mensual (GWETROOT), media de 6 puntos
- `tmax_iberia.csv` — C · 1981-01 → 2025-12 · 540 valores · melodía (violines) · NASA POWER mensual (T2M_MAX), media de 6 puntos

## Pares con |r| ≥ 0.5 (16)
- soil_root_iberia ↔ evap_iberia: r = +0.96 (anual); en bruto 0.944
- evap_iberia ↔ humidity_iberia: r = +0.85 (anual); en bruto 0.848
- soil_root_iberia ↔ humidity_iberia: r = +0.82 (anual); en bruto 0.815
- soil_root_iberia ↔ evap_iberia: r = +0.81 (mensual); en bruto 0.381
- soil_root_iberia ↔ humidity_iberia: r = +0.73 (mensual); en bruto 0.802
- precip_iberia ↔ humidity_iberia: r = +0.68 (anual); en bruto 0.697
- evap_iberia ↔ humidity_iberia: r = +0.68 (mensual, desfase -1 m); en bruto -0.112
- precip_iberia ↔ humidity_iberia: r = +0.68 (mensual); en bruto 0.695
- tmax_iberia ↔ humidity_iberia: r = -0.61 (anual); en bruto -0.444
- precip_iberia ↔ soil_root_iberia: r = +0.60 (mensual, desfase +1 m); en bruto 0.538
- tmax_iberia ↔ gistemp_iberia: r = +0.59 (anual); en bruto 0.696
- tmax_iberia ↔ gistemp_iberia: r = +0.57 (mensual); en bruto 0.301
- tmax_iberia ↔ humidity_iberia: r = -0.52 (mensual); en bruto -0.934
- precip_iberia ↔ evap_iberia: r = +0.52 (anual); en bruto 0.514
- precip_iberia ↔ evap_iberia: r = +0.50 (mensual, desfase +1 m); en bruto 0.12
- precip_iberia ↔ soil_root_iberia: r = +0.50 (anual); en bruto 0.498

## Disruptores puntuales y cambios de rumbo (2)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 2 de 139 comparaciones lo superan; por azar se esperarían ~7. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Mes de calor extremo 1988 (1988-09) → gistemp_iberia: cambio de tendencia (de subir a bajar); +1.09 → -2.81 degC anomaly 1951-1980 por década
- Verano extremo 2022 (2022-06) → fires_iberia: aceleración (arranca una tendencia); -734 → +3.7e+03 detecciones/mes por década

## Pares que solo superan 0.5 en bruto (6)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.

## Sin datos en esta extracción
ndvi_iberia
