# Refactor HIL — autonomía de laboratorio y revisión antes del hardware

**Estado: implementación autorizada y en curso con subagentes.** Base revisada:
`a155f01` en `feat/hil-pil`. Este documento recoge las seis correcciones del
usuario a la [implementación anterior](2026-11-10_1057_hil_mcp.md).

**Filosofía: lo más simple posible, poca implementación y flujo completo.** El
agente prepara el equipo y ejecuta las pruebas; el humano conserva las pausas
HITL actuales y dispone de una parada real para revisar el código antes de
desplegar o probar en hardware. Solo las operaciones claramente destructivas
utilizan la puerta `trusted`.

## 1. Decisiones del refactor

| Tema | Decisión |
|------|----------|
| SSH normal | Permitir comandos generales, scripts, paquetes, métricas y `sudo`; retirar la lista de comandos permitidos |
| Acciones destructivas | Conservar `ssh_exec_cmd_trusted` para una lista pequeña y explícita |
| Alta del equipo | Retirar `--target` de la interfaz normal; descubrir MAC por SSH y registrar el administrador de bootstrap |
| Varios PCs/proyectos | Reutilizar claves locales por equipo; cada PC añade sus propias claves al mismo `codeanvil-agent` |
| S2 | Conservar construcción, pruebas por capas/módulos/servicios, pausa configurable y contrato de entrega; cambiar únicamente la operación HIL |
| Antes del hardware | Parar, mostrar el candidato y esperar `continue` antes de desplegar, actualizar o iniciar pruebas físicas |
| Git | Código y kit sin cambios pendientes, rama con upstream y commits publicados antes del hardware; sin manifiestos HIL |
| Equipo remoto | El agente actualiza CodeAnvil, proyecto y dependencias después de la revisión; comprueba que funcionan |
| Relojes | El agente diagnostica y sincroniza antes de medir; no crear herramienta o gate de sincronización |
| Telemetría | Nombre ligado a ciclo/iteración/hora; evidencia incompleta se investiga y se decide si repetir |
| Métricas | Scripts elegidos o escritos por el agente según el requisito y las tolerancias; calibración solo cuando haga falta para sostener la conclusión |
| Evidencia | `measurement.json` pequeño, sin hashes por archivo, digest de despliegue ni solicitud formal de captura |
| Estado | Mismos reports, cycles, iterations, `Based on`, HITL y rutas de rework |

### Alta y reutilización del mismo hardware

El usuario indica únicamente dirección/puerto y el administrador de bootstrap:

```sh
codeanvil credential-setup -u pi -i raspberry.local
```

El comando descubre la MAC en la Raspberry mediante SSH, sin pedir un alias
`--target` ni inferir identidad de su IP. Registra el usuario administrador y la
MAC, con papeles distintos: el primero autoriza el alta y la segunda reconoce
el equipo. Las claves locales se asocian al equipo, no al nombre del administrador:
cambiar de administrador no debe regenerarlas para el mismo hardware.

Puede haber MAC distintas para Ethernet y WiFi. Se conserva una MAC estable como
identidad y las otras observadas como referencias del mismo equipo; cambiar de
IP o entre interfaces conocidas no da de alta otra Raspberry. La identidad MAC
no reemplaza la autenticación SSH del equipo. Si no se puede reconocer, se informa;
no se regeneran claves silenciosamente por un cambio de endpoint.

Comportamiento requerido:

| Situación | Resultado |
|-----------|-----------|
| Mismo PC/usuario local, misma Raspberry, otro proyecto | Reutilizar claves y comprobar acceso; registrar/enlazar metadata del proyecto, sin repetir el bootstrap administrativo |
| Otro PC/usuario local, misma Raspberry | Crear claves de ese cliente si no existen y autorizar sus públicas en el mismo usuario remoto `codeanvil-agent` |
| Repetir el alta desde ese segundo PC | Reutilizar sus claves, sin duplicar entradas ni reemplazar las de otros PCs |
| Cambiar IP o administrador de una Raspberry reconocida | Actualizar datos de conexión/alta y conservar las claves locales existentes |

