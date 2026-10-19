# Personalizar o projeto

Os gráficos provisórios do jogo são desenhados com retângulos, linhas e textos.
Não há dependência de imagens externas. Por isso o protótipo pode ser executado
imediatamente e você pode trocar o visual por etapas.

## Jogo

- **Nome, cores, resolução, palavras:** `game/settings.py`.
- **Computador, casa e cidade:** método `scene` em `game/main.py`.
- **Menu e história:** método `draw_menu`.
- **HUD, palavras e terminal de entrada:** método `draw_play`.
- **Pontuação e combo:** método `shoot`.
- **Vidas iniciais:** método `reset`.
- **Velocidade e palavras permitidas:** método `spawn`.
- **Intervalo de surgimento e dano:** método `update`.
- **Banco e integração HTTP:** `game/storage.py`.

Prefira palavras com letras de a a z, sem espaços, até nove letras. Se quiser
palavras maiores, ajuste `maximum` em `spawn`, a largura das caixas e as colunas.
O campo de digitação aceita até 24 letras; o nickname, até 18 caracteres.

Para trocar o desenho por sprites, crie uma pasta `game/assets`, carregue as
imagens em `__init__` (uma vez, não a cada frame) e desenhe com `blit` em `scene`.
O build precisará incluir essa pasta usando `--add-data` e localizar os arquivos
tanto no código quanto no executável PyInstaller. Atualize os testes e gere o
executável após a mudança. Para mudanças só de cor e texto isso não é necessário.

## Site

- **Texto e seções:** `docs/index.html`.
- **Cores, layout e responsividade:** `docs/style.css`.
- **Consulta ao ranking:** `docs/app.js`.
- **URLs de servidor, download e GitHub:** `docs/config.js`.
- **Captura do jogo:** `docs/assets/gameplay.png`.

Depois de mudar o jogo, atualize a captura para que o site represente a versão
distribuída. O site não usa fontes externas, bibliotecas JS ou serviço de imagem.

## Banco de dados

O `schema.sql` descreve a tabela do ranking compartilhado. O banco local do
jogo tem uma tabela semelhante com a coluna `synced`. Para evoluir o esquema
sem perder dados, escreva uma migração SQL; `CREATE TABLE IF NOT EXISTS` não
altera tabelas já existentes. Faça backup antes de mudar um banco usado.

As APIs esperam os campos `id`, `nickname`, `score`, `words`, `accuracy`,
`duration` e `level`. Se mudar a fórmula de nível, atualize a validação da API.

## Próximas melhorias viáveis

1. Sprites próprios para o computador gigante e para a casa.
2. Sons curtos de tiro, impacto e fim de jogo, com opção de silenciar.
3. Escolha de dificuldade antes da partida.
4. Palavras por tema (tecnologia, escola, espaço).

Conclua primeiro um ciclo completo de jogo → servidor → ranking no site.
