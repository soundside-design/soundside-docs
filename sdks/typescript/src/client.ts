/**
 * Soundside MCP client — thin wrapper over Streamable HTTP transport.
 *
 * Zero dependencies: uses built-in `fetch` (Node 18+).
 */

import type {
  MCPResponse,
  Resource,
  SoundsideOptions,
  ToolResult,
} from "./types.js";

const DEFAULT_ENDPOINT = "https://mcp.soundside.ai/mcp";

export class SoundsideError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SoundsideError";
  }
}

export class Soundside {
  private readonly apiKey: string;
  private readonly endpoint: string;
  private readonly timeout: number;
  private sessionId: string | null = null;
  private msgId = 0;
  private connected = false;

  /**
   * Create a new Soundside client.
   *
   * @example
   * ```ts
   * const client = new Soundside({ apiKey: "mcp_your_key" });
   * const image = await client.createImage("A sunset over the ocean");
   * console.log(image.url);
   * ```
   */
  constructor(options: SoundsideOptions) {
    this.apiKey = options.apiKey;
    this.endpoint = options.endpoint ?? DEFAULT_ENDPOINT;
    this.timeout = options.timeout ?? 120_000;
  }

  // ── low-level ──────────────────────────────────────────

  private nextId(): string {
    return String(++this.msgId);
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
    };
    if (this.sessionId) {
      h["mcp-session-id"] = this.sessionId;
    }
    return h;
  }

  private static parseSSE(text: string): MCPResponse {
    let last: MCPResponse | null = null;
    for (const line of text.split("\n")) {
      if (line.startsWith("data:")) {
        try {
          const obj: MCPResponse = JSON.parse(line.slice(5).trim());
          if (obj.id !== undefined) return obj;
          last = obj;
        } catch {
          // skip malformed JSON
        }
      }
    }
    if (last !== null) return last;
    return JSON.parse(text);
  }

  private async post(
    method: string,
    params: Record<string, unknown> = {},
  ): Promise<MCPResponse> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const res = await fetch(this.endpoint, {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: this.nextId(),
          method,
          params,
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        throw new SoundsideError(
          `HTTP ${res.status}: ${await res.text().catch(() => "unknown")}`,
        );
      }

      const sid = res.headers.get("mcp-session-id");
      if (sid) this.sessionId = sid;

      const text = await res.text();

      // Response may be JSON directly or SSE frames
      try {
        const direct = JSON.parse(text) as MCPResponse;
        if (direct.jsonrpc) return direct;
      } catch {
        // Not direct JSON — parse as SSE
      }
      return Soundside.parseSSE(text);
    } finally {
      clearTimeout(timer);
    }
  }

  private async ensureConnected(): Promise<void> {
    if (!this.connected) await this.connect();
  }

  // ── connection ─────────────────────────────────────────

  /** Initialize the MCP session. Called automatically on first tool use. */
  async connect(): Promise<void> {
    await this.post("initialize", {
      protocolVersion: "2025-11-25",
      capabilities: {},
      clientInfo: { name: "soundside-ts-sdk", version: "0.1.0" },
    });
    this.connected = true;
  }

  // ── generic tool call ──────────────────────────────────

  /** Call any MCP tool by name and return the parsed result. */
  async callTool(
    name: string,
    args: Record<string, unknown> = {},
  ): Promise<ToolResult> {
    await this.ensureConnected();
    const rpc = await this.post("tools/call", { name, arguments: args });

    if (rpc.error) {
      throw new SoundsideError(`MCP error: ${rpc.error.message}`);
    }

    const result = rpc.result ?? {};
    if (result.isError) {
      for (const ct of result.content ?? []) {
        if (ct.type === "text" && ct.text) {
          throw new SoundsideError(`Tool error: ${ct.text}`);
        }
      }
      throw new SoundsideError("Tool error: unknown");
    }

    const structured = result.structuredContent ?? {};
    let textData: Record<string, unknown> = {};
    for (const c of result.content ?? []) {
      if (c.type === "text" && c.text) {
        try {
          textData = JSON.parse(c.text);
        } catch {
          textData = { text: c.text };
        }
        break;
      }
    }

    const merged = { ...textData, ...structured };
    const resource = merged.resource_id
      ? toResource(merged)
      : undefined;
    const text = (merged.message ?? merged.text) as string | undefined;

    return { success: (merged.success as boolean) ?? true, data: merged, resource, text };
  }

  /** Return the list of available tools and their schemas. */
  async listTools(): Promise<
    Array<{ name: string; description: string; inputSchema: object }>
  > {
    await this.ensureConnected();
    const rpc = await this.post("tools/list");
    return rpc.result?.tools ?? [];
  }

  // ── polling ────────────────────────────────────────────

  /** Poll lib_list until an async resource completes. Free (0 credits). */
  async waitForResource(
    resourceId: string,
    options?: { timeout?: number; pollInterval?: number },
  ): Promise<Resource> {
    const timeout = options?.timeout ?? 300_000;
    const pollInterval = options?.pollInterval ?? 5_000;
    const start = Date.now();

    while (Date.now() - start < timeout) {
      const result = await this.callTool("lib_list", {
        entity_type: "resources",
        resource_id: resourceId,
      });
      const items = (result.data.items ?? []) as Record<string, unknown>[];
      const item = items[0] ?? result.data;
      const status = (item.status ?? item.state ?? "") as string;

      if (status === "failed" || status === "error") {
        throw new SoundsideError(
          `Resource ${resourceId} failed: ${(item.failure_reason as string) ?? "unknown"}`,
        );
      }
      // The backend surfaces the signed GCS URL as ``url`` on completed
      // resources; older responses used ``storage_url`` — accept either.
      if (status === "completed" && (item.url || item.storage_url)) {
        return toResource(item);
      }

      await sleep(pollInterval);
    }

    throw new SoundsideError(
      `Resource ${resourceId} did not complete in ${timeout / 1000}s`,
    );
  }

  /** Fetch a resource's full details (including storage URL) via lib_list. Free. */
  async getResource(resourceId: string): Promise<Resource> {
    const result = await this.callTool("lib_list", {
      entity_type: "resources",
      resource_id: resourceId,
    });
    const items = (result.data.items ?? []) as Record<string, unknown>[];
    if (items.length === 0) {
      throw new SoundsideError(`Resource ${resourceId} not found`);
    }
    return toResource(items[0]);
  }

  private async ensureUrl(resource: Resource): Promise<Resource> {
    if (resource.url) return resource;
    return this.getResource(resource.resourceId);
  }

  // ── convenience methods ────────────────────────────────

  /** Generate an image. Returns a Resource with storageUrl populated. */
  async createImage(
    prompt: string,
    options?: { provider?: string; [key: string]: unknown },
  ): Promise<Resource> {
    const { provider, ...rest } = options ?? {};
    const args: Record<string, unknown> = { prompt, ...rest };
    if (provider) args.provider = provider;
    const result = await this.callTool("create_image", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    return this.ensureUrl(result.resource);
  }

  /** Generate a video. Async — waits for completion unless wait=false. */
  async createVideo(
    prompt: string,
    options?: {
      provider?: string;
      firstFrame?: string;
      wait?: boolean;
      waitTimeout?: number;
      [key: string]: unknown;
    },
  ): Promise<Resource> {
    const { provider, firstFrame, wait = true, waitTimeout = 600_000, ...rest } = options ?? {};
    const args: Record<string, unknown> = { prompt, ...rest };
    if (provider) args.provider = provider;
    if (firstFrame) args.first_frame = firstFrame;
    const result = await this.callTool("create_video", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    if (wait && result.resource.status !== "completed") {
      return this.waitForResource(result.resource.resourceId, { timeout: waitTimeout });
    }
    return result.resource;
  }

  /** Generate audio (TTS, sound effects, transcription). */
  async createAudio(
    prompt: string,
    options?: { provider?: string; mode?: string; [key: string]: unknown },
  ): Promise<Resource> {
    const { provider, mode = "tts", ...rest } = options ?? {};
    const args: Record<string, unknown> = { prompt, mode, ...rest };
    if (provider) args.provider = provider;
    const result = await this.callTool("create_audio", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    return this.ensureUrl(result.resource);
  }

  /** Generate a music track. Async — waits for completion unless wait=false. */
  async createMusic(
    prompt: string,
    options?: {
      lyrics?: string;
      provider?: string;
      wait?: boolean;
      waitTimeout?: number;
      [key: string]: unknown;
    },
  ): Promise<Resource> {
    const { lyrics, provider, wait = true, waitTimeout = 300_000, ...rest } = options ?? {};
    const args: Record<string, unknown> = { prompt, ...rest };
    if (lyrics) args.lyrics = lyrics;
    if (provider) args.provider = provider;
    const result = await this.callTool("create_music", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    if (wait && result.resource.status !== "completed") {
      return this.waitForResource(result.resource.resourceId, { timeout: waitTimeout });
    }
    return result.resource;
  }

  /** Generate text via LLM. */
  async createText(
    prompt: string,
    options?: { provider?: string; [key: string]: unknown },
  ): Promise<ToolResult> {
    const { provider, ...rest } = options ?? {};
    const args: Record<string, unknown> = { prompt, ...rest };
    if (provider) args.provider = provider;
    return this.callTool("create_text", args);
  }

  /** Create a business artifact (presentation, chart, document, diagram). */
  async createArtifact(
    artifactType: string,
    options?: { content?: Record<string, unknown>; [key: string]: unknown },
  ): Promise<Resource> {
    const { content, ...rest } = options ?? {};
    const args: Record<string, unknown> = { artifact_type: artifactType, ...rest };
    if (content) args.content = content;
    const result = await this.callTool("create_artifact", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    return this.ensureUrl(result.resource);
  }

  /** Apply a core editing action (trim, concat, crossfade, adjust_speed, loop, color_grade, custom, burn_subtitles). */
  async editVideo(
    resourceId: string,
    action: string,
    options?: Record<string, unknown>,
  ): Promise<Resource> {
    const args: Record<string, unknown> = {
      resource_id: resourceId,
      action,
      ...options,
    };
    const result = await this.callTool("edit_video", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    return this.ensureUrl(result.resource);
  }

  /** Compose media (add_text, overlay, split_screen). */
  async composeMedia(
    action: string,
    options?: { resourceId?: string; resourceIds?: string[]; [key: string]: unknown },
  ): Promise<Resource> {
    const { resourceId, resourceIds, ...rest } = options ?? {};
    const args: Record<string, unknown> = { action, ...rest };
    if (resourceId) args.resource_id = resourceId;
    if (resourceIds) args.resource_ids = resourceIds;
    const result = await this.callTool("compose_media", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    return this.ensureUrl(result.resource);
  }

  /** Edit audio on video (mix_audio, replace_audio, pad_audio). */
  async editAudio(
    resourceId: string,
    action: string,
    options?: Record<string, unknown>,
  ): Promise<Resource> {
    const args: Record<string, unknown> = {
      resource_id: resourceId,
      action,
      ...options,
    };
    const result = await this.callTool("edit_audio", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    return this.ensureUrl(result.resource);
  }

  /** Apply cinematic effect (ken_burns, speed_ramp, film_grain, vignette). */
  async applyEffect(
    resourceId: string,
    action: string,
    options?: Record<string, unknown>,
  ): Promise<Resource> {
    const args: Record<string, unknown> = {
      resource_id: resourceId,
      action,
      ...options,
    };
    const result = await this.callTool("apply_effect", args);
    if (!result.resource) {
      throw new SoundsideError(`No resource_id in response: ${JSON.stringify(result.data)}`);
    }
    return this.ensureUrl(result.resource);
  }

  /** Extract content from media (extract_frame, extract_frames, extract_audio). */
  async extractMedia(
    resourceId: string,
    action: string,
    options?: Record<string, unknown>,
  ): Promise<ToolResult> {
    const args: Record<string, unknown> = {
      resource_id: resourceId,
      action,
      ...options,
    };
    return this.callTool("extract_media", args);
  }

  /** Analyze a media resource (technical info or AI quality analysis). */
  async analyzeMedia(
    resourceId: string,
    options?: { analysisType?: string; [key: string]: unknown },
  ): Promise<ToolResult> {
    const { analysisType = "technical", ...rest } = options ?? {};
    return this.callTool("analyze_media", {
      resource_id: resourceId,
      analysis_type: analysisType,
      ...rest,
    });
  }

  /** List library entities (resources, projects, collections). Free. */
  async libList(
    entityType: string = "resources",
    options?: Record<string, unknown>,
  ): Promise<ToolResult> {
    return this.callTool("lib_list", { entity_type: entityType, ...options });
  }

  /** Create, update, or delete library entities. */
  async libManage(
    entityType: string,
    operation: string,
    options?: Record<string, unknown>,
  ): Promise<ToolResult> {
    return this.callTool("lib_manage", {
      entity_type: entityType,
      operation,
      ...options,
    });
  }
}

// ── helpers ────────────────────────────────────────────

function toResource(data: Record<string, unknown>): Resource {
  let rawMeta = data.metadata ?? {};
  // metadata may be a JSON string (from lib_list) or an object
  if (typeof rawMeta === "string") {
    try {
      rawMeta = JSON.parse(rawMeta);
    } catch {
      rawMeta = {};
    }
  }
  const meta = rawMeta as Record<string, unknown>;

  // Canonical field on the server is ``url``. Older responses used
  // ``storage_url`` and one legacy persistence path nested it under
  // ``metadata.storage.url`` — accept any of them.
  let url =
    (data.url as string | undefined) ?? (data.storage_url as string | undefined);
  if (!url) {
    const storage = meta.storage as Record<string, unknown> | undefined;
    url = storage?.url as string | undefined;
  }

  const status = (data.status ?? data.state ?? "completed") as string;
  const thumbnailUrl = data.thumbnail_url as string | undefined;

  return {
    resourceId: (data.resource_id ?? data.id) as string,
    status,
    state: status, // alias
    url,
    storageUrl: url, // alias (same value) for legacy consumers
    durationMs: data.duration_ms as number | undefined,
    provider: (data.provider ?? meta.provider) as string | undefined,
    mimeType: (data.mime_type ?? meta.mime_type) as string | undefined,
    thumbnailUrl,
    metadata: meta,
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
