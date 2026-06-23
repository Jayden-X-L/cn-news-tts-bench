const copy = {
  en: {
    title: "Chinese News TTS Pronunciation Leaderboard",
    summary:
      "An open, target-level benchmark for raw Chinese news TTS. Every system receives the same raw text; no external frontend, LLM rewrite, SSML, or manual fix is allowed in the main track.",
    visualLabel: "Best Strict Auto Accuracy",
    visualRecords: "records",
    visualTargets: "targets",
    visualAsr: "ASR routes",
    metricModels: "TTS systems",
    metricRecords: "Public test records",
    metricTargets: "Auto-evaluable targets",
    metricBest: "Best strict score",
    backgroundKicker: "Motivation",
    backgroundTitle: "Why Chinese news TTS needs target-level evaluation",
    backgroundNote:
      "The failure is usually not a vague quality issue. A single symbol can flip the spoken meaning.",
    backgroundBody:
      "Chinese news is full of scores, hyphenated names, ranges, model numbers, unit symbols, percentages, abbreviations, and mixed-script product names. Human editors read these forms by news convention, but raw TTS systems often normalize them as ordinary text. This benchmark turns those real listening failures into explicit targets and scores whether each target was read correctly.",
    backgroundTokens: ["96-91", "苏-27", "2028-2030年", "620N·m", "3.5%", "80后", "AI", "小米SU7"],
    leaderboardKicker: "Public leaderboard",
    leaderboardTitle: "v0.1 raw model track",
    leaderboardNote:
      "Strict Acc counts unknown targets in the denominator. Higher is better; coverage shows how often the ASR ensemble can make a positive or negative target-level decision.",
    thRank: "Rank",
    thSystem: "System",
    thSource: "API source",
    thStrict: "Strict",
    thCoverage: "Coverage",
    thResolved: "Resolved",
    thCorrect: "Correct",
    thWrong: "Wrong",
    thUnknown: "Unknown",
    protocolKicker: "Evaluation protocol",
    protocolTitle: "Three-ASR target voting",
    modelKicker: "Systems",
    modelTitle: "Model and API sources",
    examplesKicker: "Examples",
    examplesTitle: "Target-level reading cases",
    examplesNote:
      "The benchmark focuses on surface forms that are common in Chinese news but easy for a raw TTS system to normalize incorrectly.",
    expected: "Expected",
    risk: "Risk",
    footer:
      "Generated TTS audio is not included in this repository. Public scores are reproducible from the fixed ASR transcripts and scoring scripts in GitHub."
  },
  zh: {
    title: "中文新闻裸 TTS 读法准确率排行榜",
    summary:
      "一个开源的 target-level 中文新闻 TTS 评测。所有系统接收同一份原始文本；主榜不允许外部规则前端、LLM 改写、SSML 或人工修正。",
    visualLabel: "最高 Strict Auto Accuracy",
    visualRecords: "public 条",
    visualTargets: "targets",
    visualAsr: "ASR 路线",
    metricModels: "TTS 系统",
    metricRecords: "Public test 条数",
    metricTargets: "可自动评估 targets",
    metricBest: "最高 strict 分数",
    backgroundKicker: "背景",
    backgroundTitle: "为什么中文新闻 TTS 需要 target-level 评测",
    backgroundNote:
      "这不是笼统的音质问题。一个符号、单位或连字符读错，就可能改变新闻含义。",
    backgroundBody:
      "中文新闻里高频出现比分、连字符、区间、型号、单位符号、百分比、英文缩写和中英数混排名称。人类编辑通常知道这些写法该怎么读，但裸 TTS 很容易按通用文本归一化读错。这个 benchmark 把这些真实收听场景里的错读点变成明确 target，逐个判断模型是否读对。",
    backgroundTokens: ["96-91", "苏-27", "2028-2030年", "620N·m", "3.5%", "80后", "AI", "小米SU7"],
    leaderboardKicker: "公开榜单",
    leaderboardTitle: "v0.1 Raw Model Track",
    leaderboardNote:
      "Strict Acc 把 unknown 计入分母。Coverage 表示三路 ASR 能明确判定 correct/wrong 的比例。",
    thRank: "排名",
    thSystem: "系统",
    thSource: "API 来源",
    thStrict: "Strict",
    thCoverage: "Coverage",
    thResolved: "Resolved",
    thCorrect: "Correct",
    thWrong: "Wrong",
    thUnknown: "Unknown",
    protocolKicker: "评估协议",
    protocolTitle: "三路 ASR target 投票",
    modelKicker: "模型信息",
    modelTitle: "模型与 API 来源",
    examplesKicker: "示例",
    examplesTitle: "Target-level 读法样例",
    examplesNote:
      "Benchmark 聚焦中文新闻中常见、但裸 TTS 容易归一化错误的表面形式。",
    expected: "期望读法",
    risk: "风险",
    footer:
      "本仓库不包含生成音频。公开分数可由固定 ASR transcript 和评分脚本复现。"
  }
};

