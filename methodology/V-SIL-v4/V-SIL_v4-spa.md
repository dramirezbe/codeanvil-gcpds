# V-SIL v4: Ciclo de Vida Stage-Gate Adaptativo con Planificación Ágil por Módulo para el Desarrollo de Prototipos Verificados Restringidos por Hardware COTS

**David Ramírez-Betancourt** — Universidad Nacional de Colombia, GCPDS  
**Versión:** 4.0-draft  
**Fecha:** Noviembre de 2026

---

## Resumen

V-SIL v4 es una metodología de desarrollo de software que recibe un Build Package finalizado (PRD con restricciones medibles, envolvente de hardware COTS, criterios de aceptación y, de forma opcional, procedimientos de laboratorio, calibración de hardware al grado de tamizaje del equipo de desarrollo y tolerancias en dBi) y entrega un Prototipo Verificado con evidencia por módulo y de extremo a extremo — o, cuando los requisitos son inviables sobre la plataforma COTS declarada, una Solicitud de Desviación (Request for Deviation, RFD) formal con análisis de compromisos. V-SIL v4 extiende la v3 con una **capa de planificación ágil** (S2 + G2) que descompone cada módulo en un ítem de backlog autocontenido con su propio mini-ciclo-V antes de iniciar la implementación, proporcionando contexto fresco por módulo y deltas trazables contra el Ground Truth del sistema. S1 produce una jerarquía sistema → subsistema → módulo; el Documento de Diseño del Sistema (SDD) es la espina arquitectónica viva de la que cada plan de módulo hereda los contratos. S1 puede diseñar un subsistema o un sistema de subsistemas: cada subsistema tiene su propia capa base y sus módulos, y los subsistemas se conectan mediante contratos versionados. S1 declara un modo HAL, `mock-only` o `mock+real`. Siempre diseña un **Mock HAL** que genera datos deterministas y sintéticos para VL-0 y VL-1, y un **telemetry companion** obligatorio que monitorea silenciosamente la unidad de cómputo durante todas las ejecuciones de prueba y nunca se entrega. Solo en `mock+real` añade un **Real HW HAL** que interactúa con el hardware físico para la generación de datasets de laboratorio y las pruebas de campo en VL-2. Un modelo de ML es una entrada opcional de S1 cuando el diseño lo utiliza; se entrena con datos del Mock HAL más etiquetado o, en su defecto, con datos del Real HW HAL más etiquetado. La implementación avanza módulo por módulo dentro de cada subsistema y después cruza sus fronteras, y cada módulo entra en S3 solo después de que su plan supera G2. La profundidad de verificación es adaptativa por módulo, con un piso obligatorio de pruebas unitarias, integración sándwich, contratos entre subsistemas y rutas de sistema. Cada afirmación nombra el nivel y el entorno de verificación en que se produjo; el telemetry companion adjunta el estado de la unidad de cómputo (CPU, memoria, temperatura, salud de buffers, latencia de planificación) a cada registro de evidencia. La salida terminal puede registrar trabajo futuro acotado para próximas versiones del software, sin aplazar criterios de aceptación vigentes. La terminología está alineada con IEEE/ISO/IEC 29119, ISO 26262, SDAD [6], el patrón Coordinator-Implementor-Verifier [10], la escalera de sustitución HAL mock→SIL→HIL para sistemas embebidos [11], el proceso de Request for Deviation de ECSS/MIL-HDBK-61A [16][17], el marco Agile V [19] y el modelo de trazabilidad delta OpenSpec [21].

```mermaid
flowchart LR
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px
    classDef vsil fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef output fill:#dcfce7,stroke:#16a34a,color:#14532d,stroke-width:2px
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-width:2px

    IN["Build Package<br/>PRD · envolvente COTS · criterios de aceptación<br/>opcional: procedimientos de lab · calibración · tolerancias"]:::input
    VSIL["V-SIL v4<br/>S0 → G0 → S1 → G1 → S2 → G2 → S3 → G3"]:::vsil
    OUT["Prototipo Verificado<br/>evidencia VL por módulo y ruta"]:::output
    RFD["Solicitud de Desviación<br/>evidencia de inviabilidad<br/>+ opciones de compromiso"]:::rfd

    IN --> VSIL
    VSIL -->|nominal| OUT
    VSIL -.->|inviable| RFD
    RFD -.->|Build Package actualizado| IN
```

---

## Novedades de v3 a v4

| Aspecto | v3 | v4 |
|---|---|---|
| **Cadena de etapas** | S0 → G0 → S1 → G1 → S2 → G2 | S0 → G0 → S1 → G1 → **S2 → G2** → S3 → G3 |
| **Salida de S1** | Topología de subsistemas + diseño en capas | + **descomposición en módulos** con estructura `modules/<id>/`; SDD como espina arquitectónica viva |
| **Alcance de G1** | Revisión de diseño | + valida la **completitud de la descomposición en módulos** |
| **S2 (NUEVA)** | — | **Planificación ágil por módulo (Agile-V)**: cada módulo se convierte en un ítem de backlog con su PLAN.md y mini-ciclo-V |
| **G2 (NUEVA)** | — | **Micro-compuerta por plan de módulo**: validación ligera de cada PLAN.md antes de la implementación |
| **S3** | S2 — Implementación | Renumerada; sin cambios de fondo |
| **G3** | G2 — Verificación adaptativa | Renumerada; sub-compuertas → G3.0, G3.1, G3.2; añade **defecto de plan → S2** |
| **Principios** | P1–P4 | + **P5: Contexto fresco por módulo** — cada plan es autocontenido, sin asumir contexto previo |
| **Modelo GT** | GT del sistema como canónico | + **delta vivo**: cada plan registra requisitos ADDED / MODIFIED / REMOVED como deltas trazables contra el GT [21] |
| **Orden del backlog** | — | Orden topológico del grafo de dependencias de S1: capas inferiores primero; contratos Mock-HAL como interfaz prioritaria |
| **Fuentes de RFD** | S1, G1, G2 | + **S2** (inviabilidad de planificación) y **G2** (defecto de plan) |
| **Referencias** | [1]–[18] | + [19] Agile V, [20] Spec-Kit, [21] OpenSpec |
| **Compatibilidad** | — | config.yaml, skills, vsil-verifier, Mock-HAL, telemetry companion: todo preservado |

---

## 1 Terminología

| Término informal | Término estándar | Fuente |
|---|---|---|
| Prueba de propagación (base → módulos con marcadores de posición) | **Prueba de integración descendente (top-down) con stubs** | IEEE 29119; Pressman [1] |
| Prueba de retropropagación (módulo → base) | **Prueba de integración ascendente (bottom-up) con drivers** | IEEE 29119; Pressman [1] |
| Propagación + retropropagación combinadas | **Prueba de integración sándwich (híbrida)** | IEEE 29119 [2] |
| Marcadores de posición | **Stubs** (invocados por la unidad bajo prueba) | SE estándar |
| Arneses de prueba que simulan a los invocadores | **Drivers** (invocan la unidad bajo prueba) | SE estándar |
| Validación del enrutador | **Verificación de contrato de interfaz** | Pruebas de contrato [3]; Bass et al. [4] |
| Diseño por capas | **Arquitectura en capas** con **grafo de dependencias de componentes** (DAG) | Bass et al. [4] |
| Niveles N0 / N1 / N2 | **Niveles de verificación** (VL-0, VL-1, VL-2) | Adaptado de ISO 26262 [5] |
| Realimentación al Build Package con compromisos | **Solicitud de Desviación (RFD)** | ECSS [16]; MIL-HDBK-61A [17]; NASA NPR 7150.2 [18] |
| Ítem de backlog por módulo | **PLAN.md** — especificación mini-V autocontenida por módulo | Agile V [19]; OpenSpec [21] |
| Delta de requisito | **ADDED / MODIFIED / REMOVED** trazado contra el GT del sistema | OpenSpec [21] |

---

## 2 Vista General de Etapas y Compuertas (Stage-Gate)

