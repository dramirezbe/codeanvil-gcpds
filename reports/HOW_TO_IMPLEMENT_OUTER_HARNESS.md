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
nombres de actividades y rutas de los ejemplos son genéricos. Los artefactos
mantienen una estructura común de plantillas, reportes e iteraciones.

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
    inputs/
    design/
    backups/
    report/01_example/
      plan.md
      review-plan.md
      implement.md
      implement_artifacts/test_run.md
      evaluate.md
      evaluate_artifacts/accepted_result.md
  src/
    api/
  verification/
    run.sh
    golden/manifest.md
    telemetry/<run_id>/
    api/
      mock_hal/
      stubs/
      fakes/
      drivers/
      test/
```

Este árbol muestra un proyecto con trabajo realizado. Al crearlo, el generador
instala instrucciones y skills, crea las carpetas de trabajo y registra identidad;
los reportes y sus artefactos aparecen al ejecutar las actividades. `src/`, el kit
`verification/` y los manifiestos del producto los escribe la actividad implementadora.
El producto ejecutable no debe importar el kit ni depender de las herramientas
del harness para arrancar.
Cada paquete del producto vive en `src/<package>/`, con su base, configuración y
módulos por responsabilidad. Su kit tiene el mismo nombre en `verification/`:
vectores y expectativas independientes, sustitutos, drivers, pruebas y telemetría.

El manifiesto de identidad conserva ID, nombre, referencias a entradas y ciclo:

```yaml
id: 019b0000-0000-7000-8000-000000000001
name: example-project
inputs:
  brief: .harness/inputs/brief.md
  criteria: .harness/inputs/criteria.md
cycle: 01_example
```

El UUID es ilustrativo y el generador asigna uno real. La clave `cycle` se añade
cuando el usuario elige un ciclo; después las skills la actualizan sin regenerar
la identidad ni reescribir los demás campos.

Mantén tres responsabilidades documentales:

- `AGENTS.md`: mapa breve, reglas comunes, ubicación del estado y catálogo de skills.
- `SKILL.md`: instrucciones de una actividad y su contrato de entrada/salida.
- Referencias y scripts: esquemas, plantillas, criterios extensos y checks mecánicos.

El mapa ayuda a localizar el trabajo; cada skill verifica si puede comenzar.
No necesitas que el archivo raíz actúe como un programa que dirige todo el flujo.
La disponibilidad de un nombre de archivo o directorio depende del entorno:
comprueba su descubrimiento nativo y genera adaptadores cuando sean necesarios.

## 4. Declara dependencias una sola vez

En el paquete que distribuye el harness, declara la relación entre skill y reporte
predecesor. Este fragmento de configuración se consume al generar el proyecto;
no constituye un segundo registro de su estado de ejecución:

```yaml
skills:
  prepare-plan:
    project_dir: .agents/skills/prepare-plan
    prerequisite: null
  review-plan:
    project_dir: .agents/skills/review-plan
    prerequisite: plan
  implement-change:
    project_dir: .agents/skills/implement-change
    prerequisite: review-plan
  evaluate-change:
    project_dir: .agents/skills/evaluate-change
    prerequisite: implement
report_order: [plan, review-plan, implement, evaluate]
stage_reports: [plan, implement]
```

Cada skill declara qué artefactos lee/escribe y qué significa terminarla. Las de
trabajo producen `plan.md` e `implement.md`; las de revisión producen
`review-plan.md` y `evaluate.md`. No hace falta una tabla de permisos dentro de
este manifiesto: los límites de edición se explicitan en el contrato de cada skill.

Genera el catálogo de `AGENTS.md` desde esta configuración. Cada fila indica la
skill, su reporte predecesor y que necesita su última iteración en `HITL: PASS`;
la actividad de entrada no tiene prerrequisito.
La condición se comprueba al cargar la skill. El generador distribuye el contrato;
no llama al modelo ni ejecuta la cadena. Las rutas de feedback viven en las skills
y en la descripción del reporte que solicita la corrección.

## 5. Haz que cada skill compruebe sus condiciones de entrada

Una skill es un contrato que el agente debe leer antes de actuar. Su descripción
permite descubrir cuándo utilizarla. El generador copia la skill y adapta sus rutas;
su cuerpo contiene las reglas operativas:

```markdown
---
name: implement-change
description: Implementar un cambio cuyo plan tiene una revisión aceptada y vigente.
metadata:
  gate: implement
---

1. Resolver proyecto y ciclo activo desde .harness/project.yaml; detenerse si el
   ciclo está cerrado o suspendido por una solicitud de cambio pendiente.
2. Comprobar que .harness/report/<cycle>/review-plan.md existe y su última
   iteración tiene HITL: PASS.
3. Comprobar que el predecesor y sus entradas no estén obsoletos. Si falla una
   condición, indicar qué skill debe ejecutarse; no editar ni escribir una iteración.
4. Leer el plan aceptado y el feedback pendiente que corresponda a este candidato.
5. Modificar únicamente los archivos autorizados por el contrato y el feedback.
6. Ejecutar las comprobaciones declaradas y conservar su salida real.
7. Respaldar el test_run.md anterior antes de sobrescribirlo y añadir una
   iteración a implement.md, identificando review-plan mediante Based on.
