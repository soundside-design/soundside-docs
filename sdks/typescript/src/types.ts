/** A generated or managed resource in Soundside.
 *
 * The signed GCS asset URL is exposed as ``url``. ``storageUrl`` is
 * kept as an alias (same value) so older code keeps compiling.
 * A missing ``url`` means the resource is still pending — poll with
 * ``waitForResource`` or ``lib_list`` until it populates.
 */
export interface Resource {
  resourceId: string;
  /** Canonical lifecycle state: "pending" | "completed" | "failed" | ... */
  status: string;
  /** Legacy alias for ``status``; same value. */
  state: string;
  /** Signed GCS URL for the generated asset. */
  url?: string;
  /** Legacy alias for ``url``; same value. */
  storageUrl?: string;
  durationMs?: number;
  provider?: string;
  mimeType?: string;
  thumbnailUrl?: string;
  metadata: Record<string, unknown>;
}

/** Raw result from an MCP tool call. */
export interface ToolResult {
  success: boolean;
  data: Record<string, unknown>;
  /** Convenience: extract the resource if present. */
  resource?: Resource;
  /** Convenience: extract text content if present. */
  text?: string;
}

/** @internal MCP JSON-RPC response shape. */
export interface MCPResponse {
  jsonrpc: string;
  id?: string;
  result?: {
    tools?: Array<{ name: string; description: string; inputSchema: object }>;
    content?: Array<{
      type: string;
      text?: string;
      uri?: string;
      name?: string;
      mimeType?: string;
    }>;
    structuredContent?: Record<string, unknown>;
    isError?: boolean;
  };
  error?: { code: number; message: string };
  method?: string;
}

/** Options for constructing a Soundside client. */
export interface SoundsideOptions {
  apiKey: string;
  endpoint?: string;
  timeout?: number;
}