Las claves privadas viven solo en el almacenamiento local de cada cliente; nunca
en Git ni en la metadata compartida del proyecto. Un PC nuevo necesita una primera
autorización administrativa para añadir sus públicas: clonar el proyecto no concede
por sí solo acceso SSH. El alta añade únicamente las claves de ese cliente y no
trunca `authorized_keys`, recrea el usuario ni invalida el acceso de otros PCs.

El almacén local pasa de depender de un alias a depender de la MAC normalizada,
con un pequeño registro de endpoint/administrador y sus claves. Antes de crear
claves, se comprueban las existentes del esquema anterior para reutilizarlas al
reconocer el equipo. Los identificadores/aliases internos antiguos pueden seguir
leyéndose por compatibilidad; no son un argumento que el usuario deba escoger.

La metadata compartida contiene identidad del equipo, endpoint, puerto, usuario
remoto `codeanvil-agent` y workspace; no rutas locales a claves ni contraseñas.
Los proyectos usan subdirectorios del UUID de proyecto ya existente, bajo una raíz
estable de trabajo del equipo. La clave de despliegue se confina a esa raíz estable
para poder reutilizarla entre proyectos. Un mismo proyecto clonado conserva su
workspace; proyectos distintos no se pisan. Compartir usuario/acceso no implementa
ejecuciones simultáneas aisladas: el laboratorio coordina el uso, sin añadir un
servicio de locks o un gestor de sesiones.

## 2. Flujo operativo propuesto

1. Abrir/resumir el ciclo y comprobar el predecesor con las skills actuales.
2. En S2, elegir el calendario de pausas existente y construir/probar como ahora.
3. Preparar el candidato local y comprobar que todo está committed y pushed.
4. Mostrar el código/kit que se va a desplegar, destino/dispositivo y operaciones
   previstas. **Parar y esperar a que el usuario termine su revisión.**
5. Tras `continue`, actualizar el equipo, sincronizar relojes y desplegar el
   candidato publicado, preservando bases de datos y estado del destino.
6. Ejecutar pruebas y scripts de medida, recoger resultados y telemetría. El
   agente resuelve dependencias y problemas operativos dentro del alcance revisado.
7. Investigar anomalías; repetir la adquisición cuando proceda, con nombre nuevo.
8. Entregar S2 y ejecutar G2 en contexto fresco, conservando sus decisiones humanas.
   G2 también pasa por la revisión previa al hardware antes de su lote de pruebas.
9. Si G2 devuelve feedback, explicar evidencia, causa, alcance y acción; reentrar
   por la ruta vigente, en el mismo ciclo y con las iteraciones normales.

No se añade `codeanvil run`, otro orquestador, un motor de permisos, perfiles
nuevos ni un estado de aprobación paralelo. La secuencia sigue en las skills.

## 3. SSH: permiso por defecto y trusted para destrucción explícita

`ssh_exec_cmd` ejecutará comandos normales sin exigir un vocabulario de lectura,
un prefijo `cd` especial o cambiar de herramienta por usar `sudo`. Los ejemplos
del kit seguirán situándose en el workspace por corrección de rutas.

La lista de desvío a `trusted` cubrirá como mínimo:

- `systemctl`, `reboot`, `shutdown`, `poweroff` y `halt`.
- Borrado recursivo con `rm`, incluyendo variantes de `rm -rf`, flags separados
  y opciones largas; las operaciones de formateo/borrado de discos también.
- Borrar, sustituir, truncar o modificar explícitamente bases de datos o su estado.
  Lectura simple con `ls`, `stat` o `cat` no requiere trusted. Por sencillez, una
  llamada a una herramienta de base de datos que pueda escribir se trata como
  trusted; no se implementa un analizador SQL para distinguir cada sentencia.

La inspección de comandos será pequeña, por tokens/nombres/opciones reconocibles;
si encuentra una acción destructiva en un comando compuesto, desvía la llamada
completa y conserva el comando exacto en la auditoría. No se intenta interpretar
Python, demostrar qué hará cualquier script ni construir un sandbox adversarial.
El agente debe usar trusted cuando sabe que un script hará una acción destructiva.

La política del runtime gobierna la aprobación de esa herramienta. El modo full
access del host puede omitir prompts: la documentación no puede prometer un
diálogo que el MCP no controla. El checkpoint de revisión previo al hardware
sigue siendo una espera explícita de la skill, incluso en ese modo.

