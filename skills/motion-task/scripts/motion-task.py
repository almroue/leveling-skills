#!/usr/bin/env python3
"""Läs, starta och sköt en Motion-task via API:t: text, bilagor, gilla kommentarer, status.

Motions publika API (api.usemotion.com/v1) har status men inga bilagor eller reaktioner.
Motions egen app använder internal.usemotion.com/v2, och den släpper in samma API-nyckel
(verifierat 2026-10-06). v2 är internt och kan ändras av Motion utan förvarning.
Var och en använder sin EGEN Motion-nyckel. Den läses ur env MOTION_API_KEY eller Claude-appens
Motion-koppling och skrivs aldrig ut. Skriptet raderar aldrig något i Motion.
Task = länk (...?task=tk_abc) eller id (tk_abc).

  motion-task.py gamla  [--arkivera]              # hittar äldre kopior av den här skillen och skripten (--arkivera flyttar dem, raderar aldrig)
  motion-task.py vem                              # visar vems nyckel som används (provar nyckeln)
  motion-task.py las    <task>                    # status, text, bilagor, kommentarer
  motion-task.py start  <task>                    # gillar andras kommentarer + status In Progress
  motion-task.py inkorg [--olasta] [--typ x] [--antal 30]   # din personliga inbox (bara läsning, max 1000 poster)
  motion-task.py moten [--sok text] [--antal 5] [--full]   # notetakerns sammanfattning + åtgärdspunkter (bara läsning)
  motion-task.py gilla  <task> [--kommentar com_x] [--egna]
  motion-task.py status <task> <namn> [--bekrafta]   # Completed/Canceled kräver --bekrafta
  motion-task.py stang  <task> --text "Stängd: ..." [--tagga namn] [--trots-steg]   # Completed + Stängd-kommentar (alla steg bockade)
  motion-task.py laget  <task> "<vad som hänt>"   # skriver eller byter raden Läget: överst i texten, rör inget annat
  motion-task.py stad   [--dagar 30] [--alla]     # öppna tasks: klara men öppna, orörda i N dagar (--alla: alla titlar, för dubbletter)
  motion-task.py hamta  <task> <mapp> [--namn fil.zip]   # senaste bilagan med det namnet
  motion-task.py bifoga <task> <fil> [<fil> ...] [--flytta]   # --flytta: .md raderas lokalt när Motion bevisligen har en byte-lik kopia
  motion-task.py steg   <task> <projekt-id> [steg]  # lägger tasken i projektets steg (utan steg: listar stegen)
  motion-task.py bocka  <task> <nr|text> [...]      # bockar + stryker över steg (nr räknas från 1, eller del av texten)
  motion-task.py kolla  <task>                    # mäter tasken mot reglerna i skillen motion-task (utgångskod 1 vid fel)
  motion-task.py dopa   <task> <gammalt-namn> <nytt-namn>   # byter namn på en bilaga (aldrig radera)
"""
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

V1 = "https://api.usemotion.com/v1"
V2 = "https://internal.usemotion.com/v2"
GILLA = ":thumbsup:"
HERE = os.path.dirname(os.path.abspath(__file__)).replace(os.path.expanduser("~"), "~", 1)
KRAVER_BEKRAFTELSE = {"completed", "canceled"}  # att stänga en task är personens beslut
INSTALLNINGAR = [
    "~/Library/Application Support/Claude/claude_desktop_config.json",
    os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude_desktop_config.json"),
    "~/.config/Claude/claude_desktop_config.json",
    "~/.claude.json",
]


def nyckel_ur_startskript():
    # Alternativ uppsättning: nyckeln står i startskriptet, inte i mcpServers.
    # run.sh läser ofta in nyckeln från env-filen bredvid, så kolla båda.
    for fil in ("~/.config/motion-mcp/env", "~/.config/motion-mcp/run.sh"):
        try:
            with open(os.path.expanduser(fil)) as f:
                m = re.search(r"MOTION_API_KEY=[\"']?([^\"'\s$]+)", f.read())
            if m:
                return m.group(1)
        except OSError:
            pass
    return None


def nyckel():
    if os.environ.get("MOTION_API_KEY"):
        return os.environ["MOTION_API_KEY"]
    for sokvag in INSTALLNINGAR:
        try:
            with open(os.path.expanduser(sokvag)) as f:
                return json.load(f)["mcpServers"]["motion"]["env"]["MOTION_API_KEY"]
        except (OSError, KeyError, ValueError):
            continue
    k = nyckel_ur_startskript()
    if k:
        return k
    sys.exit("Hittar ingen Motion-nyckel. Sätt MOTION_API_KEY eller lägg Motion-kopplingen i Claude-appen.")


