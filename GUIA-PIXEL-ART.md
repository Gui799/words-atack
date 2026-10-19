# Direção de arte — Words Atack

## Base de produção definida

**Desenhe em 550 × 380 pixels. Exibição padrão: 1100 × 760, escala 2×.**
Isso corresponde à janela atual do protótipo. A proporção é **55:38** (cerca
de 1,45:1); não é 16:9. Esta escolha preserva a composição atual. Uma mudança
para 16:9 exigiria ajustar o layout e as posições antes de produzir o cenário.

A base é um sistema de medidas para as futuras artes. O executável atual ainda
desenha os elementos provisórios diretamente em 1100 × 760. Não basta colocar
PNGs em uma pasta: integraremos os sprites e suas posições no código.

Use lápis de **1 pixel**, sem suavização, e exporte em **PNG no tamanho original**.
Não amplie os arquivos para 2× antes de enviar: a ampliação será feita pelo jogo.
Itens isolados devem ter fundo transparente. Fundo completo pode ser opaco.

## Tamanhos dos arquivos (largura × altura)

| Arquivo sugerido | Arte original | Exibição 2× | Observação |
|---|---:|---:|---|
| `background.png` | 550 × 380 | 1100 × 760 | Céu/fundo completo; sem textos e interface |
| `city.png` | 550 × 80 | 1100 × 160 | Camada transparente com prédios |
| `computer.png` | 192 × 80 | 384 × 160 | Computador gigante completo, incluindo pedestal |
| `house.png` | 96 × 48 | 192 × 96 | Casa completa; canhão separado |
| `cannon.png` | 24 × 32 | 48 × 64 | Centro horizontal alinhado ao topo da casa |
| `player.png` | 16 × 24 | 32 × 48 | Opcional: personagem decorativo, sem movimento previsto |
| `impact.png` | 32 × 32 por quadro | 64 × 64 | Explosão; sugestão de quatro quadros |
| `shot.png` | 16 × 16 por quadro | 32 × 32 | Flash do canhão; sugestão de três quadros |
| `heart.png` | 8 × 8 | 16 × 16 | Integridade/vida; estado vazio pode ser outro arquivo |
| `tile.png` | 16 × 16 | 32 × 32 | Unidade recomendada para chão e detalhes repetidos |

O cenário completo não precisa ser múltiplo de 16. A grade 16 × 16 é uma
referência para peças reutilizáveis. Os tamanhos acima são canvases de arquivo;
partes transparentes podem acomodar os desenhos menores.

## Composição na base 550 × 380

Coordenadas abaixo são do arquivo pequeno. Origem **(0, 0) no canto superior
esquerdo**; x cresce para a direita e y para baixo. Os intervalos são aproximados
porque o protótipo atual usa algumas posições ímpares na escala 2×.

| Região | Posição e espaço reservado |
|---|---|
| HUD de nickname, pontos, nível e vidas | y de 0 a 38; evite detalhes essenciais no fundo |
| Computador gigante | centro em x=275; arquivo em torno de x=179, y=40 |
| Palavras em queda | cinco colunas em x≈60, 168, 275, 383 e 490; começam em y≈124 |
| Cidade | `city.png` em x=0, y=212; base dos prédios em y≈292 |
| Casa | `house.png` em x=227, y=248; parte inferior em y≈296 |
| Canhão | `cannon.png` em x=263, y=236; saída do tiro por volta de x=275, y=248 |
| Limite de impacto/escudo | y≈292; a lógica de dano continua definida no código |
| Terminal de digitação | y de 305 a 380; não desenhe letras no fundo |

Se o canhão for feito em 24 × 32, mantenha seu pivô na base central e deixe
espaço transparente em volta. O ponto de saída do laser será ajustado no código
ao integrar a arte; não precisa ser um projétil desenhado no arquivo da casa.

## Animações

Para começar, faça artes estáticas de computador, cidade, casa e canhão. Depois:

- Computador: quatro quadros de 192 × 80 em faixa de **768 × 80**.
- Canhão: três quadros de 24 × 32 em faixa de **72 × 32**.
- Impacto: quatro quadros de 32 × 32 em faixa de **128 × 32**.
- Flash: três quadros de 16 × 16 em faixa de **48 × 16**.

Quadros da esquerda para a direita, todos com o mesmo tamanho e ponto de apoio.
Sem margens entre quadros. Exporte também o arquivo editável do seu programa.
A animação ainda precisará ser integrada ao jogo; o protótipo não lê spritesheets.

## Paleta inicial

| Cor | Hexadecimal | Função |
|---|---|---|
| Azul quase preto | `#090F1B` | Fundo |
| Azul escuro | `#111D2E` | Painéis e sombras |
| Azul cinza | `#31485A` | Prédios, bordas e volumes |
| Cinza claro | `#9BAFC2` | Metal e detalhes |
| Branco frio | `#E8F3F9` | Destaques e textos |
| Verde água | `#52F1CE` | Laser e defesa |
| Coral | `#FF6873` | Computador, ameaça e dano |
| Amarelo | `#FFD377` | Janelas, energia e acertos |

Essas oito cores são um ponto de partida, não uma limitação técnica. Prefira
contraste alto para as palavras e evite muitos detalhes atrás delas.

## Escala e integração

No Pygame, usaremos `pygame.transform.scale` para ampliar os sprites por 2×,
sem filtro de suavização. Coordenadas de arte são multiplicadas por 2 ao usar
a superfície atual. O `smoothscale` existente na apresentação da janela deverá
ser substituído por escala sem filtro quando integrarmos o conjunto de sprites.
Para pixels uniformes em janelas diferentes, a apresentação deverá usar uma
superfície base e escala inteira, com faixas nas sobras. A versão atual ainda
permite redimensionamento suave; o executável não foi alterado nesta revisão.

No site, `image-rendering: pixelated` foi aplicado às imagens e removemos rotações
e cantos arredondados. Isso preserva o estilo, mas não transforma uma captura
geométrica antiga em arte pixelada. O novo cenário do topo é um conceito SVG
provisório com formas em grade; a captura real permanece acessível abaixo dele.

Títulos usam **Tiny5**, servida localmente com licença OFL. Parágrafos continuam
com fonte de leitura comum. No jogo, palavras precisam continuar legíveis;
a fonte final das palavras será escolhida ao integrar as artes.

## Atualizar seu repositório já publicado

Use o pacote de atualização do site, que contém a pasta `docs` e este guia.
Copie os arquivos para a pasta do seu repositório, preservando `docs/config.js`,
onde você já pode ter configurado suas URLs. O pacote de atualização não inclui
esse arquivo para evitar substituir a sua configuração.

Depois, GitHub Desktop → confira Changes → Commit to main → Push origin.
O Pages publicará a atualização. Não é preciso criar outra Release do jogo
porque esta alteração não muda o executável.
