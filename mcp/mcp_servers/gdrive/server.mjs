#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { google } from "googleapis";
import { tools as legacyTools } from "@isaacphi/mcp-gdrive/dist/tools/index.js";
import { createSlidesTools } from "./slides-tools.mjs";

function oauthClient() {
  const clientId = process.env.GDRIVE_CLIENT_ID;
  const clientSecret = process.env.GDRIVE_CLIENT_SECRET;
  const refreshToken = process.env.GDRIVE_REFRESH_TOKEN;
  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error("GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET and GDRIVE_REFRESH_TOKEN are required");
  }
  const auth = new google.auth.OAuth2(clientId, clientSecret);
  auth.setCredentials({ refresh_token: refreshToken });
  return auth;
}

function googleError(error) {
  const reason = error?.response?.data?.error?.details?.find((item) => item.reason)?.reason;
  if (reason === "SERVICE_DISABLED") {
    const activationUrl = error.response.data.error.details.find((item) => item.metadata?.activationUrl)?.metadata?.activationUrl;
    return `${error.message}${activationUrl ? ` Enable the API at ${activationUrl}` : ""}`;
  }
  if (error?.code === 403 && /scope|permission|insufficient/i.test(error.message || "")) {
    return `${error.message}. Reauthorize Google OAuth with https://www.googleapis.com/auth/presentations.`;
  }
  return error?.message || String(error);
}

const auth = oauthClient();
google.options({ auth });
const slides = google.slides({ version: "v1", auth });
const drive = google.drive({ version: "v3", auth });
const toolset = process.env.GOOGLE_WORKSPACE_TOOLSET || "all";
if (!["all", "drive", "slides"].includes(toolset)) {
  throw new Error("GOOGLE_WORKSPACE_TOOLSET must be all, drive or slides");
}
const slidesTools = createSlidesTools({ slides, drive });
const allTools = toolset === "drive"
  ? legacyTools
  : toolset === "slides"
    ? slidesTools
    : [...legacyTools, ...slidesTools];

const server = new Server(
  { name: `ai-harness/google-${toolset === "all" ? "workspace" : toolset}`, version: "1.0.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: allTools.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })),
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const tool = allTools.find((candidate) => candidate.name === request.params.name);
  if (!tool) throw new Error(`Unknown tool: ${request.params.name}`);
  try {
    return await tool.handler(request.params.arguments || {});
  } catch (error) {
    return { content: [{ type: "text", text: googleError(error) }], isError: true };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