`code_sync` preservará bases de datos del destino, incluidos sidecars SQLite,
y el estado persistente declarado: excluirlos tanto del envío/sobrescritura
como del borrado por `rsync --delete`. Quitar solo `--delete` no evita sobrescribir
una base existente. Si el ensayo requiere modificarla, se hace explícitamente
por trusted. Se mantienen claves dedicadas, host/puerto y snapshots de descarga.

## 4. Checkpoint previo al hardware, sin alterar S2 ni los reportes

Se conserva **exactamente** el calendario actual de S2: pregunta por iteración,
tres opciones de granularidad, pausa de integración y respuestas
`continue`, `rework`, `stop`. El nuevo checkpoint se aplica a todas las opciones.
Si coincide con una pausa ya prevista, se presenta una sola pausa que cubra ambas.

La revisión ocurre antes del primer despliegue o actualización del lote y antes
de ejecutar contra un dispositivo local. Un probe de inventario de solo lectura
puede precederla. La aprobación identifica destino, dispositivo, candidato y
alcance de preparación/pruebas; no exige permiso por cada comando ordinario.

La pausa muestra diferencias y archivos relevantes, rama/commit publicado,
resultado de las pruebas locales y qué se ejecutará en el equipo. Espera una
respuesta real: ni silencio, ni un temporizador, ni un aviso equivalen a continuar.
Una nueva entrega, iteración, destino o cambio de código tras la revisión exige
renovar el checkpoint. Repetir una adquisición del mismo candidato dentro del
alcance revisado no exige otra pausa por cada intento.

Se usa la línea narrativa existente:

```text
Checkpoint: pre-HW review — continue — <destino, candidato y alcance revisados>
```

La línea se incluye en la Description de la iteración entregada. No es un gate,
un nuevo valor HITL ni un archivo de estado. Mientras se espera no se escribe
una sección `## Iteration` parcial ni se marca PASS. En S2, `stop` conserva su
semántica: no escribir iteración y dejar el trabajo para reanudar. Se reconoce
el stop en conversación sin modificar retrospectivamente reportes anteriores.

El padre de G2 presenta la pausa; el verificador nunca pregunta al humano. Tras
ella puede ejecutar pruebas reales con las herramientas autorizadas. Conserva
contexto fresco, no cambia el código del producto ni los umbrales y no decide HITL.
El padre gestiona preparación y cualquier trusted necesario; no hay un operador
humano obligatorio para lanzar la captura. Si el runner necesita ampliar alcance,
lo devuelve al padre, que resuelve la pausa pertinente.

Invariantes a conservar y comprobar sobre el scaffold generado:

- `.codeanvil/report/<cycle>/<stage>.md`, append-only, una iteración por entrega.
- `Based on: G1 iteration <N>` en S2 y `Based on: S2 iteration <N>` en G2 como
  primera línea de Description; mismas reglas de staleness, RFD y ciclos cerrados.
- `HITL: PASS|FEEDBACK`; ninguna pausa operativa altera el último veredicto.
- `S2_artifacts/test_run.md`, backups y `G2_artifacts/verified_prototype.md`.
- Rework S2 dentro del mismo ciclo; un defecto de diseño sigue por S1 → G1 → S2.

El parser actual toma la última sección en orden de archivo: una sección nueva
sin veredicto la convertiría en UNKNOWN. Por eso no se usa el reporte como estado
provisional de la pausa. `codeanvil status` tampoco anunciará una pausa no reportada.

## 5. Preparación automática: Git, actualización y relojes

Antes del checkpoint, el agente revisa `git status --porcelain`, actualiza la
referencia remota y comprueba HEAD/upstream. No basta con «nada unstaged»: tampoco
puede quedar código staged o untracked sin publicar. La rama debe tener upstream,
árbol limpio y estar sincronizada con la referencia publicada. Un push fallido no
permite avanzar al hardware. El agente puede preparar commits/push dentro de su
autorización vigente; no fuerza push, descarta cambios ni inventa un remoto.

