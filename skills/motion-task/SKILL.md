---
name: motion-task
description: Skapa, ändra eller sköt en task i Motion i Leveling Systems form. Titel, kort text (målrad, högst 3 steg, Sätt igång-prompt när en LLM kan hjälpa), rätt ansvarig, ping bara när någon måste agera, och länken till den som bad om tasken. Enda källan för hur en Motion-task skrivs, även bolltasks (🏐) och tasks från rutiner. Triggers "gör en task", "tasta", "lägg in i Motion", "ge Fahd en uppgift", "Motion-task", "starta tasken", "sätt status", "min Motion-inkorg", "bocka steget", "bollen".
---

# Motion-task

En task ska gå att läsa på 10 sekunder och göras utan frågor. Skriv som till en förskoleklassare, med så få ord som möjligt.
Arbetsytan är alltid **Leveling Systems** (hitta id:t med `motion_workspaces list`). Skapa och ändra fritt där. Radera aldrig något.
Texten som teamet ser är på svenska.

**Skripten** ligger i den här skillens mapp: `~/.claude/skills/motion-task/scripts/` (`motion-task.py`, `motion-kommentar.py`). Var och en använder sin **egen** Motion-nyckel (del 7). Kör dem med Bash, och utan sandbox om nätverket blockeras.

## 0. Tänk om före varje task

Skriv utkastet. Fråga dig sedan 3 saker och ändra utkastet:
1. **Kortare?** Klipp ord tills nästa ord skulle göra det oklart.
2. **Missat?** Finns något viktigt som inte står där (varför, vad som inte får röras, vad som beror på vad)? Saknas det: lägg till, eller fråga den som bad om tasken.
3. **Missförstånd?** Kan en människa i teamet eller en AI läsa något på 2 sätt? Skriv om till 1 sätt.

**Är något oklart: intervjua den som bad om tasken**, 1 fråga i taget med klickbara val. Saknas ett verktyg (till exempel en funktion i Motions API): testa dig fram och mät, gissa inte.

**Passar tasken i ett projekt?** Läs listan (`motion_projects list`) och välj det som passar. Ser du ett mönster (flera tasks om samma sak, något som borde bli ett eget projekt): säg det i 1 rad. Passar inget: inget projekt.

**Verktygslådan i beskrivningen** (det som passar, aldrig allt): fet, kursiv, understruken, överstruken, `<h1>`, `<h2>`, punktlista, numrerad lista, kryssruta, kod, länk. En kort task behöver bara fet + rutor. Rutor passar när det är steg som kan bockas av. Är tasken en fråga, ett beslut eller en enda handling: inga rutor.

## 1. Titeln

`<Område>: <emoji> <vad som ska göras> (<omfång eller datum>)`

- **Område** först: systemet eller platsen (Meta, Perspective, GHL, MötesMaskinen™, Kommunkartan, Leveling Hub, Claude för skills och verktyg). Osäker: fråga. I en rutin: välj närmaste och skriv valet i rapporten.
- **1 emoji** direkt efter kolon:

| Emoji | När |
|---|---|
| ✨ | Något nytt byggs |
| 🔧 | Något som finns ändras |
| 🐛 | Något är trasigt och ska lagas |
| 🔍 | Något ska kollas eller granskas |
| 📊 | Siffror, mätning eller rapport |
| 🧹 | Något ska städas eller tas bort |
| 🏐 | Boll mellan två personer. Ersätter emojin ovan |

- **Vad: 3-sekunderstestet.** Den som tittar på titeln förstår vad tasken handlar om på 3 sekunder. Så få ord som möjligt, rakt på sak, vardagsord, inget fast ordantal och inget fast mönster. Klipp bort det tasken ändå förklarar. Skriv vardagsord i stället för intern jargong (formulär, inte funnel). Aldrig så kort att det blir oklart. Området först är det enda jargongordet som får stå.
- **Omfånget** står helst i meningen (`alla 23 formulär`). **Parentes** sist bara för datumet på en boll (`27 sep`) eller ett omfång som inte får plats i meningen. **Fil bifogad:** `(Zip)` om bilagan är en zip, annars `(Se attachment)`, i samma parentes som ett datum (`(Zip, 27 sep)`). Inget att lägga där: ingen parentes.

Exempel: `Perspective: ✨ Låt kunden skriva fritt i alla formulär` · `MötesMaskinen™: 🐛 Kolla varför samma tid bokas två gånger` · `Claude: 🔧 Installera Motion-skillen och prova den`

