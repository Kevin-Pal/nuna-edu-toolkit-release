/* Build the one-page Nuna-Edu-Toolkit promo slide.
 * Matches the host slide-deck theme: 16:9 (13.333" x 7.5"),
 * Aptos fonts, navy / teal / orange palette. Embeds the hub QR (-> landing page).
 *
 *   cd tools/ppt && npm install && node build_ppt.js
 *
 * Output: promo/Nuna-Edu-Toolkit-slide.pptx
 */
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..", "..");
const QR = path.join(ROOT, "site", "assets", "qr", "site.png"); // hub QR -> landing page
const OUT = path.join(ROOT, "promo", "Nuna-Edu-Toolkit-slide.pptx");

// Slide-deck palette
const NAVY = "0E2841", TEAL = "156082", ORANGE = "E97132",
      INK = "1C2B39", MUTED = "5B6B7A", SOFT = "F4F7FB", LINE = "DCE5EE";
const HEAD = "Aptos Display", BODY = "Aptos";

const p = new pptxgen();
p.defineLayout({ name: "NUNA", width: 13.333, height: 7.5 });
p.layout = "NUNA";
p.author = "Nuna-Edu-Toolkit";
p.title = "Nuna-Edu-Toolkit";

const s = p.addSlide();
s.background = { color: "FFFFFF" };

// --- Left column: text ---
s.addText("OPEN TOOLKIT  ·  AIoT LAB · CUHK", {
  x: 0.75, y: 0.7, w: 8, h: 0.35, fontFace: BODY, fontSize: 13, bold: true,
  color: TEAL, charSpacing: 2, margin: 0,
});

s.addText("Nuna-Edu-Toolkit", {
  x: 0.72, y: 1.05, w: 8, h: 0.95, fontFace: HEAD, fontSize: 46, bold: true,
  color: NAVY, margin: 0,
});

s.addText("Collect & annotate first-person audio — and turn it into research datasets.", {
  x: 0.75, y: 2.05, w: 7.7, h: 0.85, fontFace: BODY, fontSize: 20, color: INK,
  margin: 0, lineSpacingMultiple: 1.05,
});

const lead = (t) => ({ text: t, options: { bold: true, color: TEAL } });
const rest = (t) => ({ text: t, options: { breakLine: true, paraSpaceAfter: 12, color: INK } });
s.addText([
  lead("Capture"),  rest("  wearable audio streamed to your own server, sliced into 1-minute segments"),
  lead("Recall"),   rest("  ASR transcript previews (Qwen3-ASR or mock) speed up annotation"),
  lead("Annotate"), rest("  event-driven block + point labels — a swappable, multi-granularity schema"),
  lead("Open"),     { text: "  self-hostable, privacy-first, free for non-commercial use", options: { color: INK } },
], { x: 0.78, y: 3.05, w: 7.7, h: 2.7, fontFace: BODY, fontSize: 16, bullet: { indent: 16 }, margin: 0 });

s.addText(
  "Anlan Peng · Ruihan Xie · Yihang Su · Zhenyu Yan · Zhiyuan Xie · Guoliang Xing    —    AIoT Lab · The Chinese University of Hong Kong",
  { x: 0.75, y: 6.9, w: 11.8, h: 0.4, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0 }
);

// --- Right column: QR card ---
const cardX = 9.0, cardY = 1.3, cardW = 3.66, cardH = 4.95;
s.addShape(p.shapes.ROUNDED_RECTANGLE, {
  x: cardX, y: cardY, w: cardW, h: cardH, fill: { color: SOFT },
  line: { color: LINE, width: 1 }, rectRadius: 0.14,
  shadow: { type: "outer", color: "0E2841", blur: 9, offset: 3, angle: 135, opacity: 0.12 },
});

s.addText("SCAN TO DOWNLOAD & TRY", {
  x: cardX, y: cardY + 0.3, w: cardW, h: 0.35, align: "center", fontFace: BODY,
  fontSize: 13, bold: true, color: NAVY, charSpacing: 1, margin: 0,
});

const qrSize = 2.5;
s.addImage({ path: QR, x: cardX + (cardW - qrSize) / 2, y: cardY + 0.82, w: qrSize, h: qrSize });

s.addText("Demo  ·  App  ·  Source — one link", {
  x: cardX, y: cardY + 0.82 + qrSize + 0.14, w: cardW, h: 0.3, align: "center",
  fontFace: BODY, fontSize: 12, color: MUTED, margin: 0,
});
s.addText("kevin-pal.github.io/nuna-edu-toolkit-release", {
  x: cardX, y: cardY + 0.82 + qrSize + 0.44, w: cardW, h: 0.3, align: "center",
  fontFace: BODY, fontSize: 10.5, color: TEAL, margin: 0,
});

p.writeFile({ fileName: OUT }).then((f) => console.log("wrote", f));