def anrop(metod, url, data=None, ct=None):
    # Utan eget User-Agent stoppar Cloudflare anropet (403, error code 1010).
    h = {"X-API-Key": nyckel(), "User-Agent": "leveling-motion-task/1.0"}
    if ct:
        h["Content-Type"] = ct
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=data, method=metod, headers=h), timeout=60
        ) as s:
            return s.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"Motion svarade {e.code}: {e.read().decode()[:300]}")


def json_anrop(metod, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(anrop(metod, url, data, "application/json" if data else None))


def task_id(arg):
    m = re.search(r"tk_[A-Za-z0-9]+", arg)
    if not m:
        sys.exit("Hittar inget task-id (tk_...) i: " + arg)
    return m.group(0)


def text_av(htmltext):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", htmltext or ""))).strip()


# shortcut: regex tar inte kapslade listor, byt till en riktig HTML-parser om en task får det.
RUTA = re.compile(r'<li data-type="taskItem" data-checked="(true|false)">(.*?)</li>', re.S)


def bocka(tid, vilka):
    beskr = json_anrop("GET", f"{V1}/tasks/{tid}").get("description") or ""
    rutor = RUTA.findall(beskr)
    val = set()
    for v in vilka:
        if v.isdigit() and 1 <= int(v) <= len(rutor):
            val.add(int(v))
            continue
        traffar = [i for i, (_, t) in enumerate(rutor, 1) if v.lower() in text_av(t).lower()]
        if len(traffar) != 1:
            sys.exit(f"{v!r} matchar {len(traffar)} steg, ska vara exakt 1. Använd stegets nummer.")
        val.add(traffar[0])
    n = [0]

    def byt(mm):
        n[0] += 1
        if n[0] not in val or mm.group(1) == "true":
            return mm.group(0)
        inre = re.sub(r"<p>(.*?)</p>", r"<p><s>\1</s></p>", mm.group(2), flags=re.S)
        return f'<li data-type="taskItem" data-checked="true">{inre}</li>'

    ny = RUTA.sub(byt, beskr)
    if ny == beskr:
        print("Redan bockat, inget ändrat.")
        return
    json_anrop("PATCH", f"{V1}/tasks/{tid}", {"description": ny})
    nu = [k for k, _ in RUTA.findall(json_anrop("GET", f"{V1}/tasks/{tid}").get("description") or "")]
    if any(nu[i - 1] != "true" for i in val):
        sys.exit("Motion tog inte emot bocken. Kolla i appen.")
    print(f"Bockade steg {sorted(val)} i {tid}")


def jag():
    return json_anrop("GET", f"{V1}/users/me")["id"]


def gamla(arkivera=False):
    """Äldre kopior av motion-task (skill-mappar, lösa skript från zip-tiden). Flyttas till ~/.claude/skills-arkiv, aldrig radera."""
    hem = os.path.expanduser("~")
    har = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))  # realpath: också när skriptet körs via en genväg
    kandidater = [f"{hem}/.claude/skills/motion-task", f"{hem}/.agents/skills/motion-task",
                  f"{hem}/.claude/scripts/motion-task.py", f"{hem}/.claude/scripts/motion-kommentar.py"]
    # en symlänk till den här skillen (till exempel ~/.claude/scripts/motion-task.py) är en genväg, inte en kopia
    gamla_ = [k for k in kandidater if os.path.lexists(k) and not (os.path.realpath(k) + os.sep).startswith(har + os.sep)]
    print(f"Den här (behålls): {har}")
    if not gamla_:
        print("Inga gamla kopior hittades.")
        return
    mal = f"{hem}/.claude/skills-arkiv/motion-gammal-{time.strftime('%Y-%m-%d')}"
    for k in gamla_:
        if not arkivera:
            print(f"GAMMAL: {k}")
            continue
        os.makedirs(mal, exist_ok=True)
        till = os.path.join(mal, os.path.basename(k))
        if os.path.lexists(till):
            till += time.strftime("-%H%M%S")
        shutil.move(k, till)
        print(f"Flyttade {k} -> {till}")
    if not arkivera:
        print("Kör igen med --arkivera för att flytta dem (inget raderas).")


