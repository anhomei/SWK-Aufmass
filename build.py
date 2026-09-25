"""
Build-Skript SWK-Aufmaß-Projekt (Roth GmbH)

Erzeugt aus der bewährten Wasser-Vorlage (vorlage/wasser-original.html) die
Aufmaß-Seiten für Wasser, Gas, Strom und koordinierte Maßnahmen sowie das
Nachkalkulations-Tool. Die JavaScript-Logik der Vorlage bleibt unverändert —
getauscht werden nur Positionstabellen und sichtbare Beschriftungen.

    python build.py

Ausgabe:
    site/index.html, wasser.html, gas.html, strom.html, koordiniert.html  (Netlify)
    nachkalkulation/nachkalkulation.html                                  (nur lokal — enthält Preise!)
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
VORLAGE = (ROOT / "vorlage" / "wasser-original.html").read_text(encoding="utf-8")
LV = json.loads((ROOT / "vorlage" / "lv2026.json").read_text(encoding="utf-8"))
# Manche Nummern stehen doppelt im LV (Teil 02 Kleinaufträge wiederholt Teil 01 mit EP 0) → erster Eintrag zählt
LV_BY_NR = {}
for _p in LV:
    LV_BY_NR.setdefault(_p["nr"], _p)

SITE = ROOT / "site"
NACHKALK = ROOT / "nachkalkulation"

# ── Positionslisten ───────────────────────────────────────────────────────────
# Abschnitt = (Titel, CSS-Klasse, [Pos.-Nr. …])  bzw. "SONSTIGES" als Platzhalter
# für die frei durchsuchbaren THÜGA-Zeilen. Kurztext/Einheit kommen aus dem LV.

GEBUEHR = ("Gebühr", "sec-dark", ["90000001500"])
PREISBLATT_T = ("Preisblatt T — Tiefbau und Oberflächen", "sec-green", [
    "50031004200", "50031004300", "50031004400", "50031004500", "50031004600",
    "50031004700", "50031004800", "50031004900", "50031005000", "90000001000"])
PREISBLATT_M = ("Preisblatt T — Tiefbau und Oberflächen", "sec-green", [
    "50037002410", "50031005800", "90000001000"])
MIKROROHR = ("Verlegung von Neuanschlüssen Rohranlagen", "sec-teal", ["50021200500", "50021200550"])

GAS_T = [
    GEBUEHR,
    ("Verlegung von Neuanschlüssen Tiefbau", "sec-blue", [
        "50012200800", "50012200950", "50012201220", "50012201250", "50012201350",
        "50012201420", "50012201450", "99006011020", "50012102860", "99006010300"]),
    ("Zusatzpositionen LV Gas / Spartenübergreifend", "sec-teal", ["90000004300", "90000004400"]),
    "SONSTIGES",
    PREISBLATT_T,
]
GAS_M = [
    ("Verlegung von Neuanschlüssen Tiefbau", "sec-blue", ["50012202000"]),
    ("Verlegung von Neuanschlüssen Montage", "sec-blue", [
        "50012202200", "50012202350", "50012202360", "50012202770", "50012202550",
        "50012202650", "50012202750", "50012202760"]),
    ("Verbinden der Inneninstallation Tiefbau", "sec-dark", ["50012600100"]),
    ("Verbinden der Inneninstallation Montage", "sec-dark", [
        "50012600200", "50012600250", "50012600300", "50012600400"]),
    ("Zusatzpositionen LV Gas", "sec-teal", ["90000002800"]),
    "SONSTIGES",
    MIKROROHR,
    PREISBLATT_M,
]

STROM_T = [
    GEBUEHR,
    ("Verlegung von Hausanschlüssen Tiefbau", "sec-blue", [
        "50011200600", "50011200650", "50011201200", "50011200950", "50011201020",
        "50011201040", "50011201060", "50011201080", "99006011010", "50011103060",
        "50011201100"]),
    ("Verbinden der Inneninstallation Tiefbau", "sec-dark", ["50011600100"]),
    ("Zusatzpositionen LV Elektrizität", "sec-teal", ["90000000925", "90000000926"]),
    "SONSTIGES",
    MIKROROHR,
    ("Preisblatt T — Tiefbau und Oberflächen", "sec-green", PREISBLATT_T[2][:-1] + ["50031005800", "90000001000"]),
]
STROM_M = ["SONSTIGES"]  # Strom-Montage macht Roth nicht — Blatt bleibt ausgeblendet

KOORD_T = [
    GEBUEHR,
    ("Koordinierter Hausanschluss — Strom (E T)", "sec-blue", [
        "50017200100", "50017200200", "50017200500", "50017200600", "50017200640", "50017200660"]),
    ("Koordinierter Hausanschluss — Gas (G T)", "sec-blue", [
        "50017200700", "50017200800", "50017201100", "50017201200", "50017201240", "50017201260"]),
    ("Koordinierter Hausanschluss — Wasser (W T)", "sec-blue", [
        "50017201300", "50017201400", "50017201700", "50017201800", "50017201840", "50017201860"]),
    ("Spartenübergreifende Zulagen / Abzüge", "sec-dark", [
        "50017102800", "50017201900", "99006011220", "99006011230", "99006011240",
        "99006010100", "99006010200", "99006011070",
        "99006011010", "99006011020", "99006011030"]),
    ("Hauseinführung / Inneninstallation Tiefbau", "sec-dark", [
        "50011600100", "50012600100", "50013600100",
        "50011201100", "50012202000", "50013202100",
        "90000000420", "90000000440"]),
    ("Zusatzpositionen Spartenübergreifend", "sec-teal", [
        "90000000110", "99006011040", "90000004300", "90000004400"]),
    "SONSTIGES",
    PREISBLATT_T,
]
KOORD_M = [
    ("Gas — Neuanschluss Montage (G M)", "sec-blue", [
        "50012202200", "50012202350", "50012202360", "50012202770", "50012202550",
        "50012202650", "50012202750", "50012202760"]),
    ("Gas — Inneninstallation Montage", "sec-dark", [
        "50012600200", "50012600250", "50012600300", "50012600400"]),
    ("Wasser — Neuanschluss Montage (W M)", "sec-blue", [
        "50013202300", "50013202450", "50013202475", "50013202650", "50013202750",
        "50013202850", "50013202860"]),
    ("Wasser — Inneninstallation Montage", "sec-dark", ["50013600200", "50013600250"]),
    "SONSTIGES",
    MIKROROHR,
    PREISBLATT_M,
]

SPARTEN = {
    # key: (Anzeigename, Blatt-1-Kürzel, Blatt-1-Titel, Blatt-2-Kürzel, Blatt-2-Titel,
    #       Modus-Optionen, Sparten-Platzhalter, OFL-Checkbox, Abschnitte 1, Abschnitte 2)
    "gas": dict(name="Gas", t1="G T", n1="Tiefbau", t2="G M", n2="Montage",
                modes=[("both", "G T + G M (Tiefbau und Montage)"), ("wt", "Nur G T — Tiefbau"), ("wm", "Nur G M — Montage")],
                sparte_ph="SWK-G / 2026-0123", ofl="Gas", s1=GAS_T, s2=GAS_M),
    "strom": dict(name="Strom", t1="E T", n1="Tiefbau", t2="E M", n2="Montage",
                  modes=[("wt", "E T — Tiefbau (Montage durch SWK)")],
                  sparte_ph="SWK-E / 2026-0123", ofl="Strom", s1=STROM_T, s2=STROM_M),
    "koordiniert": dict(name="Koordiniert", t1="Koord. T", n1="Tiefbau E/G/W", t2="Koord. M", n2="Montage G/W",
                        modes=[("both", "Tiefbau + Montage"), ("wt", "Nur Tiefbau (koordiniert)"), ("wm", "Nur Montage")],
                        sparte_ph="SWK-Koord / 2026-0123", ofl=None, s1=KOORD_T, s2=KOORD_M),
}

# ── HTML-Bausteine ────────────────────────────────────────────────────────────
THEAD = """<thead><tr>
    <th style="width:116px">Pos.-Nr.</th><th>Bezeichnung</th>
    <th style="width:44px">Einh.</th><th style="width:74px">Menge</th><th>Erläuterung</th>
  </tr></thead>"""


def einheit(me):
    return (me or "").upper().replace("STD", "H")


def pos_row(nr):
    p = LV_BY_NR[nr]  # KeyError = Tippfehler in der Positionsliste → Build bricht bewusst ab
    eh = einheit(p["me"])
    step = "1" if eh == "ST" else "0.01"
    return (f'    <tr><td class="td-nr">{nr}</td><td class="td-bez">{html.escape(p["bez"])}</td>'
            f'<td class="td-eh">{html.escape(eh)}</td><td class="td-mg"><input type="number" step="{step}" min="0"></td>'
            f'<td><input type="text"></td></tr>')


def sonstiges(key):
    return f"""  <div class="sec-hdr sec-orange">Sonstiges — Positionen aus THÜGA LV 2026 (742 Positionen durchsuchbar)</div>
  <table class="pos-tbl" id="tbl-s-{key}"><thead><tr>
    <th style="width:116px">Pos.-Nr. / Suche</th><th>Bezeichnung</th>
    <th style="width:50px">Einh.</th><th style="width:74px">Menge</th>
    <th>Erläuterung</th><th class="no-print" style="width:36px"></th>
  </tr></thead><tbody id="s-{key}"></tbody></table>
  <div class="no-print">
    <button class="btn btn-add" onclick="addRow('s-{key}')">+ Position hinzufügen</button>
  </div>
