# 3. India: luces, humo y fuego
Llanura Indo-Gangética. Las luces crecen, el aire se espesa, y cada otoño la quema de rastrojos dispara la disonancia.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (8)
- `aod_india_igp.csv` (solo por correlación en bruto) — dimensionless · 2001-01 → 2025-12 · 300 valores · textura (cuerdas con sordina / ruido filtrado) · NASA POWER mensual (AOD_55), media de 5 puntos
- `fires_punjab.csv` (solo por correlación en bruto) — detecciones/mes · 2001-01 → 2025-12 · 300 valores · percusión (timbales / redoble) · NASA FIRMS MODIS C6.1 (India, conf≥30, tipo 0)
- `lights_delhi_ncr.csv` — índice (1992 = 100) · 1992 → 2024 · 33 valores · pedal (contrabajo) · Li et al. NTL armonizado DMSP/VIIRS 1992–2024 (figshare 9828827)
- `lights_india_igp.csv` — índice (1992 = 100) · 1992 → 2024 · 33 valores · pedal (contrabajo) · Li et al. NTL armonizado DMSP/VIIRS 1992–2024 (figshare 9828827)
- `precip_india_igp.csv` — mm/day · 1981-01 → 2025-12 · 540 valores · ritmo (marimba / pizzicato) · NASA POWER mensual (PRECTOTCORR), media de 5 puntos
- `solar_india_igp.csv` — MJ/m^2/day · 1984-01 → 2025-12 · 504 valores · armonía (trompa) · NASA POWER mensual (ALLSKY_SFC_SW_DWN), media de 5 puntos
- `temp_india_igp.csv` — C · 1981-01 → 2025-12 · 540 valores · melodía (violines) · NASA POWER mensual (T2M), media de 5 puntos
- `wind_india_igp.csv` (solo por correlación en bruto) — m/s · 1981-01 → 2025-12 · 540 valores · textura (arpa / viento) · NASA POWER mensual (WS10M), media de 5 puntos

## Pares con |r| ≥ 0.5 (4)
- lights_india_igp ↔ lights_delhi_ncr: r = +0.87 (anual); en bruto 0.996
- precip_india_igp ↔ temp_india_igp: r = -0.58 (anual); en bruto -0.615
- precip_india_igp ↔ solar_india_igp: r = -0.55 (mensual); en bruto 0.216
- precip_india_igp ↔ solar_india_igp: r = -0.52 (anual); en bruto -0.652

## Disruptores puntuales y cambios de rumbo (8)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 8 de 90 comparaciones lo superan; por azar se esperarían ~4. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Quema extrema de rastrojos 2007 (2007-10) → precip_india_igp: cambio de tendencia (de subir a bajar); +1.01 → -1.71 mm/day por década
- Quema extrema de rastrojos 2014 (2014-11) → solar_india_igp: aceleración (arranca una tendencia); +0.449 → -1.86 MJ/m^2/day por década
- Crisis de humo de Delhi (2016-10) → temp_india_igp: cambio de tendencia (de subir a bajar); +2.54 → -2.67 C por década
- Crisis de humo de Delhi (2016-10) → fires_punjab: cambio de tendencia (de bajar a subir); -1.23e+03 → +1.27e+03 detecciones/mes por década
- Emergencia de aire Delhi (2017-11) → aod_india_igp: cambio de tendencia (de subir a bajar); +0.177 → -0.101 dimensionless por década
- COVID-19: confinamientos globales (2020-03) → fires_punjab: aceleración (arranca una tendencia); -425 → -3.51e+03 detecciones/mes por década
- Quema extrema de rastrojos 2020 (2020-11) → temp_india_igp: freno (la tendencia se detiene); -4.06 → +0.541 C por década
- Ola de calor India-Pakistán (2022-03) → fires_punjab: cambio de tendencia (de subir a bajar); +1.27e+03 → -3.15e+03 detecciones/mes por década

## Pares que solo superan 0.5 en bruto (15)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.

## Sin datos en esta extracción
pm25_delhi, no2_delhi
