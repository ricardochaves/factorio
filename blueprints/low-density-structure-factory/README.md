# Fábrica de estrutura de baixa densidade

Duas colunas de máquinas de montagem 3 com módulos de produtividade 3, aceleradas por transmissores com módulos de velocidade 3, que fazem estruturas de baixa densidade. Recebe chapas de cobre, vigas de aço e barras de plástico pelo sul e entrega 6,28 estruturas por segundo (377 por minuto), também pelo sul.

- Arquivo: [`low-density-structure-factory.txt`](low-density-structure-factory.txt) — string de blueprint; no jogo o nome é `Low density structure factory`.
- Esta é sempre a versão atual. Versões anteriores ficam no histórico do git.

![Vista geral, capturada no jogo](images/shot-1.webp)

## O que tem dentro

| Item | Valor |
|---|---|
| Entidades | 255 |
| Área | 20 × 34 tiles |
| Máquinas de montagem 3 | 18 |
| Transmissores | 21 |
| Módulos | 72 × `productivity-module-3`, 42 × `speed-module-3` |
| Insersores | 34 de longo-alcance, 18 de alto desempenho, 18 rápidos |
| Esteiras expressas | 73 |
| Esteiras subterrâneas expressas | 44 |

O restante são 16 postes médios, 7 esteiras rápidas (a saída) e 6 painéis de exibição, que marcam o item de cada entrada.

## Entradas e saídas

- Entradas: seis saídas de esteira subterrânea expressa na borda sul, viradas para o norte, cada uma logo acima de um painel de exibição com o ícone do item. Do oeste para o leste: chapa de cobre, chapa de cobre, chapa de cobre, viga de aço, barra de plástico, chapa de cobre. Coloque a entrada de cada esteira subterrânea ao sul do painel correspondente.
- Saída: a esteira rápida que desce pela borda sul, entre a primeira e a segunda entrada de cobre.
- Energia: os postes médios já estão ligados entre si. Ligue a rede elétrica a qualquer um deles.
- Pesquisa: precisa de “Bônus de capacidade de insersores 2”.

## Resultados medidos no jogo

Medido no Factorio 2.0.77 (jogo base, sem mods), com as seis entradas cheias (uma esteira expressa completa em cada uma) e a saída sempre livre. Cada nível de pesquisa teve 36.000 ticks (10 min) de aquecimento antes de ser medido por 216.000 ticks (60 min); os itens foram contados pelas estatísticas de produção do jogo e a potência, pelo esvaziamento de um buffer de energia. A produção depende da pesquisa de bônus de capacidade de insersores, então há um resultado por nível:

| Pesquisa | Chapas de cobre | Vigas de aço | Barras de plástico | Estruturas produzidas | Potência elétrica |
|---|---|---|---|---|---|
| Sem bônus de capacidade | 76,84/s | 7,68/s | 19,21/s | 5,38/s | 57,71 MW |
| Bônus de capacidade de insersores 1 | 77,48/s | 7,75/s | 19,37/s | 5,42/s | 57,65 MW |
| Bônus de capacidade de insersores 2 | 89,73/s | 8,97/s | 22,43/s | 6,28/s | 64,21 MW |
| Bônus de capacidade de insersores 7 (o máximo) | 89,73/s | 8,97/s | 22,43/s | 6,28/s | 63,86 MW |

A partir do nível 2, as 18 máquinas trabalharam de 99,9% a 100% da janela, e a produção é a máxima que as máquinas permitem: 6,28 estruturas por segundo, 377 por minuto. Cada máquina tem +40% de produtividade (4 módulos de produtividade 3), então saem 1,4 estruturas por receita. A velocidade de produção é 4,25 nas duas máquinas do topo (4 transmissores cada), 3,75 nas catorze do meio (3 transmissores) e 3,15 nas duas de baixo (2 transmissores).

## Como foi testado

Testado no jogo, como descrito acima, em um cenário com scripts que difere da construção de um jogador em quatro pontos: os fantasmas do blueprint foram construídos por script; os módulos foram inseridos por script a partir dos pedidos de itens do blueprint (a construção com robôs não foi testada); os itens vêm de baús infinitos por carregadores expressos, e a saída termina em um carregador e um baú que apaga o que recebe; e a energia vem de uma interface de energia elétrica ligada, por um poste adicionado, ao poste mais ao sul. O jogo também importou e construiu o blueprint e o ligou a uma fonte de energia para a imagem, que mostra o blueprint construído e energizado, não em funcionamento. O validador do catálogo confirmou que a string é válida e só usa itens do jogo base (versão 2.0.77).

## Correções feitas aqui

- A string chegou sem nome e sem descrição. O catálogo deu a ela o nome `Low density structure factory` e uma descrição com o que ela consome e produz, medida no jogo. As 255 entidades e os fios são os mesmos da string original (conferido por script).
- A descrição no jogo passava dos 500 bytes que o jogo guarda ao importar uma string, e o jogo cortava o resto sem avisar. Ela foi encurtada para caber inteira (conferido no jogo), sem perder nenhum número.

## Limites conhecidos

- As barras de plástico e as vigas de aço dividem a esteira central, uma pista para cada item: as 22,43 barras de plástico por segundo ficam muito perto do máximo de uma pista de esteira expressa (22,5/s), então a entrada de plástico precisa chegar cheia.
- Sem a pesquisa “Bônus de capacidade de insersores 2”, a produção cai para algo entre 5,38 e 5,42 estruturas por segundo.
- A medição usou as seis entradas cheias; quanto cada uma das quatro entradas de cobre consome separadamente não foi medido.
- Os módulos vêm como pedidos de itens no blueprint: ao colar com robôs, a rede logística precisa ter 72 `productivity-module-3` e 42 `speed-module-3` em armazenamento.
