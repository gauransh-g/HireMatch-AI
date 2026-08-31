/* ============================================================
   HireMatch AI — Dashboard Script
   ============================================================ */

const API = "";

// ---- State ----
let activeJobId = null;
let activeJobData = null;
let pendingFiles = [];
let candidateMap = {}; // candidate_id -> match result row
let screenedCandidateIds = [];

// ---- Selectors ----
const $ = id => document.getElementById(id);

// ---- On Load ----
document.addEventListener("DOMContentLoaded", () => {
  loadMetrics();
  loadJobs();

  // Job form
  $("job-form").addEventListener("submit", e => { e.preventDefault(); saveJob(); });
  $("btn-parse-jd").addEventListener("click", parseJD);
  $("btn-trigger-new-job").addEventListener("click", () => {
    $("job-form").reset();
    $("jd-preview-container").classList.add("hidden");
    activeJobId = null;
    activeJobData = null;
    $("active-job-select").value = "";
    $("sourcing-panel").classList.add("hidden");
    $("leaderboard-list").innerHTML = `<p>Fill in the job form and save to begin screening.</p>`;
    $("detail-panel").classList.add("hidden");
    $("comparison-panel").classList.add("hidden");
  });

  // Job selector
  $("active-job-select").addEventListener("change", e => {
    const id = parseInt(e.target.value);
    if (!id) return;
    selectJob(id);
  });

  // Upload zone
  const zone = $("drop-zone");
  const fileInput = $("file-input");
  zone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => handleFiles(fileInput.files));
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    handleFiles(e.dataTransfer.files);
  });

  $("btn-run-screening").addEventListener("click", runScreening);
  $("btn-download-report").addEventListener("click", downloadReport);
});

// ---- Metrics ----
async function loadMetrics() {
  try {
    const res = await fetch(`${API}/v1/match/metrics`);
    if (!res.ok) return;
    const m = await res.json();
    $("metric-jobs").textContent = m.total_jobs ?? 0;
    $("metric-candidates").textContent = m.total_candidates ?? 0;
    $("metric-avg-match").textContent = m.avg_match_score != null ? `${m.avg_match_score}%` : "—";
    $("metric-top-cands").textContent = m.top_candidates ?? 0;
  } catch (_) {}
}

// ---- Jobs ----
async function loadJobs() {
  try {
    const res = await fetch(`${API}/v1/jobs`);
    if (!res.ok) return;
    const jobs = await res.json();
    const sel = $("active-job-select");
    const currentVal = sel.value;
    sel.innerHTML = `<option value="">Select a job...</option>`;
    jobs.forEach(j => {
      const opt = document.createElement("option");
      opt.value = j.id;
      opt.textContent = j.title;
      sel.appendChild(opt);
    });
    if (currentVal) sel.value = currentVal;
  } catch (_) {}
}

async function parseJD() {
  const title = $("job-title").value.trim();
  const description = $("job-description").value.trim();
  if (!title || !description) { showStatus("upload-status", "Enter a title and description first.", "error"); return; }
  try {
    $("btn-parse-jd").textContent = "Analyzing...";
    $("btn-parse-jd").disabled = true;
    const res = await fetch(`${API}/v1/jobs/analyze-jd`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, must_have_skills: [], nice_to_have_skills: [] })
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderJDPreview(data);
  } catch (e) {
    showStatus("upload-status", `Analysis failed: ${e.message}`, "error");
  } finally {
    $("btn-parse-jd").textContent = "Analyze JD";
    $("btn-parse-jd").disabled = false;
  }
}

function renderJDPreview(data) {
  $("preview-jd-exp").textContent = data.experience ?? 0;
  $("preview-jd-role").textContent = data.role ?? "—";
  renderTags("preview-jd-required", data.required_skills, "tag-required");
  renderTags("preview-jd-preferred", data.preferred_skills, "tag");
  $("jd-preview-container").classList.remove("hidden");
}

