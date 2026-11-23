# AGENTS.md — Explicación del feedback del tutor

Entrada: [audit original](raw/raw-audit-output.txt), conservado sin cambios junto
con sus cuatro SVG. El tutor examinó un AGENTS generado llamado `SKILL_pre_david.md`,
sin las skills, el CLI ni sus referencias. Ese archivo original y el instrumento
`Navaja_(6).md` no se aportaron; no se presume identidad exacta con nuestro ejemplo.
El contraste local parte del commit `2af198d532986ffef70da40c20e140e228a3584d`.

## Resumen

| ID | Viabilidad como defecto | Diagnóstico y acción |
|----|------------------------|---------------------|
| N-01 | VÁLIDO | Regla general de admisión demasiado amplia; corregida. |
| N-02 | VÁLIDO | `Next:` puede pertenecer al ciclo anterior; corregida la secuencia. |
| N-03 | VÁLIDO | Falta la salida ante selección de un ciclo cerrado; corregida. |
| N-04 | INVIABLE como error demostrado | Las skills y el parser ya distinguen scopes; resumen aclarado junto con N-01. |
| N-05 | VÁLIDO | Restricción de hardware expresada con alcance excesivo; corregida. |
| N-06 | INVIABLE como error demostrado | La independencia es procedimental y su límite técnico está declarado. |
| N-07 | VÁLIDO | S2 falta en la enumeración de PASS como entrega; corregida. |
| N-08 | PARCIALMENTE VÁLIDO | Identidad no implica recuperabilidad; existen backups y Git, sin garantía universal de reproducción. |
| N-09 | INVIABLE como error demostrado | La semántica de scopes y custody está en implementación y pruebas no aportadas al tutor. |
| N-10 | INVIABLE como error demostrado | G3 y S0 ya exigen autoridad del autor para deltas GT; referencia general aclarada. |
| N-11 | INVIABLE como error demostrado | El propio tutor lo identifica como límite del audit documental. |

Son **5 errores documentales de ejecución**, **1 limitación parcialmente válida**
y **5 observaciones dependientes de contexto**, no once errores de metodología.
INVIABLE aquí rechaza la atribución de un defecto probado; no invalida las preguntas
del tutor ni garantiza que todas las ejecuciones futuras sean correctas.

El audit presenta primero 4 errores/7 no verificables y luego corrige a 5/6.
Su tabla individual contiene 5 de ejecución y 6 no verificables. Se conserva esa
inconsistencia del original; nuestra clasificación contextual es independiente.

## N-01 — Admisión nominal y reentrada

**Raw:** “The general execution rule requires the predecessor to pass before a subsequent step can execute.”

**Viabilidad: VÁLIDO, como contrato de referencia.** Las Rules absolutas pueden
bloquear rework y delta-intake, aunque el final del documento admita excepciones.
No es un defecto conceptual de las compuertas: la
[skill S2](../../../../templates/skills/S2_plan_modules/SKILL.md), en Prerequisite
and Cycle y Delta-intake, distingue avance, reparación e intake antes de los
prerrequisitos de planificación. Intake no publica S2 ni autoriza implementar.

**Corrección aplicada:** limitar PASS del predecesor al avance nominal; remitir
rework/intake/sync a la admisión explícita de su skill. Calificar igualmente la
tabla y las reglas de Available Skills por scope. FEEDBACK solo no autoriza nada.

**Aclaración posterior del autor:** una vez publicado el FEEDBACK con razones y
sugerencias en el `### Description` de la iteración, el mismo agente padre carga
la skill de la etapa responsable y ejecuta el rework acotado leyendo ese reporte.
No se limita a anunciar la ruta ni pide repetir el feedback. Se mantienen la
autoridad sobre GT, los bloqueos reales, los contextos frescos y el nuevo veredicto
humano de la compuerta. No se crea un canal de correcciones adicional al reporte.

## N-02 — Estado consultado antes de elegir el ciclo

**Raw:** “The project-state discovery operation is not explicitly rebound to the selected cycle.”

**Viabilidad: VÁLIDO.** El
[CLI status](../../../../src/codeanvil/CLI/commands/status.py) muestra todos los
ciclos, pero imprime `Next:` solamente para el activo. No actualiza `cycle:` por
haber mostrado otro ciclo. Una consulta previa no sirve para escoger el siguiente
paso después de cambiar A por B.

