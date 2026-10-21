import unittest
from radar.classify import classifica, esecuzione
from radar.fetch_anac import normalizza

AVVISO = {
    "idAvviso": "abc-123", "tipologia": "INDAGINI_DI_MERCATO_SOTTO_SOGLIA",
    "dataPubblicazione": "2026-10-20T10:00:00", "dataScadenza": "2026-11-05T12:00:00",
    "templates": [{"template": {"metadata": {"titolo": "Realizzazione di un video promozionale del territorio"},
        "sections": [
            {"name": "SEZ. A", "items": [{"denominazione_amministrazione": "Comune di Esempio", "codice_fiscale": "00000000000"}]},
            {"name": "SEZ. C", "items": [{"cig": "B000000001", "valore_complessivo_stimato": 38000,
                                          "cpv": "Servizi di produzione di film e video", "luogo_istat": "081001",
                                          "documenti_di_gara_link": "https://esempio.it/gara"}]}]}}],
}


class TestRadar(unittest.TestCase):
    def test_normalizza(self):
        r = normalizza(AVVISO)
        self.assertEqual(r["id"], "anac:abc-123")
        self.assertEqual(r["ente"], "Comune di Esempio")
        self.assertEqual(r["importo"], 38000)
        self.assertTrue(r["scadenza"].startswith("2026-11-05"))
        self.assertEqual(r["link_documenti"], "https://esempio.it/gara")

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