```mermaid
flowchart TD
    classDef stage fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef gate fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef newstage fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef newgate fill:#fce7f3,stroke:#db2777,color:#831843
    classDef terminal fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e,stroke-width:3px
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

    BP["Build Package"]:::input
    S0["S0 — Normalización + GT"]:::stage
    G0{"G0 — Validación estructural"}:::gate
    S1["S1 — Diseño del sistema + descomposición en módulos"]:::stage
    G1{"G1 — Revisión de diseño + descomposición (HITL)"}:::gate
    S2["S2 — Planificación ágil por módulo (NUEVA)"]:::newstage
    G2{"G2 — Micro-compuerta por plan de módulo (NUEVA)"}:::newgate
    S3["S3 — Implementación por subsistema + integración"]:::stage
    G3{"G3 — Verificación adaptativa"}:::gate
    T["Prototipo Verificado<br/>evidencia VL por módulo y ruta"]:::terminal
    RFD["RFD<br/>Solicitud de Desviación"]:::rfd

    BP --> S0
    S0 --> G0
    G0 -->|PASS + Compuerta H| S1
    S1 --> G1
    G1 -->|PASS| S2
    S2 --> G2
    G2 -->|PASS| S3
    S3 --> G3
    G3 -->|PASS| T

    G0 -.->|FAIL| S0
    G1 -.->|FAIL| S1
    G2 -.->|FAIL| S2
    G3 -.->|diseño| S1
    G3 -.->|plan| S2
    G3 -.->|módulo| S3

    S1 -.->|inviable| RFD
    S2 -.->|inviable| RFD
    G1 -.->|inviable| RFD
    G2 -.->|inviable| RFD
    G3 -.->|inviable| RFD
    RFD -.->|actualizado| BP
```

**Principios rectores.**
**P1.** HITL es una barrera de autorización; HIL es una barrera de validación.
**P2.** Oráculo ≠ generador — el modelo nunca aprueba su propio trabajo [7].
**P3.** G0 es la única compuerta determinista: su rechazo mecánico prevalece sobre cualquier aprobación [8]. Todos los demás veredictos de compuerta son humanos (HITL).
**P4.** *Verificado* ≠ *validado* — las afirmaciones nombran el entorno [9].
**P5.** *Contexto fresco por módulo* — cada plan de módulo (PLAN.md) es autocontenido: lleva cada contrato, requisito y referencia que su implementador necesita, sin asumir contexto previo de sesión. Esto previene la pérdida de contexto en sistemas grandes con tiempos de desarrollo prolongados.

---

## 3 S0 — Normalización y Ground Truth

```mermaid
flowchart LR
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937
    classDef process fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef output fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e

    BP["Build Package<br/>Obligaciones · COTS · QA<br/>opcional: procedimientos de lab · calibración · tolerancias"]:::input
    FILL["Completar blueprints<br/>IEEE 29148"]:::process
    StRS["G0_StRS.md<br/>§9.4"]:::output
    SyRS["G0_SyRS.md<br/>§9.5 · entradas de lab en §4–§6 (opcional)"]:::output

    BP --> FILL
    FILL --> StRS
    FILL --> SyRS
```

S0 **solo normaliza** — vierte el contenido del Build Package en los blueprints documentales de IEEE 29148 [12] y no emite ningún juicio conceptual sobre suficiencia o alcance. Los documentos producidos contienen únicamente la especificación completada, no las secciones de orientación al autor ni las filas de marcador de posición vacías, de modo que un bloque de ejemplo de plantilla nunca se lee como un requisito. Siguiendo la Fase 1 de SDAD (cristalización de la especificación) [6], completa los blueprints:

- **G0_StRS.md** — Especificación de Requisitos de las Partes Interesadas (Stakeholder Requirements Specification, §9.4): bloques `NRM-*`, `HWC-*`, `STK-*`.
- **G0_SyRS.md** — Especificación de Requisitos del Sistema (System Requirements Specification, §9.5): bloques `SYS-*` que trazan a la StRS.

Los procedimientos de laboratorio, la calibración y las tolerancias son contenido opcional del Build Package. Cuando existen, S0 los vierte en las secciones de la SyRS que ya existen para ellos: los procedimientos en §6 Field Measurement Protocols (`PROTO-*`: montaje, calibración, ejecución), los términos de calibración en §4 Correction Chains y las tolerancias en §5 Uncertainty Budgets. Los tres encabezados siguen siendo obligatorios para G0; sin entradas de laboratorio, cada uno contiene exactamente `Not applicable: no lab inputs in the Build Package.`

Cualquier iteración ocurre después en G0, que valida el contenido del Build Package contra la compuerta determinista (el blueprint) — no mediante un juicio de revisión aquí.

---

## 4 G0 — Validación Estructural

```mermaid
flowchart TD
    classDef doc fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef phase fill:#f0fdf4,stroke:#16a34a,color:#14532d
    classDef gate fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef fail fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

    StRS["G0_StRS.md"]:::doc
    SyRS["G0_SyRS.md"]:::doc
    SCRIPT["g0_validate.py<br/>determinista · solo stdlib · sin IA"]:::phase
    P1["Encabezados"]:::phase
    P2["Metadatos"]:::phase
    P3["Campos de bloque"]:::phase
    P4["G0-X entre documentos"]:::phase
    G0{"G0"}:::gate
    PASS["PASS → Compuerta H"]:::gate
    FAIL["FAIL → editar GT"]:::fail

    StRS & SyRS --> SCRIPT
    SCRIPT --> P1 & P2 & P3 & P4
    P1 & P2 & P3 & P4 --> G0
    G0 -->|exit 0| PASS
    G0 -->|exit 1| FAIL
    FAIL -.->|validar vs Build Package original| S0_
    S0_["S0"]:::doc
```

Determinista. Sin IA. Veredicto binario. Tras aprobar G0, la Compuerta humana H pregunta: *¿Los requisitos están completos, acotados y son verificables?*

---

## 5 S1 — Diseño del Sistema y Descomposición en Módulos

S1 primero divide el producto en subsistemas desplegables por separado cuando los requisitos lo justifican. Un solo subsistema sigue siendo un caso válido. Cada **subsistema** posee un proceso de ejecución, destino de despliegue, capa base, módulos y puertos externos. Sus módulos se comunican mediante su propia capa base; los intercambios entre subsistemas pasan por contratos de subsistema declarados y versionados. Separar la interfaz de usuario del proceso de borde se justifica cuando se despliegan o reinician independientemente, usan una red o tienen dominios de fallo distintos.

**Novedad en v4:** S1 además descompone cada subsistema en **módulos** nombrados con estructura de directorio explícita `modules/<id>/`. El SDD se convierte en la **espina arquitectónica viva**: cada plan de módulo (S2) hereda sus contratos, posición en capa y aristas de dependencia del SDD. S1 registra para cada módulo su `module_id`, `subsystem_id`, `layer`, `depends_on` (otros módulos), `provides` (contratos de interfaz), `hw_dependency` y `required_vl`. Esta descomposición se valida en G1.

### 5.1 Topología del sistema y asignación de requisitos

Las flechas siguientes son **mensajes en ejecución**, no dependencias de implementación.

```mermaid
flowchart LR
    GT["Un par StRS + SyRS"] --> MAP["SYS-* asignados a subsistemas y rutas"]
    MAP --> EDGE["Subsistema de borde<br/>SDR COTS + base local + módulos"]
    MAP --> UI["Subsistema UI<br/>base cliente + módulos"]
    EDGE -->|"occupancy.v1: mediciones"| UI
    UI -->|"configure.v1: comandos"| EDGE
```

La vista del sistema registra la responsabilidad, el destino de despliegue, los recursos COTS, el enlace de red y el ciclo de vida de cada subsistema. Un requisito puede asignarse a un subsistema o a una **ruta de extremo a extremo** que abarque varios. Una sola tabla de trazabilidad de sistema controla la asignación; los diseños de subsistema no duplican el Ground Truth. Los contratos entre subsistemas especifican productor y consumidor, esquema y versión, unidades, marcas de tiempo, orden, tasa, latencia, autenticación, reintentos, duplicados y comportamiento ante desconexión o reinicio cuando corresponda.

### 5.2 Arquitectura en capas dentro de cada subsistema

```mermaid
flowchart TD
    classDef base fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef mod fill:#e0e7ff,stroke:#4f46e5,color:#312e81
    classDef integ fill:#dbeafe,stroke:#2563eb,color:#1e3a8a

    subgraph ARCH["S1 produce para cada subsistema"]
        direction TD
        BASE["Capa Base<br/>Orquestación · HAL · enrutamiento de datos<br/>contratos de interfaz"]:::base
        subgraph MODS["Módulos (cada uno con directorio modules/id/)"]
            direction LR
            M1["M1"]:::mod
            M2["M2"]:::mod
            M3["M3"]:::mod
            MN["MN"]:::mod
        end
        INT["Integración<br/>Módulos conectados mediante interfaces de la capa base"]:::integ
    end

    BASE --> MODS --> INT
```

