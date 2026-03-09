const resumeForm = document.getElementById("resume-form");
const resumeFileInput = document.getElementById("resume-file");
const uploadStatus = document.getElementById("upload-status");
const keywordsSection = document.getElementById("keywords-section");
const fetchJobsButton = document.getElementById("fetch-jobs-btn");
const fetchStatus = document.getElementById("fetch-status");
const jobsFetched = document.getElementById("jobs-fetched");
const jobsNew = document.getElementById("jobs-new");
const jobCards = document.getElementById("job-cards");
let currentJobs = [];

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderKeywords(keywords) {
  if (!keywords?.length) {
    keywordsSection.innerHTML = "<p>No keywords extracted yet.</p>";
    return;
  }

  keywordsSection.innerHTML = keywords
    .map((keyword) => `<span class="keyword-tag">${escapeHtml(keyword)}</span>`)
    .join("");
}

function renderJobs(jobs) {
  const nonZeroJobs = (jobs || []).filter((job) => Number(job.match_score || 0) > 0);

  if (!nonZeroJobs.length) {
    jobCards.innerHTML = "<p>No jobs found from current RSS feeds.</p>";
    return;
  }

  const orderedJobs = [...nonZeroJobs].sort((left, right) => (right.match_score || 0) - (left.match_score || 0));

  jobCards.innerHTML = orderedJobs
    .map((job) => {
      const newPill = job.is_new ? `<span class="new-pill">NEW</span>` : "";
      const summary = escapeHtml((job.summary || "").slice(0, 220));
      const published = escapeHtml(job.published || "n/a");
      const source = escapeHtml(job.source || "Unknown source");
      const title = escapeHtml(job.title || "Untitled role");
      const link = escapeHtml(job.link || "#");
      const score = Number(job.match_score || 0).toFixed(2);
      const matchedCount = Number(job.match_count || 0);
      const matchedKeywords = (job.matched_keywords || [])
        .slice(0, 8)
        .map((keyword) => `<span class="matched-tag">${escapeHtml(keyword)}</span>`)
        .join("");
      const jobId = escapeHtml(job.id || "");

      return `
        <article class="job-card">
          ${newPill}
          <p class="score-row"><span class="score-pill">Match score: ${score}%</span> <span class="score-count">Matched keywords: ${matchedCount}</span></p>
          <h3><a href="${link}" target="_blank" rel="noopener noreferrer">${title}</a></h3>
          <p class="job-meta">${source} | ${published}</p>
          <p class="job-summary">${summary}</p>
          <div class="matched-keywords">${matchedKeywords}</div>
          <div class="card-actions">
            <button type="button" class="remove-job-btn" data-job-id="${jobId}">Remove</button>
          </div>
        </article>
      `;
    })
    .join("");

  attachRemoveHandlers();
}

function updateDisplayedCounts(jobs) {
  const nonZeroJobs = (jobs || []).filter((job) => Number(job.match_score || 0) > 0);
  jobsFetched.textContent = nonZeroJobs.length;
  jobsNew.textContent = nonZeroJobs.filter((job) => job.is_new).length;
}

async function removeJob(jobId) {
  const response = await fetch("/api/jobs/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "Failed to remove job.");
  }
}

function attachRemoveHandlers() {
  const buttons = document.querySelectorAll(".remove-job-btn");
  buttons.forEach((button) => {
    button.addEventListener("click", async () => {
      const jobId = button.dataset.jobId;
      if (!jobId) {
        return;
      }

      button.disabled = true;
      button.textContent = "Removing...";

      try {
        await removeJob(jobId);
        currentJobs = currentJobs.filter((job) => job.id !== jobId);
        updateDisplayedCounts(currentJobs);
        renderJobs(currentJobs);
        fetchStatus.textContent = "Job card removed permanently. It will stay hidden in future fetches.";
      } catch (error) {
        fetchStatus.textContent = error.message;
        button.disabled = false;
        button.textContent = "Remove";
      }
    });
  });
}

async function loadExistingKeywords() {
  try {
    const response = await fetch("/api/resume/keywords");
    const payload = await response.json();
    renderKeywords(payload.keywords || []);
  } catch (error) {
    renderKeywords([]);
  }
}

resumeForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!resumeFileInput.files?.length) {
    uploadStatus.textContent = "Choose a resume file first.";
    return;
  }

  uploadStatus.textContent = "Uploading resume...";
  const data = new FormData();
  data.append("file", resumeFileInput.files[0]);

  try {
    const response = await fetch("/api/resume/upload", {
      method: "POST",
      body: data,
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Upload failed.");
    }

    uploadStatus.textContent = `Uploaded ${payload.resume_file}. Extracted ${payload.keyword_count} keywords.`;
    renderKeywords(payload.keywords || []);
  } catch (error) {
    uploadStatus.textContent = error.message;
  }
});

fetchJobsButton.addEventListener("click", async () => {
  fetchStatus.textContent = "Fetching RSS job listings...";

  try {
    const response = await fetch("/api/jobs/fetch", { method: "POST" });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Fetching job listings failed.");
    }

    currentJobs = payload.jobs || [];
    updateDisplayedCounts(currentJobs);
    fetchStatus.textContent = `Fetched ${payload.fetched_count} jobs from configured RSS feeds.`;
    renderJobs(currentJobs);
  } catch (error) {
    fetchStatus.textContent = error.message;
    currentJobs = [];
    jobsFetched.textContent = "0";
    jobsNew.textContent = "0";
    renderJobs([]);
  }
});

loadExistingKeywords();
