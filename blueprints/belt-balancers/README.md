# Balanceadores de esteira N×M — livros 24×24

Três livros de blueprints (strings de blueprint book, Factorio 2.0.77, jogo base sem Space Age), um por tipo de esteira:

| Arquivo | Livro no jogo | Esteira | Subterrâneo máx. |
|---|---|---|---|
| [`yellow-belt.txt`](yellow-belt.txt) | `Yellow Belt balancer` | amarela (transport-belt) | 5 tiles |
| [`red-belt.txt`](red-belt.txt) | `Red Belt balancer` | vermelha (fast-transport-belt) | 7 tiles |
| [`blue-belt.txt`](blue-belt.txt) | `Blue Belt balancer` | azul (express-transport-belt) | 9 tiles |

Cada arquivo é a versão atual; versões anteriores ficam no histórico do git. As seções abaixo descrevem o livro azul;
as diferenças dos livros vermelho e amarelo estão em [Livros vermelho e amarelo](#livros-vermelho-e-amarelo).

## Estrutura

- Livro raiz `Blue Belt balancer` com **24 sublivros** (`1` … `24`), um por quantidade de esteiras de entrada.
- Cada sublivro tem `N to 1` … `N to 24` (o sublivro `2` tem 25 itens porque mantém as duas variantes `2 to 3 (Long)` e `2 to 3 (Wide)`).
- Total: **577 blueprints**, cobrindo os 576 pares N×M.

## Origem de cada blueprint

| Origem | Qtde |
|---|---|
| Original do livro base (mantido) | 49 |
| Original substituído por falhar na verificação (Raynquist fall 2025) | 16 |
| Raynquist fall 2025 (pares que não existiam: 9-x, x-9, 8-10, 10-10, 12-12, 16-16, …) | 38 |
| Gerado por composição de blocos verificados | 474 |

### Originais com defeito (substituídos)

Estes 16 blueprints do livro original não são balanceadores corretos (ex.: `4 to 5` junta dois loopbacks numa esteira só e entrega 1,0 / 0,75 / 0,75 / 0,75 / 0,75 com as 4 entradas cheias):

`2 to 5`, `3 to 5`, `3 to 7`, `4 to 5`, `5 to 2`, `5 to 3`, `5 to 4`, `5 to 6`, `5 to 7`, `6 to 5`, `6 to 7`, `7 to 3`, `7 to 5`, `7 to 6`, `7 to 8`, `8 to 7`

## Como os novos foram gerados

Blocos de biblioteca (os originais aprovados + livro do Raynquist, https://github.com/raynquist/balancer) são compostos fisicamente, sempre com fluxo para o norte e entradas/saídas contíguas:

- `LOOP`: bloco (n+L → m+L) com L saídas realimentadas nas entradas pelos lados (ex.: 24→24 = núcleo 32-32 + 8 loops).
- `STACK`: n→k embaixo e g cópias de (k/g → m/g) em cima (ex.: 12→24 = 12-12 + 12×(1→2)).
- `SQ + K1`: balanceador quadrado n×n seguido de núcleo quadrado com loops e entradas podadas (quando não há divisor comum).
- N > M: bloco N>M da biblioteca, `DSTACK` (dual do STACK), ou design N≤M com o fluxo invertido — aceito somente quando a inversão não cria sideload.
- Trechos retos longos gerados usam esteira subterrânea expressa para reduzir entidades.

## Verificação (todas aplicadas ao arquivo final)

1. **Simulação de fluxo com contrapressão** (`scripts/deep_verify.py`): 6,8 milhões de padrões de entrada/saída no total; 577/577 aprovados (saída balanceada com qualquer entrada, entrada balanceada com qualquer saída, vazão total = min(N,M) esteiras, portas contíguas, 0 avisos de sideload/subterrâneo sem par).
2. **Teste automatizado dentro do jogo** (Factorio 2.0.77 headless, dados isolados em `scripts/ingame/`): cada blueprint é importado, construído, alimentado por loaders e medido em 9 fases (tudo ligado; metade/um terço/aleatório/uma só entrada; metade/um terço/aleatório/uma só saída). Resultado: 577/577 construídos sem colisão e sem subterrâneo sem par; pior diferença entre saídas (ou entre entradas) = **4 itens em 2700**; déficit de vazão máximo 0,15 %.
3. **Verificador de terceiros** (`tzwaan/factorio_balancers`, em `scripts/xcheck/xcheck.py`): 576 PASS, 0 FAIL (`1 to 1` não tem splitter e a ferramenta não o analisa). A mesma ferramenta confirma os 16 originais defeituosos e aprova 143/143 do Raynquist.
4. A string completa do livro foi importada no jogo: 24 sublivros, 577 blueprints com entidades.

## Tamanhos dos gerados

- mediana 453 entidades, média 689, máximo 2248 (`17 to 18`, 48x84 tiles).
- Os pares com N e M entre 17 e 24 sem divisor comum são os maiores (dois núcleos 32-32 empilhados). São corretos, porém grandes; não são layouts otimizados por SAT como os do Raynquist.

## Reproduzir

```
cd scripts
export FBTIER=blue        # blue | red | yellow
python3 gen.py            # gera todos os pares
python3 build_book.py     # monta o livro e sobrescreve blueprints/belt-balancers/$FBTIER-belt.txt
python3 deep_verify.py ../blueprints/belt-balancers/$FBTIER-belt.txt
python3 export_tests.py ../blueprints/belt-balancers/$FBTIER-belt.txt && ./run_ingame.sh 3400 && python3 analyze_ingame.py
```

O gerador lê as entradas de `scripts/sources/` (fora do git; ver [`scripts/README.md`](../../scripts/README.md)).

## Livros vermelho e amarelo

Mesma estrutura (24 sublivros × `N to 1..24`), gerados pelo mesmo pipeline com `FBTIER=red` / `FBTIER=yellow`:

- [`red-belt.txt`](red-belt.txt) — esteira vermelha (fast), subterrâneo até 7 tiles.
- [`yellow-belt.txt`](yellow-belt.txt) — esteira amarela, subterrâneo até 5 tiles.

Diferenças em relação ao azul:

- Os blocos de biblioteca são convertidos para o tipo de esteira e só entram se todos os subterrâneos continuam pareados (o `16-16` e o `32-32` do Raynquist usam túneis de 9 tiles e não servem).
- O núcleo 16×16 vermelho vem do "16-16 red" do Raynquist; o 16×16 amarelo e os dois 32×32 são construídos por duplicação (dois núcleos menores + N splitters + um roteador de desentrelaçamento em faixas, `scripts/weave.py`), todos verificados.
- Por isso os blueprints grandes (N, M ≥ 17) são maiores que os azuis: vermelho até 3605 entidades, amarelo até 4876.

### red

- origem: {'original': 49, 'raynquist': 18, 'generated': 494, 'raynquist-fix': 16}
- gerados: mediana 529 entidades, máximo 3605 (`18 to 19`, 56x175 tiles)
- verificação: simulação 577/577; teste no jogo 577/577 em 9 fases (diferença máxima 4 itens por janela de 60 s); verificador de terceiros 576 PASS / 0 FAIL.

### yellow

- origem: {'original': 49, 'raynquist': 11, 'generated': 501, 'raynquist-fix': 16}
- gerados: mediana 1036 entidades, máximo 4876 (`17 to 18`, 56x206 tiles)
- verificação: simulação 577/577; teste no jogo 577/577 em 9 fases (diferença máxima 4 itens por janela de 60 s); verificador de terceiros 576 PASS / 0 FAIL.
- nota: na esteira amarela os 18 maiores loops (`17..23 to 17..24`) levam mais de 45 000 ticks para encher; com aquecimento de 180 000 ticks a vazão medida fica em 99,97 %.

## Tabela completa (livro azul)

| Blueprint | Origem | Entidades | LxA | Construção |
|---|---|---|---|---|
| 1 to 1 | original | 3 | 1x3 | Original blueprint (kept). |
| 1 to 2 | original | 4 | 2x3 | Original blueprint (kept). |
| 1 to 3 | original | 16 | 4x5 | Original blueprint (kept). |
| 1 to 4 | original | 8 | 4x4 | Original blueprint (kept). |
| 1 to 5 | original | 25 | 5x7 | Original blueprint (kept). |
| 1 to 6 | original | 19 | 6x5 | Original blueprint (kept). |
| 1 to 7 | original | 28 | 7x6 | Original blueprint (kept). |
| 1 to 8 | original | 22 | 8x6 | Original blueprint (kept). |
| 1 to 9 | raynquist | 45 | 9x8 | Source: Raynquist's balancer book (fall 2025), '1-9 TU balancer'. |
| 1 to 10 | generated | 60 | 10x11 | Generated from verified blocks: STACK 1->2 + 2x(1->5). |
| 1 to 11 | generated | 94 | 13x21 | Generated from verified blocks: K1 P=12 nl=1 dead=[1..10;10]. |
| 1 to 12 | generated | 47 | 12x9 | Generated from verified blocks: STACK 1->2 + 2x(1->6). |
| 1 to 13 | generated | 160 | 19x22 | Generated from verified blocks: K1 P=16 nl=0 dead=[0..11;12]. |
| 1 to 14 | generated | 65 | 14x10 | Generated from verified blocks: STACK 1->2 + 2x(1->7). |
| 1 to 15 | generated | 98 | 17x18 | Generated from verified blocks: K1 P=16 nl=0 dead=[0..13;14]. |
| 1 to 16 | generated | 49 | 16x9 | Generated from verified blocks: STACK 1->2 + 2x(1->8). |
| 1 to 17 | raynquist | 72 | 17x10 | Source: Raynquist's balancer book (fall 2025), '1-17 balancer'. |
| 1 to 18 | generated | 82 | 18x11 | Generated from verified blocks: STACK 1->3 + 3x(1->6). |
| 1 to 19 | generated | 798 | 45x53 | Generated from verified blocks: K1 P=32 nl=0 dead=[0..17;18]. |
| 1 to 20 | generated | 87 | 20x13 | Generated from verified blocks: STACK 1->5 + 5x(1->4). |
| 1 to 21 | generated | 109 | 21x12 | Generated from verified blocks: STACK 1->3 + 3x(1->7). |
| 1 to 22 | generated | 208 | 22x29 | Generated from verified blocks: STACK 1->11 + 11x(1->2). |
| 1 to 23 | generated | 638 | 41x45 | Generated from verified blocks: K1 P=32 nl=0 dead=[0..21;22]. |
| 1 to 24 | generated | 85 | 24x11 | Generated from verified blocks: STACK 1->3 + 3x(1->8). |
| 2 to 1 | original | 4 | 2x3 | Original blueprint (kept). |
| 2 to 2 | original | 5 | 2x3 | Original blueprint (kept). |
| 2 to 3 (Long) | original | 25 | 5x7 | Original blueprint (kept). |
| 2 to 3 (Wide) | original | 22 | 7x5 | Original blueprint (kept). |
| 2 to 4 | original | 9 | 4x4 | Original blueprint (kept). |
| 2 to 5 | raynquist-fix | 31 | 5x8 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '2-5 balancer'. |
| 2 to 6 | original | 33 | 8x6 | Original blueprint (kept). |
| 2 to 7 | original | 33 | 8x6 | Original blueprint (kept). |
| 2 to 8 | original | 23 | 8x6 | Original blueprint (kept). |
| 2 to 9 | raynquist | 51 | 9x8 | Source: Raynquist's balancer book (fall 2025), '2-9 balancer'. |
| 2 to 10 | generated | 61 | 10x11 | Generated from verified blocks: STACK 2->2 + 2x(1->5). |
| 2 to 11 | generated | 117 | 13x24 | Generated from verified blocks: SQ(2) + K1 P=12 nl=1 dead=[2..10;9]. |
| 2 to 12 | generated | 48 | 12x9 | Generated from verified blocks: STACK 2->2 + 2x(1->6). |
| 2 to 13 | generated | 196 | 19x25 | Generated from verified blocks: SQ(2) + K1 P=16 nl=0 dead=[0..10;11]. |
| 2 to 14 | generated | 66 | 14x10 | Generated from verified blocks: STACK 2->2 + 2x(1->7). |
| 2 to 15 | generated | 108 | 15x13 | Generated from verified blocks: STACK 2->3 + 3x(1->5). |
| 2 to 16 | generated | 50 | 16x9 | Generated from verified blocks: STACK 2->2 + 2x(1->8). |
| 2 to 17 | generated | 967 | 47x46 | Generated from verified blocks: SQ(2) + K1 P=32 nl=7 dead=[2..16;15]. |
| 2 to 18 | generated | 88 | 18x11 | Generated from verified blocks: STACK 2->3 + 3x(1->6). |
| 2 to 19 | generated | 815 | 45x56 | Generated from verified blocks: SQ(2) + K1 P=32 nl=0 dead=[0..16;17]. |
| 2 to 20 | generated | 93 | 20x14 | Generated from verified blocks: STACK 2->5 + 5x(1->4). |
| 2 to 21 | generated | 115 | 21x12 | Generated from verified blocks: STACK 2->3 + 3x(1->7). |
| 2 to 22 | generated | 231 | 22x32 | Generated from verified blocks: STACK 2->11 + 11x(1->2). |
| 2 to 23 | generated | 651 | 41x48 | Generated from verified blocks: SQ(2) + K1 P=32 nl=0 dead=[0..20;21]. |
| 2 to 24 | generated | 91 | 24x11 | Generated from verified blocks: STACK 2->3 + 3x(1->8). |
| 3 to 1 | original | 18 | 4x6 | Original blueprint (kept). |
| 3 to 2 | original | 25 | 5x7 | Original blueprint (kept). |
| 3 to 3 | original | 32 | 6x7 | Original blueprint (kept). |
| 3 to 4 | original | 39 | 7x8 | Original blueprint (kept). |
| 3 to 5 | raynquist-fix | 53 | 8x9 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '3-5 balancer'. |
| 3 to 6 | original | 30 | 7x6 | Original blueprint (kept). |
| 3 to 7 | raynquist-fix | 56 | 8x10 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '3-7 balancer'. |
| 3 to 8 | original | 53 | 8x10 | Original blueprint (kept). |
| 3 to 9 | raynquist | 63 | 9x9 | Source: Raynquist's balancer book (fall 2025), '3-9 balancer'. |
| 3 to 10 | generated | 89 | 10x14 | Generated from verified blocks: STACK 3->5 + 5x(1->2). |
| 3 to 11 | generated | 144 | 13x30 | Generated from verified blocks: SQ(3) + K1 P=12 nl=1 dead=[3..10;8]. |
| 3 to 12 | generated | 63 | 12x14 | Generated from verified blocks: STACK 3->3 + 3x(1->4). |
| 3 to 13 | generated | 225 | 19x31 | Generated from verified blocks: SQ(3) + K1 P=16 nl=0 dead=[0..9;10]. |
| 3 to 14 | generated | 117 | 14x16 | Generated from verified blocks: STACK 3->7 + 7x(1->2). |
| 3 to 15 | generated | 116 | 15x17 | Generated from verified blocks: STACK 3->3 + 3x(1->5). |
| 3 to 16 | generated | 88 | 16x14 | Generated from verified blocks: STACK 3->4 + 4x(1->4). |
| 3 to 17 | generated | 996 | 47x52 | Generated from verified blocks: SQ(3) + K1 P=32 nl=7 dead=[3..16;14]. |
| 3 to 18 | generated | 96 | 18x15 | Generated from verified blocks: STACK 3->3 + 3x(1->6). |
| 3 to 19 | generated | 846 | 45x62 | Generated from verified blocks: SQ(3) + K1 P=32 nl=0 dead=[0..15;16]. |
| 3 to 20 | generated | 115 | 20x15 | Generated from verified blocks: STACK 3->5 + 5x(1->4). |
| 3 to 21 | generated | 123 | 21x16 | Generated from verified blocks: STACK 3->3 + 3x(1->7). |
| 3 to 22 | generated | 258 | 22x38 | Generated from verified blocks: STACK 3->11 + 11x(1->2). |
| 3 to 23 | generated | 680 | 41x54 | Generated from verified blocks: SQ(3) + K1 P=32 nl=0 dead=[0..19;20]. |
| 3 to 24 | generated | 99 | 24x15 | Generated from verified blocks: STACK 3->3 + 3x(1->8). |
| 4 to 1 | original | 8 | 4x4 | Original blueprint (kept). |
| 4 to 2 | original | 9 | 4x4 | Original blueprint (kept). |
| 4 to 3 | original | 39 | 7x8 | Original blueprint (kept). |
| 4 to 4 | original | 30 | 4x9 | Original blueprint (kept). |
| 4 to 5 | raynquist-fix | 57 | 8x10 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '4-5 balancer'. |
| 4 to 6 | original | 52 | 6x11 | Original blueprint (kept). |
| 4 to 7 | original | 54 | 9x9 | Original blueprint (kept). |
| 4 to 8 | original | 36 | 8x6 | Original blueprint (kept). |
| 4 to 9 | raynquist | 74 | 9x12 | Source: Raynquist's balancer book (fall 2025), '4-9 balancer'. |
| 4 to 10 | generated | 93 | 10x15 | Generated from verified blocks: STACK 4->5 + 5x(1->2). |
| 4 to 11 | generated | 149 | 13x30 | Generated from verified blocks: SQ(4) + K1 P=12 nl=1 dead=[4..10;7]. |
| 4 to 12 | raynquist | 139 | 12x16 | Source: Raynquist's balancer book (fall 2025), '4-12 TU balancer'. |
| 4 to 13 | generated | 235 | 19x31 | Generated from verified blocks: SQ(4) + K1 P=16 nl=0 dead=[0..8;9]. |
| 4 to 14 | generated | 115 | 14x15 | Generated from verified blocks: STACK 4->7 + 7x(1->2). |
| 4 to 15 | generated | 165 | 17x27 | Generated from verified blocks: SQ(4) + K1 P=16 nl=0 dead=[0..10;11]. |
| 4 to 16 | generated | 79 | 16x15 | Generated from verified blocks: STACK 4->4 + 4x(1->4). |
| 4 to 17 | generated | 1004 | 47x52 | Generated from verified blocks: SQ(4) + K1 P=32 nl=7 dead=[4..16;13]. |
| 4 to 18 | generated | 146 | 18x19 | Generated from verified blocks: STACK 4->4 + 2x(2->9). |
| 4 to 19 | generated | 954 | 45x50 | Generated from verified blocks: SQ(4) + K1 P=32 nl=6 dead=[0..14;15]. |
| 4 to 20 | generated | 119 | 20x16 | Generated from verified blocks: STACK 4->5 + 5x(1->4). |
| 4 to 21 | generated | 294 | 24x26 | Generated from verified blocks: STACK 4->6 + 3x(2->7). |
| 4 to 22 | generated | 263 | 22x38 | Generated from verified blocks: STACK 4->11 + 11x(1->2). |
| 4 to 23 | generated | 710 | 41x54 | Generated from verified blocks: SQ(4) + K1 P=32 nl=0 dead=[0..18;19]. |
| 4 to 24 | generated | 123 | 24x16 | Generated from verified blocks: STACK 4->4 + 4x(1->6). |
| 5 to 1 | original | 25 | 6x7 | Original blueprint (kept). |
| 5 to 2 | raynquist-fix | 31 | 5x8 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '5-2 balancer'. |
| 5 to 3 | raynquist-fix | 57 | 8x10 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '5-3 balancer'. |
| 5 to 4 | raynquist-fix | 57 | 8x10 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '5-4 balancer'. |
| 5 to 5 | original | 81 | 10x11 | Original blueprint (kept). |
| 5 to 6 | raynquist-fix | 86 | 8x15 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '5-6 balancer'. |
| 5 to 7 | raynquist-fix | 97 | 9x15 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '5-7 balancer'. |
| 5 to 8 | original | 119 | 10x16 | Original blueprint (kept). |
| 5 to 9 | raynquist | 117 | 9x18 | Source: Raynquist's balancer book (fall 2025), '5-9 balancer'. |
| 5 to 10 | generated | 98 | 10x17 | Generated from verified blocks: STACK 5->5 + 5x(1->2). |
| 5 to 11 | generated | 183 | 13x33 | Generated from verified blocks: SQ(5) + K1 P=12 nl=1 dead=[5, 6, 7, 8, 9, 10]. |
| 5 to 12 | generated | 133 | 12x21 | Generated from verified blocks: STACK 5->6 + 3x(2->4). |
| 5 to 13 | generated | 271 | 19x34 | Generated from verified blocks: SQ(5) + K1 P=16 nl=0 dead=[0..7;8]. |
| 5 to 14 | generated | 158 | 14x21 | Generated from verified blocks: STACK 5->7 + 7x(1->2). |
| 5 to 15 | generated | 199 | 17x30 | Generated from verified blocks: SQ(5) + K1 P=16 nl=0 dead=[0..9;10]. |
| 5 to 16 | generated | 163 | 16x21 | Generated from verified blocks: STACK 5->8 + 8x(1->2). |
| 5 to 17 | generated | 1040 | 47x55 | Generated from verified blocks: SQ(5) + K1 P=32 nl=7 dead=[5..16;12]. |
| 5 to 18 | generated | 239 | 18x27 | Generated from verified blocks: STACK 5->6 + 2x(3->9). |
| 5 to 19 | generated | 990 | 45x53 | Generated from verified blocks: SQ(5) + K1 P=32 nl=6 dead=[0..13;14]. |
| 5 to 20 | generated | 124 | 20x18 | Generated from verified blocks: STACK 5->5 + 5x(1->4). |
| 5 to 21 | generated | 329 | 24x30 | Generated from verified blocks: STACK 5->6 + 3x(2->7). |
| 5 to 22 | generated | 297 | 22x41 | Generated from verified blocks: STACK 5->11 + 11x(1->2). |
| 5 to 23 | generated | 746 | 41x57 | Generated from verified blocks: SQ(5) + K1 P=32 nl=0 dead=[0..17;18]. |
| 5 to 24 | generated | 167 | 24x22 | Generated from verified blocks: STACK 5->6 + 6x(1->4). |
| 6 to 1 | original | 21 | 6x6 | Original blueprint (kept). |
| 6 to 2 | original | 32 | 7x7 | Original blueprint (kept). |
| 6 to 3 | original | 33 | 7x7 | Original blueprint (kept). |
| 6 to 4 | original | 52 | 6x11 | Original blueprint (kept). |
| 6 to 5 | raynquist-fix | 86 | 8x15 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '6-5 balancer'. |
| 6 to 6 | original | 73 | 9x11 | Original blueprint (kept). |
| 6 to 7 | raynquist-fix | 96 | 9x14 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '6-7 balancer'. |
| 6 to 8 | original | 90 | 10x13 | Original blueprint (kept). |
| 6 to 9 | raynquist | 101 | 9x16 | Source: Raynquist's balancer book (fall 2025), '6-9 balancer'. |
| 6 to 10 | generated | 184 | 11x30 | Generated from verified blocks: SQ(6) + K1 P=10 nl=0 dead=[0, 1, 2, 3]. |
| 6 to 11 | generated | 244 | 13x34 | Generated from verified blocks: SQ(6) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 6 to 12 | generated | 112 | 12x19 | Generated from verified blocks: STACK 6->6 + 3x(2->4). |
| 6 to 13 | generated | 300 | 19x33 | Generated from verified blocks: SQ(6) + K1 P=16 nl=1 dead=[6..12;7]. |
| 6 to 14 | generated | 157 | 14x20 | Generated from verified blocks: STACK 6->7 + 7x(1->2). |
| 6 to 15 | generated | 182 | 15x23 | Generated from verified blocks: STACK 6->6 + 3x(2->5). |
| 6 to 16 | generated | 158 | 16x20 | Generated from verified blocks: STACK 6->8 + 8x(1->2). |
| 6 to 17 | generated | 1073 | 47x56 | Generated from verified blocks: SQ(6) + K1 P=32 nl=7 dead=[6..16;11]. |
| 6 to 18 | generated | 193 | 18x23 | Generated from verified blocks: STACK 6->9 + 9x(1->2). |
| 6 to 19 | generated | 1002 | 45x54 | Generated from verified blocks: SQ(6) + K1 P=32 nl=6 dead=[6..18;13]. |
| 6 to 20 | generated | 252 | 20x25 | Generated from verified blocks: STACK 6->8 + 4x(2->5). |
| 6 to 21 | generated | 308 | 24x28 | Generated from verified blocks: STACK 6->6 + 3x(2->7). |
| 6 to 22 | generated | 358 | 22x42 | Generated from verified blocks: STACK 6->11 + 11x(1->2). |
| 6 to 23 | generated | 759 | 41x58 | Generated from verified blocks: SQ(6) + K1 P=32 nl=0 dead=[0..16;17]. |
| 6 to 24 | generated | 146 | 24x20 | Generated from verified blocks: STACK 6->6 + 6x(1->4). |
| 7 to 1 | original | 30 | 7x7 | Original blueprint (kept). |
| 7 to 2 | original | 37 | 8x7 | Original blueprint (kept). |
| 7 to 3 | raynquist-fix | 53 | 9x8 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '7-3 balancer'. |
| 7 to 4 | original | 54 | 9x9 | Original blueprint (kept). |
| 7 to 5 | raynquist-fix | 97 | 9x15 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '7-5 balancer'. |
| 7 to 6 | raynquist-fix | 96 | 9x14 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '7-6 balancer'. |
| 7 to 7 | original | 91 | 10x11 | Original blueprint (kept). |
| 7 to 8 | raynquist-fix | 97 | 8x16 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '7-8 balancer'. |
| 7 to 9 | raynquist | 168 | 12x18 | Source: Raynquist's balancer book (fall 2025), '7-9 balancer'. |
| 7 to 10 | raynquist | 138 | 10x19 | Source: Raynquist's balancer book (fall 2025), '7-10 balancer'. |
| 7 to 11 | generated | 261 | 13x35 | Generated from verified blocks: SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3]. |
| 7 to 12 | generated | 234 | 12x33 | Generated from verified blocks: SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 7 to 13 | raynquist | 158 | 15x15 | Source: Raynquist's balancer book (fall 2025), '7-13 balancer'. |
| 7 to 14 | generated | 141 | 14x20 | Generated from verified blocks: STACK 7->7 + 7x(1->2). |
| 7 to 15 | generated | 227 | 17x32 | Generated from verified blocks: SQ(7) + K1 P=16 nl=0 dead=[0..7;8]. |
| 7 to 16 | generated | 177 | 16x23 | Generated from verified blocks: STACK 7->8 + 8x(1->2). |
| 7 to 17 | generated | 1092 | 47x57 | Generated from verified blocks: SQ(7) + K1 P=32 nl=7 dead=[7..16;10]. |
| 7 to 18 | generated | 260 | 18x25 | Generated from verified blocks: STACK 7->9 + 9x(1->2). |
| 7 to 19 | generated | 1042 | 45x55 | Generated from verified blocks: SQ(7) + K1 P=32 nl=6 dead=[0..11;12]. |
| 7 to 20 | generated | 245 | 20x27 | Generated from verified blocks: STACK 7->10 + 10x(1->2). |
| 7 to 21 | generated | 385 | 28x31 | Generated from verified blocks: STACK 7->7 + 7x(1->3). |
| 7 to 22 | generated | 375 | 22x43 | Generated from verified blocks: STACK 7->11 + 11x(1->2). |
| 7 to 23 | generated | 778 | 41x59 | Generated from verified blocks: SQ(7) + K1 P=32 nl=0 dead=[0..15;16]. |
| 7 to 24 | generated | 337 | 24x37 | Generated from verified blocks: STACK 7->8 + 2x(4->12). |
| 8 to 1 | original | 20 | 8x6 | Original blueprint (kept). |
| 8 to 2 | original | 21 | 8x6 | Original blueprint (kept). |
| 8 to 3 | original | 50 | 8x10 | Original blueprint (kept). |
| 8 to 4 | original | 40 | 8x7 | Original blueprint (kept). |
| 8 to 5 | original | 111 | 10x17 | Original blueprint (kept). |
| 8 to 6 | original | 90 | 10x13 | Original blueprint (kept). |
| 8 to 7 | raynquist-fix | 97 | 8x16 | Replaces the original, which failed verification. Source: Raynquist's balancer book (fall 2025), '8-7 balancer'. |
| 8 to 8 | original | 82 | 10x11 | Original blueprint (kept). |
| 8 to 9 | raynquist | 137 | 11x16 | Source: Raynquist's balancer book (fall 2025), '8-9 balancer'. |
| 8 to 10 | raynquist | 124 | 10x16 | Source: Raynquist's balancer book (fall 2025), '8-10 balancer'. |
| 8 to 11 | generated | 271 | 13x33 | Generated from verified blocks: SQ(8) + K1 P=12 nl=1 dead=[0, 9, 10]. |
| 8 to 12 | raynquist | 127 | 12x14 | Source: Raynquist's balancer book (fall 2025), '8-12 balancer'. |
| 8 to 13 | raynquist | 156 | 15x15 | Source: Raynquist's balancer book (fall 2025), '8-13 balancer'. |
| 8 to 14 | generated | 310 | 18x32 | Generated from verified blocks: SQ(8) + K1 P=16 nl=0 dead=[8, 9, 10, 11, 12, 13]. |
| 8 to 15 | generated | 274 | 17x30 | Generated from verified blocks: SQ(8) + K1 P=16 nl=0 dead=[8..14;7]. |
| 8 to 16 | generated | 156 | 16x19 | Generated from verified blocks: STACK 8->8 + 8x(1->2). |
| 8 to 17 | generated | 1098 | 47x55 | Generated from verified blocks: SQ(8) + K1 P=32 nl=7 dead=[8..16;9]. |
| 8 to 18 | generated | 229 | 18x23 | Generated from verified blocks: STACK 8->9 + 9x(1->2). |
| 8 to 19 | generated | 1047 | 45x53 | Generated from verified blocks: SQ(8) + K1 P=32 nl=6 dead=[8..18;11]. |
| 8 to 20 | generated | 231 | 20x24 | Generated from verified blocks: STACK 8->10 + 10x(1->2). |
| 8 to 21 | generated | 470 | 24x36 | Generated from verified blocks: STACK 8->9 + 3x(3->7). |
| 8 to 22 | generated | 385 | 22x41 | Generated from verified blocks: STACK 8->11 + 11x(1->2). |
| 8 to 23 | generated | 961 | 41x49 | Generated from verified blocks: SQ(8) + K1 P=32 nl=4 dead=[8..22;15]. |
| 8 to 24 | generated | 261 | 24x23 | Generated from verified blocks: STACK 8->12 + 12x(1->2). |
| 9 to 1 | raynquist | 46 | 9x8 | Source: Raynquist's balancer book (fall 2025), '9-1 TU balancer'. |
| 9 to 2 | raynquist | 51 | 10x8 | Source: Raynquist's balancer book (fall 2025), '9-2 balancer'. |
| 9 to 3 | raynquist | 64 | 10x9 | Source: Raynquist's balancer book (fall 2025), '9-3 balancer'. |
| 9 to 4 | raynquist | 79 | 9x12 | Source: Raynquist's balancer book (fall 2025), '9-4 balancer'. |
| 9 to 5 | raynquist | 118 | 9x18 | Source: Raynquist's balancer book (fall 2025), '9-5 balancer'. |
| 9 to 6 | raynquist | 101 | 9x16 | Source: Raynquist's balancer book (fall 2025), '9-6 balancer'. |
| 9 to 7 | raynquist | 167 | 12x18 | Source: Raynquist's balancer book (fall 2025), '9-7 balancer'. |
| 9 to 8 | raynquist | 137 | 11x16 | Source: Raynquist's balancer book (fall 2025), '9-8 balancer'. |
| 9 to 9 | raynquist | 136 | 11x16 | Source: Raynquist's balancer book (fall 2025), '9-9 balancer'. |
| 9 to 10 | raynquist | 197 | 11x23 | Source: Raynquist's balancer book (fall 2025), '9-10 balancer'. |
| 9 to 11 | generated | 333 | 13x37 | Generated from verified blocks: SQ(9) + K1 P=12 nl=1 dead=[9, 10]. |
| 9 to 12 | raynquist | 154 | 12x18 | Source: Raynquist's balancer book (fall 2025), '9-12 balancer'. |
| 9 to 13 | generated | 409 | 19x36 | Generated from verified blocks: SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12]. |
| 9 to 14 | generated | 373 | 18x34 | Generated from verified blocks: SQ(9) + K1 P=16 nl=1 dead=[0, 1, 2, 3, 4]. |
| 9 to 15 | generated | 338 | 17x34 | Generated from verified blocks: SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12, 13, 14]. |
| 9 to 16 | generated | 303 | 16x32 | Generated from verified blocks: SQ(9) + K1 P=16 nl=0 dead=[0..15;7]. |
| 9 to 17 | generated | 1162 | 47x59 | Generated from verified blocks: SQ(9) + K1 P=32 nl=7 dead=[9..16;8]. |
| 9 to 18 | generated | 228 | 18x23 | Generated from verified blocks: STACK 9->9 + 9x(1->2). |
| 9 to 19 | generated | 1112 | 45x57 | Generated from verified blocks: SQ(9) + K1 P=32 nl=6 dead=[0..9;10]. |
| 9 to 20 | generated | 304 | 20x31 | Generated from verified blocks: STACK 9->10 + 10x(1->2). |
| 9 to 21 | generated | 469 | 24x36 | Generated from verified blocks: STACK 9->9 + 3x(3->7). |
| 9 to 22 | generated | 447 | 22x45 | Generated from verified blocks: STACK 9->11 + 11x(1->2). |
| 9 to 23 | generated | 1031 | 41x53 | Generated from verified blocks: SQ(9) + K1 P=32 nl=4 dead=[0..13;14]. |
| 9 to 24 | generated | 288 | 24x27 | Generated from verified blocks: STACK 9->12 + 12x(1->2). |
| 10 to 1 | generated | 61 | 10x12 | Generated from verified blocks: DSTACK 5x(2->1) + 5->1. |
| 10 to 2 | generated | 67 | 10x13 | Generated from verified blocks: DSTACK 5x(2->1) + 5->2. |
| 10 to 3 | generated | 93 | 10x15 | Generated from verified blocks: DSTACK 5x(2->1) + 5->3. |
| 10 to 4 | generated | 93 | 10x15 | Generated from verified blocks: REVERSED STACK 4->5 + 5x(1->2). |
| 10 to 5 | generated | 98 | 10x17 | Generated from verified blocks: REVERSED STACK 5->5 + 5x(1->2). |
| 10 to 6 | generated | 184 | 11x30 | Generated from verified blocks: REVERSED SQ(6) + K1 P=10 nl=0 dead=[0, 1, 2, 3]. |
| 10 to 7 | generated | 212 | 11x31 | Generated from verified blocks: REV(K1 P=10 nl=0 dead=[0, 1, 2]) + SQ(7). |
| 10 to 8 | raynquist | 124 | 10x16 | Source: Raynquist's balancer book (fall 2025), '10-8 balancer'. |
| 10 to 9 | generated | 197 | 11x23 | Generated from verified blocks: REVERSED LIB. |
| 10 to 10 | raynquist | 147 | 11x17 | Source: Raynquist's balancer book (fall 2025), '10-10 balancer'. |
| 10 to 11 | generated | 353 | 14x38 | Generated from verified blocks: SQ(10) + K1p P=12 loops=0+1. |
| 10 to 12 | generated | 316 | 13x36 | Generated from verified blocks: SQ(10) + K1 P=12 nl=0 dead=[10, 11]. |
| 10 to 13 | generated | 427 | 19x37 | Generated from verified blocks: SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 10 to 14 | generated | 390 | 18x35 | Generated from verified blocks: SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2, 3]. |
| 10 to 15 | generated | 355 | 17x35 | Generated from verified blocks: SQ(10) + K1 P=16 nl=1 dead=[10, 11, 12, 13, 14]. |
| 10 to 16 | generated | 317 | 17x33 | Generated from verified blocks: SQ(10) + K1 P=16 nl=0 dead=[10, 11, 12, 13, 14, 15]. |
| 10 to 17 | generated | 1236 | 47x60 | Generated from verified blocks: SQ(10) + K1 P=32 nl=7 dead=[0..16;7]. |
| 10 to 18 | generated | 533 | 18x51 | Generated from verified blocks: STACK 10->12 + 3x(4->6). |
| 10 to 19 | generated | 1132 | 45x58 | Generated from verified blocks: SQ(10) + K1 P=32 nl=6 dead=[10..18;9]. |
| 10 to 20 | generated | 254 | 20x25 | Generated from verified blocks: STACK 10->10 + 10x(1->2). |
| 10 to 21 | generated | 684 | 27x56 | Generated from verified blocks: STACK 10->12 + 3x(4->7). |
| 10 to 22 | generated | 467 | 22x46 | Generated from verified blocks: STACK 10->11 + 11x(1->2). |
| 10 to 23 | generated | 1052 | 41x54 | Generated from verified blocks: SQ(10) + K1 P=32 nl=4 dead=[0..12;13]. |
| 10 to 24 | generated | 450 | 24x45 | Generated from verified blocks: STACK 10->12 + 12x(1->2). |
| 11 to 1 | generated | 94 | 13x21 | Generated from verified blocks: REVERSED K1 P=12 nl=1 dead=[1..10;10]. |
| 11 to 2 | generated | 117 | 13x24 | Generated from verified blocks: REVERSED SQ(2) + K1 P=12 nl=1 dead=[2..10;9]. |
| 11 to 3 | generated | 144 | 13x30 | Generated from verified blocks: REVERSED SQ(3) + K1 P=12 nl=1 dead=[3..10;8]. |
| 11 to 4 | generated | 149 | 13x30 | Generated from verified blocks: REVERSED SQ(4) + K1 P=12 nl=1 dead=[4..10;7]. |
| 11 to 5 | generated | 183 | 13x33 | Generated from verified blocks: REVERSED SQ(5) + K1 P=12 nl=1 dead=[5, 6, 7, 8, 9, 10]. |
| 11 to 6 | generated | 244 | 13x34 | Generated from verified blocks: REVERSED SQ(6) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 11 to 7 | generated | 261 | 13x35 | Generated from verified blocks: REVERSED SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3]. |
| 11 to 8 | generated | 271 | 13x33 | Generated from verified blocks: REVERSED SQ(8) + K1 P=12 nl=1 dead=[0, 9, 10]. |
| 11 to 9 | generated | 333 | 13x37 | Generated from verified blocks: REVERSED SQ(9) + K1 P=12 nl=1 dead=[9, 10]. |
| 11 to 10 | raynquist | 205 | 13x23 | Source: Raynquist's balancer book (fall 2025), '11-10 balancer'. |
| 11 to 11 | generated | 208 | 13x21 | Generated from verified blocks: LOOP(12-12) nl=0. |
| 11 to 12 | generated | 385 | 14x40 | Generated from verified blocks: SQ(11) + K1 P=12 nl=0 dead=[0]. |
| 11 to 13 | generated | 491 | 19x41 | Generated from verified blocks: SQ(11) + K1 P=16 nl=1 dead=[11, 12]. |
| 11 to 14 | generated | 453 | 18x39 | Generated from verified blocks: SQ(11) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 11 to 15 | generated | 418 | 17x39 | Generated from verified blocks: SQ(11) + K1 P=16 nl=1 dead=[11, 12, 13, 14]. |
| 11 to 16 | generated | 383 | 16x37 | Generated from verified blocks: SQ(11) + K1 P=16 nl=0 dead=[11, 12, 13, 14, 15]. |
| 11 to 17 | generated | 1292 | 47x64 | Generated from verified blocks: SQ(11) + K1 P=32 nl=7 dead=[11, 12, 13, 14, 15, 16]. |
| 11 to 18 | generated | 602 | 18x55 | Generated from verified blocks: STACK 11->12 + 3x(4->6). |
| 11 to 19 | generated | 1241 | 45x62 | Generated from verified blocks: SQ(11) + K1 P=32 nl=6 dead=[0..7;8]. |
| 11 to 20 | generated | 712 | 20x61 | Generated from verified blocks: STACK 11->16 + 2x(8->10). |
| 11 to 21 | generated | 753 | 27x60 | Generated from verified blocks: STACK 11->12 + 3x(4->7). |
| 11 to 22 | generated | 322 | 22x29 | Generated from verified blocks: STACK 11->11 + 11x(1->2). |
| 11 to 23 | generated | 1106 | 41x58 | Generated from verified blocks: SQ(11) + K1 P=32 nl=4 dead=[0..11;12]. |
| 11 to 24 | generated | 519 | 24x49 | Generated from verified blocks: STACK 11->12 + 12x(1->2). |
| 12 to 1 | generated | 51 | 12x10 | Generated from verified blocks: DSTACK 2x(6->1) + 2->1. |
| 12 to 2 | generated | 52 | 12x10 | Generated from verified blocks: DSTACK 2x(6->1) + 2->2. |
| 12 to 3 | generated | 63 | 12x14 | Generated from verified blocks: REVERSED STACK 3->3 + 3x(1->4). |
| 12 to 4 | raynquist | 139 | 12x16 | Source: Raynquist's balancer book (fall 2025), '12-4 TU balancer'. |
| 12 to 5 | generated | 133 | 12x21 | Generated from verified blocks: REVERSED STACK 5->6 + 3x(2->4). |
| 12 to 6 | generated | 112 | 12x19 | Generated from verified blocks: REVERSED STACK 6->6 + 3x(2->4). |
| 12 to 7 | generated | 234 | 12x33 | Generated from verified blocks: REVERSED SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 12 to 8 | generated | 220 | 12x27 | Generated from verified blocks: DSTACK 2x(6->4) + 8->8. |
| 12 to 9 | generated | 304 | 12x35 | Generated from verified blocks: REV(K1 P=12 nl=0 dead=[0, 10, 11]) + SQ(9). |
| 12 to 10 | raynquist | 199 | 12x22 | Source: Raynquist's balancer book (fall 2025), '12-10 balancer'. |
| 12 to 11 | generated | 385 | 14x40 | Generated from verified blocks: REVERSED SQ(11) + K1 P=12 nl=0 dead=[0]. |
| 12 to 12 | raynquist | 178 | 12x19 | Source: Raynquist's balancer book (fall 2025), '12-12 balancer'. |
| 12 to 13 | generated | 468 | 19x39 | Generated from verified blocks: SQ(12) + K1p P=16 loops=2+1. |
| 12 to 14 | generated | 429 | 18x37 | Generated from verified blocks: SQ(12) + K1p P=16 loops=1+1. |
| 12 to 15 | generated | 415 | 17x37 | Generated from verified blocks: SQ(12) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 12 to 16 | generated | 354 | 16x35 | Generated from verified blocks: SQ(12) + K1 P=16 nl=0 dead=[12, 13, 14, 15]. |
| 12 to 17 | generated | 1281 | 47x62 | Generated from verified blocks: SQ(12) + K1 P=32 nl=7 dead=[0, 1, 2, 3, 4]. |
| 12 to 18 | generated | 395 | 18x34 | Generated from verified blocks: STACK 12->12 + 3x(4->6). |
| 12 to 19 | generated | 1230 | 45x60 | Generated from verified blocks: SQ(12) + K1 P=32 nl=6 dead=[0..6;7]. |
| 12 to 20 | generated | 638 | 32x44 | Generated from verified blocks: STACK 12->12 + 4x(3->5). |
| 12 to 21 | generated | 546 | 27x39 | Generated from verified blocks: STACK 12->12 + 3x(4->7). |
| 12 to 22 | generated | 871 | 26x70 | Generated from verified blocks: STACK 12->12 + 2x(6->11). |
| 12 to 23 | generated | 1111 | 41x56 | Generated from verified blocks: SQ(12) + K1 P=32 nl=4 dead=[12..22;11]. |
| 12 to 24 | generated | 312 | 24x28 | Generated from verified blocks: STACK 12->12 + 12x(1->2). |
| 13 to 1 | generated | 160 | 19x22 | Generated from verified blocks: REVERSED K1 P=16 nl=0 dead=[0..11;12]. |
| 13 to 2 | generated | 196 | 19x25 | Generated from verified blocks: REVERSED SQ(2) + K1 P=16 nl=0 dead=[0..10;11]. |
| 13 to 3 | generated | 225 | 19x31 | Generated from verified blocks: REVERSED SQ(3) + K1 P=16 nl=0 dead=[0..9;10]. |
| 13 to 4 | generated | 235 | 19x31 | Generated from verified blocks: REVERSED SQ(4) + K1 P=16 nl=0 dead=[0..8;9]. |
| 13 to 5 | generated | 271 | 19x34 | Generated from verified blocks: REVERSED SQ(5) + K1 P=16 nl=0 dead=[0..7;8]. |
| 13 to 6 | generated | 300 | 19x33 | Generated from verified blocks: REVERSED SQ(6) + K1 P=16 nl=1 dead=[6..12;7]. |
| 13 to 7 | generated | 158 | 15x15 | Generated from verified blocks: REVERSED LIB. |
| 13 to 8 | generated | 156 | 15x15 | Generated from verified blocks: REVERSED LIB. |
| 13 to 9 | generated | 409 | 19x36 | Generated from verified blocks: REVERSED SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12]. |
| 13 to 10 | generated | 427 | 19x37 | Generated from verified blocks: REVERSED SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 13 to 11 | generated | 491 | 19x41 | Generated from verified blocks: REVERSED SQ(11) + K1 P=16 nl=1 dead=[11, 12]. |
| 13 to 12 | generated | 468 | 19x39 | Generated from verified blocks: REVERSED SQ(12) + K1p P=16 loops=2+1. |
| 13 to 13 | generated | 293 | 19x20 | Generated from verified blocks: LOOP(16-16) nl=1. |
| 13 to 14 | generated | 546 | 19x38 | Generated from verified blocks: SQ(13) + K1p P=16 loops=1+1. |
| 13 to 15 | generated | 532 | 19x38 | Generated from verified blocks: SQ(13) + K1 P=16 nl=0 dead=[0, 1]. |
| 13 to 16 | generated | 495 | 20x36 | Generated from verified blocks: SQ(13) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 13 to 17 | generated | 1374 | 47x63 | Generated from verified blocks: SQ(13) + K1 P=32 nl=7 dead=[13, 14, 15, 16]. |
| 13 to 18 | generated | 982 | 22x69 | Generated from verified blocks: STACK 13->16 + 2x(8->9). |
| 13 to 19 | generated | 1323 | 45x61 | Generated from verified blocks: SQ(13) + K1 P=32 nl=6 dead=[0, 1, 2, 3, 4, 5]. |
| 13 to 20 | generated | 824 | 22x60 | Generated from verified blocks: STACK 13->16 + 2x(8->10). |
| 13 to 21 | generated | 984 | 49x58 | Generated from verified blocks: STACK 13->14 + 7x(2->3). |
| 13 to 22 | generated | 1254 | 42x67 | Generated from verified blocks: SQ(13) + K1 P=32 nl=0 dead=[0..8;9]. |
| 13 to 23 | generated | 1211 | 41x65 | Generated from verified blocks: SQ(13) + K1 P=32 nl=0 dead=[0..9;10]. |
| 13 to 24 | generated | 802 | 24x55 | Generated from verified blocks: STACK 13->16 + 4x(4->6). |
| 14 to 1 | generated | 69 | 14x11 | Generated from verified blocks: DSTACK 2x(7->1) + 2->1. |
| 14 to 2 | generated | 70 | 14x11 | Generated from verified blocks: DSTACK 2x(7->1) + 2->2. |
| 14 to 3 | generated | 114 | 14x14 | Generated from verified blocks: DSTACK 7x(2->1) + 7->3. |
| 14 to 4 | generated | 115 | 14x15 | Generated from verified blocks: REVERSED STACK 4->7 + 7x(1->2). |
| 14 to 5 | generated | 158 | 14x21 | Generated from verified blocks: REVERSED STACK 5->7 + 7x(1->2). |
| 14 to 6 | generated | 157 | 14x20 | Generated from verified blocks: REVERSED STACK 6->7 + 7x(1->2). |
| 14 to 7 | generated | 141 | 14x20 | Generated from verified blocks: REVERSED STACK 7->7 + 7x(1->2). |
| 14 to 8 | generated | 310 | 18x32 | Generated from verified blocks: REVERSED SQ(8) + K1 P=16 nl=0 dead=[8, 9, 10, 11, 12, 13]. |
| 14 to 9 | generated | 373 | 18x34 | Generated from verified blocks: REVERSED SQ(9) + K1 P=16 nl=1 dead=[0, 1, 2, 3, 4]. |
| 14 to 10 | generated | 390 | 18x35 | Generated from verified blocks: REVERSED SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2, 3]. |
| 14 to 11 | generated | 453 | 18x39 | Generated from verified blocks: REVERSED SQ(11) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 14 to 12 | generated | 429 | 18x37 | Generated from verified blocks: REVERSED SQ(12) + K1p P=16 loops=1+1. |
| 14 to 13 | generated | 546 | 19x38 | Generated from verified blocks: REVERSED SQ(13) + K1p P=16 loops=1+1. |
| 14 to 14 | generated | 255 | 18x18 | Generated from verified blocks: LOOP(16-16) nl=1. |
| 14 to 15 | generated | 502 | 19x36 | Generated from verified blocks: SQ(14) + K1p P=16 loops=0+1. |
| 14 to 16 | generated | 458 | 18x34 | Generated from verified blocks: SQ(14) + K1 P=16 nl=0 dead=[0, 1]. |
| 14 to 17 | generated | 1367 | 47x61 | Generated from verified blocks: SQ(14) + K1 P=32 nl=7 dead=[0, 1, 2]. |
| 14 to 18 | generated | 790 | 24x52 | Generated from verified blocks: STACK 14->14 + 2x(7->9). |
| 14 to 19 | generated | 1307 | 45x59 | Generated from verified blocks: SQ(14) + K1 P=32 nl=6 dead=[14, 15, 16, 17, 18]. |
| 14 to 20 | generated | 614 | 20x44 | Generated from verified blocks: STACK 14->14 + 2x(7->10). |
| 14 to 21 | generated | 693 | 49x38 | Generated from verified blocks: STACK 14->14 + 7x(2->3). |
| 14 to 22 | generated | 983 | 26x71 | Generated from verified blocks: STACK 14->14 + 2x(7->11). |
| 14 to 23 | generated | 1195 | 41x63 | Generated from verified blocks: SQ(14) + K1 P=32 nl=0 dead=[0..8;9]. |
| 14 to 24 | generated | 765 | 24x53 | Generated from verified blocks: STACK 14->16 + 4x(4->6). |
| 15 to 1 | generated | 98 | 17x18 | Generated from verified blocks: REVERSED K1 P=16 nl=0 dead=[0..13;14]. |
| 15 to 2 | generated | 109 | 17x21 | Generated from verified blocks: REV(K1 P=16 nl=0 dead=[0..12;13]) + SQ(2). |
| 15 to 3 | generated | 136 | 17x27 | Generated from verified blocks: REV(K1 P=16 nl=0 dead=[0..11;12]) + SQ(3). |
| 15 to 4 | generated | 165 | 17x27 | Generated from verified blocks: REVERSED SQ(4) + K1 P=16 nl=0 dead=[0..10;11]. |
| 15 to 5 | generated | 199 | 17x30 | Generated from verified blocks: REVERSED SQ(5) + K1 P=16 nl=0 dead=[0..9;10]. |
| 15 to 6 | raynquist | 141 | 15x13 | Source: Raynquist's balancer book (fall 2025), '15-6 balancer'. |
| 15 to 7 | generated | 227 | 17x32 | Generated from verified blocks: REVERSED SQ(7) + K1 P=16 nl=0 dead=[0..7;8]. |
| 15 to 8 | generated | 274 | 17x30 | Generated from verified blocks: REVERSED SQ(8) + K1 P=16 nl=0 dead=[8..14;7]. |
| 15 to 9 | generated | 338 | 17x34 | Generated from verified blocks: REVERSED SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12, 13, 14]. |
| 15 to 10 | raynquist | 206 | 15x19 | Source: Raynquist's balancer book (fall 2025), '15-10 balancer'. |
| 15 to 11 | generated | 418 | 17x39 | Generated from verified blocks: REVERSED SQ(11) + K1 P=16 nl=1 dead=[11, 12, 13, 14]. |
| 15 to 12 | generated | 415 | 17x37 | Generated from verified blocks: REVERSED SQ(12) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 15 to 13 | generated | 532 | 19x38 | Generated from verified blocks: REVERSED SQ(13) + K1 P=16 nl=0 dead=[0, 1]. |
| 15 to 14 | generated | 502 | 19x36 | Generated from verified blocks: REVERSED SQ(14) + K1p P=16 loops=0+1. |
| 15 to 15 | generated | 249 | 17x18 | Generated from verified blocks: LOOP(16-16) nl=0. |
| 15 to 16 | generated | 459 | 18x34 | Generated from verified blocks: SQ(15) + K1 P=16 nl=0 dead=[0]. |
| 15 to 17 | generated | 1364 | 47x61 | Generated from verified blocks: SQ(15) + K1 P=32 nl=7 dead=[15, 16]. |
| 15 to 18 | generated | 701 | 24x44 | Generated from verified blocks: STACK 15->15 + 3x(5->6). |
| 15 to 19 | generated | 1313 | 45x59 | Generated from verified blocks: SQ(15) + K1 P=32 nl=6 dead=[0, 1, 2, 3]. |
| 15 to 20 | generated | 700 | 35x40 | Generated from verified blocks: STACK 15->15 + 5x(3->4). |
| 15 to 21 | generated | 766 | 27x45 | Generated from verified blocks: STACK 15->15 + 3x(5->7). |
| 15 to 22 | generated | 1230 | 26x86 | Generated from verified blocks: STACK 15->16 + 2x(8->11). |
| 15 to 23 | generated | 1192 | 41x63 | Generated from verified blocks: SQ(15) + K1 P=32 nl=0 dead=[0..7;8]. |
| 15 to 24 | generated | 580 | 24x37 | Generated from verified blocks: STACK 15->15 + 3x(5->8). |
| 16 to 1 | generated | 49 | 16x10 | Generated from verified blocks: DSTACK 2x(8->1) + 2->1. |
| 16 to 2 | generated | 50 | 16x10 | Generated from verified blocks: DSTACK 2x(8->1) + 2->2. |
| 16 to 3 | generated | 88 | 16x14 | Generated from verified blocks: REVERSED STACK 3->4 + 4x(1->4). |
| 16 to 4 | generated | 79 | 16x15 | Generated from verified blocks: REVERSED STACK 4->4 + 4x(1->4). |
| 16 to 5 | generated | 163 | 16x21 | Generated from verified blocks: REVERSED STACK 5->8 + 8x(1->2). |
| 16 to 6 | generated | 156 | 16x20 | Generated from verified blocks: DSTACK 8x(2->1) + 8->6. |
| 16 to 7 | generated | 177 | 16x23 | Generated from verified blocks: REVERSED STACK 7->8 + 8x(1->2). |
| 16 to 8 | raynquist | 286 | 16x24 | Source: Raynquist's balancer book (fall 2025), '16-8 TU balancer'. |
| 16 to 9 | generated | 303 | 16x32 | Generated from verified blocks: REVERSED SQ(9) + K1 P=16 nl=0 dead=[0..15;7]. |
| 16 to 10 | raynquist | 197 | 16x22 | Source: Raynquist's balancer book (fall 2025), '16-10 balancer'. |
| 16 to 11 | generated | 383 | 16x37 | Generated from verified blocks: REVERSED SQ(11) + K1 P=16 nl=0 dead=[11, 12, 13, 14, 15]. |
| 16 to 12 | generated | 354 | 16x35 | Generated from verified blocks: REVERSED SQ(12) + K1 P=16 nl=0 dead=[12, 13, 14, 15]. |
| 16 to 13 | generated | 495 | 20x36 | Generated from verified blocks: REVERSED SQ(13) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 16 to 14 | generated | 458 | 18x34 | Generated from verified blocks: REVERSED SQ(14) + K1 P=16 nl=0 dead=[0, 1]. |
| 16 to 15 | generated | 459 | 18x34 | Generated from verified blocks: REVERSED SQ(15) + K1 P=16 nl=0 dead=[0]. |
| 16 to 16 | raynquist | 211 | 16x16 | Source: Raynquist's balancer book (fall 2025), '16-16 balancer'. |
| 16 to 17 | generated | 1351 | 47x59 | Generated from verified blocks: SQ(16) + K1 P=32 nl=7 dead=[0]. |
| 16 to 18 | generated | 698 | 22x49 | Generated from verified blocks: STACK 16->16 + 2x(8->9). |
| 16 to 19 | generated | 1300 | 45x57 | Generated from verified blocks: SQ(16) + K1 P=32 nl=6 dead=[0, 1, 2]. |
| 16 to 20 | generated | 540 | 20x40 | Generated from verified blocks: STACK 16->16 + 2x(8->10). |
| 16 to 21 | generated | 1200 | 27x76 | Generated from verified blocks: STACK 16->18 + 3x(6->7). |
| 16 to 22 | generated | 982 | 26x68 | Generated from verified blocks: STACK 16->16 + 2x(8->11). |
| 16 to 23 | generated | 1219 | 41x53 | Generated from verified blocks: SQ(16) + K1 P=32 nl=4 dead=[0..6;7]. |
| 16 to 24 | generated | 518 | 24x35 | Generated from verified blocks: STACK 16->16 + 4x(4->6). |
| 17 to 1 | generated | 875 | 47x57 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..15;16]) + SQ(1). |
| 17 to 2 | generated | 950 | 47x46 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[2..16;15]) + SQ(2). |
| 17 to 3 | generated | 979 | 47x52 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[3..16;14]) + SQ(3). |
| 17 to 4 | generated | 987 | 47x52 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[4..16;13]) + SQ(4). |
| 17 to 5 | generated | 1023 | 47x55 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[5..16;12]) + SQ(5). |
| 17 to 6 | generated | 1056 | 47x56 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[6..16;11]) + SQ(6). |
| 17 to 7 | generated | 1075 | 47x57 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[7..16;10]) + SQ(7). |
| 17 to 8 | generated | 1081 | 47x55 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[8..16;9]) + SQ(8). |
| 17 to 9 | generated | 1145 | 47x59 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[9..16;8]) + SQ(9). |
| 17 to 10 | generated | 1219 | 47x60 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[0..16;7]) + SQ(10). |
| 17 to 11 | generated | 1275 | 47x64 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[11, 12, 13, 14, 15, 16]) + SQ(11). |
| 17 to 12 | generated | 1264 | 47x62 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[0, 1, 2, 3, 4]) + SQ(12). |
| 17 to 13 | generated | 1357 | 47x63 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[13, 14, 15, 16]) + SQ(13). |
| 17 to 14 | generated | 1350 | 47x61 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[0, 1, 2]) + SQ(14). |
| 17 to 15 | generated | 1347 | 47x61 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[15, 16]) + SQ(15). |
| 17 to 16 | generated | 1334 | 47x59 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[0]) + SQ(16). |
| 17 to 17 | generated | 1144 | 47x43 | Generated from verified blocks: LOOP(32-32) nl=7. |
| 17 to 18 | generated | 2248 | 48x84 | Generated from verified blocks: SQ(17) + K1 P=32 nl=7 dead=[0]. |
| 17 to 19 | generated | 2220 | 47x84 | Generated from verified blocks: SQ(17) + K1 P=32 nl=6 dead=[0, 1]. |
| 17 to 20 | generated | 2198 | 48x82 | Generated from verified blocks: SQ(17) + K1 P=32 nl=6 dead=[0, 1, 2]. |
| 17 to 21 | generated | 2174 | 47x82 | Generated from verified blocks: SQ(17) + K1 P=32 nl=5 dead=[17, 18, 19, 20]. |
| 17 to 22 | generated | 2173 | 49x84 | Generated from verified blocks: SQ(17) + K1p P=32 loops=7+3. |
| 17 to 23 | generated | 2139 | 47x80 | Generated from verified blocks: SQ(17) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4, 5]. |
| 17 to 24 | generated | 2097 | 48x78 | Generated from verified blocks: SQ(17) + K1 P=32 nl=4 dead=[0..6;7]. |
| 18 to 1 | generated | 90 | 18x13 | Generated from verified blocks: DSTACK 3x(6->1) + 3->1. |
| 18 to 2 | generated | 97 | 18x14 | Generated from verified blocks: DSTACK 3x(6->1) + 3->2. |
| 18 to 3 | generated | 102 | 18x16 | Generated from verified blocks: DSTACK 3x(6->1) + 3->3. |
| 18 to 4 | generated | 171 | 18x19 | Generated from verified blocks: DSTACK 9x(2->1) + 9->4. |
| 18 to 5 | generated | 210 | 18x25 | Generated from verified blocks: DSTACK 9x(2->1) + 9->5. |
| 18 to 6 | generated | 193 | 18x23 | Generated from verified blocks: DSTACK 9x(2->1) + 9->6. |
| 18 to 7 | generated | 259 | 18x25 | Generated from verified blocks: DSTACK 9x(2->1) + 9->7. |
| 18 to 8 | generated | 229 | 18x23 | Generated from verified blocks: REVERSED STACK 8->9 + 9x(1->2). |
| 18 to 9 | generated | 228 | 18x23 | Generated from verified blocks: REVERSED STACK 9->9 + 9x(1->2). |
| 18 to 10 | generated | 419 | 18x37 | Generated from verified blocks: DSTACK 3x(6->4) + 12->10. |
| 18 to 11 | generated | 605 | 18x55 | Generated from verified blocks: DSTACK 3x(6->4) + 12->11. |
| 18 to 12 | generated | 398 | 18x34 | Generated from verified blocks: DSTACK 3x(6->4) + 12->12. |
| 18 to 13 | generated | 976 | 22x69 | Generated from verified blocks: REVERSED STACK 13->16 + 2x(8->9). |
| 18 to 14 | generated | 811 | 24x53 | Generated from verified blocks: DSTACK 2x(9->7) + 14->14. |
| 18 to 15 | generated | 693 | 24x44 | Generated from verified blocks: REVERSED STACK 15->15 + 3x(5->6). |
| 18 to 16 | generated | 692 | 22x49 | Generated from verified blocks: REVERSED STACK 16->16 + 2x(8->9). |
| 18 to 17 | generated | 2230 | 47x84 | Generated from verified blocks: REV(K1 P=32 nl=7 dead=[0]) + SQ(17). |
| 18 to 18 | generated | 1125 | 46x41 | Generated from verified blocks: LOOP(32-32) nl=7. |
| 18 to 19 | generated | 2210 | 46x82 | Generated from verified blocks: SQ(18) + K1 P=32 nl=6 dead=[0]. |
| 18 to 20 | generated | 1706 | 46x83 | Generated from verified blocks: STACK 18->18 + 2x(9->10). |
| 18 to 21 | generated | 1647 | 46x68 | Generated from verified blocks: STACK 18->18 + 3x(6->7). |
| 18 to 22 | generated | 2026 | 46x98 | Generated from verified blocks: STACK 18->18 + 2x(9->11). |
| 18 to 23 | generated | 2129 | 46x78 | Generated from verified blocks: SQ(18) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 18 to 24 | generated | 1447 | 46x60 | Generated from verified blocks: STACK 18->18 + 3x(6->8). |
| 19 to 1 | generated | 796 | 45x53 | Generated from verified blocks: REVERSED K1 P=32 nl=0 dead=[0..17;18]. |
| 19 to 2 | generated | 813 | 45x56 | Generated from verified blocks: REVERSED SQ(2) + K1 P=32 nl=0 dead=[0..16;17]. |
| 19 to 3 | generated | 844 | 45x62 | Generated from verified blocks: REVERSED SQ(3) + K1 P=32 nl=0 dead=[0..15;16]. |
| 19 to 4 | generated | 935 | 45x50 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0..14;15]) + SQ(4). |
| 19 to 5 | generated | 971 | 45x53 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0..13;14]) + SQ(5). |
| 19 to 6 | generated | 983 | 45x54 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[6..18;13]) + SQ(6). |
| 19 to 7 | generated | 1023 | 45x55 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0..11;12]) + SQ(7). |
| 19 to 8 | generated | 1028 | 45x53 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[8..18;11]) + SQ(8). |
| 19 to 9 | generated | 1093 | 45x57 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0..9;10]) + SQ(9). |
| 19 to 10 | generated | 1113 | 45x58 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[10..18;9]) + SQ(10). |
| 19 to 11 | generated | 1222 | 45x62 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0..7;8]) + SQ(11). |
| 19 to 12 | generated | 1211 | 45x60 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0..6;7]) + SQ(12). |
| 19 to 13 | generated | 1304 | 45x61 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0, 1, 2, 3, 4, 5]) + SQ(13). |
| 19 to 14 | generated | 1288 | 45x59 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[14, 15, 16, 17, 18]) + SQ(14). |
| 19 to 15 | generated | 1294 | 45x59 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0, 1, 2, 3]) + SQ(15). |
| 19 to 16 | generated | 1281 | 45x57 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0, 1, 2]) + SQ(16). |
| 19 to 17 | generated | 2201 | 47x84 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0, 1]) + SQ(17). |
| 19 to 18 | generated | 2191 | 46x82 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0]) + SQ(18). |
| 19 to 19 | generated | 1107 | 45x41 | Generated from verified blocks: LOOP(32-32) nl=6. |
| 19 to 20 | generated | 2173 | 46x80 | Generated from verified blocks: SQ(19) + K1 P=32 nl=6 dead=[0]. |
| 19 to 21 | generated | 2149 | 45x80 | Generated from verified blocks: SQ(19) + K1 P=32 nl=5 dead=[19, 20]. |
| 19 to 22 | generated | 2139 | 47x82 | Generated from verified blocks: SQ(19) + K1p P=32 loops=7+3. |
| 19 to 23 | generated | 2114 | 45x78 | Generated from verified blocks: SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3]. |
| 19 to 24 | generated | 2072 | 46x76 | Generated from verified blocks: SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 20 to 1 | generated | 87 | 20x13 | Generated from verified blocks: DSTACK 5x(4->1) + 5->1. |
| 20 to 2 | generated | 93 | 20x14 | Generated from verified blocks: DSTACK 5x(4->1) + 5->2. |
| 20 to 3 | generated | 119 | 20x16 | Generated from verified blocks: DSTACK 5x(4->1) + 5->3. |
| 20 to 4 | generated | 119 | 20x16 | Generated from verified blocks: REVERSED STACK 4->5 + 5x(1->4). |
| 20 to 5 | generated | 124 | 20x18 | Generated from verified blocks: REVERSED STACK 5->5 + 5x(1->4). |
| 20 to 6 | generated | 250 | 20x25 | Generated from verified blocks: DSTACK 4x(5->2) + 8->6. |
| 20 to 7 | generated | 271 | 20x28 | Generated from verified blocks: DSTACK 4x(5->2) + 8->7. |
| 20 to 8 | generated | 229 | 20x24 | Generated from verified blocks: REVERSED STACK 8->10 + 10x(1->2). |
| 20 to 9 | generated | 302 | 20x31 | Generated from verified blocks: REVERSED STACK 9->10 + 10x(1->2). |
| 20 to 10 | generated | 252 | 20x25 | Generated from verified blocks: REVERSED STACK 10->10 + 10x(1->2). |
| 20 to 11 | generated | 710 | 20x61 | Generated from verified blocks: REVERSED STACK 11->16 + 2x(8->10). |
| 20 to 12 | generated | 646 | 32x46 | Generated from verified blocks: DSTACK 4x(5->3) + 12->12. |
| 20 to 13 | generated | 822 | 22x60 | Generated from verified blocks: REVERSED STACK 13->16 + 2x(8->10). |
| 20 to 14 | generated | 787 | 20x58 | Generated from verified blocks: DSTACK 2x(10->8) + 16->14. |
| 20 to 15 | raynquist | 277 | 20x19 | Source: Raynquist's balancer book (fall 2025), '20-15 balancer'. |
| 20 to 16 | generated | 538 | 20x40 | Generated from verified blocks: REVERSED STACK 16->16 + 2x(8->10). |
| 20 to 17 | generated | 2178 | 47x82 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0, 1, 2]) + SQ(17). |
| 20 to 18 | generated | 1691 | 46x84 | Generated from verified blocks: DSTACK 2x(10->9) + 18->18. |
| 20 to 19 | generated | 2153 | 45x80 | Generated from verified blocks: REV(K1 P=32 nl=6 dead=[0]) + SQ(19). |
| 20 to 20 | generated | 1089 | 44x39 | Generated from verified blocks: LOOP(32-32) nl=6. |
| 20 to 21 | generated | 2140 | 44x78 | Generated from verified blocks: SQ(20) + K1 P=32 nl=5 dead=[0]. |
| 20 to 22 | generated | 2052 | 44x98 | Generated from verified blocks: STACK 20->20 + 2x(10->11). |
| 20 to 23 | generated | 2102 | 44x78 | Generated from verified blocks: SQ(20) + K1p P=32 loops=6+3. |
| 20 to 24 | generated | 1753 | 44x76 | Generated from verified blocks: STACK 20->20 + 4x(5->6). |
| 21 to 1 | generated | 117 | 21x14 | Generated from verified blocks: DSTACK 3x(7->1) + 3->1. |
| 21 to 2 | generated | 124 | 21x15 | Generated from verified blocks: DSTACK 3x(7->1) + 3->2. |
| 21 to 3 | generated | 129 | 21x17 | Generated from verified blocks: DSTACK 3x(7->1) + 3->3. |
| 21 to 4 | generated | 289 | 24x27 | Generated from verified blocks: DSTACK 3x(7->2) + 6->4. |
| 21 to 5 | generated | 323 | 24x31 | Generated from verified blocks: DSTACK 3x(7->2) + 6->5. |
| 21 to 6 | generated | 302 | 24x29 | Generated from verified blocks: DSTACK 3x(7->2) + 6->6. |
| 21 to 7 | generated | 390 | 28x33 | Generated from verified blocks: DSTACK 7x(3->1) + 7->7. |
| 21 to 8 | generated | 466 | 27x35 | Generated from verified blocks: DSTACK 3x(7->3) + 9->8. |
| 21 to 9 | generated | 465 | 27x35 | Generated from verified blocks: DSTACK 3x(7->3) + 9->9. |
| 21 to 10 | generated | 558 | 27x43 | Generated from verified blocks: DSTACK 3x(7->4) + 12->10. |
| 21 to 11 | generated | 744 | 27x61 | Generated from verified blocks: DSTACK 3x(7->4) + 12->11. |
| 21 to 12 | generated | 537 | 27x40 | Generated from verified blocks: DSTACK 3x(7->4) + 12->12. |
| 21 to 13 | generated | 974 | 35x61 | Generated from verified blocks: DSTACK 7x(3->2) + 14->13. |
| 21 to 14 | generated | 683 | 35x41 | Generated from verified blocks: DSTACK 7x(3->2) + 14->14. |
| 21 to 15 | generated | 755 | 27x46 | Generated from verified blocks: DSTACK 3x(7->5) + 15->15. |
| 21 to 16 | generated | 1189 | 27x77 | Generated from verified blocks: DSTACK 3x(7->6) + 18->16. |
| 21 to 17 | generated | 2153 | 49x82 | Generated from verified blocks: REV(K1 P=32 nl=5 dead=[17, 18, 19, 20]) + SQ(17). |
| 21 to 18 | generated | 1635 | 46x68 | Generated from verified blocks: REVERSED STACK 18->18 + 3x(6->7). |
| 21 to 19 | generated | 2128 | 47x80 | Generated from verified blocks: REV(K1 P=32 nl=5 dead=[19, 20]) + SQ(19). |
| 21 to 20 | generated | 2119 | 44x78 | Generated from verified blocks: REV(K1 P=32 nl=5 dead=[0]) + SQ(20). |
| 21 to 21 | generated | 1075 | 43x39 | Generated from verified blocks: LOOP(32-32) nl=5. |
| 21 to 22 | generated | 2131 | 51x84 | Generated from verified blocks: SQ(21) + K1p P=32 loops=9+1. |
| 21 to 23 | generated | 2097 | 47x80 | Generated from verified blocks: SQ(21) + K1p P=32 loops=7+2. |
| 21 to 24 | generated | 1456 | 43x62 | Generated from verified blocks: STACK 21->21 + 3x(7->8). |
| 22 to 1 | generated | 204 | 22x29 | Generated from verified blocks: REVERSED STACK 1->11 + 11x(1->2). |
| 22 to 2 | generated | 227 | 22x32 | Generated from verified blocks: REVERSED STACK 2->11 + 11x(1->2). |
| 22 to 3 | generated | 254 | 22x38 | Generated from verified blocks: REVERSED STACK 3->11 + 11x(1->2). |
| 22 to 4 | generated | 259 | 22x38 | Generated from verified blocks: REVERSED STACK 4->11 + 11x(1->2). |
| 22 to 5 | generated | 293 | 22x41 | Generated from verified blocks: REVERSED STACK 5->11 + 11x(1->2). |
| 22 to 6 | generated | 354 | 22x42 | Generated from verified blocks: REVERSED STACK 6->11 + 11x(1->2). |
| 22 to 7 | generated | 371 | 22x43 | Generated from verified blocks: REVERSED STACK 7->11 + 11x(1->2). |
| 22 to 8 | generated | 381 | 22x41 | Generated from verified blocks: REVERSED STACK 8->11 + 11x(1->2). |
| 22 to 9 | generated | 443 | 22x45 | Generated from verified blocks: REVERSED STACK 9->11 + 11x(1->2). |
| 22 to 10 | generated | 324 | 22x31 | Generated from verified blocks: DSTACK 11x(2->1) + 11->10. |
| 22 to 11 | generated | 318 | 22x29 | Generated from verified blocks: REVERSED STACK 11->11 + 11x(1->2). |
| 22 to 12 | generated | 861 | 26x71 | Generated from verified blocks: DSTACK 2x(11->6) + 12->12. |
| 22 to 13 | generated | 1232 | 42x67 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..8;9]) + SQ(13). |
| 22 to 14 | generated | 972 | 26x72 | Generated from verified blocks: DSTACK 2x(11->7) + 14->14. |
| 22 to 15 | generated | 946 | 26x64 | Generated from verified blocks: DSTACK 2x(11->10) + 20->15. |
| 22 to 16 | generated | 972 | 26x69 | Generated from verified blocks: DSTACK 2x(11->8) + 16->16. |
| 22 to 17 | generated | 2134 | 47x80 | Generated from verified blocks: REV(K1 P=32 nl=5 dead=[0, 1, 2, 3, 4]) + SQ(17). |
| 22 to 18 | generated | 2015 | 46x99 | Generated from verified blocks: DSTACK 2x(11->9) + 18->18. |
| 22 to 19 | generated | 2109 | 45x78 | Generated from verified blocks: REV(K1 P=32 nl=5 dead=[0, 1, 2]) + SQ(19). |
| 22 to 20 | generated | 1740 | 44x84 | Generated from verified blocks: DSTACK 2x(11->10) + 20->20. |
| 22 to 21 | generated | 2089 | 43x76 | Generated from verified blocks: REV(K1 P=32 nl=5 dead=[0]) + SQ(21). |
| 22 to 22 | generated | 1083 | 42x37 | Generated from verified blocks: LOOP(32-32) nl=5. |
| 22 to 23 | generated | 2038 | 42x74 | Generated from verified blocks: SQ(22) + K1 P=32 nl=4 dead=[0]. |
| 22 to 24 | generated | 1992 | 42x72 | Generated from verified blocks: SQ(22) + K1 P=32 nl=4 dead=[0, 1]. |
| 23 to 1 | generated | 616 | 41x45 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..21;22]) + SQ(1). |
| 23 to 2 | generated | 628 | 41x48 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..20;21]) + SQ(2). |
| 23 to 3 | generated | 657 | 41x54 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..19;20]) + SQ(3). |
| 23 to 4 | generated | 687 | 41x54 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..18;19]) + SQ(4). |
| 23 to 5 | generated | 723 | 41x57 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..17;18]) + SQ(5). |
| 23 to 6 | generated | 736 | 41x58 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..16;17]) + SQ(6). |
| 23 to 7 | generated | 755 | 41x59 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..15;16]) + SQ(7). |
| 23 to 8 | generated | 913 | 41x49 | Generated from verified blocks: REVERSED SQ(8) + K1 P=32 nl=4 dead=[8..22;15]. |
| 23 to 9 | generated | 983 | 41x53 | Generated from verified blocks: REVERSED SQ(9) + K1 P=32 nl=4 dead=[0..13;14]. |
| 23 to 10 | generated | 1004 | 41x54 | Generated from verified blocks: REVERSED SQ(10) + K1 P=32 nl=4 dead=[0..12;13]. |
| 23 to 11 | generated | 1058 | 41x58 | Generated from verified blocks: REVERSED SQ(11) + K1 P=32 nl=4 dead=[0..11;12]. |
| 23 to 12 | generated | 1063 | 41x56 | Generated from verified blocks: REVERSED SQ(12) + K1 P=32 nl=4 dead=[12..22;11]. |
| 23 to 13 | generated | 1188 | 41x65 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..9;10]) + SQ(13). |
| 23 to 14 | generated | 1172 | 41x63 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..8;9]) + SQ(14). |
| 23 to 15 | generated | 1169 | 41x63 | Generated from verified blocks: REV(K1 P=32 nl=0 dead=[0..7;8]) + SQ(15). |
| 23 to 16 | generated | 1171 | 41x53 | Generated from verified blocks: REVERSED SQ(16) + K1 P=32 nl=4 dead=[0..6;7]. |
| 23 to 17 | generated | 2087 | 47x80 | Generated from verified blocks: REVERSED SQ(17) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4, 5]. |
| 23 to 18 | generated | 2077 | 46x78 | Generated from verified blocks: REVERSED SQ(18) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 23 to 19 | generated | 2062 | 45x78 | Generated from verified blocks: REVERSED SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3]. |
| 23 to 20 | generated | 2074 | 45x76 | Generated from verified blocks: REV(K1 P=32 nl=4 dead=[20, 21, 22]) + SQ(20). |
| 23 to 21 | generated | 2065 | 43x76 | Generated from verified blocks: REV(K1 P=32 nl=4 dead=[0, 1]) + SQ(21). |
| 23 to 22 | generated | 1986 | 42x74 | Generated from verified blocks: REVERSED SQ(22) + K1 P=32 nl=4 dead=[0]. |
| 23 to 23 | generated | 1069 | 41x37 | Generated from verified blocks: LOOP(32-32) nl=4. |
| 23 to 24 | generated | 1981 | 42x72 | Generated from verified blocks: SQ(23) + K1 P=32 nl=4 dead=[0]. |
| 24 to 1 | generated | 87 | 24x13 | Generated from verified blocks: DSTACK 3x(8->1) + 3->1. |
| 24 to 2 | generated | 94 | 24x14 | Generated from verified blocks: DSTACK 3x(8->1) + 3->2. |
| 24 to 3 | generated | 99 | 24x16 | Generated from verified blocks: DSTACK 3x(8->1) + 3->3. |
| 24 to 4 | generated | 131 | 24x17 | Generated from verified blocks: DSTACK 4x(6->1) + 4->4. |
| 24 to 5 | generated | 167 | 24x22 | Generated from verified blocks: REVERSED STACK 5->6 + 6x(1->4). |
| 24 to 6 | generated | 146 | 24x20 | Generated from verified blocks: REVERSED STACK 6->6 + 6x(1->4). |
| 24 to 7 | generated | 353 | 24x30 | Generated from verified blocks: DSTACK 3x(8->3) + 9->7. |
| 24 to 8 | generated | 323 | 24x28 | Generated from verified blocks: DSTACK 3x(8->3) + 9->8. |
| 24 to 9 | generated | 322 | 24x28 | Generated from verified blocks: DSTACK 3x(8->3) + 9->9. |
| 24 to 10 | generated | 333 | 24x31 | Generated from verified blocks: DSTACK 12x(2->1) + 12->10. |
| 24 to 11 | generated | 515 | 24x49 | Generated from verified blocks: REVERSED STACK 11->12 + 12x(1->2). |
| 24 to 12 | generated | 308 | 24x28 | Generated from verified blocks: REVERSED STACK 12->12 + 12x(1->2). |
| 24 to 13 | generated | 806 | 24x55 | Generated from verified blocks: DSTACK 4x(6->4) + 16->13. |
| 24 to 14 | generated | 769 | 24x53 | Generated from verified blocks: DSTACK 4x(6->4) + 16->14. |
| 24 to 15 | generated | 576 | 24x37 | Generated from verified blocks: REVERSED STACK 15->15 + 3x(5->8). |
| 24 to 16 | generated | 522 | 24x35 | Generated from verified blocks: DSTACK 4x(6->4) + 16->16. |
| 24 to 17 | generated | 2093 | 48x78 | Generated from verified blocks: REVERSED SQ(17) + K1 P=32 nl=4 dead=[0..6;7]. |
| 24 to 18 | generated | 1439 | 46x60 | Generated from verified blocks: DSTACK 3x(8->6) + 18->18. |
| 24 to 19 | generated | 2068 | 46x76 | Generated from verified blocks: REVERSED SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 24 to 20 | generated | 1572 | 44x71 | Generated from verified blocks: DSTACK 2x(12->10) + 20->20. |
| 24 to 21 | generated | 1448 | 43x62 | Generated from verified blocks: REVERSED STACK 21->21 + 3x(7->8). |
| 24 to 22 | generated | 1988 | 42x72 | Generated from verified blocks: REVERSED SQ(22) + K1 P=32 nl=4 dead=[0, 1]. |
| 24 to 23 | generated | 1979 | 42x72 | Generated from verified blocks: REVERSED SQ(23) + K1 P=32 nl=4 dead=[0]. |
| 24 to 24 | generated | 1055 | 40x35 | Generated from verified blocks: LOOP(32-32) nl=4. |