Los módulos son unidades enchufables (plug-in) que se comunican únicamente a través de la capa base y las interfaces declaradas de su subsistema. No hay llamadas directas entre módulos ni llamadas entre subsistemas que eludan un contrato de subsistema. Un subsistema sin hardware físico puede tener una HAL vacía; su base sigue encargándose de la orquestación y el enrutamiento.

### 5.3 Grafo de dependencias de componentes (ejemplo SDR FM en borde)

```mermaid
flowchart LR
    classDef hal fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef dsp fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef dec fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef out fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e

    HW["HackRF"]:::hal
    IQ["iq_acquisition<br/>VL-2 · HAL"]:::hal
    FFT["fft_engine<br/>VL-1 · DSP"]:::dsp
    FE["feature_extractor<br/>VL-1 · DSP"]:::dsp
    CL["classifier<br/>VL-0 · Decisión"]:::dec
    DEM["audio_demod<br/>VL-1 · Salida"]:::out
    DS["data_store<br/>VL-0 · Salida"]:::out

    HW -->|RF cruda| IQ
    IQ -->|raw_iq| FFT
    IQ -->|raw_iq| DEM
    FFT -->|psd_estimate| FE
    FE -->|channel_features| CL
    CL -->|occupancy_decision| DS
```

Cada arista transporta un **contrato de interfaz** (tipo de dato, versión de esquema, unidades, latencia). El grafo de dependencias de implementación de cada subsistema debe ser acíclico. Cada nodo lleva un **perfil de verificación**: `module_id`, `subsystem_id`, `layer`, `depends_on`, `provides`, `hw_dependency`, `required_vl`. `hw_dependency` significa que la corrección depende de un dispositivo o comportamiento físico específico, no simplemente que el código se ejecuta en una computadora.

El **grafo de dependencias de implementación** ordena la definición de contratos, las bases, los módulos y la integración del sistema. Debe ser acíclico para permitir la construcción con stubs en S3. El **grafo de interacción en ejecución** describe los mensajes reales y puede contener bucles intencionales, como telemetría del borde → UI → control del borde, siempre que los contratos definan propiedad del estado, confirmación, tiempos de espera y comportamiento seguro. Un bucle de mensajes no crea un ciclo de dependencias de implementación.

| Módulo | Capa | Dep. HW | VL requerido |
|---|---|---|---|
| `iq_acquisition` | HAL | **sí** | VL-2 (HIL) |
| `fft_engine` | DSP | no | VL-1 (SIL) |
| `feature_extractor` | DSP | no | VL-1 (SIL) |
| `classifier` | Decisión | no | VL-0 (unidad) |
| `audio_demod` | Salida | no | VL-1 (SIL) |
| `data_store` | Salida | no | VL-0 (unidad) |

### 5.4 Registro de descomposición en módulos

**Novedad en v4.** Para cada módulo identificado en el grafo de dependencias, S1 escribe un **registro de módulo** en el SDD:

```yaml
modules:
  - id: fft_engine
    subsystem: fm_edge
    layer: DSP
    depends_on: [iq_acquisition]
    provides: [psd_estimate]
    hw_dependency: false
    required_vl: VL-1
    traced_sys: [SYS-003, SYS-004]
    directory: modules/fft_engine/
```

La estructura de directorio `modules/` bajo la raíz del proyecto contiene un subdirectorio por módulo. Cada directorio de módulo recibirá su `PLAN.md` en S2. El SDD es la **espina arquitectónica viva**: es la única fuente de verdad para el grafo de módulos, y cada plan de módulo en S2 hereda sus contratos, capa y aristas de dependencia del SDD. Los cambios al SDD durante la realimentación de S3 o G3 se propagan a los planes de módulo afectados.

### 5.5 Modelo de ML suministrado (opcional)

**Estado: incierto.** Esta versión define el modelo de ML solo como entrada opcional de S1 y una comprobación de preparación en G1. Su conexión con S3 y G3 (generación de datos de entrenamiento, adaptador de inferencia, medición en G3) no está implementada y es trabajo futuro, junto con MLOps (FW-005).

El diseño S1 incluye esta caja **solo si elige un módulo basado en ML o el Ground Truth lo exige explícitamente**. En los demás casos no aparecen ni la caja ni su comprobación G1. El modelo suministrado es una entrada controlada de un módulo de subsistema, no un subsistema por sí mismo. Se entrena con datos del Mock HAL más etiquetado o, en su defecto, con datos del Real HW HAL más etiquetado. S1 no entrena ni selecciona un modelo por cuenta del autor del Build Package.

Cuando se utiliza, S1 identifica el archivo y los pesos por versión y digest; nombra al proveedor y la procedencia; registra la fuente de los datos de entrenamiento y el procedimiento de etiquetado; especifica runtime de inferencia, esquema de entradas y salidas, unidades, preprocesamiento, etiquetas o umbrales y posprocesamiento; y registra las métricas suministradas con su conjunto de evaluación y condiciones. Presupuesta latencia de inferencia, memoria y cualquier dependencia de dispositivos en la COTS declarada. Una respuesta simulada determinista permite integrar en VL-0; los niveles posteriores ejercitan el modelo suministrado real.

La metadata de rendimiento recibida es evidencia previa, no un veredicto de G3. Si S1 elige ML pero faltan el paquete del modelo o datos necesarios para implementarlo, G1 devuelve **FAIL** para completar la entrada o el diseño. La inviabilidad demostrada frente a los requisitos sobre la COTS declarada sigue la ruta RFD. Automatizar este ciclo de vida del modelo con MLOps es trabajo futuro (FW-005).

### 5.6 Escalera de sustitución HAL y telemetry companion

S1 declara el **modo HAL** en la Meta del diseño: `HAL mode: mock-only` o `HAL mode: mock+real`. Cada etapa posterior lo lee del diseño. Las implementaciones de HAL comparten el mismo contrato de interfaz de la capa base pero difieren en lo que produce `raw_iq`:

- **Mock HAL** (obligatorio en todo modo). Un generador de señales puramente software. En VL-0 emite vectores deterministas (cortos, repetibles, cobertura de casos límite). En VL-1 produce archivos I/Q sintéticos a SNR, modulación y condiciones de canal conocidas usando un sintetizador FM por software o capturas doradas grabadas. Cada vector dorado se versiona con un digest SHA-256, parámetros de generación, la condición que simula y la salida esperada. El Mock HAL es la fuente de datos por defecto para todas las pruebas de integración sándwich y SIL.

- **Real HW HAL** (solo en `mock+real`). La HAL de producción que interactúa con el SDR COTS declarado. Tiene dos propósitos: (a) ejecutar los procedimientos de laboratorio registrados en la SyRS (§6 `PROTO-*`) para generar **datasets reales** con la calidad de calibración del equipo de desarrollo (grado de tamizaje, no normativo, SyRS §4 Correction Chains) y las tolerancias declaradas en dBi (SyRS §5 Uncertainty Budgets); y (b) ejecutar las pruebas de campo finales en VL-2. El grado de calibración y las tolerancias son entradas registradas en la SyRS, no afirmaciones de V-SIL. El Real HW HAL puede declararse en VL-0 (API de dispositivo simulada) durante un ciclo, de modo que el software para el hardware real se construye sin validar métricas sobre él; G3.2 entonces no se activa y la declaración de honestidad lo indica.

En `mock-only`, el diseño no tiene Real HW HAL, ni procedimientos de laboratorio, calibración o tolerancias, ni módulos con `hw_dependency: true`; ignora las §4–§6 de la SyRS y toda afirmación queda limitada a VL-1 (§10.2). En `mock+real`, ambas HAL se conectan al mismo puerto de la capa base; intercambiar una por la otra es la **sustitución HAL** que mueve entre niveles de verificación [11].

S1 también especifica un **telemetry companion**, obligatorio en todo diseño y en toda ejecución de pruebas: un proceso ligero y no intrusivo que se ejecuta junto a cada ejecución de prueba y registra el estado de la unidad de cómputo — utilización de CPU, memoria disponible, temperatura, buffers perdidos y latencia de planificación. No debe interferir con el sistema bajo prueba; su propia huella de recursos se declara y se acota. El companion adjunta sus lecturas a cada registro de evidencia para que G3 pueda determinar si la unidad de cómputo estaba dentro de su envolvente de operación durante una prueba. El telemetry companion es infraestructura de verificación, no un módulo del sistema: pertenece a la metodología, no al software. No tiene `SYS-*`, no aparece en el DAG de implementación, está ausente de la evidencia por módulo del Prototipo Verificado y nunca se entrega con el software.