8. Indicar qué actividad queda habilitada; no inventar una aceptación humana.
```

`metadata.gate` identifica el reporte de esta skill; el nombre no obliga a que
sea una revisión humana. El cuerpo distingue actividades de trabajo y revisión.
Un lector compartido puede analizar reportes y calcular vigencia para un comando
de estado. Eso no sustituye la regla de entrada de la skill ni decide por una persona.

Una instrucción incumplida no es una barrera técnica. Para impedir realmente una
escritura o un despliegue, utiliza permisos del runtime, aislamiento o controles en
la herramienta ejecutora. Un agente con acceso de escritura puede falsificar un
reporte; si necesitas una frontera de confianza, protege quién puede publicarlo.

## 6. Usa reportes como registros de decisiones

El estado debe sobrevivir al cierre del chat. Una implementación sencilla guarda
un archivo Markdown por actividad y añade una sección por intento completado.
Cada sección tiene tablas de campos y una descripción. El siguiente fragmento
muestra la cabecera y la tercera iteración; las anteriores se conservan en el
archivo real, y la numeración comienza en 1:

```markdown
# Implementation Report

| Field | Value |
|-------|-------|
| Gate | implement |
| Cycle | 01_example |
| Document | .harness/report/01_example/implement_artifacts/test_run.md |
| Created | 2026-11-13 14:30:00.000 |

---

## Iteration 3

| Field | Value |
|-------|-------|
| Date | 2026-11-13 15:20:00.000 |
| Timestamp | 2026-11-13_15-20-00-000 |
| Iteration | 3 |
| Cycle | 01_example |
| HITL | PASS |

### Description

Based on: review-plan iteration 2

Responde al feedback de evaluate iteration 1.
Se corrigió src/api/http/handler.py y verification/api/test/test_handler.py.
El comando, código de salida y conteos de la ejecución se registran aquí
y en implement_artifacts/test_run.md, con las rutas de evidencia del intento.
```

Este es un ejemplo de formato, no evidencia de una ejecución. En un reporte real
debes identificar la revisión exacta de los artefactos, los resultados observados
y la identidad o autorización de quien decide. Un nombre escrito por el agente
no autentica por sí solo una decisión humana.
Las fechas legibles y los timestamps para nombres de archivos los proporciona
una utilidad del harness; el agente no inventa ni mantiene un reloj independiente.

El campo `HITL` conserva solo dos valores de cierre; su interpretación depende de
quién tiene autoridad en esa actividad:

| Resultado | Significado |
|-----------|-------------|
| PASS en una actividad de trabajo | Salidas entregadas con las comprobaciones exigidas; no es una aceptación humana del producto. |
| PASS en una revisión humana | La persona aceptó el resultado presentado; su decisión y autor se conservan en Description. |
| FEEDBACK | Hay correcciones o decisiones pendientes; Description explica el motivo, los cambios y la ruta. |

El validador determinista informa su resultado y código de salida dentro de
Description; un error no puede convertirse en PASS por decisión del agente.
Cuando además se exige revisión humana, el resultado del programa no la sustituye.
`delivered`, `stale` o un estado desconocido son interpretaciones del lector, no
valores nuevos que deban escribirse en la fila HITL.

El parser reconoce `## Iteration N`, la tabla anterior a `### Description` y una
única fila `| HITL | PASS |` o `| HITL | FEEDBACK |`. No uses una fila con ambos
valores ni busques PASS dentro del texto libre o de ejemplos citados. Si la última
iteración está incompleta, bloquea el avance; no recuperes una aceptación antigua.
Publica la actualización de forma atómica y conserva las iteraciones anteriores.
Para un MVP, asigna un solo escritor por reporte; añade bloqueo si habrá concurrencia.

Los reportes Markdown son el origen de las decisiones. Un registro de proyectos
puede ayudar a localizarlos, pero no reemplaza ni duplica sus veredictos. Los
archivos de resultados de pruebas son evidencia; no son un segundo estado del flujo.

### Artefactos que acompañan al reporte

| Artefacto | Quién lo produce y qué contiene |
|-----------|--------------------------------|
| `design/plan.md` | Preparación: metadatos, entorno, componentes y módulos, contratos, dependencias, vectores de prueba, ejecución y trazabilidad. Incluye comando de arranque, URL o endpoint, resultado visible y cierre. |
| Checklist de revisión | Revisión: criterios cumplidos, hallazgos abiertos, recomendación, decisión humana y, en una reentrada, mapa de impacto. Se incorpora a Description. |
| `implement_artifacts/test_run.md` | Implementación: comandos exactos que la evaluación debe repetir; destino, SO/arquitectura y versiones; última ejecución local con código de salida y conteos; smoke del punto de entrada; IDs, tiempos y archivos de evidencia; telemetría y posibles inviabilidades. |
| `evaluate_artifacts/accepted_result.md` | Evaluación, solo tras PASS humano: ciclo e iteraciones de origen, entorno y preparación, herramientas, resultados por módulo y recorrido, telemetría, alcance demostrado y no demostrado, árbol entregado, evaluador e instrucciones de uso. |

