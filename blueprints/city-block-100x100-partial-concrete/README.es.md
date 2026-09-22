# Bloque de ciudad de 100 × 100 solo con robots, hormigón parcial

Modelo de lote para una ciudad solo con robots en Factorio 2.0.77, juego base (sin Space Age): un bloque de 100 × 100 casillas con
4 robopuertos, borde estandarizado, postes eléctricos, iluminación y red logística. Los bloques se repiten cada 100 casillas,
encajan sin costuras y el interior del lote queda libre para lo que quieras construir. No hay vías, estación, generación de
energía ni robots: es solo la base de robots.

- Archivo: [`city-block-100x100-partial-concrete.txt`](city-block-100x100-partial-concrete.txt) (hormigón parcial: solo el borde y las bases de los postes y de los robopuertos tienen suelo; el interior del lote conserva el terreno original). En el juego, el nombre es `City block 100x100 (partial concrete)`.
- La otra variante, [hormigón total](../city-block-100x100-full-concrete/), es un blueprint aparte: las entidades y los cables son idénticos y solo cambia el suelo. Los dos se pueden colocar uno al lado del otro (ver «Frontera entre bloques vecinos»).
- Esta es siempre la versión actual. Las versiones anteriores quedan en el historial de git (`git log -p -- blueprints/city-block-100x100-partial-concrete/`).

![Bloque con hormigón parcial](images/overview.webp)

## Qué contiene

| Elemento | Valor |
|---|---|
| Entidades | 120 |
| Área | 100 × 100 casillas |
| Robopuertos | 4, en (25, 25), (75, 25), (25, 75) y (75, 75) (coordenadas del blueprint, en casillas a partir de la esquina noroeste del bloque) |
| Postes eléctricos grandes | 16: 12 en el borde, cada 30 casillas, y 4 junto a los robopuertos |
| Lámparas | 24: 2 en cada esquina, 1 en cada poste intermedio del borde y 2 en cada robopuerto |
| Cofres de almacenamiento, sin filtro | 76, vacíos: 14 alrededor de cada robopuerto y 20 junto a los postes del borde |
| Cables | 44: 20 de cobre (12 en el anillo del borde y 8 de los postes interiores), 12 rojos y 12 verdes |

Los cofres de almacenamiento son las existencias de la red logística: según el juego, guardan los objetos que salen de las ranuras de basura del jugador y de las órdenes de deconstrucción, y lo que contienen también se proporciona a las órdenes de construcción y de logística. En la prueba, los robots construyeron con objetos sacados de uno de ellos.

Suelo, en unidades del objeto que lo coloca:

| Suelo | Unidades |
|---|---|
| Hormigón refinado | 1920 |
| Hormigón refinado con señal de peligro | 608 |
| Camino de piedra (ladrillo de piedra) | 584 |
| Casillas en total | 3112 |

El resto de los materiales: 76 cofres de almacenamiento, 24 lámparas, 16 postes eléctricos grandes y 4 robopuertos.

## Cómo se monta el bloque

