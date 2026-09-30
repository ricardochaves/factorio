# Central nuclear de 40 reactores con energía solar y acumuladores

Central nuclear con 40 reactores en dos columnas de 20, 640 intercambiadores de calor y 1292 turbinas de vapor, que entregó hasta 6136 MW en la medición. Es la v2 de la central de 40 reactores: no tiene el circuito de protección de la v1, y sus insertadores de combustible y su bomba tienen una red propia, con paneles solares y acumuladores, separada de la red de las turbinas, para seguir funcionando aunque la base pida más de lo que produce la central; el dueño del repositorio la recomienda en lugar de la v1.

- Archivo: [`nuclear-power-plant-40-reactors-v2.txt`](nuclear-power-plant-40-reactors-v2.txt) — cadena de blueprint; en el juego se llama `Nuclear power plant - 40 reactors v2`.
- Origen: diseño del dueño del repositorio, adaptado de un diseño ya existente, de autor desconocido; no se conoce ninguna licencia.
- Esta es siempre la versión actual de la v2; sus versiones anteriores quedan en el historial de git. La entrada `nuclear-power-plant-40-reactors-v1`, con circuito de protección, es otro diseño y sigue en el catálogo.

![Vista general, captura del juego](images/shot-1.webp)

## Qué contiene

| Elemento | Valor |
|---|---|
| Entidades | 8809 |
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
| Poste eléctrico mediano | 493 |
| Acumulador | 97 |
| Insertador | 80 |
| Cisterna | 68 |
| Panel solar | 53 |
| Robopuerto | 44 |
| Cofre solicitador | 40 |
| Cofre proveedor activo | 40 |
| Reactor nuclear de fisión | 40 |
| Poste eléctrico grande | 19 |
| Bomba de fluidos | 1 |

Los cuatro bordes terminan en una franja de hormigón con señal de peligro de una casilla de ancho; justo por dentro de ella, y en todo el resto de la superficie, el suelo es de hormigón.

## Diferencias respecto a la v1

Comparación con `nuclear-power-plant-40-reactors-v1`, hecha por script sobre las dos cadenas:

| Elemento | v1 | v2 |
|---|---|---|
| Bomba de fluidos | 66 | 1 |
| Combinador comparador | 1 | 0 |
| Interruptor | 1 | 0 |
| Panel solar | 1 | 53 |
| Acumulador | 2 | 97 |
| Tubería | 2137 | 2403 |
| Tubería subterránea | 1321 | 1205 |
| Poste eléctrico mediano | 488 | 493 |

- Sin circuito de protección: la v2 no tiene el combinador comparador ni el interruptor de la v1, así que la base se conecta directamente a un poste eléctrico grande de la red de las turbinas.
- Una sola bomba de vapor: la v1 tenía 66 bombas de fluidos entre las cisternas y las turbinas, y la v2 tiene una. El vapor queda en dos mitades independientes, oeste y este, y la bomba única une una mitad con la otra (ver «Cómo se distribuye el vapor»).
- Una red propia para los insertadores y la bomba: los 80 insertadores de combustible y la bomba están en un grupo de postes separado del grupo de las turbinas, con 53 paneles solares y 97 acumuladores (485 MJ); la v1 tenía solo 1 panel solar y 2 acumuladores, para su combinador.
- Igual que la v1: los 40 reactores, los 640 intercambiadores de calor, las 1292 turbinas, las 68 cisternas, los 80 insertadores, los 44 robopuertos, los 80 cofres, las 64 entradas de agua y la lógica de ahorro de combustible (las condiciones de los insertadores son las mismas).

## Entradas

