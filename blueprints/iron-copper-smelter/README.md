# Fundição de ferro/cobre

Fundição de chapas de ferro ou de cobre em fornalhas elétricas com módulos de produtividade 3, aceleradas por transmissores com módulos de velocidade 3. Uma linha de minério em esteira expressa entra pelo sul e a linha de chapas sai pelo norte.

- Arquivo: [`iron-copper-smelter.txt`](iron-copper-smelter.txt) — string de blueprint; no jogo o nome é `iron/copper smelter`.
- Origem: design de Nilaus, da série Master Class (“Advanced Smelting (8 Beacon) 45 / sec output”), publicado por ele [neste post do FactorioBin](https://factoriobin.com/post/SnAX6v23) (livro “Advanced Smelting - FACTORIO MASTER CLASS”). O post não declara licença. Esse livro foi gravado no Factorio 1.0.0, antes do 2.0; esta blueprint está gravada e foi testada no Factorio 2.0.77. A blueprint entra no catálogo com estes créditos e este link por decisão do dono do repositório. Os créditos também aparecem, resumidos, na página do site.
- Esta é sempre a versão atual. Versões anteriores ficam no histórico do git.

![Vista completa da fundição em funcionamento, com energia e minério de ferro na entrada, capturada no jogo](images/overview.webp)

## O que tem dentro

| Item | Valor |
|---|---|
| Entidades | 133 |
| Área | 13 × 47 tiles |
| Fornalhas elétricas | 13 |
| Transmissores (beacons) | 31 |
| Insersores rápidos | 27 |
| Módulos | 62 × `speed-module-3`, 26 × `productivity-module-3` |
| Postes médios | 16 |

A tabela lista as peças principais. O restante são 24 esteiras subterrâneas expressas, 14 esteiras expressas, 7 lâmpadas e 1 separador expresso.

## Entradas e saídas

- Entrada: uma linha de minério em esteira expressa, na coluna leste (x 356.5), pela borda sul, em (356.5, -246.5) nas coordenadas da blueprint, seguindo para o norte.
- Saída: a linha de chapas sai na coluna oeste (x 352.5), quatro tiles à esquerda da entrada, pela borda norte, em (352.5, -292.5), seguindo para o norte.
- Energia: os postes médios já estão ligados entre si por fios. Ligue a rede elétrica a qualquer um deles.
- Sem combustível: as fornalhas são elétricas.

## Resultados medidos no jogo

Medido no Factorio 2.0.77 (jogo base, sem mods), com a blueprint sobre grama, minério de ferro infinito entrando pela linha de entrada (a linha ficou cheia) e a linha de saída escoando tudo. Cada nível de pesquisa teve 18 000 ticks (5 min) de aquecimento antes de ser medido por 3600 ticks (60 s), contando os itens pelas estatísticas de produção do jogo e a energia pelo esvaziamento de um buffer de energia. Nas três janelas as chapas guardadas nas saídas das fornalhas ficaram estáveis (1191 → 1192, 293 → 278 e 208 → 207 chapas), então a produção medida é a vazão da linha de saída. A vazão depende da pesquisa de bônus de capacidade de insersores (os insersores rápidos são os únicos da blueprint), por isso há um resultado para cada nível:

| Pesquisa | Minério consumido | Chapas produzidas | Energia elétrica |
|---|---|---|---|
| Nenhuma (bônus 0) | 27,75/s | 33,27/s | 29,8 MW |
| Bônus de capacidade de insersores 2 (bônus +1) | 37,32/s | 44,75/s | 34,0 MW |
| Bônus de capacidade de insersores 7 (bônus +2, o máximo) | 37,47/s | 44,95/s | 34,0 MW |

As chapas saem 20 % acima do minério consumido, por causa dos módulos de produtividade 3 (2 por fornalha, +10 % cada). Com o bônus +1 ou +2 a saída chega a 44,75 e 44,95 chapas/s, praticamente uma esteira expressa cheia (45/s). Só o minério de ferro foi medido, mas o cobre tem a mesma receita no jogo (1 minério em 1 chapa, 3,2 s), então os números do cobre são os mesmos.

## Como foi testado

Testado no jogo, como descrito acima, numa cena montada por script que difere de uma construção de jogador em quatro pontos: as entidades fantasma da blueprint foram construídas por script; os módulos foram colocados por script a partir das solicitações de itens da blueprint (a construção com robôs não foi testada); o minério vem de um baú infinito por um carregador expresso; e a energia vem de uma interface de energia ligada a um poste grande. O baú, o carregador, a interface e o poste ficam fora da imagem: só o fio de cobre que sai pelo canto inferior esquerdo liga a blueprint a eles. O cenário é `iron-copper-shot` (`scripts/ingame/data/scenarios/iron-copper-shot/control.lua`), rodado por `scripts/run_iron_copper_shot.sh`. O validador do catálogo também confirmou que a string é válida e só usa itens do jogo base.

## Como testar

Com o jogo instalado, na pasta `scripts/`: `./run_iron_copper_shot.sh` (com o prefixo `SteamAppId=427520` se o Steam estiver aberto sem login). É preciso usar a versão com interface gráfica, porque a imagem é gerada com o renderizador do jogo. O script imprime as medições da tabela acima (cerca de 90 s) e refaz `images/overview.webp`.

## Limites conhecidos

- A descrição gravada na string que chegou ao catálogo (colada pelo dono do repositório) dizia "Consumes 45/s" e "Produces 45/s" (uma esteira expressa cheia). A saída de 45/s é confirmada (44,95 chapas/s no máximo), mas a entrada não: com +20 % de produtividade, 45 chapas/s pedem 37,5 minério/s, e o máximo medido foi 37,47/s.
- Por isso o catálogo reescreveu essa descrição: ela agora credita Nilaus, traz o link e diz 37,5/s de entrada e 45/s de saída, com os valores medidos. O nome (rótulo) da string não foi alterado: ele já vinha diferente do nome do design no livro do FactorioBin. O resto do conteúdo da string, decodificado, é idêntico ao da string que chegou (verificado por script), e a string corrigida foi importada e medida no jogo com os mesmos resultados.
- Uma linha de entrada com menos de 37,47 minério/s deixa a fundição abaixo do máximo.
- Sem a pesquisa de bônus de capacidade de insersores, a saída cai para 33,27 chapas/s.
- O teste usou um só tipo de minério na linha (ferro).
- Os módulos vêm como solicitação de itens na blueprint: ao colar com robôs, a rede logística precisa ter 62 `speed-module-3` e 26 `productivity-module-3` armazenados.