async function saveJob() {
  const title = $("job-title").value.trim();
  const description = $("job-description").value.trim();
  const role_family = $("role-family").value;
  if (!title || !description) return;

  const btn = $("btn-save-job");
  btn.textContent = "Saving...";
  btn.disabled = true;

  try {
    const res = await fetch(`${API}/v1/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, role_family, must_have_skills: [], nice_to_have_skills: [] })
    });
    if (!res.ok) throw new Error(await res.text());
    const job = await res.json();
    await loadJobs();
    $("active-job-select").value = job.id;
    selectJob(job.id, job);
    loadMetrics();
  } catch (e) {
    alert(`Failed to save job: ${e.message}`);
  } finally {
    btn.textContent = "Save Job";
    btn.disabled = false;
  }
}

async function selectJob(jobId, jobData = null) {
  activeJobId = jobId;
  if (jobData) {
    activeJobData = jobData;
  } else {
    try {
      const res = await fetch(`${API}/v1/jobs/${jobId}`);
      activeJobData = res.ok ? await res.json() : null;
    } catch (_) {}
  }

  $("sourcing-panel").classList.remove("hidden");
  pendingFiles = [];
  $("candidate-count-badge").textContent = 0;
  renderPreviewList([]);
  $("btn-run-screening").classList.add("hidden");

  // Load existing results if any
  loadLeaderboard(jobId);
  populateCompareDropdowns([]);
  $("comparison-panel").classList.remove("hidden");
}

// ---- File Upload & Preview ----
async function handleFiles(files) {
  if (!activeJobId) {
    showStatus("upload-status", "Save a job first before uploading resumes.", "error");
    return;
  }
  pendingFiles = [...files];
  showStatus("upload-status", `Parsing ${pendingFiles.length} file(s)...`, "info");
  $("upload-status").classList.remove("hidden");

  try {
    const form = new FormData();
    pendingFiles.forEach(f => form.append("resumes", f));
    const res = await fetch(`${API}/v1/resumes/preview`, { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderPreviewList(data.previews);
    $("candidate-count-badge").textContent = data.previews.filter(p => p.status === "ok").length;
    $("btn-run-screening").classList.remove("hidden");
    showStatus("upload-status", `${data.previews.length} resume(s) parsed.`, "success");
  } catch (e) {
    showStatus("upload-status", `Parse error: ${e.message}`, "error");
  }
}

function renderPreviewList(previews) {
  const list = $("preview-list");
  if (!previews.length) {
    list.innerHTML = `<p>No resumes loaded yet.</p>`;
    list.className = "candidate-list-preview empty-note";
    return;
  }
  list.className = "candidate-list-preview";
  list.innerHTML = previews.map(p => `
    <div class="preview-item">
      <div>
        <div class="preview-item-name">${p.candidate_name || p.file_name}</div>
        <div class="preview-item-meta">${p.years_experience != null ? p.years_experience + " yrs exp" : ""} ${p.status === "error" ? "· " + p.message : ""}</div>
      </div>
      <span class="preview-status ${p.status}">${p.status === "ok" ? "Parsed" : "Error"}</span>
    </div>
  `).join("");
}

// ---- Screening ----
async function runScreening() {
  if (!activeJobId || !pendingFiles.length) return;
  const btn = $("btn-run-screening");
  btn.textContent = "Running...";
  btn.disabled = true;
  showStatus("upload-status", "Uploading and screening candidates...", "info");

  try {
    // Upload to DB
    const form = new FormData();
    form.append("job_id", activeJobId);
    pendingFiles.forEach(f => form.append("resumes", f));
    const uploadRes = await fetch(`${API}/v1/resumes/upload`, { method: "POST", body: form });
    if (!uploadRes.ok) throw new Error(await uploadRes.text());
    const candidates = await uploadRes.json();
    const cand_ids = candidates.map(c => c.id);

    // Screen
    const screenRes = await fetch(`${API}/v1/match/screen`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: activeJobId, candidate_ids: cand_ids })
    });
    if (!screenRes.ok) throw new Error(await screenRes.text());
    const results = await screenRes.json();

    loadLeaderboard(activeJobId, results);
    populateCompareDropdowns(results);
    showStatus("upload-status", `Screening complete. ${results.length} candidate(s) ranked.`, "success");
    loadMetrics();
  } catch (e) {
    showStatus("upload-status", `Screening error: ${e.message}`, "error");
  } finally {
    btn.textContent = "Run Screening";
    btn.disabled = false;
  }
}

// ---- Leaderboard ----
async function loadLeaderboard(jobId, results = null) {
  if (!results) {
    try {
      const res = await fetch(`${API}/v1/match/job/${jobId}`);
      results = res.ok ? await res.json() : [];
    } catch (_) { results = []; }
  }

  const container = $("leaderboard-list");
  if (!results.length) {
    container.innerHTML = `<p class="empty-note">No candidates screened yet for this job.</p>`;
    $("leaderboard-subtitle").textContent = "Upload and screen resumes to generate rankings.";
    return;
  }

  $("leaderboard-subtitle").textContent = `${results.length} candidate(s) ranked`;
  candidateMap = {};
  results.forEach(r => { candidateMap[r.candidate_id] = r; });
  screenedCandidateIds = results.map(r => r.candidate_id);

  results.sort((a, b) => b.overall_score - a.overall_score);

  container.innerHTML = `
    <table class="leaderboard-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Candidate</th>
          <th>Overall</th>
          <th>Match</th>
        </tr>
      </thead>
      <tbody>
        ${results.map((r, i) => {
          const label = matchLabel(r.overall_score);
          return `
            <tr class="result-row" data-cid="${r.candidate_id}" onclick="openDetail(${r.candidate_id})">
              <td><span class="rank-num">${i + 1}</span></td>
              <td>
                <div class="cand-name">${r.candidate_name || "Candidate " + r.candidate_id}</div>
                <div class="cand-exp">${r.experience_years != null ? r.experience_years + " yrs exp" : ""}</div>
              </td>
              <td>
                <span class="score-chip">${r.overall_score}%</span>
                <div class="mini-bar"><div class="mini-bar-fill" style="width:${r.overall_score}%"></div></div>
              </td>
              <td><span class="match-badge ${label.cls}">${label.text}</span></td>
            </tr>
          `;
        }).join("")}
      </tbody>
    </table>
  `;
}

function matchLabel(score) {
  if (score >= 80) return { text: "Strong", cls: "match-strong" };
  if (score >= 60) return { text: "Moderate", cls: "match-moderate" };
  return { text: "Weak", cls: "match-weak" };
}

// ---- Detail Panel ----
let activeDetailCandidateId = null;

function openDetail(candidateId) {
  const r = candidateMap[candidateId];
  if (!r) return;
  activeDetailCandidateId = candidateId;

  $("detail-name").textContent = r.candidate_name || "Candidate";
  $("detail-meta").textContent = `${r.experience_years != null ? r.experience_years + " yrs experience" : ""}`;
  $("detail-overall-score").textContent = `${r.overall_score}%`;

  setBar("fill-skill", "val-skill", r.skill_score);
  setBar("fill-exp", "val-exp", r.experience_score);
  setBar("fill-resp", "val-resp", r.responsibility_score);
  setBar("fill-edu", "val-edu", r.education_score);
  setBar("fill-sem", "val-sem", r.semantic_score);

  $("detail-summary").textContent = r.summary || "—";

  renderList("detail-strengths", r.strengths || []);
  renderList("detail-concerns", r.concerns || []);
  renderTags("detail-matched-skills", r.matched_skills || [], "tag-matched");
  renderTags("detail-missing-skills", r.missing_skills || [], "tag-missing");

  $("detail-panel").classList.remove("hidden");
  $("detail-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

function setBar(fillId, valId, value) {
  const pct = Math.min(100, Math.max(0, value ?? 0));
  $(fillId).style.width = `${pct}%`;
  const el = $(fillId);
  if (pct >= 80) el.style.background = "var(--green)";
  else if (pct >= 60) el.style.background = "var(--amber)";
  else el.style.background = "var(--red)";
  $(valId).textContent = `${pct}%`;
}

// ---- Report Download ----
async function downloadReport() {
  if (!activeDetailCandidateId) return;
  const btn = $("btn-download-report");
  btn.textContent = "Generating...";
  btn.disabled = true;
  try {
    const res = await fetch(`${API}/v1/match/report/${activeDetailCandidateId}`);
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `HireMatch_Report_${activeDetailCandidateId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert(`Report generation failed: ${e.message}`);
  } finally {
    btn.textContent = "Download Report";
    btn.disabled = false;
  }
}

// ---- Compare ----
function populateCompareDropdowns(results) {
  const optHtml = results.map(r =>
    `<option value="${r.candidate_id}">${r.candidate_name || "Candidate " + r.candidate_id}</option>`
  ).join("");
  $("compare-select-a").innerHTML = optHtml;
  $("compare-select-b").innerHTML = optHtml;

  if (results.length >= 2) {
    $("compare-select-b").selectedIndex = 1;
  }

  [$("compare-select-a"), $("compare-select-b")].forEach(sel => {
    sel.addEventListener("change", renderComparison);
  });

  if (results.length >= 2) renderComparison();
}

async function renderComparison() {
  const aId = $("compare-select-a").value;
  const bId = $("compare-select-b").value;
  if (!aId || !bId || aId === bId) return;

  try {
    const res = await fetch(`${API}/v1/match/compare/${aId}/${bId}`);
    if (!res.ok) return;
    const data = await res.json();
    const ca = data.candidate_a;
    const cb = data.candidate_b;

    const metrics = [
      { label: "Overall Score", key: "overall_score", unit: "%" },
      { label: "Skill Match", key: "skill_score", unit: "%" },
      { label: "Experience", key: "experience_score", unit: "%" },
      { label: "Responsibility", key: "responsibility_score", unit: "%" },
      { label: "Education", key: "education_score", unit: "%" },
      { label: "Semantic", key: "semantic_score", unit: "%" },
    ];

    const col = (data, title) => `
      <div class="compare-col">
        <h3>${data.candidate_name || title}</h3>
        ${metrics.map(m => `
          <div class="compare-metric">
            <span class="compare-metric-label">${m.label}</span>
            <span class="compare-metric-val">${data[m.key] ?? "—"}${m.unit}</span>
          </div>
        `).join("")}
        <div style="margin-top:10px">
          <div class="skills-label" style="margin-bottom:6px">Matched Skills</div>
          <div class="tag-list">${(data.matched_skills || []).slice(0, 6).map(s => `<span class="tag tag-matched">${s}</span>`).join("")}</div>
        </div>
      </div>`;

    $("comparison-output").innerHTML = col(ca, "Candidate A") + col(cb, "Candidate B");
  } catch (_) {}
}

// ---- Helpers ----
function renderTags(containerId, items, tagClass = "tag") {
  const el = $(containerId);
  if (!el) return;
  el.innerHTML = (items || []).map(s => `<span class="tag ${tagClass}">${s}</span>`).join("") || `<span class="tag">—</span>`;
}

function renderList(id, items) {
  const el = $(id);
  if (!el) return;
  el.innerHTML = (items || []).map(t => `<li>${t}</li>`).join("") || "<li>None noted.</li>";
}

function showStatus(id, msg, type = "info") {
  const el = $(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `status-msg ${type}`;
  el.classList.remove("hidden");
}