def vem():
    u = json_anrop("GET", f"{V1}/users/me")
    print(f"Nyckeln funkar. Inloggad som {u['name']}.")


def namn_pa_anvandare(ws):
    try:
        lista = json_anrop("GET", f"{V1}/users?workspaceId={ws}")
        lista = lista["users"] if isinstance(lista, dict) else lista
        return {u["id"]: u["name"] for u in lista}
    except SystemExit:
        return {}


def feed(tid):
    d = json_anrop("GET", f"{V2}/tasks/{tid}/feed")
    kommentarer = [v for v in d["models"]["feedEntries"].values() if v["type"] == "COMMENT"]
    return sorted(kommentarer, key=lambda c: c["createdTime"])


def las(tid):
    v1 = json_anrop("GET", f"{V1}/tasks/{tid}")
    d = json_anrop("GET", f"{V2}/tasks/{tid}?include=attachments")
    filer = d["models"].get("uploadedFiles", {})
    namn = namn_pa_anvandare(v1["workspace"]["id"])
    mig = jag()
    print("TASK:", v1["name"])
    print("STATUS:", v1["status"]["name"])
    print("TEXT:", text_av(v1.get("description")))
    for i, (k, t) in enumerate(RUTA.findall(v1.get("description") or ""), 1):
        print(f"  STEG {i} [{'x' if k == 'true' else ' '}] {text_av(t)}")
    for f in sorted(filer.values(), key=lambda f: f["createdTime"]):
        print(f"BILAGA: {f['fileName']} ({f['fileSize']} byte, {f['createdTime']})")
    for c in feed(tid):
        r = c.get("reactions") or {}
        gillad = mig in r.get(GILLA, [])
        vem = namn.get(c["createdByUserId"], c["createdByUserId"])
        rs = ", ".join(f"{k} {len(v)}" for k, v in r.items()) or "inga"
        print(f"KOMMENTAR {c['id']} av {vem} ({c['createdTime'][:16]}): {text_av(c['body'])} [reaktioner: {rs}; gillad av mig: {'ja' if gillad else 'nej'}]")


def gilla(tid, kommentar=None, egna=False):
    mig = jag()
    gjort = 0
    for c in feed(tid):
        if kommentar and c["id"] != kommentar:
            continue
        if not kommentar and not egna and c["createdByUserId"] == mig:
            continue
        if mig in (c.get("reactions") or {}).get(GILLA, []):
            print(f"Redan gillad: {c['id']}")
            continue
        json_anrop("POST", f"{V2}/comments/{c['id']}/reactions", {"value": GILLA})
        print(f"Gillade {c['id']}")
        gjort += 1
    if gjort == 0:
        print("Inget nytt att gilla.")


def status(tid, onskat, bekrafta=False):
    v1 = json_anrop("GET", f"{V1}/tasks/{tid}")
    giltiga = [s["name"] for s in json_anrop("GET", f"{V1}/statuses?workspaceId={v1['workspace']['id']}")]
    val = next((s for s in giltiga if s.lower() == onskat.lower()), None)
    if not val:
        sys.exit(f"Okänd status '{onskat}'. Giltiga: {', '.join(giltiga)}")
    if val.lower() in KRAVER_BEKRAFTELSE and not bekrafta:
        if val.lower() == "completed":
            sys.exit("Completed: använd stang (Stängd-kommentar + Completed), eller --bekrafta om personen sagt ja.")
        sys.exit(f"{val} stänger tasken och är personens beslut. Lägg till --bekrafta om personen sagt ja.")
    gammal = v1["status"]["name"]
    if gammal != val:
        json_anrop("PATCH", f"{V1}/tasks/{tid}", {"status": val})
    ny = json_anrop("GET", f"{V1}/tasks/{tid}")["status"]["name"]
    print(f"Status: {gammal} -> {ny}")
    if ny != val:
        fast = json_anrop("GET", f"{V2}/tasks/{tid}")["models"]["tasks"][tid].get("isFixedTimeTask")
        sys.exit("Statusen blev inte som önskat." + (" Tasken är ett kalenderblock (fixed time): API:t kan inte ändra dess status. Be personen trycka Mark complete i Motion." if fast else ""))


DIR = os.path.dirname(os.path.abspath(__file__))
LAGET = re.compile(r"<p><strong>Läget:</strong>.*?</p>", re.S)


