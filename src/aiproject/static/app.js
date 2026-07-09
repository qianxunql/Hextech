    const form = document.querySelector("#form");
    const app = document.querySelector(".app");
    const input = document.querySelector("#question");
    const send = document.querySelector("#send");
    const empty = document.querySelector("#empty");
    const messages = document.querySelector("#messages");
    const globalBackButton = document.querySelector("#globalBackButton");
    const windowMinimize = document.querySelector("#windowMinimize");
    const windowMaximize = document.querySelector("#windowMaximize");
    const windowClose = document.querySelector("#windowClose");
    const sidebarToggle = document.querySelector("#sidebarToggle");
    const settingsButton = document.querySelector("#settingsButton");
    const themeButton = document.querySelector("#themeButton");
    const themeIcon = document.querySelector("#themeIcon");
    const themeLabel = document.querySelector("#themeLabel");
    const apiKeyInput = document.querySelector("#apiKeyInput");
    const saveSettings = document.querySelector("#saveSettings");
    const settingsNote = document.querySelector("#settingsNote");
    const aiTab = document.querySelector("#aiTab");
    const rosterTab = document.querySelector("#rosterTab");
    const hextechTab = document.querySelector("#hextechTab");
    const aiView = document.querySelector("#aiView");
    const rosterView = document.querySelector("#rosterView");
    const hextechView = document.querySelector("#hextechView");
    const settingsView = document.querySelector("#settingsView");
    const composerWrap = document.querySelector(".composer-wrap");
    const championGrid = document.querySelector("#championGrid");
    const rosterCount = document.querySelector("#rosterCount");
    const championSearch = document.querySelector("#championSearch");
    const hextechGrid = document.querySelector("#hextechGrid");
    const hextechCount = document.querySelector("#hextechCount");
    const hextechSearch = document.querySelector("#hextechSearch");
    const championModal = document.querySelector("#championModal");
    const modalImage = document.querySelector("#modalImage");
    const modalName = document.querySelector("#modalName");
    const modalSubtitle = document.querySelector("#modalSubtitle");
    const modalAnswer = document.querySelector("#modalAnswer");
    const hextechTooltip = document.querySelector("#hextechTooltip");

    let championItems = [];
    let hextechItems = [];
    let modalRequestId = 0;
    let activeTooltipHextechId = "";
    let activeViewName = "ai";
    let previousViewName = "ai";
    const zhCollator = new Intl.Collator("zh-Hans-CN", { numeric: true, sensitivity: "base" });

    function applyTheme(theme) {
      const isDark = theme === "dark";
      document.body.classList.toggle("dark", isDark);
      themeIcon.textContent = isDark ? "☀" : "☾";
      themeLabel.textContent = isDark ? "日间模式" : "夜间模式";
      themeButton.title = isDark ? "日间模式" : "夜间模式";
      themeButton.setAttribute("aria-label", themeButton.title);
      localStorage.setItem("hextech:theme", isDark ? "dark" : "light");
    }

    function applyNavExpanded(expanded) {
      app.classList.toggle("nav-expanded", expanded);
      document.body.classList.toggle("nav-expanded", expanded);
      sidebarToggle.title = expanded ? "收起导航" : "展开导航";
      sidebarToggle.setAttribute("aria-label", sidebarToggle.title);
      localStorage.setItem("hextech:navExpanded", expanded ? "1" : "0");
    }

    async function loadSettings() {
      try {
        const response = await fetch("/api/settings");
        const data = await response.json();
        apiKeyInput.value = "";
        apiKeyInput.placeholder = data.hasDeepseekApiKey ? "已保存，输入新 Key 可覆盖" : "sk-...";
        settingsNote.textContent = data.hasDeepseekApiKey
          ? "API Key 已配置。输入新 Key 并保存可以覆盖。"
          : "首次使用请先填写 DeepSeek API Key，否则 AI 问答无法生成回答。";
        return data;
      } catch {
        settingsNote.textContent = "读取设置失败。";
        return { hasDeepseekApiKey: false };
      }
    }

    async function saveApiKey() {
      saveSettings.disabled = true;
      settingsNote.textContent = "正在保存...";
      try {
        const response = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ deepseekApiKey: apiKeyInput.value.trim() }),
        });
        const data = await response.json();
        settingsNote.textContent = data.ok ? "已保存到 .env，AI 问答现在可以使用。" : "保存失败。";
      } catch (error) {
        settingsNote.textContent = `保存失败：${error}`;
      } finally {
        saveSettings.disabled = false;
      }
    }

    async function guideMissingApiKey() {
      const settings = await loadSettings();
      if (!settings.hasDeepseekApiKey) {
        setActiveView("settings", { skipHistory: true });
        apiKeyInput.focus();
      }
    }

    function setReady() {
      send.classList.toggle("ready", input.value.trim().length > 0);
    }

    function showMessages() {
      empty.style.display = "none";
      messages.style.display = "flex";
    }

    function addMessage(role, text) {
      showMessages();
      const node = document.createElement("div");
      node.className = `message ${role}`;
      node.textContent = text;
      messages.appendChild(node);
      messages.scrollTop = messages.scrollHeight;
      return node;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function escapeRegExp(value) {
      const slash = String.fromCharCode(92);
      const specials = new Set([slash, ".", "*", "+", "?", "^", "$", "{", "}", "(", ")", "|", "[", "]"]);
      return Array.from(String(value))
        .map((char) => specials.has(char) ? slash + char : char)
        .join("");
    }

    async function ensureHextechItems() {
      if (hextechItems.length) return hextechItems;
      const response = await fetch("/api/hextech");
      const data = await response.json();
      hextechItems = data.hextech || [];
      return hextechItems;
    }

    function linkifyHextechTerms(text) {
      const newline = String.fromCharCode(10);
      if (!hextechItems.length) {
        return escapeHtml(text).replaceAll(newline, "<br>");
      }
      const byName = new Map();
      hextechItems.forEach((item) => {
        if (item.name && item.name.length >= 2) {
          byName.set(item.name, item);
        }
      });
      const names = Array.from(byName.keys()).sort((a, b) => b.length - a.length);
      if (!names.length) {
        return escapeHtml(text).replaceAll(newline, "<br>");
      }
      const pattern = new RegExp(names.map(escapeRegExp).join("|"), "g");
      return escapeHtml(text)
        .replace(pattern, (match) => {
          const item = byName.get(match);
          if (!item) return match;
          return `<span class="hextech-term" data-hextech-id="${escapeHtml(item.id)}">${match}</span>`;
        })
        .replaceAll(newline, "<br>");
    }

    async function setModalAnswerWithHextechTerms(text) {
      try {
        await ensureHextechItems();
        modalAnswer.innerHTML = linkifyHextechTerms(text);
      } catch {
        modalAnswer.textContent = text;
      }
    }

    async function setMessageWithHextechTerms(node, text) {
      try {
        await ensureHextechItems();
        node.innerHTML = linkifyHextechTerms(text);
      } catch {
        node.textContent = text;
      }
    }

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

    function setActiveView(view, options = {}) {
      if (championModal.classList.contains("open")) {
        closeChampionModal();
      }
      const isRoster = view === "roster";
      const isHextech = view === "hextech";
      const isAi = view === "ai";
      const isSettings = view === "settings";
      if (view !== activeViewName && !options.skipHistory) {
        previousViewName = activeViewName;
      }
      activeViewName = view;
      aiTab.classList.toggle("active", isAi);
      rosterTab.classList.toggle("active", isRoster);
      hextechTab.classList.toggle("active", isHextech);
      settingsButton.classList.toggle("active", isSettings);
      aiView.classList.toggle("active", isAi);
      rosterView.classList.toggle("active", isRoster);
      hextechView.classList.toggle("active", isHextech);
      settingsView.classList.toggle("active", isSettings);
      composerWrap.style.display = isAi ? "flex" : "none";
      if (isRoster && !championGrid.dataset.loaded) {
        loadChampions();
      }
      if (isHextech && !hextechGrid.dataset.loaded) {
        loadHextechs();
      }
      if (isSettings) {
        loadSettings();
      }
    }

    function goBack() {
      if (championModal.classList.contains("open")) {
        closeChampionModal();
        return;
      }
      if (activeViewName === "settings") {
        setActiveView(previousViewName || "ai", { skipHistory: true });
        return;
      }
      if (activeViewName !== "ai") {
        setActiveView("ai");
        return;
      }
      input.focus();
    }

    function callWindowApi(action) {
      const api = window.pywebview?.api;
      if (api?.[action]) {
        api[action]();
      } else if (action === "close") {
        window.close();
      }
    }

    async function loadChampions() {
      rosterCount.textContent = "加载中";
      try {
        const response = await fetch("/api/champions");
        const data = await response.json();
        championItems = data.champions || [];
        renderChampions();
      } catch (error) {
        rosterCount.textContent = "加载失败";
        championGrid.textContent = `加载英雄名录失败：${error}`;
      }
    }

    function renderChampions() {
      championGrid.dataset.loaded = "true";
      const keyword = championSearch.value.trim().toLowerCase();
      const champions = championItems.filter((champion) => {
        const haystack = `${champion.name} ${champion.title || ""} ${champion.id}`.toLowerCase();
        return haystack.includes(keyword);
      }).sort((left, right) => zhCollator.compare(left.name, right.name));
      rosterCount.textContent = `${champions.length} / ${championItems.length} 位英雄`;
      championGrid.textContent = "";
      champions.forEach((champion) => {
        const card = document.createElement("button");
        card.className = "champion-card";
        card.type = "button";
        card.innerHTML = `
          <img src="${champion.image}" alt="${champion.name}" loading="lazy" />
          <div class="champion-name">${champion.name}</div>
          <div class="champion-title">${champion.title || champion.id}</div>
        `;
        card.addEventListener("click", () => openChampionModal(champion));
        championGrid.appendChild(card);
      });
    }

    async function loadHextechs() {
      hextechCount.textContent = "加载中";
      try {
        await ensureHextechItems();
        renderHextechs();
      } catch (error) {
        hextechCount.textContent = "加载失败";
        hextechGrid.textContent = `加载海克斯强化失败：${error}`;
      }
    }

    function renderHextechs() {
      hextechGrid.dataset.loaded = "true";
      const keyword = hextechSearch.value.trim().toLowerCase();
      const hextechs = hextechItems.filter((item) => {
        const haystack = `${item.name} ${item.tier} ${item.description} ${item.id}`.toLowerCase();
        return haystack.includes(keyword);
      });
      hextechCount.textContent = `${hextechs.length} / ${hextechItems.length} 条强化`;
      hextechGrid.textContent = "";
      hextechs.forEach((item) => {
        const card = document.createElement("button");
        card.className = "hextech-card";
        card.type = "button";
        card.dataset.hextechId = item.id;
        card.innerHTML = `
          <img src="${item.image}" alt="${item.name}" loading="lazy" />
          <div>
            <div class="hextech-name">${item.name}</div>
            <div class="hextech-tier">${item.tier}</div>
          </div>
        `;
        card.addEventListener("click", () => openHextechModal(item));
        hextechGrid.appendChild(card);
      });
    }

    async function openChampionModal(champion) {
      const requestId = ++modalRequestId;
      championModal.classList.add("open");
      championModal.setAttribute("aria-hidden", "false");
      modalAnswer.classList.remove("detail-panel");
      modalImage.src = champion.image;
      modalImage.alt = champion.name;
      modalImage.classList.remove("hextech-icon");
      modalName.textContent = champion.name;
      modalSubtitle.textContent = champion.title || champion.id;
      modalAnswer.textContent = "正在生成推荐...";

      const question = `${champion.name}适合什么海克斯强化？请给出简洁实战推荐。`;
      try {
        const answer = await askStream(question, (partial) => {
          if (requestId === modalRequestId) modalAnswer.textContent = partial;
        });
        if (requestId !== modalRequestId) return;
        await setModalAnswerWithHextechTerms(answer || "没有得到回答。");
      } catch (error) {
        if (requestId !== modalRequestId) return;
        modalAnswer.textContent = `出错了：${error}`;
      }
    }

    function closeChampionModal() {
      modalRequestId += 1;
      championModal.classList.remove("open");
      championModal.setAttribute("aria-hidden", "true");
      modalAnswer.classList.remove("detail-panel");
      modalAnswer.textContent = "";
      hideHextechTooltip();
    }

    async function openHextechModal(item) {
      const requestId = ++modalRequestId;
      championModal.classList.add("open");
      championModal.setAttribute("aria-hidden", "false");
      modalAnswer.classList.remove("detail-panel");
      modalImage.src = item.image;
      modalImage.alt = item.name;
      modalImage.classList.add("hextech-icon");
      modalName.textContent = item.name;
      modalSubtitle.textContent = item.tier;
      modalAnswer.textContent = "正在检索知识库并生成解析...";

      const question = `海克斯强化「${item.name}」（${item.tier}）适合哪些英雄或玩法？请基于知识库给出简洁实战解析：适合谁、怎么拿收益最高、哪些情况要避开。`;
      try {
        const answer = await askStream(question, (partial) => {
          if (requestId === modalRequestId) modalAnswer.textContent = partial;
        });
        if (requestId !== modalRequestId) return;
        await setModalAnswerWithHextechTerms(answer || "没有得到回答。");
      } catch (error) {
        if (requestId !== modalRequestId) return;
        modalAnswer.textContent = `出错了：${error}`;
      }
    }

    function positionHextechTooltip(event) {
      if (hextechTooltip.hidden) return;
      const gap = 14;
      const rect = hextechTooltip.getBoundingClientRect();
      const left = Math.min(event.clientX + gap, window.innerWidth - rect.width - 12);
      const top = Math.min(event.clientY + gap, window.innerHeight - rect.height - 12);
      hextechTooltip.style.left = `${Math.max(12, left)}px`;
      hextechTooltip.style.top = `${Math.max(12, top)}px`;
    }

    function showHextechTooltip(term, event) {
      const item = hextechItems.find((hextech) => hextech.id === term.dataset.hextechId);
      if (!item) return;
      if (activeTooltipHextechId !== item.id) {
        activeTooltipHextechId = item.id;
        hextechTooltip.innerHTML = `
          <div class="tooltip-head">
            <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}" />
            <div>
              <div class="tooltip-name">${escapeHtml(item.name)}</div>
              <div class="tooltip-tier">${escapeHtml(item.tier)}</div>
            </div>
          </div>
          <div class="tooltip-desc">${escapeHtml(item.description || "暂无描述")}</div>
        `;
      }
      hextechTooltip.hidden = false;
      positionHextechTooltip(event);
    }

    function hideHextechTooltip() {
      activeTooltipHextechId = "";
      hextechTooltip.hidden = true;
    }

    input.addEventListener("input", setReady);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = input.value.trim();
      if (!question || send.disabled) return;

      input.value = "";
      setReady();
      addMessage("user", question);
      const pending = addMessage("assistant", "正在检索知识库并思考...");
      send.disabled = true;

      try {
        const answer = await askStream(question, (partial) => {
          pending.textContent = partial;
          messages.scrollTop = messages.scrollHeight;
        });
        await setMessageWithHextechTerms(pending, answer || "没有得到回答。");
      } catch (error) {
        pending.textContent = `出错了：${error}`;
      } finally {
        send.disabled = false;
        input.focus();
      }
    });

    settingsButton.addEventListener("click", () => setActiveView("settings"));

    themeButton.addEventListener("click", () => {
      applyTheme(document.body.classList.contains("dark") ? "light" : "dark");
    });

    sidebarToggle.addEventListener("click", () => {
      applyNavExpanded(!app.classList.contains("nav-expanded"));
    });

    globalBackButton.addEventListener("click", goBack);
    windowMinimize.addEventListener("click", () => callWindowApi("minimize"));
    windowMaximize.addEventListener("click", () => callWindowApi("toggle_maximize"));
    windowClose.addEventListener("click", () => callWindowApi("close"));
    saveSettings.addEventListener("click", saveApiKey);
    aiTab.addEventListener("click", () => setActiveView("ai"));
    rosterTab.addEventListener("click", () => setActiveView("roster"));
    hextechTab.addEventListener("click", () => setActiveView("hextech"));
    championSearch.addEventListener("input", renderChampions);
    hextechSearch.addEventListener("input", renderHextechs);
    document.addEventListener("mouseover", (event) => {
      const term = event.target.closest?.(".hextech-term, .hextech-card");
      if (term) showHextechTooltip(term, event);
    });
    document.addEventListener("mousemove", (event) => {
      if (event.target.closest?.(".hextech-term, .hextech-card")) {
        positionHextechTooltip(event);
      }
    });
    document.addEventListener("mouseout", (event) => {
      const term = event.target.closest?.(".hextech-term, .hextech-card");
      if (term && !term.contains(event.relatedTarget)) {
        hideHextechTooltip();
      }
    });

    applyTheme(localStorage.getItem("hextech:theme") || "light");
    applyNavExpanded(localStorage.getItem("hextech:navExpanded") === "1");
    guideMissingApiKey();
    input.focus();
    setReady();
