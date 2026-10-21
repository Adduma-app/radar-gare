"""Esecuzione notturna: scarica, classifica, aggiorna lo storico e pubblica i file in docs/."""
import json, sys
from datetime import date, datetime, timedelta
from pathlib import Path
from . import config as C
from .classify import classifica
from .fetch_anac import scarica

ROOT = Path(__file__).resolve().parent.parent
DATA, DOCS = ROOT / "data", ROOT / "docs"


def _load(p, default):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def _save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1))


def _euro(x):
    return "n.d." if not x else f"{x:,.0f} €".replace(",", ".")


def _gg(iso):
    return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M") if iso and iso[:4].isdigit() else (iso or "n.d.")


def main(oggi=None):
    oggi = oggi or date.today()
    record, grezzi, errori = scarica(oggi)
    if grezzi:
        _save(DATA / "anac_campione.json", grezzi)
    storico = _load(DATA / "storico.json", {})
    nuovi = 0
    for r in record:
        classifica(r)
        if not r["pertinente"]:
            continue
        prec = storico.get(r["id"])
        r["primo_avvistamento"] = prec["primo_avvistamento"] if prec else oggi.isoformat()
        nuovi += prec is None
        storico[r["id"]] = r
    # pulizia: tieni 400 giorni
    limite = (oggi - timedelta(days=400)).isoformat()
    storico = {k: v for k, v in storico.items() if (v.get("pubblicazione") or v["primo_avvistamento"]) >= limite}
    _save(DATA / "storico.json", storico)

    oggi_iso = oggi.isoformat()
    aperte = [r for r in storico.values() if r["pertinente"] and (r.get("tipologia") or "").upper() not in C.TIPOLOGIE_ESITO
              and (not r.get("scadenza") or r["scadenza"][:10] >= oggi_iso)
              and (r.get("pubblicazione") or r["primo_avvistamento"])[:10] >= (oggi - timedelta(days=30)).isoformat()]
    aperte.sort(key=lambda r: (r.get("scadenza") or "9999"))
    esiti = [r for r in storico.values() if r["pertinente"] and (r.get("tipologia") or "").upper() in C.TIPOLOGIE_ESITO]
    esiti.sort(key=lambda r: r.get("pubblicazione") or "", reverse=True)
    scartati = [r for r in record if not r["pertinente"]]

    stato = {"aggiornato": datetime.now().isoformat(timespec="minutes"), "letti_oggi": len(record),
             "nuovi_oggi": nuovi, "aperte_pertinenti": len(aperte), "esiti_pertinenti": len(esiti),
             "scartati_oggi": len(scartati), "errori": errori}
    _save(DOCS / "data.json", {"stato": stato, "gare": aperte})
    _save(DOCS / "esiti.json", {"stato": stato, "esiti": esiti[:500]})

    # Versione testuale compatta, pensata per essere letta dall'attività programmata
    righe = [f"# Radar gare Adduma, aggiornato {stato['aggiornato']}",
             f"Letti oggi {len(record)}, nuovi {nuovi}, gare aperte pertinenti {len(aperte)}. Errori: {len(errori)}", ""]
    for r in aperte:
        righe += [f"## {r.get('titolo') or 'senza titolo'}",
                  f"- ente: {r.get('ente') or 'n.d.'} | luogo ISTAT {r.get('luogo_istat') or 'n.d.'}",
                  f"- tipologia: {r.get('tipologia')} | procedura: {r.get('procedura') or 'n.d.'}",
                  f"- importo: {_euro(r.get('importo'))}{' (FUORI TAGLIA)' if r['fuori_taglia'] else ''} | lotti: {r.get('lotti') or 'n.d.'}",
                  f"- pubblicato: {_gg(r.get('pubblicazione'))} | scadenza: {_gg(r.get('scadenza'))} | primo avvistamento: {r['primo_avvistamento']}",
                  f"- esecuzione: {r['esecuzione']} | parole chiave: {', '.join(r['kw_trovate'][:6])}",
                  f"- avviso: {r['link_avviso']}", f"- documenti: {r.get('link_documenti') or 'n.d.'}", ""]
    (DOCS / "radar.md").write_text("\n".join(righe))
    print(json.dumps(stato, ensure_ascii=False))
    if not record and errori:
        sys.exit(1)


if __name__ == "__main__":
    main()
