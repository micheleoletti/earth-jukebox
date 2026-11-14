# 6. Ártico: el hielo que se apaga
Ártico (64–90° N). El Ártico se calienta varias veces más rápido que el planeta, y el hielo marino pierde su voz de septiembre.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (6)
- `arctic_64N_90N.csv` — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · melodía (violines) · NASA GISTEMP v4 grid 2deg box 64,-180,90,180
- `co2_mlo.csv` (solo por correlación en bruto) — ppm · 1979-01 → 2026-09 · 573 valores · pedal (órgano / bajo continuo) · NOAA GML Mauna Loa
- `fires_arctic.csv` (solo por correlación en bruto) — detecciones/mes · 2001-01 → 2025-12 · 300 valores · melodía (violines) · NASA FIRMS MODIS C6.1 (Canada, conf≥30, tipo 0)
- `gistemp_global.csv` (solo por correlación en bruto) — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · melodía (violines) · NASA GISTEMP v4
- `sea_ice_extent_north.csv` — 1e6 km2 · 1979-01 → 2026-10 · 572 valores · contramelodía (flauta / celesta) · NSIDC Sea Ice Index v4
- `temp_arctic.csv` — C · 1981-01 → 2025-12 · 540 valores · melodía (violines) · NASA POWER mensual (T2M), media de 6 puntos

## Pares con |r| ≥ 0.5 (4)
- arctic_64N_90N ↔ sea_ice_extent_north: r = -0.73 (anual); en bruto -0.954
- arctic_64N_90N ↔ temp_arctic: r = +0.67 (anual); en bruto 0.886
- arctic_64N_90N ↔ temp_arctic: r = +0.65 (mensual); en bruto -0.159
- sea_ice_extent_north ↔ temp_arctic: r = -0.54 (anual); en bruto -0.847

## Disruptores puntuales y cambios de rumbo (6)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 6 de 88 comparaciones lo superan; por azar se esperarían ~4. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Mínimo anómalo de hielo 1989 (1989-04) → gistemp_global: cambio de tendencia (de subir a bajar); +0.575 → -0.51 degC anomaly 1951-1980 por década
- Mínimo anómalo de hielo 2016 (2016-10) → temp_arctic: cambio de tendencia (de subir a bajar); +2.7 → -2.08 C por década
- Incendios de Siberia 2019 (2019-06) → fires_arctic: cambio de tendencia (de bajar a subir); -5.16e+03 → +1.47e+04 detecciones/mes por década
- Ola de calor siberiana (2020-01) → gistemp_global: aceleración (arranca una tendencia); -0.0065 → +1.12 degC anomaly 1951-1980 por década
- Mínimo anómalo de hielo 2020 (2020-09) → arctic_64N_90N: cambio de tendencia (de bajar a subir); -0.784 → +2.63 degC anomaly 1951-1980 por década
- Mínimo anómalo de hielo 2020 (2020-09) → gistemp_global: aceleración (arranca una tendencia); -0.0536 → +1.02 degC anomaly 1951-1980 por década

## Pares que solo superan 0.5 en bruto (13)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.
