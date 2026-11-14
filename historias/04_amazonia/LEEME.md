# 4. Amazonía: bosque, lluvia y fuego
Arco de deforestación (Rondônia–Mato Grosso–Pará). Donde avanza la frontera, la estación seca se alarga y el fuego entra en un bosque que no evolucionó con él.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (8)
- `aod_amazon_arc.csv` — dimensionless · 2001-01 → 2025-12 · 300 valores · textura (cuerdas con sordina / ruido filtrado) · NASA POWER mensual (AOD_55), media de 4 puntos
- `evap_amazon_arc.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · armonía (fagot) · NASA POWER mensual (EVLAND), media de 4 puntos
- `fires_amazon_arc.csv` — detecciones/mes · 2001-01 → 2025-12 · 300 valores · percusión (timbales / redoble) · NASA FIRMS MODIS C6.1 (Brazil, conf≥30, tipo 0)
- `gbif_aves_amazon_arc.csv` (solo por correlación en bruto) — registros/año · 1980 → 2025 · 45 valores · ornamento (flautín (canto de aves)) · GBIF (observaciones humanas; sesgo de esfuerzo, NO abundancia)
- `lights_amazon_arc.csv` — índice (1992 = 100) · 1992 → 2024 · 33 valores · pedal (contrabajo) · Li et al. NTL armonizado DMSP/VIIRS 1992–2024 (figshare 9828827)
- `precip_amazon_arc.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 4 puntos
- `soil_root_amazon_arc.csv` — 1 · 1981-01 → 2025-12 · 540 valores · armonía (violonchelos) · NASA POWER mensual (GWETROOT), media de 4 puntos
- `tmax_amazon_arc.csv` — C · 1981-01 → 2025-12 · 540 valores · melodía (violines) · NASA POWER mensual (T2M_MAX), media de 4 puntos

## Pares con |r| ≥ 0.5 (14)
- fires_amazon_arc ↔ aod_amazon_arc: r = +0.86 (anual); en bruto 0.873
- precip_amazon_arc ↔ soil_root_amazon_arc: r = +0.82 (anual); en bruto 0.912
- soil_root_amazon_arc ↔ tmax_amazon_arc: r = -0.81 (anual); en bruto -0.933
- precip_amazon_arc ↔ evap_amazon_arc: r = +0.78 (anual); en bruto 0.904
- soil_root_amazon_arc ↔ evap_amazon_arc: r = +0.73 (anual); en bruto 0.878
- tmax_amazon_arc ↔ evap_amazon_arc: r = -0.63 (anual); en bruto -0.878
- precip_amazon_arc ↔ tmax_amazon_arc: r = -0.59 (anual); en bruto -0.857
- tmax_amazon_arc ↔ evap_amazon_arc: r = -0.58 (mensual); en bruto -0.75
- precip_amazon_arc ↔ soil_root_amazon_arc: r = +0.58 (mensual, desfase +1 m); en bruto 0.613
- aod_amazon_arc ↔ lights_amazon_arc: r = +0.57 (anual); en bruto -0.27
- soil_root_amazon_arc ↔ tmax_amazon_arc: r = -0.56 (mensual); en bruto -0.93
- fires_amazon_arc ↔ aod_amazon_arc: r = +0.53 (mensual); en bruto 0.17
- fires_amazon_arc ↔ lights_amazon_arc: r = +0.52 (anual); en bruto -0.152
- soil_root_amazon_arc ↔ aod_amazon_arc: r = -0.51 (anual); en bruto -0.114

## Disruptores puntuales y cambios de rumbo (11)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 11 de 138 comparaciones lo superan; por azar se esperarían ~7. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Temporada de fuego extrema 2006 (2006-09) → fires_amazon_arc: cambio de tendencia (de subir a bajar); +2.25e+04 → -2.08e+04 detecciones/mes por década
- Sequía amazónica 2010 (2010-06) → evap_amazon_arc: cambio de tendencia (de subir a bajar); +1.33 → -1.81 mm/day por década
- Sequía amazónica 2010 (2010-06) → tmax_amazon_arc: cambio de tendencia (de bajar a subir); -3.46 → +6.53 C por década
- Déficit de lluvia 2014 (2014-04) → precip_amazon_arc: cambio de tendencia (de bajar a subir); -1.87 → +3.7 mm/day por década
- Fuego en la Amazonía central 2018 (2018-10) → precip_amazon_arc: cambio de tendencia (de subir a bajar); +3.76 → -3.36 mm/day por década
- Fuego en la Amazonía central 2018 (2018-10) → evap_amazon_arc: cambio de tendencia (de subir a bajar); +1.37 → -2.01 mm/day por década
- Fuego en la Amazonía central 2018 (2018-10) → soil_root_amazon_arc: cambio de tendencia (de subir a bajar); +0.123 → -0.135 1 por década
- Crisis de incendios 2019 (2019-08) → tmax_amazon_arc: cambio de tendencia (de bajar a subir); -4.29 → +8.75 C por década
- Crisis de incendios 2019 (2019-08) → evap_amazon_arc: cambio de tendencia (de subir a bajar); +1.72 → -2.4 mm/day por década
- Crisis de incendios 2019 (2019-08) → precip_amazon_arc: cambio de tendencia (de subir a bajar); +3.34 → -3.08 mm/day por década
- Crisis de incendios 2019 (2019-08) → soil_root_amazon_arc: cambio de tendencia (de subir a bajar); +0.139 → -0.171 1 por década

## Voces que no llegan a 0,5 con ninguna otra, ni en bruto ni en secundario (no incluidas)
`ndvi_amazon_arc`, `oni`

## Pares que solo superan 0.5 en bruto (15)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.

## Sin datos en esta extracción
ndvi_amazon_core
