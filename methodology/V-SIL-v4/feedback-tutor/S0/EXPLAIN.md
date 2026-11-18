# S0 — Explicación del feedback del tutor

## T1 · Draft mode state transition

### Raw
> The skill states "The recorded S0 run… happens only when the human commits the draft", but provides no mechanism for the LLM to detect this commit. The LLM cannot observe a git commit or file system event unless explicitly instructed to check for it. Without a trigger to exit draft mode and execute the "recorded S0 run", the skill will either remain in draft mode indefinitely or fail to know when to write the official iteration.

### Explicación
La skill dice que existe un "modo borrador" activado por un archivo sentinela (`DRAFT`). Mientras existe, el agente puede editar el GT sin escribir una iteración oficial en el reporte. El problema: la skill dice "la iteración oficial ocurre cuando el humano *commits* el borrador", pero nunca define qué significa eso operativamente para el LLM. ¿Debe detectar un `git commit`? ¿Debe esperar que el humano borre el archivo `DRAFT`? ¿Debe esperar una instrucción verbal? Sin un trigger explícito, el agente se queda en modo borrador para siempre.

### Viabilidad: VÁLIDO
Es un error de ejecución real. La condición de entrada está clara (archivo `DRAFT` existe → modo borrador), pero la condición de salida está implícita. Un LLM no puede observar eventos del file system ni commits de git por sí solo — necesita una instrucción explícita de qué acción humana constituye el "commit del draft".

### Corrección
Se agregó un párrafo **"Exiting draft mode"** con dos triggers explícitos:
1. El humano dice "commit the draft" (instrucción verbal).
2. El humano borra el archivo `.codeanvil/report/<cycle>/DRAFT`.

Y la acción: reconciliar edits directos contra el Build Package (TRIAGE.md §2), escribir la iteración oficial, y si el archivo `DRAFT` aún existe, borrarlo.

---

## T2 · Re-entry cycle discovery

### Raw
> The instruction says "if another cycle's latest RFD.md iteration holds Superseded by cycle: <this cycle>". It does not instruct the LLM on how to find this other cycle. The LLM would need to list all directories in .codeanvil/report/, read every RFD.md, and parse the text to find a match. This is a multi-step file discovery and parsing task that is completely unstated.

### Explicación
Cuando un RFD (Request for Deviation) cierra un ciclo y abre otro, S0 necesita detectar si el ciclo actual es el "ciclo de re-entrada". Para eso debe encontrar otro ciclo cuyo `RFD.md` diga `Superseded by cycle: <este ciclo>`. El problema: la skill describe la condición lógica pero no dice cómo encontrar ese otro ciclo. El LLM tendría que listar todos los directorios en `.codeanvil/report/`, leer cada `RFD.md`, y parsear el texto — un proceso de múltiples pasos que nunca se especifica.

### Viabilidad: VÁLIDO
Es un error de ejecución. La condición es semánticamente correcta pero operativamente incompleta. Sin instrucciones de glob/traversal, el LLM puede: (a) no buscar del todo, (b) inventar un nombre de ciclo, o (c) buscar solo en un lugar equivocado. Es exactamente el tipo de instrucción que parece obvia para un humano ("busca en los reportes") pero que un LLM necesita explícita.

### Corrección
Step 4 ahora empieza con: "list every directory in `.codeanvil/report/` and read the latest iteration of each `RFD.md` found" antes de evaluar la condición `Superseded by cycle:`. El mecanismo de descubrimiento queda explícito.

---

## T3 · Contradictory inventory output

### Raw
> The Steps say "Inventory every statement… as STK | HWC | NRM | SYS | not mapped." The Output Contract says "Return… the inventory counts". The Report Description says "the inventory, the missing list… and the trace". It is unclear whether "the inventory" in the report means the full categorized mapping of every statement, or just the counts.

### Explicación
La palabra "inventory" aparece en tres lugares con granularidades distintas:
- **Steps** (paso 1): "inventaría cada declaración" → suena a un mapeo completo.
- **Report Description** (paso 5): "the inventory" → ¿el mapeo completo o solo los conteos?
- **Output Contract**: "inventory counts" → explícitamente solo conteos.

