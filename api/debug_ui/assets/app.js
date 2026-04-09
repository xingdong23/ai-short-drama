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

const stageLabelMap = {
  script: "剧本",
  character: "角色",
  video: "视频",
  voice: "语音",
  compose: "合成",
};

const stageStateLabelMap = {
  pending: "等待中",
  completed: "已完成",
  running: "执行中",
  failed: "失败",
};

const runStatusLabelMap = {
  idle: "空闲",
  running: "执行中",
  completed: "已完成",
  failed: "失败",
  ready: "就绪",
};

const pathLabelMap = {
  output: "输出根目录",
  references: "参考图目录",
  clips: "片段目录",
  audio: "音频目录",
  synced: "同步目录",
  compose: "合成目录",
};

const artifactLabelMap = {
  script: "剧本文件",
  final_video: "最终视频",
  subtitle: "字幕文件",
  bgm: "背景音乐",
  references: "参考图",
  clips: "视频片段",
  audio: "音频文件",
  synced: "同步片段",
};

const statusFieldLabelMap = {
  current_step: "当前阶段",
  theme: "主题",
  started_at: "开始时间",
  updated_at: "更新时间",
  completed_at: "完成时间",
  last_error: "最近错误",
};

const preflightCheckLabelMap = {
  pipeline_config: "流程配置",
  models_config: "模型配置",
  characters_config: "角色配置",
  ffmpeg: "FFmpeg",
  ffprobe: "FFprobe",
};

const preflightStatusLabelMap = {
  ok: "正常",
  missing: "缺失",
  error: "异常",
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

function translatePreflightDetail(detail) {
  if (!detail) {
    return "";
  }
  if (detail.startsWith("Found ")) {
    return `已找到 ${detail.slice("Found ".length)}`;
  }
  if (detail.startsWith("Missing ")) {
    return `缺少 ${detail.slice("Missing ".length)}`;
  }
  if (detail.endsWith(" not found")) {
    return `${detail.slice(0, -" not found".length)} 未找到`;
  }
  if (detail.includes(" resolved via ")) {
    const [binary, source] = detail.split(" resolved via ");
    return `${binary} 已解析，来源：${source}`;
  }
  return detail;
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
  const cleanTheme = theme.trim() || "未命名故事";
  return {
    title: `第1集：${cleanTheme}`,
    theme: cleanTheme,
    scenes: [
      {
        id: "shot_001",
        type: "establishing",
        prompt: `${cleanTheme}的城市氛围建立镜头`,
        character: null,
        dialogue: null,
        duration: 3,
        camera: "slow_pan",
      },
      {
        id: "shot_002",
        type: "dialogue",
        prompt: `小美在${cleanTheme}的情境里出现情绪波动`,
        character: "xiaomei",
        dialogue: `这段故事，就从${cleanTheme}开始。`,
        duration: 4,
        camera: "close_up",
      },
      {
        id: "shot_003",
        type: "transition",
        prompt: `把${cleanTheme}推向更强张力的转场镜头`,
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
    throw new Error("请先生成剧本，或者先载入示例，再执行手动阶段。");
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
        `<div class="path-item"><strong>${escapeHtml(pathLabelMap[label] || label)}</strong><code>${escapeHtml(value)}</code></div>`,
    )
    .join("");
}

function renderArtifacts() {
  const artifactEntries = Object.entries(state.latestArtifacts);
  if (artifactEntries.length === 0) {
    artifactsGrid.innerHTML =
      '<div class="artifact-card"><strong>等待中</strong><p>执行任意阶段后，最新产物路径会显示在这里。</p></div>';
    return;
  }

  artifactsGrid.innerHTML = artifactEntries
    .map(
      ([label, value]) =>
        `<div class="artifact-card"><strong>${escapeHtml(artifactLabelMap[label] || label)}</strong><code>${escapeHtml(
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
      return `<div class="${cssClass}"><strong>${escapeHtml(
        stageLabelMap[step] || step,
      )}</strong><span>${escapeHtml(stageStateLabelMap[label] || label)}</span></div>`;
    })
    .join("");
}

function renderStatus(run) {
  state.latestRun = run;
  const status = run?.status || "idle";
  runStatusPill.textContent = runStatusLabelMap[status] || status;
  runStatusPill.className = `status-pill ${status}`;
  const progress = run?.progress_percent ?? 0;
  runProgressLabel.textContent = `${progress}%`;
  progressBar.style.width = `${progress}%`;

  const metadata = [
    [
      "current_step",
      run?.current_step ? stageLabelMap[run.current_step] || run.current_step : "空闲",
    ],
    ["theme", run?.theme || themeInput.value.trim() || "暂无"],
    ["started_at", run?.started_at || "暂无"],
    ["updated_at", run?.updated_at || "暂无"],
    ["completed_at", run?.completed_at || "暂无"],
    ["last_error", run?.last_error || "无"],
  ];
  statusMetadata.innerHTML = metadata
    .map(
      ([label, value]) =>
        `<div><dt>${escapeHtml(statusFieldLabelMap[label] || label)}</dt><dd>${escapeHtml(value)}</dd></div>`,
    )
    .join("");

  renderStageStrip(run);
}

function renderPreflight(report) {
  const entries = Object.entries(report?.checks || {});
  if (entries.length === 0) {
    preflightChecks.innerHTML =
      '<div class="check-item"><strong>暂无数据</strong><small>点击环境检查后，这里会显示当前运行环境是否就绪。</small></div>';
    return;
  }

  preflightChecks.innerHTML = entries
    .map(([name, check]) => {
      const detail = [check.detail, check.path, check.source].filter(Boolean).join(" | ");
      return `<div class="check-item ${escapeHtml(check.status)}"><strong>${escapeHtml(
        preflightCheckLabelMap[name] || name,
      )}</strong><small>${escapeHtml(
        `${preflightStatusLabelMap[check.status] || check.status} | ${translatePreflightDetail(detail)}`,
      )}</small></div>`;
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
    throw new Error(`请求失败（${response.status}）：${text}`);
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
  logEvent("流水线状态", payload);
  return payload;
}

async function runPreflight() {
  const payload = await apiRequest("/api/v1/pipeline/preflight", {
    method: "GET",
    headers: {},
  });
  renderPreflight(payload.data);
  logEvent("环境预检查", payload);
  return payload;
}

async function withButton(button, task) {
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = "处理中...";
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
    logEvent("运行完整流水线", payload);
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
    logEvent("继续执行流水线", payload);
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
    logEvent("生成剧本", payload);
  });
});

formatScriptButton.addEventListener("click", () => {
  try {
    writeScript(readScript());
  } catch (error) {
    logEvent("剧本 JSON 错误", { error: String(error.message || error) });
  }
});

loadSampleButton.addEventListener("click", () => {
  writeScript(sampleScript(themeInput.value));
    logEvent("已载入示例剧本", state.script);
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
    logEvent("生成角色参考图", payload);
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
    logEvent("生成视频片段", payload);
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
    logEvent("生成语音与口型", payload);
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
    logEvent("执行最终合成", payload);
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
  logEvent("环境检查失败", { error: String(error.message || error) });
});
