# Componentes de terceiros

As músicas chiptune, o ambiente e os efeitos em `game/assets/audio/` são
composições e sons sintetizados para o projeto, sem gravações de terceiros.
O script `scripts/generate_audio.py` permite regenerar esses arquivos WAV.

O jogo usa **pygame-ce 2.5.8** (LGPL 2.1 e licenças das bibliotecas SDL e da fonte
distribuída pelo pacote) e o interpretador **CPython** (licença PSF).
O ZIP para jogadores inclui os avisos encontrados no pacote pygame-ce e a
licença do Python em `licenses/`. O import continua sendo `pygame`.

Código-fonte do pygame-ce: https://github.com/pygame-community/pygame-ce
Código-fonte do CPython: https://github.com/python/cpython

O empacotamento usa **PyInstaller**, GPL com exceção para distribuição dos
executáveis gerados. O servidor usa Flask e Waitress, com suas próprias licenças.
O servidor não é embutido no executável do jogo.

O site e o jogo usam a fonte **Tiny5**, do Tiny5 Project Authors, sob SIL Open
Font License 1.1. Os arquivos estão em `docs/assets/fonts/` e
`game/assets/fonts/`, acompanhados de `OFL-Tiny5.txt`. Fonte:
https://github.com/google/fonts/tree/main/ofl/tiny5

Não foram utilizadas imagens, músicas ou sprites de terceiros. As artes de
`game/assets/` são materiais visuais criados especificamente para esta prévia e
podem ser substituídos pelo grupo. O site mantém suas próprias imagens em `docs/`.

Para modificar ou substituir bibliotecas, use o código-fonte do projeto,
instale as dependências desejadas em uma venv e gere novamente o executável
com `python scripts/build_windows.py`.