**Bollar.** En boll går mellan två personer. **Ansvarig = den som äger uppgiften nu.** Sista steget är alltid `Byt ansvarig till <strong>Namn</strong> här i Motion.` Byter ägaren: `update` med bara `assigneeId`. Motion pingar den nya ägaren, tagga inte också. Kommentera (del 3) bara när det finns något att kolla, välja eller vänta på. Är bara din del klar, eller hjälper någon annan till: byt inte ansvarig. Sätt **In Progress** när du börjar på en boll.

## 2. Texten

En task är **högst ~8 rader + en Sätt igång-prompt**. Teknik bor i prompten, inte i stegen.

- **Emoji aldrig i texten.** Bara i titeln.
- **Första raden är målet**, 1 mening, med det viktigaste i `<strong>`. Inga rubriker i en kort task. En lång task med flera delar får `<h2>` över delarna.
- **Rutor skapas alltid tomma** (`data-checked="false"`), bara när stegen går att bocka av (del 0).
- **Högst 3 steg.** Verb först, det som ska göras i `<strong>`. Behövs fler: tasken är för stor, dela den. Ingen siffra före steget, listan visar ordningen. Sikta på ~8 ord per steg, aldrig så kort att det blir oklart.
- **Fet, kursiv och parentes har var sin roll.** `<strong>` = det som ska göras eller synas. `<em>` = kontrollen i steget. (Parentes) = omfång, vem eller gräns.
- **Sätt igång-prompt** när en LLM kan hjälpa (bygga, ändra, kolla, skriva, undersöka). Ingen prompt när tasken är en handling ingen LLM hjälper med (ring, godkänn, betala): då slutar tasken efter stegen. Prompten är en **länk-prompt**: den har tasklänken och säger åt mottagarens Claude att starta och läsa tasken själv. Allt material ligger i tasken, så prompten upprepar inte stegen. Länken finns först när tasken är skapad, så prompten skrivs i description-steget (del 4). Etiketten ovanför är alltid `Sätt igång (kopiera hela rutan):`. Högst ~6 rader. Reglerna (status, kommentarmall, bocka, tagga) bor i skriptet: `start` skriver ut dem, så en regeländring gäller alla tasks. Ändra dem i `REGLER` i `motion-task.py`, inte i varje task.
- **Hemligheter hör inte hemma i en task** (nyckel, lösenord, token). Hela teamet ser tasken och prompten. Behövs en nyckel: skriv vilken och var personen hämtar den.
- **Allt mottagaren behöver står i tasken.** Hänvisa aldrig till ett mejl eller en fil som enda källa.
- Länkar skrivs `<a href="…">namn</a>`. Id (task-id, commit, filväg) står bara i prompten.
- Inga tankstreck. Två korta meningar i stället.
- Skriv **ren HTML**. Motion formaterar inte markdown bredvid HTML.

| Del | HTML |
|---|---|
| Målrad | `<p><strong>…</strong></p>`, första raden |
| Luft | `<p></p>` efter målraden och före Berörda. **Före Sätt igång: 12 `<p></p>` i rad**, så kodrutan hamnar långt ner och inte tar uppmärksamheten från målet och stegen. Motion sparar tomma rader. I prompten: en tom rad mellan grupperna |
| Linje | `<hr>` före en lång lista (fler än 5 rader) |
| Varning | `<p><strong>OBS!</strong> …</p>`. Högst 1, direkt under målraden, bara om något kan gå sönder |
| Det som ska göras eller synas | `<strong>` |
| Kontroll i ett steg | `<em>` |
| Prompt att kopiera | `<pre><code>…</code></pre>`. `<`, `>` och `&` skrivs `&lt;`, `&gt;`, `&amp;` |
| Text som ska kopieras exakt | `<code>` |
| Steg | checklistan i mallen |
| Rubrik (lång task) | `<h2>…</h2>` |
| Understruken, överstruken | `<u>…</u>`, `<s>…</s>` |
| Punktlista, numrerad lista | `<ul><li><p>…</p></li></ul>`, `<ol>…</ol>` |
| Klart steg | `data-checked="true"` + texten i `<s>…</s>` (görs av `bocka`, del 6) |
| Länk | `<a href="…">namn</a>` |

Ordningen: målrad, (OBS!), steg, (lång lista), (Sätt igång), Berörda, (Bilagor).

**Bilagor-raden.** Finns en bilaga står en rad längst ner: `<p><strong>Bilagor:</strong> <code>Filnamn.md</code> (vad den innehåller, 1 rad).</p>`. En rad per fil. Ingen bilaga, ingen rad. `kolla` ger FEL om en bilaga saknas där.
Lång lista: egen checklista efter en `<hr>`. Grupper med en fet rad och en tom rad emellan.

