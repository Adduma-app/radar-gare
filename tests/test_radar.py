import unittest
from radar.classify import classifica, esecuzione
from radar.fetch_anac import normalizza

AVVISO = {  # forma reale dell'avviso ANAC (campione del 21/10/2026), dati inventati
    "idAvviso": "abc-123", "tipologia": "INDAGINI_DI_MERCATO_SOTTO_SOGLIA",
    "dataPubblicazione": "2026-10-20T10:00:00.988+00:00", "dataScadenza": "2026-11-05T12:00:00.000+00:00",
    "scoreDetails": {"description": "sum of:", "details": [{"description": "# clause"}]},
    "templates": [{"lingua": "it", "template": {
        "metadata": {"descrizione": "Realizzazione di un video promozionale del territorio"},
        "sections": [
            {"name": "SEZ. A - Committente", "fields": {"soggetti_sa": [
                {"codice_fiscale": "00000000000", "denominazione_amministrazione": "Comune di Esempio"}]}},
            {"name": "SEZ. B - Dati Generali", "fields": {"documenti_di_gara_link": "https://esempio.it/gara",
                                                          "tipo_procedura_aggiudicazione": "Aperta"}},
            {"name": "SEZ. C - Oggetto", "items": [{"cig": "B000000001", "valore_complessivo_stimato": 38000.0,
                "descrizione": "Video promozionale", "cpv": "Servizi di produzione di film e video",
                "luogo_istat": "ALCAMO", "categorie": [{"descrizione": "FORNITURA DI SERVIZI"}]}]}]}}],
}


class TestRadar(unittest.TestCase):
    def test_normalizza(self):
        r = normalizza(AVVISO)
        self.assertEqual(r["id"], "anac:abc-123")
        self.assertEqual(r["ente"], "Comune di Esempio")
        self.assertEqual(r["importo"], 38000)
        self.assertTrue(r["scadenza"].startswith("2026-11-05"))
        self.assertEqual(r["link_documenti"], "https://esempio.it/gara")
        self.assertEqual(r["titolo"], "Realizzazione di un video promozionale del territorio")
        self.assertEqual(r["procedura"], "Aperta")
        self.assertEqual(r["luogo_istat"], "ALCAMO")

    def test_pertinente_video(self):
        r = classifica(normalizza(AVVISO))
        self.assertTrue(r["pertinente"])
        self.assertEqual(r["esecuzione"], "trasferta breve")
        self.assertFalse(r["fuori_taglia"])

    def test_scarta_pulizia(self):
        r = classifica({"titolo": "Servizio di pulizia e manutenzione del verde", "descrizione": "", "cpv": ""})
        self.assertFalse(r["pertinente"])

    def test_scarta_concessione_spazi(self):
        r = classifica({"titolo": "Concessione degli impianti pubblicitari comunali", "descrizione": "", "cpv": "Servizi pubblicitari"})
        self.assertFalse(r["pertinente"])

    def test_presenza(self):
        self.assertEqual(esecuzione("Ufficio stampa con presidio presso la sede comunale"), "presenza continuativa")
        self.assertEqual(esecuzione("Ideazione immagine coordinata e campagna social"), "da remoto")
        self.assertEqual(esecuzione("Organizzazione eventi natalizi"), "evento in loco")


if __name__ == "__main__":
    unittest.main()
