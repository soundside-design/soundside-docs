/**
 * Soundside MCP Client — TypeScript Example
 * 
 * Demonstrates connecting to Soundside's MCP endpoint and generating media.
 * Requires: npm install axios
 */

import axios, { AxiosInstance } from 'axios';

interface MCPResult {
  jsonrpc: string;
  id: string;
  result?: {
    tools?: Array<{ name: string; description: string; inputSchema: object }>;
    content?: Array<{ type: string; text?: string }>;
  };
  error?: { code: number; message: string };
}

class SoundsideClient {
  private client: AxiosInstance;
  private sessionId: string | null = null;
  private msgId = 0;

  constructor(
    private apiKey: string,
    private endpoint: string = 'https://mcp.soundside.ai/mcp'
  ) {
    this.client = axios.create({
      baseURL: endpoint,
      timeout: 120_000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
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
      h['mcp-session-id'] = this.sessionId;
    }
    return h;
  }

  private parseSSE(data: string): MCPResult {
    for (const line of data.split('\n')) {
      if (line.startsWith('data:')) {
        return JSON.parse(line.slice(5));
      }
    }
    return JSON.parse(data);
  }

  async connect(): Promise<void> {
    const { data, headers } = await this.client.post(
      '',
      {
        jsonrpc: '2.0',
        id: this.nextId(),
        method: 'initialize',
        params: {
          protocolVersion: '2024-11-05',
          capabilities: {},
          clientInfo: { name: 'soundside-ts', version: '1.0' },
        },
      },
      { headers: this.headers() }
    );
    this.sessionId = headers['mcp-session-id'] ?? null;
    console.log(`✅ Connected (session: ${this.sessionId?.slice(0, 16)}...)`);
  }

  async listTools(): Promise<Array<{ name: string; description: string }>> {
    const { data } = await this.client.post(
      '',
      { jsonrpc: '2.0', id: this.nextId(), method: 'tools/list', params: {} },
      { headers: this.headers() }
    );
    const result = this.parseSSE(data);
    return result.result?.tools ?? [];
  }

  async callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
    const { data } = await this.client.post(
      '',
      {
        jsonrpc: '2.0',
        id: this.nextId(),
        method: 'tools/call',
        params: { name, arguments: args },
      },
      { headers: this.headers() }
    );
    const result = this.parseSSE(data);
    const content = result.result?.content ?? [];
    for (const c of content) {
      if (c.type === 'text' && c.text) {
        try {
          return JSON.parse(c.text);
        } catch {
          return { text: c.text };
        }
      }
    }
    return result;
  }
}

// --- Usage ---

async function main() {
  const apiKey = process.argv[2] ?? process.env.SOUNDSIDE_API_KEY;
  if (!apiKey) {
    console.error('Usage: npx tsx soundside-client.ts <API_KEY>');
    process.exit(1);
  }

  const client = new SoundsideClient(apiKey);

  // Connect
  await client.connect();

  // List tools
  const tools = await client.listTools();
  console.log(`\n📋 Available tools (${tools.length}):`);
  for (const t of tools) {
    console.log(`  • ${t.name}`);
  }

  // Generate an image
  console.log('\n🎨 Generating image...');
  const t0 = Date.now();
  const imageResult = (await client.callTool('create_image', {
    prompt: 'A vibrant sunset over a calm ocean, photorealistic',
    provider: 'vertex',
  })) as Record<string, unknown>;
  console.log(`  Resource ID: ${imageResult.resource_id ?? 'N/A'}`);
  console.log(`  Time: ${((Date.now() - t0) / 1000).toFixed(1)}s`);

  // Generate text
  console.log('\n📝 Generating text...');
  const textResult = (await client.callTool('create_text', {
    prompt: 'Write a haiku about AI agents creating art',
    provider: 'vertex',
  })) as Record<string, unknown>;
  console.log(`  ${String(textResult.text ?? JSON.stringify(textResult)).slice(0, 200)}`);
}

main().catch(console.error);
