# Fábrica de estructura de baja densidad

Dos columnas de máquinas de ensamblaje 3 con módulos de productividad 3, aceleradas por faros con módulos de velocidad 3, que hacen estructuras de baja densidad. Recibe placas de cobre, barras de acero y barras de plástico por el sur y entrega 6,28 estructuras por segundo (377 por minuto), también por el sur.

- Archivo: [`low-density-structure-factory.txt`](low-density-structure-factory.txt) — cadena de blueprint; en el juego se llama `Low density structure factory`.
- Esta es siempre la versión actual. Las versiones anteriores quedan en el historial de git.

![Vista general, captura del juego](images/shot-1.webp)

## Qué contiene

| Elemento | Valor |
|---|---|
| Entidades | 255 |
| Área | 20 × 34 casillas |
| Máquinas de ensamblaje 3 | 18 |
| Faros | 21 |
| Módulos | 72 × `productivity-module-3`, 42 × `speed-module-3` |
| Insertadores | 34 largos, 18 de lotes, 18 rápidos |
| Cintas transportadoras exprés | 73 |
| Cintas transportadoras subterráneas exprés | 44 |

El resto son 16 postes eléctricos medianos, 7 cintas transportadoras rápidas (la salida) y 6 paneles de visualización, que marcan el objeto de cada entrada.

## Entradas y salidas

- Entradas: seis salidas de cinta transportadora subterránea exprés en el borde sur, orientadas al norte, cada una justo encima de un panel de visualización con el icono del objeto. De oeste a este: placa de cobre, placa de cobre, placa de cobre, barra de acero, barra de plástico, placa de cobre. Coloca la entrada de cada cinta subterránea al sur de su panel.
- Salida: la cinta transportadora rápida que baja por el borde sur, entre la primera y la segunda entrada de cobre.
- Energía: los postes eléctricos medianos ya están conectados entre sí. Conecta la red eléctrica a cualquiera de ellos.
- Investigación: necesita «Bonificación de capacidad de insertador 2».

## Resultados medidos en el juego

Medido en Factorio 2.0.77 (juego base, sin mods), con las seis entradas llenas (una cinta transportadora exprés completa en cada una) y la salida siempre libre. Cada nivel de investigación tuvo 36.000 ticks (10 min) de calentamiento antes de medirse durante 216.000 ticks (60 min); los objetos se contaron con las estadísticas de producción del juego y la potencia, por el consumo de una reserva de energía. La producción depende de la investigación de bonificación de capacidad de insertador, así que hay un resultado por nivel:

| Investigación | Placas de cobre | Barras de acero | Barras de plástico | Estructuras producidas | Potencia eléctrica |
|---|---|---|---|---|---|
| Sin bonificación de capacidad | 76,84/s | 7,68/s | 19,21/s | 5,38/s | 57,71 MW |
| Bonificación de capacidad de insertador 1 | 77,48/s | 7,75/s | 19,37/s | 5,42/s | 57,65 MW |
| Bonificación de capacidad de insertador 2 | 89,73/s | 8,97/s | 22,43/s | 6,28/s | 64,21 MW |
| Bonificación de capacidad de insertador 7 (el máximo) | 89,73/s | 8,97/s | 22,43/s | 6,28/s | 63,86 MW |

A partir del nivel 2, las 18 máquinas trabajaron del 99,9 % al 100 % de la ventana, y la producción es la máxima que permiten las máquinas: 6,28 estructuras por segundo, 377 por minuto. Cada máquina tiene +40 % de productividad (4 módulos de productividad 3), así que cada receta da 1,4 estructuras. La velocidad de creación es 4,25 en las dos máquinas de arriba (4 faros cada una), 3,75 en las catorce del medio (3 faros) y 3,15 en las dos de abajo (2 faros).

## Cómo se probó

Probado en el juego, como se describe arriba, en un escenario con scripts que difiere de la construcción de un jugador en cuatro puntos: los fantasmas del blueprint se construyeron por script; los módulos se insertaron por script a partir de las solicitudes de objetos del blueprint (no se probó la construcción con robots); los objetos vienen de cofres infinitos mediante cargadores exprés, y la salida termina en un cargador y un cofre que borra lo que recibe; y la energía viene de una interfaz de energía eléctrica conectada, mediante un poste añadido, al poste más al sur. El juego también importó y construyó el blueprint y lo conectó a una fuente de energía para la imagen, que muestra el blueprint construido y con energía, no en funcionamiento. El validador del catálogo confirmó que la cadena es válida y solo usa objetos del juego base (versión 2.0.77).

## Correcciones hechas aquí

- La cadena llegó sin nombre y sin descripción. El catálogo le dio el nombre `Low density structure factory` y una descripción con lo que consume y produce, medido en el juego. Las 255 entidades y los cables son los mismos que en la cadena original (comprobado por script).
- La descripción en el juego superaba los 500 bytes que el juego conserva al importar una cadena, y el juego cortaba el resto sin avisar. Se acortó para que quepa entera (comprobado en el juego), sin perder ninguna cifra.

## Límites conocidos

- Las barras de plástico y las barras de acero comparten la cinta central, un carril para cada objeto: las 22,43 barras de plástico por segundo quedan muy cerca del máximo de un carril de cinta transportadora exprés (22,5/s), así que la entrada de plástico tiene que llegar llena.
- Sin la investigación «Bonificación de capacidad de insertador 2», la producción queda entre 5,38 y 5,42 estructuras por segundo.
- La medición usó las seis entradas llenas; no se midió cuánto consume por separado cada una de las cuatro entradas de cobre.
- Los módulos vienen como solicitudes de objetos en el blueprint: al pegar con robots, la red logística necesita 72 `productivity-module-3` y 42 `speed-module-3` en almacenamiento.