"""


def sections_html(sections, key):
    out = []
    for s in sections:
        if s == "SONSTIGES":
            out.append(sonstiges(key))
            continue
        title, cls, nrs = s
        rows = "\n".join(pos_row(n) for n in nrs)
        out.append(f'  <div class="sec-hdr {cls}">{html.escape(title)}</div>\n'
                   f'  <table class="pos-tbl">{THEAD}<tbody>\n{rows}\n  </tbody></table>\n')
    return "\n".join(out) + "\n"


def replace_once(src, old, new, count=1):
    n = src.count(old)
    if n != count:
        raise ValueError(f"Erwartet {count}× {old!r}, gefunden {n}×")
    return src.replace(old, new)


def replace_sheet(src, tab_title, new_body):
    """Ersetzt alles zwischen tab-title-Zeile und der folgenden sig-row."""
    start_tag = f'<div class="tab-title no-print">{tab_title}</div>'
    i = src.index(start_tag) + len(start_tag)
    j = src.index('<div class="sig-row">', i)
    return src[:i] + "\n\n" + new_body + "  " + src[j:]


BACKLINK = ('<div class="container">\n<div class="no-print" style="margin:0 0 8px 0;font-size:13px;">'
            '<a href="./" style="color:var(--color-ink, #242021);text-decoration:none;font-weight:600;">&larr; Zur Auswahl (Wasser / Gas / Strom / Koordiniert)</a></div>')


def build_wasser():
    src = replace_once(VORLAGE, '<div class="container">', BACKLINK)
    return src


def build_sparte(key, cfg):
    src = VORLAGE
    src = replace_sheet(src, "Aufmaßblatt W T — Tiefbau", sections_html(cfg["s1"], "wt"))
    src = replace_sheet(src, "Aufmaßblatt W M — Montage", sections_html(cfg["s2"], "wm"))

    t1 = f'Aufmaßblatt {cfg["t1"]} — {cfg["n1"]}'
    t2 = f'Aufmaßblatt {cfg["t2"]} — {cfg["n2"]}'
    src = replace_once(src, "Aufmaßblatt W T — Tiefbau", t1, 3)
    src = replace_once(src, "Aufmaßblatt W M — Montage", t2, 3)
    src = replace_once(src, "Aufmaßblatt W T (Tiefbau)", f'Aufmaßblatt {cfg["t1"]} ({cfg["n1"]})')
    src = replace_once(src, "Aufmaßblatt W M (Montage)", f'Aufmaßblatt {cfg["t2"]} ({cfg["n2"]})')

    src = replace_once(src, "<title>Aufmaß-Tool Wasser – Roth GmbH Tiefbau</title>",
                       f'<title>Aufmaß-Tool {cfg["name"]} – Roth GmbH Tiefbau</title>')
    src = replace_once(src, "Aufmaß-Tool — Roth GmbH Tiefbau (Wasser / SWK)",
                       f'Aufmaß-Tool — Roth GmbH Tiefbau ({cfg["name"]} / SWK)')
    src = replace_once(src, "SWK-W / 2026-0123", cfg["sparte_ph"])
    src = replace_once(src, "'SWK-Wasser_'", f"'SWK-{cfg['name']}_'")
    src = replace_once(src, "'SWK-Aufmass_'", f"'SWK-{cfg['name']}-Aufmass_'")

    # Modus-Auswahl
    old_opts = re.search(r'(<select id="g-mode"[^>]*>)(.*?)(</select>)', src, re.S)
    opts = "\n".join(f'        <option value="{v}">{html.escape(t)}</option>' for v, t in cfg["modes"])
    src = src[:old_opts.start(2)] + "\n" + opts + "\n      " + src[old_opts.end(2):]

    # Oberflächenzettel: passende Sparte vorbelegen
    src = replace_once(src, '<input type="checkbox" id="ofl-wasser" checked> Wasser',
                       '<input type="checkbox"> Wasser')
    if cfg["ofl"]:
        src = replace_once(src, f'<input type="checkbox"> {cfg["ofl"]}',
                           f'<input type="checkbox" id="ofl-wasser" checked> {cfg["ofl"]}')
    else:  # koordiniert: keine Vorbelegung, Zurücksetzen darf nicht auf fehlendes Element greifen
        src = replace_once(src, "document.getElementById('ofl-wasser').checked = true;", "")

    # Modus beim Laden anwenden (Strom: Montage-Blatt ausblenden)
    src = replace_once(src, "initRows('s-wm', 4);\n", "initRows('s-wm', 4);\nsetAufmassMode();\n")

    src = replace_once(src, '<div class="container">', BACKLINK)
    return src


# ── Startseite ────────────────────────────────────────────────────────────────
INDEX = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SWK-Aufmaß – Roth GmbH Tiefbau</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root { --red:#EE1D25; --red-dark:#B3151B; --ink:#242021; --muted:#696667; --surface:#F4F3F3; --border:#D9D7D7;
        --wasser:#2F6F8F; --gas:#F5A623; --strom:#EE1D25; --koord:#4F7942; }
* { box-sizing:border-box; }
body { margin:0; background:var(--surface); color:var(--ink); font-family:Inter, system-ui, sans-serif; }
header { background:var(--ink); color:#fff; padding:18px 16px; border-bottom:4px solid var(--red); }
header .in { max-width:960px; margin:0 auto; display:flex; align-items:center; gap:16px; }
header img { height:56px; background:#fff; border-radius:4px; padding:3px; }
h1 { font-family:Oswald, 'Arial Narrow', sans-serif; font-weight:600; font-size:26px; letter-spacing:.04em; text-transform:uppercase; margin:0; }
header p { margin:2px 0 0; color:#cfcccc; font-size:14px; }
main { max-width:960px; margin:0 auto; padding:24px 16px 40px; }
h2 { font-family:Oswald, sans-serif; font-weight:500; font-size:15px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 0 12px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); gap:14px; }
a.tile { display:block; background:#fff; border:1px solid var(--border); border-top:6px solid var(--c); border-radius:6px;
         padding:18px 16px 16px; text-decoration:none; color:var(--ink); transition:transform .12s, box-shadow .12s; }
a.tile:hover, a.tile:focus-visible { transform:translateY(-2px); box-shadow:0 6px 18px rgba(0,0,0,.08); outline:none; }
.tile .k { font-family:Oswald, sans-serif; font-size:13px; letter-spacing:.1em; color:var(--c); font-weight:600; }
.tile .t { font-family:Oswald, sans-serif; font-size:24px; font-weight:600; text-transform:uppercase; margin:2px 0 8px; }
.tile .d { font-size:13.5px; color:var(--muted); line-height:1.45; }
footer { max-width:960px; margin:0 auto; padding:0 16px 30px; font-size:12px; color:var(--muted); }
</style>
</head>
<body>
<header><div class="in">
  <img src="__LOGO__" alt="Roth GmbH">
  <div><h1>SWK-Aufmaß</h1><p>Roth GmbH Tiefbau Kaiserslautern &middot; THÜGA-LV 2026</p></div>
</div></header>
<main>
  <h2>Was möchtest du abrechnen?</h2>
  <div class="grid">
    <a class="tile" href="wasser.html" style="--c:var(--wasser)"><div class="k">W T &middot; W M</div><div class="t">Wasser</div>
      <div class="d">Hausanschluss Wasser – Tiefbau und Montage, mit Oberflächenzettel.</div></a>
    <a class="tile" href="gas.html" style="--c:var(--gas)"><div class="k">G T &middot; G M</div><div class="t">Gas</div>
      <div class="d">Hausanschluss Gas – Tiefbau und Montage, mit Oberflächenzettel.</div></a>
    <a class="tile" href="strom.html" style="--c:var(--strom)"><div class="k">E T</div><div class="t">Strom</div>
      <div class="d">Hausanschluss Strom – nur Tiefbau (Montage durch SWK).</div></a>
    <a class="tile" href="koordiniert.html" style="--c:var(--koord)"><div class="k">E / G / W</div><div class="t">Koordiniert</div>
      <div class="d">Koordinierte Maßnahme – gemeinsamer Graben mehrerer Sparten, Koord-Positionen.</div></a>
  </div>
</main>
<footer>Speichern erzeugt eine JSON-Datei für den Projektordner – es werden keine Daten auf dem Server gespeichert.</footer>
</body>
</html>
"""


