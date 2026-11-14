# 2. El Niño, director de orquesta
Pacífico tropical y teleconexiones. Un calentamiento del Pacífico marca el compás de lluvias y sequías en cuatro continentes.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (10)
- `fires_borneo_sumatra.csv` — detecciones/mes · 2001-01 → 2025-12 · 300 valores · percusión (timbales / redoble) · NASA FIRMS MODIS C6.1 (Indonesia, conf≥30, tipo 0)
- `nino34_gistemp.csv` — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · melodía (violines) · NASA GISTEMP v4 grid 2deg box -5,-170,5,-120
- `oni.csv` — degC · 1979-01 → 2026-09 · 573 valores · director (metales (trompas)) · NOAA CPC ONI (ERSSTv5)
- `precip_amazon_arc.csv` (solo por correlación en bruto) — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 4 puntos
- `precip_australia_se.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 4 puntos
- `precip_borneo_sumatra.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 4 puntos
- `precip_california.csv` (solo por correlación en bruto) — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 2 puntos
- `precip_india_igp.csv` (solo por correlación en bruto) — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 5 puntos
- `precip_peru_coast.csv` (solo por correlación en bruto) — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 1 puntos
- `tropics_20S_20N.csv` — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · melodía (violas) · NASA GISTEMP v4 grid 2deg box -20,-180,20,180

## Pares con |r| ≥ 0.5 (12)
- oni ↔ nino34_gistemp: r = +0.99 (mensual); en bruto 0.98
- oni ↔ nino34_gistemp: r = +0.99 (anual); en bruto 0.985
- oni ↔ tropics_20S_20N: r = +0.83 (mensual, desfase +2 m); en bruto 0.474
- nino34_gistemp ↔ tropics_20S_20N: r = +0.83 (mensual, desfase +2 m); en bruto 0.511
- precip_borneo_sumatra ↔ fires_borneo_sumatra: r = -0.73 (anual); en bruto -0.793
- oni ↔ tropics_20S_20N: r = +0.72 (anual); en bruto 0.34
- nino34_gistemp ↔ tropics_20S_20N: r = +0.72 (anual); en bruto 0.414
- nino34_gistemp ↔ fires_borneo_sumatra: r = +0.62 (anual); en bruto 0.581
- oni ↔ fires_borneo_sumatra: r = +0.60 (anual); en bruto 0.525
- nino34_gistemp ↔ precip_australia_se: r = -0.53 (anual); en bruto -0.534
- oni ↔ precip_australia_se: r = -0.52 (anual); en bruto -0.505
- precip_borneo_sumatra ↔ fires_borneo_sumatra: r = -0.52 (mensual); en bruto -0.637

## Disruptores puntuales y cambios de rumbo (2)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 2 de 65 comparaciones lo superan; por azar se esperarían ~3. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Erupción del Pinatubo (1991-06) → precip_amazon_arc: cambio de tendencia (de subir a bajar); +2.6 → -2.58 mm/day por década
- Black Summer (Australia) (2019-09) → tropics_20S_20N: cambio de tendencia (de bajar a subir); -0.388 → +1.28 degC anomaly 1951-1980 por década

## Voces que no llegan a 0,5 con ninguna otra, ni en bruto ni en secundario (no incluidas)
`precip_horn_africa`

## Pares que solo superan 0.5 en bruto (11)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.
