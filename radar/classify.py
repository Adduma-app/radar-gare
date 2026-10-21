"""Classificazione locale: pertinenza per parole chiave e modalità di esecuzione."""
import unicodedata
from . import config as C


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode()
    return " ".join(t.lower().split())


def punteggio_kw(testo):
    t = norm(testo)
    pos = sum(w for k, w in C.KW_POSITIVE.items() if k in t)
    neg = sum(w for k, w in C.KW_NEGATIVE.items() if k in t)
    trovate = [k for k in C.KW_POSITIVE if k in t]
    escluse = [k for k in C.KW_NEGATIVE if k in t]
    return pos - neg, trovate, escluse


def esecuzione(testo):
    """Da remoto, trasferta breve (video/foto), evento in loco, presenza continuativa."""
    t = norm(testo)
    if any(k in t for k in C.KW_PRESENZA):
        return "presenza continuativa"
    if any(k in t for k in C.KW_EVENTO):
        return "evento in loco"
    if any(k in t for k in C.KW_VIDEO):
        return "trasferta breve"
    return "da remoto"


def classifica(rec):
    testo = " ".join(str(rec.get(k) or "") for k in ("titolo", "descrizione", "cpv"))
    s, trovate, escluse = punteggio_kw(testo)
    rec["kw_score"] = s
    rec["kw_trovate"] = trovate
    rec["kw_escluse"] = escluse
    rec["esecuzione"] = esecuzione(testo)
    imp = rec.get("importo")
    rec["fuori_taglia"] = bool(imp and imp > C.TAGLIA_SOSTENIBILE)
    motivo = None
    if s < C.SOGLIA_PERTINENZA:
        motivo = "parole chiave insufficienti" if not escluse else "oggetto fuori perimetro: " + ", ".join(escluse[:3])
    elif rec["esecuzione"] == "presenza continuativa":
        motivo = "richiede presenza continuativa presso l'ente"
    rec["pertinente"] = motivo is None
    rec["motivo_scarto"] = motivo
    return rec
