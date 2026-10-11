#!/usr/bin/env python3
"""Skicka en kommentar i Motion med riktiga taggar, så att personen får en notis.

Motion-kopplingen (motionmcp) tar bort all HTML i kommentarer, så "@Namn" blir
en länk till en främling på GitHub. Det här skriptet går direkt till Motions API
med Motions eget tagg-element (Fahds lösning, 28 sep 2026).

Var och en använder sin EGEN nyckel (env MOTION_API_KEY eller Claude-appens Motion-koppling).
Den skrivs aldrig ut. Namn att tagga hämtas ur Motion (förnamn, gemener), inga id ligger i filen.
En kommentar går inte att ändra eller radera via API:t: tagga i första kommentaren.

Mall: 3 stycken med tom rad emellan, taggen sist.
  Rubrik: Beslut:, Kolla: eller Blockerad: + ämne, max 60 tecken
  Läget: 1 mening
  Din uppgift: 1 mening
Ton: som till en barndomsvän. Vänligt, rakt på sak, vardagsord.

Exempel:
  motion-kommentar.py --task tk_abc --tagga fahd --text "Kolla: Beloppen på Gosol\n\nJag har rättat 12 fakturor.\n\nKolla att summan blir 48 200 kr. Säg till om den inte gör det." --prov
(Skriv riktiga radbrytningar i --text. --prov visar bara texten.)
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

INSTALLNINGAR = os.path.expanduser(
    "~/Library/Application Support/Claude/claude_desktop_config.json"
)
API = "https://api.usemotion.com/v1/comments"

BAS = "https://api.usemotion.com/v1"
ARBETSYTA = "Leveling Systems"


def api_get(url):
    fraga = urllib.request.Request(url, headers={"X-API-Key": nyckel(), "User-Agent": "leveling-motion-kommentar/1.0"})
    try:
        with urllib.request.urlopen(fraga, timeout=30) as svar:
            return json.load(svar)
    except urllib.error.HTTPError as fel:
        sys.exit(f"Motion svarade {fel.code}: {fel.read().decode()[:300]}")


def personer():
    """Förnamn (gemener) -> (Motion-id, fullt namn), ur arbetsytans egen användarlista."""
    ws = api_get(f"{BAS}/workspaces")["workspaces"]
    val = [w for w in ws if w["name"] == ARBETSYTA]
    if not val:
        sys.exit(f"Hittar ingen arbetsyta som heter {ARBETSYTA}. Din nyckel ser: {', '.join(w['name'] for w in ws)}")
    lista = api_get(f"{BAS}/users?workspaceId={val[0]['id']}")
    lista = lista["users"] if isinstance(lista, dict) else lista
    return {u["name"].split()[0].lower(): (u["id"], u["name"]) for u in lista}


def tagg(person):
    motion_id, etikett = person
    etikett = html.escape(etikett, quote=True)
    return (
        f'<span class="font-bold" data-id="{motion_id}" '
        f'data-label="{etikett}" data-type="mention">@{etikett}</span>'
    )


ETIKETTER = ("Beslut:", "Kolla:", "Blockerad:")
RUBRIK_MAX = 60  # inkorgen klipper efter ~35 tecken: rubriken måste säga allt som är viktigt


def bygg_text(taggar, text, kand):
    # Taggen sist: inkorgens förhandsvisning visar början av kommentaren, inte taggen.
    stycken = [html.escape(s.strip()) for s in text.split("\n\n") if s.strip()]
    pinga = " ".join(tagg(kand[n]) for n in taggar)
    if stycken:
        stycken[-1] = f"{stycken[-1]} {pinga}".strip()
    elif pinga:
        stycken = [pinga]
    return "".join(f"<p>{s}</p>" for s in stycken)


def kolla_mall(taggar, text):
    if not taggar:
        return
    rubrik = text.strip().split("\n\n")[0]
    if not rubrik.startswith(ETIKETTER):
        sys.exit(f"Kommentar med tagg måste börja med {', '.join(ETIKETTER)} (se skillen motion-task, del 3).")
    if len(rubrik) > RUBRIK_MAX:
        sys.exit(f"Rubriken är {len(rubrik)} tecken, max {RUBRIK_MAX}. Korta den: inkorgen klipper efter ~35.")


def nyckel():
    if os.environ.get("MOTION_API_KEY"):
        return os.environ["MOTION_API_KEY"]
    try:
        with open(INSTALLNINGAR) as f:
            return json.load(f)["mcpServers"]["motion"]["env"]["MOTION_API_KEY"]
    except (OSError, KeyError, ValueError):
        pass
    try:  # Alternativ uppsättning: nyckeln står i startskriptet
        with open(os.path.expanduser("~/.config/motion-mcp/run.sh")) as f:
            m = re.search(r"MOTION_API_KEY=[\"']?([^\"'\s]+)", f.read())
        if m:
            return m.group(1)
    except OSError:
        pass
    sys.exit("Hittar ingen Motion-nyckel. Sätt MOTION_API_KEY eller lägg Motion-kopplingen i Claude-appen.")


def main():
    p = argparse.ArgumentParser(description="Kommentar i Motion med riktiga taggar.")
    p.add_argument("--task", required=True, help="task-id, tk_...")
    p.add_argument("--text", required=True, help="vanlig text, tom rad = nytt stycke")
    p.add_argument("--tagga", default="", help="kommaseparerat förnamn, t.ex. fahd,hamodi")
    p.add_argument("--prov", action="store_true", help="visa texten, skicka inget")
    a = p.parse_args()

    taggar = [n.strip().lower() for n in a.tagga.split(",") if n.strip()]
    kand = personer() if taggar else {}
    okanda = [n for n in taggar if n not in kand]
    if okanda:
        sys.exit(f"Okänt namn: {', '.join(okanda)}. Finns: {', '.join(kand)}")

    kolla_mall(taggar, a.text)
    innehall = bygg_text(taggar, a.text, kand)
    if a.prov:
        print(innehall)
        return

    data = json.dumps({"taskId": a.task, "content": innehall}).encode()
    fraga = urllib.request.Request(
        API,
        data=data,
        method="POST",
        # Utan eget User-Agent stoppar Cloudflare anropet (403, error code 1010).
        headers={
            "X-API-Key": nyckel(),
            "Content-Type": "application/json",
            "User-Agent": "leveling-motion-kommentar/1.0",
        },
    )
    try:
        with urllib.request.urlopen(fraga, timeout=30) as svar:
            print("Skickad:", json.load(svar).get("id"))
    except urllib.error.HTTPError as fel:
        sys.exit(f"Motion svarade {fel.code}: {fel.read().decode()[:300]}")


if __name__ == "__main__":
    main()
