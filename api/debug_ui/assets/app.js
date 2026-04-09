const pipelineForm = document.getElementById("pipeline-form");
const themeInput = document.getElementById("theme-input");
const outputDirInput = document.getElementById("output-dir-input");
const runPipelineButton = document.getElementById("run-pipeline-button");
const resumeButton = document.getElementById("resume-button");
const statusButton = document.getElementById("status-button");
const preflightButton = document.getElementById("preflight-button");
const generateScriptButton = document.getElementById("generate-script-button");
const formatScriptButton = document.getElementById("format-script-button");
const loadSampleButton = document.getElementById("load-sample-button");
const characterButton = document.getElementById("character-button");
const videoButton = document.getElementById("video-button");
const voiceButton = document.getElementById("voice-button");
const composeButton = document.getElementById("compose-button");
const scriptEditor = document.getElementById("script-editor");
const responseViewer = document.getElementById("response-viewer");
const pathMap = document.getElementById("path-map");
const artifactsGrid = document.getElementById("artifacts-grid");
const preflightChecks = document.getElementById("preflight-checks");
const stageStrip = document.getElementById("stage-strip");
const runStatusPill = document.getElementById("run-status-pill");
const runProgressLabel = document.getElementById("run-progress-label");
const progressBar = document.getElementById("progress-bar");
const statusMetadata = document.getElementById("status-metadata");

const stageOrder = ["script", "character", "video", "voice", "compose"];

