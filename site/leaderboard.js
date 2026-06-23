function pct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return (Number(value) * 100).toFixed(1) + "%";
}

async function loadLeaderboard() {
  const body = document.getElementById("leaderboard-body");
  try {
    const response = await fetch("leaderboard.json", { cache: "no-store" });
    const data = await response.json();
    const models = data.models || [];
    document.getElementById("model-count").textContent = models.length;
    document.getElementById("best-score").textContent = models.length ? pct(models[0].strict_auto_accuracy) : "--";
    if (!models.length) {
      body.innerHTML = '<tr><td colspan="10">No submissions yet.</td></tr>';
      return;
    }
    body.innerHTML = models.map(row => `
      <tr>
        <td>${row.rank}</td>
        <td>${row.model_id}</td>
        <td>${pct(row.strict_auto_accuracy)}</td>
        <td>${pct(row.resolved_accuracy)}</td>
        <td>${pct(row.coverage)}</td>
        <td>${pct(row.unknown_rate)}</td>
        <td>${pct(row.asr_disagreement_rate)}</td>
        <td>${row.correct}</td>
        <td>${row.wrong}</td>
        <td>${row.total_auto_evaluable_targets}</td>
      </tr>
    `).join("");
  } catch (error) {
    body.innerHTML = `<tr><td colspan="10">Failed to load leaderboard: ${error}</td></tr>`;
  }
}

loadLeaderboard();
