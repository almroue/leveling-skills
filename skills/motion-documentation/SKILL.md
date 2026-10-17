---
name: motion-documentation
description: 'Dokumentera ett färdigt bygge i Motion och dela det med teamet (oftast Fahd) när testerna gått igenom. Använd när Alex säger dokumentera, skriv dokumentation, dokumentera i Motion, dela med Fahd efter testet, eller när ett bygge har körda tester och ska lämnas över. Skriver Dokumentation-filen, bifogar den, bockar, stänger och frågar sedan om delning.'
---

# Motion-documentation

Tasken, titeln, texten, bilagor, status och ping följer skillen `motion-task`. Den här skillen lägger bara till dokumentationen och delningen.

## 1. Före

- **Sök först** efter en öppen task om samma bygge (`motion-task` del 4, steg 0) och använd den. Finns ingen: skapa en.
- **Testat först.** Bygget ska ha körda kontroller med utdata (en testtabell, `rule-check` med 0 FAIL, eller ett kommando med svar). Saknas de: kör dem. Dokumentera aldrig ett bygge som inte testats.
- **Finns allt prompten pekar på?** Kolla verktyg, nycklar och filer före bygget. Saknas något: säg det i 1 rad och fråga Alex. (Lärdom 17 okt: prompten sa "Jev", som inte fanns.)

## 2. Dokumentationsfilen

Namn: `<Kort titel> - Dokumentation.md`. Första raden: `# <Kort titel> - Dokumentation`. Förskolespråk, korta meningar. Märk varje påstående *(verified)* eller *(gissning)*. Rubriker i den här ordningen, hoppa över det som inte behövs:

1. **Vad det gör** (3 meningar)
2. **Så provar du** (kommandot och vad svaret ska bli)
3. **Så slår du på och av** (bara om det finns en på/av)
4. **Ändringar mot ursprunget** (vad som blev annorlunda än prompten eller briefen, och varför)
5. **Testet** (tabell med körda siffror, missar flaggade, hur många som blev rätt)
6. **Svagheter** (rakt: vad som är långsammare, lättare testat eller osäkrare än det lät)
7. **Öppet**

Skriv filen i en tillfällig mapp, inte i en projektmapp. Hör den till ett skript: lägg en kopia bredvid skriptet.

## 3. Bifoga och stäng

- `python3 ~/.claude/skills/motion-task/scripts/motion-task.py bifoga <task> <fil> --flytta`
- Finns en äldre dokumentation: `dopa` den till `GAMMAL <namn>` först.
- Lägg en `Bilagor:`-rad i tasken, en rad per fil.
- Bocka stegen, kör `kolla`, stäng med `stang` när målet är nått.

## 4. Dela med teamet

Först när testerna gått igenom (visa utdata). Fråga Alex klickbart, en fråga: **Dela med Fahd?** Val: Fahd (förval), någon annan, inte nu.

Ja:

1. Hämta personens Motion-id med `motion_users list`. Hårdkoda inga id.
2. Skapa en boll-task (`motion-task`, bollreglerna i titeldelen): `<Område>: 🏐 <vad> (<d mån>)`, ansvarig personen. Skriv den som till en förskoleklassare: mål i 1 mening, varför du, högst 5 steg med **Klart när**, regler en per rad, **Rör inte**, tekniken sist under **För din Claude**. Dokumentationen som bilaga.
3. Fahd: mjukt datum, ungefär 10 dagar fram. Fråga aldrig om datum eller tid. Hans kod (live-sajten, appen) ligger i hans repo: skicka PR, pusha aldrig till main. Kolla andra sessioner före bygge i ett delat repo.
4. Ny task: Motion pingar själv, ingen extra kommentar.
5. Säg efteråt i 1 rad vad som delades, med länken.

Inte nu: dokumentationen ligger kvar, tasken är stängd, inget skickas.

Är bygget en skill: lägg den i `almroue/leveling-skills` (publikt repo) bara efter Alex ja, och utan id, nycklar eller kundnamn.

## Aldrig

- Nycklar, tokens eller lösenord i dokumentationen: skriv bara NAMN.
- Ändra `settings.json`, hooks eller annan konfig utan Alex ja. Ta backup och skriv ändringen i dokumentationen.
- Skicka något utanför Motion (mejl, publikt repo) utan Alex ja.
