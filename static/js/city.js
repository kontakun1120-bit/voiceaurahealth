async function loadHistory() {
  const area = document.getElementById("history");
  if (!area) return;

  const res = await fetch("/api/sessions");
  const json = await res.json();

  const sessions = json.sessions || [];

  if (sessions.length === 0) {
    area.innerHTML = `<div class="panel">まだ記録はありません。</div>`;
    return;
  }

  area.innerHTML = sessions.slice().reverse().map(s => {
    const d = new Date(s.time);
    return `
      <div class="history-card">
        <strong>${d.toLocaleString()}</strong>
        <p>Energy: ${s.energy} / Stress: ${s.stress} / Emotion: ${s.emotion}</p>
        <p>Focus: ${s.focus} / Social: ${s.social}</p>
        <small>${s.source || ""}</small>
      </div>
    `;
  }).join("");
}


async function saveDummySession() {
  const sample = {
    energy: Math.floor(50 + Math.random() * 40),
    stress: Math.floor(20 + Math.random() * 60),
    emotion: Math.floor(40 + Math.random() * 50),
    focus: Math.floor(40 + Math.random() * 50),
    social: Math.floor(40 + Math.random() * 50),
    source: "city_sample",
    note: "City test session"
  };

  await fetch("/api/session", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(sample)
  });

  loadHistory();
}


document.addEventListener("DOMContentLoaded", loadHistory);