const state = {
  script: null,
  paths: null,
  latestArtifacts: {},
  latestRun: null,
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function joinPath(base, segment) {
  const trimmedBase = base.replace(/\/+$/, "");
  return `${trimmedBase}/${segment}`;
}

function derivePaths() {
  const outputDir = outputDirInput.value.trim() || "./output/debug-console-run";
  return {
    outputDir,
    referencesDir: joinPath(outputDir, "references"),
    clipsDir: joinPath(outputDir, "clips"),
    audioDir: joinPath(outputDir, "audio"),
    syncedDir: joinPath(outputDir, "synced"),
    composeDir: joinPath(outputDir, "compose"),
  };
}

function sampleScript(theme) {
  const cleanTheme = theme.trim() || "untitled story";
  return {
    title: `Episode 1: ${cleanTheme.replace(/\b\w/g, (char) => char.toUpperCase())}`,
    theme: cleanTheme,
    scenes: [
      {
        id: "shot_001",
        type: "establishing",
        prompt: `Atmospheric city establishing shot for ${cleanTheme}`,
        character: null,
        dialogue: null,
        duration: 3,
        camera: "slow_pan",
      },
      {
        id: "shot_002",
        type: "dialogue",
        prompt: `Xiaomei reacts emotionally within the theme of ${cleanTheme}`,
        character: "xiaomei",
        dialogue: `This story begins with ${cleanTheme}.`,
        duration: 4,
        camera: "close_up",
      },
      {
        id: "shot_003",
        type: "transition",
        prompt: `Transition shot that escalates tension around ${cleanTheme}`,
        character: null,
        dialogue: null,
        duration: 2,
        camera: "push_in",
      },
    ],
  };
}

function writeScript(script) {
  state.script = script;
  scriptEditor.value = JSON.stringify(script, null, 2);
}

function readScript() {
  if (!scriptEditor.value.trim()) {
    throw new Error("Generate a script or load the sample before running manual stages.");
  }
  const parsed = JSON.parse(scriptEditor.value);
  state.script = parsed;
  return parsed;
}

function logEvent(label, payload) {
  responseViewer.textContent = `${label}\n\n${JSON.stringify(payload, null, 2)}`;
}

function renderPathMap() {
  state.paths = derivePaths();
  const entries = [
    ["output", state.paths.outputDir],
    ["references", state.paths.referencesDir],
    ["clips", state.paths.clipsDir],
    ["audio", state.paths.audioDir],
    ["synced", state.paths.syncedDir],
    ["compose", state.paths.composeDir],
  ];
  pathMap.innerHTML = entries
    .map(
      ([label, value]) =>
        `<div class="path-item"><strong>${escapeHtml(label)}</strong><code>${escapeHtml(value)}</code></div>`,
    )
    .join("");
}

function renderArtifacts() {
  const artifactEntries = Object.entries(state.latestArtifacts);
  if (artifactEntries.length === 0) {
    artifactsGrid.innerHTML =
      '<div class="artifact-card"><strong>waiting</strong><p>Run a stage and the latest artifact paths will show up here.</p></div>';
    return;
  }

  artifactsGrid.innerHTML = artifactEntries
    .map(
      ([label, value]) =>
        `<div class="artifact-card"><strong>${escapeHtml(label)}</strong><code>${escapeHtml(
          Array.isArray(value) ? value.join("\n") : value,
        )}</code></div>`,
    )
    .join("");
}

function renderStageStrip(run) {
  const completed = new Set(run?.completed_steps || []);
  const currentStep = run?.current_step || "idle";
  const failed = run?.status === "failed";

  stageStrip.innerHTML = stageOrder
    .map((step) => {
      let cssClass = "stage-pill";
      let label = "pending";
      if (completed.has(step)) {
        cssClass += " completed";
        label = "completed";
      } else if (failed && currentStep === step) {
        cssClass += " failed";
        label = "failed";
      } else if (currentStep === step) {
        cssClass += " running";
        label = "running";
      }
      return `<div class="${cssClass}"><strong>${escapeHtml(step)}</strong><span>${escapeHtml(label)}</span></div>`;
    })
    .join("");
}

function renderStatus(run) {
  state.latestRun = run;
  const status = run?.status || "idle";
  runStatusPill.textContent = status;
  runStatusPill.className = `status-pill ${status}`;
  const progress = run?.progress_percent ?? 0;
  runProgressLabel.textContent = `${progress}%`;
  progressBar.style.width = `${progress}%`;

  const metadata = [
    ["current_step", run?.current_step || "idle"],
    ["theme", run?.theme || themeInput.value.trim() || "n/a"],
    ["started_at", run?.started_at || "n/a"],
    ["updated_at", run?.updated_at || "n/a"],
    ["completed_at", run?.completed_at || "n/a"],
    ["last_error", run?.last_error || "none"],
  ];
  statusMetadata.innerHTML = metadata
    .map(
      ([label, value]) =>
        `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`,
    )
    .join("");

  renderStageStrip(run);
}

function renderPreflight(report) {
  const entries = Object.entries(report?.checks || {});
  if (entries.length === 0) {
    preflightChecks.innerHTML =
      '<div class="check-item"><strong>no data</strong><small>Run preflight to inspect environment readiness.</small></div>';
    return;
  }

  preflightChecks.innerHTML = entries
    .map(([name, check]) => {
      const detail = [check.detail, check.path, check.source].filter(Boolean).join(" | ");
      return `<div class="check-item ${escapeHtml(check.status)}"><strong>${escapeHtml(
        name,
      )}</strong><small>${escapeHtml(detail)}</small></div>`;
    })
    .join("");
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed (${response.status}): ${text}`);
  }

  return response.json();
}

function collectArtifactValues(payload) {
  const artifacts = {};
  if (payload?.script_path) {
    artifacts.script = payload.script_path;
  }
  if (payload?.final_video_path) {
    artifacts.final_video = payload.final_video_path;
  }
  if (payload?.subtitle_path) {
    artifacts.subtitle = payload.subtitle_path;
  }
  if (payload?.bgm_path) {
    artifacts.bgm = payload.bgm_path;
  }
  if (payload?.reference_paths) {
    artifacts.references = Object.values(payload.reference_paths);
  }
  if (payload?.clip_paths) {
    artifacts.clips = Object.values(payload.clip_paths);
  }
  if (payload?.audio_paths) {
    artifacts.audio = Object.values(payload.audio_paths);
  }
  if (payload?.synced_paths) {
    artifacts.synced = Object.values(payload.synced_paths);
  }
  return artifacts;
}

async function refreshStatus() {
  renderPathMap();
  const params = new URLSearchParams({ output_dir: state.paths.outputDir });
  const payload = await apiRequest(`/api/v1/pipeline/status?${params.toString()}`, {
    method: "GET",
    headers: {},
  });
  renderStatus(payload.data.run);
  logEvent("Pipeline Status", payload);
  return payload;
}

async function runPreflight() {
  const payload = await apiRequest("/api/v1/pipeline/preflight", {
    method: "GET",
    headers: {},
  });
  renderPreflight(payload.data);
  logEvent("Pipeline Preflight", payload);
  return payload;
}

async function withButton(button, task) {
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = "Working...";
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.textContent = originalLabel;
  }
}

pipelineForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await withButton(runPipelineButton, async () => {
    renderPathMap();
    const payload = await apiRequest("/api/v1/pipeline/run", {
      method: "POST",
      body: JSON.stringify({
        theme: themeInput.value.trim(),
        output_dir: state.paths.outputDir,
      }),
    });
    Object.assign(state.latestArtifacts, collectArtifactValues(payload.data));
    renderArtifacts();
    logEvent("Pipeline Run", payload);
    await refreshStatus();
  });
});

resumeButton.addEventListener("click", async () => {
  await withButton(resumeButton, async () => {
    renderPathMap();
    const payload = await apiRequest("/api/v1/pipeline/resume", {
      method: "POST",
      body: JSON.stringify({
        output_dir: state.paths.outputDir,
      }),
    });
    Object.assign(state.latestArtifacts, collectArtifactValues(payload.data));
    renderArtifacts();
    logEvent("Pipeline Resume", payload);
    await refreshStatus();
  });
});

statusButton.addEventListener("click", async () => {
  await withButton(statusButton, async () => {
    await refreshStatus();
  });
});

preflightButton.addEventListener("click", async () => {
  await withButton(preflightButton, async () => {
    await runPreflight();
  });
});

generateScriptButton.addEventListener("click", async () => {
  await withButton(generateScriptButton, async () => {
    renderPathMap();
    const payload = await apiRequest("/api/v1/script/generate", {
      method: "POST",
      body: JSON.stringify({
        theme: themeInput.value.trim(),
        output_dir: state.paths.outputDir,
      }),
    });
    writeScript(payload.data.script);
    Object.assign(state.latestArtifacts, collectArtifactValues(payload.data));
    renderArtifacts();
    logEvent("Script Generate", payload);
  });
});

formatScriptButton.addEventListener("click", () => {
  try {
    writeScript(readScript());
  } catch (error) {
    logEvent("Script JSON Error", { error: String(error.message || error) });
  }
});

loadSampleButton.addEventListener("click", () => {
  writeScript(sampleScript(themeInput.value));
  logEvent("Sample Script Loaded", state.script);
});

characterButton.addEventListener("click", async () => {
  await withButton(characterButton, async () => {
    renderPathMap();
    const payload = await apiRequest("/api/v1/character/reference", {
      method: "POST",
      body: JSON.stringify({
        script: readScript(),
        output_dir: state.paths.referencesDir,
      }),
    });
    Object.assign(state.latestArtifacts, collectArtifactValues(payload.data));
    renderArtifacts();
    logEvent("Character Reference", payload);
  });
});

videoButton.addEventListener("click", async () => {
  await withButton(videoButton, async () => {
    renderPathMap();
    const payload = await apiRequest("/api/v1/video/generate", {
      method: "POST",
      body: JSON.stringify({
        script: readScript(),
        output_dir: state.paths.clipsDir,
        references_dir: state.paths.referencesDir,
      }),
    });
    Object.assign(state.latestArtifacts, collectArtifactValues(payload.data));
    renderArtifacts();
    logEvent("Video Generate", payload);
  });
});

voiceButton.addEventListener("click", async () => {
  await withButton(voiceButton, async () => {
    renderPathMap();
    const payload = await apiRequest("/api/v1/voice/synthesize", {
      method: "POST",
      body: JSON.stringify({
        script: readScript(),
        clips_dir: state.paths.clipsDir,
        output_dir: state.paths.outputDir,
      }),
    });
    Object.assign(state.latestArtifacts, collectArtifactValues(payload.data));
    renderArtifacts();
    logEvent("Voice Synthesize", payload);
  });
});

composeButton.addEventListener("click", async () => {
  await withButton(composeButton, async () => {
    renderPathMap();
    const clipsDir =
      Array.isArray(state.latestArtifacts.synced) && state.latestArtifacts.synced.length > 0
        ? state.paths.syncedDir
        : state.paths.clipsDir;
    const payload = await apiRequest("/api/v1/compose/final", {
      method: "POST",
      body: JSON.stringify({
        script: readScript(),
        clips_dir: clipsDir,
        output_dir: state.paths.outputDir,
      }),
    });
    Object.assign(state.latestArtifacts, collectArtifactValues(payload.data));
    renderArtifacts();
    logEvent("Compose Final", payload);
    await refreshStatus();
  });
});

outputDirInput.addEventListener("input", renderPathMap);
themeInput.addEventListener("change", () => {
  if (!scriptEditor.value.trim()) {
    writeScript(sampleScript(themeInput.value));
  }
});

renderPathMap();
renderArtifacts();
renderPreflight(null);
renderStatus(null);
writeScript(sampleScript(themeInput.value));
runPreflight().catch((error) => {
  logEvent("Preflight Error", { error: String(error.message || error) });
});
