"use strict";
const config = window.WORDS_ATACK_CONFIG || {};
const localHost = ["127.0.0.1", "localhost", "[::1]"].includes(location.hostname);
const apiBase = (config.apiBase || (localHost ? location.origin : "")).replace(/\/$/, "");
const body = document.querySelector("#ranking-body");
const status = document.querySelector("#ranking-status");
const refresh = document.querySelector("#refresh-ranking");
const format = new Intl.NumberFormat("pt-BR");

function safeLink(value) {
  try {
    const url = new URL(value, location.href);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch { return null; }
}
const download = safeLink(config.downloadUrl || "downloads/WordsAtack-Windows.zip");
if (download) document.querySelector("#download-link").href = download;
if (config.repositoryUrl && !config.repositoryUrl.includes("SEU-USUARIO")) {
  const repository = safeLink(config.repositoryUrl);
  if (repository) document.querySelector("#repository-link").href = repository;
} else {
  document.querySelector("#repository-link").textContent = "Repositório em preparação";
  document.querySelector("#repository-link").removeAttribute("href");
}

function empty(message) {
  body.replaceChildren();
  const row = document.createElement("tr");
  row.className = "empty";
  const cell = document.createElement("td");
  cell.colSpan = 5;
  cell.textContent = message;
  row.append(cell);
  body.append(row);
}

async function loadRanking() {
  if (!apiBase) {
    status.textContent = "Ranking online ainda não conectado nesta prévia.";
    empty("O jogo já registra suas partidas no ranking local. O ranking compartilhado aparecerá quando o servidor for publicado.");
    return;
  }
  refresh.disabled = true;
  refresh.textContent = "Conectando...";
  status.textContent = "Buscando partidas no servidor...";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(`${apiBase}/api/leaderboard?limit=10`, { signal: controller.signal, cache: "no-store" });
    if (!response.ok) throw new Error("Servidor indisponível");
    const data = await response.json();
    if (!Array.isArray(data.scores)) throw new Error("Resposta inválida");
    body.replaceChildren();
    if (!data.scores.length) empty("Nenhuma partida enviada ainda. Seja o primeiro defensor da cidade.");
    for (const [index, score] of data.scores.slice(0, 10).entries()) {
      const row = document.createElement("tr");
      const values = [String(index + 1).padStart(2, "0"), score.nickname, format.format(score.score), `${format.format(score.accuracy)}%`, score.level];
      for (const value of values) {
        const cell = document.createElement("td");
        // Nicknames são texto, nunca HTML executável.
        cell.textContent = String(value);
        row.append(cell);
      }
      body.append(row);
    }
    status.textContent = `Registro atualizado às ${new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}.`;
  } catch {
    status.textContent = "Sem conexão com o servidor de ranking neste momento.";
    empty("O download e o jogo offline continuam disponíveis. Tente atualizar o ranking mais tarde.");
  } finally {
    clearTimeout(timeout);
    refresh.disabled = false;
    refresh.textContent = "Atualizar ↻";
  }
}
refresh.addEventListener("click", loadRanking);
loadRanking();
