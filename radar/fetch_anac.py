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
    """Appiattisce la struttura: chiave -> lista dei valori trovati (esclusi i metadati di ricerca)."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("scoreDetails", "categorie", "aggiudicatari"):
                continue
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


def _template(a):
    try:
        return a["templates"][0]["template"]
    except (KeyError, IndexError, TypeError):
        return {}


def _sezione(t, prefisso):
    for sez in t.get("sections") or []:
        if str(sez.get("name", "")).upper().startswith(prefisso):
            return sez
    return {}


def normalizza(a):
    f = _walk(a, {})
    t = _template(a)
    meta = t.get("metadata") or {}
    sez_a = (_sezione(t, "SEZ. A").get("fields") or {})
    sez_b = (_sezione(t, "SEZ. B").get("fields") or {})
    lotti = _sezione(t, "SEZ. C").get("items") or []
    sa = (sez_a.get("soggetti_sa") or [{}])[0]
    id_avv = a.get("idAvviso") or _primo(f, "idavviso")
    importi = [x for x in (_num(l.get("valore_complessivo_stimato")) for l in lotti) if x]
    aggiudicatari = [s.get("denominazione") for l in lotti for ag in (l.get("aggiudicatari") or [])
                     for s in (ag.get("soggetti") or []) if s.get("denominazione")]
    vincenti = [x for x in (_num(l.get("valore_offerta_vincente")) for l in lotti) if x]
    desc_lotto = next((l.get("descrizione") for l in lotti if l.get("descrizione")), None)
    scad_lotto = next((l.get(k) for l in lotti for k in ("termine_ricezione_offerte", "termine_invito") if l.get(k)), None)
    return {
        "id": f"anac:{id_avv}",
        "fonte": "ANAC PVL",
        "tipologia": a.get("tipologia"),
        "titolo": meta.get("titolo") or meta.get("descrizione") or desc_lotto,
        "descrizione": meta.get("descrizione") or desc_lotto,
        "ente": sa.get("denominazione_amministrazione") or _primo(f, "denominazione_amministrazione"),
        "cf_ente": sa.get("codice_fiscale"),
        "luogo_istat": next((l.get("luogo_istat") for l in lotti if l.get("luogo_istat")), None),
        "luogo_nuts": next((l.get("luogo_nuts") for l in lotti if l.get("luogo_nuts")), None),
        "importo": sum(importi) if importi else None,
        "lotti": len(lotti) or None,
        "cig": [l.get("cig") for l in lotti if l.get("cig")][:5],
        "cpv": next((l.get("cpv") for l in lotti if l.get("cpv")), None),
        "procedura": sez_b.get("tipo_procedura_aggiudicazione") or _primo(f, "tipo_procedura_aggiudicazione", "tipo_procedura"),
        "pubblicazione": _data(a.get("dataPubblicazione")),
        "scadenza": _data(a.get("dataScadenza") or scad_lotto or _primo(f, "termine_ricezione_offerte", "termine_invito")),
        "link_avviso": f"https://pubblicitalegale.anticorruzione.it/bandi/{id_avv}",
        "link_documenti": sez_b.get("documenti_di_gara_link") or _primo(f, "documenti_di_gara_link"),
        "link_ted": meta.get("link_eform_ted"),
        "aggiudicatari": aggiudicatari[:3],
        "valore_aggiudicato": sum(vincenti) if vincenti else None,
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