El LLM no sabe si debe producir una tabla detallada con cada statement clasificado, o solo un resumen tipo "STK: 12, HWC: 3, NRM: 5, SYS: 8, not mapped: 2". Dependiendo de qué interprete, el reporte será radicalmente diferente.

### Viabilidad: VÁLIDO
Es un error de ejecución por inconsistencia terminológica. Las tres secciones deberían usar la misma definición. Es un bug clásico de iterar sobre un documento sin actualizar todas las referencias cuando cambia la definición.

### Corrección
Se unificó en los tres lugares:
- **Step 1**: define que el inventario es un "full categorized mapping" (cada statement con su clasificación y block ID destino), y los conteos son un "summary line".
- **Step 5**: dice "full inventory + counts + missing list + trace".
- **Output Contract**: dice "full inventory mapping, counts summary, missing list".

---

## T4 · Dynamic template alteration vs. "Fill the blueprint"

### Raw
> The skill commands the LLM to "Fill the StRS blueprint" but simultaneously commands it to "Drop the author-guidance sections… and every empty blueprint placeholder row". This requires the LLM to semantically analyze the template's headings to distinguish between "scaffolding/guidance" and "actual spec sections", and then dynamically delete the scaffolding while copying the content. This violates the "no judgement" and "copy verbatim" rules.

### Explicación
El tutor ve una contradicción: la skill dice "copia el blueprint sin juicio" pero también dice "elimina las secciones de guía". Para eliminar secciones, el LLM tiene que decidir cuáles son guía y cuáles son contenido real — eso es un juicio.

### Viabilidad: PARCIALMENTE VÁLIDO
El tutor tiene razón en que "fill + drop" es una tensión retórica. PERO — y esto es lo que el tutor no puede ver sin el blueprint — las secciones a eliminar están **enumeradas por nombre exacto**: `### Block ID Convention`, `### Fields per Block`, `### Enumeration Values`, `### Block Format`, y patrones específicos de placeholder (`_What this document specifies…_`, `_TERM_ | _Precise definition_`, etc.). No es juicio abierto, es una lista finita de strings a borrar. Sin embargo, la forma en que estaba escrito ("Drop the author-guidance sections") suena a juicio semántico, cuando en realidad es pattern matching.

### Corrección
Se reescribió como tres pasos explícitos y ordenados:
1. **Copy** — copiar el skeleton completo del blueprint.
2. **Delete** — eliminar exactamente estos patrones (lista enumerada).
3. **Fill** — llenar cada sección restante desde el Build Package.

La secuencia copy→delete→fill elimina la ambigüedad: no es "juzga qué sobra", es "copia todo, borra esta lista específica, llena lo que queda".

---

## T5 · Unverifiable CLI dependencies

### Raw
> The skill relies on an external CLI tool codeanvil for backups, timestamps, and status checks. If this tool is not installed, not in the system PATH, or does not support these exact subcommands, the skill will fail.

### Explicación
El tutor nota que la skill usa comandos como `codeanvil backup S0`, `codeanvil now`, `codeanvil status` sin verificar que existan. Si no están instalados, la skill falla.

### Viabilidad: INVIABLE
La herramienta del tutor solo lee `SKILL.md` en aislamiento, sin contexto del sistema. `codeanvil` **es** la herramienta que crea y ejecuta los proyectos — es un prerequisito estructural. Es como decir "este Makefile asume que `make` está instalado". Las skills viven dentro de proyectos scaffoldeados por `codeanvil create`, que solo funciona si `codeanvil` ya está instalado. Los tres comandos existen y tienen tests:
- `codeanvil backup` → `tests/test_backup.py`
- `codeanvil now` → produce timestamps (`codeanvil.config.time`)
- `codeanvil status` → `tests/test_sync_cli.py`, `tests/test_create.py`

### Corrección
Aunque es inviable como bug, se agregó una línea `runtime:` en el frontmatter de la skill declarando explícitamente que `codeanvil` CLI debe estar instalado y en PATH (`codeanvil backup`, `codeanvil now`, `codeanvil status`). Esto documenta la dependencia para cualquier herramienta que lea la skill en aislamiento.
