# Guia de pixel art — Words Atack

## Nova base do jogo

- Tela lógica: **640×360 px**.
- Tamanho de apresentação recomendado: **1280×720 px** (escala inteira 2×).
- Paleta diurna: céu azul, água turquesa, areia amarela clara, folhas verdes, contorno azul-marinho, creme e coral.
- Exportação: PNG, fundo transparente para sprites, sem suavização. Os textos do jogo são desenhados pelo Pygame.

Os arquivos gerados para esta prévia estão em `game/assets/`. O Pygame divide os atlas e reduz cada quadro ao tamanho lógico indicado aqui. Ao redesenhar as artes no LibreSprite, use os tamanhos lógicos e os grids abaixo; não é necessário reproduzir as dimensões grandes dos PNGs gerados.

## Tamanhos e spritesheets

| Elemento | Quadro lógico | Grade do sheet | Tamanho total do seu sheet |
|---|---:|---:|---:|
| Cenário diurno completo | 640×360 | imagem única | 640×360 |
| Computador inimigo | 96×64 | 4 colunas × 2 linhas | 384×128 |
| Corações de vida | 8×8 | 4 colunas × 1 linha | 32×8 |
| Moldura da palavra inimiga | 96×24 | 3 colunas × 1 linha | 288×24 |
| Onda do mar | 64×32 | 2 colunas × 2 linhas | 128×64 |
| Tiro laser | 16×16 | 4 colunas × 1 linha | 64×16 |
| Cursor de mira | 16×16 | imagem única | 16×16 |
| Casa | 78×48 | imagem única | 78×48 |
| Canhão laser | 24×32 | imagem única | 24×32 |
| Painel de interface | base 240×80 | 9-slice | 240×80 |
| Botão | base 96×32 | 9-slice | 96×32 |

### Quadros do computador

- Linha 1: espera/idle — expressão normal, piscada, expressão normal, piscada.
- Linha 2: ataque — preparar, tela pisca coral, boca abre, voltar à posição normal.
- Mantenha a mesma base do monitor em todos os quadros; só mova rosto, braços e antena.

### Interface e HUD

Na tela 640×360, a faixa superior ocupa **x=8, y=7, 624×34 px**. Ela mostra nickname, pontos, nível e cinco corações 8×8. O campo de digitação fica na parte inferior, em torno de **x=112, y=303, 416×38 px**. Menu, pausa, ranking e fim de jogo reutilizam os painéis e botões com 9-slice para preservar os cantos ao redimensionar.

O cursor de mira substitui o cursor do sistema durante o jogo. Rótulos, nickname, palavras, pontuação e mensagens permanecem texto dinâmico sobre a arte.

### Movimento da cena

- O mar percorre os quatro quadros de `ondas_sheet.png` em loop.
- Nuvens em blocos se movem em duas velocidades para criar profundidade.
- Para evitar que o movimento distraia da digitação, mantenha os deslocamentos curtos e lentos.

## Convenções para desenhar sheets

1. Faça cada quadro exatamente do mesmo tamanho.
2. Organize na grade indicada, sem espaço entre células e sem cruzar o desenho para o quadro vizinho.
3. Mantenha o ponto de apoio na mesma coordenada em todos os quadros.
4. Use fundo transparente nos sheets e mantenha a mesma paleta entre jogo e interface.
5. Exporte o sheet inteiro em PNG. Não o amplie para 2×; o jogo faz a escala pelo vizinho mais próximo.

As imagens em `game/assets/animations/` são rascunhos iniciais. Você pode substituí-las pelos seus arquivos do LibreSprite, mantendo os nomes e a grade, ou atualizar as dimensões de leitura em `game/rendering.py`.