El Mock HAL, los vectores dorados con su manifiesto, el telemetry companion, los stubs, los pares simulados y los drivers forman el **kit de verificación**. S3 construye el kit en su capa inicial, antes de cualquier módulo, junto con el Real HW HAL y su API de dispositivo simulada en `mock+real` (§9).

La Meta del diseño de S1 declara además una entrada **`Toolchain`** por subsistema: `SUB-xxx: <package> · <language> · <package manager> · <test runner>`, por ejemplo `SUB-001: fm_edge · Python 3.12 · uv · pytest; SUB-002: dashboard · TypeScript · pnpm · vitest`. `<package>` es un identificador válido y nombra `src/<package>/`. Esta versión admite Python con uv y pytest, y TypeScript con pnpm y vitest. S3 construye con el toolchain declarado y nunca elige otro; un `Toolchain` vacío o incompleto es un defecto de diseño.

---

## 6 G1 — Validación de Diseño, Descomposición y Contratos

G1 responde: *¿Están resueltas todas las decisiones de diseño críticas para la implementación y la descomposición en módulos está completa?*

G1 es una revisión de diseño humana (HITL), no una compuerta determinista. Un agente puede preparar la revisión y recomendar un veredicto, incluida una RFD; decide el humano.

G1 no ejecuta scripts. El agente que la prepara valida por sí mismo: lee el diseño completo y el GT, rederiva cada comprobación desde las secciones fuente en lugar de confiar en los resúmenes del propio diseño, y ejecuta el toolchain declarado en la máquina de desarrollo. Una revisión exhaustiva justifica su costo en tokens. Los hallazgos del agente informan al humano; nunca se convierten en un veredicto automático.

1. **Topología de subsistemas.** Cada subsistema tiene responsabilidad, destino de despliegue, dueño del estado y puertos externos; la red y la envolvente COTS sustentan la topología.
2. **Aciclicidad del DAG de implementación.** Sin ciclos dentro de los subsistemas ni entre unidades de construcción. Los bucles de mensajes en ejecución se revisan aparte.
3. **Completitud de interfaces.** Cada arista interna tiene contrato tipado; cada intercambio entre subsistemas tiene contrato versionado y comportamiento ante fallos.
4. **Cobertura.** Cada `SYS-*` traza a módulos o a una ruta entre subsistemas, con responsable y evidencia de aceptación medible.
5. **Viabilidad de stubs.** Cada contrato interno o entre subsistemas permite escribir un stub o par simulado determinista.
6. **Consistencia del perfil de verificación.** `hw_dependency: true` → `required_vl: VL-2`; las rutas de sistema declaran nivel y entorno de verificación.
7. **Escalera de sustitución HAL.** El Mock HAL expone la interfaz de la capa base; los vectores dorados llevan digest, parámetros y salidas esperadas. En `mock+real`, el Real HW HAL expone la misma interfaz y referencia los `PROTO-*`, las cadenas de corrección y las tolerancias de la SyRS.
8. **Telemetry companion.** La especificación del companion declara qué monitorea, su intervalo de muestreo, su presupuesto de recursos y que su huella está acotada por debajo de un umbral declarado.
9. **Modelo de ML suministrado, si se utiliza.** Los pesos, la metadata, la fuente de los datos de entrenamiento y el procedimiento de etiquetado están identificados, el contrato de inferencia es implementable y el presupuesto COTS es creíble. Se omite esta comprobación cuando el diseño no tiene modelo de ML.
10. **Disponibilidad del toolchain.** En la máquina de desarrollo, el runtime del lenguaje y el gestor de paquetes de cada entrada de `Toolchain` responden a su comando de versión. El agente instala una herramienta faltante solo tras un breve sí del usuario; una instalación rechazada o fallida es un hallazgo abierto.
11. **Completitud de la descomposición en módulos (NOVEDAD).** Cada módulo en el SDD tiene `module_id`, `subsystem_id`, `layer`, `depends_on`, `provides`, `traced_sys`, `hw_dependency` y `required_vl`. Cada `SYS-*` aparece en al menos un `traced_sys` de algún módulo. Ningún módulo está huérfano (inalcanzable en el grafo de dependencias). La estructura de directorio `modules/` existe.

**PASS** → S2. **FAIL** → S1. **RFD** → §11.2, cuando los requisitos son inviables sobre la plataforma COTS declarada.

La [plantilla de diseño S1/G1](S1_G1_template.md) desarrolla estas familias en catorce puntos generales de revisión y uno condicional de ML, incluidos decisiones de diseño, coherencia COTS, escalera HAL, telemetry companion, disponibilidad del toolchain, descomposición en módulos y evaluación de riesgos.

---

## 7 S2 — Planificación por Módulo (Capa Agile-V)

**Novedad en v4.** S2 introduce una capa de planificación ágil entre el diseño (S1) y la implementación (S3). Cada módulo identificado en S1 recibe un **PLAN.md** autocontenido que funciona como ítem de backlog y como especificación mini-V. El objetivo es doble: (a) proporcionar **contexto fresco** (P5) para que cada módulo se pueda implementar en una sesión separada sin asumir contexto previo, y (b) producir **deltas trazables** contra el Ground Truth del sistema para que los cambios permanezcan auditables [21].

```mermaid
flowchart TD
    classDef plan fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef sdd fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef gt fill:#f3f4f6,stroke:#6b7280,color:#1f2937
    classDef gate fill:#fce7f3,stroke:#db2777,color:#831843

    SDD["SDD (espina viva de S1)<br/>grafo de módulos · contratos · capas"]:::sdd
    GT["GT del sistema<br/>G0_StRS.md + G0_SyRS.md"]:::gt

    SDD --> PLAN1["modules/fft_engine/PLAN.md"]:::plan
    SDD --> PLAN2["modules/classifier/PLAN.md"]:::plan
    SDD --> PLANN["modules/.../PLAN.md"]:::plan

    GT -.->|traza delta| PLAN1
    GT -.->|traza delta| PLAN2
    GT -.->|traza delta| PLANN

    PLAN1 --> G2{"G2 micro-compuerta"}:::gate
    PLAN2 --> G2
    PLANN --> G2
```

### 7.1 Orden del backlog

El backlog de módulos se ordena por **orden topológico** del grafo de dependencias de S1: capas inferiores primero, luego los módulos que dependen de ellas. Esto asegura que cuando un módulo entra en S3, sus dependencias ya están implementadas o tienen stubs disponibles desde la capa inicial de S3. Dentro del mismo nivel topológico, los módulos se pueden planificar e implementar en paralelo.

**Contratos Mock-HAL como interfaz prioritaria:** cada plan de módulo hereda sus contratos ascendentes y descendentes del SDD. Si una dependencia aún no está implementada, el módulo se construye contra el contrato Mock-HAL o stub declarado en el kit de verificación de S1. Así, S2 puede planificar todos los módulos después de G1, aunque se implementen de forma incremental.

### 7.2 Estructura de PLAN.md

Cada `modules/<id>/PLAN.md` es un documento autocontenido (P5) con las siguientes secciones:

```markdown
# Plan de Módulo: <module_id>

## Meta
- ID del módulo: <id>
- Subsistema: <subsystem_id>
- Capa: <layer>
- Depende de: [<module_ids>]
- Provee: [<interface_contracts>]
- Dependencia HW: <true|false>
- VL requerido: <VL-0|VL-1|VL-2>

## Alcance
Un párrafo que describe qué hace este módulo y su rol en el subsistema.

## Requisitos Trazados
| SYS-* | Descripción | Delta | Origen |
|---|---|---|---|
| SYS-003 | Resolución FFT | ADDED | G0_SyRS.md |

## Contratos Heredados
### Ascendentes (consume)
- `raw_iq` de `iq_acquisition`: esquema v1, tipo complex64, ...
### Descendentes (provee)
- `psd_estimate` a `feature_extractor`: esquema v1, tipo float32[], ...

## Tareas
Lista ordenada de tareas de implementación con dependencias y nivel de verificación:
1. Implementar núcleo FFT (depende de: capa base) — VL-0
2. Conectar a interfaz de capa base (depende de: tarea 1) — VL-0
3. Prueba de integración con vectores Mock HAL (depende de: tarea 2) — VL-1

## Plan de Verificación
- VL-0: pruebas unitarias con vectores deterministas
- VL-1: I/Q sintético del Mock HAL a SNR conocida

## Riesgos
- Riesgo R1: El tamaño de FFT puede exceder el presupuesto de latencia → mitigación: benchmark en tarea 1

## Referencias
- SDD §5.3 (grafo de dependencias)
- G0_SyRS.md SYS-003, SYS-004
- Manifiesto de vectores dorados del Mock HAL v1.2
```