- Agua: 64 tuberías subterráneas, 32 en el borde norte y 32 en el borde sur. Conecta cada una a una fuente de agua; a plena potencia la central usó unas 6300 unidades de agua por segundo (medido: 6326 por segundo con una demanda de 7000 MW; calculado: 10,3 por segundo en cada uno de los 624 intercambiadores de calor que hacen falta para 6240 MW, o 6430).
- Combustible: 40 cofres solicitadores piden 10 células de combustible de uranio cada uno; los robots logísticos de los 44 robopuertos traen las células, y las células gastadas de combustible de uranio salen por los 40 cofres proveedores activos. El blueprint no trae robots: la red logística necesita robots logísticos, un cofre con células de combustible de uranio y un cofre que reciba las células gastadas.
- Base: conecta la base a uno de los 19 postes eléctricos grandes, que pertenecen al grupo de las turbinas, por ejemplo el del centro, a 12 casillas al norte del borde sur. No conectes la base a los postes de los insertadores de combustible ni de los paneles solares: eso pondría la demanda de la base sobre ellos y desharía la separación.
- Arranque: como en la v1, un reactor solo recibe combustible de su cofre después de que sale de él una célula gastada, así que pon a mano una célula de combustible de uranio en cada uno de los 40 reactores. Medido: de día y sin fuente de energía externa, la central arrancó así y se reabasteció sola, y los acumuladores se llenaron en los primeros 10 minutos.

## Consumo y producción

| Elemento | Por segundo |
|---|---|
| Energía eléctrica entregada (máximo medido) | 6136 MW |
| Célula de combustible de uranio consumida | 0,2 (12 por minuto) |
| Célula gastada de combustible de uranio producida | 0,2 (12 por minuto) |
| Agua consumida | unas 6300 |

Valores medidos a plena potencia, con 39,9 de los 40 reactores quemando (una célula por reactor cada 200 s); la energía entregada es la de la medición con una demanda de 7000 MW. Los valores calculados son 6240 MW (40 reactores de 40 MW con 116 bonificaciones por proximidad del 100 %) y 6430 unidades de agua por segundo.

## Cómo se distribuye el vapor

En la v1 el vapor formaba una red única. En la v2 son dos mitades independientes, oeste y este, cada una con 320 intercambiadores de calor, 646 turbinas y 34 cisternas, todas alimentadas por la misma red de agua. La bomba única, cerca del borde norte y conectada a la red solar, lleva vapor de la mitad oeste a la este. Los 40 umbrales de ahorro de combustible leen una cisterna de la mitad este; el nivel de vapor de la mitad oeste no se vigila. En las mediciones, las dos mitades trabajaron por igual, con 646 turbinas en cada una, y la bomba trabajó el 100 % del tiempo bajo carga.

## Cómo la central ahorra combustible

En el juego base, un reactor con combustible quema sin parar, aunque nadie use el calor. Aquí cada reactor solo recibe una célula nueva después de que se saca la gastada, y los 40 insertadores que sacan las células gastadas están conectados por un cable verde a una cisterna de la columna este, cerca del borde sur. Cada par de reactores tiene un umbral: el primero solo se reabastece mientras esa cisterna tenga menos de 24.000 unidades de vapor, el siguiente menos de 23.000, y así sucesivamente, de 1000 en 1000, hasta 5000 en el último par. Esa cisterna tiene que seguir en la red de vapor.

## Cómo la red propia mantiene los insertadores

En la v1, las bombas de fluidos que llevaban el vapor y los insertadores de combustible funcionaban con la energía de la propia central, y por eso un interruptor cortaba la base cuando pedía más de lo que la central produce. La v2 no tiene ese interruptor: el grupo de postes de los insertadores no tiene cable de cobre hacia el grupo de las turbinas, donde se conecta la base. El grupo de los insertadores tiene los 80 insertadores, 53 paneles solares, 97 acumuladores, la bomba única y 7 de los 44 robopuertos; los otros 37 robopuertos quedan en el grupo de las turbinas (recuento hecho por script sobre la cadena y confirmado en el juego).

La idea del diseño, según el dueño del repositorio, es mantener toda la central funcionando, con su producción máxima todo el tiempo, aunque la base empiece a pedir más de lo que produce. Los 32 paneles y los 90 acumuladores añadidos bajan a lo largo de las cisternas hasta el final de la columna, y solo existen donde ningún poste ni robopuerto del grupo de las turbinas alcanza, para no unir las dos redes. Con la base parada, los 53 paneles dan hasta 3180 kW de día frente a unos 400 kW de consumo del grupo (medido), y el sobrante recarga los acumuladores.

