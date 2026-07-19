const overlay = document.querySelector("#overlay");
const toggle = document.querySelector("#toggle");
const statusNode = document.querySelector("#status");
const matchesNode = document.querySelector("#matches");
const answerNode = document.querySelector("#answer");

let expanded = false;
let loading = false;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function callWindowApi(action) {
  const api = window.poroNative?.api;
  if (api?.[action]) {
    api[action]();
  }
}

function expand() {
  expanded = true;
  overlay.classList.remove("is-collapsed");
  callWindowApi("expand");
}

function collapse(force = false) {
  if (loading && !force) return;
  expanded = false;
  overlay.classList.add("is-collapsed");
  callWindowApi("collapse");
}

window.overlayCollapse = collapse;

async function askStream(question, onChunk) {
  const response = await fetch("/api/ask-stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok || !response.body) {
    const fallback = await response.text();
    throw new Error(fallback || `HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let answer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    if (!chunk) continue;
    answer += chunk;
    onChunk(answer);
  }
  const tail = decoder.decode();
  if (tail) {
    answer += tail;
    onChunk(answer);
  }
  return answer;
}

function renderMatches(matches) {
  matchesNode.textContent = "";
  matches.forEach((match) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.innerHTML = `${escapeHtml(match.name)} <span>${escapeHtml(match.score)}</span>`;
    matchesNode.appendChild(chip);
  });
}

async function recognizeAndAsk() {
  if (loading) return;
  loading = true;
  toggle.disabled = true;
  expand();
  matchesNode.textContent = "";
  answerNode.textContent = "正在读取截图和当前英雄...";
  statusNode.textContent = "截图识别中...";

  try {
    const response = await fetch("/api/recognize-screenshot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ champion: "", ocrText: "" }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }

    renderMatches(data.matches || []);
    const names = (data.matches || []).map((item) => item.name).join("、") || "未识别到可靠海克斯";
    const championText = data.champion?.name ? `当前英雄：${data.champion.name}。` : "未从选人阶段读到英雄。";
    statusNode.textContent = `${championText} 识别：${names}`;
    answerNode.textContent = "正在生成推荐...";

    const answer = await askStream(data.question, (partial) => {
      answerNode.textContent = partial;
      answerNode.scrollTop = answerNode.scrollHeight;
    });
    answerNode.textContent = answer || "没有得到回答。";
  } catch (error) {
    statusNode.textContent = "识别失败";
    answerNode.textContent = `失败：${error}\n\n可以回到主 Poro 窗口，在「局内截图识别」里手动输入海克斯名称。`;
  } finally {
    loading = false;
    toggle.disabled = false;
  }
}

toggle.addEventListener("click", () => {
  if (loading) return;
  if (expanded) {
    collapse();
    return;
  }
  recognizeAndAsk();
});
