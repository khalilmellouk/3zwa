"""
Génération du Bon de Commande PDF (ReportLab).
Modifiez ici la mise en page, les couleurs ou les sections du PDF.
"""
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_pdf(demand: dict, top: list, demand_id: str) -> bytes:
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab non installe — pip install reportlab")

    from reportlab.lib import colors as rc
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

    # ── Palette ───────────────────────────────────────────────────────────────
    BLEU_TITRE = rc.HexColor("#1a3a5c")
    BLEU_SEC   = rc.HexColor("#1f5c99")
    BLEU_LIGHT = rc.HexColor("#dce9f5")
    BLEU_ALT   = rc.HexColor("#eef4fb")
    GRIS_LABEL = rc.HexColor("#4a4a4a")
    VERT       = rc.HexColor("#1e7e34")
    VERT_BG    = rc.HexColor("#e6f4ea")
    ORANGE     = rc.HexColor("#d97706")
    ORANGE_BG  = rc.HexColor("#fff7ed")
    BORDER     = rc.HexColor("#b0c8e0")
    WHITE      = rc.white
    BLACK      = rc.HexColor("#1a1a1a")

    RANK_FG = [VERT,    BLEU_SEC, ORANGE]
    RANK_BG = [VERT_BG, BLEU_ALT, ORANGE_BG]
    RANK_LB = ["1er CHOIX — RECOMMANDE", "2eme CHOIX", "3eme CHOIX"]

    CW = 182 * mm  # largeur utile

    # ── Helpers ───────────────────────────────────────────────────────────────
    def P(t, sz=9, bold=False, color=None, align=TA_LEFT, italic=False):
        if color is None: color = BLACK
        fn = ("Helvetica-BoldOblique" if bold and italic else
              "Helvetica-Bold"        if bold else
              "Helvetica-Oblique"     if italic else "Helvetica")
        return Paragraph(str(t), ParagraphStyle(
            "x", fontSize=sz, fontName=fn,
            textColor=color, alignment=align, leading=sz + 4
        ))

    def section(title, color=None):
        if color is None: color = BLEU_SEC
        t = Table([[P(f"  {title}", 9, bold=True, color=WHITE)]], colWidths=[CW])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), color),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    def row2(label, value, alt=False):
        t = Table(
            [[P(label, 8, bold=True, color=BLEU_TITRE), P(str(value) if value else "—", 9)]],
            colWidths=[45 * mm, CW - 45 * mm]
        )
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), BLEU_LIGHT),
            ("BACKGROUND",    (1, 0), (1, 0), BLEU_ALT if alt else WHITE),
            ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ]))
        return t

    # ── Construction du document ──────────────────────────────────────────────
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            leftMargin=14 * mm, rightMargin=14 * mm)
    story = []

    # ── En-tête ───────────────────────────────────────────────────────────────
    story.append(Table([[
        P("NOVEC", 20, bold=True, color=BLEU_TITRE),
        P(f"BON DE COMMANDE\nRef. {demand_id}  |  {datetime.now().strftime('%d/%m/%Y')}",
          9, color=GRIS_LABEL, align=TA_RIGHT),
    ]], colWidths=[80 * mm, CW - 80 * mm], style=[
        ("LINEBELOW",     (0, 0), (-1, -1), 2, BLEU_TITRE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(Spacer(1, 4 * mm))

    # ── Section 1 : Détails de la commande ───────────────────────────────────
    story.append(section("1.  DETAILS DE LA COMMANDE"))
    fields = [
        ("Demandeur",     demand.get("demandeur") or "—"),
        ("Responsable",   demand.get("responsable") or "—"),
        ("Service",       demand.get("service") or "—"),
        ("Date",          demand.get("date_demande") or datetime.now().strftime("%d/%m/%Y")),
        ("Produit",       demand.get("type_produit") or "—"),
        ("Categorie",     demand.get("categorie") or "—"),
        ("Quantite",      f"{demand.get('quantite', 1)} unite(s)"),
        ("Budget max",    f"{demand['budget_max']:.2f} DH" if demand.get("budget_max") else "Non precise"),
        ("Budget alloue", f"{demand['budget_alloue']:.2f} DH" if demand.get("budget_alloue") else "Non precise"),
        ("Delai max",     f"{demand['delai_max_jours']} jours" if demand.get("delai_max_jours") else "Non precise"),
        ("Localisation",  demand.get("localisation") or "Non precisee"),
        ("Conditions",    demand.get("conditions") or "Aucune"),
    ]
    for i, (lbl, val) in enumerate(fields):
        story.append(row2(lbl, val, i % 2 == 1))
    story.append(Spacer(1, 5 * mm))

    # ── Section 2 : Fournisseurs (tableau comparatif uniquement) ─────────────
    story.append(section(f"2.  FOURNISSEURS SELECTIONNES  ({len(top)} / 3)"))
    story.append(Spacer(1, 2 * mm))

    if not top:
        story.append(P("Aucun fournisseur eligible identifie.", italic=True, color=GRIS_LABEL))
    else:
        col_w = [22 * mm, 38 * mm, 28 * mm, 24 * mm, 14 * mm, CW - 126 * mm]
        rows_cmp = [[
            P("Rang / Statut",               8, bold=True, color=WHITE, align=TA_CENTER),
            P("Nom du fournisseur",           8, bold=True, color=WHITE, align=TA_CENTER),
            P("Niveau de prix",               8, bold=True, color=WHITE, align=TA_CENTER),
            P("Delai livraison",              8, bold=True, color=WHITE, align=TA_CENTER),
            P("Score",                        8, bold=True, color=WHITE, align=TA_CENTER),
            P("Observations / Justification", 8, bold=True, color=WHITE, align=TA_CENTER),
        ]]
        for i, s in enumerate(top):
            fg  = RANK_FG[i] if i < 3 else BLEU_SEC
            lbl = RANK_LB[i] if i < 3 else f"Rang {s.get('rank', i + 1)}"
            rows_cmp.append([
                P(lbl,                         8, bold=True, color=fg,    align=TA_CENTER),
                P(s.get("supplier_name", "—"), 9, bold=True, color=BLACK),
                P(str(s.get("price_level", "—")).capitalize(), 9, color=BLACK, align=TA_CENTER),
                P(f"{s.get('delivery_time_days', '—')} jours",  9, color=BLACK, align=TA_CENTER),
                P(f"{s.get('score_percent', '—')}%", 9, bold=True, color=fg, align=TA_CENTER),
                P(s.get("justification", "—"), 8, italic=True),
            ])

        tbl = Table(rows_cmp, colWidths=col_w)
        ts  = [
            ("BACKGROUND", (0, 0), (-1, 0), BLEU_TITRE),
            ("GRID",       (0, 0), (-1, -1), 0.4, BORDER),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ]
        for i in range(len(top)):
            ts.append(("BACKGROUND", (0, i + 1), (-1, i + 1), RANK_BG[i] if i < 3 else BLEU_ALT))
        tbl.setStyle(TableStyle(ts))
        story.append(tbl)
        story.append(Spacer(1, 2 * mm))

        # Bandeau fournisseur retenu
        s1 = top[0]
        story.append(Table([[
            P(f"Fournisseur retenu : {s1.get('supplier_name', '—')}  |  "
              f"Score {s1.get('score_percent', '—')}%  |  "
              f"Delai {s1.get('delivery_time_days', '—')} jours  |  "
              f"Note {float(s1.get('rating', 0)):.1f}/5",
              9, bold=True, color=VERT)
        ]], colWidths=[CW], style=[
            ("BACKGROUND",    (0, 0), (-1, -1), VERT_BG),
            ("LINEABOVE",     (0, 0), (-1, -1), 1.5, VERT),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        story.append(Spacer(1, 5 * mm))

    # ── Section 3 : Imputation budgétaire ────────────────────────────────────
    story.append(section("3.  IMPUTATION BUDGETAIRE"))
    story.append(row2("Centre de cout", demand.get("conditions") or "—"))
    story.append(row2("Budget disponible",
                      f"{demand['budget_alloue']:.2f} DH" if demand.get("budget_alloue") else "Non precise",
                      alt=True))
    story.append(Spacer(1, 5 * mm))

    # ── Section 4 : Validation interne ───────────────────────────────────────
    story.append(section("4.  VALIDATION INTERNE"))
    story.append(Spacer(1, 2 * mm))

    tbl_val = Table([
        [
            P("Signature du demandeur",           8, bold=True, color=WHITE, align=TA_CENTER),
            P("Visa du responsable hierarchique", 8, bold=True, color=WHITE, align=TA_CENTER),
            P("Validation budgetaire (DAF)",      8, bold=True, color=WHITE, align=TA_CENTER),
        ],
        [
            P(demand.get("demandeur")   or "_______________", 10, bold=True, color=BLEU_TITRE, align=TA_CENTER),
            P(demand.get("responsable") or "_______________", 10, bold=True, color=BLEU_TITRE, align=TA_CENTER),
            P("H. Tazi",                                      10, bold=True, color=BLEU_TITRE, align=TA_CENTER),
        ],
        [
            P("Date : _______________",                                    8, color=GRIS_LABEL, align=TA_CENTER),
            P(f"Date : {demand.get('date_demande') or '_______________'}", 8, color=GRIS_LABEL, align=TA_CENTER),
            P(f"Date : {demand.get('date_demande') or '_______________'}", 8, color=GRIS_LABEL, align=TA_CENTER),
        ],
    ], colWidths=[CW / 3] * 3)
    tbl_val.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLEU_TITRE),
        ("BACKGROUND", (0, 1), (-1, 2), BLEU_ALT),
        ("GRID",       (0, 0), (-1, -1), 0.4, BORDER),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl_val)
    story.append(Spacer(1, 2 * mm))
    story.append(row2("Commentaire du responsable", demand.get("commentaire_validation") or "—"))
    story.append(Spacer(1, 5 * mm))

    # ── Section 5 : Décision finale ───────────────────────────────────────────
    story.append(section("5.  DECISION FINALE", color=rc.HexColor("#4a4a4a")))
    n1 = top[0]["supplier_name"] if len(top) > 0 else "—"
    n2 = top[1]["supplier_name"] if len(top) > 1 else "—"
    n3 = top[2]["supplier_name"] if len(top) > 2 else "—"
    decision_rows = [
        ("Decision",           "  [ ] Approuver       [ ] Rejeter       [ ] Complements requis"),
        ("Fournisseur retenu", f"  [ ] Rang 1 : {n1}    [ ] Rang 2 : {n2}    [ ] Rang 3 : {n3}"),
        ("Commentaires",       "\n\n\n"),
        ("Responsable",        "Nom : ___________________    Signature : ___________________"),
        ("Date de validation", "_____ / _____ / _______"),
    ]
    story.append(Table(
        [[P(l, 9, bold=True, color=BLEU_TITRE), P(v, 9)] for l, v in decision_rows],
        colWidths=[42 * mm, CW - 42 * mm],
        style=TableStyle([
            ("GRID",          (0, 0), (-1, -1), 0.5, BORDER),
            ("BACKGROUND",    (0, 0), (0, -1),  BLEU_LIGHT),
            ("ROWBACKGROUNDS",(1, 0), (1, -1),  [WHITE, BLEU_ALT]),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ])
    ))
    story.append(Spacer(1, 5 * mm))

    # ── Pied de page ──────────────────────────────────────────────────────────
    story.append(Table([[
        P("NOVEC  —  Gestion des Achats", 7, color=BLEU_TITRE),
        P(f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}  |  Ref. {demand_id}",
          7, color=GRIS_LABEL, align=TA_RIGHT),
    ]], colWidths=[100 * mm, CW - 100 * mm], style=[
        ("LINEABOVE",  (0, 0), (-1, -1), 1, BLEU_SEC),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    doc.build(story)
    return buf.getvalue()