#!/usr/bin/env python3
"""Copy the WakaTime stats block from README.md into the translated READMEs,
translating it on the way in.

Two limitations of waka-readme-stats make this script necessary:

1. It only ever rewrites the repository's canonical README
   (`GitHubManager.REMOTE.get_readme().path`, i.e. README.md) — there is no
   target-file input.
2. LOCALE is global per run, so one run cannot emit English in README.md and
   Portuguese/Spanish in the translations. And several strings are hardcoded in
   the action ("Code Time", "commits", "Last Updated on", "hrs"/"mins", the
   whole AI block), so they stay English in *every* locale anyway.

So the block is generated once in English and translated here. Wording for the
strings the action does localize is copied from its own
`sources/translation.json` (locales `pt` and `es`), so the translated READMEs
read like the action had been run with LOCALE set.

Rows inside the ```text blocks use fixed-width columns — name: 25 chars,
quantity: 20 chars, bar: 25 chars (see `make_list` in
`sources/graphics_list_formatter.py`). Translating a label changes its length,
so rows are re-padded after translation, with the same 25-char truncation the
action applies.

Anything without a rule below is simply left as-is, so a new upstream string
degrades to English instead of breaking the sync.

Run from the repository root. Exits non-zero only on a real error; "nothing
changed" is a success.
"""

from pathlib import Path
from re import DOTALL, compile, escape, search, sub
from sys import exit, stderr
from urllib.parse import quote, unquote

SOURCE = Path("README.md")
# Target file -> locale key used in RULES below.
TARGETS = {Path("README.pt-BR.md"): "pt-BR", Path("README.es.md"): "es"}

START = "<!--START_SECTION:waka-->"
END = "<!--END_SECTION:waka-->"
BLOCK = f"{escape(START)}.*?{escape(END)}"

