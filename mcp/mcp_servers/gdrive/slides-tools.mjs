import fs from "node:fs";
import path from "node:path";

const PRESENTATION_MIME = "application/vnd.google-apps.presentation";

export function hexToRgb(value) {
  const match = /^#?([0-9a-f]{6})$/i.exec(value || "");
  if (!match) throw new Error(`Invalid color ${JSON.stringify(value)}; expected #RRGGBB`);
  const number = Number.parseInt(match[1], 16);
  return {
    red: ((number >> 16) & 255) / 255,
    green: ((number >> 8) & 255) / 255,
    blue: (number & 255) / 255,
  };
}

function solidColor(hex) {
  return { color: { rgbColor: hexToRgb(hex) } };
}

function optionalColor(hex) {
  return { opaqueColor: { rgbColor: hexToRgb(hex) } };
}

function escapeDriveQuery(value) {
  return String(value).replaceAll("\\", "\\\\").replaceAll("'", "\\'");
}

function textBoxRequests({ objectId, pageId, text, x, y, width, height, fontSize, color, bold = false, fontFamily }) {
  if (!text) return [];
  const requests = [
    {
      createShape: {
        objectId,
        shapeType: "TEXT_BOX",
        elementProperties: {
          pageObjectId: pageId,
          size: {
            width: { magnitude: width, unit: "PT" },
            height: { magnitude: height, unit: "PT" },
          },
          transform: {
            scaleX: 1,
            scaleY: 1,
            translateX: x,
            translateY: y,
            unit: "PT",
          },
        },
      },
    },
    { insertText: { objectId, text } },
    {
      updateTextStyle: {
        objectId,
        textRange: { type: "ALL" },
        style: {
          foregroundColor: optionalColor(color),
          fontFamily,
          fontSize: { magnitude: fontSize, unit: "PT" },
          bold,
        },
        fields: "foregroundColor,fontFamily,fontSize,bold",
      },
    },
  ];
  return requests;
}

export function buildDeckRequests(slides, theme = {}) {
  const background = theme.backgroundColor || "#F7F5EF";
  const foreground = theme.textColor || "#17212B";
  const accent = theme.accentColor || "#E4572E";
  const fontFamily = theme.fontFamily || "Inter";
  const requests = [];

  slides.forEach((slide, index) => {
    const sequence = String(index + 1).padStart(3, "0");
    const pageId = `slide_${sequence}`;
    const titleId = `title_${sequence}`;
    const bodyId = `body_${sequence}`;
    const accentId = `accent_${sequence}`;
    const numberId = `number_${sequence}`;
    const isCover = slide.type === "cover" || (index === 0 && !slide.body && slide.subtitle);
    const slideBackground = slide.backgroundColor || background;

    requests.push(
      {
        createSlide: {
          objectId: pageId,
          insertionIndex: index,
          slideLayoutReference: { predefinedLayout: "BLANK" },
        },
      },
      {
        updatePageProperties: {
          objectId: pageId,
          pageProperties: { pageBackgroundFill: { solidFill: solidColor(slideBackground) } },
          fields: "pageBackgroundFill",
        },
      },
      {
        createShape: {
          objectId: accentId,
          shapeType: "RECTANGLE",
          elementProperties: {
            pageObjectId: pageId,
            size: {
              width: { magnitude: isCover ? 84 : 42, unit: "PT" },
              height: { magnitude: isCover ? 7 : 5, unit: "PT" },
            },
            transform: {
              scaleX: 1,
              scaleY: 1,
              translateX: 54,
              translateY: isCover ? 112 : 45,
              unit: "PT",
            },
          },
        },
      },
      {
        updateShapeProperties: {
          objectId: accentId,
          shapeProperties: {
            shapeBackgroundFill: { solidFill: solidColor(slide.accentColor || accent) },
            outline: { propertyState: "NOT_RENDERED" },
          },
          fields: "shapeBackgroundFill,outline.propertyState",
        },
      },
    );

    if (isCover) {
      requests.push(
        ...textBoxRequests({ objectId: titleId, pageId, text: slide.title, x: 54, y: 145, width: 610, height: 115, fontSize: 34, color: foreground, bold: true, fontFamily }),
        ...textBoxRequests({ objectId: bodyId, pageId, text: slide.subtitle || slide.body, x: 56, y: 285, width: 560, height: 90, fontSize: 17, color: foreground, fontFamily }),
      );
    } else {
      const body = Array.isArray(slide.bullets)
        ? slide.bullets.map((item) => `• ${item}`).join("\n")
        : slide.body || slide.subtitle || "";
      requests.push(
        ...textBoxRequests({ objectId: titleId, pageId, text: slide.title, x: 54, y: 63, width: 610, height: 65, fontSize: 25, color: foreground, bold: true, fontFamily }),
        ...textBoxRequests({ objectId: bodyId, pageId, text: body, x: 58, y: 145, width: 600, height: 210, fontSize: 17, color: foreground, fontFamily }),
      );
    }

    requests.push(...textBoxRequests({ objectId: numberId, pageId, text: String(index + 1), x: 670, y: 380, width: 30, height: 18, fontSize: 9, color: foreground, fontFamily }));
  });
  return requests;
}

