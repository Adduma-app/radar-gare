# Radar gare Adduma

Ogni notte legge dalla Piattaforma di Pubblicità a valore legale di ANAC tutti i bandi, gli avvisi e le indagini di mercato pubblicati in Italia (ministeri, regioni, province, comuni, università, enti) con i codici CPV dei servizi di Adduma: comunicazione, pubblicità, grafica, video, fotografia, eventi, siti web.

Poi:
1. scarta gli oggetti fuori perimetro (pulizie, lavori, concessioni di spazi pubblicitari, gadget, stampa, IT, ecc.);
2. classifica l'esecuzione: **da remoto**, **trasferta breve** (video e foto), **evento in loco**, **presenza continuativa** (scartata);
3. segna come **fuori taglia** sopra 300.000 euro;
4. tiene uno storico e pubblica in `docs/`:
   - `data.json` gare aperte pertinenti (ultimi 30 giorni, scadenza futura)
   - `radar.md` la stessa lista in testo, letta dall'attività programmata di Claude che fa score e mail
   - `esiti.json` aggiudicazioni pertinenti, utili per sapere quali enti comprano video e comunicazione e da chi
   - `index.html` una pagina consultabile con filtro

## Attivazione (una volta sola)
1. Crea il repository **pubblico** `radar-gare` sull'account `Adduma-app` e carica questi file.
2. Settings > Pages: Source "Deploy from a branch", branch `main`, cartella `/docs`.
3. Tab Actions: abilita i workflow, apri "Radar gare" e premi **Run workflow** per la prima esecuzione.
4. Se il passo "Pubblica i risultati" fallisce per permessi: Settings > Actions > General > Workflow permissions > "Read and write permissions".

## Da controllare dopo la prima esecuzione
L'endpoint ANAC non è documentato ufficialmente. Dopo il primo giro aprire `data/anac_campione.json` (tre avvisi grezzi) e verificare che titolo, ente, importo e scadenza siano estratti bene in `docs/radar.md`. Se un campo esce vuoto, aggiungere il nome giusto in `normalizza()` di `radar/fetch_anac.py`.

## Parametri
Codici CPV, parole chiave e soglie stanno in `radar/config.py`.
