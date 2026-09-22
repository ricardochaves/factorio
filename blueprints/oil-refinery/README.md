# Refinaria de petróleo

Blueprint única de uma refinaria completa para o Factorio 2.0.77, jogo base (sem Space Age).

- Arquivo: [`oil-refinery.txt`](oil-refinery.txt) — string de blueprint; no jogo o nome é `refinaria v3 (plastic feed + acid water)`.
- Esta é sempre a versão atual. Versões anteriores ficam no histórico do git (`git log -p -- blueprints/oil-refinery/`).

![Visão geral da refinaria](images/overview.webp)

## O que tem dentro

| Item | Valor |
|---|---|
| Entidades | 9.899 |
| Área | 193 × 129 tiles |
| Refinarias (`advanced-oil-processing`) | 36 |
| Usinas químicas | 416 |
| Máquinas de montagem 3 | 54 |
| Transmissores | 162 |
| Módulos | 1.300 × `speed-module-3`, 570 × `productivity-module-3` |
| Bombas / tanques | 163 / 38 |
| Roboports | 11 |

Produção (máquinas por receita): plástico 96, combustível sólido 120 (petróleo leve) + 34 (gás),
combustível de foguete 48, baterias 40, enxofre 39, ácido sulfúrico 12, lubrificante 13,
refino de petróleo leve em gás 41 e de petróleo pesado em leve 17, explosivos 2, munição de lança-chamas 2 e barris.

Cada bloco de plástico tem 48 usinas químicas (1 `speed-module-3` + 2 `productivity-module-3`, sem transmissor) e consome 1.152 de gás/s.

## Entradas

A blueprint tem 9 entradas externas, todas na borda sul (coordenadas da blueprint):

- Petróleo bruto: 2 subterrâneos em (-275.5, 499.5), que passa pelos tanques, e (-273.5, 499.5), direto ao banco oeste,
  e a linha do banco leste (x entre -176.5 e -120.5). **Ligue os dois subterrâneos.** As 36 refinarias só chegam a 100 %
  com os dois; com só o primeiro, o banco oeste fica em 54–75 %. Com tudo ligado, as refinarias consomem 3.604/s de
  petróleo bruto (medido).
- Água: 5 subterrâneos em y = 499.5 (x de -271.5 a -267.5) e a linha do banco leste (x entre -174.5 e -115.5).

## Resultados medidos no jogo

Teste automatizado no Factorio 2.0.77 headless, com fontes infinitas só nas 9 entradas externas (as bombas internas
de entrada são exercitadas), todas as saídas escoando e todos os itens alimentados:

| Indicador | Resultado |
|---|---|
| Refinarias | 100,0 % (36/36) |
| Ácido sulfúrico | 89 %, 0 % do tempo sem água (9 % com saída cheia) |
| Baterias | 100 % |
| Tanques de água do bloco de ácido | 60 % |
| Água entregue | 5.018/s |
| Petróleo bruto consumido | 3.604/s |

Em outros regimes: com gás sobrando nos produtores, ou com só o plástico escoando, as 96 usinas de plástico ficam em 100 %.

## Limites conhecidos

- Com tudo consumindo, a demanda de gás (~4.800/s) é maior que a produção (~2.160/s + refino de petróleo leve). Resultado: plástico 49 %,
  enxofre 66 % e combustível sólido a gás 0 %. Não é gargalo de bomba, é balanço de produção.
- Nesse regime escasso os dois blocos de plástico têm a mesma prioridade (`petroleum-gas > 95000`); o combustível sólido
  a gás (`> 97000`) recebe menos.

## Histórico

As mudanças futuras ficam no histórico do git. Resumo das versões anteriores a ele:

- **v3 — água dobrada no bloco de ácido sulfúrico** (22 entidades, 2 fios). Duas bombas paralelas às que já existiam:
  P1 ao lado da bomba (-116.5, 485), que leva água do banco leste ao ramal do bloco, e P2 ao lado da bomba (-127, 453.5),
  que enche o tanque de água do bloco (condição `water < 23500`, fio verde ao tanque). Ácido sulfúrico foi de 66 % para 89 %,
  baterias de 81 % para 100 %, água entregue de 4.619/s para 5.018/s.
- **v2 — alimentação de gás do bloco direito de plástico** (7 entidades novas, 2 alteradas, 3 fios). O bloco direito só
  recebia gás por uma bomba com condição `petroleum-gas > 99000`, e os tanques ficavam em ~97k: no regime escasso ele parava
  (0 %) enquanto o esquerdo ficava em 100 %. Duas bombas paralelas com `> 95000`, igual ao bloco esquerdo, e um poste médio.
- **Original** — blueprint base da qual as duas mudanças partiram.

Cada mudança foi verificada pelo modelo de fluidos (nenhum segmento ganhou tubo ou porta além dos previstos, nenhum tile
sobreposto) e no jogo (0 segmentos com mistura de fluidos).

## Como testar

A partir da raiz do repositório (precisa do Factorio instalado; ver [`scripts/README.md`](../../scripts/README.md)):

```
python3 scripts/fluid/make_full_test.py scripts/ingame/data/scenarios/fluid-test/tests.lua atual-inlet=blueprints/oil-refinery/oil-refinery.txt
./scripts/run_fluid.sh 600 && python3 scripts/fluid/balance.py
```

O sufixo do rótulo escolhe o regime: `-inlet` (fontes só nas entradas externas), `-surplus` (gás infinito nos produtores),
`-plasticonly` (só o plástico escoa); sem sufixo, produção real.