**Comprobación:** proyecto y DB temporales, con reportes sintéticos: A tiene
entregas hasta G2 y produce `Next: S3`; B llega a G0 y, tras seleccionarlo, produce
`Next: S1`. No son ejecuciones ni aprobaciones humanas de V-SIL.

**Corrección aplicada:** registrar la selección, volver a ejecutar `codeanvil status`
y usar exclusivamente su `Next:` del ciclo seleccionado. Para un ciclo nuevo sin
reportes ni `Next:`, comenzar en S0.

## N-03 — Selección de un ciclo cerrado

**Raw:** “The cycle-selection decision tree contains an incomplete branch.”

**Viabilidad: VÁLIDO.** Ofrecer todos los ciclos y prohibir después su reanudación
deja una rama sin salida explícita. Las skills ya detienen ciclos cuyo RFD tiene
`Superseded by cycle`, pero eso no completa la instrucción de selección del agente.

**Corrección aplicada:** ofrecer solo ciclos abiertos como reanudables. Si el usuario
nombra uno cerrado, explicar el cierre y pedir uno abierto o nuevo, sin activarlo
ni reabrirlo. Si el status actualizado detecta cierre, volver a seleccionar.
Se distingue la conservación de ciclos cerrados de la reanudación de abiertos.

## N-04 — Prerrequisitos por scope

**Raw:** “The conceptual requirement is present, but its enforcement cannot be confirmed.”

**Viabilidad: INVIABLE como defecto demostrado; falta contexto.** S2 exige el último
G3 del scope anterior solo para avance; un FEEDBACK posterior del mismo scope
invalida un PASS antiguo. El rework usa la admisión del feedback, no un PASS del
scope que se repara. Esto es explícito en S2 y tiene un lector dedicado:
[`scoped_report_state`](../../../../src/codeanvil/reports.py).

Las [pruebas de límites v4](../../../../tests/test_v4_flow_boundaries.py) cubren
`test_scoped_history_never_reuses_pass_after_same_scope_feedback` y el retorno
a G2 después de replanificar el scope fallido. Es evidencia de contratos concretos,
no prueba de que cualquier agente los respetará. La ambigüedad del resumen general
se corrige con N-01; no se añade otro mecanismo de admisión.

## N-05 — Límite temporal de hardware

**Raw:** “Nothing hardware-related is written before G3.”

**Viabilidad: VÁLIDO.** Esa afirmación prohíbe literalmente las restricciones COTS
que van al GT y la configuración MCP prevista antes de implementar. La intención
de diferir el enrollment no justifica prohibir toda descripción de hardware.

**Corrección aplicada:** distinguir restricciones, provisioning y enrollment.
La restricción de G3 se refiere a nuevos registros de enrollment; no impide
describir COTS, configurar MCP o utilizar declaraciones de targets existentes.
Se conserva la cadencia existente; no se ejecutó enrollment ni acceso a hardware.

## N-06 — Independencia y permisos del verificador

**Raw:** “Verification independence is procedural rather than technically enforced.”

**Viabilidad: INVIABLE como defecto demostrado; límite técnico reconocido.**
El [cuerpo del verificador](../../../../templates/agents/vsil-verifier.md) prohíbe
ediciones y decisiones HITL; [config.yaml](../../../../templates/config.yaml)
restringe herramientas de Claude/OpenCode. Codex hereda permisos y sus instrucciones
no constituyen un sandbox del SO: AGENTS ya lo declara explícitamente.

Las [pruebas de subagentes](../../../../tests/test_vsil_subagents.py) comprueban
generación y herramientas, no aislamiento adversarial universal. La custodia
identifica cambios del candidato, pero no impide físicamente toda escritura.
**Acción:** mantener esa limitación honesta; no inventar una garantía técnica ni
convertir un sandbox adicional en requisito de la metodología.

## N-07 — PASS de S2

**Raw:** “S2 is absent from this enumeration.”

**Viabilidad: VÁLIDO.** Report Format enumera S0, S1 y S3, omitiendo el nuevo S2.
En cambio, [S2](../../../../templates/skills/S2_plan_modules/SKILL.md) dice
explícitamente que PASS significa planes entregados y que solo el humano decide G2.
`stage_reports` en config incluye S0, S1, S2 y S3.

**Corrección aplicada:** incluir S2 y comprobar la enumeración del documento
generado contra los stages configurados. No se agrega una aprobación antes de G2.

## N-08 — Historial e integridad frente a recuperación

**Raw:** “A report can retain a digest identifying an earlier artifact without retaining the artifact itself.”