- **Alineación**: el blueprint usa alineación absoluta a la cuadrícula de 100 × 100. Cada copia cae en la celda de 100 × 100 que está bajo el cursor, así que los bloques vecinos no se superponen.
- **Borde**: una franja de 6 casillas en cada lado. De fuera hacia dentro: 2 de hormigón refinado, 1 de hormigón refinado con señal de peligro, 1 de camino de piedra y 2 de hormigón refinado. Dos bloques vecinos juntan los bordes y dejan una calle de 12 casillas entre ellos.
- **Bases de los robopuertos**: cada robopuerto está sobre una base de 12 × 12 casillas: un núcleo de 6 × 6 de hormigón refinado con señal de peligro, donde están el robopuerto, los cofres, el poste y las lámparas, rodeado por 1 casilla de camino de piedra y otras 2 de hormigón refinado.
- **Bases de los postes**: cada uno de los 12 postes del borde tiene su propia base, con el mismo diseño que las bases de los robopuertos a menor escala: núcleo de hormigón refinado con señal de peligro, 1 casilla de camino de piedra y 2 de hormigón refinado alrededor. La base cubre el poste, las lámparas y los cofres y avanza hacia el interior del lote más allá de la franja de 6 casillas: 3 casillas en los postes intermedios y 4 en las esquinas, igual en las cuatro esquinas.
- **Energía**: los 12 postes del borde forman un anillo de cobre; cada uno de los 4 postes interiores se conecta a 2 postes del anillo. Los postes de bloques vecinos quedan a 10 casillas uno del otro (95 → 105), así que la conexión eléctrica entre bloques se hace sola al construir (4 cables de cobre en cada lado que comparten dos bloques). El bloque no genera energía: conecta un poste del borde a tu red eléctrica. El consumo es de 200 kW en reposo (4 robopuertos × 50 kW), más 120 kW de las lámparas por la noche (24 × 5 kW). Cada robopuerto toma hasta 5 MW de la red (límite de entrada) mientras llena su reserva de 100 MJ, y cargar robots gasta 500 kW por estación de carga (hay 4 por robopuerto, hasta 2 MW).
- **Circuito**: el anillo del borde también tiene cables rojo y verde en los 12 postes. Cada bloque tiene su propia red de circuitos, sin conexión con la del vecino.
- **Alcance de los robopuertos**: en el juego base, el robopuerto tiene radio logístico 25 (área de 50 × 50) y radio de construcción 55 (área de 110 × 110). Las áreas logísticas de los 4 robopuertos se tocan y cubren todo el lote; las de construcción cubren 160 × 160 casillas, 30 más allá de cada borde.

![Cuatro bloques uno al lado del otro](images/city-2x2.webp)

## Frontera entre bloques vecinos

Cada lado del bloque es el espejo del lado opuesto, con las franjas de peligro cambiando de sentido. Por eso, al juntar dos bloques, los dos bordes de 6 casillas forman una calle de 12 casillas sin huecos, con las franjas de peligro y los caminos de piedra a la misma distancia del eje de la calle, y en el encuentro de cuatro bloques las cuatro bases de esquina quedan simétricas entre sí.

Probado en el juego casilla a casilla, con bloques en 2 × 1, 1 × 2, 2 × 2 y 3 × 3, y también con el hormigón parcial y el hormigón total alternados en damero (2 × 1, 2 × 2 y 3 × 3):

| Comprobación | Resultado |
|---|---|
| Uniones | en cada unión, la casilla a N casillas de un lado es el espejo de la casilla a N casillas del otro lado: 0 diferencias en 35 uniones (18 solo con este bloque, mirando 50 casillas hacia dentro de cada lado, es decir, hasta el medio de cada bloque; 17 en el damero, mirando solo el borde de 6 casillas) |
| Calle | las 12 casillas de la calle están todas pavimentadas, sin ningún hueco, en todas las uniones |
| Construcción | con 1, 2, 4 y 9 bloques: todas las entidades y casillas en las posiciones del blueprint, 0 fantasmas restantes, sin superposición |
| Energía | los postes de todos los bloques forman 1 red eléctrica, con 4 cables de cobre en cada lado compartido (en el 3 × 3: 180 de los bloques más 48 entre ellos) |
| Red logística | los robopuertos de todos los bloques forman 1 red (36 en el 3 × 3) y los cofres están todos dentro de ella (684) |
| Robots | construyeron 4 de 4 fantasmas de cofre de madera encima de la unión, con los cofres de madera guardados en un cofre de almacenamiento de uno de los bloques |

![Donde se encuentran cuatro bloques](images/junction.webp)

## Resultados medidos en el juego