# ── Nachkalkulation: Positionsstruktur aus den fertigen Seiten lesen ──────────
def extract_structure(page_html, sheet_titles):
    """Liest Abschnitte + Positionen aus tab-wt / tab-wm — exakt wie im Aufmaß-PDF."""
    sheets = []
    for tab, title in zip(("tab-wt", "tab-wm"), sheet_titles):
        if title is None:
            continue
        a = page_html.index(f'id="{tab}"')
        b = page_html.index('<div class="sig-row">', a)
        block = page_html[a:b]
        secs = []
        for m in re.finditer(r'<div class="sec-hdr[^"]*">(.*?)</div>\s*<table class="pos-tbl"(.*?)</table>', block, re.S):
            t = html.unescape(m.group(1)).strip()
            body = m.group(2)
            if 'id="tbl-s-' in body:
                secs.append({"title": "Sonstiges — Positionen aus THÜGA LV 2026", "sonst": True, "rows": []})
                continue
            rows = []
            for r in re.finditer(r'<td class="td-nr">(\d+)</td><td class="td-bez">(.*?)</td><td class="td-eh">(.*?)</td>', body):
                nr = r.group(1)
                rows.append({"nr": nr, "bez": html.unescape(r.group(2)), "eh": html.unescape(r.group(3))})
            secs.append({"title": t, "rows": rows})
        sheets.append({"key": "T" if tab == "tab-wt" else "M", "title": title, "sections": secs})
    return sheets


