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
2. **Teste automatizado dentro do jogo** (Factorio 2.0.77 headless, dados isolados em `scripts/ingame/`): cada blueprint é importado, construído, alimentado por loaders e medido em 9 fases (tudo ligado; metade/um terço/aleatório/uma só entrada; metade/um terço/aleatório/uma só saída). Resultado: 577/577 construídos sem colisão e sem subterrâneo sem par; pior diferença entre saídas (ou entre entradas) = **4 itens em 2.700**; déficit de vazão máximo 0,15 %.
3. **Verificador de terceiros** (`tzwaan/factorio_balancers`, em `scripts/xcheck/xcheck.py`): 576 PASS, 0 FAIL (`1 to 1` não tem splitter e a ferramenta não o analisa). A mesma ferramenta confirma os 16 originais defeituosos e aprova 143/143 do Raynquist.
4. A string completa do livro foi importada no jogo: 24 sublivros, 577 blueprints com entidades.

## Tamanhos dos gerados

- mediana 453 entidades, média 690, máximo 2.248 (`17 to 18`, 48 × 84 tiles).
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
- Por isso os blueprints grandes (N, M ≥ 17) são maiores que os azuis: vermelho até 3.605 entidades, amarelo até 4.876.

### Vermelho

- origem: `{'original': 49, 'raynquist': 18, 'generated': 494, 'raynquist-fix': 16}`
- gerados: mediana 529 entidades, máximo 3.605 (`18 to 19`, 56 × 175 tiles)
- verificação: simulação 577/577; teste no jogo 577/577 em 9 fases (diferença máxima 4 itens por janela de 60 s); verificador de terceiros 576 PASS / 0 FAIL.

### Amarelo

- origem: `{'original': 49, 'raynquist': 11, 'generated': 501, 'raynquist-fix': 16}`
- gerados: mediana 1.036 entidades, máximo 4.876 (`17 to 18`, 56 × 206 tiles)
- verificação: simulação 577/577; teste no jogo 577/577 em 9 fases (diferença máxima 4 itens por janela de 60 s); verificador de terceiros 576 PASS / 0 FAIL.
- nota: na esteira amarela os 18 maiores loops (`17..23 to 17..24`) levam mais de 45.000 ticks para encher; com aquecimento de 180.000 ticks a vazão medida fica em 99,97 %.

## Tabela completa (livro azul)