# Order matters: the more specific pattern has to come first, otherwise the
# generic one eats it ("Not Opted to Hire" before "Opted to Hire", the AI
# "No ... Activity" before the plain one, "I'm a Night 🦉" before "Night").
RULES = [
    # -- badge labels ------------------------------------------------------
    ("AI Code Time", {"pt-BR": "Tempo de Código com IA", "es": "Tiempo de Código con IA"}),
    ("Code Time", {"pt-BR": "Tempo de Código", "es": "Tiempo de Código"}),
    # -- short info (the "> " quote lines) ---------------------------------
    ("My GitHub Data", {"pt-BR": "Meus dados no GitHub", "es": "Mis datos de GitHub"}),
    (
        r"([\d.,]+ \w?B) Used in GitHub's Storage",
        {"pt-BR": r"\1 usado no armazenamento do GitHub", "es": r"\1 almacenamiento de GitHub utilizado"},
    ),
    (
        r"([\d.,]+) Contributions in the Year (\d{4})",
        {"pt-BR": r"\1 contribuições no ano de \2", "es": r"\1 contribuciones durante el año \2"},
    ),
    ("Not Opted to Hire", {"pt-BR": "Não aberto para contratação", "es": "No abierto para contratación"}),
    ("Opted to Hire", {"pt-BR": "Aberto para contratação", "es": "Abierto a contratación"}),
    ("Profile Views", {"pt-BR": "Visualizações do perfil", "es": "Visitas al perfil"}),
    (r"(\d+) Public Repositories", {"pt-BR": r"\1 repositórios públicos", "es": r"\1 repositorios públicos"}),
    (r"(\d+) Public Repository", {"pt-BR": r"\1 repositório público", "es": r"\1 repositorio público"}),
    (r"(\d+) Private Repositories", {"pt-BR": r"\1 repositórios privados", "es": r"\1 repositorios privados"}),
    (r"(\d+) Private Repository", {"pt-BR": r"\1 repositório privado", "es": r"\1 repositorio privado"}),
    ("From Hello World I've Written", {"pt-BR": "Desde o Hello World eu escrevi", "es": "Desde Hola Mundo he escrito"}),
    ("lines of code", {"pt-BR": "linhas de código", "es": "líneas de código"}),
    # -- headings ----------------------------------------------------------
    ("I'm an Early 🐤", {"pt-BR": "Eu sou diurno 🐤", "es": "Soy diurno 🐤"}),
    ("I'm a Night 🦉", {"pt-BR": "Eu sou noturno 🦉", "es": "Soy nocturno 🦉"}),
    ("I'm Most Productive on ", {"pt-BR": "Sou mais produtivo em ", "es": "Soy más productivo los "}),
    ("I Mostly Code in ", {"pt-BR": "Eu geralmente programo em ", "es": "Programo principalmente en "}),
    (
        "This Week I Spent My Time On",
        {"pt-BR": "Esta semana eu gastei meu tempo em", "es": "Esta semana me dediqué a"},
    ),
    ("Timeline", {"pt-BR": "Linha do tempo", "es": "Cronología"}),
    # -- section labels inside the ```text blocks --------------------------
    ("Time Zone", {"pt-BR": "Fuso horário", "es": "Zona horaria"}),
    ("Programming Languages", {"pt-BR": "Linguagens de programação", "es": "Lenguajes de programación"}),
    ("Editors", {"pt-BR": "Editores", "es": "Editores"}),
    ("Projects", {"pt-BR": "Projetos", "es": "Proyectos"}),
    ("Operating System", {"pt-BR": "Sistema operacional", "es": "Sistema operativo"}),
    # -- commit charts -----------------------------------------------------
    (r"\bMorning\b", {"pt-BR": "Manhã", "es": "Mañana"}),
    (r"\bDaytime\b", {"pt-BR": "Tarde", "es": "Día"}),
    (r"\bEvening\b", {"pt-BR": "Noite", "es": "Tarde"}),
    (r"\bNight\b", {"pt-BR": "Madrugada", "es": "Noche"}),
    (r"\bMonday\b", {"pt-BR": "Segunda-Feira", "es": "Lunes"}),
    (r"\bTuesday\b", {"pt-BR": "Terça-Feira", "es": "Martes"}),
    (r"\bWednesday\b", {"pt-BR": "Quarta-Feira", "es": "Miércoles"}),
    (r"\bThursday\b", {"pt-BR": "Quinta-Feira", "es": "Jueves"}),
    (r"\bFriday\b", {"pt-BR": "Sexta-Feira", "es": "Viernes"}),
    (r"\bSaturday\b", {"pt-BR": "Sábado", "es": "Sábado"}),
    (r"\bSunday\b", {"pt-BR": "Domingo", "es": "Domingo"}),
    # -- AI block (hardcoded English upstream, in every locale) ------------
    (
        "No AI Coding Activity Tracked This Week",
        {
            "pt-BR": "Nenhuma atividade de programação com IA registrada esta semana",
            "es": "Sin actividad de programación con IA registrada esta semana",
        },
    ),
    (
        "No Activity Tracked This Week",
        {"pt-BR": "Nenhuma atividade rastreada esta semana", "es": "Sin actividad registrada esta semana"},
    ),
    ("AI Coding This Week", {"pt-BR": "Programação com IA esta semana", "es": "Programación con IA esta semana"}),
    ("AI Coding Time", {"pt-BR": "Tempo de programação com IA", "es": "Tiempo de programación con IA"}),
    ("AI Coding Insights", {"pt-BR": "Análise da programação com IA", "es": "Análisis de la programación con IA"}),
    (
        r"(\S+) lines written by AI, (\S+) lines written by hand \((\S+)% AI-written\)",
        {
            "pt-BR": r"\1 linhas escritas por IA, \2 linhas escritas à mão (\3% vindas de IA)",
            "es": r"\1 líneas escritas por IA, \2 líneas escritas a mano (\3% provenientes de IA)",
        },
    ),
    (
        r"\$(\S+) Estimated AI Cost This Week",
        {"pt-BR": r"$\1 de custo estimado de IA esta semana", "es": r"$\1 de costo estimado de IA esta semana"},
    ),
    (
        r"(\S+) AI Sessions, (\S+) AI Prompts",
        {"pt-BR": r"\1 sessões de IA, \2 prompts de IA", "es": r"\1 sesiones de IA, \2 prompts de IA"},
    ),
    (
        r"(\S+) Input Tokens, (\S+) Output Tokens",
        {"pt-BR": r"\1 tokens de entrada, \2 tokens de saída", "es": r"\1 tokens de entrada, \2 tokens de salida"},
    ),
    # Model breakdown rows ("Opus  7,984 lines"); after the "lines written" rule above.
    (r"\b([\d,.]+) lines\b", {"pt-BR": r"\1 linhas", "es": r"\1 líneas"}),
    # -- AI insights: "<label> — <detail>" lines -----------------------------
    ("AI-Driven", {"pt-BR": "Guiado por IA", "es": "Impulsado por IA"}),
    ("Balanced with AI", {"pt-BR": "Equilibrado com IA", "es": "Equilibrado con IA"}),
    ("Mostly Hands-On", {"pt-BR": "Majoritariamente manual", "es": "Mayormente manual"}),
    ("Concise Prompter", {"pt-BR": "Prompts concisos", "es": "Prompts concisos"}),
    ("Detailed Prompter", {"pt-BR": "Prompts detalhados", "es": "Prompts detallados"}),
    ("Verbose Prompter", {"pt-BR": "Prompts extensos", "es": "Prompts extensos"}),
    ("One-Shot Prompter", {"pt-BR": "Um prompt por sessão", "es": "Un prompt por sesión"}),
    ("Iterative Prompter", {"pt-BR": "Prompts iterativos", "es": "Prompts iterativos"}),
    ("Hands-On Reviewer", {"pt-BR": "Revisor atento", "es": "Revisor atento"}),
    ("High AI Trust", {"pt-BR": "Alta confiança na IA", "es": "Alta confianza en la IA"}),
    (
        r"— (\S+)% of written lines came from AI",
        {"pt-BR": r"— \1% das linhas escritas vieram da IA", "es": r"— \1% de las líneas escritas provinieron de la IA"},
    ),
    (
        r"— average (\S+) characters per prompt",
        {"pt-BR": r"— média de \1 caracteres por prompt", "es": r"— promedio de \1 caracteres por prompt"},
    ),
    (
        r"— average (\S+) prompts per session",
        {"pt-BR": r"— média de \1 prompts por sessão", "es": r"— promedio de \1 prompts por sesión"},
    ),
    (
        r"— (\S+)% of changed lines were hand-edited",
        {"pt-BR": r"— \1% das linhas alteradas foram editadas à mão", "es": r"— \1% de las líneas modificadas fueron editadas a mano"},
    ),
    # -- footer, durations, placeholder values -----------------------------
    ("Last Updated on", {"pt-BR": "Última atualização em", "es": "Última actualización el"}),
    (r"\b(\d+) hrs?\b", {"pt-BR": r"\1 h", "es": r"\1 h"}),
    (r"\b(\d+) mins?\b", {"pt-BR": r"\1 min", "es": r"\1 min"}),
    (r"\b(\d+) secs?\b", {"pt-BR": r"\1 s", "es": r"\1 s"}),
    # "commits" is left alone on purpose — it is the word both communities use.
    (r"\bUnknown\b", {"pt-BR": "Desconhecido", "es": "Desconocido"}),
    (r"\bOther\b", {"pt-BR": "Outros", "es": "Otros"}),
]
RULES = [(compile(pattern), replacements) for pattern, replacements in RULES]

