const pipelineForm = document.getElementById("pipeline-form");
const themeInput = document.getElementById("theme-input");
const taskRootInput = document.getElementById("task-root-input");
const taskIdInput = document.getElementById("task-id-input");
const taskDirInput = document.getElementById("task-dir-input");
const startTaskButton = document.getElementById("start-task-button");
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
const workflowCards = Array.from(document.querySelectorAll("[data-step-card]"));
const runStatusPill = document.getElementById("run-status-pill");
const runProgressLabel = document.getElementById("run-progress-label");
const progressBar = document.getElementById("progress-bar");
const statusMetadata = document.getElementById("status-metadata");

const state = {
  taskRoot: "",
  task: null,
  script: null,
  latestArtifacts: {},
  latestRun: null,
};

const stageLabelMap = {
  script: "剧本",
  character: "角色",
  video: "视频",
  voice: "语音",
  compose: "合成",
  complete: "完成",
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
  ready: "任务已创建",
};

const pathLabelMap = {
  task_root: "任务根目录",
  task_dir: "工作目录",
  task_file: "任务文件",
  state_file: "状态文件",
  manifest_file: "运行清单",
  script_file: "剧本文件",
  final_video: "最终视频",
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
  task_id: "任务 ID",
  task_dir: "工作目录",
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
  const trimmedBase = String(base).replace(/\/+$/, "");
  if (!trimmedBase) {
    return segment;
  }
  return `${trimmedBase}/${segment}`;
}

