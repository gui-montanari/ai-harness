import test from "node:test";
import assert from "node:assert/strict";
import { buildDeckRequests, createSlidesTools, hexToRgb } from "./slides-tools.mjs";

test("hexToRgb converts six-digit colors", () => {
  assert.deepEqual(hexToRgb("#FF8000"), { red: 1, green: 128 / 255, blue: 0 });
  assert.throws(() => hexToRgb("orange"), /expected #RRGGBB/);
});

test("buildDeckRequests creates styled slides and text", () => {
  const requests = buildDeckRequests([
    { type: "cover", title: "Abertura", subtitle: "Subtítulo" },
    { type: "content", title: "Agenda", bullets: ["Um", "Dois"] },
  ]);
  assert.equal(requests.filter((request) => request.createSlide).length, 2);
  assert.ok(requests.some((request) => request.insertText?.text === "• Um\n• Dois"));
  assert.ok(requests.some((request) => request.updateTextStyle?.style.foregroundColor.opaqueColor.rgbColor));
});

test("Slides tool set exposes creation, precise editing, templates and export", () => {
  const tools = createSlidesTools({ slides: {}, drive: {} });
  const names = new Set(tools.map((tool) => tool.name));
  for (const name of [
    "gslides_create_presentation",
    "gslides_create_deck",
    "gslides_batch_update",
    "gslides_get_thumbnail",
    "gslides_copy_presentation",
    "gslides_export_presentation",
  ]) assert.ok(names.has(name), name);
});
