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
const finalScreenshotPath = process.env.CAPTURE_FINAL_SCREENSHOT
  ? resolve(process.env.CAPTURE_FINAL_SCREENSHOT)
  : null;
const captureWidth = Number(process.env.CAPTURE_WIDTH || "1280");
const captureHeight = Number(process.env.CAPTURE_HEIGHT || "720");
const captureWaitMs = Number(process.env.CAPTURE_WAIT_MS || "12000");
const captureExpectAction = process.env.CAPTURE_EXPECT_ACTION !== "false";
const expectedReleaseSha = process.env.CAPTURE_EXPECT_RELEASE_SHA || null;
const expectedBuildId = process.env.CAPTURE_EXPECT_BUILD_ID || null;
if (
  !Number.isInteger(captureWidth) ||
  !Number.isInteger(captureHeight) ||
  captureWidth < 320 ||
  captureHeight < 320
) {
  throw new Error(`Invalid capture viewport: ${captureWidth}x${captureHeight}`);
}
if (!Number.isFinite(captureWaitMs) || captureWaitMs < 1_000) {
  throw new Error(`Invalid capture wait: ${captureWaitMs}ms`);
}
const debugPort = Number(process.env.CHROME_DEBUG_PORT || "9333");
const captureRoot = await mkdtemp(join(tmpdir(), "driftline-capture-"));
const profileDir = join(captureRoot, "chrome-profile");
const framesDir = join(captureRoot, "frames");
await mkdir(profileDir, { recursive: true });
await mkdir(framesDir, { recursive: true });

const sleep = (milliseconds) =>
  new Promise((resolveSleep) => setTimeout(resolveSleep, milliseconds));