**Bilder.** API:t kan inte lägga in bilder. Bara där en bild förklarar bäst: `<p></p><p>[Klistra in skärmbild: vad den ska visa]</p><p></p>`, och säg till var.

**Bilagor (zip, fil).** Gå via API:t med `python3 ~/.claude/skills/motion-task/scripts/motion-task.py`: `bifoga <task> <fil>` lägger på en bilaga, `hamta <task> <mapp> [--namn fil.zip]` laddar ner den senaste med det namnet, `dopa <task> <gammalt> <nytt>` byter namn. Task = länk eller id. Ska en bilaga bytas ut: döp om den gamla (`namn-GAMMAL.zip`), bifoga den nya, nyaste med samma namn vinner. Bilagor går via Motions interna v2-API (samma nyckel). Motion kan ändra det utan förvarning: slutar det gå, ladda upp i Motion-appen. Skriptet raderar aldrig en bilaga i Motion. I tasken: ett steg `**Ladda ner** <filnamn> under Attachments` om en människa ska göra det.

**MD-filer i tasken.** Behöver AI:n detaljerade instruktioner, långa prompts eller bakgrund som inte får plats i texten: skriv dem i `<Kort titel> - Context.md` (första raden `# <Kort titel> - Context`) och bifoga med `bifoga <task> <fil> --flytta`. Skriptet laddar upp, hämtar tillbaka, jämför byte för byte och raderar sedan den lokala `.md`. Stämmer inte kopian ligger filen kvar. Bilagan i Motion är då enda kopian. Prompten säger `Läs <filnamn> först` och hämtar den med `hamta <task> <mapp> --namn "<filnamn>"`. Bara `.md` raderas, aldrig något annat.

**Mall:**

```html
<p><strong>Målet i 1 mening, med det viktigaste fet.</strong></p>
<p><strong>OBS!</strong> Bara om något kan gå sönder.</p>
<p></p>
<ul data-type="taskList">
<li data-type="taskItem" data-checked="false"><p><strong>Gör</strong> något med nyckelordet <em>(kontrollen, om det behövs)</em>.</p></li>
<li data-type="taskItem" data-checked="false"><p><strong>Gör</strong> nästa sak (omfång).</p></li>
<li data-type="taskItem" data-checked="false"><p><strong>Kolla</strong> att det syns.</p></li>
</ul>
<p></p><p></p><p></p><p></p><p></p><p></p><p></p><p></p><p></p><p></p><p></p><p></p>
<p><strong>Sätt igång</strong> (kopiera hela rutan):</p>
<pre><code>Du hjälper mig med en task i Motion.
Task: https://app.usemotion.com/web/pm/workspaces/WS_ID?task=tk_ID

Starta den (skriver ut reglerna): python3 ~/.claude/skills/motion-task/scripts/motion-task.py start tk_ID
Läs allt (text, bilagor, kommentarer): python3 ~/.claude/skills/motion-task/scripts/motion-task.py las tk_ID
Hämta bilagorna: python3 ~/.claude/skills/motion-task/scripts/motion-task.py hamta tk_ID ~/Downloads/task

Följ reglerna som start skriver ut. Fråga mig om något är oklart.</code></pre>
<p></p>
<p><strong>Berörda:</strong> @Namn @Namn</p>
<p><strong>Bilagor:</strong> <code>Filnamn.md</code> (vad den innehåller, 1 rad).</p>
```

`WS_ID` = arbetsytans id, `tk_ID` = taskens id.

**Kolla-task** (bollen tillbaka till den som bad): målrad = vad den andra säger är klart. Steg: **Be** Claude kolla (prompten). **Rätt:** stäng tasken. **Fel:** byt ansvarig tillbaka och skriv vad som är fel. Prompten ber Claude kolla det som sägs vara klart och svara rätt eller fel med bevis.

## 3. Personer och ping