Prueba automatizada en Factorio 2.0.77 headless (`scenarios/city-test`, 254 comprobaciones), con las dos variantes. Cada bloque se construye lejos del centro de su celda, para demostrar la alineación a la cuadrícula. La energía viene de un poste y de una interfaz de energía eléctrica fuera del bloque, conectados a un poste del borde; en las fotos que muestran la esquina superior izquierda del primer bloque (vista general, esquina de noche y 2 × 2), el cable de cobre que entra por ahí es el que conecta el bloque con esa fuente, que queda fuera del encuadre. Cada robopuerto recibió 10 robots de construcción y 10 logísticos. Las cifras de abajo son de un bloque y de cuatro bloques (2 × 2, 200 × 200 casillas).

| Comprobación | Resultado |
|---|---|
| Importación | la cadena se importa sin errores: 120 entidades y 3112 casillas, con alineación absoluta a la cuadrícula de 100 × 100 |
| Construcción | todas las entidades y casillas en las posiciones del blueprint y los cables en el mismo número que en él (por bloque: 20 de cobre, 12 rojos y 12 verdes), 0 fantasmas restantes, con 1 y con 4 bloques, sin superposición; con 4 bloques, otros 16 cables de cobre entre bloques vecinos |
| Red eléctrica | los 16 postes forman 1 red; los 64 postes de los 4 bloques también forman una sola, conectada por sí sola; los robopuertos y las lámparas están en ella |
| Robopuertos | cada robopuerto nuevo empieza con 10 MJ de los 100 MJ de la reserva y sube unos 5 MJ por segundo: 19,9 MJ a los 2 s, 59,5 MJ a los 10 s, lleno a los 20 s. Hasta entonces el estado es «Baja potencia»; con la reserva llena, todos quedan en «Trabajando» |
| Lámparas | 24 de 24 encendidas de noche (96 de 96 en los 4 bloques) |
| Red logística | los 4 robopuertos forman 1 red (16 en los 4 bloques) y los 76 cofres están dentro de ella (304 en los 4 bloques) |
| Robots | construyeron 4 de 4 fantasmas de cofre de madera en el medio del bloque, con los cofres de madera guardados en un cofre de almacenamiento del bloque |
| Circuitos | los 12 postes del anillo forman 1 red roja y 1 verde por bloque; en los 4 bloques son 4 redes de cada color |

![Robots construyendo a partir de los cofres del bloque](images/robots-at-work.webp)

## Límites conocidos

- El bloque solo trae la base de robots: no hay producción, vías, estación ni generación de energía, y el interior del lote queda vacío.
- Los robopuertos y los cofres vienen vacíos. Pon robots en los robopuertos y los objetos de construcción en los cofres; sin objetos en la red, los robots no construyen.
- Los anillos rojo y verde no se conectan entre bloques vecinos. Para tener una red de circuitos en toda la ciudad, conecta a mano, con cable rojo y cable verde, un poste de cada bloque a un poste del bloque vecino.
- Probado en terreno llano, de césped y de laboratorio. No se probaron el agua, los acantilados ni los árboles.
- Con hormigón parcial, el interior del lote queda como estaba (en las fotos, césped y tierra).

## Historial

- **Esquina noreste corregida** — la versión exportada tenía 12 casillas de hormigón refinado de más en la base del poste de la esquina noreste, en x = 87 a 89 e y = 6 a 9. Se eliminaron para que las cuatro bases de esquina quedaran iguales y las uniones entre bloques quedaran simétricas. No cambió nada más.
- **Publicación** — las entidades, los cables y los suelos son los exportados del juego. Solo se reescribieron el nombre y la descripción del blueprint (errores tipográficos y nombres alineados con los del sitio).

## Cómo probarlo

Desde la raíz del repositorio (necesita Factorio instalado; ver [`scripts/README.md`](../../scripts/README.md)):

```
./scripts/run_city_test.sh     # sin pantalla: importa, construye, mide energía, redes, fronteras y robots
./scripts/run_city_shot.sh     # con pantalla: toma las fotos y guarda images/*.webp de las dos variantes
```

Si Steam está abierto y sin sesión iniciada, usa `SteamAppId=427520 ./scripts/run_city_shot.sh`.
