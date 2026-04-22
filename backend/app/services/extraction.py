"""
Extraction de données depuis texte libre et PDF.
Modifiez ici les regex d'extraction ou ajoutez de nouveaux champs.
"""
import re
from datetime import datetime
from app.core.config import CATEGORY_KEYWORDS


# ── Helpers numériques ────────────────────────────────────────────────────────

def _parse_number(s) -> float | None:
    if not s:
        return None
    try:
        return float(str(s).replace("\u202f", "").replace("\xa0", "")
                    .replace(" ", "").replace(",", "."))
    except Exception:
        return None


def _detect_category(text: str) -> str:
    """Détecte la catégorie produit à partir des mots-clés."""
    tl = text.lower()
    for cat, words in CATEGORY_KEYWORDS.items():
        if any(w in tl for w in words):
            return cat
    return "Autre"


# ── Extraction texte libre ────────────────────────────────────────────────────

def extract_from_text(text: str) -> dict:
    """Extraction rapide depuis un texte non structuré (formulaire manuel)."""
    tl = text.lower()

    # Produit
    produit = None
    for pat in [r"produit\s*:?\s*(.+?)(?:\n|$)",
                r"article\s*:?\s*(.+?)(?:\n|$)",
                r"objet\s*:?\s*(.+?)(?:\n|$)"]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            produit = m.group(1).strip()[:120]
            break

    # Budget
    budget = None
    for pat in [r"(\d[\d\s]*(?:[,\.]\d+)?)\s*(?:DH|MAD|dh)",
                r"budget\s*(?:max(?:imum)?)?\s*:?\s*([\d\s,\.]+)"]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1).replace(" ", "").replace(",", "."))
                if val > 0:
                    budget = val
                    break
            except Exception:
                pass

    # Quantité
    qty = 1
    m = re.search(r"(\d+)\s*(?:unites?|pieces?|lots?|pc|kg|licences?)", text, re.IGNORECASE)
    if m:
        qty = int(m.group(1))

    # Délai
    delay = None
    m = re.search(r"(\d+)\s*jours?", text, re.IGNORECASE)
    if m and 1 <= int(m.group(1)) <= 365:
        delay = int(m.group(1))

    return {
        "type_produit":    produit or "A preciser",
        "categorie":       _detect_category(text),
        "quantite":        qty,
        "budget_max":      budget,
        "delai_max_jours": delay,
        "localisation":    None,
        "conditions":      None,
        "demandeur":       None,
        "service":         None,
        "confiance":       0.35,
    }


# ── Extraction PDF structurée ─────────────────────────────────────────────────