function parentPath(value) {
  const normalized = String(value || "").replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  if (index <= 0) {
    return normalized || "";
  }
  return normalized.slice(0, index);
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

function deriveTaskPaths(task) {
  if (!task?.task_dir) {
    return {};
  }
  const taskDir = task.task_dir;
  return {
    task_root: state.taskRoot || parentPath(taskDir),
    task_dir: taskDir,
    task_file: task.task_file_path || joinPath(taskDir, "task.json"),
    state_file: task.state_path || joinPath(taskDir, "state.json"),
    manifest_file: task.manifest_path || joinPath(taskDir, "manifest.json"),
    script_file: task.script_path || joinPath(taskDir, "script.json"),
    final_video: task.final_video_path || joinPath(taskDir, "final.mp4"),
    references: task.directories?.references || joinPath(taskDir, "references"),
    clips: task.directories?.clips || joinPath(taskDir, "clips"),
    audio: task.directories?.audio || joinPath(taskDir, "audio"),
    synced: task.directories?.synced || joinPath(taskDir, "synced"),
    compose: task.directories?.compose || joinPath(taskDir, "compose"),
  };
}

function writeScript(script) {
  state.script = script;
  scriptEditor.value = JSON.stringify(script, null, 2);
}

function readScript() {
  if (!scriptEditor.value.trim()) {
    throw new Error("请先执行 script 阶段，或者先载入示例剧本。");
  }
  const parsed = JSON.parse(scriptEditor.value);
  state.script = parsed;
  return parsed;
}

function logEvent(label, payload) {
  responseViewer.textContent = `${label}\n\n${JSON.stringify(payload, null, 2)}`;
}

function renderTaskIdentity() {
  taskRootInput.value = state.taskRoot || "等待服务端返回";
  taskIdInput.value = state.task?.task_id || "";
  taskDirInput.value = state.task?.task_dir || "";
}

function setTask(task) {
  if (!task) {
    return;
  }
  const taskDir = task.task_dir || task.output_dir || state.task?.task_dir || "";
  const directories = task.directories || state.task?.directories || {
    references: joinPath(taskDir, "references"),
    clips: joinPath(taskDir, "clips"),
    audio: joinPath(taskDir, "audio"),
    synced: joinPath(taskDir, "synced"),
    compose: joinPath(taskDir, "compose"),
  };
  state.task = {
    ...state.task,
    ...task,
    task_dir: taskDir,
    task_file_path: task.task_file_path || state.task?.task_file_path || joinPath(taskDir, "task.json"),
    script_path: task.script_path || state.task?.script_path || joinPath(taskDir, "script.json"),
    state_path: task.state_path || state.task?.state_path || joinPath(taskDir, "state.json"),
    manifest_path: task.manifest_path || state.task?.manifest_path || joinPath(taskDir, "manifest.json"),
    final_video_path:
      task.final_video_path || state.task?.final_video_path || joinPath(taskDir, "final.mp4"),
    directories,
  };
  if (!state.taskRoot && taskDir) {
    state.taskRoot = parentPath(taskDir);
  }
  renderTaskIdentity();
  renderPathMap();
}

function clearTaskState() {
  state.task = null;
  state.latestArtifacts = {};
  state.latestRun = null;
  renderTaskIdentity();
  renderArtifacts();
  renderStatus(null);
  renderPathMap();
}

function renderPathMap() {
  if (!state.task) {
    pathMap.innerHTML =
      '<div class="path-item"><strong>等待任务</strong><code>点击“开始任务”后，系统会分配 task_id 和独立工作目录。</code></div>';
    return;
  }

  const entries = Object.entries(deriveTaskPaths(state.task));
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
      '<div class="artifact-card"><strong>等待中</strong><code>开始任务并执行任意阶段后，这里会显示当前 task_id 对应的最新产物。</code></div>';
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

function stageArtifactComplete(step) {
  if (step === "script") {
    return Boolean(state.latestArtifacts.script || scriptEditor.value.trim());
  }
  if (step === "character") {
    return Array.isArray(state.latestArtifacts.references) && state.latestArtifacts.references.length > 0;
  }
  if (step === "video") {
    return Array.isArray(state.latestArtifacts.clips) && state.latestArtifacts.clips.length > 0;
  }
  if (step === "voice") {
    return Array.isArray(state.latestArtifacts.synced) && state.latestArtifacts.synced.length > 0;
  }
  if (step === "compose") {
    return Boolean(state.latestArtifacts.final_video);
  }
  return false;
}

function workflowNote(step, status) {
  if (!state.task?.task_id) {
    return "先开始任务，拿到 task_id 和工作目录。";
  }
  if (status === "running") {
    return "当前阶段正在执行。";
  }
  if (status === "failed") {
    return "这个阶段执行失败了，先看右侧最近错误。";
  }
  if (step === "script") {
    return status === "completed" ? "剧本已写入当前任务目录。" : "第一步：生成并保存 script.json。";
  }
  if (step === "character") {
    return status === "completed" ? "参考图已落到当前任务目录。" : "第二步：围绕当前 task_id 生成参考图。";
  }
  if (step === "video") {
    return status === "completed" ? "片段已经进入当前任务的 clips/。" : "第三步：生成视频片段。";
  }
  if (step === "voice") {
    return status === "completed" ? "audio/ 和 synced/ 已经更新。" : "第四步：生成配音并做口型同步。";
  }
  return status === "completed" ? "当前任务已经产出 final.mp4。" : "第五步：合成最终视频。";
}

function renderWorkflow(run) {
  const completedFromRun = new Set(run?.completed_steps || []);
  const currentStep = run?.current_step || null;
  const isFailedRun = run?.status === "failed";
  const isRunningRun = run?.status === "running";

  for (const card of workflowCards) {
    const step = card.dataset.stepCard;
    const statusElement = card.querySelector("[data-step-status]");
    const noteElement = card.querySelector("[data-step-note]");

    let status = "pending";
    if (completedFromRun.has(step) || stageArtifactComplete(step)) {
      status = "completed";
    }
    if (isFailedRun && currentStep === step) {
      status = "failed";
    } else if (isRunningRun && currentStep === step) {
      status = "running";
    }

    card.classList.remove("pending", "completed", "running", "failed");
    card.classList.add(status);
    if (statusElement) {
      statusElement.textContent = stageStateLabelMap[status] || status;
    }
    if (noteElement) {
      noteElement.textContent = workflowNote(step, status);
    }
  }
}

function renderStatus(run) {
  state.latestRun = run;
  const status = run?.status || (state.task ? "ready" : "idle");
  runStatusPill.textContent = runStatusLabelMap[status] || status;
  runStatusPill.className = `status-pill ${status}`;
  const progress = run?.progress_percent ?? 0;
  runProgressLabel.textContent = `${progress}%`;
  progressBar.style.width = `${progress}%`;

  const metadata = [
    ["task_id", run?.task_id || state.task?.task_id || "未开始"],
    ["task_dir", run?.task_dir || state.task?.task_dir || "未分配"],
    [
      "current_step",
      run?.current_step ? `${run.current_step} / ${stageLabelMap[run.current_step] || run.current_step}` : "空闲",
    ],
    ["theme", run?.theme || state.task?.theme || themeInput.value.trim() || "暂无"],
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

  renderWorkflow(run);
}

function renderPreflight(report) {
  const entries = Object.entries(report?.checks || {});
  if (entries.length === 0) {
    preflightChecks.innerHTML =
      '<div class="check-item"><strong>暂无数据</strong><small>点击“环境检查”后，这里会显示当前运行环境是否就绪。</small></div>';
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

function updateArtifacts(payload) {
  Object.assign(state.latestArtifacts, collectArtifactValues(payload));
  renderArtifacts();
  renderWorkflow(state.latestRun);
}

function currentTaskOrThrow() {
  if (!state.task?.task_id) {
    throw new Error("请先点击“开始任务”，让系统分配 task_id。");
  }
  return state.task;
}

async function createTask() {
  const payload = await apiRequest("/api/v1/pipeline/tasks", {
    method: "POST",
    body: JSON.stringify({
      theme: themeInput.value.trim() || null,
    }),
  });
  clearTaskState();
  setTask(payload.data);
  logEvent("开始任务", payload);
  return payload.data;
}

async function ensureTask() {
  if (state.task?.task_id) {
    return state.task;
  }
  return createTask();
}

async function refreshStatus() {
  const task = currentTaskOrThrow();
  const params = new URLSearchParams({ task_id: task.task_id });
  const payload = await apiRequest(`/api/v1/pipeline/status?${params.toString()}`, {
    method: "GET",
    headers: {},
  });
  if (payload.data.task_root_dir) {
    state.taskRoot = payload.data.task_root_dir;
  }
  if (payload.data.run) {
    setTask(payload.data.run);
    updateArtifacts(payload.data.run);
    renderStatus(payload.data.run);
  } else {
    renderStatus(null);
  }
  logEvent("流水线状态", payload);
  return payload;
}

async function bootstrapStatus() {
  const payload = await apiRequest("/api/v1/pipeline/status", {
    method: "GET",
    headers: {},
  });
  state.taskRoot = payload.data.task_root_dir || "";
  renderTaskIdentity();
  renderPathMap();
  return payload;
}

async function runPreflight() {
  const payload = await apiRequest("/api/v1/pipeline/preflight", {
    method: "GET",
    headers: {},
  });
  renderPreflight(payload.data);
  logEvent("环境检查", payload);
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

startTaskButton.addEventListener("click", async () => {
  await withButton(startTaskButton, async () => {
    await createTask();
  });
});

pipelineForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await withButton(runPipelineButton, async () => {
    const task = await ensureTask();
    const payload = await apiRequest("/api/v1/pipeline/run", {
      method: "POST",
      body: JSON.stringify({
        theme: themeInput.value.trim(),
        task_id: task.task_id,
      }),
    });
    setTask(payload.data);
    updateArtifacts(payload.data);
    logEvent("运行完整流水线", payload);
    await refreshStatus();
  });
});

resumeButton.addEventListener("click", async () => {
  await withButton(resumeButton, async () => {
    const task = currentTaskOrThrow();
    const payload = await apiRequest("/api/v1/pipeline/resume", {
      method: "POST",
      body: JSON.stringify({
        task_id: task.task_id,
      }),
    });
    setTask(payload.data);
    updateArtifacts(payload.data);
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
    const task = await ensureTask();
    const payload = await apiRequest("/api/v1/script/generate", {
      method: "POST",
      body: JSON.stringify({
        theme: themeInput.value.trim(),
        task_id: task.task_id,
      }),
    });
    writeScript(payload.data.script);
    updateArtifacts(payload.data);
    logEvent("执行 script", payload);
    await refreshStatus();
  });
});

formatScriptButton.addEventListener("click", () => {
  try {
    writeScript(readScript());
    renderWorkflow(state.latestRun);
  } catch (error) {
    logEvent("剧本 JSON 错误", { error: String(error.message || error) });
  }
});

loadSampleButton.addEventListener("click", () => {
  writeScript(sampleScript(themeInput.value));
  renderWorkflow(state.latestRun);
  logEvent("已载入示例剧本", state.script);
});

characterButton.addEventListener("click", async () => {
  await withButton(characterButton, async () => {
    const task = await ensureTask();
    const payload = await apiRequest("/api/v1/character/reference", {
      method: "POST",
      body: JSON.stringify({
        task_id: task.task_id,
        script: readScript(),
      }),
    });
    updateArtifacts(payload.data);
    logEvent("执行 character", payload);
    await refreshStatus();
  });
});

videoButton.addEventListener("click", async () => {
  await withButton(videoButton, async () => {
    const task = await ensureTask();
    const payload = await apiRequest("/api/v1/video/generate", {
      method: "POST",
      body: JSON.stringify({
        task_id: task.task_id,
        script: readScript(),
      }),
    });
    updateArtifacts(payload.data);
    logEvent("执行 video", payload);
    await refreshStatus();
  });
});

voiceButton.addEventListener("click", async () => {
  await withButton(voiceButton, async () => {
    const task = await ensureTask();
    const payload = await apiRequest("/api/v1/voice/synthesize", {
      method: "POST",
      body: JSON.stringify({
        task_id: task.task_id,
        script: readScript(),
      }),
    });
    updateArtifacts(payload.data);
    logEvent("执行 voice", payload);
    await refreshStatus();
  });
});

composeButton.addEventListener("click", async () => {
  await withButton(composeButton, async () => {
    const task = await ensureTask();
    const payload = await apiRequest("/api/v1/compose/final", {
      method: "POST",
      body: JSON.stringify({
        task_id: task.task_id,
        script: readScript(),
      }),
    });
    updateArtifacts(payload.data);
    logEvent("执行 compose", payload);
    await refreshStatus();
  });
});

themeInput.addEventListener("change", () => {
  if (!scriptEditor.value.trim()) {
    writeScript(sampleScript(themeInput.value));
    renderWorkflow(state.latestRun);
  }
});

renderTaskIdentity();
renderPathMap();
renderArtifacts();
renderPreflight(null);
writeScript(sampleScript(themeInput.value));
renderStatus(null);

bootstrapStatus()
  .then(() => runPreflight())
  .catch((error) => {
    logEvent("初始化失败", { error: String(error.message || error) });
  });