# A stats row: name (25 chars) + quantity (20 chars) + bar (25 chars) + percent.
BAR_SYMBOLS = "█░⣿⣀⬛⬜"
ROW = compile(rf"^(?P<name>.{{25}})(?P<text>.*?)(?P<bar>[{BAR_SYMBOLS}]{{25}})   (?P<percent>[\d.]+ % ?)$")

# shields.io badge: ![alt](https://img.shields.io/badge/<label>-<value>-<style>)
BADGE = compile(r"!\[(?P<alt>[^\]]+)\]\((?P<base>https?://img\.shields\.io/badge/)(?P<label>[^-]+)-(?P<value>[^-]+)-(?P<tail>[^)]+)\)")

# Both target locales write 1.234,56 where English writes 1,234.56.
NUMBER = compile(r"\d+(?:,\d{3})+(?:\.\d+)?|\d+\.\d+")


def localize_numbers(text: str) -> str:
    """Swap the thousands and decimal separators of every number in `text`."""
    return NUMBER.sub(lambda match: match.group(0).translate(str.maketrans(",.", ".,")), text)


def translate(text: str, locale: str) -> str:
    """Apply every rule that has a translation for `locale`, in order."""
    for pattern, replacements in RULES:
        if locale in replacements:
            text = pattern.sub(replacements[locale], text)
    return text


def translate_badge(line: str, locale: str) -> str:
    """Translate a shields.io badge, whose label and value are URL-encoded."""

    def encode(text: str) -> str:
        # shields.io reads a literal dash as "--" and a literal underscore as "__".
        return quote(text.replace("_", "__").replace("-", "--"))

    def replace(match) -> str:
        alt = translate(match["alt"], locale)
        label = encode(translate(unquote(match["label"]), locale))
        value = encode(translate(unquote(match["value"]), locale))
        return f"![{alt}]({match['base']}{label}-{value}-{match['tail']})"

    return BADGE.sub(replace, line)


def translate_row(match, locale: str) -> str:
    """Translate a stats row and rebuild its fixed-width columns."""
    name = translate(match["name"].rstrip(), locale)
    text = localize_numbers(translate(match["text"].rstrip(), locale))
    percent = localize_numbers(match["percent"])
    # Same truncation and padding as `make_list` in the action.
    return f"{name[:25]}{' ' * (25 - len(name))}{text}{' ' * (20 - len(text))}{match['bar']}   {percent}"


def translate_block(block: str, locale: str) -> str:
    """Translate the whole waka block, line by line."""
    lines = []
    for line in block.split("\n"):
        row = ROW.match(line)
        if row is not None:
            lines.append(translate_row(row, locale))
        elif BADGE.search(line) is not None:
            lines.append(translate_badge(line, locale))
        else:
            # Prose lines ("> " info, AI block) carry formatted numbers too.
            lines.append(translate(localize_numbers(line), locale))
    return "\n".join(lines)


def read_block(path: Path) -> str:
    match = search(BLOCK, path.read_text(encoding="utf-8"), DOTALL)
    if match is None:
        print(f"{path}: no {START} … {END} section found", file=stderr)
        exit(1)
    return match.group(0)


def main() -> None:
    block = read_block(SOURCE)
    changed = []

    for target, locale in TARGETS.items():
        if not target.exists():
            print(f"{target}: missing, skipped", file=stderr)
            continue

        contents = target.read_text(encoding="utf-8")
        read_block(target)  # fail loudly if the markers were dropped
        translated = translate_block(block, locale)
        updated = sub(BLOCK, lambda _: translated, contents, count=1, flags=DOTALL)

        if updated != contents:
            target.write_text(updated, encoding="utf-8")
            changed.append(str(target))

    print(f"Synced: {', '.join(changed)}" if changed else "Already in sync.")


if __name__ == "__main__":
    main()
