# Publicar Words Atack no GitHub

O projeto foi entregue com código, executável Windows e site preparados.
Este guia não pressupõe que você já tenha criado um repositório.
Substitua `SEU-USUARIO` pelo seu usuário real do GitHub em todos os exemplos.

## 1. Prepare e teste a pasta

Extraia o pacote completo em uma pasta de trabalho. Abra essa pasta no VS Code.
O terminal deve estar na pasta que contém `run_game.py` e `README.md`.

Teste primeiro o procedimento do README: servidor, jogo, configuração F2 e
atualização do ranking. Assim você publica algo que já consegue demonstrar.

## 2. Crie um repositório vazio

Entre em https://github.com/new e escolha:

- **Repository name:** `words-atack`.
- **Description:** `Jogo de defesa por digitação em Pygame, com site e ranking em Flask e SQLite.`
- **Visibility:** Public, para facilitar avaliação e GitHub Pages.
- Deixe desmarcada a criação de README, `.gitignore` e licença. O projeto já
  contém os dois primeiros; você pode escolher uma licença depois.

Clique em **Create repository** e copie a URL HTTPS mostrada pelo GitHub.

## 3. Ajuste o site antes de enviar

Em `docs/config.js`, configure:

```javascript
window.WORDS_ATACK_CONFIG = {
  apiBase: "",
  downloadUrl: "https://github.com/SEU-USUARIO/words-atack/releases/latest/download/WordsAtack-Windows.zip",
  repositoryUrl: "https://github.com/SEU-USUARIO/words-atack"
};
```

Pode deixar `apiBase` vazio enquanto não tiver um servidor publicado. O site
informará que o ranking online ainda não está conectado. O download passará
a funcionar assim que você concluir a criação da Release no passo 5.

## 4. Envie o código pelo Git

Se for seu primeiro uso de Git, configure a autoria. Use um e-mail da sua conta
ou o endereço privado `noreply` mostrado nas configurações de e-mail do GitHub.
Os comandos abaixo afetam somente este repositório.

```powershell
git init -b main
git config user.name "Seu Nome"
git config user.email "SEU-EMAIL"
git add .
git status
git commit -m "feat: cria previa jogavel do Words Atack com site e ranking"
git remote add origin https://github.com/SEU-USUARIO/words-atack.git
git push -u origin main
```

O Git pode abrir o navegador para autenticação. Use o fluxo oferecido pelo
Git Credential Manager; não coloque senha ou token em arquivos do projeto.

Antes do commit, confira em `git status` que não há `.venv`, banco de dados,
`.env`, `dist`, `build`, `.exe` ou ZIP de download. O `.gitignore` já cuida disso.
As capturas PNG do jogo devem ser incluídas.

O executável fica em **Releases**. O repositório guarda o código-fonte.
Não foi criado um commit automático no pacote entregue: a autoria será sua.

## 5. Disponibilize o download em uma Release

No repositório, abra **Releases → Create a new release** (ou **Draft a new release**).

1. Em **Choose a tag**, digite `v0.1.0` e escolha criar essa tag em `main`.
2. Título: `Words Atack — Prévia 0.1.0`.
3. Descrição sugerida:

   > Primeira prévia jogável para Windows 64 bits. Inclui nickname, defesa por
   > digitação, combos e ranking local. Extraia o ZIP e abra WordsAtack.exe.
   > O ranking online depende do servidor configurado. Gráficos provisórios.

4. Arraste **`docs/downloads/WordsAtack-Windows.zip`** para a área de anexos.
   Se já recompilou o jogo, use o ZIP atualizado em `dist/WordsAtack-Windows.zip`.
5. Publique a Release como uma versão normal para o link `releases/latest`
   encontrar o arquivo. Não marque **pre-release** se usar esse link.
6. Teste o download. Preserve o nome exato `WordsAtack-Windows.zip`.

O pacote entregue também traz uma cópia desse ZIP ao lado do ZIP do projeto.
Ela pode ser anexada diretamente. O GitHub adiciona um ZIP do código-fonte
automaticamente; ele é diferente do ZIP para jogar.

