# Usina nuclear de 40 reatores

Usina nuclear com 40 reatores em duas colunas de 20, 640 permutadores de calor e 1.292 turbinas a vapor, que entrega até 6.240 MW. Robôs logísticos trazem as células de combustível de urânio, e um circuito no centro da borda sul só manda energia para a base enquanto a base não pede mais do que a usina produz.

- Arquivo: [`nuclear-power-plant-40-reactors-v1.txt`](nuclear-power-plant-40-reactors-v1.txt) — string de blueprint; no jogo o nome é `Nuclear power plant - 40 reactors`.
- Origem: design do dono do repositório, adaptado de um design pronto de autor desconhecido; uma busca na web não encontrou o autor original, então nenhuma licença é conhecida.
- Esta é sempre a versão atual. Versões anteriores ficam no histórico do git.

![Vista geral, capturada no jogo](images/shot-1.webp)

## O que tem dentro

| Item | Valor |
|---|---|
| Entidades | 8.574 |
| Área | 370 × 159 tiles |
| Tubo de calor | 2.294 |
| Cano | 2.137 |
| Cano subterrâneo | 1.321 |
| Turbina a vapor | 1.292 |
| Permutador de calor | 640 |

## Lista de materiais

Tudo o que o blueprint usa, contado pelo validador do catálogo a partir da string:

| Item | Quantidade |
|---|---|
| Tubo de calor | 2.294 |
| Cano | 2.137 |
| Cano subterrâneo | 1.321 |
| Turbina a vapor | 1.292 |
| Permutador de calor | 640 |
| Poste médio | 488 |
| Insersor | 80 |
| Tanque de armazenamento | 68 |
| Bomba | 66 |
| Roboport | 44 |
| Baú solicitador | 40 |
| Baú provedor ativo | 40 |
| Reator nuclear | 40 |
| Poste grande | 19 |
| Acumulador | 2 |
| Combinador de decisão | 1 |
| Interruptor de energia | 1 |
| Painel solar | 1 |
| Concreto | 57.740 |
| Concreto com sinal de perigo | 1.090 |

As quatro bordas terminam numa faixa de concreto com sinal de perigo de um tile de largura; logo dentro dela, e em todo o resto do piso, o chão é concreto, com exceção de um quadrado de 6 × 6 tiles de concreto com sinal de perigo sob o circuito.

## Entradas

- Água: 64 canos subterrâneos, 32 na borda norte e 32 na borda sul. Ligue cada um à água; na potência máxima a usina precisa de cerca de 6.430 unidades de água por segundo (calculado: 10,3 por segundo em cada um dos 624 permutadores de calor necessários para 6.240 MW).
- Combustível: 40 baús solicitadores pedem 10 células de combustível de urânio cada; os robôs logísticos dos 44 roboports trazem as células, e as células de urânio vazias saem pelos 40 baús provedores ativos. O blueprint não traz robôs: a rede logística precisa de robôs logísticos, de um baú com células de combustível de urânio e de um baú que receba as células vazias.
- Base: ligue a base somente ao poste grande no centro da borda sul, que fica depois do interruptor de energia (veja a próxima seção).
- Partida: um reator só recebe combustível do baú depois que uma célula vazia sai dele, então a usina não parte sozinha. Coloque à mão uma célula de combustível de urânio em cada um dos 40 reatores e ligue uma fonte de energia a um poste da usina (não ao poste de saída): o blueprint vem com o interruptor aberto e os acumuladores vazios, e as bombas de vapor e os insersores só funcionam com energia. No teste, a fonte ficou ligada 20 minutos, até o acumulador da usina encher.

## Como a usina economiza combustível

No jogo base, um reator com combustível queima sem parar, mesmo quando ninguém usa o calor. Aqui cada reator só recebe uma célula nova depois que a vazia é retirada, e os 40 insersores que retiram as células vazias estão ligados por um fio verde a um tanque de armazenamento da coluna leste de tanques, perto da borda sul. Cada par de reatores tem um limite: o primeiro só é reabastecido enquanto esse tanque tiver menos de 24.000 unidades de vapor, o seguinte menos de 23.000, e assim por diante, de 1.000 em 1.000, até 5.000 no último par. Com pouca carga o vapor armazenado sobe e só alguns reatores queimam; os 40 só queimam juntos com o tanque abaixo de 5.000 unidades. Esse tanque precisa continuar na rede de vapor.

## Como o circuito protege a usina

As bombas que levam o vapor dos tanques às turbinas e os insersores que colocam combustível nos reatores são movidos pela energia da própria usina. Se a base estivesse ligada na mesma rede elétrica e pedisse mais do que a usina produz, a falta de energia chegaria também a essas bombas e insersores: o vapor para de chegar às turbinas, a produção cai, a falta aumenta, e a usina colapsa.

Por isso a saída para a base passa por um interruptor de energia, no centro da borda sul:

- Um acumulador da rede da usina informa a sua carga ao combinador de decisão por um fio vermelho.
- O combinador fecha o interruptor quando a carga passa de 90 % e o mantém fechado enquanto ela estiver em 50 % ou mais; o próprio sinal de saída volta para a entrada por um fio verde e guarda esse estado.
- Quando a base pede mais do que a usina produz, o acumulador descarrega; abaixo de 50 %, o interruptor abre e a base fica sem energia, enquanto a usina continua a alimentar as suas bombas e insersores. Com o acumulador de novo acima de 90 %, a base volta a receber energia.
- O combinador tem a sua própria rede elétrica, com um poste médio, um painel solar e outro acumulador, separada da usina e da base.

