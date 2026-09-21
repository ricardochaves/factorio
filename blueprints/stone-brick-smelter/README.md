# Fornalha de tijolos de pedra

Blueprint que transforma pedra em tijolos de pedra: oito fornalhas elétricas com módulos de produtividade 3, cercadas por dezoito transmissores com módulos de velocidade 3. Ela é alimentada por uma esteira expressa cheia de pedra e entrega os tijolos em outra esteira expressa.

- Arquivo: [`stone-brick-smelter.txt`](stone-brick-smelter.txt) — string de blueprint; no jogo o nome é `Stone smelter`.
- Esta é sempre a versão atual. Versões anteriores ficam no histórico do git.

![Vista completa da fornalha, com as oito fornalhas elétricas em funcionamento entre os transmissores, capturada no jogo](images/overview-all-working.webp)

## O que tem dentro

| Item | Valor |
|---|---|
| Entidades | 73 |
| Área | 11 × 29 tiles |
| Fornalhas elétricas (`electric-furnace`) | 8 |
| Transmissores (`beacon`) | 18 |
| Módulos | 36 × `speed-module-3`, 16 × `productivity-module-3` |
| Insersores rápidos (`fast-inserter`) | 8 |
| Insersores de alto desempenho (`bulk-inserter`) | 8 |

## Entradas e saídas

A blueprint tem uma entrada e uma saída, ambas em esteiras expressas que correm para o norte (coordenadas da blueprint, sem girar):

- Entrada: pedra, pela extremidade sul da coluna da direita. Ligue uma esteira que leve só pedra: nenhum insersor da blueprint tem filtro, então, se outro item que as fornalhas aceitem estiver na esteira, nada impede que os insersores o coloquem nas fornalhas.
- Saída: tijolos de pedra, pela extremidade norte da coluna da esquerda (a esteira subterrânea expressa de saída).
- Energia: a blueprint não inclui geração de energia. A subestação (`substation`) na ponta sul é o ponto de ligação à rede elétrica.
- Módulos: vêm como pedidos de itens (36 × `speed-module-3` e 16 × `productivity-module-3`); é preciso entregá-los com robôs ou colocá-los à mão.

## Consumo e produção

Em itens por segundo, com a esteira de entrada cheia e todas as tecnologias pesquisadas:

| Itens por segundo | Calculado | Medido no jogo |
|---|---|---|
| Pedra consumida | 45 | 44,93 |
| Tijolos de pedra produzidos | 27 | 26,95 |

O consumo de 45/s é o limite de uma esteira expressa. A produção vem de 45 ÷ 2 × 1,2: 2 pedras dão 1 tijolo, e os 2 módulos de produtividade 3 de cada fornalha somam 20 %. A saída é 60 % de uma esteira expressa. A potência elétrica medida nesse regime é de 20,53 MW.

## Resultados medidos no jogo

Teste automatizado no Factorio 2.0.77 sem interface gráfica (cenário `smelter-test`): uma esteira de pedra sempre cheia (baú infinito e carregador expresso), a saída escoando e a energia vinda de uma interface de energia elétrica, com 60 s de aquecimento e 60 s de medição. A potência elétrica é lida depois disso: a interface de energia elétrica para de produzir e o teste mede, durante 10 s, quanto do buffer da interface a blueprint consome. O teste roda em duas superfícies ao mesmo tempo: com todas as tecnologias pesquisadas e sem nenhuma.

| Indicador | Todas as tecnologias | Nenhuma tecnologia |
|---|---|---|
| Pedra consumida | 44,93/s | 21,83/s |
| Tijolos de pedra produzidos | 26,95/s | 13,12/s |
| Tempo de trabalho da última fornalha da fila | 53,9 % | 47,8 % |
| Tempo de trabalho das outras sete fornalhas | 93,4 % a 100 % | 43,1 % a 47,6 % |
| Potência elétrica | 20,53 MW | 15,12 MW |

Sem nenhuma tecnologia pesquisada, no fim da medição os oito insersores de alto desempenho estavam trabalhando e quatro fornalhas estavam sem ingredientes: o limite passa a ser esses insersores, e a saída cai para 13,12/s.

## Como foi testado

Teste no jogo, com o cenário `smelter-test`: 17 verificações, todas passaram.

- A string é importada sem erro, e o jogo lê o nome e a descrição dela.
- As 73 entidades e os 52 módulos batem com a string, contados a partir do JSON decodificado.
- Uma única rede elétrica liga a blueprint à fonte de energia, e nenhuma máquina fica sem energia.
- A esteira cheia resulta no consumo e na produção calculados acima, e todas as fornalhas trabalham.

A imagem principal foi capturada no jogo, com interface gráfica, num cenário de laboratório com a blueprint construída, energizada e alimentada, no instante em que as oito fornalhas estavam em funcionamento. Esse cenário de captura não faz parte do repositório.

O validador do catálogo também confirmou que a string é válida e só usa itens do jogo base (versão 2.0.77).

## Como testar

Para rodar o teste no macOS, com o Factorio instalado pelo Steam (a versão testada é a 2.0.77), a partir da raiz do repositório:

```
scripts/run_smelter_test.sh
```

O script exporta a string, roda o cenário sem interface gráfica (o servidor só escuta em 127.0.0.1) e termina com código 0 apenas se todas as verificações passarem. Ele é escrito em zsh; para usar outro caminho do executável, defina a variável `FACTORIO_BIN` (mais detalhes em [scripts/README.md](../../scripts/README.md)).

## Limites conhecidos

- A blueprint precisa de tecnologias pesquisadas: sem nenhuma, a saída cai para 13,12 tijolos/s. O teste não separa qual tecnologia faz a diferença.
- A última fornalha da fila, a do norte, no fim da esteira de pedra, recebe só a pedra que sobra: com todas as tecnologias pesquisadas ela trabalhou 53,9 % do tempo, contra 93,4 % a 100 % nas outras sete.
- A blueprint não inclui geração de energia; em plena produção ela consome 20,53 MW.
