# Central nuclear de 40 reactores con energía solar y acumuladores

Central nuclear con 40 reactores en dos columnas de 20, 640 intercambiadores de calor y 1292 turbinas de vapor, con una potencia máxima calculada de 6240 MW. Es la v2 de la central de 40 reactores: no tiene el circuito de protección de la v1, y sus insertadores de combustible tienen una red propia, con paneles solares y acumuladores, separada de la red de las turbinas; el dueño del repositorio la recomienda en lugar de la v1.

- Archivo: [`nuclear-power-plant-40-reactors-v2.txt`](nuclear-power-plant-40-reactors-v2.txt) — cadena de blueprint; en el juego se llama `Nuclear power plant - 40 reactors v2`.
- Origen: diseño del dueño del repositorio, adaptado de un diseño ya existente, de autor desconocido; no se conoce ninguna licencia.
- Esta es siempre la versión actual de la v2; sus versiones anteriores quedan en el historial de git. La entrada `nuclear-power-plant-40-reactors-v1`, con circuito de protección, es otro diseño y sigue en el catálogo.

![Vista general, captura del juego](images/shot-1.webp)

## Qué contiene

| Elemento | Valor |
|---|---|
| Entidades | 8659 |
| Área | 370 × 159 casillas |
| Tubería térmica | 2294 |
| Tubería | 2403 |
| Tubería subterránea | 1205 |
| Turbina de vapor | 1292 |
| Intercambiador de calor | 640 |

## Lista de materiales

Todo lo que usa el blueprint, contado por el validador del catálogo a partir de la cadena:

| Elemento | Cantidad |
|---|---|
| Hormigón | 57.776 |
| Tubería | 2403 |
| Tubería térmica | 2294 |
| Turbina de vapor | 1292 |
| Tubería subterránea | 1205 |
| Hormigón con señal de peligro | 1054 |
| Intercambiador de calor | 640 |
| Poste eléctrico mediano | 465 |
| Insertador | 80 |
| Cisterna | 68 |
| Robopuerto | 44 |
| Cofre solicitador | 40 |
| Cofre proveedor activo | 40 |
| Reactor nuclear de fisión | 40 |
| Panel solar | 21 |
| Poste eléctrico grande | 19 |
| Acumulador | 7 |
| Bomba de fluidos | 1 |

Los cuatro bordes terminan en una franja de hormigón con señal de peligro de una casilla de ancho; justo por dentro de ella, y en todo el resto de la superficie, el suelo es de hormigón.

## Diferencias respecto a la v1

Comparación con `nuclear-power-plant-40-reactors-v1`, hecha por script sobre las dos cadenas:

| Elemento | v1 | v2 |
|---|---|---|
| Bomba de fluidos | 66 | 1 |
| Combinador comparador | 1 | 0 |
| Interruptor | 1 | 0 |
| Panel solar | 1 | 21 |
| Acumulador | 2 | 7 |
| Tubería | 2137 | 2403 |
| Tubería subterránea | 1321 | 1205 |
| Poste eléctrico mediano | 488 | 465 |

- Sin circuito de protección: la v2 no tiene el combinador comparador ni el interruptor de la v1, así que la base se conecta directamente a un poste eléctrico grande de la red de las turbinas.
- Una sola bomba de vapor: la v1 tenía 66 bombas de fluidos entre las cisternas y las turbinas, y la v2 tiene una. El vapor queda en dos mitades independientes, oeste y este, y la bomba única une una mitad con la otra (ver «Cómo se distribuye el vapor»).
- Una red propia para los insertadores: los 80 insertadores de combustible están en un grupo de postes separado del grupo de las turbinas, con 21 paneles solares y 7 acumuladores; la v1 tenía solo 1 panel solar y 2 acumuladores, para su combinador.
- Igual que la v1: los 40 reactores, los 640 intercambiadores de calor, las 1292 turbinas, las 68 cisternas, los 80 insertadores, los 44 robopuertos, los 80 cofres, las 64 entradas de agua y la lógica de ahorro de combustible (las condiciones de los insertadores son las mismas).

## Entradas

- Agua: 64 tuberías subterráneas, 32 en el borde norte y 32 en el borde sur. Conecta cada una a una fuente de agua; a plena potencia la central necesita unas 6430 unidades de agua por segundo (calculado: 10,3 por segundo en cada uno de los 624 intercambiadores de calor que hacen falta para 6240 MW).
- Combustible: 40 cofres solicitadores piden 10 células de combustible de uranio cada uno; los robots logísticos de los 44 robopuertos traen las células, y las células gastadas de combustible de uranio salen por los 40 cofres proveedores activos. El blueprint no trae robots: la red logística necesita robots logísticos, un cofre con células de combustible de uranio y un cofre que reciba las células gastadas.
- Base: conecta la base a uno de los 19 postes eléctricos grandes, que pertenecen al grupo de las turbinas, por ejemplo el del centro, a 12 casillas al norte del borde sur. No conectes la base a los postes de los insertadores de combustible ni de los paneles solares: eso pondría la demanda de la base sobre ellos y desharía la separación.
- Arranque: como en la v1, un reactor solo recibe combustible de su cofre después de que sale de él una célula gastada, así que pon a mano una célula de combustible de uranio en cada uno de los 40 reactores. Esto no se probó en esta versión: los insertadores de combustible funcionan con paneles solares y acumuladores, así que solo se mueven de día o mientras los acumuladores tengan carga.