def kommentar(tid, tagga, text, prov=False):
    kor = [sys.executable, os.path.join(DIR, "motion-kommentar.py"), "--task", tid, "--tagga", tagga or "", "--text", text]
    r = subprocess.run(kor + (["--prov"] if prov else []), capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr.strip() or r.stdout.strip())
    return r.stdout.strip()


def stang(tid, tagga, text, trots_steg=False):
    text = text.replace("\\n", "\n")
    if not text.strip().startswith("Stängd:"):
        sys.exit("Texten ska börja med 'Stängd: <ämne>', sedan lösningen eller varför, sedan 'Inget att göra...'.")
    if len([s for s in text.split("\n\n") if s.strip()]) != 3:
        sys.exit("Stängd-kommentaren ska ha 3 stycken med tom rad emellan (rubrik, lösningen, Inget att göra...).")
    kvar = [text_av(t) for k, t in RUTA.findall(json_anrop("GET", f"{V1}/tasks/{tid}").get("description") or "") if k == "false"]
    if kvar and not trots_steg:
        sys.exit("Steg som inte är bockade: " + " | ".join(kvar) + "\nGjorda: bocka dem först. Inte gjorda: tasken är inte klar (Canceled kräver personens ja).")
    kommentar(tid, tagga, text, prov=True)  # fäller fel tagg eller rubrik innan något ändras
    status(tid, "Completed", bekrafta=True)  # kalenderblock stoppas här, då skickas ingen kommentar
    print("Kommentar", kommentar(tid, tagga, text))


def laget(tid, rad):
    beskr = json_anrop("GET", f"{V1}/tasks/{tid}").get("description") or ""
    ny_rad = f"<p><strong>Läget:</strong> {html.escape(rad.strip())}</p>"
    ny = LAGET.sub(lambda _: ny_rad, beskr, count=1) if LAGET.search(beskr) else ny_rad + beskr
    json_anrop("PATCH", f"{V1}/tasks/{tid}", {"description": ny})
    if ny_rad not in (json_anrop("GET", f"{V1}/tasks/{tid}").get("description") or ""):
        sys.exit("Motion tog inte emot Läget-raden. Kolla i appen.")
    print(f"Läget skrivet överst i {tid}")