let currentLang = localStorage.getItem("cnNewsTtsLang") || "zh";
let leaderboardData = null;
let animationFrame = null;

function pct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return (Number(value) * 100).toFixed(1) + "%";
}

function barWidth(value) {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return "0%";
  return `${Math.max(0, Math.min(100, numeric * 100)).toFixed(2)}%`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function textFor(row, key) {
  return row[`${key}_${currentLang}`] || row[`${key}_en`] || row[key] || "";
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

function renderStaticText(data) {
  const t = copy[currentLang];
  document.documentElement.lang = currentLang === "zh" ? "zh-CN" : "en";
  setText("title", t.title);
  setText("summary", t.summary);
  setText("visual-label", t.visualLabel);
  setText("visual-records-label", t.visualRecords);
  setText("visual-targets-label", t.visualTargets);
  setText("visual-asr-label", t.visualAsr);
  setText("metric-models", t.metricModels);
  setText("metric-records", t.metricRecords);
  setText("metric-targets", t.metricTargets);
  setText("metric-best", t.metricBest);
  setText("background-kicker", t.backgroundKicker);
  setText("background-title", t.backgroundTitle);
  setText("background-note", t.backgroundNote);
  setText("background-body", t.backgroundBody);
  setText("leaderboard-kicker", t.leaderboardKicker);
  setText("leaderboard-title", t.leaderboardTitle);
  setText("leaderboard-note", t.leaderboardNote);
  setText("protocol-kicker", t.protocolKicker);
  setText("protocol-title", t.protocolTitle);
  setText("model-kicker", t.modelKicker);
  setText("model-title", t.modelTitle);
  setText("examples-kicker", t.examplesKicker);
  setText("examples-title", t.examplesTitle);
  setText("examples-note", t.examplesNote);
  setText("footer-text", t.footer);
  setText("th-rank", t.thRank);
  setText("th-system", t.thSystem);
  setText("th-source", t.thSource);
  setText("th-strict", t.thStrict);
  setText("th-coverage", t.thCoverage);
  setText("th-resolved", t.thResolved);
  setText("th-correct", t.thCorrect);
  setText("th-wrong", t.thWrong);
  setText("th-unknown", t.thUnknown);

  setText("model-count", data.models.length);
  setText("record-count", data.benchmark.records);
  setText("target-count", data.benchmark.auto_evaluable_targets);
  setText("visual-records", data.benchmark.records);
  setText("visual-targets", data.benchmark.auto_evaluable_targets);
  setText("visual-asr", data.asr_ensemble.length);

  const tokenList = document.getElementById("background-tokens");
  tokenList.innerHTML = t.backgroundTokens.map((token) => `<span>${escapeHtml(token)}</span>`).join("");

  document.querySelectorAll(".lang-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === currentLang);
  });
}

function renderLeaderboard(data) {
  const body = document.getElementById("leaderboard-body");
  const best = data.models[0];
  const bestScore = pct(best.strict_auto_accuracy);
  setText("best-score", bestScore);
  setText("visual-score", bestScore);
  document.getElementById("visual-bar").style.width = barWidth(best.strict_auto_accuracy);

  body.innerHTML = data.models.map((row) => `
    <tr>
      <td class="rank">#${escapeHtml(row.rank)}</td>
      <td>
        <div class="system-name">${escapeHtml(textFor(row, "name"))}</div>
        <div class="system-sub">${escapeHtml(row.model_id)}</div>
      </td>
      <td>
        <div>${escapeHtml(textFor(row, "provider"))}</div>
        <div class="system-sub">${escapeHtml(textFor(row, "api_source"))} · ${escapeHtml(row.model)}</div>
      </td>
      <td class="score-cell">
        <div class="score-line">
          <span>${pct(row.strict_auto_accuracy)}</span>
          <div class="mini-bar"><div style="width:${barWidth(row.strict_auto_accuracy)}"></div></div>
        </div>
      </td>
      <td><span class="score-chip">${pct(row.coverage)}</span></td>
      <td><span class="score-chip">${pct(row.resolved_accuracy)}</span></td>
      <td class="count-good">${escapeHtml(row.correct)}</td>
      <td class="count-bad">${escapeHtml(row.wrong)}</td>
      <td class="count-muted">${escapeHtml(row.unknown)}</td>
    </tr>
  `).join("");
}

function renderProtocol(data) {
  const list = document.getElementById("protocol-list");
  list.innerHTML = data.asr_ensemble.map((item, index) => `
    <div class="protocol-item">
      <div class="protocol-index">${index + 1}</div>
      <div>
        <div class="protocol-name">${escapeHtml(item.name)}</div>
        <div class="protocol-source">${escapeHtml(item.id)} · ${escapeHtml(item.source)}</div>
      </div>
    </div>
  `).join("");
}

function renderModels(data) {
  const list = document.getElementById("model-list");
  list.innerHTML = data.models.map((row) => `
    <div class="model-row">
      <div>
        <strong>${escapeHtml(textFor(row, "name"))}</strong><br>
        <span>${escapeHtml(row.model_id)}</span>
      </div>
      <div>
        <strong>${escapeHtml(row.model)}</strong><br>
        <span>${escapeHtml(row.voice)}</span>
      </div>
      <div>
        <strong>${escapeHtml(row.sample_rate)} Hz</strong><br>
        <span>${escapeHtml(String(row.audio_format || "").toUpperCase())}</span>
      </div>
    </div>
  `).join("");
}

function renderExamples(data) {
  const t = copy[currentLang];
  const grid = document.getElementById("case-grid");
  grid.innerHTML = data.examples.map((item) => `
    <article class="case-card">
      <div class="case-category">${escapeHtml(item[`category_${currentLang}`] || item.category_en || item.category)}</div>
      <div class="case-input">${escapeHtml(item.input)}</div>
      <div class="case-meta">
        <div><b>${escapeHtml(t.expected)}:</b> ${escapeHtml(item[`expected_${currentLang}`] || item.expected_en)}</div>
        <div><b>${escapeHtml(t.risk)}:</b> ${escapeHtml(item[`risk_${currentLang}`] || item.risk_en)}</div>
      </div>
    </article>
  `).join("");
}

function drawSignalCanvas(data) {
  const canvas = document.getElementById("signal-canvas");
  const ctx = canvas?.getContext("2d");
  if (!canvas || !ctx || !data?.models?.length) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const scores = data.models.map((row) => Number(row.strict_auto_accuracy || 0));
  const coverage = data.models.map((row) => Number(row.coverage || 0));

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(window.innerWidth * dpr);
    canvas.height = Math.floor(window.innerHeight * dpr);
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function render(time = 0) {
    const w = window.innerWidth;
    const h = window.innerHeight;
    ctx.clearRect(0, 0, w, h);

    const grid = 42;
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(13,148,136,0.12)";
    for (let x = (time / 80) % grid; x < w; x += grid) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += grid) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    const baseY = h * 0.28;
    const amplitude = Math.max(56, h * 0.10);
    const step = Math.max(90, w / (scores.length + 1));
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(13,148,136,0.42)";
    ctx.beginPath();
    scores.forEach((score, index) => {
      const x = 54 + index * step;
      const y = baseY + (1 - score) * amplitude + Math.sin(time / 900 + index) * 8;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    coverage.forEach((value, index) => {
      const x = 54 + index * step;
      const y = baseY + (1 - value) * amplitude + 88;
      ctx.fillStyle = index === 0 ? "rgba(59,91,219,0.62)" : "rgba(245,158,11,0.42)";
      ctx.fillRect(x - 2, y - 2, 4, 4);
    });

    const scanY = (time / 32) % h;
    ctx.fillStyle = "rgba(59,91,219,0.050)";
    ctx.fillRect(0, scanY, w, 2);

    if (!reducedMotion) {
      animationFrame = requestAnimationFrame(render);
    }
  }

  resize();
  window.addEventListener("resize", resize, { passive: true });
  if (animationFrame) cancelAnimationFrame(animationFrame);
  render(0);
  if (!reducedMotion) animationFrame = requestAnimationFrame(render);
}

function renderAll() {
  if (!leaderboardData) return;
  renderStaticText(leaderboardData);
  renderLeaderboard(leaderboardData);
  renderProtocol(leaderboardData);
  renderModels(leaderboardData);
  renderExamples(leaderboardData);
  drawSignalCanvas(leaderboardData);
}

async function loadLeaderboard() {
  try {
    const response = await fetch("leaderboard.json", { cache: "no-store" });
    leaderboardData = await response.json();
    renderAll();
  } catch (error) {
    document.getElementById("leaderboard-body").innerHTML =
      `<tr><td colspan="9">Failed to load leaderboard: ${escapeHtml(error.message || error)}</td></tr>`;
  }
}

document.querySelectorAll(".lang-button").forEach((button) => {
  button.addEventListener("click", () => {
    currentLang = button.dataset.lang;
    localStorage.setItem("cnNewsTtsLang", currentLang);
    renderAll();
  });
});

loadLeaderboard();
