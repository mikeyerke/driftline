#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const chromeBinary =
  process.env.CHROME_BINARY ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl = process.env.CAPTURE_URL || "http://127.0.0.1:5173/";
const outputPath = resolve(
  process.argv[2] ||
    "submission/assets/driftline-continuous-candidate-proof.mp4",
);
const debugPort = Number(process.env.CHROME_DEBUG_PORT || "9333");
const captureRoot = await mkdtemp(join(tmpdir(), "driftline-capture-"));
const profileDir = join(captureRoot, "chrome-profile");
const framesDir = join(captureRoot, "frames");
await mkdir(profileDir, { recursive: true });
await mkdir(framesDir, { recursive: true });

const sleep = (milliseconds) =>
  new Promise((resolveSleep) => setTimeout(resolveSleep, milliseconds));

async function waitForJson(url, timeoutMs = 15_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return await response.json();
      lastError = new Error(`${url} returned ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await sleep(150);
  }
  throw lastError || new Error(`Timed out waiting for ${url}`);
}

class CdpClient {
  constructor(webSocketUrl) {
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
    this.socket = new WebSocket(webSocketUrl);
  }

  async connect() {
    await new Promise((resolveConnect, rejectConnect) => {
      this.socket.addEventListener("open", resolveConnect, { once: true });
      this.socket.addEventListener("error", rejectConnect, { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(message.error.message));
        else pending.resolve(message.result);
        return;
      }
      const callbacks = this.listeners.get(message.method) || [];
      for (const callback of callbacks) callback(message.params || {});
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolveSend, rejectSend) => {
      this.pending.set(id, { resolve: resolveSend, reject: rejectSend });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  on(method, callback) {
    const callbacks = this.listeners.get(method) || [];
    callbacks.push(callback);
    this.listeners.set(method, callbacks);
  }

  close() {
    this.socket.close();
  }
}

function quotedConcatPath(path) {
  return path.replaceAll("'", "'\\''");
}

let chrome;
let client;
let captureError;
try {
  chrome = spawn(
    chromeBinary,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--no-default-browser-check",
      `--remote-debugging-port=${debugPort}`,
      `--user-data-dir=${profileDir}`,
      "about:blank",
    ],
    { stdio: ["ignore", "ignore", "pipe"] },
  );

  const version = await waitForJson(
    `http://127.0.0.1:${debugPort}/json/version`,
  );
  if (!version.Browser?.includes("Chrome")) {
    throw new Error(`Unexpected capture browser: ${version.Browser || "unknown"}`);
  }

  const pageResponse = await fetch(
    `http://127.0.0.1:${debugPort}/json/new?${encodeURIComponent(targetUrl)}`,
    { method: "PUT" },
  );
  if (!pageResponse.ok) {
    throw new Error(`Chrome page creation returned ${pageResponse.status}`);
  }
  const page = await pageResponse.json();
  client = new CdpClient(page.webSocketDebuggerUrl);
  await client.connect();
  await client.send("Page.enable");
  await client.send("Runtime.enable");
  await client.send("Emulation.setDeviceMetricsOverride", {
    width: 1280,
    height: 720,
    deviceScaleFactor: 1,
    mobile: false,
  });

  const evaluate = async (expression, awaitPromise = true) => {
    const result = await client.send("Runtime.evaluate", {
      expression,
      awaitPromise,
      returnByValue: true,
    });
    if (result.exceptionDetails) {
      throw new Error(
        result.exceptionDetails.exception?.description ||
          result.exceptionDetails.text ||
          "Browser evaluation failed",
      );
    }
    return result.result?.value;
  };

  const waitFor = async (expression, label, timeoutMs = 12_000) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if (await evaluate(expression)) return;
      await sleep(150);
    }
    const diagnostic = await evaluate(`({
      url: location.href,
      text: document.body.innerText.slice(0, 800),
    })`);
    throw new Error(
      `Timed out waiting for ${label}: ${JSON.stringify(diagnostic)}`,
    );
  };

  const clickButton = async (label) => {
    const serialized = JSON.stringify(label);
    const clicked = await evaluate(`(() => {
      const target = [...document.querySelectorAll('button')].find(
        (node) => node.textContent.trim().includes(${serialized}),
      );
      if (!target || target.disabled) return false;
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      target.click();
      return true;
    })()`);
    if (!clicked) throw new Error(`Could not click button: ${label}`);
  };

  const clickRadio = async (label) => {
    const serialized = JSON.stringify(label);
    const clicked = await evaluate(`(() => {
      const target = [...document.querySelectorAll('[role="radio"]')].find(
        (node) => node.textContent.trim().includes(${serialized}),
      );
      if (!target) return false;
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      target.click();
      return true;
    })()`);
    if (!clicked) throw new Error(`Could not click response: ${label}`);
  };

  await waitFor(
    `document.body.innerText.includes('Run the decision workflow')`,
    "candidate overview",
  );

  const frames = [];
  let writeChain = Promise.resolve();
  client.on("Page.screencastFrame", ({ data, metadata, sessionId }) => {
    const frameNumber = frames.length;
    const framePath = join(
      framesDir,
      `frame-${String(frameNumber).padStart(5, "0")}.jpg`,
    );
    frames.push({
      path: framePath,
      timestamp: metadata?.timestamp ?? frameNumber / 10,
    });
    writeChain = writeChain
      .then(() => writeFile(framePath, Buffer.from(data, "base64")))
      .then(() => client.send("Page.screencastFrameAck", { sessionId }));
  });

  await client.send("Page.startScreencast", {
    format: "jpeg",
    quality: 90,
    maxWidth: 1280,
    maxHeight: 720,
    everyNthFrame: 1,
  });

  await sleep(1_000);
  await clickButton("Run the decision workflow");
  await waitFor(
    `document.body.innerText.toLowerCase().includes('council recommendation')`,
    "generation 1 council",
  );
  await sleep(1_200);

  await evaluate(`(() => {
    const target = [...document.querySelectorAll('summary')].find(
      (node) => node.textContent.includes('Open full evidence'),
    );
    if (!target) return false;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.click();
    return true;
  })()`);
  await sleep(1_400);

  await clickRadio("Ship to every workspace");
  await sleep(850);
  await clickRadio("Roll back globally");
  await sleep(850);
  await clickRadio("Segment the rollout");
  await sleep(1_000);

  await evaluate(`(() => {
    const input = document.querySelector('input[placeholder="Your name"]');
    if (!input) return false;
    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    input.focus();
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
      .set.call(input, 'Mike E.');
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  })()`);
  await sleep(900);
  await waitFor(
    `[...document.querySelectorAll('button')].some(
      (node) => node.textContent.includes('Approve segmented experiment') &&
        !node.disabled,
    )`,
    "enabled named-human approval",
    3_000,
  );
  await clickButton("Approve segmented experiment");
  await waitFor(
    `document.body.innerText.toLowerCase().includes('run demo measurement fallback') ||
      document.body.innerText.toLowerCase().includes('generation 2')`,
    "monitor result or truthful local fallback",
    5_000,
  );
  const alreadyReopened = await evaluate(
    `document.body.innerText.toLowerCase().includes('generation 2')`,
  );
  if (!alreadyReopened) {
    await sleep(850);
    await clickButton("Run demo measurement fallback");
  }
  await waitFor(
    `document.body.innerText.toLowerCase().includes('generation 2')`,
    "generation 2 reopen",
    8_000,
  );
  await sleep(1_600);

  await evaluate(`(() => {
    const target = [...document.querySelectorAll('[role="radio"]')].find(
      (node) => node.textContent.includes('Roll back globally'),
    );
    target?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  })()`);
  await sleep(1_300);

  const finalState = await evaluate(`(() => {
    const rollback = [...document.querySelectorAll('[role="radio"]')].find(
      (node) => node.textContent.includes('Roll back globally'),
    );
    const approver = document.querySelector('input[placeholder="Your name"]');
    return {
      generation2: document.body.innerText.toLowerCase().includes('generation 2'),
      rollbackSelected: rollback?.getAttribute('aria-checked') === 'true',
      approverCleared: !approver?.value,
      externalWritesNone: document.body.innerText.toLowerCase().includes('external writes') &&
        document.body.innerText.toLowerCase().includes('none'),
      actionRolledBack: document.body.innerText.toLowerCase().includes('rolled back'),
    };
  })()`);
  if (!Object.values(finalState).every(Boolean)) {
    throw new Error(`Candidate final-state proof failed: ${JSON.stringify(finalState)}`);
  }

  await evaluate(`scrollTo({ top: 0, behavior: 'smooth' })`);
  await sleep(1_200);
  await client.send("Page.stopScreencast");
  await writeChain;

  if (frames.length < 10) {
    throw new Error(`Capture produced only ${frames.length} frames`);
  }

  const concatLines = ["ffconcat version 1.0"];
  for (let index = 0; index < frames.length; index += 1) {
    const frame = frames[index];
    const nextFrame = frames[index + 1];
    const duration = nextFrame
      ? Math.max(0.033, Math.min(2, nextFrame.timestamp - frame.timestamp))
      : 1.2;
    concatLines.push(`file '${quotedConcatPath(frame.path)}'`);
    concatLines.push(`duration ${duration.toFixed(4)}`);
  }
  concatLines.push(
    `file '${quotedConcatPath(frames[frames.length - 1].path)}'`,
  );
  const concatPath = join(captureRoot, "frames.ffconcat");
  await writeFile(concatPath, `${concatLines.join("\n")}\n`);
  await mkdir(dirname(outputPath), { recursive: true });

  const ffmpeg = spawnSync(
    "ffmpeg",
    [
      "-hide_banner",
      "-loglevel",
      "error",
      "-y",
      "-f",
      "concat",
      "-safe",
      "0",
      "-i",
      concatPath,
      "-vf",
      "fps=30,scale=1280:720:force_original_aspect_ratio=decrease:in_range=pc:out_range=tv,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
      "-c:v",
      "libx264",
      "-preset",
      "medium",
      "-crf",
      "19",
      "-pix_fmt",
      "yuv420p",
      "-color_range",
      "tv",
      "-movflags",
      "+faststart",
      outputPath,
    ],
    { encoding: "utf8" },
  );
  if (ffmpeg.status !== 0) {
    throw new Error(ffmpeg.stderr || `ffmpeg exited ${ffmpeg.status}`);
  }

  console.log(
    JSON.stringify(
      {
        output: outputPath,
        frames: frames.length,
        finalState,
        label: "local unreleased candidate proof",
      },
      null,
      2,
    ),
  );
} catch (error) {
  captureError = error;
  throw error;
} finally {
  try {
    await client?.send("Page.stopScreencast");
  } catch {}
  client?.close();
  chrome?.kill("SIGTERM");
  await sleep(200);
  if (!process.env.KEEP_CAPTURE_FRAMES) {
    await rm(captureRoot, { recursive: true, force: true });
  } else if (captureError) {
    console.error(`Capture frames retained at ${captureRoot}`);
  }
}
