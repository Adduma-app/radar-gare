"""Configurazione del Radar gare Adduma: codici CPV, parole chiave, soglie."""

# Prefissi CPV interrogati su ANAC (filtro lato server). Da 3 a 8 cifre.
CPV_PREFISSI = [
    "79340", "79341", "79342",          # pubblicità e marketing
    "79413", "79416",                   # consulenza marketing, pubbliche relazioni
    "79822", "79823",                   # progettazione grafica, impaginazione
    "79950", "79951", "79952", "79954", "79956",  # eventi, fiere, feste
    "79960", "79961",                   # servizi fotografici
    "92100", "92110", "92111", "92112", # produzione film e video
    "92221",                            # produzione programmi televisivi
    "72413",                            # progettazione siti web
]
CPV_PER_CHIAMATA = 10   # chiamate corte: un errore resta isolato
GIORNI_FINESTRA = 10    # quanti giorni di pubblicazioni leggere a ogni esecuzione
PAGE_SIZE = 100
MAX_PAGINE = 40

# Parole che confermano la pertinenza (cercate in oggetto e descrizione, minuscolo, senza accenti)
KW_POSITIVE = {
    "video": 3, "audiovisiv": 3, "filmat": 3, "documentari": 3, "spot": 3, "riprese": 2,
    "cortometraggi": 2, "videoclip": 3, "reel": 2,
    "grafic": 3, "immagine coordinata": 4, "brand": 3, "logo": 2, "marchio": 1, "identita visiva": 4,
    "comunicazione": 2, "campagna": 3, "promozion": 2, "pubblicit": 2, "marketing": 2,
    "social": 3, "sito web": 3, "sito internet": 3, "portale web": 1, "web design": 3,
    "evento": 2, "eventi": 2, "manifestazion": 1, "allestiment": 2, "fiera": 1, "stand": 1,
    "ufficio stampa": 2, "contenuti multimediali": 3, "multimedial": 2, "fotograf": 2,
    "packaging": 3, "infografic": 3, "storytelling": 3, "valorizzazione turistica": 2,
}
# Parole che indicano un oggetto fuori perimetro (pesano in negativo)
KW_NEGATIVE = {
    "lavori": 4, "manutenzione": 3, "pulizia": 5, "ristorazione": 5, "catering": 2, "mensa": 5,
    "vigilanza": 5, "portierato": 5, "trasporto": 3, "noleggio": 2, "fornitura di": 2,
    "gadget": 4, "cancelleria": 5, "tipografic": 3, "stampa di": 2, "affissione": 3,
    "concessione": 4, "spazi pubblicitari": 4, "impianti pubblicitari": 5,
    "software": 3, "hardware": 4, "licenze": 3, "assistenza tecnica": 2, "sanitari": 4,
    "farmac": 4, "carburant": 5, "assicurativ": 5, "brokeraggio": 5, "tesoreria": 5,
    "luminarie": 4, "fuochi": 4, "service audio": 1, "sorveglianza": 4, "smaltimento": 5,
}
SOGLIA_PERTINENZA = 2   # punteggio parole chiave minimo per entrare nel radar

# Esecuzione: cosa obbliga a stare sul posto
KW_PRESENZA = ["presso la sede", "presidio", "in presenza", "postazione presso", "personale dedicato presso",
               "distacco", "front office", "sportello", "addetto stampa presso", "in loco per tutta"]
KW_EVENTO = ["evento", "eventi", "manifestazion", "allestiment", "fiera", "stand", "festival", "convegno"]
KW_VIDEO = ["video", "audiovisiv", "riprese", "documentari", "spot", "filmat", "fotograf"]

TIPOLOGIE_OPPORTUNITA = {"BANDI", "INDAGINI_DI_MERCATO_SOTTO_SOGLIA", "AVVISI_PREINFORMAZIONE",
                          "AVVISI", "PREINFORMAZIONE", "ELENCHI", "SISTEMI_QUALIFICAZIONE"}
TIPOLOGIE_ESITO = {"RISULTATI", "ESITI", "AGGIUDICAZIONI"}
# tipologie che non sono né opportunità né esiti utili
TIPOLOGIE_ESCLUSE = {"MODIFICHE_CONTRATTUALI", "MODIFICHE", "RETTIFICHE_ESITO"}

TAGLIA_SOSTENIBILE = 300_000