El despliegue usa solo el candidato committed y publicado. Para que los archivos
ignorados presentes en el host no se cuelen en rsync, usar una exportación temporal
del árbol Git publicado —por ejemplo `git archive HEAD`— como origen del envío.
No se crea un inventario persistente ni un manifiesto/hash HIL. Los logs/resultados
siguen la política normal del repositorio; no se ignora código para eludir el chequeo.

Después de `continue`, el agente instala/actualiza lo necesario en HW y comprueba
los comandos que necesita. Distingue el repo/ref de **CodeAnvil** del repo/ref del
**proyecto entregado**. Un candidato de la herramienta sin release puede instalarse
desde su referencia ya pusheada; no se deduce un tag a partir de la versión numérica
ni se instala el commit del proyecto como si fuera CodeAnvil.

Las versiones se registran y los fallos se resuelven automáticamente. Se retira el
bloqueo por igualdad exacta de SemVer; importa que funcionen las capacidades usadas.
No se introduce un nuevo gestor de versiones o un protocolo de atestación.

Para relojes, el agente usa las herramientas disponibles del sistema: consulta hora
UTC/servicio de tiempo y habilita o corrige sincronización cuando haga falta. Si usa
`systemctl`, pasa por trusted. Sincroniza **antes** de medir; durante la adquisición
usa duraciones monotónicas y evita cambiar la hora. Registra incidencias y su efecto
en las medidas; si afectan al criterio, investiga y repite, sin un gate de reloj nuevo.

## 6. Métricas, telemetría y feedback explicable

El agente elige herramientas o escribe scripts para medir lo que pide el GT.
S2 entrega las pruebas y scripts de verificación. G2 puede diagnosticar con medidas
auxiliares y devolver observaciones, sin editar el DUT, cambiar el umbral ni sustituir
una prueba requerida ausente: si falta esa prueba, lo explica y vuelve a S2.

No se exige calibración, fuente calibrada, oráculo formal o presupuesto GUM para
cada prueba funcional. El agente razona si el método y la resolución son suficientes
para la tolerancia solicitada y registra esa justificación. Si el requisito sí exige
calibración/correcciones, debe satisfacerlo o declarar el resultado inconcluso; no
amplía tolerancias ni inventa medidas para conseguir PASS. PIL con Mock HAL sigue
siendo VERIFIED; una afirmación real se limita a lo que el ensayo demuestra.

Identificador de ejecución: `<cycle>_<iteration>_<codeanvil now --machine>`.
`iteration` es la iteración de la etapa S2/G2 que se está realizando, no un contador
HIL nuevo; la etapa y el destino se registran en el resultado. Un intento adicional
usa otro timestamp dentro de la misma iteración. Ejemplo de disposición:

```text
verification/telemetry/<run_id>/
  <cycle>_<iteration>_<timestamp>.jsonl
  measurement.json
  <capturas o salidas de scripts>
```

Se conserva la creación que evita sobrescrituras y el snapshot por fetch. No se
exigen hashes por archivo ni `--not-before`. Las fechas reales y los archivos del
intento se registran en los reportes existentes.

Si falta telemetría: avisar, investigar collector/proceso/disco/sensores y decidir
si repetir o continuar con el alcance restante. Registrar causa, decisión y medidas
afectadas; no reejecutar automáticamente todo ni convertir un dato faltante en cero.
El exit 0 del collector sigue sin certificar cobertura completa. La pérdida de una
métrica no invalida por sí sola todas las pruebas no dependientes de ella.

Cuando G2 devuelve feedback a S2, su Description debe explicar: comando/destino y
resultado observado; criterio esperado; evidencia/logs pertinentes; causa técnica
(o hipótesis pendiente de confirmar); módulo/kit/PATH/requisito afectado; acción
concreta y ruta. No basta «falló» ni se necesita una lista de hashes.
Un problema operativo se diagnostica y corrige durante la preparación; no se inventa
un defecto del producto para etiquetar una caída de SSH. Si impide medir, se informa
y se pausa. Un defecto del módulo o kit usa `Verdict: module defect` hacia S2; uno
de diseño conserva `Verdict: design defect` hacia S1/G1; inviabilidad sigue por RFD.

## 7. Nuevo contrato de measurement.json (versión 2)