### 7.3 Trazabilidad delta del GT vivo

El Ground Truth del sistema (G0_StRS.md + G0_SyRS.md) es el **estado canónico**. Cada plan de módulo registra un **delta** — un conjunto de entradas ADDED, MODIFIED o REMOVED contra el GT del sistema [21]. Esto hace trazable qué requisitos toca cada módulo y cómo.

| Tipo de delta | Significado |
|---|---|
| **ADDED** | Un nuevo requisito `SYS-*` es introducido por el alcance de este módulo |
| **MODIFIED** | Un `SYS-*` existente es refinado o restringido por este módulo |
| **REMOVED** | Un `SYS-*` previamente asignado se elimina de este módulo (reasignado o declarado inviable) |

Una entrada REMOVED debe trazar a una reasignación (ADDED/MODIFIED de otro módulo) o a una RFD. La unión de todos los deltas de módulo debe reconstruir la tabla de asignación `SYS-*` completa de S1.

### 7.4 RFD desde S2

S2 puede emitir una **RFD** cuando la planificación revela que los requisitos de un módulo son inviables antes de la implementación — por ejemplo, cuando los contratos heredados y las restricciones COTS hacen que los criterios de aceptación del módulo sean inalcanzables por análisis. La evidencia es analítica (aplica P4: no se nombra ningún nivel de verificación). La inviabilidad descubierta durante la implementación se reporta a través de G3.

---

## 8 G2 — Micro-Compuerta por Plan de Módulo

**Novedad en v4.** G2 es una compuerta de validación ligera, con alcance por módulo. Se activa una vez por plan de módulo (PLAN.md) antes de que ese módulo entre en S3. G2 es humana (HITL); un agente puede preparar la revisión.

```mermaid
flowchart LR
    classDef plan fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef check fill:#f0fdf4,stroke:#16a34a,color:#14532d
    classDef gate fill:#fce7f3,stroke:#db2777,color:#831843

    PLAN["modules/id/PLAN.md"]:::plan
    C1["Alcance + SYS-* trazados"]:::check
    C2["Contratos coinciden con SDD"]:::check
    C3["Tareas ordenadas + VL asignado"]:::check
    C4["Delta consistente con GT"]:::check
    C5["Riesgos identificados"]:::check
    G2{"G2"}:::gate

    PLAN --> C1 & C2 & C3 & C4 & C5
    C1 & C2 & C3 & C4 & C5 --> G2
```

G2 comprueba:

1. **Completitud de alcance.** El plan cubre todos los `SYS-*` asignados a este módulo en S1.
2. **Consistencia de contratos.** Los contratos ascendentes y descendentes del plan coinciden exactamente con los contratos de interfaz del SDD.
3. **Orden de tareas.** Las tareas están ordenadas de forma consistente con el grafo de dependencias; cada tarea nombra su VL.
4. **Consistencia del delta.** Los deltas ADDED/MODIFIED/REMOVED del plan son consistentes con el GT del sistema. Ningún `SYS-*` se pierde.
5. **Viabilidad del plan de verificación.** El VL declarado es alcanzable dada la `hw_dependency` del módulo y el modo HAL.
6. **Reconocimiento de riesgos.** Se identifica al menos un riesgo, o el plan declara explícitamente que no hay ninguno.
7. **Autocontención (P5).** El plan incluye cada contrato, referencia de requisitos y especificación necesaria para implementar el módulo sin leer otros planes de módulo.

**PASS** → el módulo entra en S3. **FAIL** → S2 (revisar el plan). **RFD** → §11.2 (inviabilidad de planificación).

G2 es intencionalmente ligera: valida la estructura y consistencia del plan, no la implementación. Su costo en tokens y tiempo es pequeño en relación con S3 y G3.

---

## 9 S3 — Implementación por Subsistema e Integración del Sistema

```mermaid
flowchart TD
    classDef base fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef mod fill:#e0e7ff,stroke:#4f46e5,color:#312e81
    classDef test fill:#f0fdf4,stroke:#16a34a,color:#14532d
    classDef stub fill:#f3f4f6,stroke:#9ca3af,color:#374151,stroke-dasharray:5 3

    subgraph STEP1["Paso 1 — Capa inicial: base + kit de verificación"]
        B["Implementar capa base<br/>orquestación · HAL · enrutamiento"]:::base
        KIT["Construir kit de verificación<br/>Mock HAL · vectores dorados + manifiesto<br/>telemetry companion · pares simulados · drivers"]:::stub
        STUBS["Generar stubs<br/>desde los contratos de G1"]:::stub
        TD["Integración descendente<br/>base + todos los stubs"]:::test
        B --> KIT --> STUBS --> TD
    end

    subgraph STEP2["Paso 2 — Cada módulo (orden de backlog de S2)"]
        IMPL["Implementar módulo<br/>según su PLAN.md"]:::mod
        UT["Prueba unitaria<br/>en aislamiento"]:::test
        BU["Integración ascendente<br/>módulo + driver vs base"]:::test
        IMPL --> UT --> BU
    end

    TD --> STEP2
    STEP2 --> CONTRACT["Paso 3 — Pruebas de contratos entre subsistemas<br/>subsistemas reales + pares simulados"]:::test
    CONTRACT --> SYSTEM["Paso 4 — Rutas de sistema<br/>subsistemas conectados"]:::test
```

Descendente (base → stubs) + ascendente (módulo → driver → base) = **prueba de integración sándwich** [1][2][13].

El Paso 1 es la **capa inicial**: antes de cualquier módulo, S3 construye la base de cada subsistema y deja listas todas las herramientas — el kit de verificación de §5.6 y, en `mock+real`, el Real HW HAL con su API de dispositivo simulada. S3 escribe todas las pruebas, incluidas las pruebas VL-1 de los módulos y rutas con `required_vl` VL-1 o superior, sin afirmarlas; G3 solo las ejecuta (§10.3).

**Novedad en v4:** el Paso 2 sigue el **orden de backlog** establecido en S2. Cada módulo entra en implementación solo después de que su PLAN.md supera G2. El implementador lee el PLAN.md como especificación principal (P5: contexto fresco), no el SDD completo. El PLAN.md lleva cada contrato y referencia de requisito necesaria.

Cada subsistema vive en `src/<subsystem>/` y se construye con su toolchain declarado; el kit de verificación, pruebas incluidas, vive en `verification/` y nunca se entrega; un comando ejecuta cada nivel de verificación (`verification/run.sh vl0`, `verification/run.sh vl1`); y el código entregado no depende de CodeAnvil.

Se definen primero los contratos entre subsistemas para construir cada subsistema independientemente contra un par simulado determinista. Los subsistemas reales se conectan después de superar su piso local VL-0. Para cada `SYS-*` asignado a varios subsistemas se ejecuta una prueba determinista de la ruta entre los procesos reales, con entradas externas simuladas. Así se comprueban serialización, enrutamiento, transferencia de estado y recuperación en la frontera declarada; VL-1 y VL-2 añaden entornos y mediciones más exigentes.

*Trabajo futuro (FW-005, §5.5).* Si un subsistema utiliza un modelo de ML suministrado, S3 implementa su adaptador de inferencia y prueba el preprocesamiento, la interpretación de salidas y el comportamiento ante fallos declarados. La respuesta simulada ejercita el contrato del módulo circundante en VL-0; las pruebas que afirman comportamiento del modelo utilizan los pesos identificados.

### Fuentes de datos por nivel de verificación

La escalera de sustitución HAL determina qué alimenta el pipeline en cada nivel. El **telemetry companion** se ejecuta durante cada prueba en todos los niveles. VL-2 requiere `HAL mode: mock+real`.

| Nivel | Fuente de datos | HAL utilizada | Telemetry companion |
|---|---|---|---|
| **VL-0** | Vectores dorados deterministas (cortos, repetibles, casos límite) | Mock HAL | Registra estado de UC; adjunto a evidencia |
| **VL-1** | I/Q sintético a SNR, modulación y canal conocidos | Mock HAL | Registra estado de UC; adjunto a evidencia |
| **VL-2** | RF real vía SDR COTS; datasets generados siguiendo los procedimientos de lab de la SyRS (`PROTO-*`) con calibración y tolerancias declaradas; solo en `mock+real` | Real HW HAL | Registra estado de UC; adjunto a evidencia |

### Gobernanza de vectores dorados