function resultText(value) {
  return { content: [{ type: "text", text: typeof value === "string" ? value : JSON.stringify(value, null, 2) }], isError: false };
}

async function exportPresentation(drive, { presentationId, format, outputPath, overwrite = false }) {
  const mimeTypes = {
    pdf: "application/pdf",
    pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  };
  const mimeType = mimeTypes[format];
  if (!mimeType) throw new Error("format must be pdf or pptx");
  const destination = path.resolve(outputPath);
  if (!overwrite && fs.existsSync(destination)) throw new Error(`Output already exists: ${destination}`);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  const response = await drive.files.export({ fileId: presentationId, mimeType }, { responseType: "arraybuffer" });
  fs.writeFileSync(destination, Buffer.from(response.data), { flag: overwrite ? "w" : "wx" });
  return resultText({ presentationId, format, outputPath: destination, bytes: Buffer.byteLength(response.data) });
}

export function createSlidesTools({ slides, drive }) {
  return [
    {
      name: "gslides_list_presentations",
      description: "List Google Slides presentations available in the authenticated Google Drive",
      inputSchema: {
        type: "object",
        properties: {
          nameContains: { type: "string", description: "Optional case-insensitive name fragment" },
          pageSize: { type: "integer", minimum: 1, maximum: 100, default: 20 },
          pageToken: { type: "string" },
        },
      },
      handler: async ({ nameContains, pageSize = 20, pageToken }) => {
        const conditions = [`mimeType = '${PRESENTATION_MIME}'`, "trashed = false"];
        if (nameContains) conditions.push(`name contains '${escapeDriveQuery(nameContains)}'`);
        const response = await drive.files.list({
          q: conditions.join(" and "),
          pageSize,
          pageToken,
          orderBy: "modifiedTime desc",
          fields: "nextPageToken,files(id,name,modifiedTime,createdTime,webViewLink,parents,capabilities(canEdit))",
        });
        return resultText({ presentations: response.data.files || [], nextPageToken: response.data.nextPageToken || null });
      },
    },
    {
      name: "gslides_get_presentation",
      description: "Read the complete structure and content of a Google Slides presentation",
      inputSchema: {
        type: "object",
        properties: { presentationId: { type: "string" } },
        required: ["presentationId"],
      },
      handler: async ({ presentationId }) => resultText((await slides.presentations.get({ presentationId })).data),
    },
    {
      name: "gslides_create_presentation",
      description: "Create a new blank Google Slides presentation",
      inputSchema: {
        type: "object",
        properties: { title: { type: "string", minLength: 1 } },
        required: ["title"],
      },
      handler: async ({ title }) => {
        const presentation = (await slides.presentations.create({ requestBody: { title } })).data;
        return resultText({ ...presentation, webViewLink: `https://docs.google.com/presentation/d/${presentation.presentationId}/edit` });
      },
    },
    {
      name: "gslides_create_deck",
      description: "Create a complete styled Google Slides deck from structured slide content",
      inputSchema: {
        type: "object",
        properties: {
          title: { type: "string", minLength: 1 },
          slides: {
            type: "array",
            minItems: 1,
            items: {
              type: "object",
              properties: {
                type: { type: "string", enum: ["cover", "content"] },
                title: { type: "string" },
                subtitle: { type: "string" },
                body: { type: "string" },
                bullets: { type: "array", items: { type: "string" } },
                backgroundColor: { type: "string", pattern: "^#?[0-9A-Fa-f]{6}$" },
                accentColor: { type: "string", pattern: "^#?[0-9A-Fa-f]{6}$" },
              },
              required: ["title"],
            },
          },
          theme: {
            type: "object",
            properties: {
              backgroundColor: { type: "string", pattern: "^#?[0-9A-Fa-f]{6}$" },
              textColor: { type: "string", pattern: "^#?[0-9A-Fa-f]{6}$" },
              accentColor: { type: "string", pattern: "^#?[0-9A-Fa-f]{6}$" },
              fontFamily: { type: "string" },
            },
          },
        },
        required: ["title", "slides"],
      },
      handler: async ({ title, slides: slideSpecs, theme }) => {
        const presentation = (await slides.presentations.create({ requestBody: { title } })).data;
        const presentationId = presentation.presentationId;
        try {
          const requests = buildDeckRequests(slideSpecs, theme);
          const initialSlideId = presentation.slides?.[0]?.objectId
            || (await slides.presentations.get({ presentationId, fields: "slides.objectId" })).data.slides?.[0]?.objectId;
          if (initialSlideId) requests.push({ deleteObject: { objectId: initialSlideId } });
          await slides.presentations.batchUpdate({ presentationId, requestBody: { requests } });
          return resultText({
            presentationId,
            title,
            slideCount: slideSpecs.length,
            webViewLink: `https://docs.google.com/presentation/d/${presentationId}/edit`,
          });
        } catch (error) {
          error.message = `${error.message} (blank presentation was created: https://docs.google.com/presentation/d/${presentationId}/edit)`;
          throw error;
        }
      },
    },
    {
      name: "gslides_batch_update",
      description: "Apply native Google Slides presentations.batchUpdate requests for precise editing",
      inputSchema: {
        type: "object",
        properties: {
          presentationId: { type: "string" },
          requests: { type: "array", minItems: 1, items: { type: "object" } },
          requiredRevisionId: { type: "string", description: "Optional optimistic-concurrency revision ID" },
        },
        required: ["presentationId", "requests"],
      },
      handler: async ({ presentationId, requests, requiredRevisionId }) => {
        const requestBody = { requests };
        if (requiredRevisionId) requestBody.writeControl = { requiredRevisionId };
        return resultText((await slides.presentations.batchUpdate({ presentationId, requestBody })).data);
      },
    },
    {
      name: "gslides_replace_text",
      description: "Replace text throughout a Google Slides presentation",
      inputSchema: {
        type: "object",
        properties: {
          presentationId: { type: "string" },
          find: { type: "string" },
          replace: { type: "string" },
          matchCase: { type: "boolean", default: false },
        },
        required: ["presentationId", "find", "replace"],
      },
      handler: async ({ presentationId, find, replace, matchCase = false }) => {
        const response = await slides.presentations.batchUpdate({
          presentationId,
          requestBody: { requests: [{ replaceAllText: { containsText: { text: find, matchCase }, replaceText: replace } }] },
        });
        return resultText(response.data);
      },
    },
    {
      name: "gslides_get_thumbnail",
      description: "Render one slide as a PNG thumbnail for visual review",
      inputSchema: {
        type: "object",
        properties: {
          presentationId: { type: "string" },
          pageObjectId: { type: "string" },
          size: { type: "string", enum: ["SMALL", "MEDIUM", "LARGE"], default: "LARGE" },
        },
        required: ["presentationId", "pageObjectId"],
      },
      handler: async ({ presentationId, pageObjectId, size = "LARGE" }) => {
        const thumbnail = (await slides.presentations.pages.getThumbnail({
          presentationId,
          pageObjectId,
          "thumbnailProperties.mimeType": "PNG",
          "thumbnailProperties.thumbnailSize": size,
        })).data;
        const response = await fetch(thumbnail.contentUrl);
        if (!response.ok) throw new Error(`Could not download thumbnail: HTTP ${response.status}`);
        const image = Buffer.from(await response.arrayBuffer());
        return {
          content: [
            { type: "text", text: JSON.stringify({ presentationId, pageObjectId, width: thumbnail.width, height: thumbnail.height }) },
            { type: "image", data: image.toString("base64"), mimeType: "image/png" },
          ],
          isError: false,
        };
      },
    },
    {
      name: "gslides_copy_presentation",
      description: "Copy an existing Google Slides presentation to use it as a template",
      inputSchema: {
        type: "object",
        properties: {
          presentationId: { type: "string" },
          title: { type: "string" },
          folderId: { type: "string", description: "Optional destination Drive folder ID" },
        },
        required: ["presentationId", "title"],
      },
      handler: async ({ presentationId, title, folderId }) => {
        const requestBody = { name: title };
        if (folderId) requestBody.parents = [folderId];
        const file = (await drive.files.copy({
          fileId: presentationId,
          requestBody,
          fields: "id,name,webViewLink,parents",
        })).data;
        return resultText(file);
      },
    },
    {
      name: "gslides_export_presentation",
      description: "Export a Google Slides presentation to a local PDF or PowerPoint file",
      inputSchema: {
        type: "object",
        properties: {
          presentationId: { type: "string" },
          format: { type: "string", enum: ["pdf", "pptx"] },
          outputPath: { type: "string" },
          overwrite: { type: "boolean", default: false },
        },
        required: ["presentationId", "format", "outputPath"],
      },
      handler: async (args) => exportPresentation(drive, args),
    },
  ];
}