def main():
    logo = re.search(r"const ROTH_LOGO = '([^']+)'", VORLAGE).group(1)
    SITE.mkdir(exist_ok=True)
    NACHKALK.mkdir(exist_ok=True)

    pages = {"wasser": build_wasser()}
    for key, cfg in SPARTEN.items():
        pages[key] = build_sparte(key, cfg)
    for key, src in pages.items():
        (SITE / f"{key}.html").write_text(src, encoding="utf-8")
    (SITE / "index.html").write_text(INDEX.replace("__LOGO__", logo), encoding="utf-8")

    struct = {
        "wasser": {"name": "Wasser", "sheets": extract_structure(pages["wasser"], ["W T — Tiefbau", "W M — Montage"])},
        "gas": {"name": "Gas", "sheets": extract_structure(pages["gas"], ["G T — Tiefbau", "G M — Montage"])},
        "strom": {"name": "Strom", "sheets": extract_structure(pages["strom"], ["E T — Tiefbau", None])},
        "koordiniert": {"name": "Koordiniert", "sheets": extract_structure(pages["koordiniert"], ["Koord. Tiefbau E/G/W", "Montage G/W"])},
    }
    # Plausibilität: jede feste Position muss einen LV-Preis haben, keine Doppelten je Blatt
    for sk, sp in struct.items():
        for sh in sp["sheets"]:
            seen = set()
            for sec in sh["sections"]:
                for r in sec["rows"]:
                    assert r["nr"] in LV_BY_NR, f"{sk}/{sh['key']}: {r['nr']} nicht im LV"
                    assert r["nr"] not in seen, f"{sk}/{sh['key']}: {r['nr']} doppelt"
                    seen.add(r["nr"])

    # EP auf 2 Stellen; EUR-Positionen (Skonto-Faktor 1,035) auf 3 Stellen. Exakte Dubletten (Nr + Text) nur einmal.
    lv, gesehen = [], set()
    for p in LV:
        if (p["nr"], p["bez"]) in gesehen:
            continue
        gesehen.add((p["nr"], p["bez"]))
        me = einheit(p["me"])
        lv.append({"nr": p["nr"], "bez": p["bez"], "me": me, "ep": round(p["ep"] or 0, 3 if me == "EUR" else 2)})
    tpl = (ROOT / "vorlage" / "nachkalkulation-vorlage.html").read_text(encoding="utf-8")
    out = (tpl.replace("/*__STRUKTUR__*/null", json.dumps(struct, ensure_ascii=False))
              .replace("/*__LV__*/[]", json.dumps(lv, ensure_ascii=False))
              .replace("__LOGO__", logo))
    (NACHKALK / "nachkalkulation.html").write_text(out, encoding="utf-8")

    for key in pages:
        n = sum(len(s["rows"]) for sh in struct[key]["sheets"] for s in sh["sections"])
        print(f"{key:12s} {n:3d} feste Positionen")
    print("fertig:", SITE, NACHKALK)


if __name__ == "__main__":
    main()
