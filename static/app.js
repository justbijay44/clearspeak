const form = document.getElementById("upload-form");
const submitBtn = document.getElementById("submit-btn");
const fileInput = document.getElementById("file");
const dropzone = document.getElementById("dropzone");
const dropzoneText = document.getElementById("dropzone-text");
const statusSection = document.getElementById("status-section");
const statusText = document.getElementById("status-text");
const statusSub = document.getElementById("status-sub");
const spinner = document.getElementById("spinner");
const downloadLink = document.getElementById("download-link");
const resetBtn = document.getElementById("reset-btn");
const errorLine = document.getElementById("error-line");
const originalFrame = document.getElementById("original-frame");
const dubbedFrame = document.getElementById("dubbed-frame");
const originalVideo = document.getElementById("original-video");
const dubbedVideo = document.getElementById("dubbed-video");

const POLL_INTERVAL_MS = 3000;
let startTime = null;

// --- file selection / drag & drop feedback ---

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) {
    dropzoneText.textContent = fileInput.files[0].name;
  }
});

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);

["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);

dropzone.addEventListener("drop", (e) => {
  const files = e.dataTransfer.files;
  if (files.length) {
    fileInput.files = files;
    dropzoneText.textContent = files[0].name;
  }
});

// --- form submit ---

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  resetStatusUI();

  const domainHint = document.getElementById("domain_hint").value;
  if (!fileInput.files.length) return;

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  if (domainHint) formData.append("domain_hint", domainHint);

  submitBtn.disabled = true;
  statusSection.classList.remove("hidden");
  setStatus("Uploading...", "This may take a moment for larger files.");
  startTimer();

  try {
    const res = await fetch("/jobs", { method: "POST", body: formData });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    const { job_id } = await res.json();
    pollJob(job_id);
  } catch (err) {
    showError(err.message);
  }
});

function pollJob(jobId) {
  setStatus("Processing...", "Transcribing, generating voiceover, and rendering video.");

  const poll = async () => {
    try {
      const res = await fetch(`/jobs/${jobId}`);
      if (!res.ok) throw new Error(`Status check failed (${res.status})`);
      const job = await res.json();

      if (job.status === "complete") {
        onComplete(jobId);
      } else if (job.status === "failed") {
        showError(job.error || "Processing failed.");
      } else {
        setTimeout(poll, POLL_INTERVAL_MS);
      }
    } catch (err) {
      showError(err.message);
    }
  };

  poll();
}

function onComplete(jobId) {
  spinner.classList.add("done");
  setStatus("Done", `Completed in ${formatElapsed()}.`);
  downloadLink.href = `/jobs/${jobId}/download`;
  downloadLink.classList.remove("hidden");
  resetBtn.classList.remove("hidden");

  originalVideo.src = `/jobs/${jobId}/original`;
  dubbedVideo.src = `/jobs/${jobId}/download`;
  originalFrame.classList.add("has-src");
  dubbedFrame.classList.add("has-src");
}

function showError(message) {
  spinner.classList.add("errored");
  setStatus("Something went wrong", message);
  errorLine.classList.add("hidden"); // details already shown in status-sub
  submitBtn.disabled = false;
  resetBtn.classList.remove("hidden");
}

resetBtn.addEventListener("click", () => {
  form.reset();
  dropzoneText.textContent = "Drop a video here or ";
  const link = document.createElement("span");
  link.className = "link-text";
  link.textContent = "browse";
  dropzoneText.appendChild(link);
  statusSection.classList.add("hidden");
  originalFrame.classList.remove("has-src");
  dubbedFrame.classList.remove("has-src");
  originalVideo.removeAttribute("src");
  dubbedVideo.removeAttribute("src");
  resetStatusUI();
  submitBtn.disabled = false;
});

// --- helpers ---

function setStatus(main, sub) {
  statusText.textContent = main;
  statusSub.textContent = sub || "";
}

function resetStatusUI() {
  errorLine.classList.add("hidden");
  errorLine.textContent = "";
  downloadLink.classList.add("hidden");
  resetBtn.classList.add("hidden");
  spinner.classList.remove("done", "errored");
}

function startTimer() {
  startTime = Date.now();
}

function formatElapsed() {
  if (!startTime) return "";
  const secs = Math.round((Date.now() - startTime) / 1000);
  return secs < 60 ? `${secs}s` : `${Math.floor(secs / 60)}m ${secs % 60}s`;
}