| Blueprint | Origem | Entidades | LxA | Construção |
|---|---|---|---|---|
| 1 to 1 | `original` | 3 | 1x3 | Blueprint original (mantido). |
| 1 to 2 | `original` | 4 | 2x3 | Blueprint original (mantido). |
| 1 to 3 | `original` | 16 | 4x5 | Blueprint original (mantido). |
| 1 to 4 | `original` | 8 | 4x4 | Blueprint original (mantido). |
| 1 to 5 | `original` | 25 | 5x7 | Blueprint original (mantido). |
| 1 to 6 | `original` | 19 | 6x5 | Blueprint original (mantido). |
| 1 to 7 | `original` | 28 | 7x6 | Blueprint original (mantido). |
| 1 to 8 | `original` | 22 | 8x6 | Blueprint original (mantido). |
| 1 to 9 | `raynquist` | 45 | 9x8 | Fonte: livro de balanceadores do Raynquist (fall 2025), '1-9 TU balancer'. |
| 1 to 10 | `generated` | 60 | 10x11 | Gerado com blocos verificados: STACK 1->2 + 2x(1->5). |
| 1 to 11 | `generated` | 94 | 13x21 | Gerado com blocos verificados: K1 P=12 nl=1 dead=[1..10;10]. |
| 1 to 12 | `generated` | 47 | 12x9 | Gerado com blocos verificados: STACK 1->2 + 2x(1->6). |
| 1 to 13 | `generated` | 160 | 19x22 | Gerado com blocos verificados: K1 P=16 nl=0 dead=[0..11;12]. |
| 1 to 14 | `generated` | 65 | 14x10 | Gerado com blocos verificados: STACK 1->2 + 2x(1->7). |
| 1 to 15 | `generated` | 98 | 17x18 | Gerado com blocos verificados: K1 P=16 nl=0 dead=[0..13;14]. |
| 1 to 16 | `generated` | 49 | 16x9 | Gerado com blocos verificados: STACK 1->2 + 2x(1->8). |
| 1 to 17 | `raynquist` | 72 | 17x10 | Fonte: livro de balanceadores do Raynquist (fall 2025), '1-17 balancer'. |
| 1 to 18 | `generated` | 82 | 18x11 | Gerado com blocos verificados: STACK 1->3 + 3x(1->6). |
| 1 to 19 | `generated` | 798 | 45x53 | Gerado com blocos verificados: K1 P=32 nl=0 dead=[0..17;18]. |
| 1 to 20 | `generated` | 87 | 20x13 | Gerado com blocos verificados: STACK 1->5 + 5x(1->4). |
| 1 to 21 | `generated` | 109 | 21x12 | Gerado com blocos verificados: STACK 1->3 + 3x(1->7). |
| 1 to 22 | `generated` | 208 | 22x29 | Gerado com blocos verificados: STACK 1->11 + 11x(1->2). |
| 1 to 23 | `generated` | 638 | 41x45 | Gerado com blocos verificados: K1 P=32 nl=0 dead=[0..21;22]. |
| 1 to 24 | `generated` | 85 | 24x11 | Gerado com blocos verificados: STACK 1->3 + 3x(1->8). |
| 2 to 1 | `original` | 4 | 2x3 | Blueprint original (mantido). |
| 2 to 2 | `original` | 5 | 2x3 | Blueprint original (mantido). |
| 2 to 3 (Long) | `original` | 25 | 5x7 | Blueprint original (mantido). |
| 2 to 3 (Wide) | `original` | 22 | 7x5 | Blueprint original (mantido). |
| 2 to 4 | `original` | 9 | 4x4 | Blueprint original (mantido). |
| 2 to 5 | `raynquist-fix` | 31 | 5x8 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '2-5 balancer'. |
| 2 to 6 | `original` | 33 | 8x6 | Blueprint original (mantido). |
| 2 to 7 | `original` | 33 | 8x6 | Blueprint original (mantido). |
| 2 to 8 | `original` | 23 | 8x6 | Blueprint original (mantido). |
| 2 to 9 | `raynquist` | 51 | 9x8 | Fonte: livro de balanceadores do Raynquist (fall 2025), '2-9 balancer'. |
| 2 to 10 | `generated` | 61 | 10x11 | Gerado com blocos verificados: STACK 2->2 + 2x(1->5). |
| 2 to 11 | `generated` | 117 | 13x24 | Gerado com blocos verificados: SQ(2) + K1 P=12 nl=1 dead=[2..10;9]. |
| 2 to 12 | `generated` | 48 | 12x9 | Gerado com blocos verificados: STACK 2->2 + 2x(1->6). |
| 2 to 13 | `generated` | 196 | 19x25 | Gerado com blocos verificados: SQ(2) + K1 P=16 nl=0 dead=[0..10;11]. |
| 2 to 14 | `generated` | 66 | 14x10 | Gerado com blocos verificados: STACK 2->2 + 2x(1->7). |
| 2 to 15 | `generated` | 108 | 15x13 | Gerado com blocos verificados: STACK 2->3 + 3x(1->5). |
| 2 to 16 | `generated` | 50 | 16x9 | Gerado com blocos verificados: STACK 2->2 + 2x(1->8). |
| 2 to 17 | `generated` | 967 | 47x46 | Gerado com blocos verificados: SQ(2) + K1 P=32 nl=7 dead=[2..16;15]. |
| 2 to 18 | `generated` | 88 | 18x11 | Gerado com blocos verificados: STACK 2->3 + 3x(1->6). |
| 2 to 19 | `generated` | 815 | 45x56 | Gerado com blocos verificados: SQ(2) + K1 P=32 nl=0 dead=[0..16;17]. |
| 2 to 20 | `generated` | 93 | 20x14 | Gerado com blocos verificados: STACK 2->5 + 5x(1->4). |
| 2 to 21 | `generated` | 115 | 21x12 | Gerado com blocos verificados: STACK 2->3 + 3x(1->7). |
| 2 to 22 | `generated` | 231 | 22x32 | Gerado com blocos verificados: STACK 2->11 + 11x(1->2). |
| 2 to 23 | `generated` | 651 | 41x48 | Gerado com blocos verificados: SQ(2) + K1 P=32 nl=0 dead=[0..20;21]. |
| 2 to 24 | `generated` | 91 | 24x11 | Gerado com blocos verificados: STACK 2->3 + 3x(1->8). |
| 3 to 1 | `original` | 18 | 4x6 | Blueprint original (mantido). |
| 3 to 2 | `original` | 25 | 5x7 | Blueprint original (mantido). |
| 3 to 3 | `original` | 32 | 6x7 | Blueprint original (mantido). |
| 3 to 4 | `original` | 39 | 7x8 | Blueprint original (mantido). |
| 3 to 5 | `raynquist-fix` | 53 | 8x9 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '3-5 balancer'. |
| 3 to 6 | `original` | 30 | 7x6 | Blueprint original (mantido). |
| 3 to 7 | `raynquist-fix` | 56 | 8x10 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '3-7 balancer'. |
| 3 to 8 | `original` | 53 | 8x10 | Blueprint original (mantido). |
| 3 to 9 | `raynquist` | 63 | 9x9 | Fonte: livro de balanceadores do Raynquist (fall 2025), '3-9 balancer'. |
| 3 to 10 | `generated` | 89 | 10x14 | Gerado com blocos verificados: STACK 3->5 + 5x(1->2). |
| 3 to 11 | `generated` | 144 | 13x30 | Gerado com blocos verificados: SQ(3) + K1 P=12 nl=1 dead=[3..10;8]. |
| 3 to 12 | `generated` | 63 | 12x14 | Gerado com blocos verificados: STACK 3->3 + 3x(1->4). |
| 3 to 13 | `generated` | 225 | 19x31 | Gerado com blocos verificados: SQ(3) + K1 P=16 nl=0 dead=[0..9;10]. |
| 3 to 14 | `generated` | 117 | 14x16 | Gerado com blocos verificados: STACK 3->7 + 7x(1->2). |
| 3 to 15 | `generated` | 116 | 15x17 | Gerado com blocos verificados: STACK 3->3 + 3x(1->5). |
| 3 to 16 | `generated` | 88 | 16x14 | Gerado com blocos verificados: STACK 3->4 + 4x(1->4). |
| 3 to 17 | `generated` | 996 | 47x52 | Gerado com blocos verificados: SQ(3) + K1 P=32 nl=7 dead=[3..16;14]. |
| 3 to 18 | `generated` | 96 | 18x15 | Gerado com blocos verificados: STACK 3->3 + 3x(1->6). |
| 3 to 19 | `generated` | 846 | 45x62 | Gerado com blocos verificados: SQ(3) + K1 P=32 nl=0 dead=[0..15;16]. |
| 3 to 20 | `generated` | 115 | 20x15 | Gerado com blocos verificados: STACK 3->5 + 5x(1->4). |
| 3 to 21 | `generated` | 123 | 21x16 | Gerado com blocos verificados: STACK 3->3 + 3x(1->7). |
| 3 to 22 | `generated` | 258 | 22x38 | Gerado com blocos verificados: STACK 3->11 + 11x(1->2). |
| 3 to 23 | `generated` | 680 | 41x54 | Gerado com blocos verificados: SQ(3) + K1 P=32 nl=0 dead=[0..19;20]. |
| 3 to 24 | `generated` | 99 | 24x15 | Gerado com blocos verificados: STACK 3->3 + 3x(1->8). |
| 4 to 1 | `original` | 8 | 4x4 | Blueprint original (mantido). |
| 4 to 2 | `original` | 9 | 4x4 | Blueprint original (mantido). |
| 4 to 3 | `original` | 39 | 7x8 | Blueprint original (mantido). |
| 4 to 4 | `original` | 30 | 4x9 | Blueprint original (mantido). |
| 4 to 5 | `raynquist-fix` | 57 | 8x10 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '4-5 balancer'. |
| 4 to 6 | `original` | 52 | 6x11 | Blueprint original (mantido). |
| 4 to 7 | `original` | 54 | 9x9 | Blueprint original (mantido). |
| 4 to 8 | `original` | 36 | 8x6 | Blueprint original (mantido). |
| 4 to 9 | `raynquist` | 74 | 9x12 | Fonte: livro de balanceadores do Raynquist (fall 2025), '4-9 balancer'. |
| 4 to 10 | `generated` | 93 | 10x15 | Gerado com blocos verificados: STACK 4->5 + 5x(1->2). |
| 4 to 11 | `generated` | 149 | 13x30 | Gerado com blocos verificados: SQ(4) + K1 P=12 nl=1 dead=[4..10;7]. |
| 4 to 12 | `raynquist` | 139 | 12x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '4-12 TU balancer'. |
| 4 to 13 | `generated` | 235 | 19x31 | Gerado com blocos verificados: SQ(4) + K1 P=16 nl=0 dead=[0..8;9]. |
| 4 to 14 | `generated` | 115 | 14x15 | Gerado com blocos verificados: STACK 4->7 + 7x(1->2). |
| 4 to 15 | `generated` | 165 | 17x27 | Gerado com blocos verificados: SQ(4) + K1 P=16 nl=0 dead=[0..10;11]. |
| 4 to 16 | `generated` | 79 | 16x15 | Gerado com blocos verificados: STACK 4->4 + 4x(1->4). |
| 4 to 17 | `generated` | 1.004 | 47x52 | Gerado com blocos verificados: SQ(4) + K1 P=32 nl=7 dead=[4..16;13]. |
| 4 to 18 | `generated` | 146 | 18x19 | Gerado com blocos verificados: STACK 4->4 + 2x(2->9). |
| 4 to 19 | `generated` | 954 | 45x50 | Gerado com blocos verificados: SQ(4) + K1 P=32 nl=6 dead=[0..14;15]. |
| 4 to 20 | `generated` | 119 | 20x16 | Gerado com blocos verificados: STACK 4->5 + 5x(1->4). |
| 4 to 21 | `generated` | 294 | 24x26 | Gerado com blocos verificados: STACK 4->6 + 3x(2->7). |
| 4 to 22 | `generated` | 263 | 22x38 | Gerado com blocos verificados: STACK 4->11 + 11x(1->2). |
| 4 to 23 | `generated` | 710 | 41x54 | Gerado com blocos verificados: SQ(4) + K1 P=32 nl=0 dead=[0..18;19]. |
| 4 to 24 | `generated` | 123 | 24x16 | Gerado com blocos verificados: STACK 4->4 + 4x(1->6). |
| 5 to 1 | `original` | 25 | 6x7 | Blueprint original (mantido). |
| 5 to 2 | `raynquist-fix` | 31 | 5x8 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '5-2 balancer'. |
| 5 to 3 | `raynquist-fix` | 57 | 8x10 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '5-3 balancer'. |
| 5 to 4 | `raynquist-fix` | 57 | 8x10 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '5-4 balancer'. |
| 5 to 5 | `original` | 81 | 10x11 | Blueprint original (mantido). |
| 5 to 6 | `raynquist-fix` | 86 | 8x15 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '5-6 balancer'. |
| 5 to 7 | `raynquist-fix` | 97 | 9x15 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '5-7 balancer'. |
| 5 to 8 | `original` | 119 | 10x16 | Blueprint original (mantido). |
| 5 to 9 | `raynquist` | 117 | 9x18 | Fonte: livro de balanceadores do Raynquist (fall 2025), '5-9 balancer'. |
| 5 to 10 | `generated` | 98 | 10x17 | Gerado com blocos verificados: STACK 5->5 + 5x(1->2). |
| 5 to 11 | `generated` | 183 | 13x33 | Gerado com blocos verificados: SQ(5) + K1 P=12 nl=1 dead=[5, 6, 7, 8, 9, 10]. |
| 5 to 12 | `generated` | 133 | 12x21 | Gerado com blocos verificados: STACK 5->6 + 3x(2->4). |
| 5 to 13 | `generated` | 271 | 19x34 | Gerado com blocos verificados: SQ(5) + K1 P=16 nl=0 dead=[0..7;8]. |
| 5 to 14 | `generated` | 158 | 14x21 | Gerado com blocos verificados: STACK 5->7 + 7x(1->2). |
| 5 to 15 | `generated` | 199 | 17x30 | Gerado com blocos verificados: SQ(5) + K1 P=16 nl=0 dead=[0..9;10]. |
| 5 to 16 | `generated` | 163 | 16x21 | Gerado com blocos verificados: STACK 5->8 + 8x(1->2). |
| 5 to 17 | `generated` | 1.040 | 47x55 | Gerado com blocos verificados: SQ(5) + K1 P=32 nl=7 dead=[5..16;12]. |
| 5 to 18 | `generated` | 239 | 18x27 | Gerado com blocos verificados: STACK 5->6 + 2x(3->9). |
| 5 to 19 | `generated` | 990 | 45x53 | Gerado com blocos verificados: SQ(5) + K1 P=32 nl=6 dead=[0..13;14]. |
| 5 to 20 | `generated` | 124 | 20x18 | Gerado com blocos verificados: STACK 5->5 + 5x(1->4). |
| 5 to 21 | `generated` | 329 | 24x30 | Gerado com blocos verificados: STACK 5->6 + 3x(2->7). |
| 5 to 22 | `generated` | 297 | 22x41 | Gerado com blocos verificados: STACK 5->11 + 11x(1->2). |
| 5 to 23 | `generated` | 746 | 41x57 | Gerado com blocos verificados: SQ(5) + K1 P=32 nl=0 dead=[0..17;18]. |
| 5 to 24 | `generated` | 167 | 24x22 | Gerado com blocos verificados: STACK 5->6 + 6x(1->4). |
| 6 to 1 | `original` | 21 | 6x6 | Blueprint original (mantido). |
| 6 to 2 | `original` | 32 | 7x7 | Blueprint original (mantido). |
| 6 to 3 | `original` | 33 | 7x7 | Blueprint original (mantido). |
| 6 to 4 | `original` | 52 | 6x11 | Blueprint original (mantido). |
| 6 to 5 | `raynquist-fix` | 86 | 8x15 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '6-5 balancer'. |
| 6 to 6 | `original` | 73 | 9x11 | Blueprint original (mantido). |
| 6 to 7 | `raynquist-fix` | 96 | 9x14 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '6-7 balancer'. |
| 6 to 8 | `original` | 90 | 10x13 | Blueprint original (mantido). |
| 6 to 9 | `raynquist` | 101 | 9x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '6-9 balancer'. |
| 6 to 10 | `generated` | 184 | 11x30 | Gerado com blocos verificados: SQ(6) + K1 P=10 nl=0 dead=[0, 1, 2, 3]. |
| 6 to 11 | `generated` | 244 | 13x34 | Gerado com blocos verificados: SQ(6) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 6 to 12 | `generated` | 112 | 12x19 | Gerado com blocos verificados: STACK 6->6 + 3x(2->4). |
| 6 to 13 | `generated` | 300 | 19x33 | Gerado com blocos verificados: SQ(6) + K1 P=16 nl=1 dead=[6..12;7]. |
| 6 to 14 | `generated` | 157 | 14x20 | Gerado com blocos verificados: STACK 6->7 + 7x(1->2). |
| 6 to 15 | `generated` | 182 | 15x23 | Gerado com blocos verificados: STACK 6->6 + 3x(2->5). |
| 6 to 16 | `generated` | 158 | 16x20 | Gerado com blocos verificados: STACK 6->8 + 8x(1->2). |
| 6 to 17 | `generated` | 1.073 | 47x56 | Gerado com blocos verificados: SQ(6) + K1 P=32 nl=7 dead=[6..16;11]. |
| 6 to 18 | `generated` | 193 | 18x23 | Gerado com blocos verificados: STACK 6->9 + 9x(1->2). |
| 6 to 19 | `generated` | 1.002 | 45x54 | Gerado com blocos verificados: SQ(6) + K1 P=32 nl=6 dead=[6..18;13]. |
| 6 to 20 | `generated` | 252 | 20x25 | Gerado com blocos verificados: STACK 6->8 + 4x(2->5). |
| 6 to 21 | `generated` | 308 | 24x28 | Gerado com blocos verificados: STACK 6->6 + 3x(2->7). |
| 6 to 22 | `generated` | 358 | 22x42 | Gerado com blocos verificados: STACK 6->11 + 11x(1->2). |
| 6 to 23 | `generated` | 759 | 41x58 | Gerado com blocos verificados: SQ(6) + K1 P=32 nl=0 dead=[0..16;17]. |
| 6 to 24 | `generated` | 146 | 24x20 | Gerado com blocos verificados: STACK 6->6 + 6x(1->4). |
| 7 to 1 | `original` | 30 | 7x7 | Blueprint original (mantido). |
| 7 to 2 | `original` | 37 | 8x7 | Blueprint original (mantido). |
| 7 to 3 | `raynquist-fix` | 53 | 9x8 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '7-3 balancer'. |
| 7 to 4 | `original` | 54 | 9x9 | Blueprint original (mantido). |
| 7 to 5 | `raynquist-fix` | 97 | 9x15 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '7-5 balancer'. |
| 7 to 6 | `raynquist-fix` | 96 | 9x14 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '7-6 balancer'. |
| 7 to 7 | `original` | 91 | 10x11 | Blueprint original (mantido). |
| 7 to 8 | `raynquist-fix` | 97 | 8x16 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '7-8 balancer'. |
| 7 to 9 | `raynquist` | 168 | 12x18 | Fonte: livro de balanceadores do Raynquist (fall 2025), '7-9 balancer'. |
| 7 to 10 | `raynquist` | 138 | 10x19 | Fonte: livro de balanceadores do Raynquist (fall 2025), '7-10 balancer'. |
| 7 to 11 | `generated` | 261 | 13x35 | Gerado com blocos verificados: SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3]. |
| 7 to 12 | `generated` | 234 | 12x33 | Gerado com blocos verificados: SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 7 to 13 | `raynquist` | 158 | 15x15 | Fonte: livro de balanceadores do Raynquist (fall 2025), '7-13 balancer'. |
| 7 to 14 | `generated` | 141 | 14x20 | Gerado com blocos verificados: STACK 7->7 + 7x(1->2). |
| 7 to 15 | `generated` | 227 | 17x32 | Gerado com blocos verificados: SQ(7) + K1 P=16 nl=0 dead=[0..7;8]. |
| 7 to 16 | `generated` | 177 | 16x23 | Gerado com blocos verificados: STACK 7->8 + 8x(1->2). |
| 7 to 17 | `generated` | 1.092 | 47x57 | Gerado com blocos verificados: SQ(7) + K1 P=32 nl=7 dead=[7..16;10]. |
| 7 to 18 | `generated` | 260 | 18x25 | Gerado com blocos verificados: STACK 7->9 + 9x(1->2). |
| 7 to 19 | `generated` | 1.042 | 45x55 | Gerado com blocos verificados: SQ(7) + K1 P=32 nl=6 dead=[0..11;12]. |
| 7 to 20 | `generated` | 245 | 20x27 | Gerado com blocos verificados: STACK 7->10 + 10x(1->2). |
| 7 to 21 | `generated` | 385 | 28x31 | Gerado com blocos verificados: STACK 7->7 + 7x(1->3). |
| 7 to 22 | `generated` | 375 | 22x43 | Gerado com blocos verificados: STACK 7->11 + 11x(1->2). |
| 7 to 23 | `generated` | 778 | 41x59 | Gerado com blocos verificados: SQ(7) + K1 P=32 nl=0 dead=[0..15;16]. |
| 7 to 24 | `generated` | 337 | 24x37 | Gerado com blocos verificados: STACK 7->8 + 2x(4->12). |
| 8 to 1 | `original` | 20 | 8x6 | Blueprint original (mantido). |
| 8 to 2 | `original` | 21 | 8x6 | Blueprint original (mantido). |
| 8 to 3 | `original` | 50 | 8x10 | Blueprint original (mantido). |
| 8 to 4 | `original` | 40 | 8x7 | Blueprint original (mantido). |
| 8 to 5 | `original` | 111 | 10x17 | Blueprint original (mantido). |
| 8 to 6 | `original` | 90 | 10x13 | Blueprint original (mantido). |
| 8 to 7 | `raynquist-fix` | 97 | 8x16 | Substitui o original, que falhou na verificação. Fonte: livro de balanceadores do Raynquist (fall 2025), '8-7 balancer'. |
| 8 to 8 | `original` | 82 | 10x11 | Blueprint original (mantido). |
| 8 to 9 | `raynquist` | 137 | 11x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '8-9 balancer'. |
| 8 to 10 | `raynquist` | 124 | 10x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '8-10 balancer'. |
| 8 to 11 | `generated` | 271 | 13x33 | Gerado com blocos verificados: SQ(8) + K1 P=12 nl=1 dead=[0, 9, 10]. |
| 8 to 12 | `raynquist` | 127 | 12x14 | Fonte: livro de balanceadores do Raynquist (fall 2025), '8-12 balancer'. |
| 8 to 13 | `raynquist` | 156 | 15x15 | Fonte: livro de balanceadores do Raynquist (fall 2025), '8-13 balancer'. |
| 8 to 14 | `generated` | 310 | 18x32 | Gerado com blocos verificados: SQ(8) + K1 P=16 nl=0 dead=[8, 9, 10, 11, 12, 13]. |
| 8 to 15 | `generated` | 274 | 17x30 | Gerado com blocos verificados: SQ(8) + K1 P=16 nl=0 dead=[8..14;7]. |
| 8 to 16 | `generated` | 156 | 16x19 | Gerado com blocos verificados: STACK 8->8 + 8x(1->2). |
| 8 to 17 | `generated` | 1.098 | 47x55 | Gerado com blocos verificados: SQ(8) + K1 P=32 nl=7 dead=[8..16;9]. |
| 8 to 18 | `generated` | 229 | 18x23 | Gerado com blocos verificados: STACK 8->9 + 9x(1->2). |
| 8 to 19 | `generated` | 1.047 | 45x53 | Gerado com blocos verificados: SQ(8) + K1 P=32 nl=6 dead=[8..18;11]. |
| 8 to 20 | `generated` | 231 | 20x24 | Gerado com blocos verificados: STACK 8->10 + 10x(1->2). |
| 8 to 21 | `generated` | 470 | 24x36 | Gerado com blocos verificados: STACK 8->9 + 3x(3->7). |
| 8 to 22 | `generated` | 385 | 22x41 | Gerado com blocos verificados: STACK 8->11 + 11x(1->2). |
| 8 to 23 | `generated` | 961 | 41x49 | Gerado com blocos verificados: SQ(8) + K1 P=32 nl=4 dead=[8..22;15]. |
| 8 to 24 | `generated` | 261 | 24x23 | Gerado com blocos verificados: STACK 8->12 + 12x(1->2). |
| 9 to 1 | `raynquist` | 46 | 9x8 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-1 TU balancer'. |
| 9 to 2 | `raynquist` | 51 | 10x8 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-2 balancer'. |
| 9 to 3 | `raynquist` | 64 | 10x9 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-3 balancer'. |
| 9 to 4 | `raynquist` | 79 | 9x12 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-4 balancer'. |
| 9 to 5 | `raynquist` | 118 | 9x18 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-5 balancer'. |
| 9 to 6 | `raynquist` | 101 | 9x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-6 balancer'. |
| 9 to 7 | `raynquist` | 167 | 12x18 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-7 balancer'. |
| 9 to 8 | `raynquist` | 137 | 11x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-8 balancer'. |
| 9 to 9 | `raynquist` | 136 | 11x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-9 balancer'. |
| 9 to 10 | `raynquist` | 197 | 11x23 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-10 balancer'. |
| 9 to 11 | `generated` | 333 | 13x37 | Gerado com blocos verificados: SQ(9) + K1 P=12 nl=1 dead=[9, 10]. |
| 9 to 12 | `raynquist` | 154 | 12x18 | Fonte: livro de balanceadores do Raynquist (fall 2025), '9-12 balancer'. |
| 9 to 13 | `generated` | 409 | 19x36 | Gerado com blocos verificados: SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12]. |
| 9 to 14 | `generated` | 373 | 18x34 | Gerado com blocos verificados: SQ(9) + K1 P=16 nl=1 dead=[0, 1, 2, 3, 4]. |
| 9 to 15 | `generated` | 338 | 17x34 | Gerado com blocos verificados: SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12, 13, 14]. |
| 9 to 16 | `generated` | 303 | 16x32 | Gerado com blocos verificados: SQ(9) + K1 P=16 nl=0 dead=[0..15;7]. |
| 9 to 17 | `generated` | 1.162 | 47x59 | Gerado com blocos verificados: SQ(9) + K1 P=32 nl=7 dead=[9..16;8]. |
| 9 to 18 | `generated` | 228 | 18x23 | Gerado com blocos verificados: STACK 9->9 + 9x(1->2). |
| 9 to 19 | `generated` | 1.112 | 45x57 | Gerado com blocos verificados: SQ(9) + K1 P=32 nl=6 dead=[0..9;10]. |
| 9 to 20 | `generated` | 304 | 20x31 | Gerado com blocos verificados: STACK 9->10 + 10x(1->2). |
| 9 to 21 | `generated` | 469 | 24x36 | Gerado com blocos verificados: STACK 9->9 + 3x(3->7). |
| 9 to 22 | `generated` | 447 | 22x45 | Gerado com blocos verificados: STACK 9->11 + 11x(1->2). |
| 9 to 23 | `generated` | 1.031 | 41x53 | Gerado com blocos verificados: SQ(9) + K1 P=32 nl=4 dead=[0..13;14]. |
| 9 to 24 | `generated` | 288 | 24x27 | Gerado com blocos verificados: STACK 9->12 + 12x(1->2). |
| 10 to 1 | `generated` | 61 | 10x12 | Gerado com blocos verificados: DSTACK 5x(2->1) + 5->1. |
| 10 to 2 | `generated` | 67 | 10x13 | Gerado com blocos verificados: DSTACK 5x(2->1) + 5->2. |
| 10 to 3 | `generated` | 93 | 10x15 | Gerado com blocos verificados: DSTACK 5x(2->1) + 5->3. |
| 10 to 4 | `generated` | 93 | 10x15 | Gerado com blocos verificados: REVERSED STACK 4->5 + 5x(1->2). |
| 10 to 5 | `generated` | 98 | 10x17 | Gerado com blocos verificados: REVERSED STACK 5->5 + 5x(1->2). |
| 10 to 6 | `generated` | 184 | 11x30 | Gerado com blocos verificados: REVERSED SQ(6) + K1 P=10 nl=0 dead=[0, 1, 2, 3]. |
| 10 to 7 | `generated` | 212 | 11x31 | Gerado com blocos verificados: REV(K1 P=10 nl=0 dead=[0, 1, 2]) + SQ(7). |
| 10 to 8 | `raynquist` | 124 | 10x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '10-8 balancer'. |
| 10 to 9 | `generated` | 197 | 11x23 | Gerado com blocos verificados: REVERSED LIB. |
| 10 to 10 | `raynquist` | 147 | 11x17 | Fonte: livro de balanceadores do Raynquist (fall 2025), '10-10 balancer'. |
| 10 to 11 | `generated` | 353 | 14x38 | Gerado com blocos verificados: SQ(10) + K1p P=12 loops=0+1. |
| 10 to 12 | `generated` | 316 | 13x36 | Gerado com blocos verificados: SQ(10) + K1 P=12 nl=0 dead=[10, 11]. |
| 10 to 13 | `generated` | 427 | 19x37 | Gerado com blocos verificados: SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 10 to 14 | `generated` | 390 | 18x35 | Gerado com blocos verificados: SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2, 3]. |
| 10 to 15 | `generated` | 355 | 17x35 | Gerado com blocos verificados: SQ(10) + K1 P=16 nl=1 dead=[10, 11, 12, 13, 14]. |
| 10 to 16 | `generated` | 317 | 17x33 | Gerado com blocos verificados: SQ(10) + K1 P=16 nl=0 dead=[10, 11, 12, 13, 14, 15]. |
| 10 to 17 | `generated` | 1.236 | 47x60 | Gerado com blocos verificados: SQ(10) + K1 P=32 nl=7 dead=[0..16;7]. |
| 10 to 18 | `generated` | 533 | 18x51 | Gerado com blocos verificados: STACK 10->12 + 3x(4->6). |
| 10 to 19 | `generated` | 1.132 | 45x58 | Gerado com blocos verificados: SQ(10) + K1 P=32 nl=6 dead=[10..18;9]. |
| 10 to 20 | `generated` | 254 | 20x25 | Gerado com blocos verificados: STACK 10->10 + 10x(1->2). |
| 10 to 21 | `generated` | 684 | 27x56 | Gerado com blocos verificados: STACK 10->12 + 3x(4->7). |
| 10 to 22 | `generated` | 467 | 22x46 | Gerado com blocos verificados: STACK 10->11 + 11x(1->2). |
| 10 to 23 | `generated` | 1.052 | 41x54 | Gerado com blocos verificados: SQ(10) + K1 P=32 nl=4 dead=[0..12;13]. |
| 10 to 24 | `generated` | 450 | 24x45 | Gerado com blocos verificados: STACK 10->12 + 12x(1->2). |
| 11 to 1 | `generated` | 94 | 13x21 | Gerado com blocos verificados: REVERSED K1 P=12 nl=1 dead=[1..10;10]. |
| 11 to 2 | `generated` | 117 | 13x24 | Gerado com blocos verificados: REVERSED SQ(2) + K1 P=12 nl=1 dead=[2..10;9]. |
| 11 to 3 | `generated` | 144 | 13x30 | Gerado com blocos verificados: REVERSED SQ(3) + K1 P=12 nl=1 dead=[3..10;8]. |
| 11 to 4 | `generated` | 149 | 13x30 | Gerado com blocos verificados: REVERSED SQ(4) + K1 P=12 nl=1 dead=[4..10;7]. |
| 11 to 5 | `generated` | 183 | 13x33 | Gerado com blocos verificados: REVERSED SQ(5) + K1 P=12 nl=1 dead=[5, 6, 7, 8, 9, 10]. |
| 11 to 6 | `generated` | 244 | 13x34 | Gerado com blocos verificados: REVERSED SQ(6) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 11 to 7 | `generated` | 261 | 13x35 | Gerado com blocos verificados: REVERSED SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3]. |
| 11 to 8 | `generated` | 271 | 13x33 | Gerado com blocos verificados: REVERSED SQ(8) + K1 P=12 nl=1 dead=[0, 9, 10]. |
| 11 to 9 | `generated` | 333 | 13x37 | Gerado com blocos verificados: REVERSED SQ(9) + K1 P=12 nl=1 dead=[9, 10]. |
| 11 to 10 | `raynquist` | 205 | 13x23 | Fonte: livro de balanceadores do Raynquist (fall 2025), '11-10 balancer'. |
| 11 to 11 | `generated` | 208 | 13x21 | Gerado com blocos verificados: LOOP(12-12) nl=0. |
| 11 to 12 | `generated` | 385 | 14x40 | Gerado com blocos verificados: SQ(11) + K1 P=12 nl=0 dead=[0]. |
| 11 to 13 | `generated` | 491 | 19x41 | Gerado com blocos verificados: SQ(11) + K1 P=16 nl=1 dead=[11, 12]. |
| 11 to 14 | `generated` | 453 | 18x39 | Gerado com blocos verificados: SQ(11) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 11 to 15 | `generated` | 418 | 17x39 | Gerado com blocos verificados: SQ(11) + K1 P=16 nl=1 dead=[11, 12, 13, 14]. |
| 11 to 16 | `generated` | 383 | 16x37 | Gerado com blocos verificados: SQ(11) + K1 P=16 nl=0 dead=[11, 12, 13, 14, 15]. |
| 11 to 17 | `generated` | 1.292 | 47x64 | Gerado com blocos verificados: SQ(11) + K1 P=32 nl=7 dead=[11, 12, 13, 14, 15, 16]. |
| 11 to 18 | `generated` | 602 | 18x55 | Gerado com blocos verificados: STACK 11->12 + 3x(4->6). |
| 11 to 19 | `generated` | 1.241 | 45x62 | Gerado com blocos verificados: SQ(11) + K1 P=32 nl=6 dead=[0..7;8]. |
| 11 to 20 | `generated` | 712 | 20x61 | Gerado com blocos verificados: STACK 11->16 + 2x(8->10). |
| 11 to 21 | `generated` | 753 | 27x60 | Gerado com blocos verificados: STACK 11->12 + 3x(4->7). |
| 11 to 22 | `generated` | 322 | 22x29 | Gerado com blocos verificados: STACK 11->11 + 11x(1->2). |
| 11 to 23 | `generated` | 1.106 | 41x58 | Gerado com blocos verificados: SQ(11) + K1 P=32 nl=4 dead=[0..11;12]. |
| 11 to 24 | `generated` | 519 | 24x49 | Gerado com blocos verificados: STACK 11->12 + 12x(1->2). |
| 12 to 1 | `generated` | 51 | 12x10 | Gerado com blocos verificados: DSTACK 2x(6->1) + 2->1. |
| 12 to 2 | `generated` | 52 | 12x10 | Gerado com blocos verificados: DSTACK 2x(6->1) + 2->2. |
| 12 to 3 | `generated` | 63 | 12x14 | Gerado com blocos verificados: REVERSED STACK 3->3 + 3x(1->4). |
| 12 to 4 | `raynquist` | 139 | 12x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '12-4 TU balancer'. |
| 12 to 5 | `generated` | 133 | 12x21 | Gerado com blocos verificados: REVERSED STACK 5->6 + 3x(2->4). |
| 12 to 6 | `generated` | 112 | 12x19 | Gerado com blocos verificados: REVERSED STACK 6->6 + 3x(2->4). |
| 12 to 7 | `generated` | 234 | 12x33 | Gerado com blocos verificados: REVERSED SQ(7) + K1 P=12 nl=0 dead=[0, 1, 2, 3, 4]. |
| 12 to 8 | `generated` | 220 | 12x27 | Gerado com blocos verificados: DSTACK 2x(6->4) + 8->8. |
| 12 to 9 | `generated` | 304 | 12x35 | Gerado com blocos verificados: REV(K1 P=12 nl=0 dead=[0, 10, 11]) + SQ(9). |
| 12 to 10 | `raynquist` | 199 | 12x22 | Fonte: livro de balanceadores do Raynquist (fall 2025), '12-10 balancer'. |
| 12 to 11 | `generated` | 385 | 14x40 | Gerado com blocos verificados: REVERSED SQ(11) + K1 P=12 nl=0 dead=[0]. |
| 12 to 12 | `raynquist` | 178 | 12x19 | Fonte: livro de balanceadores do Raynquist (fall 2025), '12-12 balancer'. |
| 12 to 13 | `generated` | 468 | 19x39 | Gerado com blocos verificados: SQ(12) + K1p P=16 loops=2+1. |
| 12 to 14 | `generated` | 429 | 18x37 | Gerado com blocos verificados: SQ(12) + K1p P=16 loops=1+1. |
| 12 to 15 | `generated` | 415 | 17x37 | Gerado com blocos verificados: SQ(12) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 12 to 16 | `generated` | 354 | 16x35 | Gerado com blocos verificados: SQ(12) + K1 P=16 nl=0 dead=[12, 13, 14, 15]. |
| 12 to 17 | `generated` | 1.281 | 47x62 | Gerado com blocos verificados: SQ(12) + K1 P=32 nl=7 dead=[0, 1, 2, 3, 4]. |
| 12 to 18 | `generated` | 395 | 18x34 | Gerado com blocos verificados: STACK 12->12 + 3x(4->6). |
| 12 to 19 | `generated` | 1.230 | 45x60 | Gerado com blocos verificados: SQ(12) + K1 P=32 nl=6 dead=[0..6;7]. |
| 12 to 20 | `generated` | 638 | 32x44 | Gerado com blocos verificados: STACK 12->12 + 4x(3->5). |
| 12 to 21 | `generated` | 546 | 27x39 | Gerado com blocos verificados: STACK 12->12 + 3x(4->7). |
| 12 to 22 | `generated` | 871 | 26x70 | Gerado com blocos verificados: STACK 12->12 + 2x(6->11). |
| 12 to 23 | `generated` | 1.111 | 41x56 | Gerado com blocos verificados: SQ(12) + K1 P=32 nl=4 dead=[12..22;11]. |
| 12 to 24 | `generated` | 312 | 24x28 | Gerado com blocos verificados: STACK 12->12 + 12x(1->2). |
| 13 to 1 | `generated` | 160 | 19x22 | Gerado com blocos verificados: REVERSED K1 P=16 nl=0 dead=[0..11;12]. |
| 13 to 2 | `generated` | 196 | 19x25 | Gerado com blocos verificados: REVERSED SQ(2) + K1 P=16 nl=0 dead=[0..10;11]. |
| 13 to 3 | `generated` | 225 | 19x31 | Gerado com blocos verificados: REVERSED SQ(3) + K1 P=16 nl=0 dead=[0..9;10]. |
| 13 to 4 | `generated` | 235 | 19x31 | Gerado com blocos verificados: REVERSED SQ(4) + K1 P=16 nl=0 dead=[0..8;9]. |
| 13 to 5 | `generated` | 271 | 19x34 | Gerado com blocos verificados: REVERSED SQ(5) + K1 P=16 nl=0 dead=[0..7;8]. |
| 13 to 6 | `generated` | 300 | 19x33 | Gerado com blocos verificados: REVERSED SQ(6) + K1 P=16 nl=1 dead=[6..12;7]. |
| 13 to 7 | `generated` | 158 | 15x15 | Gerado com blocos verificados: REVERSED LIB. |
| 13 to 8 | `generated` | 156 | 15x15 | Gerado com blocos verificados: REVERSED LIB. |
| 13 to 9 | `generated` | 409 | 19x36 | Gerado com blocos verificados: REVERSED SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12]. |
| 13 to 10 | `generated` | 427 | 19x37 | Gerado com blocos verificados: REVERSED SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 13 to 11 | `generated` | 491 | 19x41 | Gerado com blocos verificados: REVERSED SQ(11) + K1 P=16 nl=1 dead=[11, 12]. |
| 13 to 12 | `generated` | 468 | 19x39 | Gerado com blocos verificados: REVERSED SQ(12) + K1p P=16 loops=2+1. |
| 13 to 13 | `generated` | 293 | 19x20 | Gerado com blocos verificados: LOOP(16-16) nl=1. |
| 13 to 14 | `generated` | 546 | 19x38 | Gerado com blocos verificados: SQ(13) + K1p P=16 loops=1+1. |
| 13 to 15 | `generated` | 532 | 19x38 | Gerado com blocos verificados: SQ(13) + K1 P=16 nl=0 dead=[0, 1]. |
| 13 to 16 | `generated` | 495 | 20x36 | Gerado com blocos verificados: SQ(13) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 13 to 17 | `generated` | 1.374 | 47x63 | Gerado com blocos verificados: SQ(13) + K1 P=32 nl=7 dead=[13, 14, 15, 16]. |
| 13 to 18 | `generated` | 982 | 22x69 | Gerado com blocos verificados: STACK 13->16 + 2x(8->9). |
| 13 to 19 | `generated` | 1.323 | 45x61 | Gerado com blocos verificados: SQ(13) + K1 P=32 nl=6 dead=[0, 1, 2, 3, 4, 5]. |
| 13 to 20 | `generated` | 824 | 22x60 | Gerado com blocos verificados: STACK 13->16 + 2x(8->10). |
| 13 to 21 | `generated` | 984 | 49x58 | Gerado com blocos verificados: STACK 13->14 + 7x(2->3). |
| 13 to 22 | `generated` | 1.254 | 42x67 | Gerado com blocos verificados: SQ(13) + K1 P=32 nl=0 dead=[0..8;9]. |
| 13 to 23 | `generated` | 1.211 | 41x65 | Gerado com blocos verificados: SQ(13) + K1 P=32 nl=0 dead=[0..9;10]. |
| 13 to 24 | `generated` | 802 | 24x55 | Gerado com blocos verificados: STACK 13->16 + 4x(4->6). |
| 14 to 1 | `generated` | 69 | 14x11 | Gerado com blocos verificados: DSTACK 2x(7->1) + 2->1. |
| 14 to 2 | `generated` | 70 | 14x11 | Gerado com blocos verificados: DSTACK 2x(7->1) + 2->2. |
| 14 to 3 | `generated` | 114 | 14x14 | Gerado com blocos verificados: DSTACK 7x(2->1) + 7->3. |
| 14 to 4 | `generated` | 115 | 14x15 | Gerado com blocos verificados: REVERSED STACK 4->7 + 7x(1->2). |
| 14 to 5 | `generated` | 158 | 14x21 | Gerado com blocos verificados: REVERSED STACK 5->7 + 7x(1->2). |
| 14 to 6 | `generated` | 157 | 14x20 | Gerado com blocos verificados: REVERSED STACK 6->7 + 7x(1->2). |
| 14 to 7 | `generated` | 141 | 14x20 | Gerado com blocos verificados: REVERSED STACK 7->7 + 7x(1->2). |
| 14 to 8 | `generated` | 310 | 18x32 | Gerado com blocos verificados: REVERSED SQ(8) + K1 P=16 nl=0 dead=[8, 9, 10, 11, 12, 13]. |
| 14 to 9 | `generated` | 373 | 18x34 | Gerado com blocos verificados: REVERSED SQ(9) + K1 P=16 nl=1 dead=[0, 1, 2, 3, 4]. |
| 14 to 10 | `generated` | 390 | 18x35 | Gerado com blocos verificados: REVERSED SQ(10) + K1 P=16 nl=1 dead=[0, 1, 2, 3]. |
| 14 to 11 | `generated` | 453 | 18x39 | Gerado com blocos verificados: REVERSED SQ(11) + K1 P=16 nl=1 dead=[0, 1, 2]. |
| 14 to 12 | `generated` | 429 | 18x37 | Gerado com blocos verificados: REVERSED SQ(12) + K1p P=16 loops=1+1. |
| 14 to 13 | `generated` | 546 | 19x38 | Gerado com blocos verificados: REVERSED SQ(13) + K1p P=16 loops=1+1. |
| 14 to 14 | `generated` | 255 | 18x18 | Gerado com blocos verificados: LOOP(16-16) nl=1. |
| 14 to 15 | `generated` | 502 | 19x36 | Gerado com blocos verificados: SQ(14) + K1p P=16 loops=0+1. |
| 14 to 16 | `generated` | 458 | 18x34 | Gerado com blocos verificados: SQ(14) + K1 P=16 nl=0 dead=[0, 1]. |
| 14 to 17 | `generated` | 1.367 | 47x61 | Gerado com blocos verificados: SQ(14) + K1 P=32 nl=7 dead=[0, 1, 2]. |
| 14 to 18 | `generated` | 790 | 24x52 | Gerado com blocos verificados: STACK 14->14 + 2x(7->9). |
| 14 to 19 | `generated` | 1.307 | 45x59 | Gerado com blocos verificados: SQ(14) + K1 P=32 nl=6 dead=[14, 15, 16, 17, 18]. |
| 14 to 20 | `generated` | 614 | 20x44 | Gerado com blocos verificados: STACK 14->14 + 2x(7->10). |
| 14 to 21 | `generated` | 693 | 49x38 | Gerado com blocos verificados: STACK 14->14 + 7x(2->3). |
| 14 to 22 | `generated` | 983 | 26x71 | Gerado com blocos verificados: STACK 14->14 + 2x(7->11). |
| 14 to 23 | `generated` | 1.195 | 41x63 | Gerado com blocos verificados: SQ(14) + K1 P=32 nl=0 dead=[0..8;9]. |
| 14 to 24 | `generated` | 765 | 24x53 | Gerado com blocos verificados: STACK 14->16 + 4x(4->6). |
| 15 to 1 | `generated` | 98 | 17x18 | Gerado com blocos verificados: REVERSED K1 P=16 nl=0 dead=[0..13;14]. |
| 15 to 2 | `generated` | 109 | 17x21 | Gerado com blocos verificados: REV(K1 P=16 nl=0 dead=[0..12;13]) + SQ(2). |
| 15 to 3 | `generated` | 136 | 17x27 | Gerado com blocos verificados: REV(K1 P=16 nl=0 dead=[0..11;12]) + SQ(3). |
| 15 to 4 | `generated` | 165 | 17x27 | Gerado com blocos verificados: REVERSED SQ(4) + K1 P=16 nl=0 dead=[0..10;11]. |
| 15 to 5 | `generated` | 199 | 17x30 | Gerado com blocos verificados: REVERSED SQ(5) + K1 P=16 nl=0 dead=[0..9;10]. |
| 15 to 6 | `raynquist` | 141 | 15x13 | Fonte: livro de balanceadores do Raynquist (fall 2025), '15-6 balancer'. |
| 15 to 7 | `generated` | 227 | 17x32 | Gerado com blocos verificados: REVERSED SQ(7) + K1 P=16 nl=0 dead=[0..7;8]. |
| 15 to 8 | `generated` | 274 | 17x30 | Gerado com blocos verificados: REVERSED SQ(8) + K1 P=16 nl=0 dead=[8..14;7]. |
| 15 to 9 | `generated` | 338 | 17x34 | Gerado com blocos verificados: REVERSED SQ(9) + K1 P=16 nl=1 dead=[9, 10, 11, 12, 13, 14]. |
| 15 to 10 | `raynquist` | 206 | 15x19 | Fonte: livro de balanceadores do Raynquist (fall 2025), '15-10 balancer'. |
| 15 to 11 | `generated` | 418 | 17x39 | Gerado com blocos verificados: REVERSED SQ(11) + K1 P=16 nl=1 dead=[11, 12, 13, 14]. |
| 15 to 12 | `generated` | 415 | 17x37 | Gerado com blocos verificados: REVERSED SQ(12) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 15 to 13 | `generated` | 532 | 19x38 | Gerado com blocos verificados: REVERSED SQ(13) + K1 P=16 nl=0 dead=[0, 1]. |
| 15 to 14 | `generated` | 502 | 19x36 | Gerado com blocos verificados: REVERSED SQ(14) + K1p P=16 loops=0+1. |
| 15 to 15 | `generated` | 249 | 17x18 | Gerado com blocos verificados: LOOP(16-16) nl=0. |
| 15 to 16 | `generated` | 459 | 18x34 | Gerado com blocos verificados: SQ(15) + K1 P=16 nl=0 dead=[0]. |
| 15 to 17 | `generated` | 1.364 | 47x61 | Gerado com blocos verificados: SQ(15) + K1 P=32 nl=7 dead=[15, 16]. |
| 15 to 18 | `generated` | 701 | 24x44 | Gerado com blocos verificados: STACK 15->15 + 3x(5->6). |
| 15 to 19 | `generated` | 1.313 | 45x59 | Gerado com blocos verificados: SQ(15) + K1 P=32 nl=6 dead=[0, 1, 2, 3]. |
| 15 to 20 | `generated` | 700 | 35x40 | Gerado com blocos verificados: STACK 15->15 + 5x(3->4). |
| 15 to 21 | `generated` | 766 | 27x45 | Gerado com blocos verificados: STACK 15->15 + 3x(5->7). |
| 15 to 22 | `generated` | 1.230 | 26x86 | Gerado com blocos verificados: STACK 15->16 + 2x(8->11). |
| 15 to 23 | `generated` | 1.192 | 41x63 | Gerado com blocos verificados: SQ(15) + K1 P=32 nl=0 dead=[0..7;8]. |
| 15 to 24 | `generated` | 580 | 24x37 | Gerado com blocos verificados: STACK 15->15 + 3x(5->8). |
| 16 to 1 | `generated` | 49 | 16x10 | Gerado com blocos verificados: DSTACK 2x(8->1) + 2->1. |
| 16 to 2 | `generated` | 50 | 16x10 | Gerado com blocos verificados: DSTACK 2x(8->1) + 2->2. |
| 16 to 3 | `generated` | 88 | 16x14 | Gerado com blocos verificados: REVERSED STACK 3->4 + 4x(1->4). |
| 16 to 4 | `generated` | 79 | 16x15 | Gerado com blocos verificados: REVERSED STACK 4->4 + 4x(1->4). |
| 16 to 5 | `generated` | 163 | 16x21 | Gerado com blocos verificados: REVERSED STACK 5->8 + 8x(1->2). |
| 16 to 6 | `generated` | 156 | 16x20 | Gerado com blocos verificados: DSTACK 8x(2->1) + 8->6. |
| 16 to 7 | `generated` | 177 | 16x23 | Gerado com blocos verificados: REVERSED STACK 7->8 + 8x(1->2). |
| 16 to 8 | `raynquist` | 286 | 16x24 | Fonte: livro de balanceadores do Raynquist (fall 2025), '16-8 TU balancer'. |
| 16 to 9 | `generated` | 303 | 16x32 | Gerado com blocos verificados: REVERSED SQ(9) + K1 P=16 nl=0 dead=[0..15;7]. |
| 16 to 10 | `raynquist` | 197 | 16x22 | Fonte: livro de balanceadores do Raynquist (fall 2025), '16-10 balancer'. |
| 16 to 11 | `generated` | 383 | 16x37 | Gerado com blocos verificados: REVERSED SQ(11) + K1 P=16 nl=0 dead=[11, 12, 13, 14, 15]. |
| 16 to 12 | `generated` | 354 | 16x35 | Gerado com blocos verificados: REVERSED SQ(12) + K1 P=16 nl=0 dead=[12, 13, 14, 15]. |
| 16 to 13 | `generated` | 495 | 20x36 | Gerado com blocos verificados: REVERSED SQ(13) + K1 P=16 nl=0 dead=[0, 1, 2]. |
| 16 to 14 | `generated` | 458 | 18x34 | Gerado com blocos verificados: REVERSED SQ(14) + K1 P=16 nl=0 dead=[0, 1]. |
| 16 to 15 | `generated` | 459 | 18x34 | Gerado com blocos verificados: REVERSED SQ(15) + K1 P=16 nl=0 dead=[0]. |
| 16 to 16 | `raynquist` | 211 | 16x16 | Fonte: livro de balanceadores do Raynquist (fall 2025), '16-16 balancer'. |
| 16 to 17 | `generated` | 1.351 | 47x59 | Gerado com blocos verificados: SQ(16) + K1 P=32 nl=7 dead=[0]. |
| 16 to 18 | `generated` | 698 | 22x49 | Gerado com blocos verificados: STACK 16->16 + 2x(8->9). |
| 16 to 19 | `generated` | 1.300 | 45x57 | Gerado com blocos verificados: SQ(16) + K1 P=32 nl=6 dead=[0, 1, 2]. |
| 16 to 20 | `generated` | 540 | 20x40 | Gerado com blocos verificados: STACK 16->16 + 2x(8->10). |
| 16 to 21 | `generated` | 1.200 | 27x76 | Gerado com blocos verificados: STACK 16->18 + 3x(6->7). |
| 16 to 22 | `generated` | 982 | 26x68 | Gerado com blocos verificados: STACK 16->16 + 2x(8->11). |
| 16 to 23 | `generated` | 1.219 | 41x53 | Gerado com blocos verificados: SQ(16) + K1 P=32 nl=4 dead=[0..6;7]. |
| 16 to 24 | `generated` | 518 | 24x35 | Gerado com blocos verificados: STACK 16->16 + 4x(4->6). |
| 17 to 1 | `generated` | 875 | 47x57 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..15;16]) + SQ(1). |
| 17 to 2 | `generated` | 950 | 47x46 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[2..16;15]) + SQ(2). |
| 17 to 3 | `generated` | 979 | 47x52 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[3..16;14]) + SQ(3). |
| 17 to 4 | `generated` | 987 | 47x52 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[4..16;13]) + SQ(4). |
| 17 to 5 | `generated` | 1.023 | 47x55 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[5..16;12]) + SQ(5). |
| 17 to 6 | `generated` | 1.056 | 47x56 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[6..16;11]) + SQ(6). |
| 17 to 7 | `generated` | 1.075 | 47x57 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[7..16;10]) + SQ(7). |
| 17 to 8 | `generated` | 1.081 | 47x55 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[8..16;9]) + SQ(8). |
| 17 to 9 | `generated` | 1.145 | 47x59 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[9..16;8]) + SQ(9). |
| 17 to 10 | `generated` | 1.219 | 47x60 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[0..16;7]) + SQ(10). |
| 17 to 11 | `generated` | 1.275 | 47x64 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[11, 12, 13, 14, 15, 16]) + SQ(11). |
| 17 to 12 | `generated` | 1.264 | 47x62 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[0, 1, 2, 3, 4]) + SQ(12). |
| 17 to 13 | `generated` | 1.357 | 47x63 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[13, 14, 15, 16]) + SQ(13). |
| 17 to 14 | `generated` | 1.350 | 47x61 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[0, 1, 2]) + SQ(14). |
| 17 to 15 | `generated` | 1.347 | 47x61 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[15, 16]) + SQ(15). |
| 17 to 16 | `generated` | 1.334 | 47x59 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[0]) + SQ(16). |
| 17 to 17 | `generated` | 1.144 | 47x43 | Gerado com blocos verificados: LOOP(32-32) nl=7. |
| 17 to 18 | `generated` | 2.248 | 48x84 | Gerado com blocos verificados: SQ(17) + K1 P=32 nl=7 dead=[0]. |
| 17 to 19 | `generated` | 2.220 | 47x84 | Gerado com blocos verificados: SQ(17) + K1 P=32 nl=6 dead=[0, 1]. |
| 17 to 20 | `generated` | 2.198 | 48x82 | Gerado com blocos verificados: SQ(17) + K1 P=32 nl=6 dead=[0, 1, 2]. |
| 17 to 21 | `generated` | 2.174 | 47x82 | Gerado com blocos verificados: SQ(17) + K1 P=32 nl=5 dead=[17, 18, 19, 20]. |
| 17 to 22 | `generated` | 2.173 | 49x84 | Gerado com blocos verificados: SQ(17) + K1p P=32 loops=7+3. |
| 17 to 23 | `generated` | 2.139 | 47x80 | Gerado com blocos verificados: SQ(17) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4, 5]. |
| 17 to 24 | `generated` | 2.097 | 48x78 | Gerado com blocos verificados: SQ(17) + K1 P=32 nl=4 dead=[0..6;7]. |
| 18 to 1 | `generated` | 90 | 18x13 | Gerado com blocos verificados: DSTACK 3x(6->1) + 3->1. |
| 18 to 2 | `generated` | 97 | 18x14 | Gerado com blocos verificados: DSTACK 3x(6->1) + 3->2. |
| 18 to 3 | `generated` | 102 | 18x16 | Gerado com blocos verificados: DSTACK 3x(6->1) + 3->3. |
| 18 to 4 | `generated` | 171 | 18x19 | Gerado com blocos verificados: DSTACK 9x(2->1) + 9->4. |
| 18 to 5 | `generated` | 210 | 18x25 | Gerado com blocos verificados: DSTACK 9x(2->1) + 9->5. |
| 18 to 6 | `generated` | 193 | 18x23 | Gerado com blocos verificados: DSTACK 9x(2->1) + 9->6. |
| 18 to 7 | `generated` | 259 | 18x25 | Gerado com blocos verificados: DSTACK 9x(2->1) + 9->7. |
| 18 to 8 | `generated` | 229 | 18x23 | Gerado com blocos verificados: REVERSED STACK 8->9 + 9x(1->2). |
| 18 to 9 | `generated` | 228 | 18x23 | Gerado com blocos verificados: REVERSED STACK 9->9 + 9x(1->2). |
| 18 to 10 | `generated` | 419 | 18x37 | Gerado com blocos verificados: DSTACK 3x(6->4) + 12->10. |
| 18 to 11 | `generated` | 605 | 18x55 | Gerado com blocos verificados: DSTACK 3x(6->4) + 12->11. |
| 18 to 12 | `generated` | 398 | 18x34 | Gerado com blocos verificados: DSTACK 3x(6->4) + 12->12. |
| 18 to 13 | `generated` | 976 | 22x69 | Gerado com blocos verificados: REVERSED STACK 13->16 + 2x(8->9). |
| 18 to 14 | `generated` | 811 | 24x53 | Gerado com blocos verificados: DSTACK 2x(9->7) + 14->14. |
| 18 to 15 | `generated` | 693 | 24x44 | Gerado com blocos verificados: REVERSED STACK 15->15 + 3x(5->6). |
| 18 to 16 | `generated` | 692 | 22x49 | Gerado com blocos verificados: REVERSED STACK 16->16 + 2x(8->9). |
| 18 to 17 | `generated` | 2.230 | 47x84 | Gerado com blocos verificados: REV(K1 P=32 nl=7 dead=[0]) + SQ(17). |
| 18 to 18 | `generated` | 1.125 | 46x41 | Gerado com blocos verificados: LOOP(32-32) nl=7. |
| 18 to 19 | `generated` | 2.210 | 46x82 | Gerado com blocos verificados: SQ(18) + K1 P=32 nl=6 dead=[0]. |
| 18 to 20 | `generated` | 1.706 | 46x83 | Gerado com blocos verificados: STACK 18->18 + 2x(9->10). |
| 18 to 21 | `generated` | 1.647 | 46x68 | Gerado com blocos verificados: STACK 18->18 + 3x(6->7). |
| 18 to 22 | `generated` | 2.026 | 46x98 | Gerado com blocos verificados: STACK 18->18 + 2x(9->11). |
| 18 to 23 | `generated` | 2.129 | 46x78 | Gerado com blocos verificados: SQ(18) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 18 to 24 | `generated` | 1.447 | 46x60 | Gerado com blocos verificados: STACK 18->18 + 3x(6->8). |
| 19 to 1 | `generated` | 796 | 45x53 | Gerado com blocos verificados: REVERSED K1 P=32 nl=0 dead=[0..17;18]. |
| 19 to 2 | `generated` | 813 | 45x56 | Gerado com blocos verificados: REVERSED SQ(2) + K1 P=32 nl=0 dead=[0..16;17]. |
| 19 to 3 | `generated` | 844 | 45x62 | Gerado com blocos verificados: REVERSED SQ(3) + K1 P=32 nl=0 dead=[0..15;16]. |
| 19 to 4 | `generated` | 935 | 45x50 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0..14;15]) + SQ(4). |
| 19 to 5 | `generated` | 971 | 45x53 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0..13;14]) + SQ(5). |
| 19 to 6 | `generated` | 983 | 45x54 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[6..18;13]) + SQ(6). |
| 19 to 7 | `generated` | 1.023 | 45x55 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0..11;12]) + SQ(7). |
| 19 to 8 | `generated` | 1.028 | 45x53 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[8..18;11]) + SQ(8). |
| 19 to 9 | `generated` | 1.093 | 45x57 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0..9;10]) + SQ(9). |
| 19 to 10 | `generated` | 1.113 | 45x58 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[10..18;9]) + SQ(10). |
| 19 to 11 | `generated` | 1.222 | 45x62 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0..7;8]) + SQ(11). |
| 19 to 12 | `generated` | 1.211 | 45x60 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0..6;7]) + SQ(12). |
| 19 to 13 | `generated` | 1.304 | 45x61 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0, 1, 2, 3, 4, 5]) + SQ(13). |
| 19 to 14 | `generated` | 1.288 | 45x59 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[14, 15, 16, 17, 18]) + SQ(14). |
| 19 to 15 | `generated` | 1.294 | 45x59 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0, 1, 2, 3]) + SQ(15). |
| 19 to 16 | `generated` | 1.281 | 45x57 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0, 1, 2]) + SQ(16). |
| 19 to 17 | `generated` | 2.201 | 47x84 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0, 1]) + SQ(17). |
| 19 to 18 | `generated` | 2.191 | 46x82 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0]) + SQ(18). |
| 19 to 19 | `generated` | 1.107 | 45x41 | Gerado com blocos verificados: LOOP(32-32) nl=6. |
| 19 to 20 | `generated` | 2.173 | 46x80 | Gerado com blocos verificados: SQ(19) + K1 P=32 nl=6 dead=[0]. |
| 19 to 21 | `generated` | 2.149 | 45x80 | Gerado com blocos verificados: SQ(19) + K1 P=32 nl=5 dead=[19, 20]. |
| 19 to 22 | `generated` | 2.139 | 47x82 | Gerado com blocos verificados: SQ(19) + K1p P=32 loops=7+3. |
| 19 to 23 | `generated` | 2.114 | 45x78 | Gerado com blocos verificados: SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3]. |
| 19 to 24 | `generated` | 2.072 | 46x76 | Gerado com blocos verificados: SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 20 to 1 | `generated` | 87 | 20x13 | Gerado com blocos verificados: DSTACK 5x(4->1) + 5->1. |
| 20 to 2 | `generated` | 93 | 20x14 | Gerado com blocos verificados: DSTACK 5x(4->1) + 5->2. |
| 20 to 3 | `generated` | 119 | 20x16 | Gerado com blocos verificados: DSTACK 5x(4->1) + 5->3. |
| 20 to 4 | `generated` | 119 | 20x16 | Gerado com blocos verificados: REVERSED STACK 4->5 + 5x(1->4). |
| 20 to 5 | `generated` | 124 | 20x18 | Gerado com blocos verificados: REVERSED STACK 5->5 + 5x(1->4). |
| 20 to 6 | `generated` | 250 | 20x25 | Gerado com blocos verificados: DSTACK 4x(5->2) + 8->6. |
| 20 to 7 | `generated` | 271 | 20x28 | Gerado com blocos verificados: DSTACK 4x(5->2) + 8->7. |
| 20 to 8 | `generated` | 229 | 20x24 | Gerado com blocos verificados: REVERSED STACK 8->10 + 10x(1->2). |
| 20 to 9 | `generated` | 302 | 20x31 | Gerado com blocos verificados: REVERSED STACK 9->10 + 10x(1->2). |
| 20 to 10 | `generated` | 252 | 20x25 | Gerado com blocos verificados: REVERSED STACK 10->10 + 10x(1->2). |
| 20 to 11 | `generated` | 710 | 20x61 | Gerado com blocos verificados: REVERSED STACK 11->16 + 2x(8->10). |
| 20 to 12 | `generated` | 646 | 32x46 | Gerado com blocos verificados: DSTACK 4x(5->3) + 12->12. |
| 20 to 13 | `generated` | 822 | 22x60 | Gerado com blocos verificados: REVERSED STACK 13->16 + 2x(8->10). |
| 20 to 14 | `generated` | 787 | 20x58 | Gerado com blocos verificados: DSTACK 2x(10->8) + 16->14. |
| 20 to 15 | `raynquist` | 277 | 20x19 | Fonte: livro de balanceadores do Raynquist (fall 2025), '20-15 balancer'. |
| 20 to 16 | `generated` | 538 | 20x40 | Gerado com blocos verificados: REVERSED STACK 16->16 + 2x(8->10). |
| 20 to 17 | `generated` | 2.178 | 47x82 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0, 1, 2]) + SQ(17). |
| 20 to 18 | `generated` | 1.691 | 46x84 | Gerado com blocos verificados: DSTACK 2x(10->9) + 18->18. |
| 20 to 19 | `generated` | 2.153 | 45x80 | Gerado com blocos verificados: REV(K1 P=32 nl=6 dead=[0]) + SQ(19). |
| 20 to 20 | `generated` | 1.089 | 44x39 | Gerado com blocos verificados: LOOP(32-32) nl=6. |
| 20 to 21 | `generated` | 2.140 | 44x78 | Gerado com blocos verificados: SQ(20) + K1 P=32 nl=5 dead=[0]. |
| 20 to 22 | `generated` | 2.052 | 44x98 | Gerado com blocos verificados: STACK 20->20 + 2x(10->11). |
| 20 to 23 | `generated` | 2.102 | 44x78 | Gerado com blocos verificados: SQ(20) + K1p P=32 loops=6+3. |
| 20 to 24 | `generated` | 1.753 | 44x76 | Gerado com blocos verificados: STACK 20->20 + 4x(5->6). |
| 21 to 1 | `generated` | 117 | 21x14 | Gerado com blocos verificados: DSTACK 3x(7->1) + 3->1. |
| 21 to 2 | `generated` | 124 | 21x15 | Gerado com blocos verificados: DSTACK 3x(7->1) + 3->2. |
| 21 to 3 | `generated` | 129 | 21x17 | Gerado com blocos verificados: DSTACK 3x(7->1) + 3->3. |
| 21 to 4 | `generated` | 289 | 24x27 | Gerado com blocos verificados: DSTACK 3x(7->2) + 6->4. |
| 21 to 5 | `generated` | 323 | 24x31 | Gerado com blocos verificados: DSTACK 3x(7->2) + 6->5. |
| 21 to 6 | `generated` | 302 | 24x29 | Gerado com blocos verificados: DSTACK 3x(7->2) + 6->6. |
| 21 to 7 | `generated` | 390 | 28x33 | Gerado com blocos verificados: DSTACK 7x(3->1) + 7->7. |
| 21 to 8 | `generated` | 466 | 27x35 | Gerado com blocos verificados: DSTACK 3x(7->3) + 9->8. |
| 21 to 9 | `generated` | 465 | 27x35 | Gerado com blocos verificados: DSTACK 3x(7->3) + 9->9. |
| 21 to 10 | `generated` | 558 | 27x43 | Gerado com blocos verificados: DSTACK 3x(7->4) + 12->10. |
| 21 to 11 | `generated` | 744 | 27x61 | Gerado com blocos verificados: DSTACK 3x(7->4) + 12->11. |
| 21 to 12 | `generated` | 537 | 27x40 | Gerado com blocos verificados: DSTACK 3x(7->4) + 12->12. |
| 21 to 13 | `generated` | 974 | 35x61 | Gerado com blocos verificados: DSTACK 7x(3->2) + 14->13. |
| 21 to 14 | `generated` | 683 | 35x41 | Gerado com blocos verificados: DSTACK 7x(3->2) + 14->14. |
| 21 to 15 | `generated` | 755 | 27x46 | Gerado com blocos verificados: DSTACK 3x(7->5) + 15->15. |
| 21 to 16 | `generated` | 1.189 | 27x77 | Gerado com blocos verificados: DSTACK 3x(7->6) + 18->16. |
| 21 to 17 | `generated` | 2.153 | 49x82 | Gerado com blocos verificados: REV(K1 P=32 nl=5 dead=[17, 18, 19, 20]) + SQ(17). |
| 21 to 18 | `generated` | 1.635 | 46x68 | Gerado com blocos verificados: REVERSED STACK 18->18 + 3x(6->7). |
| 21 to 19 | `generated` | 2.128 | 47x80 | Gerado com blocos verificados: REV(K1 P=32 nl=5 dead=[19, 20]) + SQ(19). |
| 21 to 20 | `generated` | 2.119 | 44x78 | Gerado com blocos verificados: REV(K1 P=32 nl=5 dead=[0]) + SQ(20). |
| 21 to 21 | `generated` | 1.075 | 43x39 | Gerado com blocos verificados: LOOP(32-32) nl=5. |
| 21 to 22 | `generated` | 2.131 | 51x84 | Gerado com blocos verificados: SQ(21) + K1p P=32 loops=9+1. |
| 21 to 23 | `generated` | 2.097 | 47x80 | Gerado com blocos verificados: SQ(21) + K1p P=32 loops=7+2. |
| 21 to 24 | `generated` | 1.456 | 43x62 | Gerado com blocos verificados: STACK 21->21 + 3x(7->8). |
| 22 to 1 | `generated` | 204 | 22x29 | Gerado com blocos verificados: REVERSED STACK 1->11 + 11x(1->2). |
| 22 to 2 | `generated` | 227 | 22x32 | Gerado com blocos verificados: REVERSED STACK 2->11 + 11x(1->2). |
| 22 to 3 | `generated` | 254 | 22x38 | Gerado com blocos verificados: REVERSED STACK 3->11 + 11x(1->2). |
| 22 to 4 | `generated` | 259 | 22x38 | Gerado com blocos verificados: REVERSED STACK 4->11 + 11x(1->2). |
| 22 to 5 | `generated` | 293 | 22x41 | Gerado com blocos verificados: REVERSED STACK 5->11 + 11x(1->2). |
| 22 to 6 | `generated` | 354 | 22x42 | Gerado com blocos verificados: REVERSED STACK 6->11 + 11x(1->2). |
| 22 to 7 | `generated` | 371 | 22x43 | Gerado com blocos verificados: REVERSED STACK 7->11 + 11x(1->2). |
| 22 to 8 | `generated` | 381 | 22x41 | Gerado com blocos verificados: REVERSED STACK 8->11 + 11x(1->2). |
| 22 to 9 | `generated` | 443 | 22x45 | Gerado com blocos verificados: REVERSED STACK 9->11 + 11x(1->2). |
| 22 to 10 | `generated` | 324 | 22x31 | Gerado com blocos verificados: DSTACK 11x(2->1) + 11->10. |
| 22 to 11 | `generated` | 318 | 22x29 | Gerado com blocos verificados: REVERSED STACK 11->11 + 11x(1->2). |
| 22 to 12 | `generated` | 861 | 26x71 | Gerado com blocos verificados: DSTACK 2x(11->6) + 12->12. |
| 22 to 13 | `generated` | 1.232 | 42x67 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..8;9]) + SQ(13). |
| 22 to 14 | `generated` | 972 | 26x72 | Gerado com blocos verificados: DSTACK 2x(11->7) + 14->14. |
| 22 to 15 | `generated` | 946 | 26x64 | Gerado com blocos verificados: DSTACK 2x(11->10) + 20->15. |
| 22 to 16 | `generated` | 972 | 26x69 | Gerado com blocos verificados: DSTACK 2x(11->8) + 16->16. |
| 22 to 17 | `generated` | 2.134 | 47x80 | Gerado com blocos verificados: REV(K1 P=32 nl=5 dead=[0, 1, 2, 3, 4]) + SQ(17). |
| 22 to 18 | `generated` | 2.015 | 46x99 | Gerado com blocos verificados: DSTACK 2x(11->9) + 18->18. |
| 22 to 19 | `generated` | 2.109 | 45x78 | Gerado com blocos verificados: REV(K1 P=32 nl=5 dead=[0, 1, 2]) + SQ(19). |
| 22 to 20 | `generated` | 1.740 | 44x84 | Gerado com blocos verificados: DSTACK 2x(11->10) + 20->20. |
| 22 to 21 | `generated` | 2.089 | 43x76 | Gerado com blocos verificados: REV(K1 P=32 nl=5 dead=[0]) + SQ(21). |
| 22 to 22 | `generated` | 1.083 | 42x37 | Gerado com blocos verificados: LOOP(32-32) nl=5. |
| 22 to 23 | `generated` | 2.038 | 42x74 | Gerado com blocos verificados: SQ(22) + K1 P=32 nl=4 dead=[0]. |
| 22 to 24 | `generated` | 1.992 | 42x72 | Gerado com blocos verificados: SQ(22) + K1 P=32 nl=4 dead=[0, 1]. |
| 23 to 1 | `generated` | 616 | 41x45 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..21;22]) + SQ(1). |
| 23 to 2 | `generated` | 628 | 41x48 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..20;21]) + SQ(2). |
| 23 to 3 | `generated` | 657 | 41x54 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..19;20]) + SQ(3). |
| 23 to 4 | `generated` | 687 | 41x54 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..18;19]) + SQ(4). |
| 23 to 5 | `generated` | 723 | 41x57 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..17;18]) + SQ(5). |
| 23 to 6 | `generated` | 736 | 41x58 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..16;17]) + SQ(6). |
| 23 to 7 | `generated` | 755 | 41x59 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..15;16]) + SQ(7). |
| 23 to 8 | `generated` | 913 | 41x49 | Gerado com blocos verificados: REVERSED SQ(8) + K1 P=32 nl=4 dead=[8..22;15]. |
| 23 to 9 | `generated` | 983 | 41x53 | Gerado com blocos verificados: REVERSED SQ(9) + K1 P=32 nl=4 dead=[0..13;14]. |
| 23 to 10 | `generated` | 1.004 | 41x54 | Gerado com blocos verificados: REVERSED SQ(10) + K1 P=32 nl=4 dead=[0..12;13]. |
| 23 to 11 | `generated` | 1.058 | 41x58 | Gerado com blocos verificados: REVERSED SQ(11) + K1 P=32 nl=4 dead=[0..11;12]. |
| 23 to 12 | `generated` | 1.063 | 41x56 | Gerado com blocos verificados: REVERSED SQ(12) + K1 P=32 nl=4 dead=[12..22;11]. |
| 23 to 13 | `generated` | 1.188 | 41x65 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..9;10]) + SQ(13). |
| 23 to 14 | `generated` | 1.172 | 41x63 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..8;9]) + SQ(14). |
| 23 to 15 | `generated` | 1.169 | 41x63 | Gerado com blocos verificados: REV(K1 P=32 nl=0 dead=[0..7;8]) + SQ(15). |
| 23 to 16 | `generated` | 1.171 | 41x53 | Gerado com blocos verificados: REVERSED SQ(16) + K1 P=32 nl=4 dead=[0..6;7]. |
| 23 to 17 | `generated` | 2.087 | 47x80 | Gerado com blocos verificados: REVERSED SQ(17) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4, 5]. |
| 23 to 18 | `generated` | 2.077 | 46x78 | Gerado com blocos verificados: REVERSED SQ(18) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 23 to 19 | `generated` | 2.062 | 45x78 | Gerado com blocos verificados: REVERSED SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3]. |
| 23 to 20 | `generated` | 2.074 | 45x76 | Gerado com blocos verificados: REV(K1 P=32 nl=4 dead=[20, 21, 22]) + SQ(20). |
| 23 to 21 | `generated` | 2.065 | 43x76 | Gerado com blocos verificados: REV(K1 P=32 nl=4 dead=[0, 1]) + SQ(21). |
| 23 to 22 | `generated` | 1.986 | 42x74 | Gerado com blocos verificados: REVERSED SQ(22) + K1 P=32 nl=4 dead=[0]. |
| 23 to 23 | `generated` | 1.069 | 41x37 | Gerado com blocos verificados: LOOP(32-32) nl=4. |
| 23 to 24 | `generated` | 1.981 | 42x72 | Gerado com blocos verificados: SQ(23) + K1 P=32 nl=4 dead=[0]. |
| 24 to 1 | `generated` | 87 | 24x13 | Gerado com blocos verificados: DSTACK 3x(8->1) + 3->1. |
| 24 to 2 | `generated` | 94 | 24x14 | Gerado com blocos verificados: DSTACK 3x(8->1) + 3->2. |
| 24 to 3 | `generated` | 99 | 24x16 | Gerado com blocos verificados: DSTACK 3x(8->1) + 3->3. |
| 24 to 4 | `generated` | 131 | 24x17 | Gerado com blocos verificados: DSTACK 4x(6->1) + 4->4. |
| 24 to 5 | `generated` | 167 | 24x22 | Gerado com blocos verificados: REVERSED STACK 5->6 + 6x(1->4). |
| 24 to 6 | `generated` | 146 | 24x20 | Gerado com blocos verificados: REVERSED STACK 6->6 + 6x(1->4). |
| 24 to 7 | `generated` | 353 | 24x30 | Gerado com blocos verificados: DSTACK 3x(8->3) + 9->7. |
| 24 to 8 | `generated` | 323 | 24x28 | Gerado com blocos verificados: DSTACK 3x(8->3) + 9->8. |
| 24 to 9 | `generated` | 322 | 24x28 | Gerado com blocos verificados: DSTACK 3x(8->3) + 9->9. |
| 24 to 10 | `generated` | 333 | 24x31 | Gerado com blocos verificados: DSTACK 12x(2->1) + 12->10. |
| 24 to 11 | `generated` | 515 | 24x49 | Gerado com blocos verificados: REVERSED STACK 11->12 + 12x(1->2). |
| 24 to 12 | `generated` | 308 | 24x28 | Gerado com blocos verificados: REVERSED STACK 12->12 + 12x(1->2). |
| 24 to 13 | `generated` | 806 | 24x55 | Gerado com blocos verificados: DSTACK 4x(6->4) + 16->13. |
| 24 to 14 | `generated` | 769 | 24x53 | Gerado com blocos verificados: DSTACK 4x(6->4) + 16->14. |
| 24 to 15 | `generated` | 576 | 24x37 | Gerado com blocos verificados: REVERSED STACK 15->15 + 3x(5->8). |
| 24 to 16 | `generated` | 522 | 24x35 | Gerado com blocos verificados: DSTACK 4x(6->4) + 16->16. |
| 24 to 17 | `generated` | 2.093 | 48x78 | Gerado com blocos verificados: REVERSED SQ(17) + K1 P=32 nl=4 dead=[0..6;7]. |
| 24 to 18 | `generated` | 1.439 | 46x60 | Gerado com blocos verificados: DSTACK 3x(8->6) + 18->18. |
| 24 to 19 | `generated` | 2.068 | 46x76 | Gerado com blocos verificados: REVERSED SQ(19) + K1 P=32 nl=4 dead=[0, 1, 2, 3, 4]. |
| 24 to 20 | `generated` | 1.572 | 44x71 | Gerado com blocos verificados: DSTACK 2x(12->10) + 20->20. |
| 24 to 21 | `generated` | 1.448 | 43x62 | Gerado com blocos verificados: REVERSED STACK 21->21 + 3x(7->8). |
| 24 to 22 | `generated` | 1.988 | 42x72 | Gerado com blocos verificados: REVERSED SQ(22) + K1 P=32 nl=4 dead=[0, 1]. |
| 24 to 23 | `generated` | 1.979 | 42x72 | Gerado com blocos verificados: REVERSED SQ(23) + K1 P=32 nl=4 dead=[0]. |
| 24 to 24 | `generated` | 1.055 | 40x35 | Gerado com blocos verificados: LOOP(32-32) nl=4. |
