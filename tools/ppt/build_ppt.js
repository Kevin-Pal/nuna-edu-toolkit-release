/* Build the one-page Nuna-Edu-Toolkit promo slide.
 * 16:9 (13.333" x 7.5"), deep-purple banner + Times New Roman serif,
 * tri-color footer bar. Embeds the hub QR (-> landing page).
 *
 *   cd tools/ppt && npm install && node build_ppt.js
 *
 * Output: promo/Nuna-Edu-Toolkit-slide.pptx
 */
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..", "..");
const QR = path.join(ROOT, "site", "assets", "qr", "site.png"); // hub QR -> landing page
const LAB = path.join(ROOT, "site", "assets", "img", "aiot-lab-logo.png"); // AIoT Lab logo
const OUT = path.join(ROOT, "promo", "Nuna-Edu-Toolkit-slide.pptx");

// Deck template palette
const PURPLE = "740E6C", DPURPLE = "570B51",
      WHITE = "FFFFFF", INK = "1A1A1A", MUTED = "6B5B68",
      CARD = "F7EFF6", CARDLINE = "D9BBD5";
// Template uses Times New Roman serif throughout (bold for headings)
const HEAD = "Times New Roman", BODY = "Times New Roman";

const p = new pptxgen();
p.defineLayout({ name: "NUNA", width: 13.333, height: 7.5 });
p.layout = "NUNA";
p.author = "Nuna-Edu-Toolkit";
p.title = "Nuna-Edu-Toolkit";

const s = p.addSlide();
s.background = { color: "FFFFFF" };

// --- Top banner (template header bar) ---
const barH = 1.18;
s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 13.333, h: barH, fill: { color: PURPLE } });
s.addText("Nuna-Edu-Toolkit", {
  x: 0.5, y: 0, w: 8.2, h: barH, valign: "middle", fontFace: HEAD, fontSize: 40,
  bold: true, color: WHITE, margin: 0,
});
s.addText("OPEN TOOLKIT  ·  AIoT LAB · CUHK", {
  x: 7.0, y: 0, w: 5.83, h: barH, valign: "middle", align: "right", fontFace: BODY,
  fontSize: 13, bold: true, color: WHITE, charSpacing: 1, margin: 0,
});

// --- Left column: lede + features ---
s.addText("Collect & annotate first-person audio — and turn it into research datasets.", {
  x: 0.55, y: 1.52, w: 7.7, h: 0.85, fontFace: BODY, fontSize: 20, italic: true,
  color: INK, margin: 0, lineSpacingMultiple: 1.05,
});

const lead = (t) => ({ text: t, options: { bold: true, color: PURPLE } });
const rest = (t) => ({ text: t, options: { breakLine: true, paraSpaceAfter: 22, color: INK } });
s.addText([
  lead("Capture"),  rest("  wearable audio streamed to your own server, sliced into 1-minute segments"),
  lead("Recall"),   rest("  pluggable ASR previews (bring your own model) speed up annotation"),
  lead("Annotate"), rest("  event-driven block + point labels — a swappable, multi-granularity schema"),
  lead("Open"),     { text: "  self-hostable, privacy-first, free for non-commercial use", options: { color: INK } },
], { x: 0.6, y: 2.95, w: 7.7, h: 3.2, fontFace: BODY, fontSize: 17, margin: 0 });

// --- AIoT Lab logo + affiliation + contact (letterhead above footer bar) ---
s.addImage({ path: LAB, x: 0.55, y: 6.18, w: 0.82, h: 0.82 });
s.addText(
  "Anlan Peng · Ruihan Xie · Yihang Su · Siyang Jiang · Zhiyuan Xie · Zhenyu Yan · Guoliang Xing  —  AIoT Lab · The Chinese University of Hong Kong",
  { x: 1.52, y: 6.24, w: 11.3, h: 0.34, fontFace: BODY, fontSize: 11.5, italic: true,
    color: MUTED, margin: 0, valign: "middle" }
);
s.addText([
  { text: "Contact   ", options: { bold: true, color: PURPLE } },
  { text: "Anlan Peng · pa025@ie.cuhk.edu.hk", options: { color: INK } },
  { text: "        aiot.ie.cuhk.edu.hk", options: { color: PURPLE } },
], { x: 1.52, y: 6.60, w: 11.3, h: 0.34, fontFace: BODY, fontSize: 11.5, margin: 0, valign: "middle" });

// --- Right column: QR card ---
const cardX = 9.05, cardY = 1.62, cardW = 3.7, cardH = 4.6;
s.addShape(p.shapes.ROUNDED_RECTANGLE, {
  x: cardX, y: cardY, w: cardW, h: cardH, fill: { color: CARD },
  line: { color: CARDLINE, width: 1 }, rectRadius: 0.12,
  shadow: { type: "outer", color: PURPLE, blur: 9, offset: 3, angle: 135, opacity: 0.14 },
});

s.addText("SCAN TO DOWNLOAD & TRY", {
  x: cardX, y: cardY + 0.3, w: cardW, h: 0.35, align: "center", fontFace: HEAD,
  fontSize: 14, bold: true, color: PURPLE, charSpacing: 1, margin: 0,
});

const qrSize = 2.4;
s.addImage({ path: QR, x: cardX + (cardW - qrSize) / 2, y: cardY + 0.82, w: qrSize, h: qrSize });

s.addText("Demo  ·  App  ·  Source — one link", {
  x: cardX, y: cardY + 0.82 + qrSize + 0.16, w: cardW, h: 0.3, align: "center",
  fontFace: BODY, fontSize: 12.5, color: MUTED, margin: 0,
});
s.addText("kevin-pal.github.io/nuna-edu-toolkit-release", {
  x: cardX, y: cardY + 0.82 + qrSize + 0.48, w: cardW, h: 0.3, align: "center",
  fontFace: BODY, fontSize: 11, bold: true, color: PURPLE, margin: 0,
});

// --- Tri-color footer bar (template footer) ---
const footY = 7.18, footH = 0.32, seg = 13.333 / 3;
[DPURPLE, PURPLE, DPURPLE].forEach((c, i) => {
  s.addShape(p.shapes.RECTANGLE, { x: seg * i, y: footY, w: seg, h: footH, fill: { color: c } });
});

p.writeFile({ fileName: OUT }).then((f) => console.log("wrote", f));
