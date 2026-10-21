"""Lettura degli avvisi dalla Piattaforma di Pubblicità a valore legale di ANAC.

Endpoint pubblico, senza autenticazione, usato dalla ricerca avanzata del portale:
GET https://pubblicitalegale.anticorruzione.it/api/v0/avvisi-full-text-specializzata
Non è documentato ufficialmente: per questo il parsing cerca i campi per nome
in tutta la struttura invece di dipendere da un percorso fisso, e un campione
grezzo viene salvato in data/anac_campione.json per controllare lo schema.
"""
import json, time, urllib.parse, urllib.request
from datetime import date, datetime, timedelta
from . import config as C

BASE = "https://pubblicitalegale.anticorruzione.it/api/v0/avvisi-full-text-specializzata"
HEADERS = {
    "User-Agent": "RadarGareAdduma/1.0 (+https://github.com/Adduma-app/radar-gare)",
    "Accept": "application/json",
    "Accept-Language": "it-IT,it;q=0.9",
}


def _get(params, tentativi=3):
    url = BASE + "?" + urllib.parse.urlencode(params, safe=",/")
    for i in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as ex:  # rete, timeout, JSON non valido
            if i == tentativi - 1:
                raise RuntimeError(f"ANAC non raggiungibile ({ex}) per {url}")
            time.sleep(3 * (i + 1))


def _walk(o, out):
    """Appiattisce la struttura: chiave -> lista dei valori trovati."""
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                _walk(v, out)
            elif v not in (None, ""):
                out.setdefault(k.lower(), []).append(v)
    elif isinstance(o, list):
        for x in o:
            _walk(x, out)
    return out


def _primo(f, *chiavi):
    for k in chiavi:
        if f.get(k):
            return f[k][0]
    return None


def _num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace("€", "").replace(" ", "").replace(".", "").replace(",", ".")) \
            if isinstance(v, str) and "," in v else float(v)
    except ValueError:
        return None


def _data(v):
    if not v:
        return None
    if isinstance(v, (int, float)):  # epoch in millisecondi
        return datetime.utcfromtimestamp(v / 1000).isoformat(timespec="minutes")
    s = str(v).strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "")[:19]).isoformat(timespec="minutes")
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:16] if "%H" in fmt else s[:10], fmt).isoformat(timespec="minutes")
        except ValueError:
            continue
    return s


def normalizza(a):
    f = _walk(a, {})
    id_avv = a.get("idAvviso") or _primo(f, "idavviso", "id")
    importi = [x for x in (_num(v) for v in f.get("valore_complessivo_stimato", []) + f.get("importo", [])) if x]
    return {
        "id": f"anac:{id_avv}",
        "fonte": "ANAC PVL",
        "tipologia": a.get("tipologia") or _primo(f, "tipologia"),
        "titolo": _primo(f, "titolo", "oggetto", "oggetto_appalto", "descrizione_breve", "denominazione_procedura"),
        "descrizione": _primo(f, "descrizione", "oggetto_lotto", "descrizione_lotto"),
        "ente": _primo(f, "denominazione_amministrazione", "denominazione", "stazione_appaltante", "ragione_sociale"),
        "cf_ente": _primo(f, "codice_fiscale", "cf_amministrazione"),
        "luogo_istat": _primo(f, "luogo_istat", "codice_istat"),
        "luogo_nuts": _primo(f, "luogo_nuts", "nuts"),
        "importo": max(importi) if importi else None,
        "lotti": len(f.get("cig", [])) or None,
        "cig": f.get("cig", [])[:5],
        "cpv": _primo(f, "cpv"),
        "procedura": _primo(f, "tipo_procedura", "procedura", "tipologia_procedura"),
        "pubblicazione": _data(a.get("dataPubblicazione") or _primo(f, "datapubblicazione")),
        "scadenza": _data(a.get("dataScadenza") or _primo(f, "termine_ricezione_offerte", "termine_invito", "datascadenza")),
        "link_avviso": f"https://pubblicitalegale.anticorruzione.it/bandi/{id_avv}",
        "link_documenti": _primo(f, "documenti_di_gara_link", "url_documentazione", "link"),
        "aggiudicatari": f.get("denominazione_aggiudicatario", [])[:3] or f.get("aggiudicatari", [])[:3],
        "valore_aggiudicato": _num(_primo(f, "valore_offerta_vincente", "importo_aggiudicazione")),
    }


def scarica(oggi=None, giorni=C.GIORNI_FINESTRA):
    oggi = oggi or date.today()
    inizio = (oggi - timedelta(days=giorni)).strftime("%d/%m/%Y")
    fine = oggi.strftime("%d/%m/%Y")
    visti, grezzi, errori = {}, [], []
    cpv = sorted(C.CPV_PREFISSI)
    for i in range(0, len(cpv), C.CPV_PER_CHIAMATA):
        gruppo = ",".join(cpv[i:i + C.CPV_PER_CHIAMATA])
        for pagina in range(C.MAX_PAGINE):
            params = {"page": pagina, "pageSize": C.PAGE_SIZE, "dataPubblicazioneStart": inizio,
                      "dataPubblicazioneEnd": fine, "cpv": gruppo, "sortField": "dataPubblicazione",
                      "sortDirection": "desc", "operatore": "AND"}
            try:
                r = _get(params)
            except RuntimeError as ex:
                errori.append(str(ex))
                break
            content = r.get("content") or []
            if not content:
                break
            for a in content:
                if len(grezzi) < 3:
                    grezzi.append(a)
                rec = normalizza(a)
                visti[rec["id"]] = rec
            if (pagina + 1) * C.PAGE_SIZE >= int(r.get("count") or 0):
                break
            time.sleep(0.7)
    return list(visti.values()), grezzi, errori