def tid_av(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def stad(dagar=30, alla=False):
    ws = next(w["id"] for w in json_anrop("GET", f"{V1}/workspaces")["workspaces"] if w["name"] == "Leveling Systems")
    oppna, cursor = [], None
    while True:
        d = json_anrop("GET", f"{V1}/tasks?workspaceId={ws}" + (f"&cursor={cursor}" if cursor else ""))
        oppna += [t for t in d["tasks"] if not t.get("completed") and not t["status"].get("isResolvedStatus") and t["status"]["name"] not in ("Completed", "Canceled")]
        cursor = (d.get("meta") or {}).get("nextCursor")
        if not cursor:
            break
    nu = datetime.now(timezone.utc)

    def rad(t):
        orord = (nu - tid_av(t.get("lastInteractedTime") or t["updatedTime"])).days
        vem = ", ".join(a["name"] for a in t.get("assignees") or []) or "ingen"
        return f"  {orord:>3} d | {t['status']['name']} | {vem} | {t['name']} | https://app.usemotion.com/web/pm/workspaces/{ws}?task={t['id']}"

    klara = [t for t in oppna if (r := RUTA.findall(t.get("description") or "")) and all(k == "true" for k, _ in r)]
    gamla_t = [t for t in oppna if t not in klara and (nu - tid_av(t.get("lastInteractedTime") or t["updatedTime"])).days >= dagar]
    print(f"ÖPPNA: {len(oppna)}")
    print(f"\nKLARA MEN ÖPPNA (alla steg bockade, stäng med stang): {len(klara)}")
    print("\n".join(map(rad, klara)))
    print(f"\nORÖRDA I {dagar}+ DAGAR (fråga personen: Canceled eller leva vidare?): {len(gamla_t)}")
    print("\n".join(map(rad, sorted(gamla_t, key=lambda t: t.get("lastInteractedTime") or t["updatedTime"]))))
    if alla:
        print("\nALLA ÖPPNA, efter titel (leta dubbletter):")
        print("\n".join(map(rad, sorted(oppna, key=lambda t: t["name"].split(":", 1)[-1].strip().lower()))))


REGLER = f"""Gör det tasken ber om. Rör inte mer än tasken säger.
Klart steg: bocka och stryk över det: python3 {HERE}/motion-task.py bocka <task> <stegets nummer>
Status: In Progress medan du jobbar. Waiting (blå) när ni väntar på något utanför tasken (ett svar, en leverans, tid) och ingen måste agera nu. Blocked när en människa måste agera för att du ska komma vidare.
Jobbet klart och alla steg bockade: stäng själv och tagga den som bad om tasken: python3 {HERE}/motion-task.py stang <task> --tagga namn --text "Stängd: ämne\\n\\nLösningen i 1 mening.\\n\\nInget att göra. Säg till om något saknas, så öppnar jag igen."
Ska någon kolla ditt jobb: skapa ingen ny task. Skriv läget överst (python3 {HERE}/motion-task.py laget <task> "vad som hänt"), byt ansvarig till den som kollar och skriv en Kolla-kommentar. Canceled sätter du aldrig själv.
Kommentera bara när någon måste agera (Beslut, Kolla, Blockerad) eller när du stänger (Stängd). Tre stycken med tom rad emellan: rubrik (Etikett: ämne, max 60 tecken), läget, vad personen gör. Skriv som till en barndomsvän: vardagsord, rakt på sak, avslappnat.
Tagga sist: python3 {HERE}/motion-kommentar.py --task <task> --tagga namn --text "..."
Fråga mig om något är oklart. Avsluta med 1 rad till mig i chatten."""


def start(tid):
    print("REGLER FÖR DEN HÄR TASKEN:\n" + REGLER.replace("<task>", tid) + "\n")
    gilla(tid)
    nu = json_anrop("GET", f"{V1}/tasks/{tid}")["status"]["name"]
    if nu in ("Todo", "Backlog", "Blocked", "Waiting"):
        status(tid, "In Progress")
    else:
        print(f"Status lämnas som den är: {nu}")


def hamta_filer(tid):
    d = json_anrop("GET", f"{V2}/tasks/{tid}?include=attachments")
    return sorted(d["models"].get("uploadedFiles", {}).values(), key=lambda f: f["createdTime"])


def hamta(tid, mapp, namn=None):
    val = {}
    for f in hamta_filer(tid):
        if namn is None or f["fileName"] == namn:
            val[f["fileName"]] = f  # senaste med samma namn vinner
    if not val:
        sys.exit("Ingen bilaga hittades" + (f" med namnet {namn}" if namn else ""))
    os.makedirs(mapp, exist_ok=True)
    for n, f in val.items():
        data = anrop("GET", f"{V2}/files/{f['id']}/download")
        with open(os.path.join(mapp, os.path.basename(n)), "wb") as out:  # basename: filnamnet kommer från Motion
            out.write(data)
        print(f"Hämtade {n}: {len(data)} byte, sha256 {hashlib.sha256(data).hexdigest()[:16]}")


def bifoga(tid, filer, flytta=False):
    ws = json_anrop("GET", f"{V1}/tasks/{tid}")["workspace"]["id"]
    for sokvag in filer:
        namn = os.path.basename(sokvag)
        bd = "----leveling" + uuid.uuid4().hex
        falt = {"targetType": "TEAM_TASK", "targetId": tid, "workspaceId": ws}
        delar = [
            f'--{bd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
            for k, v in falt.items()
        ]
        # Motion nekar application/octet-stream, och macOS känner inte igen .md
        typ = mimetypes.guess_type(namn)[0] or ("text/plain" if namn.endswith(".md") else "application/octet-stream")
        with open(sokvag, "rb") as f:
            innehall = f.read()
        delar.append(
            f'--{bd}\r\nContent-Disposition: form-data; name="file"; filename="{namn}"\r\n'
            f"Content-Type: {typ}\r\n\r\n".encode() + innehall + b"\r\n"
        )
        delar.append(f"--{bd}--\r\n".encode())
        svar = json.loads(anrop("POST", f"{V2}/files/attachment", b"".join(delar), f"multipart/form-data; boundary={bd}"))
        print(f"Bifogade {namn} ({len(innehall)} byte): {svar['ids'][0]}")
        if flytta:
            # Raderar bara en .md, och bara när Motions kopia är byte-lik (annars ligger filen kvar).
            kopia = anrop("GET", f"{V2}/files/{svar['ids'][0]}/download")
            if namn.endswith(".md") and hashlib.sha256(kopia).digest() == hashlib.sha256(innehall).digest():
                os.remove(sokvag)
                print(f"Raderade {sokvag} lokalt. Bilagan i Motion är enda kopian.")
            else:
                print(f"Behöll {sokvag}: inte en .md eller kopian i Motion stämmer inte.")


EMOJI = r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50]"
JARGONG = ["funnel", "q8", "fritext", "mb:", "snapshot", "workflow"]


