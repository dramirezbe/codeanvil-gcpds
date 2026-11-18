# S0 — Análisis de los patches del tutor

Comparación patch por patch entre la skill actual (`templates/skills/S0_normalise_build_package/SKILL.md`) y la versión corregida propuesta por el tutor.

---

## P-01 · Quitar "no scripts" del campo compatibility

**Cambio:** `"No network access, no scripts."` → `"No network access."`
**Rationale del tutor:** Contradice el script Python para SHA-256 que aparece más adelante.

**Veredicto: RECHAZAR.**

El tutor ve una contradicción porque la skill tiene un one-liner `python -c "import hashlib..."`. Pero "no scripts" en el contexto de V-SIL se refiere a que la skill no tiene scripts propios en su carpeta `scripts/` (como G0 que tiene `g0_validate.py`). El one-liner de Python es un comando inline que el agente ejecuta, no un script del skill. Además, en la rama `feat/vsil-v4` ese one-liner ya fue reemplazado por `codeanvil custody digest` (C5), así que la supuesta contradicción desaparece con el merge. Quitar "no scripts" abriría la puerta a que alguien piense que puede agregar scripts a S0, lo cual no es el diseño.

**Acción:** Cuando el merge de `feat/vsil-v4` llegue a main, el one-liner desaparece y la contradicción se resuelve sola. No hay que tocar `compatibility`.

---

## P-02 · Agregar "Python 3 MUST be installed" al runtime

**Cambio:** Agregar `Python 3 MUST be installed and on PATH.` al campo `runtime`.
**Rationale del tutor:** El script de SHA-256 necesita Python.

**Veredicto: RECHAZAR.**

Misma razón que P-01. El one-liner `python -c hashlib...` está condenado a muerte por D14 (`codeanvil custody digest`). Agregar Python 3 como dependencia explícita de S0 sería incorrecto — S0 no ejecuta Python por diseño; `codeanvil` (escrito en Python) es la dependencia, y esa ya está declarada en `runtime`. Cuando un skill necesita Python real (como G0 con `g0_validate.py`), lo declara en su frontmatter `runtime: "methodology"`.

---

## P-03 · Re-entry: "evaluate if the Build Package has changed"

**Cambio:** `"this is the re-entry cycle and the whole flow is redone from here. Compute the SHA-256"` → `"this is the re-entry cycle. Before re-normalising, evaluate if the Build Package has changed. Compute the SHA-256"`
**Rationale del tutor:** Clarifica que la evaluación es condicional, no que el flujo se rehace incondicionalmente.

**Veredicto: ACEPTAR.**

Es una mejora de claridad legítima. La redacción actual dice "the whole flow is redone from here" seguido inmediatamente de un check de digest que puede abortar — lo que contradice "redone from here". La propuesta del tutor es más precisa: primero evalúa si el Build Package cambió, y solo entonces procede. No cambia la semántica, solo la hace explícita.

---

## P-04 · Corregir path de blueprints en tabla Inputs

**Cambio:** `templates/skills/S0_.../templates/StRS.md` → `.agents/skills/S0_.../templates/StRS.md`
**Rationale del tutor:** El path debe usar `.agents/skills/` que es la estructura estándar del proyecto scaffoldeado.

**Veredicto: RECHAZAR.**

El tutor no tiene contexto del sistema de path rewriting. La skill vive en `templates/skills/` en el REPO SOURCE. Durante scaffold, `codeanvil create` copia a `.agents/skills/` y ejecuta `path_replacements` del `config.yaml` sobre todos los `.md`. El path `templates/skills/...` es CORRECTO para el source template — se reescribe automáticamente a `.agents/skills/...` en el proyecto scaffoldeado. Si ponemos `.agents/skills/` en el source, el rewriter lo dejaría intacto pero el path sería incorrecto en el contexto del repo (no existe `.agents/` en el repo source).

---

## P-05 · Re-evaluar Decision Table al salir de draft mode

