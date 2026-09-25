# SWK-Aufmaß (Wasser / Gas / Strom / Koordiniert) + Nachkalkulation

Neues Projekt vom 25.09.2026. Das bestehende Wasser-Tool
(`anhomei/SWK-Aufmass-Wasser` → https://rothgmbh-aufmass-swk.netlify.app/) bleibt **unverändert**.

## Inhalt

| Datei | Zweck | Wo |
|---|---|---|
| `site/index.html` | Startseite: Auswahl Wasser / Gas / Strom / Koordiniert | Netlify |
| `site/wasser.html` | Kopie des bestehenden Wasser-Tools (+ Link zur Startseite) | Netlify |
| `site/gas.html` | G T + G M, Oberflächenzettel (Gas vorbelegt) | Netlify |
| `site/strom.html` | nur E T (Montage macht SWK), Oberflächenzettel (Strom vorbelegt) | Netlify |
| `site/koordiniert.html` | Koord-Positionen E/G/W Tiefbau + Montage G/W | Netlify |
| `nachkalkulation/nachkalkulation.html` | Nachkalkulation mit LV-Preisen und 90 €/h | **nur lokal** (enthält Preise und internen Satz) |
| `build.py` | erzeugt alle Seiten aus der Vorlage | – |
| `vorlage/wasser-original.html` | Stand GitHub-Commit `f45cf17` (15.06.2026) | – |
| `vorlage/lv2026.json` | Auszug aus `S:\Roth GmbH\2026\SWK\Thüga-LV\Leistungsverzeichnis\Thüga-LV 2026.xlsx` | – |
| `vorlage/nachkalkulation-vorlage.html` | Oberfläche und Logik der Nachkalkulation | – |

## Positionen ändern

1. Positionslisten in `build.py` anpassen (Abschnitte `GAS_T`, `GAS_M`, `STROM_T`, `KOORD_T`, `KOORD_M`, nur Pos.-Nr.).
   Kurztext und Einheit kommen automatisch aus dem LV.
2. `python build.py` ausführen. Damit werden Aufmaß-Seiten **und** Nachkalkulation neu erzeugt,
   Reihenfolge und Positionen sind danach in beiden identisch.
3. Wasser-Positionen: in `vorlage/wasser-original.html` ändern (bleibt 1:1 wie das Live-Tool).

Neues LV (z. B. 2027): `vorlage/lv2026.json` aus der neuen Excel erzeugen (Spalten: OZ, externe Nr., Kurztext, ME, EP).
Achtung: Manche Nummern stehen im LV doppelt (Teil 02 wiederholt Teil 01 mit EP 0). Es zählt der erste Eintrag.

## Nachkalkulation: Bedienung

1. Sparte wählen, Auftragsdaten eintragen.
2. Im Suchfeld die letzten Ziffern der Pos.-Nr. aus dem Monteurs-PDF tippen, **Enter**, Menge eintragen, **Enter**, nächste Nummer.
   Positionen, die nicht im Aufmaßblatt stehen, werden aus dem LV unter „Sonstiges“ ergänzt.
3. Stunden Tiefbau / Montage eintragen. Rechts stehen sofort Erlös, Kosten (h × 90 €/h), Deckungsbeitrag, Marge,
   €/h erzielt, Soll-Stunden und die Ampel (grün ≥ 15 % Marge, gelb 0–15 %, rot = Verlust).
4. PDF für die Akte, Speichern als JSON für später.

## Online / Deploy

- Live: https://rothgmbh-swk-aufmass.netlify.app/ (Netlify-Site `rothgmbh-swk-aufmass`, ID in `netlify-site.json`)
- Repo: https://github.com/anhomei/SWK-Aufmass (öffentlich, ohne LV-Preise und ohne Nachkalkulation)
- Update: `python build.py` → `python deploy.py` (Token aus `tools/_deploy/.env`) → `git commit` + `git push`
- Kein Auto-Deploy bei Push: Netlify ist nicht mit GitHub verknüpft, deploy.py lädt `site/` direkt hoch.