## Resultados medidos en el juego

Medido en Factorio 2.0.77 con la cadena de esta entrada. Cada fila es la media de 18.000 ticks (5 min), después de 18.000 ticks (5 min) con la misma carga; la energía sale de las estadísticas eléctricas del juego; el agua, de sus estadísticas de fluidos; y las células quemadas, del número medio de reactores quemando, dividido entre 200 s (la duración de una célula). La potencia máxima calculada es 6240 MW.

| Carga pedida por la base (MW) | Entregado a la base (MW) | Células quemadas | Agua |
|---|---|---|---|
| 3000 | 3000 | 0,10/s | 2952/s |
| 5000 | 5000 | 0,17/s | 5129/s |
| 6000 | 5940 | 0,20/s | 6124/s |
| 6240 | 6080 | 0,20/s | 6268/s |
| 7000 | 6136 | 0,20/s | 6326/s |
| 5000, después de la sobrecarga | 5000 | 0,18/s | 5291/s |

Red solar, medida al mismo tiempo. En las filas de la noche, el juego se mantuvo a medianoche y la base pedía 5000 MW. Las ventanas medidas de la noche y de la recarga duran 9000 ticks (150 s), salvo la de la carga extra de 3 MW, de 6000 ticks; la de la fila de 7000 MW, de día, es la de 18.000 ticks de la tabla anterior.

| Situación | Carga de la red solar (kW) | Acumuladores (MJ) | Insertadores sin energía | Bomba trabajando |
|---|---|---|---|---|
| Base pidiendo 7000 MW, de día | 387 | 485, llenos | 0 de 80 | 100 % |
| Noche, sin carga extra | 397 | 464 → 405 | 0 de 80 | 100 % |
| Noche, con 1 MW extra | 1406 | 336 → 125 | 0 de 80 | 100 % |
| Noche, con 3 MW extra | sin energía | 0 | 40 de 80, de media | 0 % |
| De nuevo de día, sin carga extra | 391, y 2789 van a los acumuladores | 46 → 465 | 0 de 80 | 100 % |

- Sobrecarga de la base: con una demanda de 7000 MW, la central entregó 6136 MW, con 39,9 de los 40 reactores quemando y las 1292 turbinas trabajando. Los 80 insertadores y la bomba tuvieron energía todo el tiempo, el combustible siguió fluyendo (0,20 células por segundo) y los acumuladores se mantuvieron llenos. En la v1, sin el circuito, la misma carga hizo colapsar la central (221 MW).
- De 6000 a 7000 MW pedidos, la entrega quedó por debajo de lo pedido (5940, 6080 y 6136 MW) con la temperatura de los reactores todavía subiendo (707 → 735, 753 → 767 y 775 → 783 °C): el máximo sostenido no se midió en equilibrio térmico y ronda los 6100 MW o más.
- Arranque: sin fuente de energía externa, de día, con una célula en cada reactor, la central arrancó sola y se reabasteció (40 células cambiadas en 10 minutos, con 26,6 de los 40 reactores quemando de media), y los acumuladores pasaron de 0 a 485 MJ en ese tiempo.
- Noche: los 485 MJ cubren la carga de 397 kW de la red solar durante unos 20 minutos (calculado a partir de la caída medida) y, con 1 MW extra, durante unos 6 minutos. Con 3 MW extra, los acumuladores se agotaron en menos de 1 minuto (calculado), los insertadores se pararon, los reactores se quedaron sin células y la central se apagó (0 MW).
- Después de la falta total, cuando volvió el día la central se reinició sola: entre 50 s y 200 s después, los 40 reactores quemaban de nuevo y entregaba 4957 MW a los 5000 MW pedidos.
- Robopuertos: con 6000 MW o más pedidos, los 37 robopuertos del grupo de las turbinas quedaron todos con poca energía; los 7 del grupo solar nunca, salvo mientras llenaban sus baterías internas en el arranque.
- Vapor: en todas las fases con carga, 646 turbinas trabajaron en cada mitad, y ninguna turbina estaba parada a los 40.000 ticks.

