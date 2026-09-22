# Balanceadores de cinta N × M — libros 24 × 24

Tres libros de blueprints (cadenas de libro de blueprints, Factorio 2.0.77, juego base sin Space Age), uno por tipo de cinta:

| Archivo | Libro en el juego | Cinta | Subterránea máx. |
|---|---|---|---|
| [`yellow-belt.txt`](yellow-belt.txt) | `Yellow Belt balancer` | amarilla (transport-belt) | 5 casillas |
| [`red-belt.txt`](red-belt.txt) | `Red Belt balancer` | roja (fast-transport-belt) | 7 casillas |
| [`blue-belt.txt`](blue-belt.txt) | `Blue Belt balancer` | azul (express-transport-belt) | 9 casillas |

Cada archivo es la versión actual; las versiones anteriores quedan en el historial de git. Las secciones siguientes describen el libro azul;
las diferencias de los libros rojo y amarillo están en [Libros rojo y amarillo](#libros-rojo-y-amarillo).

## Estructura

- Libro raíz `Blue Belt balancer` con **24 sublibros** (`1` … `24`), uno por cantidad de cintas de entrada.
- Cada sublibro tiene `N to 1` … `N to 24` (el sublibro `2` tiene 25 elementos porque conserva las dos variantes `2 to 3 (Long)` y `2 to 3 (Wide)`).
- Total: **577 blueprints**, que cubren los 576 pares N × M.

## Origen de cada blueprint

| Origen | Cant. |
|---|---|
| Original del libro base (conservado) | 49 |
| Original reemplazado por no superar la verificación (Raynquist fall 2025) | 16 |
| Raynquist fall 2025 (pares que no existían: 9-x, x-9, 8-10, 10-10, 12-12, 16-16, …) | 38 |
| Generado por composición de bloques verificados | 474 |

### Originales defectuosos (reemplazados)

Estos 16 blueprints del libro original no son balanceadores correctos (p. ej., `4 to 5` junta dos bucles de retorno en una sola cinta y entrega 1,0 / 0,75 / 0,75 / 0,75 / 0,75 con las 4 entradas llenas):

`2 to 5`, `3 to 5`, `3 to 7`, `4 to 5`, `5 to 2`, `5 to 3`, `5 to 4`, `5 to 6`, `5 to 7`, `6 to 5`, `6 to 7`, `7 to 3`, `7 to 5`, `7 to 6`, `7 to 8`, `8 to 7`

## Cómo se generaron los nuevos

Los bloques de biblioteca (los originales aprobados + el libro de Raynquist, https://github.com/raynquist/balancer) se componen físicamente, siempre con flujo hacia el norte y entradas/salidas contiguas:

- `LOOP`: bloque (n+L → m+L) con L salidas realimentadas en las entradas por los lados (p. ej., 24→24 = núcleo 32-32 + 8 bucles).
- `STACK`: n→k abajo y g copias de (k/g → m/g) arriba (p. ej., 12→24 = 12-12 + 12×(1→2)).
- `SQ + K1`: balanceador cuadrado n × n seguido de un núcleo cuadrado con bucles y entradas podadas (cuando no hay divisor común).
- N > M: bloque N>M de la biblioteca, `DSTACK` (dual del STACK) o diseño N≤M con el flujo invertido — aceptado solo cuando la inversión no crea carga lateral.
- Los tramos rectos largos generados usan cinta subterránea exprés para reducir entidades.

## Verificación (todas aplicadas al archivo final)

1. **Simulación de flujo con contrapresión** (`scripts/deep_verify.py`): 6,8 millones de patrones de entrada/salida en total; 577/577 aprobados (salida balanceada con cualquier entrada, entrada balanceada con cualquier salida, caudal total = min(N,M) cintas, puertos contiguos, 0 avisos de carga lateral/subterránea sin pareja).
2. **Prueba automatizada dentro del juego** (Factorio 2.0.77 headless, datos aislados en `scripts/ingame/`): cada blueprint se importa, se construye, se alimenta con cargadores y se mide en 9 fases (todo activo; mitad/un tercio/aleatorio/una sola entrada; mitad/un tercio/aleatorio/una sola salida). Resultado: 577/577 construidos sin colisión y sin subterránea sin pareja; peor diferencia entre salidas (o entre entradas) = **4 objetos en 2700**; déficit de caudal máximo 0,15 %.
3. **Verificador de terceros** (`tzwaan/factorio_balancers`, en `scripts/xcheck/xcheck.py`): 576 PASS, 0 FAIL (`1 to 1` no tiene divisor y la herramienta no lo analiza). La misma herramienta confirma los 16 originales defectuosos y aprueba 143/143 de los de Raynquist.
4. La cadena completa del libro se importó en el juego: 24 sublibros, 577 blueprints con entidades.

## Tamaños de los generados

- mediana 453 entidades, media 690, máximo 2248 (`17 to 18`, 48 × 84 casillas).
- Los pares con N y M entre 17 y 24 sin divisor común son los más grandes (dos núcleos 32-32 apilados). Son correctos, pero grandes; no son diseños optimizados por SAT como los de Raynquist.

## Reproducir

```
cd scripts
export FBTIER=blue        # blue | red | yellow
python3 gen.py            # genera todos los pares
python3 build_book.py     # monta el libro y sobrescribe blueprints/belt-balancers/$FBTIER-belt.txt
python3 deep_verify.py ../blueprints/belt-balancers/$FBTIER-belt.txt
python3 export_tests.py ../blueprints/belt-balancers/$FBTIER-belt.txt && ./run_ingame.sh 3400 && python3 analyze_ingame.py
```

El generador lee las entradas de `scripts/sources/` (fuera de git; ver [`scripts/README.md`](../../scripts/README.md)).

## Libros rojo y amarillo

Misma estructura (24 sublibros × `N to 1..24`), generados por el mismo proceso con `FBTIER=red` / `FBTIER=yellow`:

- [`red-belt.txt`](red-belt.txt) — cinta roja (fast), subterránea de hasta 7 casillas.
- [`yellow-belt.txt`](yellow-belt.txt) — cinta amarilla, subterránea de hasta 5 casillas.

Diferencias respecto al azul:

- Los bloques de biblioteca se convierten al tipo de cinta y solo entran si todas las subterráneas siguen emparejadas (el `16-16` y el `32-32` de Raynquist usan túneles de 9 casillas y no sirven).
- El núcleo 16 × 16 rojo viene del "16-16 red" de Raynquist; el 16 × 16 amarillo y los dos 32 × 32 se construyen por duplicación (dos núcleos menores + N divisores + un enrutador de desentrelazado en franjas, `scripts/weave.py`), todos verificados.
- Por eso los blueprints grandes (N, M ≥ 17) son más grandes que los azules: rojo hasta 3605 entidades, amarillo hasta 4876.

### Rojo

- origen: `{'original': 49, 'raynquist': 18, 'generated': 494, 'raynquist-fix': 16}`
- generados: mediana 529 entidades, máximo 3605 (`18 to 19`, 56 × 175 casillas)
- verificación: simulación 577/577; prueba en el juego 577/577 en 9 fases (diferencia máxima de 4 objetos por ventana de 60 s); verificador de terceros 576 PASS / 0 FAIL.

### Amarillo

- origen: `{'original': 49, 'raynquist': 11, 'generated': 501, 'raynquist-fix': 16}`
- generados: mediana 1036 entidades, máximo 4876 (`17 to 18`, 56 × 206 casillas)
- verificación: simulación 577/577; prueba en el juego 577/577 en 9 fases (diferencia máxima de 4 objetos por ventana de 60 s); verificador de terceros 576 PASS / 0 FAIL.
- nota: en la cinta amarilla los 18 bucles más grandes (`17..23 to 17..24`) tardan más de 45.000 ticks en llenarse; con un calentamiento de 180.000 ticks el caudal medido queda en 99,97 %.

## Tabla completa (libro azul)

| Blueprint | Origen | Entidades | AnxAl | Construcción |
|---|---|---|---|---|
| 1 to 1 | `original` | 3 | 1x3 | Blueprint original (conservado). |
| 1 to 2 | `original` | 4 | 2x3 | Blueprint original (conservado). |
| 1 to 3 | `original` | 16 | 4x5 | Blueprint original (conservado). |
| 1 to 4 | `original` | 8 | 4x4 | Blueprint original (conservado). |
| 1 to 5 | `original` | 25 | 5x7 | Blueprint original (conservado). |
| 1 to 6 | `original` | 19 | 6x5 | Blueprint original (conservado). |
| 1 to 7 | `original` | 28 | 7x6 | Blueprint original (conservado). |
| 1 to 8 | `original` | 22 | 8x6 | Blueprint original (conservado). |
| 1 to 9 | `raynquist` | 45 | 9x8 | Fuente: libro de balanceadores de Raynquist (fall 2025), '1-9 TU balancer'. |
| 1 to 10 | `generated` | 60 | 10x11 | Generado con bloques verificados: STACK 1->2 + 2x(1->5). |
| 1 to 11 | `generated` | 94 | 13x21 | Generado con bloques verificados: K1 P=12 nl=1 dead=[1..10;10]. |
| 1 to 12 | `generated` | 47 | 12x9 | Generado con bloques verificados: STACK 1->2 + 2x(1->6). |
| 1 to 13 | `generated` | 160 | 19x22 | Generado con bloques verificados: K1 P=16 nl=0 dead=[0..11;12]. |
| 1 to 14 | `generated` | 65 | 14x10 | Generado con bloques verificados: STACK 1->2 + 2x(1->7). |
| 1 to 15 | `generated` | 98 | 17x18 | Generado con bloques verificados: K1 P=16 nl=0 dead=[0..13;14]. |
| 1 to 16 | `generated` | 49 | 16x9 | Generado con bloques verificados: STACK 1->2 + 2x(1->8). |
| 1 to 17 | `raynquist` | 72 | 17x10 | Fuente: libro de balanceadores de Raynquist (fall 2025), '1-17 balancer'. |
| 1 to 18 | `generated` | 82 | 18x11 | Generado con bloques verificados: STACK 1->3 + 3x(1->6). |
| 1 to 19 | `generated` | 798 | 45x53 | Generado con bloques verificados: K1 P=32 nl=0 dead=[0..17;18]. |
| 1 to 20 | `generated` | 87 | 20x13 | Generado con bloques verificados: STACK 1->5 + 5x(1->4). |
| 1 to 21 | `generated` | 109 | 21x12 | Generado con bloques verificados: STACK 1->3 + 3x(1->7). |
| 1 to 22 | `generated` | 208 | 22x29 | Generado con bloques verificados: STACK 1->11 + 11x(1->2). |
| 1 to 23 | `generated` | 638 | 41x45 | Generado con bloques verificados: K1 P=32 nl=0 dead=[0..21;22]. |
| 1 to 24 | `generated` | 85 | 24x11 | Generado con bloques verificados: STACK 1->3 + 3x(1->8). |
| 2 to 1 | `original` | 4 | 2x3 | Blueprint original (conservado). |
| 2 to 2 | `original` | 5 | 2x3 | Blueprint original (conservado). |
| 2 to 3 (Long) | `original` | 25 | 5x7 | Blueprint original (conservado). |
| 2 to 3 (Wide) | `original` | 22 | 7x5 | Blueprint original (conservado). |
| 2 to 4 | `original` | 9 | 4x4 | Blueprint original (conservado). |
| 2 to 5 | `raynquist-fix` | 31 | 5x8 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '2-5 balancer'. |
| 2 to 6 | `original` | 33 | 8x6 | Blueprint original (conservado). |
| 2 to 7 | `original` | 33 | 8x6 | Blueprint original (conservado). |
| 2 to 8 | `original` | 23 | 8x6 | Blueprint original (conservado). |
| 2 to 9 | `raynquist` | 51 | 9x8 | Fuente: libro de balanceadores de Raynquist (fall 2025), '2-9 balancer'. |
| 2 to 10 | `generated` | 61 | 10x11 | Generado con bloques verificados: STACK 2->2 + 2x(1->5). |
| 2 to 11 | `generated` | 117 | 13x24 | Generado con bloques verificados: SQ(2) + K1 P=12 nl=1 dead=[2..10;9]. |
| 2 to 12 | `generated` | 48 | 12x9 | Generado con bloques verificados: STACK 2->2 + 2x(1->6). |
| 2 to 13 | `generated` | 196 | 19x25 | Generado con bloques verificados: SQ(2) + K1 P=16 nl=0 dead=[0..10;11]. |
| 2 to 14 | `generated` | 66 | 14x10 | Generado con bloques verificados: STACK 2->2 + 2x(1->7). |
| 2 to 15 | `generated` | 108 | 15x13 | Generado con bloques verificados: STACK 2->3 + 3x(1->5). |
| 2 to 16 | `generated` | 50 | 16x9 | Generado con bloques verificados: STACK 2->2 + 2x(1->8). |
| 2 to 17 | `generated` | 967 | 47x46 | Generado con bloques verificados: SQ(2) + K1 P=32 nl=7 dead=[2..16;15]. |
| 2 to 18 | `generated` | 88 | 18x11 | Generado con bloques verificados: STACK 2->3 + 3x(1->6). |
| 2 to 19 | `generated` | 815 | 45x56 | Generado con bloques verificados: SQ(2) + K1 P=32 nl=0 dead=[0..16;17]. |
| 2 to 20 | `generated` | 93 | 20x14 | Generado con bloques verificados: STACK 2->5 + 5x(1->4). |
| 2 to 21 | `generated` | 115 | 21x12 | Generado con bloques verificados: STACK 2->3 + 3x(1->7). |
| 2 to 22 | `generated` | 231 | 22x32 | Generado con bloques verificados: STACK 2->11 + 11x(1->2). |
| 2 to 23 | `generated` | 651 | 41x48 | Generado con bloques verificados: SQ(2) + K1 P=32 nl=0 dead=[0..20;21]. |
| 2 to 24 | `generated` | 91 | 24x11 | Generado con bloques verificados: STACK 2->3 + 3x(1->8). |
| 3 to 1 | `original` | 18 | 4x6 | Blueprint original (conservado). |
| 3 to 2 | `original` | 25 | 5x7 | Blueprint original (conservado). |
| 3 to 3 | `original` | 32 | 6x7 | Blueprint original (conservado). |
| 3 to 4 | `original` | 39 | 7x8 | Blueprint original (conservado). |
| 3 to 5 | `raynquist-fix` | 53 | 8x9 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '3-5 balancer'. |
| 3 to 6 | `original` | 30 | 7x6 | Blueprint original (conservado). |
| 3 to 7 | `raynquist-fix` | 56 | 8x10 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '3-7 balancer'. |
| 3 to 8 | `original` | 53 | 8x10 | Blueprint original (conservado). |
| 3 to 9 | `raynquist` | 63 | 9x9 | Fuente: libro de balanceadores de Raynquist (fall 2025), '3-9 balancer'. |
| 3 to 10 | `generated` | 89 | 10x14 | Generado con bloques verificados: STACK 3->5 + 5x(1->2). |
| 3 to 11 | `generated` | 144 | 13x30 | Generado con bloques verificados: SQ(3) + K1 P=12 nl=1 dead=[3..10;8]. |
| 3 to 12 | `generated` | 63 | 12x14 | Generado con bloques verificados: STACK 3->3 + 3x(1->4). |
| 3 to 13 | `generated` | 225 | 19x31 | Generado con bloques verificados: SQ(3) + K1 P=16 nl=0 dead=[0..9;10]. |
| 3 to 14 | `generated` | 117 | 14x16 | Generado con bloques verificados: STACK 3->7 + 7x(1->2). |
| 3 to 15 | `generated` | 116 | 15x17 | Generado con bloques verificados: STACK 3->3 + 3x(1->5). |
| 3 to 16 | `generated` | 88 | 16x14 | Generado con bloques verificados: STACK 3->4 + 4x(1->4). |
| 3 to 17 | `generated` | 996 | 47x52 | Generado con bloques verificados: SQ(3) + K1 P=32 nl=7 dead=[3..16;14]. |
| 3 to 18 | `generated` | 96 | 18x15 | Generado con bloques verificados: STACK 3->3 + 3x(1->6). |
| 3 to 19 | `generated` | 846 | 45x62 | Generado con bloques verificados: SQ(3) + K1 P=32 nl=0 dead=[0..15;16]. |
| 3 to 20 | `generated` | 115 | 20x15 | Generado con bloques verificados: STACK 3->5 + 5x(1->4). |
| 3 to 21 | `generated` | 123 | 21x16 | Generado con bloques verificados: STACK 3->3 + 3x(1->7). |
| 3 to 22 | `generated` | 258 | 22x38 | Generado con bloques verificados: STACK 3->11 + 11x(1->2). |
| 3 to 23 | `generated` | 680 | 41x54 | Generado con bloques verificados: SQ(3) + K1 P=32 nl=0 dead=[0..19;20]. |
| 3 to 24 | `generated` | 99 | 24x15 | Generado con bloques verificados: STACK 3->3 + 3x(1->8). |
| 4 to 1 | `original` | 8 | 4x4 | Blueprint original (conservado). |
| 4 to 2 | `original` | 9 | 4x4 | Blueprint original (conservado). |
| 4 to 3 | `original` | 39 | 7x8 | Blueprint original (conservado). |
| 4 to 4 | `original` | 30 | 4x9 | Blueprint original (conservado). |
| 4 to 5 | `raynquist-fix` | 57 | 8x10 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '4-5 balancer'. |
| 4 to 6 | `original` | 52 | 6x11 | Blueprint original (conservado). |
| 4 to 7 | `original` | 54 | 9x9 | Blueprint original (conservado). |
| 4 to 8 | `original` | 36 | 8x6 | Blueprint original (conservado). |
| 4 to 9 | `raynquist` | 74 | 9x12 | Fuente: libro de balanceadores de Raynquist (fall 2025), '4-9 balancer'. |
| 4 to 10 | `generated` | 93 | 10x15 | Generado con bloques verificados: STACK 4->5 + 5x(1->2). |
| 4 to 11 | `generated` | 149 | 13x30 | Generado con bloques verificados: SQ(4) + K1 P=12 nl=1 dead=[4..10;7]. |
| 4 to 12 | `raynquist` | 139 | 12x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '4-12 TU balancer'. |
| 4 to 13 | `generated` | 235 | 19x31 | Generado con bloques verificados: SQ(4) + K1 P=16 nl=0 dead=[0..8;9]. |
| 4 to 14 | `generated` | 115 | 14x15 | Generado con bloques verificados: STACK 4->7 + 7x(1->2). |
| 4 to 15 | `generated` | 165 | 17x27 | Generado con bloques verificados: SQ(4) + K1 P=16 nl=0 dead=[0..10;11]. |
| 4 to 16 | `generated` | 79 | 16x15 | Generado con bloques verificados: STACK 4->4 + 4x(1->4). |
| 4 to 17 | `generated` | 1004 | 47x52 | Generado con bloques verificados: SQ(4) + K1 P=32 nl=7 dead=[4..16;13]. |
| 4 to 18 | `generated` | 146 | 18x19 | Generado con bloques verificados: STACK 4->4 + 2x(2->9). |
| 4 to 19 | `generated` | 954 | 45x50 | Generado con bloques verificados: SQ(4) + K1 P=32 nl=6 dead=[0..14;15]. |
| 4 to 20 | `generated` | 119 | 20x16 | Generado con bloques verificados: STACK 4->5 + 5x(1->4). |
| 4 to 21 | `generated` | 294 | 24x26 | Generado con bloques verificados: STACK 4->6 + 3x(2->7). |
| 4 to 22 | `generated` | 263 | 22x38 | Generado con bloques verificados: STACK 4->11 + 11x(1->2). |
| 4 to 23 | `generated` | 710 | 41x54 | Generado con bloques verificados: SQ(4) + K1 P=32 nl=0 dead=[0..18;19]. |
| 4 to 24 | `generated` | 123 | 24x16 | Generado con bloques verificados: STACK 4->4 + 4x(1->6). |
| 5 to 1 | `original` | 25 | 6x7 | Blueprint original (conservado). |
| 5 to 2 | `raynquist-fix` | 31 | 5x8 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '5-2 balancer'. |
| 5 to 3 | `raynquist-fix` | 57 | 8x10 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '5-3 balancer'. |
| 5 to 4 | `raynquist-fix` | 57 | 8x10 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '5-4 balancer'. |
| 5 to 5 | `original` | 81 | 10x11 | Blueprint original (conservado). |
| 5 to 6 | `raynquist-fix` | 86 | 8x15 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '5-6 balancer'. |
| 5 to 7 | `raynquist-fix` | 97 | 9x15 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '5-7 balancer'. |
| 5 to 8 | `original` | 119 | 10x16 | Blueprint original (conservado). |
| 5 to 9 | `raynquist` | 117 | 9x18 | Fuente: libro de balanceadores de Raynquist (fall 2025), '5-9 balancer'. |
| 5 to 10 | `generated` | 98 | 10x17 | Generado con bloques verificados: STACK 5->5 + 5x(1->2). |
| 5 to 11 | `generated` | 183 | 13x33 | Generado con bloques verificados: SQ(5) + K1 P=12 nl=1 dead=[5, 6, 7, 8, 9, 10]. |
| 5 to 12 | `generated` | 133 | 12x21 | Generado con bloques verificados: STACK 5->6 + 3x(2->4). |
| 5 to 13 | `generated` | 271 | 19x34 | Generado con bloques verificados: SQ(5) + K1 P=16 nl=0 dead=[0..7;8]. |
| 5 to 14 | `generated` | 158 | 14x21 | Generado con bloques verificados: STACK 5->7 + 7x(1->2). |
| 5 to 15 | `generated` | 199 | 17x30 | Generado con bloques verificados: SQ(5) + K1 P=16 nl=0 dead=[0..9;10]. |
| 5 to 16 | `generated` | 163 | 16x21 | Generado con bloques verificados: STACK 5->8 + 8x(1->2). |
| 5 to 17 | `generated` | 1040 | 47x55 | Generado con bloques verificados: SQ(5) + K1 P=32 nl=7 dead=[5..16;12]. |
| 5 to 18 | `generated` | 239 | 18x27 | Generado con bloques verificados: STACK 5->6 + 2x(3->9). |
| 5 to 19 | `generated` | 990 | 45x53 | Generado con bloques verificados: SQ(5) + K1 P=32 nl=6 dead=[0..13;14]. |
| 5 to 20 | `generated` | 124 | 20x18 | Generado con bloques verificados: STACK 5->5 + 5x(1->4). |
| 5 to 21 | `generated` | 329 | 24x30 | Generado con bloques verificados: STACK 5->6 + 3x(2->7). |
| 5 to 22 | `generated` | 297 | 22x41 | Generado con bloques verificados: STACK 5->11 + 11x(1->2). |
| 5 to 23 | `generated` | 746 | 41x57 | Generado con bloques verificados: SQ(5) + K1 P=32 nl=0 dead=[0..17;18]. |
| 5 to 24 | `generated` | 167 | 24x22 | Generado con bloques verificados: STACK 5->6 + 6x(1->4). |
| 6 to 1 | `original` | 21 | 6x6 | Blueprint original (conservado). |
| 6 to 2 | `original` | 32 | 7x7 | Blueprint original (conservado). |
| 6 to 3 | `original` | 33 | 7x7 | Blueprint original (conservado). |
| 6 to 4 | `original` | 52 | 6x11 | Blueprint original (conservado). |
| 6 to 5 | `raynquist-fix` | 86 | 8x15 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '6-5 balancer'. |
| 6 to 6 | `original` | 73 | 9x11 | Blueprint original (conservado). |
| 6 to 7 | `raynquist-fix` | 96 | 9x14 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '6-7 balancer'. |
| 6 to 8 | `original` | 90 | 10x13 | Blueprint original (conservado). |
| 6 to 9 | `raynquist` | 101 | 9x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '6-9 balancer'. |
| 6 to 10 | `generated` | 184 | 11x30 | Generado con bloques verificados: SQ(6) + K1 P=10 nl=0 dead=[0, 1, 2, 3]. |
| 6 to 11 | `generated` | 244 | 13x34 | Generado con bloques verificados: SQ(6) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 6 to 12 | `generated` | 112 | 12x19 | Generado con bloques verificados: STACK 6->6 + 3x(2->4). |
| 6 to 13 | `generated` | 300 | 19x33 | Generado con bloques verificados: SQ(6) + K1 P=16 nl=1 dead=[6..12;7]. |
| 6 to 14 | `generated` | 157 | 14x20 | Generado con bloques verificados: STACK 6->7 + 7x(1->2). |
| 6 to 15 | `generated` | 182 | 15x23 | Generado con bloques verificados: STACK 6->6 + 3x(2->5). |
| 6 to 16 | `generated` | 158 | 16x20 | Generado con bloques verificados: STACK 6->8 + 8x(1->2). |
| 6 to 17 | `generated` | 1073 | 47x56 | Generado con bloques verificados: SQ(6) + K1 P=32 nl=7 dead=[6..16;11]. |
| 6 to 18 | `generated` | 193 | 18x23 | Generado con bloques verificados: STACK 6->9 + 9x(1->2). |
| 6 to 19 | `generated` | 1002 | 45x54 | Generado con bloques verificados: SQ(6) + K1 P=32 nl=6 dead=[6..18;13]. |
| 6 to 20 | `generated` | 252 | 20x25 | Generado con bloques verificados: STACK 6->8 + 4x(2->5). |
| 6 to 21 | `generated` | 308 | 24x28 | Generado con bloques verificados: STACK 6->6 + 3x(2->7). |
| 6 to 22 | `generated` | 358 | 22x42 | Generado con bloques verificados: STACK 6->11 + 11x(1->2). |
| 6 to 23 | `generated` | 759 | 41x58 | Generado con bloques verificados: SQ(6) + K1 P=32 nl=0 dead=[0..16;17]. |
| 6 to 24 | `generated` | 146 | 24x20 | Generado con bloques verificados: STACK 6->6 + 6x(1->4). |
| 7 to 1 | `original` | 30 | 7x7 | Blueprint original (conservado). |
| 7 to 2 | `original` | 37 | 8x7 | Blueprint original (conservado). |
| 7 to 3 | `raynquist-fix` | 53 | 9x8 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '7-3 balancer'. |
| 7 to 4 | `original` | 54 | 9x9 | Blueprint original (conservado). |
| 7 to 5 | `raynquist-fix` | 97 | 9x15 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '7-5 balancer'. |
| 7 to 6 | `raynquist-fix` | 96 | 9x14 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '7-6 balancer'. |
| 7 to 7 | `original` | 91 | 10x11 | Blueprint original (conservado). |
| 7 to 8 | `raynquist-fix` | 97 | 8x16 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '7-8 balancer'. |
| 7 to 9 | `raynquist` | 168 | 12x18 | Fuente: libro de balanceadores de Raynquist (fall 2025), '7-9 balancer'. |
| 7 to 10 | `raynquist` | 138 | 10x19 | Fuente: libro de balanceadores de Raynquist (fall 2025), '7-10 balancer'. |
| 7 to 11 | `generated` | 261 | 13x35 | Generado con bloques verificados: SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3]. |
| 7 to 12 | `generated` | 234 | 12x33 | Generado con bloques verificados: SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 7 to 13 | `raynquist` | 158 | 15x15 | Fuente: libro de balanceadores de Raynquist (fall 2025), '7-13 balancer'. |
| 7 to 14 | `generated` | 141 | 14x20 | Generado con bloques verificados: STACK 7->7 + 7x(1->2). |
| 7 to 15 | `generated` | 227 | 17x32 | Generado con bloques verificados: SQ(7) + K1 P=16 nl=0 dead=[0..7;8]. |
| 7 to 16 | `generated` | 177 | 16x23 | Generado con bloques verificados: STACK 7->8 + 8x(1->2). |
| 7 to 17 | `generated` | 1092 | 47x57 | Generado con bloques verificados: SQ(7) + K1 P=32 nl=7 dead=[7..16;10]. |
| 7 to 18 | `generated` | 260 | 18x25 | Generado con bloques verificados: STACK 7->9 + 9x(1->2). |
| 7 to 19 | `generated` | 1042 | 45x55 | Generado con bloques verificados: SQ(7) + K1 P=32 nl=6 dead=[0..11;12]. |
| 7 to 20 | `generated` | 245 | 20x27 | Generado con bloques verificados: STACK 7->10 + 10x(1->2). |
| 7 to 21 | `generated` | 385 | 28x31 | Generado con bloques verificados: STACK 7->7 + 7x(1->3). |
| 7 to 22 | `generated` | 375 | 22x43 | Generado con bloques verificados: STACK 7->11 + 11x(1->2). |
| 7 to 23 | `generated` | 778 | 41x59 | Generado con bloques verificados: SQ(7) + K1 P=32 nl=0 dead=[0..15;16]. |
| 7 to 24 | `generated` | 337 | 24x37 | Generado con bloques verificados: STACK 7->8 + 2x(4->12). |
| 8 to 1 | `original` | 20 | 8x6 | Blueprint original (conservado). |
| 8 to 2 | `original` | 21 | 8x6 | Blueprint original (conservado). |
| 8 to 3 | `original` | 50 | 8x10 | Blueprint original (conservado). |
| 8 to 4 | `original` | 40 | 8x7 | Blueprint original (conservado). |
| 8 to 5 | `original` | 111 | 10x17 | Blueprint original (conservado). |
| 8 to 6 | `original` | 90 | 10x13 | Blueprint original (conservado). |
| 8 to 7 | `raynquist-fix` | 97 | 8x16 | Reemplaza al original, que no superó la verificación. Fuente: libro de balanceadores de Raynquist (fall 2025), '8-7 balancer'. |
| 8 to 8 | `original` | 82 | 10x11 | Blueprint original (conservado). |
| 8 to 9 | `raynquist` | 137 | 11x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '8-9 balancer'. |
| 8 to 10 | `raynquist` | 124 | 10x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '8-10 balancer'. |
| 8 to 11 | `generated` | 271 | 13x33 | Generado con bloques verificados: SQ(8) + K1 P=12 nl=1 dead=[0, 9, 10]. |
| 8 to 12 | `raynquist` | 127 | 12x14 | Fuente: libro de balanceadores de Raynquist (fall 2025), '8-12 balancer'. |
| 8 to 13 | `raynquist` | 156 | 15x15 | Fuente: libro de balanceadores de Raynquist (fall 2025), '8-13 balancer'. |
| 8 to 14 | `generated` | 310 | 18x32 | Generado con bloques verificados: SQ(8) + K1 P=16 nl=0 dead=[8, 9, 10, 11, 12, 13]. |
| 8 to 15 | `generated` | 274 | 17x30 | Generado con bloques verificados: SQ(8) + K1 P=16 nl=0 dead=[8..14;7]. |
| 8 to 16 | `generated` | 156 | 16x19 | Generado con bloques verificados: STACK 8->8 + 8x(1->2). |
| 8 to 17 | `generated` | 1098 | 47x55 | Generado con bloques verificados: SQ(8) + K1 P=32 nl=7 dead=[8..16;9]. |
| 8 to 18 | `generated` | 229 | 18x23 | Generado con bloques verificados: STACK 8->9 + 9x(1->2). |
| 8 to 19 | `generated` | 1047 | 45x53 | Generado con bloques verificados: SQ(8) + K1 P=32 nl=6 dead=[8..18;11]. |
| 8 to 20 | `generated` | 231 | 20x24 | Generado con bloques verificados: STACK 8->10 + 10x(1->2). |
| 8 to 21 | `generated` | 470 | 24x36 | Generado con bloques verificados: STACK 8->9 + 3x(3->7). |
| 8 to 22 | `generated` | 385 | 22x41 | Generado con bloques verificados: STACK 8->11 + 11x(1->2). |
| 8 to 23 | `generated` | 961 | 41x49 | Generado con bloques verificados: SQ(8) + K1 P=32 nl=4 dead=[8..22;15]. |
| 8 to 24 | `generated` | 261 | 24x23 | Generado con bloques verificados: STACK 8->12 + 12x(1->2). |
| 9 to 1 | `raynquist` | 46 | 9x8 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-1 TU balancer'. |
| 9 to 2 | `raynquist` | 51 | 10x8 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-2 balancer'. |
| 9 to 3 | `raynquist` | 64 | 10x9 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-3 balancer'. |
| 9 to 4 | `raynquist` | 79 | 9x12 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-4 balancer'. |
| 9 to 5 | `raynquist` | 118 | 9x18 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-5 balancer'. |
| 9 to 6 | `raynquist` | 101 | 9x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-6 balancer'. |
| 9 to 7 | `raynquist` | 167 | 12x18 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-7 balancer'. |
| 9 to 8 | `raynquist` | 137 | 11x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-8 balancer'. |
| 9 to 9 | `raynquist` | 136 | 11x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-9 balancer'. |
| 9 to 10 | `raynquist` | 197 | 11x23 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-10 balancer'. |
| 9 to 11 | `generated` | 333 | 13x37 | Generado con bloques verificados: SQ(9) + K1 P=12 nl=1 dead=[9, 10]. |
| 9 to 12 | `raynquist` | 154 | 12x18 | Fuente: libro de balanceadores de Raynquist (fall 2025), '9-12 balancer'. |
| 9 to 13 | `generated` | 409 | 19x36 | Generado con bloques verificados: SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12]. |
| 9 to 14 | `generated` | 373 | 18x34 | Generado con bloques verificados: SQ(9) + K1 P=16 nl=1 dead=[0, 1, 2, 3, 4]. |
| 9 to 15 | `generated` | 338 | 17x34 | Generado con bloques verificados: SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12, 13, 14]. |
| 9 to 16 | `generated` | 303 | 16x32 | Generado con bloques verificados: SQ(9) + K1 P=16 nl=0 dead=[0..15;7]. |
| 9 to 17 | `generated` | 1162 | 47x59 | Generado con bloques verificados: SQ(9) + K1 P=32 nl=7 dead=[9..16;8]. |
| 9 to 18 | `generated` | 228 | 18x23 | Generado con bloques verificados: STACK 9->9 + 9x(1->2). |
| 9 to 19 | `generated` | 1112 | 45x57 | Generado con bloques verificados: SQ(9) + K1 P=32 nl=6 dead=[0..9;10]. |
| 9 to 20 | `generated` | 304 | 20x31 | Generado con bloques verificados: STACK 9->10 + 10x(1->2). |
| 9 to 21 | `generated` | 469 | 24x36 | Generado con bloques verificados: STACK 9->9 + 3x(3->7). |
| 9 to 22 | `generated` | 447 | 22x45 | Generado con bloques verificados: STACK 9->11 + 11x(1->2). |
| 9 to 23 | `generated` | 1031 | 41x53 | Generado con bloques verificados: SQ(9) + K1 P=32 nl=4 dead=[0..13;14]. |
| 9 to 24 | `generated` | 288 | 24x27 | Generado con bloques verificados: STACK 9->12 + 12x(1->2). |
| 10 to 1 | `generated` | 61 | 10x12 | Generado con bloques verificados: DSTACK 5x(2->1) + 5->1. |
| 10 to 2 | `generated` | 67 | 10x13 | Generado con bloques verificados: DSTACK 5x(2->1) + 5->2. |
| 10 to 3 | `generated` | 93 | 10x15 | Generado con bloques verificados: DSTACK 5x(2->1) + 5->3. |
| 10 to 4 | `generated` | 93 | 10x15 | Generado con bloques verificados: REVERSED STACK 4->5 + 5x(1->2). |
| 10 to 5 | `generated` | 98 | 10x17 | Generado con bloques verificados: REVERSED STACK 5->5 + 5x(1->2). |
| 10 to 6 | `generated` | 184 | 11x30 | Generado con bloques verificados: REVERSED SQ(6) + K1 P=10 nl=0 dead=[0, 1, 2, 3]. |
| 10 to 7 | `generated` | 212 | 11x31 | Generado con bloques verificados: REV(K1 P=10 nl=0 dead=[0, 1, 2]) + SQ(7). |
| 10 to 8 | `raynquist` | 124 | 10x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '10-8 balancer'. |
| 10 to 9 | `generated` | 197 | 11x23 | Generado con bloques verificados: REVERSED LIB. |
| 10 to 10 | `raynquist` | 147 | 11x17 | Fuente: libro de balanceadores de Raynquist (fall 2025), '10-10 balancer'. |
| 10 to 11 | `generated` | 353 | 14x38 | Generado con bloques verificados: SQ(10) + K1p P=12 loops=0+1. |
| 10 to 12 | `generated` | 316 | 13x36 | Generado con bloques verificados: SQ(10) + K1 P=12 nl=0 dead=[10, 11]. |
| 10 to 13 | `generated` | 427 | 19x37 | Generado con bloques verificados: SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 10 to 14 | `generated` | 390 | 18x35 | Generado con bloques verificados: SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2, 3]. |
| 10 to 15 | `generated` | 355 | 17x35 | Generado con bloques verificados: SQ(10) + K1 P=16 nl=1 dead=[10, 11, 12, 13, 14]. |
| 10 to 16 | `generated` | 317 | 17x33 | Generado con bloques verificados: SQ(10) + K1 P=16 nl=0 dead=[10, 11, 12, 13, 14, 15]. |
| 10 to 17 | `generated` | 1236 | 47x60 | Generado con bloques verificados: SQ(10) + K1 P=32 nl=7 dead=[0..16;7]. |
| 10 to 18 | `generated` | 533 | 18x51 | Generado con bloques verificados: STACK 10->12 + 3x(4->6). |
| 10 to 19 | `generated` | 1132 | 45x58 | Generado con bloques verificados: SQ(10) + K1 P=32 nl=6 dead=[10..18;9]. |
| 10 to 20 | `generated` | 254 | 20x25 | Generado con bloques verificados: STACK 10->10 + 10x(1->2). |
| 10 to 21 | `generated` | 684 | 27x56 | Generado con bloques verificados: STACK 10->12 + 3x(4->7). |
| 10 to 22 | `generated` | 467 | 22x46 | Generado con bloques verificados: STACK 10->11 + 11x(1->2). |
| 10 to 23 | `generated` | 1052 | 41x54 | Generado con bloques verificados: SQ(10) + K1 P=32 nl=4 dead=[0..12;13]. |
| 10 to 24 | `generated` | 450 | 24x45 | Generado con bloques verificados: STACK 10->12 + 12x(1->2). |
| 11 to 1 | `generated` | 94 | 13x21 | Generado con bloques verificados: REVERSED K1 P=12 nl=1 dead=[1..10;10]. |
| 11 to 2 | `generated` | 117 | 13x24 | Generado con bloques verificados: REVERSED SQ(2) + K1 P=12 nl=1 dead=[2..10;9]. |
| 11 to 3 | `generated` | 144 | 13x30 | Generado con bloques verificados: REVERSED SQ(3) + K1 P=12 nl=1 dead=[3..10;8]. |
| 11 to 4 | `generated` | 149 | 13x30 | Generado con bloques verificados: REVERSED SQ(4) + K1 P=12 nl=1 dead=[4..10;7]. |
| 11 to 5 | `generated` | 183 | 13x33 | Generado con bloques verificados: REVERSED SQ(5) + K1 P=12 nl=1 dead=[5, 6, 7, 8, 9, 10]. |
| 11 to 6 | `generated` | 244 | 13x34 | Generado con bloques verificados: REVERSED SQ(6) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 11 to 7 | `generated` | 261 | 13x35 | Generado con bloques verificados: REVERSED SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3]. |
| 11 to 8 | `generated` | 271 | 13x33 | Generado con bloques verificados: REVERSED SQ(8) + K1 P=12 nl=1 dead=[0, 9, 10]. |
| 11 to 9 | `generated` | 333 | 13x37 | Generado con bloques verificados: REVERSED SQ(9) + K1 P=12 nl=1 dead=[9, 10]. |
| 11 to 10 | `raynquist` | 205 | 13x23 | Fuente: libro de balanceadores de Raynquist (fall 2025), '11-10 balancer'. |
| 11 to 11 | `generated` | 208 | 13x21 | Generado con bloques verificados: LOOP(12-12) nl=0. |
| 11 to 12 | `generated` | 385 | 14x40 | Generado con bloques verificados: SQ(11) + K1 P=12 nl=0 dead=[0]. |
| 11 to 13 | `generated` | 491 | 19x41 | Generado con bloques verificados: SQ(11) + K1 P=16 nl=1 dead=[11, 12]. |
| 11 to 14 | `generated` | 453 | 18x39 | Generado con bloques verificados: SQ(11) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 11 to 15 | `generated` | 418 | 17x39 | Generado con bloques verificados: SQ(11) + K1 P=16 nl=1 dead=[11, 12, 13, 14]. |
| 11 to 16 | `generated` | 383 | 16x37 | Generado con bloques verificados: SQ(11) + K1 P=16 nl=0 dead=[11, 12, 13, 14, 15]. |
| 11 to 17 | `generated` | 1292 | 47x64 | Generado con bloques verificados: SQ(11) + K1 P=32 nl=7 dead=[11, 12, 13, 14, 15, 16]. |
| 11 to 18 | `generated` | 602 | 18x55 | Generado con bloques verificados: STACK 11->12 + 3x(4->6). |
| 11 to 19 | `generated` | 1241 | 45x62 | Generado con bloques verificados: SQ(11) + K1 P=32 nl=6 dead=[0..7;8]. |
| 11 to 20 | `generated` | 712 | 20x61 | Generado con bloques verificados: STACK 11->16 + 2x(8->10). |
| 11 to 21 | `generated` | 753 | 27x60 | Generado con bloques verificados: STACK 11->12 + 3x(4->7). |
| 11 to 22 | `generated` | 322 | 22x29 | Generado con bloques verificados: STACK 11->11 + 11x(1->2). |
| 11 to 23 | `generated` | 1106 | 41x58 | Generado con bloques verificados: SQ(11) + K1 P=32 nl=4 dead=[0..11;12]. |
| 11 to 24 | `generated` | 519 | 24x49 | Generado con bloques verificados: STACK 11->12 + 12x(1->2). |
| 12 to 1 | `generated` | 51 | 12x10 | Generado con bloques verificados: DSTACK 2x(6->1) + 2->1. |
| 12 to 2 | `generated` | 52 | 12x10 | Generado con bloques verificados: DSTACK 2x(6->1) + 2->2. |
| 12 to 3 | `generated` | 63 | 12x14 | Generado con bloques verificados: REVERSED STACK 3->3 + 3x(1->4). |
| 12 to 4 | `raynquist` | 139 | 12x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '12-4 TU balancer'. |
| 12 to 5 | `generated` | 133 | 12x21 | Generado con bloques verificados: REVERSED STACK 5->6 + 3x(2->4). |
| 12 to 6 | `generated` | 112 | 12x19 | Generado con bloques verificados: REVERSED STACK 6->6 + 3x(2->4). |
| 12 to 7 | `generated` | 234 | 12x33 | Generado con bloques verificados: REVERSED SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 12 to 8 | `generated` | 220 | 12x27 | Generado con bloques verificados: DSTACK 2x(6->4) + 8->8. |
| 12 to 9 | `generated` | 304 | 12x35 | Generado con bloques verificados: REV(K1 P=12 nl=0 dead=[0, 10, 11]) + SQ(9). |
| 12 to 10 | `raynquist` | 199 | 12x22 | Fuente: libro de balanceadores de Raynquist (fall 2025), '12-10 balancer'. |
| 12 to 11 | `generated` | 385 | 14x40 | Generado con bloques verificados: REVERSED SQ(11) + K1 P=12 nl=0 dead=[0]. |
| 12 to 12 | `raynquist` | 178 | 12x19 | Fuente: libro de balanceadores de Raynquist (fall 2025), '12-12 balancer'. |
| 12 to 13 | `generated` | 468 | 19x39 | Generado con bloques verificados: SQ(12) + K1p P=16 loops=2+1. |
| 12 to 14 | `generated` | 429 | 18x37 | Generado con bloques verificados: SQ(12) + K1p P=16 loops=1+1. |
| 12 to 15 | `generated` | 415 | 17x37 | Generado con bloques verificados: SQ(12) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 12 to 16 | `generated` | 354 | 16x35 | Generado con bloques verificados: SQ(12) + K1 P=16 nl=0 dead=[12, 13, 14, 15]. |
| 12 to 17 | `generated` | 1281 | 47x62 | Generado con bloques verificados: SQ(12) + K1 P=32 nl=7 dead=[0, 1, 2, 3, 4]. |
| 12 to 18 | `generated` | 395 | 18x34 | Generado con bloques verificados: STACK 12->12 + 3x(4->6). |
| 12 to 19 | `generated` | 1230 | 45x60 | Generado con bloques verificados: SQ(12) + K1 P=32 nl=6 dead=[0..6;7]. |
| 12 to 20 | `generated` | 638 | 32x44 | Generado con bloques verificados: STACK 12->12 + 4x(3->5). |
| 12 to 21 | `generated` | 546 | 27x39 | Generado con bloques verificados: STACK 12->12 + 3x(4->7). |
| 12 to 22 | `generated` | 871 | 26x70 | Generado con bloques verificados: STACK 12->12 + 2x(6->11). |
| 12 to 23 | `generated` | 1111 | 41x56 | Generado con bloques verificados: SQ(12) + K1 P=32 nl=4 dead=[12..22;11]. |
| 12 to 24 | `generated` | 312 | 24x28 | Generado con bloques verificados: STACK 12->12 + 12x(1->2). |
| 13 to 1 | `generated` | 160 | 19x22 | Generado con bloques verificados: REVERSED K1 P=16 nl=0 dead=[0..11;12]. |
| 13 to 2 | `generated` | 196 | 19x25 | Generado con bloques verificados: REVERSED SQ(2) + K1 P=16 nl=0 dead=[0..10;11]. |
| 13 to 3 | `generated` | 225 | 19x31 | Generado con bloques verificados: REVERSED SQ(3) + K1 P=16 nl=0 dead=[0..9;10]. |
| 13 to 4 | `generated` | 235 | 19x31 | Generado con bloques verificados: REVERSED SQ(4) + K1 P=16 nl=0 dead=[0..8;9]. |
| 13 to 5 | `generated` | 271 | 19x34 | Generado con bloques verificados: REVERSED SQ(5) + K1 P=16 nl=0 dead=[0..7;8]. |
| 13 to 6 | `generated` | 300 | 19x33 | Generado con bloques verificados: REVERSED SQ(6) + K1 P=16 nl=1 dead=[6..12;7]. |
| 13 to 7 | `generated` | 158 | 15x15 | Generado con bloques verificados: REVERSED LIB. |
| 13 to 8 | `generated` | 156 | 15x15 | Generado con bloques verificados: REVERSED LIB. |
| 13 to 9 | `generated` | 409 | 19x36 | Generado con bloques verificados: REVERSED SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12]. |
| 13 to 10 | `generated` | 427 | 19x37 | Generado con bloques verificados: REVERSED SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 13 to 11 | `generated` | 491 | 19x41 | Generado con bloques verificados: REVERSED SQ(11) + K1 P=16 nl=1 dead=[11, 12]. |
| 13 to 12 | `generated` | 468 | 19x39 | Generado con bloques verificados: REVERSED SQ(12) + K1p P=16 loops=2+1. |
| 13 to 13 | `generated` | 293 | 19x20 | Generado con bloques verificados: LOOP(16-16) nl=1. |
| 13 to 14 | `generated` | 546 | 19x38 | Generado con bloques verificados: SQ(13) + K1p P=16 loops=1+1. |
| 13 to 15 | `generated` | 532 | 19x38 | Generado con bloques verificados: SQ(13) + K1 P=16 nl=0 dead=[0, 1]. |
| 13 to 16 | `generated` | 495 | 20x36 | Generado con bloques verificados: SQ(13) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 13 to 17 | `generated` | 1374 | 47x63 | Generado con bloques verificados: SQ(13) + K1 P=32 nl=7 dead=[13, 14, 15, 16]. |
| 13 to 18 | `generated` | 982 | 22x69 | Generado con bloques verificados: STACK 13->16 + 2x(8->9). |
| 13 to 19 | `generated` | 1323 | 45x61 | Generado con bloques verificados: SQ(13) + K1 P=32 nl=6 dead=[0, 1, 2, 3, 4, 5]. |
| 13 to 20 | `generated` | 824 | 22x60 | Generado con bloques verificados: STACK 13->16 + 2x(8->10). |
| 13 to 21 | `generated` | 984 | 49x58 | Generado con bloques verificados: STACK 13->14 + 7x(2->3). |
| 13 to 22 | `generated` | 1254 | 42x67 | Generado con bloques verificados: SQ(13) + K1 P=32 nl=0 dead=[0..8;9]. |
| 13 to 23 | `generated` | 1211 | 41x65 | Generado con bloques verificados: SQ(13) + K1 P=32 nl=0 dead=[0..9;10]. |
| 13 to 24 | `generated` | 802 | 24x55 | Generado con bloques verificados: STACK 13->16 + 4x(4->6). |
| 14 to 1 | `generated` | 69 | 14x11 | Generado con bloques verificados: DSTACK 2x(7->1) + 2->1. |
| 14 to 2 | `generated` | 70 | 14x11 | Generado con bloques verificados: DSTACK 2x(7->1) + 2->2. |
| 14 to 3 | `generated` | 114 | 14x14 | Generado con bloques verificados: DSTACK 7x(2->1) + 7->3. |
| 14 to 4 | `generated` | 115 | 14x15 | Generado con bloques verificados: REVERSED STACK 4->7 + 7x(1->2). |
| 14 to 5 | `generated` | 158 | 14x21 | Generado con bloques verificados: REVERSED STACK 5->7 + 7x(1->2). |
| 14 to 6 | `generated` | 157 | 14x20 | Generado con bloques verificados: REVERSED STACK 6->7 + 7x(1->2). |
| 14 to 7 | `generated` | 141 | 14x20 | Generado con bloques verificados: REVERSED STACK 7->7 + 7x(1->2). |
| 14 to 8 | `generated` | 310 | 18x32 | Generado con bloques verificados: REVERSED SQ(8) + K1 P=16 nl=0 dead=[8, 9, 10, 11, 12, 13]. |
| 14 to 9 | `generated` | 373 | 18x34 | Generado con bloques verificados: REVERSED SQ(9) + K1 P=16 nl=1 dead=[0, 1, 2, 3, 4]. |
| 14 to 10 | `generated` | 390 | 18x35 | Generado con bloques verificados: REVERSED SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2, 3]. |
| 14 to 11 | `generated` | 453 | 18x39 | Generado con bloques verificados: REVERSED SQ(11) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 14 to 12 | `generated` | 429 | 18x37 | Generado con bloques verificados: REVERSED SQ(12) + K1p P=16 loops=1+1. |
| 14 to 13 | `generated` | 546 | 19x38 | Generado con bloques verificados: REVERSED SQ(13) + K1p P=16 loops=1+1. |
| 14 to 14 | `generated` | 255 | 18x18 | Generado con bloques verificados: LOOP(16-16) nl=1. |
| 14 to 15 | `generated` | 502 | 19x36 | Generado con bloques verificados: SQ(14) + K1p P=16 loops=0+1. |
| 14 to 16 | `generated` | 458 | 18x34 | Generado con bloques verificados: SQ(14) + K1 P=16 nl=0 dead=[0, 1]. |
| 14 to 17 | `generated` | 1367 | 47x61 | Generado con bloques verificados: SQ(14) + K1 P=32 nl=7 dead=[0, 1, 2]. |
| 14 to 18 | `generated` | 790 | 24x52 | Generado con bloques verificados: STACK 14->14 + 2x(7->9). |
| 14 to 19 | `generated` | 1307 | 45x59 | Generado con bloques verificados: SQ(14) + K1 P=32 nl=6 dead=[14, 15, 16, 17, 18]. |
| 14 to 20 | `generated` | 614 | 20x44 | Generado con bloques verificados: STACK 14->14 + 2x(7->10). |
| 14 to 21 | `generated` | 693 | 49x38 | Generado con bloques verificados: STACK 14->14 + 7x(2->3). |
| 14 to 22 | `generated` | 983 | 26x71 | Generado con bloques verificados: STACK 14->14 + 2x(7->11). |
| 14 to 23 | `generated` | 1195 | 41x63 | Generado con bloques verificados: SQ(14) + K1 P=32 nl=0 dead=[0..8;9]. |
| 14 to 24 | `generated` | 765 | 24x53 | Generado con bloques verificados: STACK 14->16 + 4x(4->6). |
| 15 to 1 | `generated` | 98 | 17x18 | Generado con bloques verificados: REVERSED K1 P=16 nl=0 dead=[0..13;14]. |
| 15 to 2 | `generated` | 109 | 17x21 | Generado con bloques verificados: REV(K1 P=16 nl=0 dead=[0..12;13]) + SQ(2). |
| 15 to 3 | `generated` | 136 | 17x27 | Generado con bloques verificados: REV(K1 P=16 nl=0 dead=[0..11;12]) + SQ(3). |
| 15 to 4 | `generated` | 165 | 17x27 | Generado con bloques verificados: REVERSED SQ(4) + K1 P=16 nl=0 dead=[0..10;11]. |
| 15 to 5 | `generated` | 199 | 17x30 | Generado con bloques verificados: REVERSED SQ(5) + K1 P=16 nl=0 dead=[0..9;10]. |
| 15 to 6 | `raynquist` | 141 | 15x13 | Fuente: libro de balanceadores de Raynquist (fall 2025), '15-6 balancer'. |
| 15 to 7 | `generated` | 227 | 17x32 | Generado con bloques verificados: REVERSED SQ(7) + K1 P=16 nl=0 dead=[0..7;8]. |
| 15 to 8 | `generated` | 274 | 17x30 | Generado con bloques verificados: REVERSED SQ(8) + K1 P=16 nl=0 dead=[8..14;7]. |
| 15 to 9 | `generated` | 338 | 17x34 | Generado con bloques verificados: REVERSED SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12, 13, 14]. |
| 15 to 10 | `raynquist` | 206 | 15x19 | Fuente: libro de balanceadores de Raynquist (fall 2025), '15-10 balancer'. |
| 15 to 11 | `generated` | 418 | 17x39 | Generado con bloques verificados: REVERSED SQ(11) + K1 P=16 nl=1 dead=[11, 12, 13, 14]. |
| 15 to 12 | `generated` | 415 | 17x37 | Generado con bloques verificados: REVERSED SQ(12) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 15 to 13 | `generated` | 532 | 19x38 | Generado con bloques verificados: REVERSED SQ(13) + K1 P=16 nl=0 dead=[0, 1]. |
| 15 to 14 | `generated` | 502 | 19x36 | Generado con bloques verificados: REVERSED SQ(14) + K1p P=16 loops=0+1. |
| 15 to 15 | `generated` | 249 | 17x18 | Generado con bloques verificados: LOOP(16-16) nl=0. |
| 15 to 16 | `generated` | 459 | 18x34 | Generado con bloques verificados: SQ(15) + K1 P=16 nl=0 dead=[0]. |
| 15 to 17 | `generated` | 1364 | 47x61 | Generado con bloques verificados: SQ(15) + K1 P=32 nl=7 dead=[15, 16]. |
| 15 to 18 | `generated` | 701 | 24x44 | Generado con bloques verificados: STACK 15->15 + 3x(5->6). |
| 15 to 19 | `generated` | 1313 | 45x59 | Generado con bloques verificados: SQ(15) + K1 P=32 nl=6 dead=[0, 1, 2, 3]. |
| 15 to 20 | `generated` | 700 | 35x40 | Generado con bloques verificados: STACK 15->15 + 5x(3->4). |
| 15 to 21 | `generated` | 766 | 27x45 | Generado con bloques verificados: STACK 15->15 + 3x(5->7). |
| 15 to 22 | `generated` | 1230 | 26x86 | Generado con bloques verificados: STACK 15->16 + 2x(8->11). |
| 15 to 23 | `generated` | 1192 | 41x63 | Generado con bloques verificados: SQ(15) + K1 P=32 nl=0 dead=[0..7;8]. |
| 15 to 24 | `generated` | 580 | 24x37 | Generado con bloques verificados: STACK 15->15 + 3x(5->8). |
| 16 to 1 | `generated` | 49 | 16x10 | Generado con bloques verificados: DSTACK 2x(8->1) + 2->1. |
| 16 to 2 | `generated` | 50 | 16x10 | Generado con bloques verificados: DSTACK 2x(8->1) + 2->2. |
| 16 to 3 | `generated` | 88 | 16x14 | Generado con bloques verificados: REVERSED STACK 3->4 + 4x(1->4). |
| 16 to 4 | `generated` | 79 | 16x15 | Generado con bloques verificados: REVERSED STACK 4->4 + 4x(1->4). |
| 16 to 5 | `generated` | 163 | 16x21 | Generado con bloques verificados: REVERSED STACK 5->8 + 8x(1->2). |
| 16 to 6 | `generated` | 156 | 16x20 | Generado con bloques verificados: DSTACK 8x(2->1) + 8->6. |
| 16 to 7 | `generated` | 177 | 16x23 | Generado con bloques verificados: REVERSED STACK 7->8 + 8x(1->2). |
| 16 to 8 | `raynquist` | 286 | 16x24 | Fuente: libro de balanceadores de Raynquist (fall 2025), '16-8 TU balancer'. |
| 16 to 9 | `generated` | 303 | 16x32 | Generado con bloques verificados: REVERSED SQ(9) + K1 P=16 nl=0 dead=[0..15;7]. |
| 16 to 10 | `raynquist` | 197 | 16x22 | Fuente: libro de balanceadores de Raynquist (fall 2025), '16-10 balancer'. |
| 16 to 11 | `generated` | 383 | 16x37 | Generado con bloques verificados: REVERSED SQ(11) + K1 P=16 nl=0 dead=[11, 12, 13, 14, 15]. |
| 16 to 12 | `generated` | 354 | 16x35 | Generado con bloques verificados: REVERSED SQ(12) + K1 P=16 nl=0 dead=[12, 13, 14, 15]. |
| 16 to 13 | `generated` | 495 | 20x36 | Generado con bloques verificados: REVERSED SQ(13) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 16 to 14 | `generated` | 458 | 18x34 | Generado con bloques verificados: REVERSED SQ(14) + K1 P=16 nl=0 dead=[0, 1]. |
| 16 to 15 | `generated` | 459 | 18x34 | Generado con bloques verificados: REVERSED SQ(15) + K1 P=16 nl=0 dead=[0]. |
| 16 to 16 | `raynquist` | 211 | 16x16 | Fuente: libro de balanceadores de Raynquist (fall 2025), '16-16 balancer'. |
| 16 to 17 | `generated` | 1351 | 47x59 | Generado con bloques verificados: SQ(16) + K1 P=32 nl=7 dead=[0]. |
| 16 to 18 | `generated` | 698 | 22x49 | Generado con bloques verificados: STACK 16->16 + 2x(8->9). |
| 16 to 19 | `generated` | 1300 | 45x57 | Generado con bloques verificados: SQ(16) + K1 P=32 nl=6 dead=[0, 1, 2]. |
| 16 to 20 | `generated` | 540 | 20x40 | Generado con bloques verificados: STACK 16->16 + 2x(8->10). |
| 16 to 21 | `generated` | 1200 | 27x76 | Generado con bloques verificados: STACK 16->18 + 3x(6->7). |
| 16 to 22 | `generated` | 982 | 26x68 | Generado con bloques verificados: STACK 16->16 + 2x(8->11). |
| 16 to 23 | `generated` | 1219 | 41x53 | Generado con bloques verificados: SQ(16) + K1 P=32 nl=4 dead=[0..6;7]. |
| 16 to 24 | `generated` | 518 | 24x35 | Generado con bloques verificados: STACK 16->16 + 4x(4->6). |
| 17 to 1 | `generated` | 875 | 47x57 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..15;16]) + SQ(1). |
| 17 to 2 | `generated` | 950 | 47x46 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[2..16;15]) + SQ(2). |
| 17 to 3 | `generated` | 979 | 47x52 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[3..16;14]) + SQ(3). |
| 17 to 4 | `generated` | 987 | 47x52 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[4..16;13]) + SQ(4). |
| 17 to 5 | `generated` | 1023 | 47x55 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[5..16;12]) + SQ(5). |
| 17 to 6 | `generated` | 1056 | 47x56 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[6..16;11]) + SQ(6). |
| 17 to 7 | `generated` | 1075 | 47x57 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[7..16;10]) + SQ(7). |
| 17 to 8 | `generated` | 1081 | 47x55 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[8..16;9]) + SQ(8). |
| 17 to 9 | `generated` | 1145 | 47x59 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[9..16;8]) + SQ(9). |
| 17 to 10 | `generated` | 1219 | 47x60 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[0..16;7]) + SQ(10). |
| 17 to 11 | `generated` | 1275 | 47x64 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[11, 12, 13, 14, 15, 16]) + SQ(11). |
| 17 to 12 | `generated` | 1264 | 47x62 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[0, 1, 2, 3, 4]) + SQ(12). |
| 17 to 13 | `generated` | 1357 | 47x63 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[13, 14, 15, 16]) + SQ(13). |
| 17 to 14 | `generated` | 1350 | 47x61 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[0, 1, 2]) + SQ(14). |
| 17 to 15 | `generated` | 1347 | 47x61 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[15, 16]) + SQ(15). |
| 17 to 16 | `generated` | 1334 | 47x59 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[0]) + SQ(16). |
| 17 to 17 | `generated` | 1144 | 47x43 | Generado con bloques verificados: LOOP(32-32) nl=7. |
| 17 to 18 | `generated` | 2248 | 48x84 | Generado con bloques verificados: SQ(17) + K1 P=32 nl=7 dead=[0]. |
| 17 to 19 | `generated` | 2220 | 47x84 | Generado con bloques verificados: SQ(17) + K1 P=32 nl=6 dead=[0, 1]. |
| 17 to 20 | `generated` | 2198 | 48x82 | Generado con bloques verificados: SQ(17) + K1 P=32 nl=6 dead=[0, 1, 2]. |
| 17 to 21 | `generated` | 2174 | 47x82 | Generado con bloques verificados: SQ(17) + K1 P=32 nl=5 dead=[17, 18, 19, 20]. |
| 17 to 22 | `generated` | 2173 | 49x84 | Generado con bloques verificados: SQ(17) + K1p P=32 loops=7+3. |
| 17 to 23 | `generated` | 2139 | 47x80 | Generado con bloques verificados: SQ(17) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4, 5]. |
| 17 to 24 | `generated` | 2097 | 48x78 | Generado con bloques verificados: SQ(17) + K1 P=32 nl=4 dead=[0..6;7]. |
| 18 to 1 | `generated` | 90 | 18x13 | Generado con bloques verificados: DSTACK 3x(6->1) + 3->1. |
| 18 to 2 | `generated` | 97 | 18x14 | Generado con bloques verificados: DSTACK 3x(6->1) + 3->2. |
| 18 to 3 | `generated` | 102 | 18x16 | Generado con bloques verificados: DSTACK 3x(6->1) + 3->3. |
| 18 to 4 | `generated` | 171 | 18x19 | Generado con bloques verificados: DSTACK 9x(2->1) + 9->4. |
| 18 to 5 | `generated` | 210 | 18x25 | Generado con bloques verificados: DSTACK 9x(2->1) + 9->5. |
| 18 to 6 | `generated` | 193 | 18x23 | Generado con bloques verificados: DSTACK 9x(2->1) + 9->6. |
| 18 to 7 | `generated` | 259 | 18x25 | Generado con bloques verificados: DSTACK 9x(2->1) + 9->7. |
| 18 to 8 | `generated` | 229 | 18x23 | Generado con bloques verificados: REVERSED STACK 8->9 + 9x(1->2). |
| 18 to 9 | `generated` | 228 | 18x23 | Generado con bloques verificados: REVERSED STACK 9->9 + 9x(1->2). |
| 18 to 10 | `generated` | 419 | 18x37 | Generado con bloques verificados: DSTACK 3x(6->4) + 12->10. |
| 18 to 11 | `generated` | 605 | 18x55 | Generado con bloques verificados: DSTACK 3x(6->4) + 12->11. |
| 18 to 12 | `generated` | 398 | 18x34 | Generado con bloques verificados: DSTACK 3x(6->4) + 12->12. |
| 18 to 13 | `generated` | 976 | 22x69 | Generado con bloques verificados: REVERSED STACK 13->16 + 2x(8->9). |
| 18 to 14 | `generated` | 811 | 24x53 | Generado con bloques verificados: DSTACK 2x(9->7) + 14->14. |
| 18 to 15 | `generated` | 693 | 24x44 | Generado con bloques verificados: REVERSED STACK 15->15 + 3x(5->6). |
| 18 to 16 | `generated` | 692 | 22x49 | Generado con bloques verificados: REVERSED STACK 16->16 + 2x(8->9). |
| 18 to 17 | `generated` | 2230 | 47x84 | Generado con bloques verificados: REV(K1 P=32 nl=7 dead=[0]) + SQ(17). |
| 18 to 18 | `generated` | 1125 | 46x41 | Generado con bloques verificados: LOOP(32-32) nl=7. |
| 18 to 19 | `generated` | 2210 | 46x82 | Generado con bloques verificados: SQ(18) + K1 P=32 nl=6 dead=[0]. |
| 18 to 20 | `generated` | 1706 | 46x83 | Generado con bloques verificados: STACK 18->18 + 2x(9->10). |
| 18 to 21 | `generated` | 1647 | 46x68 | Generado con bloques verificados: STACK 18->18 + 3x(6->7). |
| 18 to 22 | `generated` | 2026 | 46x98 | Generado con bloques verificados: STACK 18->18 + 2x(9->11). |
| 18 to 23 | `generated` | 2129 | 46x78 | Generado con bloques verificados: SQ(18) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 18 to 24 | `generated` | 1447 | 46x60 | Generado con bloques verificados: STACK 18->18 + 3x(6->8). |
| 19 to 1 | `generated` | 796 | 45x53 | Generado con bloques verificados: REVERSED K1 P=32 nl=0 dead=[0..17;18]. |
| 19 to 2 | `generated` | 813 | 45x56 | Generado con bloques verificados: REVERSED SQ(2) + K1 P=32 nl=0 dead=[0..16;17]. |
| 19 to 3 | `generated` | 844 | 45x62 | Generado con bloques verificados: REVERSED SQ(3) + K1 P=32 nl=0 dead=[0..15;16]. |
| 19 to 4 | `generated` | 935 | 45x50 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0..14;15]) + SQ(4). |
| 19 to 5 | `generated` | 971 | 45x53 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0..13;14]) + SQ(5). |
| 19 to 6 | `generated` | 983 | 45x54 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[6..18;13]) + SQ(6). |
| 19 to 7 | `generated` | 1023 | 45x55 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0..11;12]) + SQ(7). |
| 19 to 8 | `generated` | 1028 | 45x53 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[8..18;11]) + SQ(8). |
| 19 to 9 | `generated` | 1093 | 45x57 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0..9;10]) + SQ(9). |
| 19 to 10 | `generated` | 1113 | 45x58 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[10..18;9]) + SQ(10). |
| 19 to 11 | `generated` | 1222 | 45x62 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0..7;8]) + SQ(11). |
| 19 to 12 | `generated` | 1211 | 45x60 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0..6;7]) + SQ(12). |
| 19 to 13 | `generated` | 1304 | 45x61 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0, 1, 2, 3, 4, 5]) + SQ(13). |
| 19 to 14 | `generated` | 1288 | 45x59 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[14, 15, 16, 17, 18]) + SQ(14). |
| 19 to 15 | `generated` | 1294 | 45x59 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0, 1, 2, 3]) + SQ(15). |
| 19 to 16 | `generated` | 1281 | 45x57 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0, 1, 2]) + SQ(16). |
| 19 to 17 | `generated` | 2201 | 47x84 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0, 1]) + SQ(17). |
| 19 to 18 | `generated` | 2191 | 46x82 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0]) + SQ(18). |
| 19 to 19 | `generated` | 1107 | 45x41 | Generado con bloques verificados: LOOP(32-32) nl=6. |
| 19 to 20 | `generated` | 2173 | 46x80 | Generado con bloques verificados: SQ(19) + K1 P=32 nl=6 dead=[0]. |
| 19 to 21 | `generated` | 2149 | 45x80 | Generado con bloques verificados: SQ(19) + K1 P=32 nl=5 dead=[19, 20]. |
| 19 to 22 | `generated` | 2139 | 47x82 | Generado con bloques verificados: SQ(19) + K1p P=32 loops=7+3. |
| 19 to 23 | `generated` | 2114 | 45x78 | Generado con bloques verificados: SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3]. |
| 19 to 24 | `generated` | 2072 | 46x76 | Generado con bloques verificados: SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 20 to 1 | `generated` | 87 | 20x13 | Generado con bloques verificados: DSTACK 5x(4->1) + 5->1. |
| 20 to 2 | `generated` | 93 | 20x14 | Generado con bloques verificados: DSTACK 5x(4->1) + 5->2. |
| 20 to 3 | `generated` | 119 | 20x16 | Generado con bloques verificados: DSTACK 5x(4->1) + 5->3. |
| 20 to 4 | `generated` | 119 | 20x16 | Generado con bloques verificados: REVERSED STACK 4->5 + 5x(1->4). |
| 20 to 5 | `generated` | 124 | 20x18 | Generado con bloques verificados: REVERSED STACK 5->5 + 5x(1->4). |
| 20 to 6 | `generated` | 250 | 20x25 | Generado con bloques verificados: DSTACK 4x(5->2) + 8->6. |
| 20 to 7 | `generated` | 271 | 20x28 | Generado con bloques verificados: DSTACK 4x(5->2) + 8->7. |
| 20 to 8 | `generated` | 229 | 20x24 | Generado con bloques verificados: REVERSED STACK 8->10 + 10x(1->2). |
| 20 to 9 | `generated` | 302 | 20x31 | Generado con bloques verificados: REVERSED STACK 9->10 + 10x(1->2). |
| 20 to 10 | `generated` | 252 | 20x25 | Generado con bloques verificados: REVERSED STACK 10->10 + 10x(1->2). |
| 20 to 11 | `generated` | 710 | 20x61 | Generado con bloques verificados: REVERSED STACK 11->16 + 2x(8->10). |
| 20 to 12 | `generated` | 646 | 32x46 | Generado con bloques verificados: DSTACK 4x(5->3) + 12->12. |
| 20 to 13 | `generated` | 822 | 22x60 | Generado con bloques verificados: REVERSED STACK 13->16 + 2x(8->10). |
| 20 to 14 | `generated` | 787 | 20x58 | Generado con bloques verificados: DSTACK 2x(10->8) + 16->14. |
| 20 to 15 | `raynquist` | 277 | 20x19 | Fuente: libro de balanceadores de Raynquist (fall 2025), '20-15 balancer'. |
| 20 to 16 | `generated` | 538 | 20x40 | Generado con bloques verificados: REVERSED STACK 16->16 + 2x(8->10). |
| 20 to 17 | `generated` | 2178 | 47x82 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0, 1, 2]) + SQ(17). |
| 20 to 18 | `generated` | 1691 | 46x84 | Generado con bloques verificados: DSTACK 2x(10->9) + 18->18. |
| 20 to 19 | `generated` | 2153 | 45x80 | Generado con bloques verificados: REV(K1 P=32 nl=6 dead=[0]) + SQ(19). |
| 20 to 20 | `generated` | 1089 | 44x39 | Generado con bloques verificados: LOOP(32-32) nl=6. |
| 20 to 21 | `generated` | 2140 | 44x78 | Generado con bloques verificados: SQ(20) + K1 P=32 nl=5 dead=[0]. |
| 20 to 22 | `generated` | 2052 | 44x98 | Generado con bloques verificados: STACK 20->20 + 2x(10->11). |
| 20 to 23 | `generated` | 2102 | 44x78 | Generado con bloques verificados: SQ(20) + K1p P=32 loops=6+3. |
| 20 to 24 | `generated` | 1753 | 44x76 | Generado con bloques verificados: STACK 20->20 + 4x(5->6). |
| 21 to 1 | `generated` | 117 | 21x14 | Generado con bloques verificados: DSTACK 3x(7->1) + 3->1. |
| 21 to 2 | `generated` | 124 | 21x15 | Generado con bloques verificados: DSTACK 3x(7->1) + 3->2. |
| 21 to 3 | `generated` | 129 | 21x17 | Generado con bloques verificados: DSTACK 3x(7->1) + 3->3. |
| 21 to 4 | `generated` | 289 | 24x27 | Generado con bloques verificados: DSTACK 3x(7->2) + 6->4. |
| 21 to 5 | `generated` | 323 | 24x31 | Generado con bloques verificados: DSTACK 3x(7->2) + 6->5. |
| 21 to 6 | `generated` | 302 | 24x29 | Generado con bloques verificados: DSTACK 3x(7->2) + 6->6. |
| 21 to 7 | `generated` | 390 | 28x33 | Generado con bloques verificados: DSTACK 7x(3->1) + 7->7. |
| 21 to 8 | `generated` | 466 | 27x35 | Generado con bloques verificados: DSTACK 3x(7->3) + 9->8. |
| 21 to 9 | `generated` | 465 | 27x35 | Generado con bloques verificados: DSTACK 3x(7->3) + 9->9. |
| 21 to 10 | `generated` | 558 | 27x43 | Generado con bloques verificados: DSTACK 3x(7->4) + 12->10. |
| 21 to 11 | `generated` | 744 | 27x61 | Generado con bloques verificados: DSTACK 3x(7->4) + 12->11. |
| 21 to 12 | `generated` | 537 | 27x40 | Generado con bloques verificados: DSTACK 3x(7->4) + 12->12. |
| 21 to 13 | `generated` | 974 | 35x61 | Generado con bloques verificados: DSTACK 7x(3->2) + 14->13. |
| 21 to 14 | `generated` | 683 | 35x41 | Generado con bloques verificados: DSTACK 7x(3->2) + 14->14. |
| 21 to 15 | `generated` | 755 | 27x46 | Generado con bloques verificados: DSTACK 3x(7->5) + 15->15. |
| 21 to 16 | `generated` | 1189 | 27x77 | Generado con bloques verificados: DSTACK 3x(7->6) + 18->16. |
| 21 to 17 | `generated` | 2153 | 49x82 | Generado con bloques verificados: REV(K1 P=32 nl=5 dead=[17, 18, 19, 20]) + SQ(17). |
| 21 to 18 | `generated` | 1635 | 46x68 | Generado con bloques verificados: REVERSED STACK 18->18 + 3x(6->7). |
| 21 to 19 | `generated` | 2128 | 47x80 | Generado con bloques verificados: REV(K1 P=32 nl=5 dead=[19, 20]) + SQ(19). |
| 21 to 20 | `generated` | 2119 | 44x78 | Generado con bloques verificados: REV(K1 P=32 nl=5 dead=[0]) + SQ(20). |
| 21 to 21 | `generated` | 1075 | 43x39 | Generado con bloques verificados: LOOP(32-32) nl=5. |
| 21 to 22 | `generated` | 2131 | 51x84 | Generado con bloques verificados: SQ(21) + K1p P=32 loops=9+1. |
| 21 to 23 | `generated` | 2097 | 47x80 | Generado con bloques verificados: SQ(21) + K1p P=32 loops=7+2. |
| 21 to 24 | `generated` | 1456 | 43x62 | Generado con bloques verificados: STACK 21->21 + 3x(7->8). |
| 22 to 1 | `generated` | 204 | 22x29 | Generado con bloques verificados: REVERSED STACK 1->11 + 11x(1->2). |
| 22 to 2 | `generated` | 227 | 22x32 | Generado con bloques verificados: REVERSED STACK 2->11 + 11x(1->2). |
| 22 to 3 | `generated` | 254 | 22x38 | Generado con bloques verificados: REVERSED STACK 3->11 + 11x(1->2). |
| 22 to 4 | `generated` | 259 | 22x38 | Generado con bloques verificados: REVERSED STACK 4->11 + 11x(1->2). |
| 22 to 5 | `generated` | 293 | 22x41 | Generado con bloques verificados: REVERSED STACK 5->11 + 11x(1->2). |
| 22 to 6 | `generated` | 354 | 22x42 | Generado con bloques verificados: REVERSED STACK 6->11 + 11x(1->2). |
| 22 to 7 | `generated` | 371 | 22x43 | Generado con bloques verificados: REVERSED STACK 7->11 + 11x(1->2). |
| 22 to 8 | `generated` | 381 | 22x41 | Generado con bloques verificados: REVERSED STACK 8->11 + 11x(1->2). |
| 22 to 9 | `generated` | 443 | 22x45 | Generado con bloques verificados: REVERSED STACK 9->11 + 11x(1->2). |
| 22 to 10 | `generated` | 324 | 22x31 | Generado con bloques verificados: DSTACK 11x(2->1) + 11->10. |
| 22 to 11 | `generated` | 318 | 22x29 | Generado con bloques verificados: REVERSED STACK 11->11 + 11x(1->2). |
| 22 to 12 | `generated` | 861 | 26x71 | Generado con bloques verificados: DSTACK 2x(11->6) + 12->12. |
| 22 to 13 | `generated` | 1232 | 42x67 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..8;9]) + SQ(13). |
| 22 to 14 | `generated` | 972 | 26x72 | Generado con bloques verificados: DSTACK 2x(11->7) + 14->14. |
| 22 to 15 | `generated` | 946 | 26x64 | Generado con bloques verificados: DSTACK 2x(11->10) + 20->15. |
| 22 to 16 | `generated` | 972 | 26x69 | Generado con bloques verificados: DSTACK 2x(11->8) + 16->16. |
| 22 to 17 | `generated` | 2134 | 47x80 | Generado con bloques verificados: REV(K1 P=32 nl=5 dead=[0, 1, 2, 3, 4]) + SQ(17). |
| 22 to 18 | `generated` | 2015 | 46x99 | Generado con bloques verificados: DSTACK 2x(11->9) + 18->18. |
| 22 to 19 | `generated` | 2109 | 45x78 | Generado con bloques verificados: REV(K1 P=32 nl=5 dead=[0, 1, 2]) + SQ(19). |
| 22 to 20 | `generated` | 1740 | 44x84 | Generado con bloques verificados: DSTACK 2x(11->10) + 20->20. |
| 22 to 21 | `generated` | 2089 | 43x76 | Generado con bloques verificados: REV(K1 P=32 nl=5 dead=[0]) + SQ(21). |
| 22 to 22 | `generated` | 1083 | 42x37 | Generado con bloques verificados: LOOP(32-32) nl=5. |
| 22 to 23 | `generated` | 2038 | 42x74 | Generado con bloques verificados: SQ(22) + K1 P=32 nl=4 dead=[0]. |
| 22 to 24 | `generated` | 1992 | 42x72 | Generado con bloques verificados: SQ(22) + K1 P=32 nl=4 dead=[0, 1]. |
| 23 to 1 | `generated` | 616 | 41x45 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..21;22]) + SQ(1). |
| 23 to 2 | `generated` | 628 | 41x48 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..20;21]) + SQ(2). |
| 23 to 3 | `generated` | 657 | 41x54 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..19;20]) + SQ(3). |
| 23 to 4 | `generated` | 687 | 41x54 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..18;19]) + SQ(4). |
| 23 to 5 | `generated` | 723 | 41x57 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..17;18]) + SQ(5). |
| 23 to 6 | `generated` | 736 | 41x58 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..16;17]) + SQ(6). |
| 23 to 7 | `generated` | 755 | 41x59 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..15;16]) + SQ(7). |
| 23 to 8 | `generated` | 913 | 41x49 | Generado con bloques verificados: REVERSED SQ(8) + K1 P=32 nl=4 dead=[8..22;15]. |
| 23 to 9 | `generated` | 983 | 41x53 | Generado con bloques verificados: REVERSED SQ(9) + K1 P=32 nl=4 dead=[0..13;14]. |
| 23 to 10 | `generated` | 1004 | 41x54 | Generado con bloques verificados: REVERSED SQ(10) + K1 P=32 nl=4 dead=[0..12;13]. |
| 23 to 11 | `generated` | 1058 | 41x58 | Generado con bloques verificados: REVERSED SQ(11) + K1 P=32 nl=4 dead=[0..11;12]. |
| 23 to 12 | `generated` | 1063 | 41x56 | Generado con bloques verificados: REVERSED SQ(12) + K1 P=32 nl=4 dead=[12..22;11]. |
| 23 to 13 | `generated` | 1188 | 41x65 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..9;10]) + SQ(13). |
| 23 to 14 | `generated` | 1172 | 41x63 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..8;9]) + SQ(14). |
| 23 to 15 | `generated` | 1169 | 41x63 | Generado con bloques verificados: REV(K1 P=32 nl=0 dead=[0..7;8]) + SQ(15). |
| 23 to 16 | `generated` | 1171 | 41x53 | Generado con bloques verificados: REVERSED SQ(16) + K1 P=32 nl=4 dead=[0..6;7]. |
| 23 to 17 | `generated` | 2087 | 47x80 | Generado con bloques verificados: REVERSED SQ(17) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4, 5]. |
| 23 to 18 | `generated` | 2077 | 46x78 | Generado con bloques verificados: REVERSED SQ(18) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 23 to 19 | `generated` | 2062 | 45x78 | Generado con bloques verificados: REVERSED SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3]. |
| 23 to 20 | `generated` | 2074 | 45x76 | Generado con bloques verificados: REV(K1 P=32 nl=4 dead=[20, 21, 22]) + SQ(20). |
| 23 to 21 | `generated` | 2065 | 43x76 | Generado con bloques verificados: REV(K1 P=32 nl=4 dead=[0, 1]) + SQ(21). |
| 23 to 22 | `generated` | 1986 | 42x74 | Generado con bloques verificados: REVERSED SQ(22) + K1 P=32 nl=4 dead=[0]. |
| 23 to 23 | `generated` | 1069 | 41x37 | Generado con bloques verificados: LOOP(32-32) nl=4. |
| 23 to 24 | `generated` | 1981 | 42x72 | Generado con bloques verificados: SQ(23) + K1 P=32 nl=4 dead=[0]. |
| 24 to 1 | `generated` | 87 | 24x13 | Generado con bloques verificados: DSTACK 3x(8->1) + 3->1. |
| 24 to 2 | `generated` | 94 | 24x14 | Generado con bloques verificados: DSTACK 3x(8->1) + 3->2. |
| 24 to 3 | `generated` | 99 | 24x16 | Generado con bloques verificados: DSTACK 3x(8->1) + 3->3. |
| 24 to 4 | `generated` | 131 | 24x17 | Generado con bloques verificados: DSTACK 4x(6->1) + 4->4. |
| 24 to 5 | `generated` | 167 | 24x22 | Generado con bloques verificados: REVERSED STACK 5->6 + 6x(1->4). |
| 24 to 6 | `generated` | 146 | 24x20 | Generado con bloques verificados: REVERSED STACK 6->6 + 6x(1->4). |
| 24 to 7 | `generated` | 353 | 24x30 | Generado con bloques verificados: DSTACK 3x(8->3) + 9->7. |
| 24 to 8 | `generated` | 323 | 24x28 | Generado con bloques verificados: DSTACK 3x(8->3) + 9->8. |
| 24 to 9 | `generated` | 322 | 24x28 | Generado con bloques verificados: DSTACK 3x(8->3) + 9->9. |
| 24 to 10 | `generated` | 333 | 24x31 | Generado con bloques verificados: DSTACK 12x(2->1) + 12->10. |
| 24 to 11 | `generated` | 515 | 24x49 | Generado con bloques verificados: REVERSED STACK 11->12 + 12x(1->2). |
| 24 to 12 | `generated` | 308 | 24x28 | Generado con bloques verificados: REVERSED STACK 12->12 + 12x(1->2). |
| 24 to 13 | `generated` | 806 | 24x55 | Generado con bloques verificados: DSTACK 4x(6->4) + 16->13. |
| 24 to 14 | `generated` | 769 | 24x53 | Generado con bloques verificados: DSTACK 4x(6->4) + 16->14. |
| 24 to 15 | `generated` | 576 | 24x37 | Generado con bloques verificados: REVERSED STACK 15->15 + 3x(5->8). |
| 24 to 16 | `generated` | 522 | 24x35 | Generado con bloques verificados: DSTACK 4x(6->4) + 16->16. |
| 24 to 17 | `generated` | 2093 | 48x78 | Generado con bloques verificados: REVERSED SQ(17) + K1 P=32 nl=4 dead=[0..6;7]. |
| 24 to 18 | `generated` | 1439 | 46x60 | Generado con bloques verificados: DSTACK 3x(8->6) + 18->18. |
| 24 to 19 | `generated` | 2068 | 46x76 | Generado con bloques verificados: REVERSED SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 24 to 20 | `generated` | 1572 | 44x71 | Generado con bloques verificados: DSTACK 2x(12->10) + 20->20. |
| 24 to 21 | `generated` | 1448 | 43x62 | Generado con bloques verificados: REVERSED STACK 21->21 + 3x(7->8). |
| 24 to 22 | `generated` | 1988 | 42x72 | Generado con bloques verificados: REVERSED SQ(22) + K1 P=32 nl=4 dead=[0, 1]. |
| 24 to 23 | `generated` | 1979 | 42x72 | Generado con bloques verificados: REVERSED SQ(23) + K1 P=32 nl=4 dead=[0]. |
| 24 to 24 | `generated` | 1055 | 40x35 | Generado con bloques verificados: LOOP(32-32) nl=4. |
