import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const source = fs.readFileSync(new URL("../src/client.ts", import.meta.url), "utf8");

test("artifact wrapper uses server type field", () => {
  assert.match(source, /\{ type, \.\.\.options \}/);
  assert.doesNotMatch(source, /artifact_type|args\.content/);
});

test("canonical transcription wrapper is prompt-free", () => {
  const method = source.slice(source.indexOf("async transcribe("), source.indexOf("async editVideo("));
  assert.match(method, /analysis_type: "transcribe"/);
  assert.match(method, /resource_id: resourceId/);
  assert.doesNotMatch(method, /prompt/);
  assert.doesNotMatch(method, /provider:/);
});

test("provider-backed wrappers require provider", () => {
  for (const name of ["createImage", "createVideo", "createAudio", "createMusic"]) {
    const start = source.indexOf(`async ${name}(`);
    const end = source.indexOf("Promise<Resource>", start);
    assert.match(source.slice(start, end), /provider: string/);
  }
});