`test_run.md` es un artefacto de trabajo que se respalda antes de sobrescribirlo;
no es un reporte append-only adicional. El reporte de la actividad sí conserva
sus iteraciones. La entrega final se llena desde una plantilla estable y permite
arrancar el producto sin tener que reconstruir la conversación del agente.

## 7. La aprobación debe corresponder al trabajo actual

Comprobar que un reporte contiene `HITL: PASS` es insuficiente. También debes comprobar
que pertenece al proyecto/ciclo correcto y que sigue describiendo sus entradas.

La regla de entrada es: todos los prerrequisitos existen, son válidos, tienen el
resultado requerido y siguen vigentes; además, no hay un feedback posterior que
impida continuar con esas mismas entradas. Cualquier condición desconocida bloquea
la actividad con una explicación concreta.

Supón que el plan tiene iteración 4 y la revisión acepta esa iteración. Si el plan
pasa a iteración 5, la revisión anterior queda obsoleta. La implementación basada
en ella también queda obsoleta, aunque su reporte conserve PASS. La evaluación
de esa implementación debe considerarse obsoleta por propagación.

Guarda la dependencia exacta como `Based on: <predecesor> iteration <N>` al inicio
de Description y recorre sus antecesores para calcular vigencia. La actividad de
entrada no lleva esa línea. El comando de estado señala la entrada que cambió y
la actividad que necesita repetirse, sin borrar reportes ni modificar decisiones.

Una referencia a la iteración no detecta ediciones directas del artefacto sin nuevo
reporte. Identifica también el candidato evaluado: por ejemplo, el digest del
documento revisado o el commit limpio de código y kit. Esa referencia se registra
en Description o en su artefacto de evidencia; no es un campo adicional obligatorio
en todas las iteraciones. Define qué entradas invalidan cada resultado.

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

Una iteración de evaluación con `| HITL | FEEDBACK |` usa la misma tabla anterior.
Su descripción puede seguir esta estructura; los nombres de pasos son genéricos:

```markdown
### Description

Based on: implement iteration 2
Verdict: module defect

1. Corregir src/api/http/handler.py: devuelve HTTP 500 ante un dato inválido; se esperaba
   HTTP 400. Evidencia: salida de la prueba del endpoint en el intento registrado.
2. Corregir verification/api/test/test_handler.py, repetir las comprobaciones
   afectadas y entregar otra iteración de implement. Conservar los demás módulos.

Decision: la persona revisora solicita estas correcciones.
```

La lista enumerada es el canal de reentrada: indica archivos y cambios concretos.
La implementación registra en Description qué iteración de evaluación responde;
la comunicación entre actividades permanece en los reportes. Antes de evaluar
otra vez, debe existir una nueva entrega de implementación. Si aparece
`Verdict: design defect`, se modifica el plan, se obtiene otra revisión humana y
se adapta la implementación siguiendo su mapa de impacto. El fallo de entorno
permite repetir el intento tras repararlo; no se etiqueta como defecto del producto.

Para correcciones de entradas en borrador, usa `report/<cycle>/DRAFT`, sin extensión
Markdown. Limítalo a las actividades de preparación/revisión que lo declaren: se
edita y comprueba sin añadir una iteración por cada errata. No autoriza avanzar.
Se retira cuando cada hallazgo tiene una resolución y se publica la iteración final.
Un cambio de línea base decidido puede cerrar el ciclo con
`Superseded by cycle: <nuevo-ciclo>` y reentrar con las entradas nuevas; las skills
rechazan ejecutar trabajo en un ciclo cerrado.

## 9. Distribuye el harness sin sobrescribir el proyecto

El generador instala la estructura; el agente ejecuta el trabajo dentro de ella.
Puedes ofrecer comandos para crear, inspeccionar, actualizar y diagnosticar un
proyecto sin implementar un servicio que llame al modelo y dirija cada transición.
Si después añades un ejecutor automático, debe consumir los mismos contratos.

El scaffolding inicial debe copiar skills y referencias, crear el manifiesto de
identidad, adaptar rutas y producir el mapa de instrucciones. Identifica la versión
de la distribución sin añadir por ello campos al protocolo de reportes. Valida el
proyecto generado, no solo las plantillas originales.

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

Al abrir una sesión, inspecciona primero identidad, ciclos, reportes y vigencia.
Pregunta qué ciclo usar y ofrece el activo como opción; no cambies la identidad
para abrir otro. Localiza el feedback pendiente y carga la skill correspondiente.
El historial del chat puede ayudar, pero no es el origen del estado del proyecto.

Las pausas dentro de una actividad tampoco son veredictos nuevos. Una respuesta
`continue`, `rework` o `stop` se conserva como `Checkpoint: <punto> — <respuesta> —
<nota>` en Description de la iteración completada. Si se detiene antes de entregar,
se conservan los archivos y no se escribe una iteración parcial para simular cierre.

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