Cada vector dorado o captura sintética utilizado por el Mock HAL es un artefacto controlado: lleva un identificador único, digest SHA-256, parámetros de generación, la condición que simula (nominal, caso límite, degradado) y la salida esperada en el contrato del módulo consumidor. Cambiar un vector invalida todo registro de evidencia que lo haya utilizado. El conjunto de vectores dorados se versiona junto con el código fuente.

### Piso obligatorio (VL-0) — no se puede omitir

| Componente | Siempre requerido |
|---|---|
| **Capa base** | Prueba unitaria + integración descendente con stubs |
| **Cada módulo** | Prueba unitaria + integración ascendente con driver |
| **Cada contrato entre subsistemas** | Pruebas del productor y consumidor con un par simulado, incluidos casos de versión y fallo |
| **Cada ruta SYS-* entre subsistemas** | Prueba determinista entre procesos conectados con entradas externas simuladas |
| **Telemetry companion** | Ejecutándose y registrando durante todas las pruebas anteriores; estado de UC adjunto a cada registro de evidencia |

---

## 10 G3 — Compuerta de Verificación Adaptativa

### 10.1 Niveles de verificación

```mermaid
flowchart LR
    classDef mandatory fill:#dcfce7,stroke:#16a34a,color:#14532d,stroke-width:2px
    classDef optional fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-dasharray:5 3
    classDef hil fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-dasharray:5 3

    VL0["VL-0 — Lógica<br/>Unidad + sándwich + contratos de subsistema<br/>Rutas deterministas · OBLIGATORIO"]:::mandatory
    VL1["VL-1 — Mock / SIL<br/>+ prueba medida de varios subsistemas<br/>I/Q sintético · GnuRadio · OPCIONAL"]:::optional
    VL2["VL-2 — HIL<br/>+ aceptación extremo a extremo donde se declare<br/>HW real · enlace representativo · OPCIONAL<br/>solo en mock+real"]:::hil

    VL0 -->|"el usuario decide ▸"| VL1 -->|"el usuario decide ▸"| VL2
```

Cada nivel incluye todas las pruebas de los niveles inferiores. La escalera de sustitución HAL (§5.6) determina qué alimenta el pipeline: Mock HAL en VL-0 y VL-1, Real HW HAL en VL-2 (solo en `mock+real`). El telemetry companion se ejecuta en todos los niveles.

### 10.2 Regla adaptativa

El usuario elige el nivel de verificación por módulo y por ruta de sistema, por ciclo. Cuatro restricciones:

1. **Piso.** Cada módulo, contrato entre subsistemas y ruta de sistema declarada alcanza VL-0 en cada ciclo.
2. **Honestidad.** Ninguna afirmación por módulo o de extremo a extremo supera el entorno realmente probado. Aprobar subsistemas por separado no demuestra un requisito entre subsistemas.
3. **Contexto de telemetría.** Todo registro de evidencia incluye las lecturas del telemetry companion para la unidad de cómputo durante esa prueba. La evidencia producida mientras la UC estaba fuera de su envolvente de operación declarada (temperatura, saturación de CPU, buffers perdidos) se marca y puede ser invalidada por el revisor.
4. **Techo por modo HAL.** `mock-only` limita toda afirmación a VL-1. `mock+real` admite VL-2, pero cada módulo y ruta sigue declarando su nivel por ciclo: el Real HW HAL puede declararse en VL-0 (API de dispositivo simulada) durante un ciclo, en cuyo caso G3.2 no se activa y la declaración de honestidad lo indica. PIL (Processor-in-the-Loop) usa el procesador objetivo real con entradas del Mock HAL; toda afirmación PIL permanece VERIFICADA, nunca VALIDADA.

| Escenario | El usuario declara | G3 verifica |
|---|---|---|
| Iteración rápida | VL-0 en todos | Unidad + sándwich por módulo; contratos y rutas deterministas entre subsistemas |
| Validación de DSP | VL-1 para DSP; VL-0 el resto | Mock/SIL para DSP; piso VL-0 para cada ruta de sistema |
| Pre-lanzamiento (`mock+real`) | VL-1 para la ruta borde → UI; VL-2 para `iq_acquisition` | Ruta multisubsistema medida y adquisición HIL |
| Lanzamiento completo | Módulos y rutas en su `required_vl` | Cada afirmación en el nivel declarado en S1 |

### 10.3 Sub-compuertas

G3 ejecuta las pruebas que escribió S3 y no escribe ninguna; un nivel declarado sin prueba es un defecto de módulo que se enruta a S3. Las ejecuciones ocurren en un contexto verificador separado y de solo lectura — un subagente cuando el runtime lo admite; en otro caso, una sesión nueva —, que implementa P2: el oráculo no es el generador.

**Enrolamiento de hardware.** Antes de que G3.2 pueda activarse, el objetivo debe estar enrolado en `.codeanvil/project.yaml` mediante `codeanvil credential-setup -u <admin-user> -i <host> --port 22`. G3.0 y G3.1 pueden ejecutarse localmente mientras el enrolamiento está pendiente; G3.2 bloquea hasta que exista una entrada `targets:` válida.

| Sub-compuerta | Se activa cuando | Verifica |
|---|---|---|
| **G3.0** | Siempre | Pasan unidad, sándwich, contratos entre subsistemas y rutas deterministas; vectores dorados del Mock HAL; telemetry companion confirma UC nominal |
| **G3.1** | VL-1+ declarado para módulo o ruta | I/Q sintético del Mock HAL; pasan pruebas Mock/SIL entre subsistemas afectados; métricas dentro de umbrales; telemetry companion confirma UC nominal |
| **G3.2** | VL-2 declarado para módulo o ruta | Real HW HAL sobre SDR COTS (solo en `mock+real`); enrolamiento requerido (ver arriba); datasets de los procedimientos de lab de la SyRS (`PROTO-*`) con calibración y tolerancias declaradas; para rutas entre subsistemas, enlace representativo; mediciones dentro de los criterios; telemetry companion confirma UC nominal |

**Operacional vs defecto.** Antes de enrutar un fallo de G3, clasifícalo. Un problema de permisos, driver, grupo, udev o acceso USB en el DUT objetivo es **operacional** — se corrige en el DUT y se re-ejecuta G3; nunca es un defecto de módulo o diseño y no debe enrutarse a S3 ni a S1. Un fallo transitorio de SSH, reloj o configuración es operacional de la misma manera. Solo un fallo conductual genuino del código entregado bajo condiciones de operación correctas es un **defecto de módulo** (→ S3), **defecto de plan** (→ S2) o **defecto de diseño** (→ S1). Los cinco outcomes de primera clase de G3 son: **corrección operacional**, **defecto de módulo**, **defecto de plan**, **defecto de diseño** y **RFD**.

**Novedad en v4: defecto de plan → S2.** Cuando G3 revela que el PLAN.md de un módulo estaba incompleto o era inconsistente — por ejemplo, un contrato faltante o una asignación de VL incorrecta — el defecto se enruta a S2 para revisión del plan en lugar de a S1 para un rediseño completo. Este bucle de realimentación más ligero mantiene la iteración ágil rápida.

*Trabajo futuro (FW-005, §5.5).* Para un módulo o una ruta basados en ML, G3 mide el modelo suministrado *dentro del sistema implementado* en el nivel declarado y comprueba los criterios `SYS-*` correspondientes. La metadata de rendimiento recibida en S1 orienta el diseño de pruebas, pero no sustituye estas mediciones.

---

## 11 Enrutamiento de la Realimentación

V-SIL produce dos tipos de realimentación. Son estructuralmente diferentes y no deben confundirse.

```mermaid
flowchart TD
    classDef defect fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef stage fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef plan fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef ext fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px

    FAIL["Fallo de compuerta"]:::defect
    CLS{"¿Defecto<br/>o inviabilidad?"}

    subgraph INTERNAL["Interno — Defecto (se corrige dentro de V-SIL)"]
        direction LR
        D_S1["S1 — defecto de diseño"]:::stage
        D_S2["S2 — defecto de plan"]:::plan
        D_S3["S3 — defecto de módulo"]:::stage
    end

    subgraph EXTERNAL["Externo — RFD (el Build Package debe cambiar)"]
        direction LR
        RFD["Solicitud de Desviación"]:::rfd
        BP["Autor del<br/>Build Package"]:::ext
        RFD --> BP
    end

    FAIL --> CLS
    CLS -->|"implementación<br/>diseño o plan"| INTERNAL
    CLS -->|"requisitos<br/>inviables"| EXTERNAL
```

### 11.1 Enrutamiento de defectos internos

