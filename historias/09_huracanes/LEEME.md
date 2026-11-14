# 9. Atlántico: mar caliente, huracanes fuertes
Atlántico tropical. El mar pone la energía y El Niño la frena: la temporada es un pulso entre dos océanos.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (6)
- `ace_north_atlantic.csv` — 1e4 kt2 · 1980-01 → 2025-12 · 552 valores · director (metales) · NOAA IBTrACS v04r01 (USA_WIND, 6 h)
- `atlantic_mdr_sst.csv` — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · director (metales) · NASA GISTEMP v4 grid 2deg box 10,-80,20,-20
- `gistemp_global.csv` — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · melodía (violines) · NASA GISTEMP v4
- `north_atlantic_0_60N.csv` — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · director (metales) · NASA GISTEMP v4 grid 2deg box 0,-80,60,0
- `skin_temp_atlantic_mdr.csv` — C · 1981-01 → 2025-12 · 540 valores · melodía (violines) · NASA POWER mensual (TS), media de 3 puntos
- `wind_atlantic_mdr.csv` — m/s · 1981-01 → 2025-12 · 540 valores · director (metales) · NASA POWER mensual (WS10M), media de 3 puntos

## Pares con |r| ≥ 0.5 (14)
- atlantic_mdr_sst ↔ skin_temp_atlantic_mdr: r = +0.93 (anual); en bruto 0.945
- atlantic_mdr_sst ↔ skin_temp_atlantic_mdr: r = +0.91 (mensual); en bruto 0.549
- atlantic_mdr_sst ↔ north_atlantic_0_60N: r = +0.86 (anual); en bruto 0.9
- north_atlantic_0_60N ↔ skin_temp_atlantic_mdr: r = +0.79 (anual); en bruto 0.849
- north_atlantic_0_60N ↔ wind_atlantic_mdr: r = -0.74 (anual); en bruto -0.537
- atlantic_mdr_sst ↔ north_atlantic_0_60N: r = +0.73 (mensual); en bruto 0.829
- atlantic_mdr_sst ↔ wind_atlantic_mdr: r = -0.72 (anual); en bruto -0.68
- skin_temp_atlantic_mdr ↔ wind_atlantic_mdr: r = -0.70 (anual); en bruto -0.666
- north_atlantic_0_60N ↔ skin_temp_atlantic_mdr: r = +0.65 (mensual); en bruto 0.42
- north_atlantic_0_60N ↔ gistemp_global: r = +0.64 (anual); en bruto 0.935
- atlantic_mdr_sst ↔ gistemp_global: r = +0.57 (anual); en bruto 0.805
- atlantic_mdr_sst ↔ wind_atlantic_mdr: r = -0.53 (mensual, desfase -1 m); en bruto -0.392
- skin_temp_atlantic_mdr ↔ wind_atlantic_mdr: r = -0.51 (mensual, desfase -1 m); en bruto -0.7
- ace_north_atlantic ↔ north_atlantic_0_60N: r = +0.51 (anual); en bruto 0.579

## Disruptores puntuales y cambios de rumbo (4)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 4 de 77 comparaciones lo superan; por azar se esperarían ~4. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Mes de energía ciclónica extrema 2003 (2003-09) → oni: cambio de tendencia (de subir a bajar); +4.14 → -2.89 degC por década
- Temporada 2004 (2004-08) → skin_temp_atlantic_mdr: cambio de tendencia (de subir a bajar); +1.3 → -1.53 C por década
- Mes de energía ciclónica extrema 2004 (2004-09) → atlantic_mdr_sst: cambio de tendencia (de subir a bajar); +1.02 → -1.2 degC anomaly 1951-1980 por década
- Mes de energía ciclónica extrema 2016 (2016-10) → oni: cambio de tendencia (de subir a bajar); +4.06 → -1.74 degC por década

Voces añadidas solo por girar tras un disruptor: `oni.csv`

## Pares que solo superan 0.5 en bruto (8)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.