Obligatorios: `schema_version`, `cycle`, `stage`, `iteration`, `run_id`, `target`,
`command`, `started_at`, `finished_at`, `exit_code`, `measurements`.
Cada medición registra requisito, métrica, valor, criterio y resultado
`pass|fail|inconclusive`; unidades cuando correspondan. `value` puede ser número,
texto o booleano para cubrir métricas y pruebas funcionales. Un fallo antes de
medir puede dejar la lista vacía, con exit no cero y explicación del error.

Opcionales: entorno/versiones, archivos, estado de telemetría, configuración del
dispositivo y contexto metrológico cuando el ensayo lo necesite. Se permiten campos
adicionales; no se obliga a todas las mediciones a un intervalo escalar cerrado.
Se retiran `deployment_sha256`, hashes de capturas, `oracle`, calibración e
incertidumbre como campos universalmente obligatorios. La validación común se
reduce a lectura/estructura básica y valores numéricos finitos; el agente evalúa
los criterios específicos. Un JSON bien formado no decide el veredicto de G2.

Ejemplo **sintético del formato**, sin representar una ejecución ni un PASS real:

```json
{
  "schema_version": 2,
  "cycle": "01_sdr",
  "stage": "G2",
  "iteration": 2,
  "run_id": "01_sdr_2_2026-11-11_20-42-40-123",
  "target": "rpi",
  "command": "verification/run.sh vl2",
  "started_at": "2026-11-12T01:42:40Z",
  "finished_at": "2026-11-12T01:43:10Z",
  "exit_code": 0,
  "measurements": [
    {
      "requirement_id": "SYS-ACQ-001",
      "metric": "sample_rate",
      "value": 2000000,
      "unit": "samples/s",
      "criterion": "2000000 ± 2 %, según SyRS",
      "result": "pass"
    }
  ],
  "telemetry": {"status": "complete", "files": ["01_sdr_2_2026-11-11_20-42-40-123.jsonl"]},
  "artifacts": [{"path": "capture.iq", "kind": "capture"}]
}
```

No se reescriben evidencias v1 ni reportes históricos. Las nuevas ejecuciones
escriben v2; los archivos anteriores permanecen como evidencia del flujo anterior.

## 8. Implementación futura por unidades

| Unidad | Cambio coherente y archivos principales | Comprobación enfocada |
|--------|----------------------------------------|-----------------------|
| R0 Alta reutilizable | `credential_setup.py`, script de bootstrap, config/registro de dispositivos y resolución MCP: MAC descubierta, administrador registrado, sin `--target` normal, claves locales por equipo y públicas acumuladas por PC | Otro proyecto no regenera claves; otro PC accede al mismo usuario sin borrar claves previas; cambio de IP/interfaz conocida reutiliza identidad; proyectos no pisan workspace ni pierden accesos antiguos |
| R1 SSH sencillo | `classifier.py`, `server.py`, transporte y guía MCP: permitir por defecto, trusted destructivo, proteger DB/estado en sync | Comandos ordinarios/sudo/scripts pasan; variantes destructivas se desvían antes de SSH; rsync no borra ni sustituye DB |
| R2 Preparación y revisión HW | S2 SKILL/layout, transporte de candidato Git, aprovisionamiento/probe: limpio+pusheado, checkpoint antes de update/deploy/test, actualización automática y relojes manejados por agente | Candidato sucio/no publicado no llega a HW; exportación no envía ignorados; stop/continue respetan contrato |
| R3 Evidencia pequeña | Schema/validador/guía canónicos de G2 y copias compartidas de S2: formato v2 y nombres por ciclo/iteración; retirar manifiestos y preflights SHA HIL de contratos/tests | JSON funcional sin calibración ni hashes; errores e inconclusos; scripts/copias del scaffold autosuficientes |
| R4 G2 operativo | G2 SKILL, `vsil-verifier`, headers por runtime, checklist G1 y prototype: agente ejecuta HW, padre gestiona pausa/trusted, feedback causal y tolerancias según GT | Misma cadena y rutas; verificador no pregunta/edita DUT/decide HITL; diagnóstico no se disfraza de código defectuoso |
| R5 Coherencia y escenario | README/AGENTS fuente y generado, pruebas de reports/status/scaffold/MCP, este plan | Rework G2→S2 en mismo ciclo, iteraciones/baselines/stale correctos; recorrido local y remoto sin manifiesto |

