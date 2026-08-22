const chart = new Chart(document.getElementById("chart"), {
  type: "line",
  data: {
    labels: [],
    datasets: [{
      label: "temperature_c",
      data: [],
      borderColor: "#4FA8D8",
      backgroundColor: "rgba(79,168,216,0.12)",
      fill: true,
      tension: 0.25,
      pointRadius: 0,
      borderWidth: 2,
    }],
  },
  options: {
    animation: false,
    scales: {
      x: { ticks: { color: "#8CA0AF", maxTicksLimit: 6 }, grid: { color: "#24333F" } },
      y: { ticks: { color: "#8CA0AF" }, grid: { color: "#24333F" } },
    },
    plugins: { legend: { display: false } },
  },
});

function zoneInfo(score) {
  if (score < 0.3) return { cls: "zone-safe", label: "LOW" };
  if (score < 0.6) return { cls: "zone-watch", label: "WATCH" };
  return { cls: "zone-danger", label: "HIGH" };
}

function setNeedle(score) {
  const clamped = Math.max(0, Math.min(1, score ?? 0));
  const angle = clamped * 180 - 90; // 0 -> -90deg (west/safe), 1 -> +90deg (east/danger)
  document.getElementById("needle").setAttribute("transform", `rotate(${angle} 100 100)`);
}

async function refresh() {
  const latest = await (await fetch("/api/latest")).json();

  const readingsEl = document.getElementById("readings");
  const entries = Object.entries(latest.readings);
  readingsEl.innerHTML = entries.length
    ? entries.map(([key, value]) =>
        `<div class="card reading-card"><div class="label">${key}</div><div class="value">${value}</div></div>`
      ).join("")
    : `<div class="empty-state">No readings yet. Start the poller: <code>uv run python -m sensors.poller</code></div>`;

  const riskNumberEl = document.getElementById("risk-number");
  const riskZoneEl = document.getElementById("risk-zone");
  const riskCaptionEl = document.getElementById("risk-caption");

  if (latest.prediction) {
    const { risk_score, model_version, ts } = latest.prediction;
    const zone = zoneInfo(risk_score);
    riskNumberEl.textContent = risk_score.toFixed(2);
    riskZoneEl.textContent = zone.label;
    riskZoneEl.className = `risk-zone ${zone.cls}`;
    riskCaptionEl.textContent = `${model_version} — ${ts}`;
    setNeedle(risk_score);
  } else {
    riskNumberEl.textContent = "—";
    riskZoneEl.textContent = "NO MODEL YET";
    riskZoneEl.className = "risk-zone";
    riskCaptionEl.textContent = "Inference not connected — waiting on Repo A";
    setNeedle(0);
  }

  const history = await (await fetch("/api/history/temperature_c")).json();
  chart.data.labels = history.map(r => r.ts);
  chart.data.datasets[0].data = history.map(r => r.value);
  chart.update();

  document.getElementById("last-updated").textContent = new Date().toLocaleTimeString();
}

refresh();
setInterval(refresh, 10000);
