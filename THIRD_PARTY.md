# Componentes de terceiros

O jogo usa **pygame-ce 2.5.8** (LGPL 2.1 e licenças das bibliotecas SDL e da fonte
distribuída pelo pacote) e o interpretador **CPython** (licença PSF).
O ZIP para jogadores inclui os avisos encontrados no pacote pygame-ce e a
licença do Python em `licenses/`. O import continua sendo `pygame`.

Código-fonte do pygame-ce: https://github.com/pygame-community/pygame-ce
Código-fonte do CPython: https://github.com/python/cpython

O empacotamento usa **PyInstaller**, GPL com exceção para distribuição dos
executáveis gerados. O servidor usa Flask e Waitress, com suas próprias licenças.
O servidor não é embutido no executável do jogo.

O site usa a fonte **Tiny5**, do Tiny5 Project Authors, sob SIL Open Font License
1.1. O arquivo é servido localmente em `docs/assets/fonts/Tiny5.ttf`, acompanhado
da licença `OFL-Tiny5.txt`. Fonte: https://github.com/google/fonts/tree/main/ofl/tiny5

Não foram utilizadas imagens, músicas ou sprites externos. Os cenários e o ícone
do site foram criados em código para este projeto. Os gráficos são provisórios.

Para modificar ou substituir bibliotecas, use o código-fonte do projeto,
instale as dependências desejadas em uma venv e gere novamente o executável
com `python scripts/build_windows.py`.