- **Ansvarig** (assignee) = den som äger uppgiften. Alltid 1 person.
- **Ping-regeln:** en notis i någons inkorg betyder *du ska göra något*. Tagga bara den som måste agera nu: `Beslut` (någon ska välja), `Kolla` (någon ska granska) eller `Blockerad` (du väntar på just den personen). Klart, påbörjat, läst och FYI står i tasken, inte i inkorgen.
- **Ny task:** ingen taggkommentar. Motion pingar ansvarig själv när du sätter ansvarig.
- **Byter du ansvarig:** tagga inte den nya ägaren, Motion pingar redan.
- **Många på en gång:** fler än 2 tasks inom 1 timme ger ingen tagg per task. Säg i chatten vad som flyttats.
- **Status behålls som vanligt** (del 6). Statusnotisen är OK.
- **En riktig ping fungerar bara i en kommentar.** En tagg i beskrivningen blir vanlig text. Raden `Berörda:` pingar ingen.
- **Kommentarmallen:** 3 stycken med tom rad emellan, taggen sist.

  ```
  Kolla: Beloppen på fakturorna

  Jag har rättat 12 fakturor.

  Kolla att summan blir 48 200 kr. Säg till om den inte gör det. @Namn
  ```

  1. **Rubrik:** `Beslut:`, `Kolla:` eller `Blockerad:` + ämnet, max 60 tecken. Inkorgen visar bara de första ~35, så rubriken ska säga det viktiga.
  2. **Läget:** 1 mening. Vad har hänt.
  3. **Din uppgift:** 1 mening, verb först. Taggen sist i stycket.
  4. **Tonen:** som till en barndomsvän. Vänligt och avslappnat, rakt på sak, vardagsord. Ingen hälsningsfras, ingen tack-slinga.
- **Tagga med skriptet, aldrig med kopplingen.** Kopplingen (`motion_comments create`) tar bort taggen, och "@Namn" blir en länk till en främling på GitHub. Skriptet skickar Motions eget tagg-element:
  `python3 ~/.claude/skills/motion-task/scripts/motion-kommentar.py --task <id> --tagga fahd --text "<mallen, tom rad mellan stycken>"`
  Namn = förnamn i gemener, hämtat ur Motion (flera: `--tagga fahd,hamodi`). Skriptet vägrar en tagg utan etikett eller med rubrik över 60 tecken. `--prov` visar texten utan att skicka. En kommentar går inte att ändra eller radera: tagga rätt första gången. Går skriptet inte: skriv i svaret "Tagga @Namn i en kommentar, så pingas de."
- **Ansvarig kan bara vara någon i Motion-teamet.** Personer utanför kan nämnas i texten.

## 4. Så gör du i Motion

Verktyget är `mcp__motion__motion_tasks`. **Ett anrop i taget.**

0. `motion_projects list` med `workspaceId` (del 0: välj projekt). Sedan `list` med `workspaceId` och ett ord ur titeln. Finns tasken redan: ändra den, skapa ingen ny.
1. `create` med `name` och `workspaceId`, och `projectName` om tasken hör till ett projekt (det går inte att sätta sen). Create tar bort all HTML, och `assigneeId` i create ger INTERNAL_ERROR.
2. `update` med `description` (HTML), `priority: MEDIUM`, `duration: 30` och `dueDate` 10 dagar fram (YYYY-MM-DD), om inget annat sägs. Skicka aldrig `autoScheduled`. Prompten får taskens eget id, som finns först efter `create`.
3. `update` med bara `assigneeId`.
4. Kolla med `list`: `workspaceId`, `assigneeId` och ett ord ur titeln. `get` visar varken ansvarig eller text.
5. **Verifiera:** kör `python3 ~/.claude/skills/motion-task/scripts/motion-task.py kolla <id>`. Den mäter titel, steg, tomma rutor, emoji i texten, naken länk, tankstreck, markdown, hemlighet och att prompten har taskens eget id. FEL: rätta och kör om. VARNING: väg den (3-sekunderstest, max 3 steg). Visa tasken för den som bad om den först när `kolla` säger OK, och skriv `(verifierat med kolla)`.
6. Ingen taggkommentar på en ny task. Tagga bara om någon måste agera nu (del 3).

- **Fråga bara** om vem, vad eller område saknas. En fråga i taget, med klickbara val. Aldrig om datum, tid, prioritet eller taggar.
- **Flytta** = byt ansvarig med `update` och `assigneeId`. Använd aldrig `move` (den byter arbetsyta) eller `delete`.
- **Läs den gamla texten med `las <id>`** (ren text, inga bilder). Kopplingen visar den aldrig. En ny `description` ersätter allt, också skärmbilder någon klistrat in. Fråga innan du skriver om texten i en task som redan finns.
- **INTERNAL_ERROR:** Motion stryper efter ungefär 3 ändringar i rad. Vänta 90 sekunder och kör samma anrop igen. Flera tasks: vänta 60 sekunder mellan dem.
- `list` med `name` filtrerar efter `limit`: sätt inget lågt `limit`.
- Motion kan lägga arbetet efter datumet ("Scheduled past deadline"). Säg det och fråga: hög prioritet eller hårt datum?

## 5. Efter

