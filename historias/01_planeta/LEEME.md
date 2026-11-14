# 1. El pulso del planeta
Global. CO₂, temperatura, nivel del mar y hielo: cuatro voces que llevan 45 años tocando la misma partitura.

Criterio: |r| ≥ 0.5 con alguna otra voz, en el dato secundario (mensual en su mejor desfase, o anual sin tendencia) o en el dato bruto. Spearman.

## Sets de datos incluidos (5)
- `co2_mlo.csv` — ppm · 1979-01 → 2026-09 · 573 valores · pedal (órgano / bajo continuo) · NOAA GML Mauna Loa
- `gistemp_global.csv` (solo por correlación en bruto) — degC anomaly 1951-1980 · 1979-01 → 2026-10 · 574 valores · melodía (violines) · NASA GISTEMP v4
- `global_mean_sea_level.csv` — mm · 1992-12 → 2025-02 · 387 valores · pedal (violonchelos) · NOAA STAR altimetry (TOPEX/Jason/Sentinel-6), seasonal signal kept
- `sea_ice_extent_north.csv` (solo por correlación en bruto) — 1e6 km2 · 1979-01 → 2026-10 · 572 valores · contramelodía (flauta / celesta) · NSIDC Sea Ice Index v4
- `sea_ice_extent_south.csv` — 1e6 km2 · 1979-01 → 2026-10 · 572 valores · contramelodía (flauta / celesta) · NSIDC Sea Ice Index v4

## Pares con |r| ≥ 0.5 (2)
- global_mean_sea_level ↔ sea_ice_extent_south: r = -0.56 (anual); en bruto -0.332
- co2_mlo ↔ sea_ice_extent_south: r = -0.54 (anual); en bruto -0.106

## Disruptores puntuales y cambios de rumbo (2)
No exigen correlación: se compara la tendencia de los 5 años anteriores al disruptor con la de los 5 posteriores y se listan los giros mayores que el 95 % de las demás fechas de la serie. 2 de 73 comparaciones lo superan; por azar se esperarían ~4. Ver `cambios_de_rumbo.csv` y `disruptores.csv`.
- Pico térmico global 1995 (1995-02) → co2_mlo: aceleración; +10.6 → +19.1 ppm por década
- Black Summer (Australia) (2019-09) → gistemp_global: aceleración (arranca una tendencia); +0.0244 → +1.14 degC anomaly 1951-1980 por década

## Voces que no llegan a 0,5 con ninguna otra, ni en bruto ni en secundario (no incluidas)
`oni`

## Pares que solo superan 0.5 en bruto (10)
Ver `pares_solo_en_bruto.csv`: comparten tendencia o estación, no variación de un año a otro.
