# 8. Borneo y Sumatra: turba, humo y El Niño
Borneo y Sumatra. Cada El Niño seca las turberas drenadas; el fuego las convierte en humo que cruza fronteras.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (6)
- `aod_borneo_sumatra.csv` — dimensionless · 2001-01 → 2025-12 · 300 valores · textura (cuerdas con sordina / ruido filtrado) · NASA POWER mensual (AOD_55), media de 4 puntos
- `fires_borneo_sumatra.csv` — detecciones/mes · 2001-01 → 2025-12 · 300 valores · percusión (timbales / redoble) · NASA FIRMS MODIS C6.1 (Indonesia, conf≥30, tipo 0)
- `lights_borneo_sumatra.csv` (solo por correlación en bruto) — índice (1992 = 100) · 1992 → 2024 · 33 valores · pedal (contrabajo) · Li et al. NTL armonizado DMSP/VIIRS 1992–2024 (figshare 9828827)
- `oni.csv` — degC · 1979-01 → 2026-09 · 573 valores · director (metales (trompas)) · NOAA CPC ONI (ERSSTv5)
- `precip_borneo_sumatra.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 4 puntos
- `soil_top_borneo_sumatra.csv` — 1 · 1981-01 → 2025-12 · 540 valores · armonía (violonchelos) · NASA POWER mensual (GWETTOP), media de 4 puntos

## Pares con |r| ≥ 0.5 (15)
- fires_borneo_sumatra ↔ aod_borneo_sumatra: r = +0.85 (anual); en bruto 0.774
- precip_borneo_sumatra ↔ soil_top_borneo_sumatra: r = +0.84 (anual); en bruto 0.911
- fires_borneo_sumatra ↔ aod_borneo_sumatra: r = +0.73 (mensual); en bruto 0.221
- precip_borneo_sumatra ↔ fires_borneo_sumatra: r = -0.73 (anual); en bruto -0.793
- precip_borneo_sumatra ↔ aod_borneo_sumatra: r = -0.68 (anual); en bruto -0.612
- soil_top_borneo_sumatra ↔ fires_borneo_sumatra: r = -0.65 (anual); en bruto -0.736
- soil_top_borneo_sumatra ↔ aod_borneo_sumatra: r = -0.62 (anual); en bruto -0.629
- oni ↔ fires_borneo_sumatra: r = +0.60 (anual); en bruto 0.525
- precip_borneo_sumatra ↔ soil_top_borneo_sumatra: r = +0.59 (mensual, desfase +1 m); en bruto 0.574
- oni ↔ soil_top_borneo_sumatra: r = -0.59 (anual); en bruto -0.453
- soil_top_borneo_sumatra ↔ fires_borneo_sumatra: r = -0.57 (mensual, desfase -1 m); en bruto -0.625
- soil_top_borneo_sumatra ↔ aod_borneo_sumatra: r = -0.56 (mensual); en bruto -0.272
- oni ↔ soil_top_borneo_sumatra: r = -0.56 (mensual, desfase -2 m); en bruto -0.366
- oni ↔ aod_borneo_sumatra: r = +0.53 (anual); en bruto 0.538
- precip_borneo_sumatra ↔ fires_borneo_sumatra: r = -0.52 (mensual); en bruto -0.637

## Disruptores puntuales y cambios de rumbo (1)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 1 de 80 comparaciones lo superan; por azar se esperarían ~4. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Humo 2019 (2019-08) → solar_borneo_sumatra: cambio de tendencia (de subir a bajar); +1.55 → -1.37 MJ/m^2/day por década

Voces añadidas solo por girar tras un disruptor: `solar_borneo_sumatra.csv`

## Pares que solo superan 0.5 en bruto (2)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.

## Sin datos en esta extracción
ndvi_borneo_sumatra
