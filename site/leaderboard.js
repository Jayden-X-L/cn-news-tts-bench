const copy = {
  en: {
    title: "Chinese News TTS Pronunciation Leaderboard",
    summary:
      "An open, target-level benchmark for raw Chinese news TTS. Every system receives the same raw text; no external frontend, LLM rewrite, SSML, or manual fix is allowed in the main track.",
    visualLabel: "Best Strict Auto Accuracy",
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

function pct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return (Number(value) * 100).toFixed(1) + "%";
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

  const tokenList = document.getElementById("background-tokens");
  tokenList.innerHTML = t.backgroundTokens.map((token) => `<span>${token}</span>`).join("");

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
  document.getElementById("visual-bar").style.width = bestScore;

  body.innerHTML = data.models.map((row) => `
    <tr>
      <td class="rank">${row.rank}</td>
      <td>
        <div class="system-name">${textFor(row, "name")}</div>
        <div class="system-sub">${row.model_id}</div>
      </td>
      <td>
        <div>${textFor(row, "provider")}</div>
        <div class="system-sub">${textFor(row, "api_source")} · ${row.model}</div>
      </td>
      <td class="score-cell">
        <div class="score-line">
          <span>${pct(row.strict_auto_accuracy)}</span>
          <div class="mini-bar"><div style="width:${pct(row.strict_auto_accuracy)}"></div></div>
        </div>
      </td>
      <td>${pct(row.coverage)}</td>
      <td>${pct(row.resolved_accuracy)}</td>
      <td class="count-good">${row.correct}</td>
      <td class="count-bad">${row.wrong}</td>
      <td class="count-muted">${row.unknown}</td>
    </tr>
  `).join("");
}

function renderProtocol(data) {
  const list = document.getElementById("protocol-list");
  list.innerHTML = data.asr_ensemble.map((item, index) => `
    <div class="protocol-item">
      <div class="protocol-index">${index + 1}</div>
      <div>
        <div class="protocol-name">${item.name}</div>
        <div class="protocol-source">${item.id} · ${item.source}</div>
      </div>
    </div>
  `).join("");
}

function renderModels(data) {
  const list = document.getElementById("model-list");
  list.innerHTML = data.models.map((row) => `
    <div class="model-row">
      <div>
        <strong>${textFor(row, "name")}</strong><br>
        <span>${row.model_id}</span>
      </div>
      <div>
        <strong>${row.model}</strong><br>
        <span>${row.voice}</span>
      </div>
      <div>
        <strong>${row.sample_rate} Hz</strong><br>
        <span>${row.audio_format.toUpperCase()}</span>
      </div>
    </div>
  `).join("");
}

function renderExamples(data) {
  const t = copy[currentLang];
  const grid = document.getElementById("case-grid");
  grid.innerHTML = data.examples.map((item) => `
    <article class="case-card">
      <div class="case-category">${item[`category_${currentLang}`]}</div>
      <div class="case-input">${item.input}</div>
      <div class="case-meta">
        <div><b>${t.expected}:</b> ${item[`expected_${currentLang}`]}</div>
        <div><b>${t.risk}:</b> ${item[`risk_${currentLang}`]}</div>
      </div>
    </article>
  `).join("");
}

function renderAll() {
  if (!leaderboardData) return;
  renderStaticText(leaderboardData);
  renderLeaderboard(leaderboardData);
  renderProtocol(leaderboardData);
  renderModels(leaderboardData);
  renderExamples(leaderboardData);
}

async function loadLeaderboard() {
  try {
    const response = await fetch("leaderboard.json", { cache: "no-store" });
    leaderboardData = await response.json();
    renderAll();
  } catch (error) {
    document.getElementById("leaderboard-body").innerHTML =
      `<tr><td colspan="9">Failed to load leaderboard: ${error}</td></tr>`;
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
