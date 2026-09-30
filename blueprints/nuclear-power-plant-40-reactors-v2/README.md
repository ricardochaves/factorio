# Usina nuclear de 40 reatores com energia solar e acumuladores

Usina nuclear com 40 reatores em duas colunas de 20, 640 permutadores de calor e 1.292 turbinas a vapor, com potência máxima calculada de 6.240 MW. É a v2 da usina de 40 reatores: não tem o circuito de proteção da v1, e os insersores de combustível têm uma rede própria, com painéis solares e acumuladores, separada da rede das turbinas; o dono do repositório a recomenda em vez da v1.

- Arquivo: [`nuclear-power-plant-40-reactors-v2.txt`](nuclear-power-plant-40-reactors-v2.txt) — string de blueprint; no jogo o nome é `Nuclear power plant - 40 reactors v2`.
- Origem: design do dono do repositório, adaptado de um design pronto de autor desconhecido; nenhuma licença é conhecida.
- Esta é sempre a versão atual da v2; versões anteriores dela ficam no histórico do git. A `nuclear-power-plant-40-reactors-v1`, com circuito de proteção, é outro design e continua no catálogo.

![Vista geral, capturada no jogo](images/shot-1.webp)

## O que tem dentro

| Item | Valor |
|---|---|
| Entidades | 8.659 |
| Área | 370 × 159 tiles |
| Tubo de calor | 2.294 |
| Cano | 2.403 |
| Cano subterrâneo | 1.205 |
| Turbina a vapor | 1.292 |
| Permutador de calor | 640 |

## Lista de materiais

Tudo o que a blueprint usa, contado pelo validador do catálogo a partir da string:

| Item | Quantidade |
|---|---|
| Concreto | 57.776 |
| Cano | 2.403 |
| Tubo de calor | 2.294 |
| Turbina a vapor | 1.292 |
| Cano subterrâneo | 1.205 |
| Concreto com sinal de perigo | 1.054 |
| Permutador de calor | 640 |
| Poste médio | 465 |
| Insersor | 80 |
| Tanque de armazenamento | 68 |
| Roboport | 44 |
| Baú solicitador | 40 |
| Baú provedor ativo | 40 |
| Reator nuclear | 40 |
| Painel solar | 21 |
| Poste grande | 19 |
| Acumulador | 7 |
| Bomba | 1 |

As quatro bordas terminam numa faixa de concreto com sinal de perigo de um tile de largura; dentro dela, em todo o resto do piso, o chão é concreto.

## Diferenças em relação à v1

Comparação com a `nuclear-power-plant-40-reactors-v1`, feita por script sobre as duas strings:

| Item | v1 | v2 |
|---|---|---|
| Bomba | 66 | 1 |
| Combinador de decisão | 1 | 0 |
| Interruptor de energia | 1 | 0 |
| Painel solar | 1 | 21 |
| Acumulador | 2 | 7 |
| Cano | 2.137 | 2.403 |
| Cano subterrâneo | 1.321 | 1.205 |
| Poste médio | 488 | 465 |

- Sem circuito de proteção: a v2 não tem o combinador de decisão nem o interruptor de energia da v1, então a base se liga direto a um poste grande da rede das turbinas.
- Uma só bomba de vapor: a v1 tinha 66 bombas entre os tanques e as turbinas, e a v2 tem uma. O vapor fica em duas metades independentes, oeste e leste, e a bomba única liga uma à outra (veja "Como o vapor é distribuído").
- Rede própria para os insersores: os 80 insersores de combustível ficam num grupo de postes separado do grupo das turbinas, com 21 painéis solares e 7 acumuladores; na v1 havia só 1 painel solar e 2 acumuladores, para o combinador.
- Igual à v1: os 40 reatores, os 640 permutadores de calor, as 1.292 turbinas, os 68 tanques, os 80 insersores, os 44 roboports, os 80 baús, as 64 entradas de água e a lógica de economia de combustível (as condições dos insersores são as mesmas).

## Entradas

- Água: 64 canos subterrâneos, 32 na borda norte e 32 na borda sul. Ligue cada um à água; na potência máxima a usina precisa de cerca de 6.430 unidades de água por segundo (calculado: 10,3 por segundo em cada um dos 624 permutadores de calor necessários para 6.240 MW).
- Combustível: 40 baús solicitadores pedem 10 células de combustível de urânio cada; os robôs logísticos dos 44 roboports trazem as células, e as células de urânio vazias saem pelos 40 baús provedores ativos. A blueprint não traz robôs: a rede logística precisa de robôs logísticos, de um baú com células de combustível de urânio e de um baú que receba as células vazias.
- Base: ligue a base a um dos 19 postes grandes, que pertencem ao grupo das turbinas, por exemplo o do centro, a 12 tiles ao norte da borda sul. Não ligue a base aos postes dos insersores de combustível nem dos painéis solares: isso poria a demanda da base sobre eles e desfaria a separação.
- Partida: como na v1, um reator só recebe combustível do baú depois que uma célula vazia sai dele, então coloque à mão uma célula de combustível de urânio em cada um dos 40 reatores. Isso não foi testado nesta versão: os insersores de combustível usam painéis solares e acumuladores, então só se movem de dia ou enquanto os acumuladores tiverem carga.

