#!/usr/bin/env python3
"""Gera relatório de auditoria em PDF (A4, pt-BR).

Usado por security-audit e principles-audit. Títulos, categorias e nome do
arquivo vêm de findings.json (`report`, `category_labels`, `category_order`);
os defaults preservam a auditoria de segurança.

Uso (sempre em venv isolado):

    python generate_report.py findings.json
    python generate_report.py findings.json -o relatorio.pdf
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Flowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# --- Paleta -----------------------------------------------------------------
CRITICA = colors.HexColor("#B91C1C")
ALTA = colors.HexColor("#EA580C")
MEDIA = colors.HexColor("#D97706")
BAIXA = colors.HexColor("#2563EB")
FORTE = colors.HexColor("#059669")
INFO = colors.HexColor("#6B7280")
NAVY = colors.HexColor("#0F172A")
SLATE = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#E2E8F0")
SURFACE = colors.HexColor("#F8FAFC")
CHIP_BG = {
    "critica": colors.HexColor("#FEE2E2"),
    "alta": colors.HexColor("#FFEDD5"),
    "media": colors.HexColor("#FEF3C7"),
    "baixa": colors.HexColor("#DBEAFE"),
    "informativa": colors.HexColor("#F1F5F9"),
}
CHIP_FG = {
    "critica": CRITICA,
    "alta": ALTA,
    "media": MEDIA,
    "baixa": BAIXA,
    "informativa": INFO,
}
HEX = {
    "critica": "#B91C1C",
    "alta": "#EA580C",
    "media": "#D97706",
    "baixa": "#2563EB",
    "informativa": "#6B7280",
    "forte": "#059669",
}
SEV_LABEL = {
    "critica": "CRÍTICA",
    "alta": "ALTA",
    "media": "MÉDIA",
    "baixa": "BAIXA",
    "informativa": "INFORMATIVA",
}
SEV_ORDER = ["critica", "alta", "media", "baixa", "informativa"]
CAT_LABEL = {
    "isolamento_dados": "Isolamento de dados",
    "autorizacao": "Autorização",
    "idor_superficies_publicas": "IDOR e superfícies públicas",
    "auth_sessao": "Auth e sessão",
    "segredos_dados_sensiveis": "Segredos e dados sensíveis",
    "inputs_injecao": "Inputs e injeção",
    "abuso_disponibilidade": "Abuso e disponibilidade",
    # Compatibilidade de relatórios antigos.
    "banco_sem_tranca": "Banco sem tranca",
    "permissao_navegador": "Permissão no navegador",
    "idor": "IDOR",
    "chaves_expostas": "Chaves expostas",
    "xss": "Inputs sem tratamento",
}
CAT_ORDER = [
    "isolamento_dados",
    "autorizacao",
    "idor_superficies_publicas",
    "auth_sessao",
    "segredos_dados_sensiveis",
    "inputs_injecao",
    "abuso_disponibilidade",
]
DEFAULT_REPORT = {
    "title": "Relatório de Auditoria de Segurança",
    "kicker": "AUDITORIA DE SEGURANÇA · 7 CATEGORIAS",
    "footer": "gerado por security-audit",
    "filename": "relatorio-auditoria-seguranca.pdf",
}


def report_meta(data: dict) -> dict:
    meta = dict(DEFAULT_REPORT)
    meta.update(data.get("report") or {})
    return meta


def category_labels_of(data: dict) -> dict:
    labels = dict(CAT_LABEL)
    labels.update(data.get("category_labels") or {})
    return labels


def category_order_of(data: dict) -> list:
    declared = data.get("category_order")
    labels = category_labels_of(data)
    if declared:
        order = list(declared)
    else:
        order = [k for k in CAT_ORDER if k in labels]
        for k in labels:
            if k not in order:
                order.append(k)
    for f in data.get("findings") or []:
        cat = f.get("category")
        if cat and cat not in order:
            order.append(cat)
    return order


def cat_name(data: dict, key: str) -> str:
    return category_labels_of(data).get(key) or str(key).replace("_", " ")


REQUIRED_TOP = [
    "project_name",
    "date",
    "scope",
    "methodology",
    "stack",
    "coverage_notes",
    "findings",
    "strengths",
    "weaknesses",
    "recommendations",
    "issues",
]
REQUIRED_FINDING = [
    "id",
    "category",
    "severity",
    "file",
    "lines",
    "title",
    "description",
    "snippet",
    "why_exploitable",
    "exploitability_conditions",
    "impact",
    "fix",
    "acceptance_criteria",
]


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_findings(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"JSON inválido em {path}: {exc}")
    if not isinstance(data, dict):
        die("findings.json deve ser um objeto")
    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        die(f"campos obrigatórios ausentes: {', '.join(missing)}")
    for i, f in enumerate(data["findings"]):
        miss = [k for k in REQUIRED_FINDING if k not in f]
        if miss:
            die(f"finding[{i}] sem campos: {', '.join(miss)}")
        if f["severity"] not in SEV_LABEL:
            die(f"finding[{i}] severity inválida: {f['severity']}")
        cat = f.get("category") or ""
        allowed_categories = (
            set(CAT_LABEL)
            | set(data.get("category_order") or [])
            | set((data.get("category_labels") or {}).keys())
        )
        if cat not in allowed_categories:
            die(f"finding[{i}] category inválida: {cat}")
    return data


def styles() -> dict:
    base = getSampleStyleSheet()
    s = {}
    s["cover_kicker"] = ParagraphStyle(
        "cover_kicker",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#94A3B8"),
        letterSpacing=1.2,
        spaceAfter=6,
    )
    s["cover_title"] = ParagraphStyle(
        "cover_title",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.white,
        spaceAfter=8,
    )
    s["cover_meta"] = ParagraphStyle(
        "cover_meta",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#CBD5E1"),
    )
    s["h1"] = ParagraphStyle(
        "h1",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=NAVY,
        spaceBefore=4,
        spaceAfter=10,
        borderPadding=0,
    )
    s["h2"] = ParagraphStyle(
        "h2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=NAVY,
        spaceBefore=12,
        spaceAfter=6,
    )
    s["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=SLATE,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    s["body_left"] = ParagraphStyle(
        "body_left",
        parent=s["body"],
        alignment=TA_LEFT,
    )
    s["small"] = ParagraphStyle(
        "small",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=SLATE,
    )
    s["muted"] = ParagraphStyle(
        "muted",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=MUTED,
    )
    s["cell"] = ParagraphStyle(
        "cell",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=SLATE,
    )
    s["cell_path"] = ParagraphStyle(
        "cell_path",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=7,
        leading=9.5,
        textColor=SLATE,
    )
    s["cell_bold"] = ParagraphStyle(
        "cell_bold",
        parent=s["cell"],
        fontName="Helvetica-Bold",
        textColor=NAVY,
    )
    s["th"] = ParagraphStyle(
        "th",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.white,
    )
    s["code"] = ParagraphStyle(
        "code",
        parent=base["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=NAVY,
        backColor=SURFACE,
        leftIndent=0,
        spaceBefore=4,
        spaceAfter=8,
    )
    s["issue_delim"] = ParagraphStyle(
        "issue_delim",
        parent=base["Normal"],
        fontName="Courier-Bold",
        fontSize=8,
        leading=11,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=6,
    )
    s["stat"] = ParagraphStyle(
        "stat",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=NAVY,
    )
    s["stat_lbl"] = ParagraphStyle(
        "stat_lbl",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        alignment=TA_CENTER,
        textColor=MUTED,
    )
    s["chip"] = ParagraphStyle(
        "chip",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
    )
    s["caption"] = ParagraphStyle(
        "caption",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        alignment=TA_CENTER,
        textColor=MUTED,
        spaceBefore=2,
        spaceAfter=8,
    )
    s["prio"] = ParagraphStyle(
        "prio",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=NAVY,
    )
    return s


class HRule(Flowable):
    def __init__(self, color=LINE, thickness=0.6, space=4):
        super().__init__()
        self.color = color
        self.thickness = thickness
        self.space = space
        self.height = thickness + space

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


class StripeBar(Flowable):
    def __init__(self, height=5):
        super().__init__()
        self.h = height
        self.cols = [CRITICA, ALTA, MEDIA, BAIXA, FORTE]

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.h

    def draw(self):
        w = self.width / len(self.cols)
        for i, c in enumerate(self.cols):
            self.canv.setFillColor(c)
            self.canv.rect(i * w, 0, w + 0.3, self.h, stroke=0, fill=1)


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_loc(file: str, lines: str, *, compact: bool = False) -> str:
    """Em coluna estreita, caminho numa linha e número de linha na de baixo."""
    if compact:
        return f"{esc(file)}<br/>:{esc(lines)}"
    return f"{esc(file)}:{esc(lines)}"


def md_inline(text: str) -> str:
    """Escape then apply a tiny subset of markdown: **bold**, `code`."""
    import re

    text = esc(text)
    text = re.sub(r"`([^`]+)`", r"<font face='Courier' size='8'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def make_chip(severity: str, st: dict) -> Table:
    label = SEV_LABEL[severity]
    fg = CHIP_FG[severity]
    bg = CHIP_BG[severity]
    style = ParagraphStyle(
        f"chip_{severity}",
        parent=st["chip"],
        textColor=fg,
    )
    inner = Table([[Paragraph(label, style)]], colWidths=[2.4 * cm])
    inner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.6, fg),
            ]
        )
    )
    return inner


def cover_banner(data: dict, st: dict, width: float) -> Table:
    meta = report_meta(data)
    title = f"{esc(meta['title'])} — {esc(data['project_name'])}"
    inner = [
        [Paragraph(esc(meta["kicker"]), st["cover_kicker"])],
        [Paragraph(title, st["cover_title"])],
        [
            Paragraph(
                f"Data: {esc(data['date'])} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Achados: {len(data['findings'])} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Issues: {len(data['issues'])}",
                st["cover_meta"],
            )
        ],
    ]
    t = Table(inner, colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (0, 0), 22),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 18),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -2), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def stack_block(data: dict, st: dict, width: float) -> Table:
    stack = data.get("stack") or {}
    rows_src = [
        ("Linguagem", stack.get("language", "—")),
        ("Framework", stack.get("framework", "—")),
        ("ORM / query", stack.get("orm", "—")),
        ("Auth", stack.get("auth", "—")),
        ("Frontend", stack.get("frontend", "—")),
        ("Deploy", ", ".join(stack.get("deploy") or []) or "—"),
        ("Isolamento", stack.get("isolation_mechanism", "—")),
    ]
    cells = []
    for label, value in rows_src:
        cells.append(
            [
                Paragraph(f"<b>{esc(label)}</b>", st["small"]),
                Paragraph(esc(value), st["small"]),
            ]
        )
    t = Table(cells, colWidths=[3.4 * cm, width - 3.4 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE),
            ]
        )
    )
    return t


def stat_cards(counts: Counter, total: int, st: dict, width: float) -> Table:
    items = [("TOTAL", str(total), NAVY)]
    for key in SEV_ORDER:
        items.append((SEV_LABEL[key], str(counts.get(key, 0)), CHIP_FG[key]))
    col_w = width / len(items)
    cells = []
    for label, value, color in items:
        num_style = ParagraphStyle(
            f"stat_{label}",
            parent=st["stat"],
            textColor=color,
            fontSize=16,
        )
        box = [
            Paragraph(esc(value), num_style),
            Paragraph(esc(label), st["stat_lbl"]),
        ]
        inner = Table([[box[0]], [box[1]]], colWidths=[col_w - 4])
        inner.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        cells.append(inner)
    t = Table([cells], colWidths=[col_w] * len(items))
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def draw_donut(counts: Counter, dest: Path) -> None:
    labels, sizes, cols = [], [], []
    for key in SEV_ORDER:
        n = counts.get(key, 0)
        if n <= 0:
            continue
        labels.append(f"{SEV_LABEL[key]} ({n})")
        sizes.append(n)
        cols.append(HEX[key])
    fig, ax = plt.subplots(figsize=(4.4, 4.4), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    total = sum(sizes)
    if total == 0:
        ax.pie(
            [1],
            colors=["#059669"],
            startangle=90,
            wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
        )
        ax.text(0, 0, "0\nACHADOS", ha="center", va="center", fontsize=13, color="#059669", fontweight="bold")
    else:
        ax.pie(
            sizes,
            colors=cols,
            startangle=90,
            wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
        )
        ax.text(
            0,
            0,
            f"{total}\nACHADOS",
            ha="center",
            va="center",
            fontsize=12,
            color="#0F172A",
            fontweight="bold",
        )
        ax.legend(
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.04),
            ncol=2,
            frameon=False,
            fontsize=8,
        )
    ax.set_aspect("equal")
    plt.tight_layout(pad=0.4)
    fig.savefig(dest, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_bars(data: dict, cat_counts: Counter, dest: Path) -> None:
    order = category_order_of(data)
    labels = [cat_name(data, k) for k in order]
    values = [cat_counts.get(k, 0) for k in order]
    fig, ax = plt.subplots(figsize=(5.6, 4.2), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    palette = ["#0F172A", "#334155", "#B91C1C", "#EA580C", "#2563EB", "#D97706", "#059669"]
    bar_colors = [palette[i % len(palette)] for i in range(len(labels))]
    y = range(len(labels))
    ax.barh(list(y), values, color=bar_colors, height=0.55)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=8, color="#334155")
    ax.invert_yaxis()
    ax.set_xlabel("Achados", fontsize=8, color="#64748B")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#E2E8F0")
    ax.spines["bottom"].set_color("#E2E8F0")
    ax.tick_params(colors="#64748B", labelsize=8)
    xmax = max(values + [1])
    ax.set_xlim(0, xmax + 0.8)
    for i, v in enumerate(values):
        ax.text(v + 0.08, i, str(v), va="center", fontsize=8, color="#0F172A")
    plt.tight_layout()
    fig.savefig(dest, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def findings_table(findings: list, st: dict, width: float) -> Table:
    header = [
        Paragraph("Severidade", st["th"]),
        Paragraph("Arquivo:linha", st["th"]),
        Paragraph("Descrição", st["th"]),
    ]
    rows = [header]
    col_w = [2.6 * cm, 6.6 * cm, width - 9.2 * cm]
    for f in findings:
        loc = format_loc(f["file"], f["lines"], compact=True)
        desc = f"<b>{esc(f['title'])}</b><br/>{esc(f['description'])}"
        rows.append(
            [
                make_chip(f["severity"], st),
                Paragraph(loc, st["cell_path"]),
                Paragraph(desc, st["cell"]),
            ]
        )
    t = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (1, i), (-1, i), SURFACE))
    t.setStyle(TableStyle(style_cmds))
    return t


def finding_detail(data: dict, f: dict, st: dict, width: float) -> list:
    chip = make_chip(f["severity"], st)
    head = Table(
        [
            [
                chip,
                Paragraph(
                    f"<b>{esc(f['id'])}</b> · {esc(cat_name(data, f['category']))}<br/>"
                    f"{esc(f['title'])}",
                    st["body_left"],
                ),
            ]
        ],
        colWidths=[2.6 * cm, width - 2.6 * cm],
    )
    head.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (0, 0), 6),
            ]
        )
    )
    snippet = (f.get("snippet") or "").rstrip() + "\n"
    block = [
        head,
        Spacer(1, 4),
        Paragraph(f"<b>Onde.</b> {format_loc(f['file'], f['lines'])}", st["small"]),
        Paragraph(esc(f["description"]), st["body"]),
        Paragraph("<b>Por que é explorável.</b> " + esc(f["why_exploitable"]), st["body"]),
    ]
    if f.get("exploitability_conditions"):
        block.append(
            Paragraph(
                "<b>Condições.</b> " + esc(f["exploitability_conditions"]),
                st["body"],
            )
        )
    block += [
        Paragraph("<b>Impacto.</b> " + esc(f["impact"]), st["body"]),
        Paragraph("<b>Correção sugerida.</b> " + esc(f["fix"]), st["body"]),
        Paragraph("<b>Trecho</b>", st["small"]),
        Preformatted(snippet, st["code"], maxLineLength=110),
    ]
    criteria = f.get("acceptance_criteria") or []
    if criteria:
        items = [
            ListItem(Paragraph(esc(c), st["small"]), leftIndent=8, bulletColor=NAVY)
            for c in criteria
        ]
        block.append(Paragraph("<b>Critérios de aceite</b>", st["small"]))
        block.append(ListFlowable(items, bulletType="bullet", leftIndent=12, bulletFontSize=7))
    block.append(Spacer(1, 8))
    return [KeepTogether(block)]


def markdown_to_flowables(md: str, st: dict) -> list:
    flow = []
    lines = md.replace("\r\n", "\n").split("\n")
    buf: list[str] = []
    in_code = False
    code_lines: list[str] = []

    def flush_buf():
        nonlocal buf
        text = " ".join(x.strip() for x in buf if x.strip())
        buf = []
        if text:
            flow.append(Paragraph(md_inline(text), st["body_left"]))

    for raw in lines:
        if raw.strip().startswith("```"):
            if in_code:
                flow.append(Preformatted("\n".join(code_lines) + "\n", st["code"], maxLineLength=110))
                code_lines = []
                in_code = False
            else:
                flush_buf()
                in_code = True
            continue
        if in_code:
            code_lines.append(raw)
            continue
        if raw.startswith("# "):
            flush_buf()
            flow.append(Paragraph(md_inline(raw[2:]), st["h2"]))
        elif raw.startswith("## "):
            flush_buf()
            flow.append(Paragraph(md_inline(raw[3:]), st["h2"]))
        elif raw.startswith("### "):
            flush_buf()
            flow.append(Paragraph(md_inline(raw[4:]), st["h2"]))
        elif raw.strip().startswith("- "):
            flush_buf()
            item = raw.strip()[2:]
            if item.startswith("[ ] ") or item.startswith("[x] ") or item.startswith("[X] "):
                item = item[4:]
                prefix = "[ ] "
            else:
                prefix = "• "
            flow.append(Paragraph(prefix + md_inline(item), st["small"]))
        elif raw.strip() == "":
            flush_buf()
            flow.append(Spacer(1, 3))
        else:
            buf.append(raw)
    flush_buf()
    if in_code and code_lines:
        flow.append(Preformatted("\n".join(code_lines) + "\n", st["code"], maxLineLength=110))
    return flow


def issue_block(n: int, issue: dict, st: dict, width: float) -> list:
    title = issue.get("title") or f"Issue {n}"
    labels = ", ".join(issue.get("labels") or ["security"])
    body = issue.get("body") or ""
    delim_open = Paragraph(esc(f"--- ISSUE {n} ---"), st["issue_delim"])
    delim_close = Paragraph(esc(f"--- FIM ISSUE {n} ---"), st["issue_delim"])
    header = Paragraph(
        f"<b>{esc(title)}</b><br/><font color='#64748B'>Labels sugeridas: {esc(labels)}</font>",
        st["body_left"],
    )
    inner = [delim_open, header, Spacer(1, 4)]
    inner.extend(markdown_to_flowables(body, st))
    inner.append(delim_close)
    t = Table([[inner]], colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LINEBEFORE", (0, 0), (0, 0), 3, NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return [t, Spacer(1, 10)]


def build_story(data: dict, st: dict, chart_dir: Path) -> list:
    width = A4[0] - 4 * cm
    findings = data["findings"]
    counts = Counter(f["severity"] for f in findings)
    cat_counts = Counter(f["category"] for f in findings)
    donut_path = chart_dir / "donut.png"
    bars_path = chart_dir / "bars.png"
    draw_donut(counts, donut_path)
    draw_bars(data, cat_counts, bars_path)

    story: list = []

    # --- a) Capa ---
    story.append(cover_banner(data, st, width))
    story.append(StripeBar(5))
    story.append(Spacer(1, 14))
    story.append(Paragraph("Escopo auditado", st["h2"]))
    story.append(Paragraph(esc(data["scope"]), st["body"]))
    story.append(Paragraph("Nota metodológica", st["h2"]))
    story.append(Paragraph(esc(data["methodology"]), st["body"]))
    story.append(Paragraph("Stack detectada", st["h2"]))
    story.append(stack_block(data, st, width))
    coverage = data.get("coverage_notes") or {}
    if coverage:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Aplicabilidade das categorias", st["h2"]))
        cov_rows = [[Paragraph("<b>Categoria</b>", st["cell_bold"]), Paragraph("<b>Nota</b>", st["cell_bold"])]]
        order = category_order_of(data)
        extra = [k for k in coverage.keys() if k not in order]
        for i, k in enumerate(order + extra, start=1):
            label = f"{i}. {cat_name(data, k)}"
            cov_rows.append(
                [
                    Paragraph(esc(label), st["cell"]),
                    Paragraph(esc(coverage.get(k, "não informado")), st["cell"]),
                ]
            )
        cov_t = Table(cov_rows, colWidths=[5.2 * cm, width - 5.2 * cm])
        cov_t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), SURFACE),
                    ("GRID", (0, 0), (-1, -1), 0.3, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(cov_t)

    story.append(PageBreak())

    # --- b) Resumo executivo ---
    story.append(Paragraph("Resumo executivo", st["h1"]))
    story.append(HRule(NAVY, 1.2, 8))
    story.append(Paragraph("Totais por severidade", st["h2"]))
    story.append(stat_cards(counts, len(findings), st, width))
    story.append(Spacer(1, 12))

    donut = Image(str(donut_path), width=8.2 * cm, height=8.2 * cm)
    bars = Image(str(bars_path), width=9.4 * cm, height=7.2 * cm)
    charts = Table([[donut, bars]], colWidths=[8.6 * cm, width - 8.6 * cm])
    charts.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(charts)
    story.append(
        Paragraph(
            "Rosca: distribuição por severidade. Barras: achados por categoria.",
            st["caption"],
        )
    )

    # --- c) Fortes / fracos ---
    story.append(Paragraph("Pontos fortes e pontos fracos", st["h1"]))
    story.append(HRule(NAVY, 1.2, 8))
    story.append(Paragraph("O que está protegido", st["h2"]))
    strengths = data.get("strengths") or []
    if not strengths:
        story.append(Paragraph("Nenhum ponto forte registrado — a cobertura ficou incompleta?", st["body"]))
    else:
        for sitem in strengths:
            title = sitem.get("title") if isinstance(sitem, dict) else str(sitem)
            evidence = sitem.get("evidence", "") if isinstance(sitem, dict) else ""
            file_ = sitem.get("file", "") if isinstance(sitem, dict) else ""
            body = f"<b>{esc(title)}</b>"
            if evidence:
                body += f" — {esc(evidence)}"
            if file_:
                body += f"<br/><font color='#64748B' face='Courier' size='8'>{esc(file_)}</font>"
            row = Table(
                [[Paragraph("●", ParagraphStyle("dot", fontSize=10, textColor=FORTE, leading=12)), Paragraph(body, st["body_left"])]],
                colWidths=[0.6 * cm, width - 0.6 * cm],
            )
            row.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            story.append(row)

    story.append(Paragraph("Riscos centrais", st["h2"]))
    weaknesses = data.get("weaknesses") or []
    if not weaknesses:
        story.append(Paragraph("Nenhum risco central destacado além da tabela de achados.", st["body"]))
    else:
        for w in weaknesses:
            text = w if isinstance(w, str) else w.get("text", str(w))
            row = Table(
                [[Paragraph("●", ParagraphStyle("dotw", fontSize=10, textColor=CRITICA, leading=12)), Paragraph(esc(text), st["body_left"])]],
                colWidths=[0.6 * cm, width - 0.6 * cm],
            )
            row.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            story.append(row)

    story.append(PageBreak())

    # --- d) Tabela de achados ---
    story.append(Paragraph("Achados detalhados", st["h1"]))
    story.append(HRule(NAVY, 1.2, 8))
    if not findings:
        story.append(Paragraph("Nenhum achado verificado nesta auditoria.", st["body"]))
    else:
        story.append(findings_table(findings, st, width))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Detalhamento por achado", st["h2"]))
        for f in findings:
            story.extend(finding_detail(data, f, st, width))

    # --- e) Recomendações ---
    story.append(Spacer(1, 10))
    story.append(Paragraph("Recomendações priorizadas", st["h1"]))
    story.append(HRule(NAVY, 1.2, 8))
    recs = data.get("recommendations") or []
    if not recs:
        story.append(Paragraph("Sem recomendações adicionais além das correções dos achados.", st["body"]))
    else:
        prio_color = {"P1": CRITICA, "P2": ALTA, "P3": MEDIA, "P4": BAIXA}
        for rec in recs:
            if isinstance(rec, str):
                prio, text = "P?", rec
            else:
                prio, text = rec.get("priority", "P?"), rec.get("text", "")
            color = prio_color.get(str(prio).upper(), SLATE)
            badge = ParagraphStyle(
                f"prio_{prio}",
                parent=st["prio"],
                textColor=colors.white,
                alignment=TA_CENTER,
                fontSize=8,
            )
            badge_t = Table([[Paragraph(esc(str(prio)), badge)]], colWidths=[1.4 * cm])
            badge_t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), color),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            row = Table(
                [[badge_t, Paragraph(esc(text), st["body_left"])]],
                colWidths=[1.8 * cm, width - 1.8 * cm],
            )
            row.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(row)

    # --- f) Issues ---
    story.append(PageBreak())
    story.append(Paragraph("Issues para o GitHub", st["h1"]))
    story.append(HRule(NAVY, 1.2, 8))
    story.append(
        Paragraph(
            "Texto completo, pronto para copiar e colar. Cada bloco vive entre "
            "as linhas --- ISSUE n --- e --- FIM ISSUE n ---.",
            st["body"],
        )
    )
    issues = data.get("issues") or []
    if not issues:
        story.append(Paragraph("Nenhuma issue acionável. Achados informativos não geraram ticket.", st["body"]))
    else:
        for i, issue in enumerate(issues, start=1):
            story.extend(issue_block(i, issue, st, width))

    return story


def add_header_footer(canvas, doc, data: dict):
    meta = report_meta(data)
    project = data["project_name"]
    canvas.saveState()
    page_w, page_h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, page_h - 0.45 * cm, page_w, 0.45 * cm, stroke=0, fill=1)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    header = f"{meta['title']} — {project}"
    canvas.drawString(2 * cm, page_h - 1.35 * cm, header)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, page_h - 1.5 * cm, page_w - 2 * cm, page_h - 1.5 * cm)
    canvas.line(2 * cm, 1.55 * cm, page_w - 2 * cm, 1.55 * cm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 1.1 * cm, f"Uso interno · {meta['footer']}")
    canvas.drawRightString(page_w - 2 * cm, 1.1 * cm, f"Página {doc.page}")
    canvas.restoreState()


def generate(data: dict, output: Path) -> None:
    st = styles()
    meta = report_meta(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="audit-charts-") as tmp:
        chart_dir = Path(tmp)
        story = build_story(data, st, chart_dir)
        doc = SimpleDocTemplate(
            str(output),
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2.1 * cm,
            bottomMargin=2 * cm,
            title=f"{meta['title']} — {data['project_name']}",
            author=meta["footer"],
        )
        doc.build(
            story,
            onFirstPage=lambda c, d: add_header_footer(c, d, data),
            onLaterPages=lambda c, d: add_header_footer(c, d, data),
        )
    print(f"wrote {output}")


def main() -> None:
    p = argparse.ArgumentParser(description="Gera o PDF de uma auditoria (segurança ou princípios).")
    p.add_argument("findings", type=Path, help="Caminho para findings.json")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="PDF de saída (default: report.filename no JSON, ao lado do findings)",
    )
    args = p.parse_args()
    if not args.findings.is_file():
        die(f"arquivo não encontrado: {args.findings}")
    audit_dir = args.findings.parent
    verifier = Path(__file__).with_name("verify_audit.py")
    evidence = audit_dir / "evidence.json"
    coverage = audit_dir / "coverage.md"
    if not verifier.is_file():
        die("verify_audit.py deve estar ao lado do gerador")
    repo_root = next(
        (parent for parent in audit_dir.parents if (parent / "AGENTS.md").is_file() or (parent / ".git").exists()),
        audit_dir.parent,
    )
    verify_command = [
        sys.executable,
        str(verifier),
        "--root",
        str(repo_root),
        "--findings",
        str(args.findings),
        "--evidence",
        str(evidence),
        "--coverage",
        str(coverage),
    ]
    inventory = audit_dir / "inventory.json"
    if inventory.is_file():
        verify_command.extend(["--inventory", str(inventory)])
    verified = subprocess.run(verify_command, text=True, capture_output=True, check=False)
    if verified.returncode != 0:
        die((verified.stderr or verified.stdout).strip())
    data = load_findings(args.findings)
    output = args.output or (args.findings.parent / report_meta(data)["filename"])
    generate(data, output)


if __name__ == "__main__":
    main()