Se modifican conjuntamente skills, referencias, headers generados y tests que hoy
exigen el flujo rígido. `shared_skill_assets` conserva una fuente canónica y copias
autosuficientes. `src/codeanvil/reports.py` no necesita nuevos estados. No se eliminan
los hashes GT/golden del resto de V-SIL: este recorte afecta a la reproducibilidad
HIL añadida en la pasada anterior. Archivos antiguos del usuario no se borran al
dejar de ser obligatorios; no se añade un comando de migración o limpieza.

La ejecución futura mantiene commits separados con pruebas/docs de cada unidad,
revisión del padre y push cuando pase su validación, sin PR. El recorrido físico
final requiere el destino disponible; no se presenta una simulación como HIL real.

## 9. Revisión de este documento

Se contrastó con S2 Pause Schedule, su rework y formato de entrega; G2 y el
verificador; `TEMPLATE_AGENT.md`; `reports.py`; transporte rsync; schema actual y
el generador de assets compartidos. Dos subagentes auditaron contratos de estado
y riesgos operativos. Esta entrega solo escribe el plan: no cambia esas reglas
activas ni ejecuta hardware.

Validación de esta unidad documental: `git diff --check` y lectura/parseo del
ejemplo JSON, ambos correctos. Se generó un scaffold temporal del comportamiento
actual en `/tmp/hil-refactor-plan-p88eps1e/project`: pausas/stop de S2, `Based on`,
rutas de feedback, reescritura de paths y copias autosuficientes comprobados. La
revisión final del plan por el subagente no encontró requisitos omitidos.
Runtime del refactor: N/A, no se implementa código en esta entrega. Rollback:
eliminar este plan y su enlace desde el registro anterior; los 16 commits previos
permanecen intactos. La identidad del commit se informa al entregar el documento.

Ampliación posterior al plan `0e73414`: alta sin `--target`, identidad MAC y acceso
de varios PCs al mismo usuario remoto. Se contrastó con el almacenamiento local
de claves, el append de `authorized_keys` y el confinamiento rsync actuales;
`git diff --check` correcto. Runtime: N/A, propuesta documental. Rollback de esta
ampliación: sus dos decisiones, subsección de alta y unidad R0 únicamente.

## 10. Ejecución autorizada

El usuario autorizó implementar todo el refactor y pushear en `feat/hil-pil`.
`remote_access` implementa R0; `telemetry_ci`, R1/transporte de R2;
`pil_methodology`, evidencia y contratos R2–R4. El padre revisa, integra, prueba,
commitea y pushea cada unidad. Sin PR ni release. Ningún test simulado se registra
como una medición física. El checkpoint previo a HW se aplica también a cualquier
validación física que se proponga durante esta entrega.

Las comprobaciones y límites de rollback se añaden aquí al cerrar cada unidad.

- R0a: registro local de equipos por MAC, aliases de interfaces y adopción de
  identidades de claves existentes; metadata pública separada de claves privadas.
  `test_identity.py`: **17 passed**. Escenario: registro/fusión y resolución de
  claves en directorios temporales, sin SSH. Rollback: `identity.py`, extensiones
  de `config.py` y sus tests; el bootstrap público se integra en la siguiente unidad.
- R1: SSH permite comandos ordinarios, scripts y sudo; solo operaciones
  destructivas visibles desvían a trusted. Excludes rsync protegen DB, sidecars y
  estado declarado tanto de sobrescritura como de borrado. **59 tests passed**;
  escenario rsync real local conserva estado, actualiza código y borra código
  obsoleto. Rollback: router, excludes y tests de política/transporte, sin tocar
  identidad MAC ni la preparación Git de la unidad siguiente.
- R0b: discovery autenticado con claves existentes o administrador y payload
  aditivo de `authorized_keys`. La adopción de exec legacy no cambia la clave
  deploy antigua: conserva proyectos previos y usa exec para nuevos workspaces.
  **8 tests passed**, incluido Bash real sobre archivos temporales que conserva
  claves de otros PCs y repeticiones sin duplicación. Registro MAC: **17 passed**.
  Rollback: helper de alta, payload, tests y propiedad local de compatibilidad;
  el CLI se conecta a estas funciones en R0c.