def _extract_budget_alloue(text: str) -> float | None:
    """Extrait le budget disponible/alloué — exige DH explicite."""
    for pat in [
        r"budget\s*disponible\s*:\s*([\d][\d\s,\.]*)\s*(?:DH|MAD|dh)",
        r"budget\s*alloue\s*:\s*([\d][\d\s,\.]*)\s*(?:DH|MAD|dh)",
        r"enveloppe\s*(?:budg[e\u00e9]taire)?\s*:\s*([\d][\d\s,\.]*)\s*(?:DH|MAD|dh)",
        r"dotation\s*:\s*([\d][\d\s,\.]*)\s*(?:DH|MAD|dh)",
        r"montant\s*alloue\s*:\s*([\d][\d\s,\.]*)\s*(?:DH|MAD|dh)",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = _parse_number(m.group(1))
            if val and val > 10:
                return val
    return None


def extract_from_pdf(text: str) -> dict:
    """Extraction intelligente depuis une fiche de demande d'achat PDF."""
    result = {}

    # 1. Demandeur
    for pat in [
        r"nom du demandeur\s*:\s*([A-Za-z\u00C0-\u017E][^\n]{2,50}?)\s{2,}",
        r"nom du demandeur\s*:\s*([A-Za-z\u00C0-\u017E][^\n]{2,50}?)(?:\s+service|\s+poste|\s+d[e\u00e9])",
        r"[e\u00e9]tabli par\s*:\s*([^\n:]{3,50})",
        r"pr[e\u00e9]par[e\u00e9] par\s*:\s*([^\n:]{3,50})",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val and len(val) > 2 and ":" not in val:
                result["demandeur"] = val
                break
    if not result.get("demandeur"):
        sig_m = re.search(r"(?:Signature du demandeur|demandeur).*?\n([A-Z][^\n]{3,60})", text, re.IGNORECASE)
        if sig_m:
            names = re.findall(r"[A-Z][a-z\u00C0-\u017E]*\.?\s+[A-Za-z\u00C0-\u017E][a-z\u00C0-\u017E]+", sig_m.group(1))
            if names:
                result["demandeur"] = names[0]

    # 2. Responsable / Visa
    result["responsable"] = _extract_visa(text, result)

    # 3. Service
    for pat in [
        r"service\s*/\s*d[e\u00e9]partement\s*:\s*(.+?)(?=\n|$)",
        r"d[e\u00e9]partement\s*:\s*(.+?)(?=\n|$)",
        r"service\s*:\s*([A-Za-z\u00C0-\u017E][^\n]{2,60})",
        r"direction\s*:\s*([A-Za-z\u00C0-\u017E][^\n]{2,60})",
    ]:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            if val and len(val) > 2 and ":" not in val[:20]:
                result["service"] = val
                break

    # 4. Produit
    m = re.search(r"description\s*:\s*(.+?)(?:\nQuantit|\n\n|\n[0-9]+\.)", text, re.IGNORECASE | re.DOTALL)
    if m:
        result["type_produit"] = re.sub(r"\s+", " ", m.group(1)).strip()[:150]
    else:
        m2 = re.search(r"Nature de l.achat\s*:?\s*(.+?)(?:\n)", text, re.IGNORECASE)
        if m2:
            checked = re.findall(r"\u25a0\s+([^\u25a0\n]+?)(?=\s*\u25a0|\s*$)", m2.group(1))
            if checked:
                result["type_produit"] = " / ".join(c.strip() for c in checked[:3])

    # 5. Quantité
    qty = 1
    for pat in [
        r"(\d+)\s*articles?\s*\(",
        r"(\d+)\s*(?:unit[e\u00e9]s?|pi[e\u00e8]ces?|lots?|exemplaires?)",
        r"quantit[e\u00e9]\s+demand[e\u00e9]e\s*\n?\s*(\d+)",
        r"quantit[e\u00e9]\s*:\s*(\d+)",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                qty = max(1, int(m.group(1))); break
            except Exception:
                pass
    result["quantite"] = qty

    # 6. Budget demandé
    budget = None
    m = re.search(r"(\d[\d\s,\.]+)\s*DH\s+(\d[\d\s,\.]+)\s*DH\s+\d{1,2}/\d{1,2}/", text, re.IGNORECASE)
    if m:
        budget = _parse_number(m.group(2))
    if not budget:
        for pat in [
            r"co[u\u00fb]t total\s*(?:estim[e\u00e9])?\s*:?\s*([\d\s,\.]+)\s*(?:DH|MAD)",
            r"montant total\s*:?\s*([\d\s,\.]+)\s*(?:DH|MAD)",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                budget = _parse_number(m.group(1))
                if budget: break
    if not budget:
        amounts = [_parse_number(a) for a in re.findall(r"(\d[\d\s]*[,\.]\d{2})\s*DH", text, re.IGNORECASE)]
        valid = [a for a in amounts if a and a > 0]
        if valid:
            budget = max(valid)
    result["budget_max"]    = budget
    result["budget_alloue"] = _extract_budget_alloue(text)

    # 7. Délai
    result["delai_max_jours"] = _extract_delay(text)

    # 8. Date
    m = re.search(r"(?:Date\s*:\s*|[—\-]\s*Date\s*:\s*)(\d{1,2}/\d{1,2}/\d{4})", text[:300])
    result["date_demande"] = m.group(1) if m else None

    # 9. Catégorie
    result["categorie"]    = _detect_category(text)
    result["localisation"] = "Maroc"

    # 10. Conditions / commentaire
    for pat in [
        r"commentaire.*?:\s*(.+?)(?:\n\n|$)",
        r"motif.*?:\s*(.+?)(?:\n\n|[0-9]+\.|$)",
    ]:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            cond = re.sub(r"\s+", " ", m.group(1)).strip()[:200]
            if len(cond) > 5:
                result["conditions"] = cond
                break

    result["confiance"] = 0.80
    return result


def _extract_visa(text: str, result: dict) -> str | None:
    """Extrait le visa du responsable hiérarchique depuis le bloc de signatures."""
    visa            = None
    sig_block_found = False

    val_m = re.search(
        r"Signature du demandeur\s*\n"
        r"Visa du responsable hi[eé]rarchique\s*\n"
        r"Validation budg[eé]taire[^\n]*\n"
        r"([^\n]+)\n([^\n]*)\n([^\n]*)\n",
        text, re.IGNORECASE
    )
    if val_m:
        sig_block_found = True
        sigs = [s.strip() for s in [val_m.group(1), val_m.group(2), val_m.group(3)]
                if s.strip() and not s.strip().lower().startswith("date")]
        demandeur_low = str(result.get("demandeur") or "").strip().lower()

        def _matches(sig: str) -> bool:
            sig_l = sig.lower()
            for part in demandeur_low.split():
                if len(part) > 2 and part in sig_l:
                    return True
            if demandeur_low:
                initiale = demandeur_low.split()[0][0] + "."
                if sig_l.startswith(initiale):
                    return True
            return False

        if len(sigs) == 3:
            visa = sigs[1]
        elif len(sigs) == 2:
            if _matches(sigs[0]):
                visa = sigs[1]
            else:
                result["demandeur"] = None
                visa = sigs[0]
        elif len(sigs) == 1:
            if _matches(sigs[0]):
                visa = None
            else:
                result["demandeur"] = None
                visa = sigs[0]

    if not visa and not sig_block_found:
        val_m2 = re.search(
            r"Signature du demandeur\s+Visa du responsable hi.rarchique.*?\n([^\n]+)",
            text, re.IGNORECASE | re.DOTALL
        )
        if val_m2:
            sig_block_found = True
            pat_names = (r"[A-Z][a-z\u00C0-\u017E]*\.\s+[A-Za-z\u00C0-\u017E][a-z\u00C0-\u017E]+"
                         r"|[A-Z][a-z\u00C0-\u017E]{2,}\s+[A-Z][a-z\u00C0-\u017E]{2,}")
            all_names = re.findall(pat_names, val_m2.group(1).strip())
            if len(all_names) >= 2:
                visa = all_names[1]

    if not visa and not sig_block_found:
        for pat in [
            r"responsable.*hie.*archique\s*:\s*([A-Za-z\u00C0-\u017E][^\n:]{2,40})",
            r"approuve\s+par\s*:\s*([A-Za-z\u00C0-\u017E][^\n:]{2,40})",
            r"vise\s+par\s*:\s*([A-Za-z\u00C0-\u017E][^\n:]{2,40})",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if val and len(val) > 1 and "date" not in val.lower():
                    visa = val
                    break
    return visa


def _extract_delay(text: str) -> int | None:
    """Extrait le délai de livraison en jours."""
    m = re.search(r"date de livraison\s+souhait[e\u00e9]e?\s*\n?([\d/]+)", text, re.IGNORECASE)
    if m:
        try:
            deliv = datetime.strptime(m.group(1), "%d/%m/%Y")
            m2    = re.search(r"Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})", text[:300])
            if m2:
                req  = datetime.strptime(m2.group(1), "%d/%m/%Y")
                days = (deliv - req).days
                if 1 <= days <= 365:
                    return max(1, days)
        except Exception:
            pass
    m3 = re.search(r"(\d+)\s*jours?", text, re.IGNORECASE)
    if m3 and 1 <= int(m3.group(1)) <= 365:
        return int(m3.group(1))
    return None