**Cambio:** Agregar "Re-evaluate the Decision Table to determine the correct action (e.g., ask before overwriting a hand-written pair)" al inicio de "Exiting draft mode".
**Rationale del tutor:** Previene bypass silencioso de la protección de overwrite para pares escritos a mano.

**Veredicto: ACEPTAR.**

Buen catch. Si el agente entra en draft mode sobre un par hand-written, al salir debería re-evaluar la Decision Table para verificar si aún aplica la fila "ask once before overwriting". Sin esto, el agente podría sobreescribir un par hand-written sin preguntar después de un draft. Es una mejora de seguridad procedimental.

---

## P-06 · Restaurar catch-all para placeholders vacíos

**Cambio:** `"Delete exactly these guidance patterns"` → `"Delete the following guidance patterns — they are not requirements, including any empty blueprint placeholder row or instruction sentence:"`
**Rationale del tutor:** Restaura la regla catch-all para placeholders vacíos que se perdió en nuestro refactor T4.

**Veredicto: ACEPTAR.**

Nuestro fix de T4 (reescribir como copy→delete→fill) accidentalmente eliminó la frase "and every empty blueprint placeholder row or instruction sentence" que estaba en la versión original. La lista enumerada cubre los patrones CONOCIDOS, pero la frase catch-all cubre cualquier placeholder vacío que no esté en la lista explícita. Es un safety net válido que se perdió en el refactor.

---

## P-07 · Decision Table: integrar referencia a Re-entry

**Cambio:** `"Re-normalise, applying the latest G0 feedback (an RFD re-entry lands here)"` → `"Re-normalise: execute the ## Re-entry procedure to apply the latest G0 feedback before filling the blueprints."`
**Rationale del tutor:** La sección Re-entry estaba "huérfana" — existía pero nada la invocaba desde el flujo principal.

**Veredicto: ACEPTAR.**

La sección `## Re-entry` explica qué hacer con G0 FEEDBACK, pero ni la Decision Table ni los Steps la referencian explícitamente. El agente podría llegar a "Re-normalise" y no saber que debe ejecutar primero el procedimiento de Re-entry. Agregar la referencia explícita cierra esa brecha.

---

## P-08 · Steps: agregar branch condicional para Re-entry

**Cambio:** Agregar al inicio de Steps: `"If the Decision Table routes to Re-normalise via G0 FEEDBACK, execute the ## Re-entry procedure first. Otherwise,"`
**Rationale del tutor:** Integra la rama de Re-entry en la secuencia lineal de Steps para que no se pueda saltear.

**Veredicto: ACEPTAR.**

Complementa P-07. La Decision Table ahora dice "execute ## Re-entry", y los Steps ahora tienen el branch point explícito. Sin esto, un agente que sigue Steps linealmente se saltaría Re-entry incluso cuando la Decision Table lo requiere.

---

## Resumen

| Patch | Veredicto | Razón |
|-------|-----------|-------|
| P-01 | ❌ RECHAZAR | "no scripts" se refiere a scripts del skill, no a one-liners; el one-liner desaparece con v4 |
| P-02 | ❌ RECHAZAR | Python 3 no es dependencia de S0; `codeanvil` (ya declarado) lo es |
| P-03 | ✅ ACEPTAR | Mejora de claridad: condicional explícito antes de re-normalizar |
| P-04 | ❌ RECHAZAR | Path es correcto para source template; `path_replacements` lo reescribe en scaffold |
| P-05 | ✅ ACEPTAR | Seguridad procedimental: re-evaluar Decision Table al salir de draft |
| P-06 | ✅ ACEPTAR | Restaura catch-all para placeholders perdido en nuestro refactor T4 |
| P-07 | ✅ ACEPTAR | Cierra brecha: Decision Table ahora referencia explícitamente ## Re-entry |
| P-08 | ✅ ACEPTAR | Cierra brecha: Steps tiene branch point para Re-entry |

**4 rechazados, 4 aceptados.**