def kolla(tid):
    t = json_anrop("GET", f"{V1}/tasks/{tid}")
    titel, beskr, st = t["name"], t.get("description") or "", t["status"]["name"]
    fel, varn = [], []
    if not re.match(r"^[^:]{2,40}: " + EMOJI, titel):
        fel.append("Titeln ska vara '<Område>: <emoji> <vad>'")
    if len(titel.split()) > 12:
        varn.append(f"Titeln har {len(titel.split())} ord (3-sekunderstestet: klipp)")
    if any(j in titel.lower() for j in JARGONG):
        fel.append("Jargong i titeln (skriv med vardagsord)")
    if "—" in titel + beskr or " – " in titel + beskr:
        fel.append("Tankstreck, skriv två korta meningar")
    if re.search(EMOJI, beskr):
        fel.append("Emoji i texten (bara i titeln)")
    if re.search(r"\*\*|^\s*#{1,3} |\n- ", beskr):
        fel.append("Markdown i beskrivningen (skriv ren HTML)")
    rutor = RUTA.findall(beskr)
    if len(rutor) > 3 and "<hr>" not in beskr:
        varn.append(f"{len(rutor)} steg: max 3, annars dela tasken eller lägg en lång lista efter <hr>")
    if any(k == "true" for k, _ in rutor) and st in ("Todo", "Backlog"):
        fel.append("Bockade rutor på en task som inte startats (rutor skapas tomma)")
    utan_kod = re.sub(r'href="[^"]*"', "", re.sub(r"<pre>.*?</pre>", "", beskr, flags=re.S))
    if re.search(r"https?://", utan_kod):
        fel.append("Naken länk i texten (använd <a href>)")
    if re.search(r"\b(sk|pk|ghp|xox[bp])[-_][A-Za-z0-9]{16,}|(nyckel|token|lösenord|password|api[_-]?key)\s*[:=]\s*\S{12,}", beskr, re.I):
        fel.append("Ser ut som en hemlighet i texten. Ta bort den och rotera nyckeln")
    if "<pre>" in beskr and f"start {tid}" not in beskr:
        fel.append("Sätt igång-prompten saknar taskens eget id i 'start <id>'")
    for f in sorted({f["fileName"] for f in hamta_filer(tid)} - {n for n in {f["fileName"] for f in hamta_filer(tid)} if n.startswith("GAMMAL")}):
        if "Bilagor:" not in beskr or f not in text_av(beskr):
            fel.append(f"Bilagan {f} saknas i raden 'Bilagor:' längst ner (filnamn + vad den innehåller)")
    for x in fel:
        print("FEL:", x)
    for x in varn:
        print("VARNING:", x)
    if not fel and not varn:
        print("OK: inga avvikelser från reglerna")
    sys.exit(1 if fel else 0)


def dopa(tid, gammalt, nytt):
    traffar = [f for f in hamta_filer(tid) if f["fileName"] == gammalt]
    if not traffar:
        sys.exit(f"Ingen bilaga heter {gammalt}")
    for f in traffar:  # alla med det namnet, så att 'nyaste vinner' inte gömmer en gammal
        json_anrop("PATCH", f"{V2}/files/{f['id']}", {"fileName": nytt})
        print(f"Döpte om {gammalt} -> {nytt} ({f['id']})")


def inkorg(olasta, typ, antal):
    d = json_anrop("GET", f"{V2}/notifications/items")
    poster = [d["models"]["inboxItems"][i] for i in d["ids"]]  # nyast först; Motion ignorerar filter, vi filtrerar själva
    print(f"INKORG: {len(poster)} poster, {sum(not p['read'] for p in poster)} olästa")
    for p in [p for p in poster if (not olasta or not p["read"]) and (not typ or p["type"] == typ)][:antal]:
        m = p["payload"]["metadata"]
        print(f"{'OLÄST' if not p['read'] else 'läst '} {p['createdTime'][:16]} {p['type']} {p['payload']['snapshot']['title']} | task={m.get('taskId', '-')} kommentar={m.get('commentId', '-')}")


