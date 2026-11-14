# Cómo implementar un outer harness para agentes de código

## Terminología y estado de la literatura en 2026

**La distinción entre inner harness y outer harness está respaldada por literatura
de 2026, pero los términos no forman una taxonomía universalmente normalizada.**
Macedo estudia precisamente la polisemia de *agent harness* y propone una definición
operativa: es una contribución conceptual, no un estándar adoptado por todo el
sector. Consulta realizada el 13 de noviembre de 2026.
[Macedo, preprint del 8 de junio de 2026](https://arxiv.org/abs/2606.10106v1).

| Término | Definición y alcance en las fuentes consultadas |
|---------|------------------------------------------------|
| **Agent harness / harness** | Infraestructura externa al modelo que lo hace operativo: contexto, herramientas, estado, bucle de acción y controles. El término puede abarcar el sistema completo; no designa exclusivamente la capa que añade el usuario. [Trivedy, 10 de marzo de 2026](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness). |
| **Inner harness / builder harness** | Parte construida dentro del agente: código de ejecución, prompt de sistema incorporado y esquemas de herramientas. Se distingue de la configuración añadida por el usuario. [Baltes y Treude, 26 de octubre de 2026, §I](https://arxiv.org/html/2610.35348v1#S1); [Böckeler, 2 de abril de 2026, figura 1](https://martinfowler.com/articles/harness-engineering.html). |
| **Outer harness / user harness** | Capa que el usuario o equipo compone para su contexto: instrucciones, configuración, hooks y mecanismos de guía y feedback. Aprovecha las capacidades del agente existente y puede mantenerse separada de su implementación. [Böckeler, 2 de abril de 2026](https://martinfowler.com/articles/harness-engineering.html); [Baltes y Treude, §I–II](https://arxiv.org/html/2610.35348v1#S2). |
| **Agent runtime** | Nombre funcional para el mecanismo que ejecuta llamadas al modelo y herramientas y administra sesiones y contexto. Se solapa con funciones del harness; no establece una frontera idéntica en todos los productos. Microsoft describe un harness compuesto sobre su runtime existente. [Documentación técnica, actualizada el 28 de octubre de 2026](https://learn.microsoft.com/en-us/agent-framework/concepts/harness). |
| **Cockpit / host** | Metáfora práctica para el entorno desde el que se opera el agente. Un cuaderno de ingeniería de 2026 usa esta expresión para el runtime y su interfaz con controles nativos. Es el vocabulario de esa implementación, no una equivalencia académica general con *inner harness*. [Lennon, baseline del 12 de septiembre de 2026](https://github.com/DynamicDevices/durable-agent-harness#readme). |
| **Agent framework** | Biblioteca o infraestructura con la que se construyen aplicaciones de agentes. La diferencia con un harness es su papel arquitectónico; un framework también puede proporcionar un harness ya implementado. [Macedo, junio de 2026](https://arxiv.org/abs/2606.10106v1); [Microsoft, octubre de 2026](https://learn.microsoft.com/en-us/agent-framework/concepts/harness). |

Así, llamar **inner harness** a la infraestructura incorporada del agente y
**outer harness** a la capa añadida por su usuario es coherente con las fuentes.
El agente de código es el sistema que utiliza el modelo y esa infraestructura;
no es exactamente sinónimo de una sola de sus capas. Para este documento usaremos
*runtime* al hablar de ejecución y *cockpit* solo al hablar del entorno de operación.
Esta elección es una convención editorial apoyada en los usos anteriores.

### Cómo se relacionan las definiciones con esta guía

Böckeler organiza el outer harness en **guías**, que orientan antes de actuar
(*feedforward*), y **sensores**, que permiten corregir después de observar resultados
(*feedback*). Distingue controles computacionales, como tests y linters, de controles
inferenciales, como revisiones con modelos. [Artículo de abril de 2026](https://martinfowler.com/articles/harness-engineering.html#FeedforwardAndFeedback).

En la arquitectura propuesta aquí, las instrucciones y plantillas aportan guías;
los checks y evaluaciones aportan sensores; los reportes conservan sus resultados
y las rutas de feedback convierten esos resultados en trabajo de corrección. Es
una aplicación de ese marco conceptual, no una definición normativa de outer harness.

La separación también importa al medir resultados: Baltes y Treude distinguen
configuración externa, implementación interna, modelo, tareas e interacción humana
como variables de un experimento. Cambiar varias a la vez dificulta atribuir una
mejora al harness. Su trabajo era un preprint en revisión en la versión consultada.
[Baltes y Treude, octubre de 2026, §II](https://arxiv.org/html/2610.35348v1#S2).

### Fuentes y nivel de evidencia

- **Investigación académica, preprint:** Sanderson Oliveira de Macedo,
  *What makes a harness a harness: necessary and sufficient conditions for an agent harness*,
  8 de junio de 2026, [arXiv:2606.10106v1](https://arxiv.org/abs/2606.10106v1).
- **Investigación académica, preprint en revisión:** Sebastian Baltes y Christoph Treude,
  *Toward Evidence-Based Agentic Software Engineering*, 26 de octubre de 2026,
  [arXiv:2610.35348v1](https://arxiv.org/abs/2610.35348v1).
- **Artículo de práctica profesional:** Birgitta Böckeler,
  *Harness engineering for coding agent users*, 2 de abril de 2026,
  [MartinFowler.com](https://martinfowler.com/articles/harness-engineering.html).
- **Artículo técnico de un proveedor:** Vivek Trivedy,
  *The Anatomy of an Agent Harness*, 10 de marzo de 2026,
  [LangChain](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness).
- **Documentación de implementación:** Microsoft, *Agent Harness*, actualización
  del 28 de octubre de 2026, [Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/concepts/harness).
- **Cuaderno de ingeniería de un autor:** Alex Lennon, *Durable Agent Harness*,
  baseline v1.2 del 12 de septiembre de 2026, consultado como evidencia de uso de
  *cockpit / host*, [repositorio original](https://github.com/DynamicDevices/durable-agent-harness#readme).

Estas fuentes documentan usos y propuestas de 2026 con distinto nivel de evidencia.
No se presupone que una metáfora de un repositorio, una definición de proveedor
y una propuesta académica tengan la misma autoridad o el mismo alcance.

## Arquitectura propuesta en esta guía

Un **outer harness** convierte un proceso de trabajo en instrucciones ejecutables,
artefactos y condiciones de avance que un agente de código puede seguir dentro de
un repositorio. Su función es establecer qué trabajo está autorizado, con qué
entradas, quién puede decidir y qué evidencia permite continuar.

Puedes implementarlo con archivos, skills y unos pocos scripts. El agente aporta
la capacidad de razonar y modificar software; el harness aporta contratos y
continuidad entre sesiones. Esta guía propone una arquitectura genérica: los
nombres, estados y rutas de los ejemplos son decisiones ilustrativas.

## 1. Outer harness, entorno del agente y framework

Un agente de código suele ejecutarse en un entorno que ya gestiona el ciclo de
conversación, las llamadas al modelo, las herramientas, las ediciones y los permisos.
Aquí llamamos **entorno del agente** a esa capa existente. El outer harness añade
el proceso del proyecto por encima de ella.

Un framework de agentes es una biblioteca o infraestructura con la que puedes
construir una aplicación de agentes: programar llamadas al modelo, herramientas,
transferencias entre agentes, estado y ejecución. Las capacidades concretas dependen
del framework. La diferencia principal está en qué capa necesitas implementar.

| Pregunta | Outer harness basado en repositorio | Aplicación construida con un framework |
|----------|--------------------------------------|-----------------------------------------|
| ¿Dónde se expresa el proceso? | Contratos, skills, documentos y comprobaciones del proyecto. | Código de la aplicación, grafos, callbacks o configuración del framework. |
| ¿Quién ejecuta el ciclo modelo/herramientas? | El entorno del agente de código existente. | La aplicación y su runtime, según la arquitectura elegida. |
| ¿Cómo continúa otra sesión? | Reconstruye el trabajo desde artefactos y reportes persistentes. | Usa la persistencia y el protocolo de recuperación implementados por la aplicación. |
| ¿Qué se distribuye? | Un paquete de instrucciones, plantillas, scripts y adaptadores. | Una aplicación o servicio con sus dependencias y configuración. |
| ¿Cuándo conviene? | Equipos que ya usan agentes de código y necesitan un proceso compartido. | Productos que necesitan controlar programáticamente agentes y su ejecución. |

Ambos enfoques pueden combinarse. Un framework puede ejecutar operaciones que
exige el harness, y una aplicación de agentes puede consumir sus contratos. Ninguno
garantiza corrección por sí mismo. Una carpeta de prompts tampoco crea continuidad
si no define entradas, salidas, decisiones y reglas de recuperación.

## 2. Empieza por los contratos del trabajo

Antes de escribir prompts, describe cada actividad con este contrato:

| Campo | Qué debe resolver |
|-------|-------------------|
| Propósito | Un resultado concreto, observable y acotado. |
| Entradas | Documentos, código, decisiones y revisiones que puede utilizar. |
| Prerrequisitos | Qué reportes deben existir y qué resultado habilita la actividad. |
| Escrituras permitidas | Archivos que puede crear o modificar; propietario de cada artefacto. |
| Comprobaciones | Scripts, pruebas o revisiones que debe realizar. |
| Salidas | Artefactos y formato del reporte que produce. |
| Autoridad | Qué decide el agente, qué decide un programa y qué decide una persona. |
| Feedback | Dónde vuelve el trabajo cuando aparece cada clase de problema. |
| Interrupción | Qué se conserva y cómo se reanuda sin repetir efectos externos. |

Como ejemplo, considera cuatro actividades: preparar un plan, revisarlo,
implementar el cambio y evaluar el resultado. Son etiquetas de ejemplo; cualquier
otro proceso puede tener actividades, ramas o decisiones diferentes.

La separación debe seguir responsabilidades. Quien evalúa un candidato puede
ejecutar pruebas y explicar fallos; modificar ese candidato durante la evaluación
requiere volver a la actividad que tiene permiso para implementarlo.

## 3. Construye un proyecto que contenga el harness

Una distribución mínima puede generar esta estructura:

```text
project/
  AGENTS.md
  .agents/skills/
    prepare-plan/SKILL.md
    review-plan/SKILL.md
    implement-change/SKILL.md
    evaluate-change/SKILL.md
  .harness/
    project.yaml
    workflow.yaml
    inputs/
    design/
    reports/cycle-001/
    evidence/cycle-001/
  tools/
    check_prerequisites.py
    inspect_state.py
  src/
  tests/
```

Las rutas son una convención del ejemplo. `src/` y `tests/` pertenecen al producto;
el generador puede dejarlas sin crear hasta que exista una implementación.
`project.yaml` identifica el proyecto con `project_id` y el ciclo con `active_cycle`;
ambos deben coincidir con el contexto de los reportes que consume una actividad.
Las herramientas auxiliares del harness no deben convertirse accidentalmente en
dependencias necesarias para ejecutar el producto entregado.

Mantén tres responsabilidades documentales:

- `AGENTS.md`: mapa breve, reglas comunes, ubicación del estado y catálogo de skills.
- `SKILL.md`: instrucciones de una actividad y su contrato de entrada/salida.
- Referencias y scripts: esquemas, plantillas, criterios extensos y checks mecánicos.

El mapa ayuda a localizar el trabajo; cada skill verifica si puede comenzar.
No necesitas que el archivo raíz actúe como un programa que dirige todo el flujo.
La disponibilidad de un nombre de archivo o directorio depende del entorno:
comprueba su descubrimiento nativo y genera adaptadores cuando sean necesarios.

## 4. Declara dependencias una sola vez

Usa un manifiesto para representar el proceso y generar sus vistas:

```yaml
schema_version: 1
workflow_version: 1.0.0
steps:
  prepare-plan:
    kind: work
    requires: {}
    writes: [.harness/design/plan.md]
  review-plan:
    kind: human_review
    requires: {prepare-plan: DELIVERED}
    writes: []
  implement-change:
    kind: work
    requires: {review-plan: ACCEPTED}
    writes: [src/, tests/]
  evaluate-change:
    kind: human_review
    requires: {implement-change: DELIVERED}
    writes: []
feedback_routes:
  implementation: implement-change
  design: prepare-plan
  environment: retry-current
  baseline: new-cycle
```

`writes` enumera artefactos de trabajo; cada actividad también puede publicar su
propio reporte y evidencia bajo las rutas comunes. Una revisión puede autorizar
una herramienta para ejecutar pruebas sin autorizar ediciones de código.

Genera desde este manifiesto el catálogo y las precondiciones mecánicas. Evita
mantener listas independientes en documentación, scripts e instrucciones. Valida
IDs, referencias y ciclos de dependencias al construir la distribución. Las rutas
de feedback son retornos de trabajo, no dependencias que deban formar un ciclo.

## 5. Haz que cada skill compruebe sus condiciones de entrada

Una skill es un contrato que el agente debe leer antes de actuar. Su descripción
permite descubrir cuándo utilizarla; su cuerpo contiene las reglas operativas.
Este fragmento ilustra una skill cuyo contenido completo se genera del manifiesto:

```markdown
---
name: implement-change
description: Implementar un cambio cuyo plan tiene una revisión aceptada y vigente.
---

1. Resolver proyecto y ciclo activo desde .harness/project.yaml.
2. Ejecutar la comprobación de prerrequisitos para implement-change.
3. Si está bloqueada, explicar la causa y la actividad que debe ejecutarse; no editar.
4. Leer el plan aceptado y el feedback pendiente que corresponda a este candidato.
5. Modificar únicamente los archivos autorizados por el contrato y el feedback.
6. Ejecutar las comprobaciones declaradas y conservar su salida real.
7. Publicar artefactos y un reporte completo que identifique sus entradas.
8. Indicar qué actividad queda habilitada; no inventar una aceptación humana.
```

El checker compartido resuelve rutas, lee reportes y calcula vigencia. No debe
reemplazar el razonamiento de la actividad ni decidir una revisión humana. Si no
existe checker todavía, la skill puede realizar esas comprobaciones explícitamente;
extrae a código lo repetitivo a medida que se estabilice el contrato.

Una instrucción incumplida no es una barrera técnica. Para impedir realmente una
escritura o un despliegue, utiliza permisos del runtime, aislamiento o controles en
la herramienta ejecutora. Un agente con acceso de escritura puede falsificar un
reporte; si necesitas una frontera de confianza, protege quién puede publicarlo.

## 6. Usa reportes como registros de decisiones

El estado debe sobrevivir al cierre del chat. Una implementación sencilla guarda
un archivo Markdown por actividad y añade una sección por intento completado.
Cada sección tiene campos estructurados y una explicación legible. Por ejemplo:

````markdown
# Reporte: implement-change

## Iteration 3

```yaml
schema_version: 1
project_id: example-project
cycle: cycle-001
workflow_version: 1.0.0
step: implement-change
iteration: 3
candidate: "<commit o snapshot de los artefactos de trabajo>"
result: DELIVERED
decided_by: agent
based_on:
  review-plan: 2
responds_to:
  evaluate-change: 1
artifacts:
  - src/handler.py
  - tests/test_handler.py
```

### Trabajo realizado
Se corrigió la validación indicada en el feedback de evaluación.

### Evidencia
Registrar comando exacto, candidato, entorno, salida y código de salida reales.
````

Este es un ejemplo de formato, no evidencia de una ejecución. En un reporte real
debes identificar la revisión exacta de los artefactos, los resultados observados
y la identidad o autorización de quien decide. Un nombre escrito por el agente
no autentica por sí solo una decisión humana.

Mantén separados los significados de los resultados:

| Resultado | Significado |
|-----------|-------------|
| DELIVERED | La actividad produjo sus salidas; no implica aceptación externa. |
| ACCEPTED | La autoridad declarada aceptó el candidato identificado. |
| FEEDBACK | Hay correcciones o decisiones pendientes, con una ruta explícita. |

Una comprobación determinista puede tener `PASS`/`FAIL`; su código de salida no
equivale automáticamente a una aceptación del producto. `stale`, `missing` y
`invalid` son estados calculados por el lector, no nuevos veredictos humanos.

El parser debe reconocer una única cabecera estructurada por iteración, ignorar
ejemplos citados, validar el esquema y rechazar resultados ambiguos. No busques la
palabra ACCEPTED en cualquier parte del Markdown. Si la última iteración está
incompleta, bloquea el avance; no recuperes silenciosamente una aceptación antigua.
Publica la actualización de forma atómica y conserva las iteraciones anteriores.
Para un MVP, asigna un solo escritor por reporte; añade bloqueo si habrá concurrencia.

También puedes usar registros inmutables por intento o JSON como fuente canónica
y generar Markdown como vista. Elige un formato y un único origen de estado;
no mantengas una base de datos y reportes que discrepen sobre la decisión vigente.

## 7. La aprobación debe corresponder al trabajo actual

Comprobar que un reporte dice ACCEPTED es insuficiente. También debes comprobar
que pertenece al proyecto/ciclo correcto y que sigue describiendo sus entradas.

La regla de entrada es: todos los prerrequisitos existen, son válidos, tienen el
resultado requerido y siguen vigentes; además, no hay un feedback posterior que
impida continuar con esas mismas entradas. Cualquier condición desconocida bloquea
la actividad con una explicación concreta.

Supón que el plan tiene iteración 4 y la revisión acepta esa iteración. Si el plan
pasa a iteración 5, la revisión anterior queda obsoleta. La implementación basada
en ella también queda obsoleta, aunque su reporte conserve DELIVERED. La evaluación
de esa implementación debe considerarse obsoleta por propagación.

Guarda la dependencia exacta en `based_on` y recorre sus antecesores para calcular
vigencia. Un comando de estado debe señalar la primera entrada que cambió y la
actividad que necesita repetirse. No debe borrar reportes ni modificar decisiones.

Una referencia a la iteración no detecta ediciones directas del artefacto sin nuevo
reporte. Identifica también el candidato mediante un commit, una versión inmutable
o un digest de las rutas relevantes. Define qué cambios invalidan cada evidencia;
no compares ciegamente todo HEAD si el único cambio es publicar el propio reporte.

La identidad del ciclo mantiene juntas una línea base y sus decisiones. Un cambio
de objetivo puede abrir otro ciclo sin reescribir la historia. Una corrección dentro
del alcance normalmente produce nuevas iteraciones en el ciclo existente.

## 8. Diseña el feedback como una instrucción de reentrada

Un reporte que solo diga «falló» obliga al siguiente agente a reconstruir el problema.
Un feedback útil contiene: observado, esperado, evidencia, causa o hipótesis,
archivos afectados, actividad responsable y condición para volver a evaluar.

| Clase | Ejemplo | Ruta |
|-------|---------|------|
| Implementación | Un dato permitido por el contrato se rechaza. | Corregir la implementación y ejecutar las pruebas afectadas. |
| Diseño | Dos componentes tienen contratos incompatibles. | Corregir el plan, revisar de nuevo y adaptar la implementación. |
| Entorno | Falta un permiso, dependencia o conexión necesaria. | Reparar la preparación y repetir el intento con evidencia nueva. |
| Línea base | El objetivo exige una capacidad que la entrada no autoriza. | Pedir una decisión al propietario de la entrada; abrir otro ciclo si corresponde. |

Ejemplo: «La evaluación 1 observó HTTP 500 ante un dato inválido; el contrato exige
HTTP 400. Corregir el adaptador y su prueba. Conservar el resto de los módulos y
repetir las pruebas del endpoint antes de solicitar otra evaluación».

El nuevo reporte declara `responds_to` para cerrar ese feedback. Reintentar con el
mismo candidato no resuelve un defecto de implementación o diseño. Un fallo de
entorno sí puede justificar repetirlo, indicando la reparación y un intento nuevo.
Una hipótesis sin confirmar no debe registrarse como causa demostrada.

Para correcciones en borrador, utiliza un marcador separado de los reportes finales.
Permite editar, comprobar y resolver preguntas sin publicar una iteración por cada
errata. El borrador no autoriza avanzar. Al cerrarlo, publica el resultado completo
con las decisiones tomadas y la revisión final de sus entradas.

## 9. Distribuye el harness sin sobrescribir el proyecto

El generador instala la estructura; el agente ejecuta el trabajo dentro de ella.
Puedes ofrecer comandos para crear, inspeccionar, actualizar y diagnosticar un
proyecto sin implementar un servicio que llame al modelo y dirija cada transición.
Si después añades un ejecutor automático, debe consumir los mismos contratos.

El scaffolding inicial debe copiar skills y referencias, crear el manifiesto de
identidad, adaptar rutas y producir el mapa de instrucciones. Registra versión del
harness y esquema. Valida el proyecto generado, no solo las plantillas originales.

Una actualización necesita un inventario de archivos administrados: mostrar el
diff, respaldar lo sustituido y preservar código, entradas, reportes y modificaciones
del usuario. Si hay conflicto, reconciliarlo explícitamente. Repetir la instalación
no debe vaciar carpetas ni reiniciar el ciclo. Cambiar contratos o esquemas puede
requerir migración; no reinterpretar reportes antiguos con semántica nueva.

Usa una ubicación canónica para las skills. Genera enlaces, copias administradas
o punteros solo donde el runtime realmente los lea. Si un runtime carga varios
archivos de instrucciones de forma acumulativa, evita duplicar el mismo contenido.
Prueba descubrimiento desde la raíz y desde subcarpetas, y documenta la herencia.
Una sesión puede añadir instrucciones y herramientas personales o administradas.
Inspecciona las fuentes activas; una configuración local no demuestra aislamiento.

Separa dependencias del harness, dependencias del producto y entornos de herramientas
externas. Un launcher estable puede resolver sus instalaciones desde el proyecto
actual, conservando configuraciones portables al mover o clonar el repositorio.
Instalar una herramienta no equivale a habilitarla para un proyecto ni a concederle
credenciales. Cuando el runtime lo requiera, reinicia la sesión y verifica capacidades.

MCP u otro adaptador aporta operaciones sobre sistemas externos. La skill explica
cuándo usarlas; el servidor ejecutor aplica sus permisos. Un servidor de comandos
no necesita convertirse en el coordinador del proceso.

## 10. Separa publicación del harness y despliegue del producto

Hay dos entregas: distribuir el harness al repositorio de trabajo y desplegar el
software producido a su entorno de ejecución. Mantén sus referencias separadas.

Para el segundo caso, identifica candidato, destino, comandos y datos persistentes
antes de ejecutar acciones externas. Despliega una revisión identificable; evita
copias de archivos sueltos que mezclen candidatos o borren bases de datos. Observa
las versiones y capacidades necesarias, sin exigir igualdad de versiones arbitraria.

Una autorización debe corresponder al candidato, destino y alcance de la acción.
No la infieras de silencio ni de una aceptación de diseño anterior. Los controles
de permisos de la máquina siguen aplicando aunque la skill autorice continuar.
Separa secretos y rutas privadas de las configuraciones compartidas.

Conserva comandos, salidas, entorno y evidencia de cada intento en una ubicación
propia. Recuperar evidencia remota exige identificar el intento; encontrar un archivo
con el nombre esperado no demuestra que pertenezca al candidato actual.

## 11. Reanuda desde archivos y delega con contratos pequeños

Al abrir una sesión, identifica proyecto/ciclo, inspecciona reportes y vigencia,
localiza el feedback pendiente y carga la skill correspondiente. Pregunta solo por
decisiones o contexto que las fuentes persistentes no resuelvan. El historial del
chat puede ayudar, pero no debe ser el único lugar que conserve una autorización.

Después de una interrupción, inspecciona artefactos y vuelve a ejecutar los checks
pertinentes. Conserva lo que funciona. Antes de repetir una operación externa,
averigua si ya ocurrió y usa identificadores de intento o mecanismos de idempotencia.

La delegación es opcional. Un subagente recibe tarea, entradas versionadas, rutas
editables, comandos y formato de devolución. El padre integra resultados y conserva
las decisiones que no delegó. La concurrencia requiere entradas listas y escrituras
sin conflicto; varios agentes no deben publicar decisiones en el mismo reporte.

Para una evaluación independiente, usa contexto nuevo y un candidato congelado.
No permitas ajustar el código o los criterios para convertir el resultado en éxito.
Si el runtime no ofrece subagentes, una sesión nueva puede cumplir ese papel.
Contexto nuevo reduce arrastre de supuestos; no garantiza independencia estadística
ni crea permisos de solo lectura por sí mismo.

## 12. Verifica el harness como software

La consistencia de instrucciones se prueba con proyectos generados y estados de
fallo deliberados, además de la lectura editorial de las skills.

| Escenario | Resultado que debes comprobar |
|-----------|--------------------------------|
| Falta un prerrequisito | Bloqueo que identifica la actividad requerida; ninguna edición de producto. |
| Cambia una entrada aceptada | Sus consumidores aparecen obsoletos, incluso por dependencia indirecta. |
| Última iteración incompleta o corrupta | Estado inválido; no reaparece una aprobación antigua. |
| Falta la decisión humana | La recomendación del agente no habilita el siguiente paso. |
| Feedback de diseño | Se revisa el diseño nuevo antes de continuar implementación/evaluación. |
| Fallo de entorno | Se diagnostica y repite el intento; no se inventa un defecto del producto. |
| Se interrumpe una sesión | La recuperación usa archivos y evita duplicar efectos externos. |
| Se mueve, clona o actualiza el proyecto | Se conservan identidad, artefactos, reportes y rutas portables. |
| Se cambia de runtime | Se descubren instrucciones, skills y herramientas con sus permisos efectivos. |

Empieza con un caso diminuto que recorra un avance, un feedback y una reanudación.
Registra duración, intervención humana, bloqueos incorrectos y pérdida de contexto.
Evalúa varias ejecuciones: fijar entradas y herramientas hace reproducibles los
checks deterministas, pero no convierte la salida del modelo en determinista.

Antes de distribuir la primera versión, verifica que cada actividad tiene un dueño,
que las decisiones apuntan a candidatos identificables, que otra sesión puede
reconstruir el trabajo y que el generador conserva proyectos existentes. Añade
automatización cuando resuelva fallos observados de ese contrato mínimo.
