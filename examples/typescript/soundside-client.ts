/**
 * Soundside MCP Client — TypeScript SDK
 *
 * Production-grade client for Soundside's MCP endpoint with async polling,
 * error handling, and pipeline support.
 *
 * Requirements: npm install axios
 * Usage: npx tsx soundside-client.ts <API_KEY>
 *    or: SOUNDSIDE_API_KEY=mcp_... npx tsx soundside-client.ts
 */

import axios, { AxiosInstance, AxiosResponse } from "axios";

interface MCPResult {
  jsonrpc: string;
  id?: string;
  result?: {
    tools?: Array<{ name: string; description: string; inputSchema: object }>;
    content?: Array<{ type: string; text?: string; uri?: string; name?: string; mimeType?: string }>;
    structuredContent?: Record<string, unknown>;
    isError?: boolean;
  };
  error?: { code: number; message: string };
  method?: string; // notification frames have 'method' but no 'id'
}

interface ResourceItem {
  id?: string;
  resource_id?: string;
  status?: string;
  /** Legacy alias for status (older responses). */
  state?: string;
  /** Signed GCS URL (canonical). */
  url?: string;
  /** Legacy alias for url. */
  storage_url?: string;
  failure_reason?: string;
  [key: string]: unknown;
}

class SoundsideClient {
  private client: AxiosInstance;
  private sessionId: string | null = null;
  private msgId = 0;

  constructor(
    private apiKey: string,
    private endpoint: string = "https://mcp.soundside.ai/mcp"
  ) {
    this.client = axios.create({
      baseURL: endpoint,
      timeout: 120_000,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
    });
  }

  private nextId(): string {
    return String(++this.msgId);
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
    };
    if (this.sessionId) {
      h["mcp-session-id"] = this.sessionId;
    }
    return h;
  }

  private parseSSE(data: string | object): MCPResult {
    if (typeof data !== "string") return data as MCPResult;

    // Server sends multiple SSE frames: notifications (with 'method') then
    // the actual JSON-RPC response (with 'id'). Find the response frame.
    let lastData: MCPResult | null = null;
    for (const line of data.split("\n")) {
      if (line.startsWith("data:")) {
        try {
          const obj: MCPResult = JSON.parse(line.slice(5).trim());
          // JSON-RPC responses have 'id'; notifications have 'method' only
          if (obj.id !== undefined) {
            return obj;
          }
          lastData = obj; // keep as fallback
        } catch {
          // skip malformed JSON
        }
      }
    }
    if (lastData !== null) {
      return lastData;
    }
    return JSON.parse(data);
  }

  private extractToolResult(rpc: MCPResult): Record<string, unknown> {
    if (rpc.error) return { error: rpc.error };

    // Check for tool-level errors (isError=true in MCP result)
    if (rpc.result?.isError) {
      const content = rpc.result?.content ?? [];
      for (const c of content) {
        if (c.type === "text" && c.text) {
          throw new Error(`Tool error: ${c.text}`);
        }
      }
      throw new Error("Tool error: unknown error");
    }

    // Prefer structuredContent (MCP 2025-11-25 format)
    if (rpc.result?.structuredContent) {
      const sc = rpc.result.structuredContent;
      // FastMCP wraps returns in a 'result' key — unwrap if needed
      if (sc.result !== undefined && Object.keys(sc).length === 1) {
        return sc.result as Record<string, unknown>;
      }
      return sc;
    }

    // Fall back to content blocks
    const content = rpc.result?.content ?? [];
    let parsed: Record<string, unknown> = {};

    // Extract text content
    for (const c of content) {
      if (c.type === "text" && c.text) {
        try {
          parsed = JSON.parse(c.text);
        } catch {
          parsed = { text: c.text };
        }
        break;
      }
    }

    // Extract resource_link content blocks (MCP 2025-11-25)
    const resourceLinks = content
      .filter((c) => c.type === "resource_link")
      .map((c) => ({ uri: c.uri, name: c.name, mimeType: c.mimeType }));
    if (resourceLinks.length > 0) {
      parsed._resourceLinks = resourceLinks;
    }

    return Object.keys(parsed).length > 0
      ? parsed
      : (rpc as unknown as Record<string, unknown>);
  }

  async connect(): Promise<void> {
    const { data, headers }: AxiosResponse = await this.client.post(
      "",
      {
        jsonrpc: "2.0",
        id: this.nextId(),
        method: "initialize",
        params: {
          protocolVersion: "2025-11-25",
          capabilities: {},
          clientInfo: { name: "soundside-ts-sdk", version: "1.1" },
        },
      },
      { headers: this.headers() }
    );
    this.sessionId = headers["mcp-session-id"] ?? null;
    console.log(
      `✅ Connected (session: ${this.sessionId?.slice(0, 16)}...)`
    );
  }

  async listTools(): Promise<
    Array<{ name: string; description: string }>
  > {
    const { data } = await this.client.post(
      "",
      {
        jsonrpc: "2.0",
        id: this.nextId(),
        method: "tools/list",
        params: {},
      },
      { headers: this.headers() }
    );
    const result = this.parseSSE(data);
    return result.result?.tools ?? [];
  }

  async callTool(
    name: string,
    args: Record<string, unknown>,
    timeout?: number
  ): Promise<Record<string, unknown>> {
    const { data } = await this.client.post(
      "",
      {
        jsonrpc: "2.0",
        id: this.nextId(),
        method: "tools/call",
        params: { name, arguments: args },
      },
      {
        headers: this.headers(),
        timeout: timeout ?? 120_000,
      }
    );
    const result = this.parseSSE(data);
    return this.extractToolResult(result);
  }

  /**
   * Poll until an async resource completes.
   *
   * Checks lib_list every `pollIntervalMs` until:
   * - status="completed" AND url is present → returns the resource
   * - status="failed" or "error" → throws Error
   * - timeout exceeded → throws Error
   *
   * lib_list calls are free (zero credits). The signed GCS asset URL
   * arrives on the item as ``url``; older responses used ``storage_url``.
   * Both are accepted.
   */
  async waitForResource(
    resourceId: string,
    timeoutMs: number = 300_000,
    pollIntervalMs: number = 5_000
  ): Promise<ResourceItem> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const result = await this.callTool("lib_list", {
        entity_type: "resources",
        resource_id: resourceId,
      });

      const items = (result.items ?? []) as ResourceItem[];
      const item: ResourceItem = items[0] ?? (result as ResourceItem);
      const status = item.status ?? item.state ?? "";

      if (status === "failed" || status === "error") {
        throw new Error(
          `Resource ${resourceId} failed: ${item.failure_reason ?? "unknown"}`
        );
      }

      if (status === "completed" && (item.url || item.storage_url)) {
        return item;
      }

      await new Promise((r) => setTimeout(r, pollIntervalMs));
    }

    throw new Error(
      `Resource ${resourceId} did not complete in ${timeoutMs / 1000}s`
    );
  }

  /**
   * Call a tool, then poll until the resource completes.
   *
   * Convenience wrapper for async tools (create_video, create_music, etc.)
   * that combines callTool() + waitForResource().
   */
  async callToolAndWait(
    name: string,
    args: Record<string, unknown>,
    timeoutMs: number = 300_000,
    pollIntervalMs: number = 5_000,
    callTimeoutMs?: number
  ): Promise<Record<string, unknown>> {
    const result = await this.callTool(name, args, callTimeoutMs);
    const resourceId = result.resource_id as string | undefined;

    if (!resourceId) {
      // Sync tool — no resource_id to poll
      return result;
    }

    const status = (result.status as string) ?? (result.state as string) ?? "";
    const assetUrl = (result.url as string) ?? (result.storage_url as string);
    if (status === "completed" && assetUrl) {
      // Already complete
      return result;
    }

    // Async — poll until done
    return await this.waitForResource(resourceId, timeoutMs, pollIntervalMs);
  }
}