## 6. Ative o GitHub Pages

No repositório, abra **Settings → Pages**:

1. Em **Build and deployment → Source**, escolha **Deploy from a branch**.
2. Escolha a branch **main** e a pasta **/docs**.
3. Clique em **Save**.
4. Acompanhe a publicação na aba **Actions** e aguarde aparecer o endereço
   informado pelo GitHub em **Settings → Pages**.

O endereço normalmente será:

```text
https://SEU-USUARIO.github.io/words-atack/
```

Abra o link e teste a versão de celular, os menus e o download. O uso de
caminhos relativos permite publicar o site dentro do nome do repositório.
O arquivo `docs/.nojekyll` mantém a publicação como arquivos estáticos.

**Importante:** Pages não executa Python e não hospeda um banco SQL ativo.
Ele publica HTML, CSS, JavaScript e arquivos estáticos. O executável é baixado
pela Release e aberto no Windows, fora do navegador.

## 7. Conecte um ranking público quando precisar

Para apresentar tudo no mesmo computador, basta o servidor local do README.
Para permitir que outras pessoas enviem pontuações, use uma hospedagem que
execute Python e ofereça **volume persistente** para o SQLite.
Não use armazenamento temporário: ele pode apagar o ranking em reinicializações.

Configuração genérica da hospedagem, a partir da raiz do repositório:

```text
Instalação: python -m pip install -r requirements-server.txt
Inicialização: python run_server.py
```

Defina no painel de ambiente:

```text
HOST=0.0.0.0
PORT=<porta exigida pela hospedagem>
WORDS_ATACK_DB=<caminho absoluto do volume persistente>/ranking.sqlite3
WORDS_ATACK_ORIGINS=https://SEU-USUARIO.github.io
```

Se a hospedagem já fornece `PORT`, mantenha o valor dela. A origem CORS é
`https://SEU-USUARIO.github.io`, sem `/words-atack` no final. O servidor usa
Waitress e não liga o depurador do Flask. A hospedagem deve fornecer HTTPS.

Depois:

1. Verifique `https://SEU-SERVIDOR/api/health`; deve retornar `status: ok`.
2. Em `docs/config.js`, mude `apiBase` para `https://SEU-SERVIDOR`.
3. Envie o commit de configuração ao GitHub e aguarde a atualização do Pages.
4. No jogo, menu **F2**, informe `https://SEU-SERVIDOR` e salve.
5. Termine uma partida e atualize o ranking no site.

Não inclua `/api` no fim da configuração. Não coloque senhas em `config.js`.
O ranking desta prévia não verifica trapaças e não deve ser usado para prêmios.

## 8. Trabalhe com versões pequenas

Para mudanças futuras, use uma branch, por exemplo:

```powershell
git switch -c feat/novos-sprites
```

Edite e teste. Depois:

```powershell
git add .
git commit -m "feat: adiciona sprites da cidade e do computador"
git push -u origin feat/novos-sprites
```

No GitHub, abra um **Pull Request** para `main`. Revise os arquivos e os testes
antes de mesclar. Para trabalho individual com prazo curto, você também pode
fazer commits pequenos diretamente em `main`.

O workflow em `.github/workflows/checks.yml` executa os testes no Windows e
gera um pacote. Em **Actions → execução concluída → Artifacts**, você pode
baixar o artefato para conferir. O artefato não cria uma Release automaticamente;
anexe o ZIP produzido a uma nova Release quando quiser publicar outra versão.

Para gerar o pacote no seu computador:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/build_windows.py
```

Ao mudar o jogo, gere novamente o executável. Ao mudar apenas HTML, CSS ou
JavaScript, basta publicar o commit para atualizar o Pages.

## Referências oficiais

- GitHub Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- Fonte de publicação: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- Criar Releases: https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository
- PyInstaller: https://pyinstaller.org/en/stable/operating-mode.html
- Flask em produção: https://flask.palletsprojects.com/en/stable/deploying/