## Consumo e produção

| Item | Por segundo |
|---|---|
| Energia elétrica produzida (máximo calculado) | até 6.240 MW |
| Célula de combustível de urânio consumida | 0,2 (12 por minuto) |
| Célula de urânio vazia produzida | 0,2 (12 por minuto) |
| Água consumida | cerca de 6.430 |

Valores calculados na potência máxima: 40 reatores de 40 MW com 116 bônus de vizinhança de 100 %, uma célula de combustível por reator a cada 200 s e 10,3 unidades de água por segundo em cada um dos 624 permutadores de calor necessários para 6.240 MW. Nada disso foi medido nesta versão, e o fluxo de vapor com uma só bomba entre as duas metades na potência máxima também não.

## Como o vapor é distribuído

Na v1 o vapor formava uma rede única. Na v2 são duas metades independentes, oeste e leste, cada uma com 320 permutadores de calor, 646 turbinas e 34 tanques, todas alimentadas pela mesma rede de água. A bomba única, perto da borda norte e ligada à rede solar, leva vapor da metade oeste para a leste. Os 40 limites de economia de combustível leem um tanque da metade leste; o nível de vapor da metade oeste não é monitorado. As contagens foram feitas por script sobre a string, e o funcionamento desse arranjo não foi medido.

## Como a usina economiza combustível

No jogo base, um reator com combustível queima sem parar, mesmo quando ninguém usa o calor. Aqui cada reator só recebe uma célula nova depois que a vazia é retirada, e os 40 insersores que retiram as células vazias estão ligados por um fio verde a um tanque de armazenamento da coluna leste de tanques, perto da borda sul. Cada par de reatores tem um limite: o primeiro só é reabastecido enquanto esse tanque tiver menos de 24.000 unidades de vapor, o seguinte menos de 23.000, e assim por diante, de 1.000 em 1.000, até 5.000 no último par. Esse tanque precisa continuar na rede de vapor.

## Como a rede própria mantém os insersores

Na v1, as bombas de vapor e os insersores de combustível usavam a energia da própria usina, e por isso um interruptor cortava a base quando ela pedia mais do que a usina produz. Na v2 não há esse interruptor: o grupo de postes dos insersores não tem fio de cobre para o grupo das turbinas, onde a base se liga. O grupo dos insersores tem os 80 insersores, 21 painéis solares, 7 acumuladores, a bomba única e 7 dos 44 roboports; os outros 37 roboports ficam no grupo das turbinas (contagem feita por script sobre a string).

A ideia do projeto, segundo o dono do repositório, é manter a usina toda funcionando, na produção máxima o tempo todo, mesmo que a base passe a pedir mais do que ela produz. Isso não foi medido no jogo. Os painéis solares só produzem de dia; à noite os insersores dependem da carga dos acumuladores.

## Como foi testado

Não houve teste de funcionamento. O jogo importou e construiu as 8.659 entidades da blueprint e a ligou a uma fonte de energia; 1 dos 2 grupos de postes ficou fora do alcance dessa fonte, e o teste ligou esse grupo a ela com um fio adicionado, o que junta as duas redes só no teste; nenhuma máquina foi abastecida com itens. O validador do catálogo confirmou que a string é válida e só usa itens do jogo base (versão 2.0.77). A imagem foi capturada no jogo e mostra a blueprint construída, não em funcionamento.

## Correções feitas aqui

- A string não tinha nome nem descrição. Agora o nome é `Nuclear power plant - 40 reactors v2`, e a descrição, em inglês, traz a potência e o consumo calculados, as entradas, como ligar a base e como dar a partida.
- A string original é a que o dono do repositório forneceu; o resto do conteúdo decodificado é idêntico ao dela, conferido por script.

## Limites conhecidos

- Nada foi medido no jogo nesta versão: a potência entregue, o consumo, o fluxo de vapor com uma só bomba entre as duas metades, a partida e o funcionamento sob uma base que pede mais do que a usina produz.
- Os 40 limites de economia de combustível leem um tanque da metade leste, e a bomba única, ligada à rede solar, é a única ligação entre as duas metades; o nível de vapor da metade oeste não é monitorado, e isso não foi testado.
- A rede dos insersores depende de painéis solares e de acumuladores; à noite ou com os acumuladores vazios, os insersores param, e o funcionamento nessas condições não foi testado.
- Os 7 roboports do grupo dos insersores gastam 350 kW parados (7 × 50 kW), e os 21 painéis solares dão no máximo 1.260 kW (21 × 60 kW), só de dia (valores do jogo, calculados): carregar robôs nesses roboports pode deixar os insersores sem energia, e isso não foi testado.
- Os 37 roboports do grupo das turbinas dividem com a base a falta de energia, se a base pedir mais do que a usina produz.
- Os robôs logísticos não foram testados.
- Se os baús solicitadores ficarem sem células, os reatores deixam de ser reabastecidos; a lógica é a da v1, mas isso não foi testado nesta versão. Mantenha o estoque de células na rede logística.
- As bordas usam concreto com sinal de perigo comum, não concreto refinado com marca de perigo.