// --- Main ---

async function main() {
  const apiKey =
    process.argv[2] ?? process.env.SOUNDSIDE_API_KEY;
  if (!apiKey) {
    console.error("Usage: npx tsx soundside-client.ts <API_KEY>");
    console.error(
      "   or: SOUNDSIDE_API_KEY=mcp_... npx tsx soundside-client.ts"
    );
    process.exit(1);
  }

  const client = new SoundsideClient(apiKey);

  // 1. Connect
  await client.connect();

  // 2. List tools
  const tools = await client.listTools();
  console.log(`\n📋 Available tools (${tools.length}):`);
  for (const t of tools) {
    console.log(`  • ${t.name}: ${(t.description ?? "").slice(0, 60)}`);
  }

  // 3. Generate an image (sync — returns immediately)
  console.log("\n🎨 Generating image (vertex)...");
  const t0 = Date.now();
  const imageResult = await client.callTool("create_image", {
    prompt: "A vibrant sunset over a calm ocean, photorealistic",
    provider: "vertex",
  });
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`  Resource ID: ${imageResult.resource_id ?? "N/A"}`);
  console.log(`  Time: ${elapsed}s`);
  const imageUrl = (imageResult.url ?? imageResult.storage_url) as string | undefined;
  if (imageUrl) {
    console.log(`  URL: ${imageUrl.slice(0, 80)}...`);
  }

  // 4. Analyze it
  if (imageResult.resource_id) {
    console.log("\n🔍 Analyzing image...");
    const analysis = await client.callTool("analyze_media", {
      resource_id: imageResult.resource_id,
    });
    const meta = (analysis.metadata ?? analysis) as Record<string, unknown>;
    console.log(`  Type: ${meta.mime_type ?? "N/A"}`);
    const img = meta.image as Record<string, unknown> | undefined;
    if (img) {
      console.log(`  Dimensions: ${img.width}×${img.height}`);
    }
  }

  // 5. Generate text
  console.log("\n📝 Generating text (vertex)...");
  const textResult = await client.callTool("create_text", {
    prompt: "Write a haiku about AI agents creating art",
    provider: "vertex",
  });
  console.log(
    `  ${String(textResult.text ?? JSON.stringify(textResult)).slice(0, 200)}`
  );

  // 6. Demo: callToolAndWait (generates video and polls until complete)
  if (imageResult.resource_id) {
    console.log("\n🎬 Generating video with callToolAndWait (minimax)...");
    console.log("   This calls create_video then automatically polls until complete.");
    const vt0 = Date.now();
    try {
      const video = await client.callToolAndWait(
        "create_video",
        {
          prompt: "Gentle waves lapping at a golden shore at sunset",
          provider: "minimax",
          first_frame: imageResult.resource_id,
        },
        600_000 // 10 min timeout for video
      );
      const velapsed = ((Date.now() - vt0) / 1000).toFixed(1);
      console.log(`  ✅ Video complete in ${velapsed}s`);
      console.log(`  Resource ID: ${video.id ?? video.resource_id ?? "N/A"}`);
      const videoUrl = (video.url ?? video.storage_url) as string | undefined;
      if (videoUrl) {
        console.log(`  URL: ${videoUrl.slice(0, 80)}...`);
      }
    } catch (err) {
      console.log(`  ⚠️  Video generation failed: ${err}`);
    }
  }
}

main().catch(console.error);