- Preparación MCP: `init_codeanvil` actualiza automáticamente una cuenta ya dada
  de alta, con un ref publicado explícito de la herramienta; no crea claves ni
  deduce tags desde SemVer. Probe conserva versiones como diagnóstico. El servidor
  resuelve claves MAC/adoptadas y selecciona exec para sync legacy compatible.
  **30 tests passed** de dispatch y actualización; Bash ejecuta las capacidades
  con herramientas falsas y se detiene en fallo. Rollback: server/provision y sus
  tests; la preparación de acceso permanece en credential-setup.
- R2 transporte: `code_sync` exige árbol limpio y rama sincronizada con upstream
  recién consultado, exporta el commit publicado con Git y despliega solo ese
  árbol temporal. **16 tests passed** de despliegue/rsync/protocolo, con remotos Git
  bare locales, casos sucios/no publicados y enlaces que escapan. Sin manifiesto
  ni hashes HIL. Rollback: exportación/chequeo Git y destinos compatibles del
  transporte, fixtures de protocolo y tests de despliegue.
- R2–R4 metodología: S1/G1 permiten preparación posterior y metrología según el
  requisito; S2 conserva sus **1739 bytes** de Pause Schedule y añade la revisión
  previa a HW; G2 pasa la iteración normal al verificador fresco, que ejecuta HW
  dentro del alcance revisado y devuelve feedback causal. Schema/checker v2 retiran
  atestaciones, manifiestos, hashes HIL y oráculo universal. **206 tests passed**
  en `test_hil_measurements`, `test_vsil_v3_{s1,g1,g2,s2,subagent,agents_md}`,
  `test_create`, `test_gate_questions` y `test_report_state`. Escenario: scaffold
  temporal con assets autosuficientes, checker v2 ejecutado como subprocess y
  rework/staleness existentes. Rollback: los 17 archivos de skills, verificador y
  tests de esta unidad conjuntamente; no altera parser de reportes ni transporte.
  Es una migración coherente de **1358 líneas añadidas+eliminadas**, principalmente
  sustitución del contrato anterior; separar schema de sus callers dejaría flags
  obsoletos activos. Se informa el tamaño, sin comprimir texto/tests ni crear PR.
- R0c: CLI sin `--target`/`--workspace`, discovery autenticado, reutilización de
  claves locales y workspace por UUID. Otro PC añade sus claves al mismo usuario;
  el clon legacy migra una sola fila sin duplicar equipo ni cambiar claves de
  otros clientes. Se retira el motor shell antiguo a favor del CLI. **46 tests
  passed** (`test_credential_setup`, `test_hil_enrollment`, `test_cli`), incluidos
  generación/recuperación real de un par SSH temporal y Bash aditivo. La revisión
  cruzada corrigió pérdida del pin en fallback, acceso final no comprobado y
  pares público/privado incompatibles; claves perdidas se restauran, no regeneran.
  Escenario: primer PC, otro proyecto/IP/admin/interfaz, segundo PC, adopción y
  clon legacy, fallos sin publicar metadata. Rollback: CLI/parser/dispatch,
  helper, wrapper shell, ancla estable del registro y tests de esta unidad.
  Migración coherente de **992 líneas añadidas+eliminadas**, con tests y retirada
  del motor anterior; se informa sobrepaso sin comprimir ni separar el contrato.
- R5 interfaz operativa: skill de uso MCP alineada con alta por MAC, preparación,
  ejecución autónoma y trusted destructivo; se retiran helpers de pin SemVer sin
  callers y el error de acceso dirige a credential-setup. **127 tests passed**
  del servidor aislado. Escenario MCP stdio real con SSH/rsync simulados: **9
  passed**, variantes legacy/MAC canónica/MAC adoptada, Git remoto bare local,
  clave y pin correctos, destinos de deploy, snapshots, errores y auditoría.
  Rollback: guía de uso, limpieza de config y parametrización de `test_protocol`;
  no cambia enrolamiento ni el parser de reportes.