**Länken till den som bad om tasken i samma svar**, och i varje senare svar som nämner tasken. Klickbar med taskens titel:
`[<titel>](https://app.usemotion.com/web/pm/workspaces/<WS_ID>?task=<id>)`
Inte `/web/calendar?task=`, den öppnar bara dina egna tasks. I en rutin: länken i rapporten och mejlet.

## 6. Starta och sköt en task (när du ska göra den)

Skriptet `python3 ~/.claude/skills/motion-task/scripts/motion-task.py` gör det via API:t:

- `start <länk>`: **gillar** (👍) kommentarer som andra skrivit, så de ser att du läst dem, och sätter **In Progress**. Egna kommentarer gillas inte.
- `las <länk>`: status, hela texten, bilagor och kommentarer i full längd (med reaktioner). Kopplingen klipper kommentarer vid 120 tecken och visar ingen text.
- `hamta <länk> <mapp>`: laddar ner bilagorna.
- `kolla <länk>`: mäter tasken mot reglerna (del 4 steg 5), utgångskod 1 vid fel.
- `bocka <länk> <nr|text> [...]`: bockar steget och stryker över texten, rör inget annat. Nummer räknas från 1 uppifrån. `las` visar varje steg som `[x]` eller `[ ]`. **Bocka varje steg när det är klart**, så syns det svart på vitt vad som är gjort. En bock syns inte live hos någon som har tasken öppen: ladda om sidan.
- `status <länk> <namn>`: byter status. I Leveling Systems: Backlog, Blocked, Canceled, Completed, In Progress, Todo och **Waiting** (blå).
- `steg <länk> <projekt-id> [steg]`: lägger tasken i projektets steg (utan steg: listar stegen).
- `inkorg [--olasta] [--typ x] [--antal 30]`: din egen Motion-inkorg (andras går inte att läsa). Typer: `mentioned-in-task-comment`, `task-assigned`, `task-status-updated`, `project-stage-entered`, `mentioned-in-note`.
- `moten [--sok text] [--antal 5] [--full]`: AI Notetakerns sammanfattning, deltagare och åtgärdspunkter. **Konfidentiella möten** (ägarstruktur, skatt, löner, personfrågor) blir aldrig tasks, eftersom hela teamet ser tasks.
- `gamla [--arkivera]`: hittar äldre kopior av den här skillen och skripten (zip-tiden) och flyttar dem till `~/.claude/skills-arkiv/` med `--arkivera`. Raderar aldrig. Kör den efter varje installation så att ingen gammal kopia ligger kvar.
- `vem`: visar vems nyckel som används. Bra som första prov (del 7).

**Kalenderblock** (`isFixedTimeTask`, till exempel tasks som GHL skapar från en bokning) går inte att stänga via API (testat med 5 vägar). Be personen trycka Mark complete i Motion. Skriptet säger det när det händer.

**Var dynamisk med status.** **In Progress** när du jobbar. **Waiting** (blå) när ni väntar på något utanför tasken (ett svar, en leverans, tid) och ingen måste agera nu. **Blocked** när en människa måste agera för att du ska komma vidare, med en `Blockerad:`-kommentar till just den personen. **Backlog** om det ska vänta. Tillbaka till In Progress när det går igen. **Completed och Canceled bara när personen sagt det** (skriptet kräver `--bekrafta`). Kommentera bara när någon måste agera (del 3).

## 7. Din egen Motion-nyckel

Skripten behöver din nyckel. Den är personlig och hemlig: den ger tillgång till hela din Motion.

1. **Skapa den själv:** logga in i Motion, öppna Settings och skapa en API-nyckel. Motion visar den bara en gång.
2. **Lägg den själv där skripten hittar den:** antingen i Motion-kopplingens inställning i Claude-appen (`mcpServers.motion.env.MOTION_API_KEY`), eller som `export MOTION_API_KEY=…` i din egen terminal-profil. Skriv den bara på din egen dator. Klistra aldrig in den i chatten, i en task, i en kommentar eller i en fil som delas.
3. **Rensa gamla kopior:** `python3 ~/.claude/skills/motion-task/scripts/motion-task.py gamla` listar dem, `gamla --arkivera` flyttar dem.
4. **Prova:** `python3 ~/.claude/skills/motion-task/scripts/motion-task.py vem` ska svara `Nyckeln funkar. Inloggad som <ditt namn>.`

Läs aldrig nyckelns värde. Behöver du veta att den finns: kör `vem`. Har en nyckel hamnat i en chatt eller en fil: skapa en ny i Motion och ta bort den gamla.