Só o poste grande depois do interruptor passa por essa proteção. Ligar a base a qualquer outro poste da usina junta as duas redes e desfaz a proteção.

## Resultados medidos no jogo

Medido no Factorio 2.0.77, com a string corrigida desta entrada. Cada linha é a média de 18.000 ticks (5 min), depois de 18.000 ticks (5 min) na mesma carga; a energia vem das estatísticas elétricas do jogo; a água, das estatísticas de fluidos; e as células queimadas, do número médio de reatores queimando, dividido por 200 s (a duração de uma célula). A potência máxima calculada é 6.240 MW: 40 reatores de 40 MW com 116 bônus de vizinhança de 100 %.

| Carga pedida pela base (MW) | Entregue à base (MW) | Células queimadas | Água |
|---|---|---|---|
| 3.000 | 3.000 | 0,103/s | 3.177/s |
| 5.000 | 5.000 | 0,164/s | 5.099/s |
| 6.000 | 6.000 | 0,200/s | 6.194/s |
| 6.240 | 6.240 | 0,194/s | 6.232/s |
| 7.000, com o circuito | 6.062 em média | 0,199/s | 6.294/s |
| 7.000, sem o circuito | 221 | 0/s | 228/s |

- Consumo na potência máxima: 0,2 célula de combustível de urânio por segundo (12 por minuto, uma a cada 200 s por reator) e cerca de 6.430 unidades de água por segundo, calculadas; a medição a 6.240 MW deu 6.232/s porque parte do vapor veio dos tanques. Em espera, sem carga, a usina gasta cerca de 2 MW com os próprios roboports.
- A 6.000 MW, a temperatura dos reatores subiu durante a medição (729 → 748 °C). A 6.240 MW, ela caiu um pouco (760 → 752 °C), com 38,7 dos 40 reatores queimando em média: os 6.240 MW se mantiveram nos 10 minutos do teste com a ajuda do vapor armazenado. Com 7.000 MW pedidos, as turbinas geraram 6.066 MW com a temperatura subindo, então a produção contínua fica perto de 6.200 MW.
- Com 7.000 MW pedidos e o circuito ligado, o interruptor abriu três vezes em 5 minutos e ficou fechado 93 % do tempo; as bombas de vapor ficaram com energia em 91 % das amostras, e a usina continuou funcionando.
- Com o interruptor forçado a ficar fechado (sem o circuito), a mesma carga de 7.000 MW colapsou a usina: as bombas de vapor ficaram sem energia, nenhum reator recebeu combustível, e a entrega caiu para 221 MW. Com a carga reduzida a 5.000 MW ela continuou em 221 MW; só voltou quando a carga foi a zero. Com o circuito restaurado, a usina voltou a entregar 5.000 MW.

## Como foi testado

Três execuções no jogo. Na primeira, o executor de fotos do catálogo importou e construiu o blueprint e o ligou a uma fonte de energia; 1 grupo de postes ficou fora do alcance da fonte, e o teste o ligou a ela com um fio adicionado. A imagem vem dessa execução e mostra o blueprint construído, não em funcionamento.

Na segunda, um cenário de teste feito para esta entrada (não incluído no repositório) construiu o blueprint numa superfície de laboratório sempre de dia, pôs água infinita nos 64 canos subterrâneos de entrada, e fez o papel dos robôs logísticos: a cada segundo completou 10 células de combustível de urânio em cada baú solicitador e esvaziou os baús provedores ativos. O cenário colocou uma célula em cada reator e ligou uma fonte de energia temporária, retirada antes das medições. Na terceira, com os reatores vazios, a mesma fonte e combustível nos baús, nenhum reator queimou em 5 minutos; com uma célula à mão em cada reator, a usina partiu e depois se reabasteceu sozinha. A base foi uma carga elétrica ajustável ligada ao poste grande de saída. O validador do catálogo confirmou que a string é válida e só usa itens do jogo base (versão 2.0.77).

## Correções feitas aqui

- Na coluna leste, a linha de turbinas da altura y = −157,5 não tinha o cano subterrâneo de entrada na borda: as 19 turbinas dessa linha nunca recebiam vapor. O teste da string original confirmou isso (1.273 de 1.292 turbinas funcionando); com o cano subterrâneo adicionado, as 1.292 funcionam.
- A string não tinha nome nem descrição. Agora o nome é `Nuclear power plant - 40 reactors`, e a descrição, em inglês, traz a potência e o consumo medidos, as entradas e como ligar a base.
- A string original é a que o dono do repositório forneceu; o resto do conteúdo decodificado é idêntico ao dela, conferido por script.
- A descrição no jogo passava dos 500 bytes que o jogo guarda ao importar uma string, e o jogo cortava o resto sem avisar. Ela foi encurtada para caber inteira (conferido no jogo); os detalhes que saíram dela estão neste relatório.

## Limites conhecidos

- As bordas usam concreto com sinal de perigo comum, não concreto refinado com marca de perigo, por decisão do dono do repositório.
- A rede do combinador depende de um painel solar e de um acumulador; o teste foi feito sempre de dia, então o funcionamento à noite não foi medido.
- Os robôs logísticos não foram testados: o teste colocou e retirou as células de combustível por script.
- Se os baús solicitadores ficarem sem células, a usina desliga: no teste, com os baús esvaziados e 5.000 MW de carga, os 40 reatores pararam e as bombas de vapor ficaram sem energia; com 400 células de volta nos baús, ela continuou parada por 5 minutos. É preciso dar a partida de novo, como na primeira vez (esse reinício não foi testado). Mantenha o estoque de células na rede logística.
- A partida sem uma fonte de energia externa não foi testada.