let releaseIdentity = null;
if (expectedReleaseSha || expectedBuildId) {
  const healthUrl = new URL("/health", targetUrl);
  const response = await fetch(healthUrl);
  if (!response.ok) {
    throw new Error(`Capture health preflight returned ${response.status}`);
  }
  releaseIdentity = await response.json();
  if (
    expectedReleaseSha &&
    releaseIdentity.release_sha !== expectedReleaseSha
  ) {
    throw new Error(
      `Capture release mismatch: /health reports ${releaseIdentity.release_sha}; ` +
        `expected ${expectedReleaseSha}`,
    );
  }
  if (expectedBuildId && releaseIdentity.build_id !== expectedBuildId) {
    throw new Error(
      `Capture build mismatch: /health reports ${releaseIdentity.build_id}; ` +
        `expected ${expectedBuildId}`,
    );
  }
}

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
    width: captureWidth,
    height: captureHeight,
    deviceScaleFactor: 1,
    mobile: captureWidth <= 500,
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

  const waitFor = async (expression, label, timeoutMs = captureWaitMs) => {
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

  await evaluate(`(() => {
    const style = document.createElement('style');
    style.textContent = \`
      #driftline-capture-pointer {
        position: fixed;
        top: 0;
        left: 0;
        z-index: 2147483647;
        width: 18px;
        height: 18px;
        border: 3px solid #ffffff;
        border-radius: 999px;
        background: #155eef;
        box-shadow: 0 2px 8px rgba(5, 18, 48, .42);
        pointer-events: none;
        transform: translate(-50%, -50%);
        transition: width 90ms ease, height 90ms ease, background 90ms ease;
      }
      #driftline-capture-pointer.pressed {
        width: 14px;
        height: 14px;
        background: #0b3ea8;
      }
      .driftline-capture-pulse {
        position: fixed;
        z-index: 2147483646;
        width: 18px;
        height: 18px;
        border: 3px solid #155eef;
        border-radius: 999px;
        pointer-events: none;
        transform: translate(-50%, -50%);
        animation: driftline-capture-pulse 520ms ease-out forwards;
      }
      @keyframes driftline-capture-pulse {
        from { opacity: .9; width: 18px; height: 18px; }
        to { opacity: 0; width: 52px; height: 52px; }
      }
    \`;
    document.head.append(style);
    const pointer = document.createElement('div');
    pointer.id = 'driftline-capture-pointer';
    pointer.setAttribute('aria-hidden', 'true');
    document.body.append(pointer);
    window.__driftlineCapturePointer = (x, y, pressed = false) => {
      pointer.style.left = x + 'px';
      pointer.style.top = y + 'px';
      pointer.classList.toggle('pressed', pressed);
    };
    window.__driftlineCapturePulse = (x, y) => {
      const pulse = document.createElement('div');
      pulse.className = 'driftline-capture-pulse';
      pulse.style.left = x + 'px';
      pulse.style.top = y + 'px';
      document.body.append(pulse);
      setTimeout(() => pulse.remove(), 600);
    };
    window.__driftlineCapturePointer(${captureWidth - 90}, ${captureHeight - 50});
    return true;
  })()`);

  let pointerX = captureWidth - 90;
  let pointerY = captureHeight - 50;
  let pointerClicks = 0;

  const movePointer = async (x, y) => {
    const steps = 9;
    const startX = pointerX;
    const startY = pointerY;
    for (let step = 1; step <= steps; step += 1) {
      const progress = step / steps;
      pointerX = startX + (x - startX) * progress;
      pointerY = startY + (y - startY) * progress;
      await client.send("Input.dispatchMouseEvent", {
        type: "mouseMoved",
        x: pointerX,
        y: pointerY,
      });
      await evaluate(
        `window.__driftlineCapturePointer?.(${pointerX}, ${pointerY}, false)`,
      );
      await sleep(24);
    }
  };

  const clickAt = async ({ x, y }) => {
    await movePointer(x, y);
    await evaluate(`window.__driftlineCapturePointer?.(${x}, ${y}, true)`);
    await client.send("Input.dispatchMouseEvent", {
      type: "mousePressed",
      x,
      y,
      button: "left",
      clickCount: 1,
    });
    await sleep(90);
    await client.send("Input.dispatchMouseEvent", {
      type: "mouseReleased",
      x,
      y,
      button: "left",
      clickCount: 1,
    });
    pointerClicks += 1;
    await evaluate(`(() => {
      window.__driftlineCapturePointer?.(${x}, ${y}, false);
      window.__driftlineCapturePulse?.(${x}, ${y});
    })()`);
    await sleep(180);
  };

  const targetCenter = async (targetExpression, label) => {
    const found = await evaluate(`(() => {
      const target = ${targetExpression};
      if (!target || target.disabled) return false;
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return true;
    })()`);
    if (!found) throw new Error(`Could not find interactive target: ${label}`);
    await sleep(520);
    const center = await evaluate(`(() => {
      const target = ${targetExpression};
      if (!target || target.disabled) return null;
      const bounds = target.getBoundingClientRect();
      return {
        x: bounds.left + bounds.width / 2,
        y: bounds.top + bounds.height / 2,
      };
    })()`);
    if (!center) throw new Error(`Could not locate interactive target: ${label}`);
    return center;
  };

  const clickButton = async (label) => {
    const serialized = JSON.stringify(label);
    const center = await targetCenter(
      `[...document.querySelectorAll('button')].find(
        (node) => node.textContent.trim().includes(${serialized}),
      )`,
      `button ${label}`,
    );
    await clickAt(center);
  };

  const clickRadio = async (label) => {
    const serialized = JSON.stringify(label);
    const center = await targetCenter(
      `[...document.querySelectorAll('[role="radio"]')].find(
        (node) => node.textContent.trim().includes(${serialized}),
      )`,
      `response ${label}`,
    );
    await clickAt(center);
  };

  const clickSummary = async (label) => {
    const serialized = JSON.stringify(label);
    const center = await targetCenter(
      `[...document.querySelectorAll('summary')].find(
        (node) => node.textContent.includes(${serialized}),
      )`,
      `summary ${label}`,
    );
    await clickAt(center);
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
    maxWidth: captureWidth,
    maxHeight: captureHeight,
    everyNthFrame: 1,
  });

  await sleep(1_000);
  await clickButton("Run the decision workflow");
  await waitFor(
    `document.body.innerText.toLowerCase().includes('council recommendation')`,
    "generation 1 council",
  );
  await sleep(1_200);

  await clickSummary("Open full evidence");
  await sleep(1_400);

  await clickRadio("Ship to every workspace");
  await sleep(850);
  await clickRadio("Roll back globally");
  await sleep(850);
  await clickRadio("Segment the rollout");
  await sleep(1_000);

  const approverCenter = await targetCenter(
    `document.querySelector('input[placeholder="Your name"]')`,
    "human approver input",
  );
  await clickAt(approverCenter);
  await client.send("Input.insertText", { text: "Mike E." });
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
  const requiredFinalState = captureExpectAction
    ? finalState
    : {
        generation2: finalState.generation2,
        rollbackSelected: finalState.rollbackSelected,
        approverCleared: finalState.approverCleared,
      };
  if (!Object.values(requiredFinalState).every(Boolean)) {
    const mode = captureExpectAction ? "candidate action" : "current release";
    throw new Error(
      `${mode} final-state proof failed: ${JSON.stringify(finalState)}`,
    );
  }

  if (finalScreenshotPath) {
    const screenshotReady = await evaluate(`(() => {
      const target = document.querySelector('.learning-receipt');
      if (!target) return false;
      target.scrollIntoView({ behavior: 'instant', block: 'start' });
      scrollBy({ top: -160, behavior: 'instant' });
      document.querySelector('#driftline-capture-pointer')?.remove();
      document.querySelectorAll('.driftline-capture-pulse').forEach((node) => node.remove());
      return true;
    })()`);
    if (!screenshotReady) {
      throw new Error("Could not prepare the generation-2 learning receipt screenshot");
    }
    await sleep(500);
    const screenshot = await client.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false,
    });
    const screenshotBytes = Buffer.from(screenshot.data, "base64");
    const pngSignature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
    if (!screenshotBytes.subarray(0, 8).equals(pngSignature)) {
      throw new Error("Final-state screenshot is not a PNG");
    }
    const screenshotWidth = screenshotBytes.readUInt32BE(16);
    const screenshotHeight = screenshotBytes.readUInt32BE(20);
    if (screenshotWidth !== captureWidth || screenshotHeight !== captureHeight) {
      throw new Error(
        `Final-state screenshot is ${screenshotWidth}x${screenshotHeight}; ` +
          `expected ${captureWidth}x${captureHeight}`,
      );
    }
    await mkdir(dirname(finalScreenshotPath), { recursive: true });
    await writeFile(finalScreenshotPath, screenshotBytes);
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
      `fps=30,scale=${captureWidth}:${captureHeight}:force_original_aspect_ratio=decrease:in_range=pc:out_range=tv,pad=${captureWidth}:${captureHeight}:(ow-iw)/2:(oh-ih)/2,format=yuv420p`,
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
        pointerClicks,
        finalState,
        finalScreenshot: finalScreenshotPath,
        viewport: `${captureWidth}x${captureHeight}`,
        releaseIdentity,
        label: captureExpectAction
          ? "local unreleased candidate proof"
          : "current-release decision-loop proof",
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