def moten(sok, antal, full):
    d = json_anrop("POST", f"{V2}/notetaker/query", {"filters": {}})  # alla möten teamet kan se; Motion ger 1 sida
    m = d["models"]
    rader = sorted((x for x in m["meetingInsights"].values() if x.get("summary")), key=lambda x: x["startTime"], reverse=True)
    rader = [x for x in rader if not sok or sok.lower() in (x["eventData"].get("title", "") + " " + " ".join(x["eventData"].get("attendeeEmails", []))).lower()]
    punkter = {}
    for p in m["meetingActionItems"].values():
        punkter.setdefault(p["meetingInsightsId"], []).append(p)
    print(f"MÖTEN: {len(m['meetingInsights'])} totalt, {len(rader)} med sammanfattning efter filter")
    for x in rader[:antal]:
        e = x["eventData"]
        print(f"\n{x['startTime'][:16]} {e.get('title')} | {x['id']} | deltagare: {', '.join(sorted(set(e.get('attendeeEmails', []))))}")
        print("  " + text_av(x["summary"] if full else x["summary"][:600]))
        for p in punkter.get(x["id"], []):
            print(f"  ÅTGÄRD: {p['taskData']['name']} (task={p.get('taskId') or '-'})")


def steg(tid, projekt, namn=None):
    svar = json_anrop("GET", f"{V2}/projects/{projekt}")
    alla = svar["models"]["projects"][projekt]["stages"]
    if not namn:
        for st in alla:
            print(f"{st['name']} ({st['taskCount']} tasks)")
        return
    traff = [st for st in alla if st["name"].lower() == namn.lower()]
    if not traff:
        sys.exit(f"Steget {namn!r} finns inte. Steg: {', '.join(st['name'] for st in alla)}")
    sid = traff[0]["stageDefinitionId"]
    json_anrop("PATCH", f"{V2}/tasks/{tid}", {"data": {"type": "NORMAL", "projectId": projekt, "stageDefinitionId": sid}})
    nu = json_anrop("GET", f"{V2}/tasks/{tid}")["models"]["tasks"][tid]
    if nu.get("stageDefinitionId") != sid:
        sys.exit("Motion tog inte emot steget. Kolla i appen.")
    print(f"{tid} ligger i steget {traff[0]['name']}")


def flagga(a, namn):
    return a[a.index(namn) + 1] if namn in a else None


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "las":
        las(task_id(a[1]))
    elif a[:1] == ["moten"]:
        moten(flagga(a, "--sok"), int(flagga(a, "--antal") or 5), "--full" in a)
    elif a[:1] == ["inkorg"]:
        inkorg("--olasta" in a, flagga(a, "--typ"), int(flagga(a, "--antal") or 30))
    elif a[:1] == ["gamla"]:
        gamla("--arkivera" in a)
    elif a[:1] == ["vem"]:
        vem()
    elif len(a) >= 2 and a[0] == "start":
        start(task_id(a[1]))
    elif len(a) >= 2 and a[0] == "gilla":
        gilla(task_id(a[1]), flagga(a, "--kommentar"), "--egna" in a)
    elif a[:1] == ["stad"]:
        stad(int(flagga(a, "--dagar") or 30), "--alla" in a)
    elif len(a) >= 2 and a[0] == "stang" and flagga(a, "--text"):
        stang(task_id(a[1]), flagga(a, "--tagga"), flagga(a, "--text"), "--trots-steg" in a)
    elif len(a) >= 3 and a[0] == "laget":
        laget(task_id(a[1]), a[2])
    elif len(a) >= 3 and a[0] == "status":
        status(task_id(a[1]), a[2], "--bekrafta" in a)
    elif len(a) >= 3 and a[0] == "hamta":
        hamta(task_id(a[1]), a[2], flagga(a, "--namn"))
    elif len(a) >= 4 and a[0] == "dopa":
        dopa(task_id(a[1]), a[2], a[3])
    elif len(a) >= 3 and a[0] == "steg":
        steg(task_id(a[1]), a[2], a[3] if len(a) > 3 else None)
    elif len(a) >= 3 and a[0] == "bocka":
        bocka(task_id(a[1]), a[2:])
    elif len(a) >= 2 and a[0] == "kolla":
        kolla(task_id(a[1]))
    elif len(a) >= 3 and a[0] == "bifoga":
        bifoga(task_id(a[1]), [x for x in a[2:] if x != "--flytta"], "--flytta" in a)
    else:
        sys.exit(__doc__)