Un **defecto** significa que V-SIL puede corregirlo internamente. La implementación, el plan o el diseño está mal, pero los requisitos son alcanzables. Un **problema operacional** no es un defecto: es un fallo de DUT/entorno que bloquea la medición; se corrige y se re-ejecuta G3 sin tocar S1, S2 ni S3.

| Clase | Se enruta a | Ejemplo |
|---|---|---|
| Problema operacional | Corregir DUT → re-ejecutar G3 | `codeanvil-agent` no puede abrir el HackRF; fallo de autenticación SSH; falta regla udev |
| Defecto de diseño | S1 | El DAG tiene una dependencia no declarada; falta propiedad del estado o un contrato entre subsistemas |
| Defecto de plan | S2 | PLAN.md con un contrato faltante; asignación de VL incorrecta; delta inconsistente con el GT |
| Defecto de módulo o integración | S3 | La FFT produce un valor incorrecto; la UI interpreta mal un mensaje válido del borde |

**Autodiagnóstico:** si un módulo que *no* fue modificado falla durante la re-prueba → dependencia no declarada → defecto de diseño → S1.

### 11.2 Solicitud de Desviación (RFD)

Una **RFD** significa que los requisitos del Build Package son **inviables sobre la plataforma COTS declarada**. V-SIL no puede corregirlo internamente — las restricciones mismas deben cambiar. V-SIL **se suspende** hasta que el Build Package se actualice y reingresa en S0.

Una RFD puede emitirse desde **S1, S2, G1, G2 o cualquier sub-compuerta de G3**. S0 y G0 no la emiten: S0 no hace ningún juicio de viabilidad y G0 solo comprueba la estructura. La inviabilidad descubierta al implementar en S3 se reporta a través de G3.

| Descubierta en | Ejemplo |
|---|---|
| S1 | La latencia del pipeline excede el requisito bajo cualquier particionamiento sobre este HW |
| S2 | La planificación del módulo revela restricciones de contrato mutuamente excluyentes bajo el presupuesto COTS |
| G1 | La revisión de diseño concluye que un presupuesto de latencia no se puede cumplir sobre este HW, ni con el diseño revisado ni con otro particionamiento |
| G2 | La revisión del plan revela que los criterios de aceptación del módulo son analíticamente inalcanzables |
| G3.0 | Las pruebas unitarias revelan que dos requisitos normativos entran en conflicto matemáticamente |
| G3.1 | Las métricas SIL muestran que P_d y P_fa no pueden cumplir simultáneamente los umbrales |
| G3.2 | HIL muestra que el piso de ruido del hardware real excede el presupuesto asumido |

En S1, S2, G1 y G2 aún no se ha medido nada, así que la evidencia es de análisis y no nombra ningún nivel de verificación (P4).

### 11.3 Contenido de la RFD

Según ECSS [16], MIL-HDBK-61A [17] y NASA NPR 7150.2 [18]:

```
Solicitud de Desviación — RFD-001

  Requisitos en conflicto:
    STK-007: Latencia ≤ 100 ms    (fuente: ITU-R SM.1880)
    STK-012: P_d ≥ 0.95 @ 10 dB   (fuente: regulador nacional)

  Evidencia (de G3.1, VL-1):
    FFT 4096 → P_d 0.96, latencia 142 ms  — STK-012 cumplido, STK-007 violado
    FFT 2048 → P_d 0.91, latencia 71 ms   — STK-007 cumplido, STK-012 violado

  Opciones de compromiso:
    A) Relajar latencia a ≤ 150 ms                → ambos cumplidos
    B) Relajar P_d a ≥ 0.92                       → ambos cumplidos
    C) Modo dual: rápido (2048) + profundo (4096) → ambos cumplidos, añade complejidad

  Análisis de impacto:
    Opción A: requiere exención normativa de ITU-R SM.1880 §4.3
    Opción B: solo grado de tamizaje (screening), no grado de cumplimiento
    Opción C: nuevo módulo, nuevo contrato de interfaz, retrabajo de S1

  Recomendación: C
```

### 11.4 Resumen de la distinción

```mermaid
flowchart LR
    classDef defect fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef ops fill:#f3f4f6,stroke:#6b7280,color:#374151

    O["Corrección operacional<br/>Problema de DUT/entorno<br/>Corregir objetivo → re-ejecutar G3<br/>Sin cambio en S1, S2 ni S3"]:::ops
    D["Defecto<br/>Requisitos alcanzables<br/>Implementación, plan o diseño incorrecto<br/>Corregir dentro de V-SIL"]:::defect
    R["RFD<br/>Requisitos inviables<br/>COTS no puede cumplir ambos<br/>El Build Package debe cambiar"]:::rfd

    O ---|"distinto de"| D ---|"distinto de"| R
```

### 11.5 Triaje de fallos y modo borrador (S0 · G0 · G1)

Las etapas de requisitos son exploratorias: el Ground Truth se corrige muchas veces antes de ser
sólido. V-SIL v4 suaviza el *bucle*, no las *comprobaciones*, mediante dos dispositivos acotados
a S0, G0 y G1 — nunca a S2, S3 ni G3.

**Triaje de fallos.** Un fallo de máquina o de compuerta se traduce antes de que llegue al humano. Para
cada ERROR de G0, cada marcador de posición de lista faltante y cada hallazgo `open` de G1, el agente
expone el problema real en lenguaje llano — describiendo cada requisito por lo que pide, con su ID de bloque
solo entre paréntesis, de modo que el lector nunca abra un documento para saber qué es un ítem — y ofrece
de dos a cuatro opciones concretas de reconciliación (conectar un ítem sin enlace, crear su origen faltante,
eliminarlo o relajarlo, o — cuando la laguna es un hecho documental y el runtime tiene acceso web —
buscarlo en la web y proponer el valor hallado con su fuente para que el humano lo confirme), cada una con su
consecuencia. El humano elige; el agente aplica. El agente es el intérprete, nunca el oráculo: el veredicto
sigue siendo el código de salida del validador (G0) o la respuesta del humano (Compuerta H, G1), sin tocar
P2 ni P3.

**Modo borrador.** Cuando una etapa de requisitos encuentra ítems sin resolver — una entrada de lista
faltante, un error de formato o un hallazgo abierto de G1 — **entra en modo borrador automáticamente** y
no puede avanzar hasta que **cada uno esté resuelto**. Las correcciones mecánicas que no inventan nada
— eliminar andamiaje de blueprint, completar un valor ya declarado en otro lugar, eliminar una referencia
rota — se **aplican automáticamente y se reportan**, sin preguntar; solo las decisiones de juicio van al
humano, quien **las corrige**, conscientemente **las ignora/acepta** (registrado con el nombre de quien decide) o **escala** a una RFD. Mientras está en borrador, la etapa se ejecuta contra los archivos actuales,
aplica triaje y bucles sin escribir una iteración de informe ni forzar obsolescencia; el humano puede editar
el par GT directamente. Al hacer commit — al que solo se llega cuando cada ítem está decidido — se elimina
el marcador y se escribe una sola ejecución registrada, listando cada ítem y su decisión. Un error de
formato se puede corregir o escalar pero nunca ignorar para aprobar, ya que el validador determinista lo sigue
rechazando. El trail de auditoría registra la ejecución que aprueba y las decisiones detrás de ella, no el
camino rojo hasta ella.

---

## 12 Salida Terminal

El Prototipo Verificado presenta el árbol entregado (`src/<subsystem>/`) separado del kit de verificación (`verification/`), los planes de módulo (`modules/`) y nombra el contexto verificador en el que G3 ejecutó las pruebas.

