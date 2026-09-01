import fs from "node:fs";
import path from "node:path";
const dir = process.env.GDRIVE_CREDS_DIR;
const token = process.env.GDRIVE_REFRESH_TOKEN;
if (!dir || !token) throw new Error("GDRIVE_CREDS_DIR/GDRIVE_REFRESH_TOKEN ausente");
fs.mkdirSync(dir, {recursive: true});
fs.writeFileSync(path.join(dir, ".gdrive-server-credentials.json"), JSON.stringify({refresh_token: token, scope: "https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/presentations", token_type: "Bearer", expiry_date: Date.parse("2100-01-01T00:00:00Z")}, null, 2) + "\n", {mode: 0o600});