**Viabilidad: PARCIALMENTE VÁLIDO, como límite de garantía.** La distinción es correcta:
un hash no recupera bytes. Sin embargo, el tutor no recibió
[`backup.py`](../../../../src/codeanvil/CLI/commands/backup.py), los targets de
config ni las instrucciones S3/G3: hay copias de GT/diseño/planes/evidencia antes
de sobrescritura; la recuperación de código corresponde a Git, no a esos backups.

[test_backup.py](../../../../tests/test_backup.py) comprueba copias/manifiestos,
proveniencia por RFD, reanudación y planes con nombres iguales en rutas distintas.
Esto no demuestra reconstrucción integral de todos los ciclos ni conservación
automática de dependencias externas. **Aclaración aplicada:** diferenciar identidad,
backups de trabajo y referencias Git; no prometer reproducibilidad universal.

## N-09 — Custodia entre scopes sucesivos

**Raw:** “Its actual staleness resolution is delegated to `codeanvil status` and the custody implementation.”

**Viabilidad: INVIABLE como defecto demostrado; falta contexto.** S2 enlaza su
`Based on` con G1; cita el G3 anterior como proveniencia, sin convertirlo en un
archivo append-only que deba conservar su digest. S3/G3 comprueban el predecesor
actual, mientras verify global conserva las diferencias históricas como diagnóstico.

`test_cadence_keeps_historical_g3_differences_out_of_current_prerequisite`, en
[los límites v4](../../../../tests/test_v4_flow_boundaries.py), demuestra que
cambian los árboles históricos mientras el candidato admitido sigue fresco, y
que editar manualmente el plan sí bloquea. **Acción:** no cambiar el algoritmo
a partir de una hipótesis no reproducida como fallo; conservar la distinción
entre check del candidato y diagnóstico histórico.

## N-10 — Autoridad de deltas GT

**Raw:** “Ground Truth delta acceptance and author authorization are not explicitly bound.”

**Viabilidad: INVIABLE como defecto metodológico demostrado; el contrato está en las skills.**
[G3](../../../../templates/skills/G3_adaptive_verification/SKILL.md), en Slice
cadence and integrity, pide autoridad del autor del Build Package para GT y prohíbe
inferir aceptación desde PASS. [S0](../../../../templates/skills/S0_normalise_build_package/SKILL.md),
en Delta-sync, detiene cambios sin esa autoridad y limita su escritura al payload
aceptado. S2 intake conserva la aceptación explícita; no la crea.

No se exige que reviewer y autor sean la misma persona ni se supone que lo sean.
**Aclaración aplicada:** explicitar esa autoridad en AGENTS; una aprobación de G3
por otra persona no reemplaza al autor. Se refleja un requisito existente, sin
crear una nueva compuerta o implementar autenticación de identidades.

## N-11 — Dependencias no aportadas al audit

**Raw:** “This finding is a limitation of the available evidence, not a confirmed defect in the methodology.”

**Viabilidad: INVIABLE como defecto a corregir.** El propio audit delimita su
evidencia. Aquí sí se inspeccionaron las skills activas, referencias, CLI y
subagentes relevantes; las pruebas locales no equivalen a una ejecución completa
de la metodología con decisiones humanas ni a validación física.

**Acción:** registrar qué se examinó y los límites de la comprobación. No agregar
un orquestador ni copiar todas las skills dentro de AGENTS para satisfacer una
herramienta que revisó únicamente ese archivo.

## Correcciones y verificación

Las cinco correcciones y las aclaraciones N-04/N-08/N-10 están en el commit
`e44d7c000b69ebe807b0f42653ebff53d5437fc5`, sobre la plantilla generadora,
no sobre un archivo arbitrario entregado al tutor. No cambian el CLI ni las skills.

Comando ejecutado:

```bash
.venv/bin/python -m pytest -q tests/test_vsil_agents_md.py tests/test_create.py tests/test_report_state.py tests/test_v4_flow_boundaries.py tests/test_v4_scope_contracts.py tests/test_backup.py tests/test_vsil_subagents.py
```

Resultado: **135 passed**. Incluye generación, admisión/scopes, estado, backups y
contratos de subagentes. Además se comprobó N-02 con dos ciclos sintéticos y DB
aislada. No se ejecutaron gates humanos ni pruebas hardware.

El audit entregado dice expresamente que no propone patches. Por ello no se crea
un `corrected/PATCHES.md` ficticio ni un `corrected/ANALYSIS.md` de patches inexistentes.
La carpeta queda preparada para la segunda parte del procedimiento original.