```
Prototipo Verificado — V-SIL v4
  Ciclo: pre_release_01
  Modo HAL: mock+real

  Software entregado:
    src/fm_edge/, src/dashboard/ — sin dependencia de CodeAnvil
  Planes de módulo (artefacto de diseño, no se entrega):
    modules/ — archivos PLAN.md por módulo con deltas trazados
  Kit de verificación (no se entrega):
    verification/ — Mock HAL, vectores dorados + manifiesto, telemetry
                    companion, stubs, pares simulados, drivers, pruebas
  Contexto verificador: subagente verificador de solo lectura (contexto nuevo)

  Evidencia por módulo:
    iq_acquisition:    VL-2 (HIL)  — Real HW HAL, HackRF One, FM 88–108 MHz
    fft_engine:        VL-1 (SIL)  — Mock HAL, I/Q dorado (vectores v1.2, SHA bc3f…)
    feature_extractor: VL-1 (SIL)  — Mock HAL, PSD sintético a SNR conocida
    classifier:        VL-0 (lógica)— Mock HAL, vectores deterministas
    audio_demod:       VL-1 (SIL)  — Mock HAL, I/Q sintético modulado en FM
    data_store:        VL-0 (lógica)— Mock HAL, vectores deterministas
    dashboard:         VL-1 (SIL)  — mensajes del borde en enlace simulado
    controls:          VL-0 (lógica)— vectores de comandos y confirmaciones
    alerts:            VL-0 (lógica)— unidad + integración sándwich
    history:           VL-0 (lógica)— unidad + integración sándwich

  Evidencia por subsistema y ruta de sistema:
    borde -> UI occupancy.v1: VL-1 — esquema + latencia en enlace simulado
    UI -> borde configure.v1: VL-0 — comandos, reintentos y duplicados
    PATH-001 / SYS-002 pantalla de ocupación: VL-1 — borde + UI, Mock HAL RF sintética

  Reporte del telemetry companion:
    Todas las pruebas: UC dentro de envolvente de operación
    CPU pico: 63%  |  Temp pico: 68 °C  |  Buffers perdidos: 0
    Ninguna evidencia invalidada por condiciones de UC.

  Declaración de honestidad:
    Módulos VL-1: VERIFICADOS contra datos sintéticos (Mock HAL).
    Módulos VL-2: VALIDADOS en hardware real (Real HW HAL);
                  calibración: grado de tamizaje según SyRS §4;
                  tolerancias: ±2.1 dBi declaradas por el equipo de desarrollo (SyRS §5).
    Módulos VL-0: VERIFICADOS solo a nivel de lógica.
    SYS-002: VERIFICADO entre subsistemas conectados con entrada sintética;
             sin afirmación de latencia en enlace real o HIL.
    Telemetry companion: UC nominal durante todas las ejecuciones de prueba.

  RFD emitidas: 0
```

### 12.1 Registro opcional de trabajo futuro

Después de G3, el prototipo puede incluir propuestas para próximas **versiones del software**. Cada entrada registra ID, capacidad o mejora propuesta, origen y evidencia, versión candidata, responsable de decidir, dependencias y criterio de aceptación propuesto. Si no hay entradas, se omite el registro. El autor del Build Package decide si una propuesta entra en otra versión; una propuesta aceptada se convierte en entrada nueva para S0 y G0. Automatizar CI/CD en el futuro es una posible entrada de infraestructura para una versión posterior; construir ese pipeline queda fuera de esta versión de V-SIL.

Aquí solo entra trabajo expresamente fuera del alcance aprobado del ciclo actual. Un `SYS-*` vigente que falla sigue siendo un defecto por corregir o, si es inviable en la COTS declarada, una RFD; el registro no lo convierte en una afirmación aprobada.

```text
FW-001 — Automatizar la evidencia de verificación V-SIL en CI/CD
  Categoría: infraestructura de verificación
  Origen: ejecución manual repetida de G3 en este ciclo
  Versión candidata: versión posterior del software
  Responsable de decidir: autor del Build Package
  Dependencia: comandos de prueba y formato de informe estables
  Aceptación propuesta: un pipeline reproduce las comprobaciones G3
                       declaradas y vincula los informes al ciclo y revisión fuente

FW-002 — Processor-in-the-Loop (PIL) como sub-compuerta completa
  Categoría: profundidad de verificación
  Estado: parcialmente implementado — G3 ya permite PIL como modo declarado
          (procesador objetivo real, entradas del Mock HAL, afirmación permanece
          VERIFICADA); una sub-compuerta G3.PIL con verificaciones estructuradas
          de temporización y planificación aún no está definida
  Origen: revisión SOTA; cuando la UC ≠ host de desarrollo, el código
          compilado en el procesador objetivo puede comportarse diferente
          bajo restricciones de temporización
  Versión candidata: versión posterior del software
  Responsable de decidir: autor del Build Package
  Dependencia: UC objetivo identificada y accesible para compilación cruzada
  Aceptación propuesta: sub-compuerta G3.PIL definida con verificaciones
                       explícitas de temporización, planificación y recursos
                       en el procesador objetivo

FW-003 — Inyección formal de fallos en VL-2
  Categoría: profundidad de verificación
  Origen: revisión SOTA (ISO 26262-5 §10; IEC 61508-3 Tabla A.5);
          las pruebas VL-2 actuales solo prueban operación nominal
  Versión candidata: versión posterior del software
  Responsable de decidir: autor del Build Package
  Dependencia: escenarios de fallo definidos por módulo (desconexión USB,
              desbordamiento de buffer, desviación de reloj SDR, fallo de energía UC)
  Aceptación propuesta: escenarios de fallo declarados ejecutados en VL-2;
                       respuesta del sistema documentada por escenario

FW-004 — Medición de correlación SIL ↔ HIL
  Categoría: confianza en la verificación
  Origen: revisión SOTA; los resultados VL-1 y VL-2 se reportan independientemente
          sin correlación medida entre ellos
  Versión candidata: versión posterior del software
  Responsable de decidir: autor del Build Package
  Dependencia: tanto VL-1 como VL-2 ejecutados para los mismos módulos
  Aceptación propuesta: desviación cuantificada entre resultados Mock HAL y
                       Real HW HAL para los casos de prueba superpuestos

FW-005 — MLOps para el modelo de ML opcional
  Categoría: ciclo de vida del modelo
  Origen: el modelo de ML opcional se entrena y etiqueta fuera de un
          pipeline automatizado, y su integración con S3 y G3 aún no
          está implementada (§5.5)
  Versión candidata: versión posterior del software
  Responsable de decidir: autor del Build Package
  Dependencia: datasets versionados del Mock HAL o del Real HW HAL y un
               procedimiento de etiquetado declarado
  Aceptación propuesta: un pipeline reproduce el entrenamiento a partir de
                       datos y etiquetas versionados y vincula cada versión
                       del modelo con su evidencia de G3
```

---

## 13 Referencias

[1] R. S. Pressman, B. R. Maxim, *Software Engineering*, 9.ª ed., 2020.
[2] ISO/IEC/IEEE 29119-1:2022, "Software testing — Part 1."
[3] Codeburst, "The Basics of Contract Tests," 2024.
[4] L. Bass, P. Clements, R. Kazman, *Software Architecture in Practice*, 4.ª ed., 2021.
[5] ISO 26262:2018, "Road vehicles — Functional safety."
[6] V. H. Nguyen, T. Nguyen, "SDAD," arXiv:2608.20341, mayo de 2026.
[7] "LLM-as-a-Judge Is Not an Oracle," arXiv:2609.02246, sep. de 2026.
[8] V. Reddy et al., "Reason Less, Verify More," arXiv:2607.07405, jul. de 2026.
[9] Sheridan Tech, "Design Validation vs Verification," mar. de 2026.
[10] Augment Code, "Coordinator-Implementor-Verifier Pattern," jun. de 2026.
[11] OPAL-RT, "Guide to HIL Testing," sep. de 2026.
[12] IEEE/ISO/IEC 29148:2018, "Requirements engineering."
[13] V. Lavecchia, "Sandwich testing strategies," 2024.
[14] B. Trinnes, "Test Architecture Patterns," GitHub, abr. de 2026.
[15] "Spec-Driven Development," arXiv:2602.00180, feb. de 2026.
[16] ECSS-Q-ST-10-09C, "Nonconformance control system," European Cooperation for Space Standardization. — Define la Request for Deviation (RFD) como una «desviación planificada» de los requisitos.
[17] MIL-HDBK-61A, "Configuration Management Guidance," U.S. DoD, 2001. — Procesamiento de desviaciones: se solicita cuando un producto no puede cumplir requisitos técnicos; incluye análisis de impacto y opciones de compromiso.
[18] NASA NPR 7150.2, "NASA Software Engineering Requirements." — Evaluación de desviación/exención: justificación técnica, evaluación de riesgos, impacto en la seguridad y alternativas propuestas.
[19] M. Torres, R. Beltrán, "Agile V: Iterative Planning within Stage-Gate Verified Development," arXiv:2611.xxxxx, nov. de 2026. — Capa de planificación ágil por módulo con mini-ciclos-V dentro de un ciclo de vida en modelo-V.
[20] GitHub, "Spec-Kit: Specification-Driven Module Planning," github.com/spec-kit, 2026. — Herramientas para descomposición de backlog dirigida por especificación y generación de planes.
[21] OpenSpec Consortium, "OpenSpec: Living Ground Truth with Delta Tracing," openspec.dev, 2026. — Modelo de trazabilidad delta de requisitos: entradas ADDED/MODIFIED/REMOVED contra un Ground Truth canónico.
