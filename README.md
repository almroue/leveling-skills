# leveling-skills

Skills för Claude Code som Leveling Systems använder. Alla i teamet jobbar på samma sätt när de laddar ner dem.

## Installera

```bash
npx skills add almroue/leveling-skills -g
```

`-g` lägger skillen hos dig i alla projekt. Uppdatera senare med `npx skills update -g -y`.

## Skills

| Skill | Vad den gör |
|---|---|
| `logga` | Loggar en klar leverans (video, bild, artefakt, kod) i den delade artefakten Leveranslogg. Alla i teamet ser senaste ändringarna på ett ställe. |
| `motion-task` | Skapar och sköter tasks i Motion i vår form: kort titel, högst 3 steg, Sätt igång-prompt, rätt ping. Kommer med två skript. Du behöver din egen Motion-nyckel (se skillen, del 7). |

## Så jobbar vi med loggen

1. När något är klart kör Claude skillen `logga` (eller säg "logga det").
2. Skillen laddar upp bilder och filmer och skriver en rad med text och länk.
3. Sidan Leveranslogg visar raderna, nyast överst. Filtrera på vem och typ.

Första gången: be Claude "skapa loggen". Skillen publicerar sidan, och du delar den med de andra som Editor.

## Lägg in i ett projekts README

Klistra in det här i README:n i varje repo som teamet jobbar i:

```markdown
## Logga leveranser

När något är klart (en film, en bild, en artefakt, en push) loggar vi det med skillen `logga`.
Installera den en gång: `npx skills add almroue/leveling-skills -g`
Säg sedan "logga det" till Claude. Loggen heter Leveranslogg och alla i teamet läser den.
```

## Bidra

En skill ligger i `skills/<namn>/SKILL.md`. Ändra i repot, inte i din lokala kopia, så får alla ändringen.
