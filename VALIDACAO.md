# Verificação da entrega — 19/10/2026

Ambiente: Windows 10 64 bits, Python 3.14.6, pygame-ce 2.5.8,
Flask 3.1.3 e PyInstaller 6.22.3.

## Concluído

- **11 testes automatizados passaram**, cobrindo regras de tiro, combo, nível,
  precisão, foco/pausa, impactos, fim de jogo, recomeço e renderização das telas.
- Testes de API: persistência SQLite, ordenação, UUID idempotente, conflito de
  resultados, tipos inválidos, limites de corpo e origem CORS.
- Teste real de sincronização HTTP entre armazenamento do jogo e API, incluindo
  preservação das partidas quando o servidor não está disponível.
- Executável gerado no Windows e iniciado em modo de diagnóstico: saída 0,
  importações e seis telas renderizadas pelo binário empacotado.
- `node --check` passou nos dois arquivos JavaScript do site.
- Site carregado no navegador em layout estreito; navegação e atualização do
  ranking verificadas. Uma partida de teste enviada ao Flask apareceu na tabela
  por meio do JavaScript. O registro de teste não faz parte da entrega.
- Endpoint de saúde e download local responderam HTTP 200.
- Capturas do jogo revisadas para verificar textos, cenário e botões.

## Limites

Os testes gráficos do jogo usaram o driver de vídeo simulado do SDL; não
substituem uma sessão de jogo manual no computador da apresentação.
O executável não foi testado em outro computador nem assinado digitalmente.
O servidor do ranking não foi publicado na internet e nenhum repositório ou
GitHub Pages foi criado na conta do usuário. O passo a passo está no guia.

O projeto completo contém código, site, documentação e uma cópia do ZIP do jogo
em `docs/downloads`. Diretórios de build, caches e bancos de teste não entram no
arquivo de entrega. Os bancos definitivos são criados automaticamente ao executar.