## Consumo y producción

| Elemento | Por segundo |
|---|---|
| Energía eléctrica producida (máximo calculado) | hasta 6240 MW |
| Célula de combustible de uranio consumida | 0,2 (12 por minuto) |
| Célula gastada de combustible de uranio producida | 0,2 (12 por minuto) |
| Agua consumida | unas 6430 |

Valores calculados a plena potencia: 40 reactores de 40 MW con 116 bonificaciones por proximidad del 100 %, una célula de combustible por reactor cada 200 s y 10,3 unidades de agua por segundo en cada uno de los 624 intercambiadores de calor que hacen falta para 6240 MW. Nada de esto se midió en esta versión, ni tampoco el flujo de vapor con una sola bomba entre las dos mitades a plena potencia.

## Cómo se distribuye el vapor

En la v1 el vapor formaba una red única. En la v2 son dos mitades independientes, oeste y este, cada una con 320 intercambiadores de calor, 646 turbinas y 34 cisternas, todas alimentadas por la misma red de agua. La bomba única, cerca del borde norte y conectada a la red solar, lleva vapor de la mitad oeste a la este. Los 40 umbrales de ahorro de combustible leen una cisterna de la mitad este; el nivel de vapor de la mitad oeste no se vigila. Los recuentos se hicieron por script sobre la cadena, y el funcionamiento de esta disposición no se midió.

## Cómo la central ahorra combustible

En el juego base, un reactor con combustible quema sin parar, aunque nadie use el calor. Aquí cada reactor solo recibe una célula nueva después de que se saca la gastada, y los 40 insertadores que sacan las células gastadas están conectados por un cable verde a una cisterna de la columna este, cerca del borde sur. Cada par de reactores tiene un umbral: el primero solo se reabastece mientras esa cisterna tenga menos de 24.000 unidades de vapor, el siguiente menos de 23.000, y así sucesivamente, de 1000 en 1000, hasta 5000 en el último par. Esa cisterna tiene que seguir en la red de vapor.

## Cómo la red propia mantiene los insertadores

En la v1, las bombas de fluidos que llevaban el vapor y los insertadores de combustible funcionaban con la energía de la propia central, y por eso un interruptor cortaba la base cuando pedía más de lo que la central produce. La v2 no tiene ese interruptor: el grupo de postes de los insertadores no tiene cable de cobre hacia el grupo de las turbinas, donde se conecta la base. El grupo de los insertadores tiene los 80 insertadores, 21 paneles solares, 7 acumuladores, la bomba única y 7 de los 44 robopuertos; los otros 37 robopuertos quedan en el grupo de las turbinas (recuento hecho por script sobre la cadena).

La idea del diseño, según el dueño del repositorio, es mantener toda la central funcionando, con su producción máxima todo el tiempo, aunque la base empiece a pedir más de lo que produce. Esto no se midió en el juego. Los paneles solares solo producen de día; de noche los insertadores dependen de la carga de los acumuladores.

## Cómo se probó

No hubo prueba de funcionamiento. El juego importó y construyó las 8659 entidades del blueprint y lo conectó a una fuente de energía; 1 de los 2 grupos de postes quedó fuera del alcance de esa fuente, y la prueba conectó ese grupo a ella con un cable añadido, lo que une las dos redes solo en la prueba; no se abasteció ninguna máquina con objetos. El validador del catálogo confirmó que la cadena es válida y solo usa objetos del juego base (versión 2.0.77). La imagen se capturó en el juego y muestra el blueprint construido, no en funcionamiento.

## Correcciones hechas aquí

- La cadena no tenía nombre ni descripción. Ahora el nombre es `Nuclear power plant - 40 reactors v2`, y la descripción, en inglés, da la potencia y el consumo calculados, las entradas, cómo conectar la base y cómo arrancarla.
- La cadena original es la que proporcionó el dueño del repositorio; el resto del contenido decodificado es idéntico al de ella, comprobado por script.

## Límites conocidos

- En esta versión no se midió nada en el juego: la potencia entregada, el consumo, el flujo de vapor con una sola bomba entre las dos mitades, el arranque y el comportamiento con una base que pide más de lo que la central produce.
- Los 40 umbrales de ahorro de combustible leen una cisterna de la mitad este, y la bomba única, conectada a la red solar, es el único enlace entre las dos mitades; el nivel de vapor de la mitad oeste no se vigila, y esto no se probó.
- La red de los insertadores depende de paneles solares y de acumuladores; de noche o con los acumuladores vacíos, los insertadores se paran, y el funcionamiento en esas condiciones no se probó.
- Los 7 robopuertos del grupo de los insertadores consumen 350 kW en reposo (7 × 50 kW), y los 21 paneles solares dan como máximo 1260 kW (21 × 60 kW), solo de día (valores del juego, calculados): cargar robots en esos robopuertos puede dejar sin energía a los insertadores, y esto no se probó.
- Los 37 robopuertos del grupo de las turbinas comparten con la base la falta de energía, si la base pide más de lo que la central produce.
- Los robots logísticos no se probaron.
- Si los cofres solicitadores se quedan sin células, los reactores dejan de reabastecerse; la lógica es la de la v1, pero esto no se probó en esta versión. Mantén una reserva de células en la red logística.
- Los bordes usan hormigón con señal de peligro normal, no hormigón refinado con señal de peligro.
