/** A generated or managed resource in Soundside. */
export interface Resource {
  resourceId: string;
  state: string;
  storageUrl?: string;
  durationMs?: number;
  provider?: string;
  mimeType?: string;
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