## Cómo se probó

Dos ejecuciones en el juego. En la primera, el ejecutor de fotos del catálogo importó y construyó las 8809 entidades del blueprint y lo conectó a una fuente de energía; 1 de los 2 grupos de postes quedó fuera del alcance de esa fuente, y la prueba conectó ese grupo a ella con un cable añadido, lo que une las dos redes solo en la prueba. La imagen sale de esa ejecución y muestra el blueprint construido, no en funcionamiento.

En la segunda, un escenario de prueba hecho para esta entrada (no incluido en el repositorio) construyó el blueprint en una superficie de laboratorio, de día, puso agua infinita en las 64 entradas e hizo el papel de los robots logísticos: cada segundo completó 10 células de combustible de uranio en cada cofre solicitador y vació los cofres proveedores activos. El escenario puso una célula en cada reactor, sin ninguna fuente de energía externa. La base fue una carga eléctrica ajustable conectada a un poste eléctrico grande de la red de las turbinas; una segunda carga, conectada a un poste de la red solar, simuló el consumo extra de robots; y la noche se mantuvo fijando la hora de la superficie a medianoche. El juego confirmó que las dos redes son separadas y que la red solar tiene los 80 insertadores, los 53 paneles, los 97 acumuladores, la bomba, 7 robopuertos y ninguna turbina. Cada medición es de una sola ejecución. El validador del catálogo confirmó que la cadena es válida y solo usa objetos del juego base (versión 2.0.77).

## Correcciones hechas aquí

- La cadena no tenía nombre ni descripción. Ahora el nombre es `Nuclear power plant - 40 reactors v2`, y la descripción, en inglés, da la potencia, el consumo y el comportamiento de la red solar medidos, las entradas, cómo conectar la base y cómo arrancarla.
- Cambio pedido por el dueño del repositorio: la red solar recibió 32 paneles solares, 90 acumuladores y 28 postes eléctricos medianos, en una franja entre la columna este de cisternas y las turbinas, hasta el final de las cisternas. Ninguno de ellos es alcanzado por postes ni robopuertos del grupo de las turbinas, y las dos redes siguen separadas (comprobado por script y en el juego).
- La cadena original es la que proporcionó el dueño del repositorio; la comparación por script muestra solo el nombre, la descripción y estas adiciones (150 entidades y 28 cables).

## Límites conocidos

- El máximo sostenido no se midió en equilibrio térmico: de 6000 a 7000 MW pedidos, la temperatura de los reactores todavía subía al final de la medición, y la potencia de 6240 MW no se alcanzó.
- La red solar puede agotarse: una carga extra sostenida por encima de lo que dan los paneles de día (3180 kW) o de lo que aguantan los acumuladores de noche deja a los insertadores sin energía, y la central se apaga hasta que vuelve el sol. Con la carga propia de la red (397 kW), los acumuladores aguantan unos 20 minutos de oscuridad total (calculado).
- Los robots logísticos no se probaron: la carga extra de las pruebas fue una carga eléctrica, y el efecto de robots reales cargando en los 7 robopuertos de la red solar no se midió.
- No se ejecutó un ciclo completo de día y noche: la noche se mantuvo fija, a medianoche.
- Los 40 umbrales de ahorro de combustible leen una cisterna de la mitad este, y la bomba única, conectada a la red solar, es el único enlace entre las dos mitades; el nivel de vapor de la mitad oeste no se vigila.
- Los 37 robopuertos del grupo de las turbinas comparten con la base la falta de energía, si la base pide más de lo que la central produce.
- Si los cofres solicitadores se quedan sin células, los reactores dejan de reabastecerse; la lógica es la de la v1, pero esto no se probó en esta versión. Mantén una reserva de células en la red logística.
- Los bordes usan hormigón con señal de peligro normal, no hormigón refinado con señal de peligro.
