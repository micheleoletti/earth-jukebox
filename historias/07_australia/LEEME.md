# 7. Australia: Niño, sequía y Black Summer
Sureste de Australia. El Pacífico y el Índico marcan sequías de años; cuando coinciden, arde el verano.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (8)
- `aod_australia_se.csv` (solo por correlación en bruto) — dimensionless · 2001-01 → 2025-12 · 300 valores · textura (cuerdas con sordina / ruido filtrado) · NASA POWER mensual (AOD_55), media de 4 puntos
- `evap_australia_se.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · armonía (fagot) · NASA POWER mensual (EVLAND), media de 4 puntos
- `fires_australia_se.csv` — detecciones/mes · 2001-01 → 2025-12 · 300 valores · percusión (timbales / redoble) · NASA FIRMS MODIS C6.1 (Australia, conf≥30, tipo 0)
- `iod_dmi_gistemp.csv` — degC · 1979-01 → 2026-10 · 574 valores · melodía (violines) · Dipolo del Índico: caja oeste − este (rejilla NASA GISTEMP v4)
- `oni.csv` — degC · 1979-01 → 2026-09 · 573 valores · director (metales (trompas)) · NOAA CPC ONI (ERSSTv5)
- `precip_australia_se.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 4 puntos
- `soil_root_australia_se.csv` — 1 · 1981-01 → 2025-12 · 540 valores · armonía (violonchelos) · NASA POWER mensual (GWETROOT), media de 4 puntos
- `tmax_australia_se.csv` — C · 1981-01 → 2025-12 · 540 valores · melodía (violines) · NASA POWER mensual (T2M_MAX), media de 4 puntos

## Pares con |r| ≥ 0.5 (18)
- precip_australia_se ↔ soil_root_australia_se: r = +0.94 (anual); en bruto 0.957
- precip_australia_se ↔ evap_australia_se: r = +0.90 (anual); en bruto 0.913
- soil_root_australia_se ↔ evap_australia_se: r = +0.85 (anual); en bruto 0.873
- tmax_australia_se ↔ evap_australia_se: r = -0.85 (anual); en bruto -0.85
- soil_root_australia_se ↔ evap_australia_se: r = +0.84 (mensual); en bruto 0.083
- soil_root_australia_se ↔ tmax_australia_se: r = -0.76 (anual); en bruto -0.799
- precip_australia_se ↔ tmax_australia_se: r = -0.74 (anual); en bruto -0.777
- precip_australia_se ↔ soil_root_australia_se: r = +0.64 (mensual, desfase +1 m); en bruto 0.287
- precip_australia_se ↔ evap_australia_se: r = +0.62 (mensual, desfase +1 m); en bruto 0.404
- soil_root_australia_se ↔ tmax_australia_se: r = -0.61 (mensual); en bruto -0.725
- iod_dmi_gistemp ↔ evap_australia_se: r = -0.60 (anual); en bruto -0.59
- iod_dmi_gistemp ↔ precip_australia_se: r = -0.60 (anual); en bruto -0.562
- tmax_australia_se ↔ evap_australia_se: r = -0.59 (mensual); en bruto 0.549
- oni ↔ evap_australia_se: r = -0.59 (anual); en bruto -0.568
- iod_dmi_gistemp ↔ soil_root_australia_se: r = -0.56 (anual); en bruto -0.533
- tmax_australia_se ↔ fires_australia_se: r = +0.54 (anual); en bruto 0.494
- evap_australia_se ↔ fires_australia_se: r = -0.52 (anual); en bruto -0.489
- oni ↔ precip_australia_se: r = -0.52 (anual); en bruto -0.505

## Disruptores puntuales y cambios de rumbo (3)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 3 de 132 comparaciones lo superan; por azar se esperarían ~7. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Déficit de lluvia 2017 (2017-09) → iod_dmi_gistemp: aceleración (arranca una tendencia); +0.0952 → -2.15 degC por década
- Déficit de lluvia 2017 (2017-09) → soil_root_australia_se: aceleración (arranca una tendencia); -0.0761 → +0.36 1 por década
- Déficit de lluvia 2017 (2017-09) → precip_australia_se: aceleración (arranca una tendencia); -0.465 → +3.88 mm/day por década

## Pares que solo superan 0.5 en bruto (2)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.

## Sin datos en esta extracción
ndvi_australia_se
