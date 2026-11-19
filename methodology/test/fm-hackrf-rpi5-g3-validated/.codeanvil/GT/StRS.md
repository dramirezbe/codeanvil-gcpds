# Nodo de monitoreo continuo y calibrado de radiodifusión FM

## Stakeholder Requirements Specification (StRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.4 — *Stakeholder requirements specification.*
>
> **Template version:** 4.0.0  
> **Creation date:** 2026-11-12  
> **Last modified:** 2026-11-12  
> **Document status:** `APPROVED`

---

## Document Metadata

| Field | Value |
|---|---|
| **Document ID** | `STRS-FM-001` |
| **Project** | Nodo de monitoreo continuo y calibrado de radiodifusión FM |
| **Organization** | Agencia Nacional del Espectro (ANE), Colombia |
| **Version** | `1.0.0` |
| **Classification** | `INTERNAL` |
| **Author(s)** | _No suministrado por el Build Package._ |
| **Reviewer(s)** | _No suministrado por el Build Package._ |
| **Approver(s)** | Persona responsable del proyecto (aprobación declarada el 2026-11-12). |

### Companion Documents

| Document ID | Title | Relationship |
|---|---|---|
| `SYRS-FM-001` | System Requirements Specification | Par G0 derivado de este documento |
| `S1-FM-001` | S1 design document | Salida de diseño (S1) |

### Change Log

| Version | Date | Author | Change Description |
|---|---|---|---|
| 1.0.0 | 2026-11-12 | _No suministrado por el Build Package._ | Normalización S0 del Build Package |

---

## 1. Introduction

### 1.1 Purpose

Este documento especifica los requisitos de las partes interesadas para un nodo de monitoreo continuo y calibrado de radiodifusión FM. Está dirigido al equipo de desarrollo, a la persona responsable del proyecto y a las partes que revisan la aceptación del nodo. Es la vista de sistema de todos los subsistemas, bandas y tipos de medición, y deriva al SyRS la especificación técnica por medida.

### 1.2 Scope

El sistema es un nodo físico instalado en un sitio, con antena, receptor HackRF One y placa Raspberry Pi 5, que mide cada 6 segundos la potencia calibrada de los 199 canales del Plan Técnico FM (100 kHz de separación), decide ocupación, compara con la lista de estaciones asignadas, calcula ciclo de trabajo, levanta cinco alertas, guarda un informe de tamizaje y ofrece cuatro vistas web de solo lectura.

El sistema no determina cumplimiento o incumplimiento regulatorio, no identifica estaciones por demodulación o RDS, no mide dirección ni geolocaliza, no usa GPS ni referencia de frecuencia externa, no usa control automático de ganancia, no pide inicio de sesión ni escribe a través de la web, no emite alertas desde la potencia recibida sin límite configurado, no avisa fuera del nodo, no funciona sin alimentación, no se calibra con un conmutador interno, no incluye filtro de banda, LNA, atenuador o protección externa, no cifra el tráfico web y no compara más de dos sitios.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|---|---|
| StRS | Stakeholder Requirements Specification (este documento). |
| SyRS | System Requirements Specification, documento companion. |
| Nodo | Equipo físico instalado en un sitio: antena, receptor HackRF One, placa Raspberry Pi 5, fuente, gabinete y cables. |
| Barrido | Ciclo completo de adquisición y evaluación de los 199 canales del Plan Técnico FM. |
| Canal | Canal FM de 100 kHz de separación, del canal 1 (88,1 MHz) al canal 199 (107,9 MHz). |
| Occupied | Estado de un canal cuando el exceso sobre el piso de ruido alcanza el umbral de ocupación. |
| Free | Estado de un canal que cumple todas las condiciones de liberación; nunca se convierte en Free por omisión. |
| Uncertain | Estado de un canal cuando el sistema no puede afirmar Occupied ni Free. |
| Valor liberado | Valor de potencia o estado que el módulo productor declara válido; si no, se guarda con la razón de retención y no se dibuja. |
| Evidencia de tamizaje | Resultado identificado como evidencia para revisión, no como determinación de cumplimiento regulatorio. |
| Referencia de asignación | Archivo propio del sitio con la lista de estaciones asignadas por canal. |
| AGC | Control automático de ganancia; prohibido por R-22. |
| NTP | Protocolo de hora por red usado para el sello UTC. |

### 1.4 References

| Ref ID | Document | Version / Date |
|---|---|---|
| `REF-001` | ESPECIFICACION-DESARROLLO.md — Nodo de monitoreo continuo y calibrado de radiodifusión FM | Aprobada 2026-11-12 |
| `REF-002` | anexo-A-parametros.md — Parámetros de la solución | 1.0.0 — 2026-11-12 |
| `REF-003` | anexo-B-formatos-de-datos.md — Formatos de datos entre módulos | 1.0.0 — 2026-11-12 |
| `REF-004` | anexo-C-procedimientos.md — Procedimientos y algoritmos paso a paso | 1.0.0 — 2026-11-12 |
| `REF-005` | anexo-D-errores.md — Catálogo de errores | 1.0.0 — 2026-11-12 |
| `REF-006` | anexo-E-pruebas.md — Plan de pruebas | 1.0.0 — 2026-11-12 |

### 1.5 Document Overview

La sección 1 presenta el propósito, el alcance, las definiciones, las referencias y el inventario de hardware. La sección 2 describe el sistema, sus funciones, usuarios, restricciones, supuestos, diagrama de bloques y topología de buses. La sección 3 contiene los bloques de requisitos de las partes interesadas y las restricciones de la plataforma. La sección 4 enumera las interfaces externas. La sección 5 resume los requisitos no funcionales. La sección 6 traza cada bloque a su fuente y a su prueba.

### 1.6 Hardware Inventory

| Component ID | Component Name | Role in System | Manufacturer | Part Number |
|---|---|---|---|---|
| `HW-001` | Receptor SDR HackRF One | Recibe la banda FM y entrega muestras I/Q | Great Scott Gadgets | HackRF One |
| `HW-002` | Placa de cómputo Raspberry Pi 5, 8 GB | Ejecuta adquisición, procesamiento, informes y web | Raspberry Pi Ltd | Raspberry Pi 5, 8 GB |
| `HW-003` | Refrigeración activa Raspberry Pi Active Cooler | Disipa el calor de la placa | Raspberry Pi Ltd | Active Cooler (Pi 5) |
| `HW-004` | microSD industrial Kingston 64 GB | Almacena sistema, configuración, informes y registros persistentes | Kingston | SDCIT2/64GBSP |
| `HW-005` | Antena dipolo coaxial HK033 | Captura la banda FM de 88,1 a 107,9 MHz | Rohde & Schwarz | HK033 |
| `HW-006` | Cable de antena LMR-195 de 3 m | Conecta la antena al receptor | CommScope / Andrew (Amphenol) | 7855829 |
| `HW-007` | Cable USB 2.0 tipo A a Micro-B de 0,5 m | Conecta el receptor a la placa | Lindy | 36650 |
| `HW-008` | Fuente de alimentación de escritorio 65 W | Alimenta la placa por USB-C con Power Delivery | Inventus Power (ELPAC) | XWA0650PDA-USB-C (5A version) |
| `HW-009` | Gabinete de policarbonato ARCA-304021 | Contiene y protege el nodo | Fibox | ARCA-304021 |
| `HW-010` | Fuente de referencia trazable de calibración | Establece la corrección de amplitud en el sitio | No suministrado por el Build Package | No suministrado por el Build Package |
| `HW-011` | Referencia independiente de verificación | Verifica la corrección con trazabilidad independiente | No suministrado por el Build Package | No suministrado por el Build Package |

---

## 2. Overall System Description

### 2.1 Product Perspective

El sistema es un nodo nuevo, no un reemplazo ni una extensión de un sistema existente. Se instalan varios nodos en distintos sitios; lo único que cambia entre ellos son los archivos de configuración (R-52). La medición y el software corren en la placa; el nodo se conecta a la red del sitio por Ethernet y publica las vistas web en el puerto 8080. La calibración se establece en el sitio contra una fuente trazable y se verifica con una referencia independiente.

### 2.2 Product Functions

- Medición de los 199 canales por barrido, con potencia en dBm e incertidumbre.
- Decisión de ocupación con tres estados: Occupied, Free y Uncertain.
- Comparación con la lista de estaciones asignadas del sitio.
- Cálculo del ciclo de trabajo por canal e intervalo.
- Calibración de amplitud, verificación periódica y control de validez de la calibración.
- Cinco alertas: canal en silencio, ocupación inesperada, sensor fuera de línea, calibración no demostrada y deriva del piso de ruido.
- Informe de tamizaje guardado en disco a medida que se produce.
- Cuatro vistas web de solo lectura y descarga de informes, sin inicio de sesión.
- Supervisión de procesos, reinicio automático y watchdog de hardware.
- Configuración por archivos, sin reescribir código para agregar un nodo.

### 2.3 User Characteristics

| User Type | Description | Technical Level |
|---|---|---|
| Personal de la ANE | Revisa mediciones, informes, alertas y evidencia de tamizaje. | `TECHNICAL` |
| Operador del nodo | Instala, configura, calibra, verifica y ejecuta los procedimientos locales. | `EXPERT` |
| Persona de la red del sitio | Consulta las vistas web y descarga informes, sin inicio de sesión. | `BASIC` |

### 2.4 Constraints

El diseño no puede superar los límites físicos de la plataforma: sintonía de 1 MHz a 6 000 MHz, muestreo máximo de 20 Msps, resolución de 8 bits, tolerancia del cristal de ±20 ppm, ganancia máxima del LNA de 40 dB y del amplificador RF de 14 dB, ancho de banda de 256 kHz por emisión FM estéreo, variación lenta de ±10 dB en un día y temperatura ambiente de hasta 40 °C. El nodo usa el HackRF One (R-54), no incluye GPS (R-71), no usa AGC (R-22), no incluye filtro, LNA, atenuador o protección externa, y su costo no excede 3 200 USD sin referencias de calibración ni licencias (R-53).

### 2.5 Assumptions and Dependencies

- La alimentación eléctrica es continua y está garantizada por el usuario; los cortes están fuera del alcance y R-48 los supone ausentes.
- Se dispone de una fuente trazable y de una referencia independiente de 0,5 dB (k = 2); su disponibilidad efectiva debe confirmarse y su costo queda fuera de los 3 200 USD.
- El sitio dispone de una lista publicada de estaciones FM para la validación de campo de 72 h.
- La red del sitio ofrece servicio NTP y acceso HTTP al puerto 8080.
- La tarjeta microSD, el gabinete, el mástil, el adaptador de mástil, los prensaestopas y el cable de red se eligen y prueban en la puesta en marcha.
- Las pruebas de calificación de hardware de la sección 9.2 del Build Package no se han ejecutado; el documento no contiene resultados de medición.

### 2.6 Block Diagram

```text
  AIRE (88–108 MHz)
        │
   ┌────▼─────┐   cable 3 m    ┌────────────────┐   USB 2.0    ┌───────────────────────────────────────┐
   │  Antena  ├───────────────►│  HackRF One    ├─────────────►│  Raspberry Pi 5 (8 GB)                │
   │ dipolo   │  N → SMA       │  muestras I/Q  │  20 MB/s     │                                       │
   │ vertical │                │  8 bits 10 Msps│              │  adquisición → estimador espectral →  │
   └──────────┘                └────────────────┘              │  calibración → detector de ocupación →│
                                                                │  comparador → registros →             │
   Entradas laterales:                                         │  historial (RAM) · informe (disco) ·  │
   · hora por red (NTP)                                        │  alertas · servicio web               │
   · configuración del sitio                                   └───────────────────────┬───────────────┘
   · lista de estaciones asignadas                                                      │ HTTP :8080
   · referencias externas de calibración (a mano)                                       ▼
                                                                          navegador en la red del sitio
```

El inventario de hardware con sus identificadores está en §1.6. Fuente: REF-001 §4.1.

### 2.7 Bus and Interface Topology

| From | To | Bus/Protocol | Data Rate (theoretical) | Data Rate (sustained) |
|---|---|---|---|---|
| `HW-005` | `HW-006` | RF, 50 Ω, N a SMA | 88,1–107,9 MHz | No aplica |
| `HW-006` | `HW-001` | RF, 50 Ω, SMA | 88,1–107,9 MHz | No aplica |
| `HW-001` | `HW-002` | USB 2.0 | 480 Mbit/s | 20 MB/s (160 Mbit/s) |
| `HW-002` | `HW-004` | microSD UHS-I | No suministrado | ≥30 MB/s (U3) |
| `HW-003` | `HW-002` | Conector de ventilador, 5 V | No aplica | No aplica |
| `HW-008` | `HW-002` | USB-C con Power Delivery, 5 V / 5 A | 25 W | 25 W |
| `HW-002` | Red del sitio | Gigabit Ethernet, HTTP :8080 | 1 Gbit/s | No suministrado (descargas web: 20 MB/s) |
| Fuente NTP | `HW-002` | NTP sobre Ethernet | No aplica | No aplica |
| `HW-010` / `HW-011` | `HW-001` | RF, conexión manual al puerto de antena | 88–108 MHz | No aplica |

El ventilador y NTP no son buses de datos: el primero es una conexión de alimentación de 5 V y el segundo un protocolo de consulta cada 64 a 1024 s (Anexo A). La tarjeta es UHS-I U3, que garantiza al menos 30 MB/s de escritura sostenida; el límite de 20 MB/s es el de las descargas web (REF-001 §4.5 y Anexo A `download_rate_limit`), no la capacidad sostenida de la interfaz Ethernet.

---

## 3. Specific Requirements

### 3.1 Normative Obligations

_No se suministra ninguna obligación normativa con fuente y cláusula concretas. La única referencia normativa citada es IEC 60529 para el significado de IP65 (R-65 y P-095); su cláusula no se suministra._

### 3.2 Stakeholder Requirements

#### 3.2.1 Cobertura, barrido y tiempo

---

**`STK-REQ-001` — Período de barrido completo de la banda**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL completar un barrido de toda la banda (todos los canales del Plan Técnico FM) con un período de barrido de 10 s como máximo.

**Acceptance Criteria:**

1. [ ] Intervalo máximo entre inicios de barridos consecutivos ≤ 10 s en una corrida declarada (se excluye el intervalo interrumpido por un reinicio registrado del watchdog).

**Notes:**  
Prueba de aceptación: P-001 (REF-006, Anexo E). Texto fuente: REF-001 §3.1.

---

**`STK-REQ-002` — Cobertura de los 199 canales del Plan Técnico FM**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
En cada barrido, el sistema SHALL evaluar los 199 canales del Plan Técnico FM: del canal 1 (88,1 MHz) al canal 199 (107,9 MHz), separados 100 kHz.

**Acceptance Criteria:**

1. [ ] 100 % de los barridos tienen un registro para cada canal.

**Notes:**  
Prueba de aceptación: P-002 (REF-006, Anexo E). Texto fuente: REF-001 §3.1.

---

**`STK-REQ-069` — Integración de potencia sobre 256 kHz**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL integrar la potencia recibida de cada canal sobre un ancho de banda de 256 kHz.

**Acceptance Criteria:**

1. [ ] Ancho de integración ≥ 256 kHz.

**Notes:**  
Prueba de aceptación: P-068 (REF-006, Anexo E). Texto fuente: REF-001 §3.1.

---

**`STK-REQ-028` — Sello UTC con resolución de 1 ms o mejor**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Cada barrido SHALL sellarse en UTC con una resolución de 1 ms o mejor.

**Acceptance Criteria:**

1. [ ] Resolución de la marca de tiempo ≤ 1 ms.

**Notes:**  
Prueba de aceptación: P-030 (REF-006, Anexo E). Texto fuente: REF-001 §3.1.

---

**`STK-REQ-057` — Adquisición sin desbordamientos ni tramas perdidas**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL sostener la adquisición a la tasa de muestreo desplegada sin desbordamientos ni tramas perdidas.

**Acceptance Criteria:**

1. [ ] 0 eventos de pérdida de muestras o sobrecarga de búfer en una corrida continua a la tasa desplegada (banco de 60 s y corrida de campo).

**Notes:**  
Prueba de aceptación: P-036 (REF-006, Anexo E). Texto fuente: REF-001 §3.1.

---

**`STK-REQ-022` — Prohibición de control automático de ganancia**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL NOT usar control automático de ganancia.

**Acceptance Criteria:**

1. [ ] 0 adquisiciones con AGC activado.

**Notes:**  
Prueba de aceptación: P-024 (REF-006, Anexo E). Texto fuente: REF-001 §3.1.

---

**`STK-REQ-023` — Registro de ganancias y estado del amplificador**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Con cada adquisición, el sistema SHALL registrar las ganancias individuales y el estado del amplificador.

**Acceptance Criteria:**

1. [ ] 100 % de las adquisiciones con sus ganancias y estado de amplificador.

**Notes:**  
Prueba de aceptación: P-025 (REF-006, Anexo E). Texto fuente: REF-001 §3.1.

---

**`STK-REQ-050` — Error de asignación a canal de 5 kHz a 100 MHz**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Por defecto, el sistema SHALL asignar el contenido espectral a la frecuencia de canal con un error de a lo sumo 5 kHz a 100 MHz.

**Acceptance Criteria:**

1. [ ] Error de asignación más incertidumbre expandida de la fuente ≤ 5 kHz con tonos CW en el centro de ≥ 5 canales (incluidos el más bajo y el más alto, con al menos un canal por captura).

**Notes:**  
Prueba de aceptación: P-056 (REF-006, Anexo E). Texto fuente: REF-001 §3.1.

#### 3.2.2 Detección de ocupación

---

**`STK-REQ-003` — Estado de ocupación por canal y barrido**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Para cada canal y cada barrido, el sistema SHALL liberar un estado de ocupación: Occupied (ocupado), Free (libre) o Uncertain (incierto).

**Acceptance Criteria:**

1. [ ] 100 % de los registros de canal-barrido llevan uno de los tres estados.

**Notes:**  
Prueba de aceptación: P-003 (REF-006, Anexo E). Texto fuente: REF-001 §3.2.

---

**`STK-REQ-004` — Detección de canales ocupados con SNR de al menos 0 dB**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si la relación señal/ruido de un canal ocupado es de al menos 0 dB, el sistema SHALL reportar el canal como ocupado con probabilidad de detección ≥ 95 %.

**Acceptance Criteria:**

1. [ ] Probabilidad de detección ≥ 95 % sobre observaciones de canales ocupados con SNR ≥ 0 dB (conjunto de aceptación: ≥ 20 observaciones de ≥ 10 canales distintos, ningún canal con más del 20 % de las observaciones, referencia independiente).

**Notes:**  
Prueba de aceptación: P-004 (REF-006, Anexo E). Texto fuente: REF-001 §3.2.

---

**`STK-REQ-005` — Falsa alarma máxima de 5 % en canales vacantes**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL reportar un canal vacante como ocupado con probabilidad de falsa alarma ≤ 5 %.

**Acceptance Criteria:**

1. [ ] Probabilidad de falsa alarma ≤ 5 % sobre observaciones de canales vacantes confirmados por una referencia independiente.

**Notes:**  
Prueba de aceptación: P-005 (REF-006, Anexo E). Texto fuente: REF-001 §3.2.

---

**`STK-REQ-006` — Condiciones de liberación del estado Free**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL liberar un canal como Free solo si una señal con la potencia mínima recibida declarada quedaría al menos 10 dB por encima del nivel de ruido verificado y por encima del umbral de detección activo.

**Acceptance Criteria:**

1. [ ] Margen mínimo entre la potencia mínima declarada y el ruido verificado en los registros liberados como Free ≥ 10 dB; un solo registro que viole la regla hace fallar la prueba.

**Notes:**  
Prueba de aceptación: P-006 (REF-006, Anexo E). Texto fuente: REF-001 §3.2.

---

**`STK-REQ-007` — Estado Uncertain cuando no puede liberarse Free**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si un canal no puede liberarse como Free, o su validez de ocupación no es válida, el sistema SHALL liberar el estado Uncertain.

**Acceptance Criteria:**

1. [ ] 0 % de los registros sin validez o sin condiciones de liberación se liberan como Free.

**Notes:**  
Prueba de aceptación: P-007 (REF-006, Anexo E). Texto fuente: REF-001 §3.2.

---

**`STK-REQ-008` — Ciclo de trabajo y fracción Uncertain por intervalo**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Para cada canal y cada intervalo de reporte declarado, el sistema SHALL informar el ciclo de trabajo junto con la fracción de barridos Uncertain.

**Acceptance Criteria:**

1. [ ] 100 % de los canales con ciclo de trabajo y fracción Uncertain por cada intervalo.

**Notes:**  
Prueba de aceptación: P-008 (REF-006, Anexo E). Texto fuente: REF-001 §3.2.

---

**`STK-REQ-059` — Condiciones de liberación visibles en el informe**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Además de lo exigido por R-62, el informe SHALL mostrar, para cada canal liberado como Free, que no hubo detección, que la validez de ocupación era válida, que el margen de liberación fue de al menos 10 dB y que el umbral de detección no superó la potencia mínima declarada.

**Acceptance Criteria:**

1. [ ] 100 % de los registros Free muestran esas condiciones de liberación.

**Notes:**  
Prueba de aceptación: P-009 (REF-006, Anexo E). Texto fuente: REF-001 §3.2.

---

**`STK-REQ-030` — Entradas guardadas para reverificar estados Free**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El informe SHALL guardar las entradas de cada estado de ocupación liberado, de modo que todo estado Free del informe pueda volver a verificarse.

**Acceptance Criteria:**

1. [ ] 100 % de los estados Free pueden re-verificarse con las entradas guardadas.

**Notes:**  
Prueba de aceptación: P-032 (REF-006, Anexo E). Texto fuente: REF-001 §3.2.

#### 3.2.3 Potencia calibrada e incertidumbre

---

**`STK-REQ-009` — Potencia de canal calibrada en dBm**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Para cada canal y barrido, el sistema SHALL registrar una potencia de canal recibida calibrada, en dBm, en el plano de referencia del receptor (el conector de antena del SDR).

**Acceptance Criteria:**

1. [ ] 100 % de los registros con potencia calibrada en dBm.

**Notes:**  
Prueba de aceptación: P-010 (REF-006, Anexo E). Texto fuente: REF-001 §3.3.

---

**`STK-REQ-010` — Error absoluto de potencia calibrada de 3 dB**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
La potencia de canal calibrada SHALL tener un error absoluto de a lo sumo 3 dB después de la calibración.

**Acceptance Criteria:**

1. [ ] Diferencia absoluta con una referencia independiente calificada ≤ 3 dB, en ≥ 10 canales distintos, restando de cada diferencia su incertidumbre expandida; un canal no concluyente impide la aceptación.

**Notes:**  
Prueba de aceptación: P-011 (REF-006, Anexo E). Texto fuente: REF-001 §3.3.

---

**`STK-REQ-011` — Incertidumbre y base por valor de potencia**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Con cada valor de potencia, el sistema SHALL informar su incertidumbre como semiancho en dB, junto con la base de esa incertidumbre.

**Acceptance Criteria:**

1. [ ] 100 % de los valores con incertidumbre y su base.

**Notes:**  
Prueba de aceptación: P-012 (REF-006, Anexo E). Texto fuente: REF-001 §3.3.

---

**`STK-REQ-012` — Valor, incertidumbre, límite y comparación por salida**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL entregar cada salida requerida con su valor, su incertidumbre, el límite aplicable (o el registro de que no existe) y la comparación con ese límite.

**Acceptance Criteria:**

1. [ ] 100 % de las salidas con valor, incertidumbre, límite o ausencia registrada, y comparación.

**Notes:**  
Prueba de aceptación: P-013 (REF-006, Anexo E). Texto fuente: REF-001 §3.3.

---

**`STK-REQ-013` — Ausencia de límite registrada sin comparación dentro**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si no aplica ningún límite a la potencia de canal recibida, el sistema SHALL registrar la ausencia del límite y SHALL NOT presentar la comparación como «dentro del límite».

**Acceptance Criteria:**

1. [ ] 0 % de los registros sin límite presentan la comparación como dentro del límite.

**Notes:**  
Prueba de aceptación: P-014 (REF-006, Anexo E). Texto fuente: REF-001 §3.3.

---

**`STK-REQ-014` — Comparación indeterminada no convertida en dentro o fuera**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL NOT convertir un estado de comparación indeterminado, no configurado o no evaluable en «dentro» o «fuera» del límite mediante promedios, redondeos, un intervalo pequeño o un valor por defecto.

**Acceptance Criteria:**

1. [ ] 0 conversiones de ese tipo en los informes.

**Notes:**  
Prueba de aceptación: P-015 (REF-006, Anexo E). Texto fuente: REF-001 §3.3.

---

**`STK-REQ-029` — Procedencia de la potencia calibrada**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Con cada valor de potencia calibrada, el informe SHALL guardar además el estado de ganancias usado y el identificador del registro de calibración aplicable, para poder reconstruir su procedencia.

**Acceptance Criteria:**

1. [ ] 100 % de los registros de potencia calibrada nombran ganancias y registro de calibración.

**Notes:**  
Prueba de aceptación: P-031 (REF-006, Anexo E). Texto fuente: REF-001 §3.3.

#### 3.2.4 Calibración y verificación

---

**`STK-REQ-017` — Corrección de amplitud trazable a patrón**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Toda medición de potencia SHALL llevar una corrección de amplitud establecida contra una fuente de referencia cuyo nivel es trazable a un patrón nacional o internacional.

**Acceptance Criteria:**

1. [ ] 100 % de las mediciones con corrección establecida contra una referencia trazable; el registro de calibración nombra la fuente, su fecha de calibración y su incertidumbre.

**Notes:**  
Prueba de aceptación: P-018 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

---

**`STK-REQ-018` — Datos de identificación de cada calibración**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Por cada calibración, el sistema SHALL conservar su identificador, la configuración de hardware y firmware aplicable, el plano de referencia, la fuente de referencia y su estado de validez.

**Acceptance Criteria:**

1. [ ] 100 % de las calibraciones con esos cinco datos en su registro.

**Notes:**  
Prueba de aceptación: P-019 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

---

**`STK-REQ-019` — Verificación periódica dentro del intervalo declarado**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL permitir verificar periódicamente la corrección de amplitud, a intervalos que no superen un intervalo declarado.

**Acceptance Criteria:**

1. [ ] Tiempo máximo entre dos verificaciones aprobadas ≤ intervalo declarado (mínimo 4 días; ver la nota sobre el máximo en la sección 9).

**Notes:**  
Prueba de aceptación: P-020 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

---

**`STK-REQ-020` — Referencia de verificación independiente**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
La referencia usada para verificar la exactitud absoluta de potencia SHALL ser un instrumento distinto, y con trazabilidad independiente, de la usada para establecer la corrección.

**Acceptance Criteria:**

1. [ ] 0 verificaciones en las que la referencia coincide con la que estableció la corrección.

**Notes:**  
Prueba de aceptación: P-021 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

---

**`STK-REQ-060` — Referencia e incertidumbre en el registro de validación**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El registro de validación SHALL identificar la referencia independiente usada y su incertidumbre.

**Acceptance Criteria:**

1. [ ] 100 % de los registros de validación con esos datos.

**Notes:**  
Prueba de aceptación: P-022 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

---

**`STK-REQ-021` — Retención de potencia sin calibración demostrable**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si la corrección de amplitud activa ya no puede demostrarse, el sistema SHALL marcar los registros afectados y SHALL NOT liberar sus valores de potencia.

**Acceptance Criteria:**

1. [ ] 0 valores de potencia liberados mientras la corrección no puede demostrarse (prueba por inyección de fallos: verificación vencida, corrección derivada).

**Notes:**  
Prueba de aceptación: P-023 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

---

**`STK-REQ-058` — Configuración de medición igual a la calibrada**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
La configuración de medición SHALL ser la misma con la que se estableció la calibración activa.

**Acceptance Criteria:**

1. [ ] 0 barridos ejecutados con una configuración distinta de la del registro de calibración activo.

**Notes:**  
Prueba de aceptación: P-037 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

---

**`STK-REQ-055` — Caracterización de rango dinámico y compresión**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL caracterizar el rango dinámico utilizable y el comportamiento de compresión del receptor para la configuración de ganancias desplegada.

**Acceptance Criteria:**

1. [ ] Al menos una configuración desplegada con rango dinámico y compresión documentados.

**Notes:**  
Prueba de aceptación: P-034 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

---

**`STK-REQ-056` — Registro de referencia de frecuencia y corrección**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Por cada dispositivo, el sistema SHALL registrar el estado de su referencia de frecuencia y la corrección necesaria para conservar la correspondencia entre espectro y frecuencia de canal.

**Acceptance Criteria:**

1. [ ] 100 % de los dispositivos con estado de referencia de frecuencia registrado.

**Notes:**  
Prueba de aceptación: P-035 (REF-006, Anexo E). Texto fuente: REF-001 §3.4.

#### 3.2.5 Calidad de la captura y salud del nodo

---

**`STK-REQ-024` — Marcado de capturas saturadas**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si alguna muestra cruda retenida de una captura está a plena escala del convertidor, el sistema SHALL marcar los registros afectados como saturados y SHALL NOT liberar su potencia.

**Acceptance Criteria:**

1. [ ] 0 valores de potencia liberados desde una captura con una muestra a plena escala.

**Notes:**  
Prueba de aceptación: P-026 (REF-006, Anexo E). Texto fuente: REF-001 §3.5.

---

**`STK-REQ-025` — Marcado de barridos con desbordamiento o trama perdida**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si ocurre un desbordamiento de recepción o una pérdida de trama durante un barrido, el sistema SHALL marcar los registros de ese barrido, SHALL NOT liberar su potencia y SHALL liberar su ocupación como Uncertain.

**Acceptance Criteria:**

1. [ ] 0 potencias liberadas y 0 estados distintos de Uncertain en barridos con desbordamiento o trama perdida.

**Notes:**  
Prueba de aceptación: P-027 (REF-006, Anexo E). Texto fuente: REF-001 §3.5.

---

**`STK-REQ-026` — Conteo de tramas perdidas**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL detectar y contar las tramas perdidas del flujo de adquisición.

**Acceptance Criteria:**

1. [ ] 100 % de las pérdidas inyectadas se cuentan como tramas perdidas.

**Notes:**  
Prueba de aceptación: P-028 (REF-006, Anexo E). Texto fuente: REF-001 §3.5.

---

**`STK-REQ-027` — Registro de salud por barrido**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Por cada barrido, el sistema SHALL emitir un registro de salud con el conteo de desbordamientos, el conteo de tramas perdidas y el número de registros publicados.

**Acceptance Criteria:**

1. [ ] 100 % de los barridos con registro de salud que contiene los tres conteos.

**Notes:**  
Prueba de aceptación: P-029 (REF-006, Anexo E). Texto fuente: REF-001 §3.5.

#### 3.2.6 Comparación con las estaciones asignadas

---

**`STK-REQ-015` — Comparación con la referencia de asignación del sitio**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
En cada barrido, el sistema SHALL comparar el estado de ocupación de cada canal con la referencia de asignación de estaciones del sitio y SHALL registrar el resultado como consistent, unassigned-occupied, assigned-free o indeterminate.

**Acceptance Criteria:**

1. [ ] 100 % de los registros de canal-barrido con resultado de comparación.

**Notes:**  
Prueba de aceptación: P-016 (REF-006, Anexo E). Texto fuente: REF-001 §3.6.

---

**`STK-REQ-016` — Referencia de asignación propia del sitio**

| Field | Value |
|---|---|
| **Type** | `INTERFACE` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL aceptar una referencia de asignación de estaciones propia del sitio y SHALL usarla para la comparación de ocupación.

**Acceptance Criteria:**

1. [ ] Al menos una referencia del sitio cargada y usada por la comparación.

**Notes:**  
Prueba de aceptación: P-017 (REF-006, Anexo E). Texto fuente: REF-001 §3.6.

#### 3.2.7 Alertas

---

**`STK-REQ-034` — Alerta de canal en silencio**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si la comparación de una estación que antes estaba por encima de 90 % de ciclo de trabajo resulta assigned-free durante un número declarado de horas de emisión, el sistema SHALL emitir una alerta de canal en silencio (channel-silent).

**Acceptance Criteria:**

1. [ ] Ninguna alerta omitida cuando se cumple la condición de silencio (las horas se declaran en la configuración, entre 0,1 y 720 h).

**Notes:**  
Prueba de aceptación: P-041 (REF-006, Anexo E). Texto fuente: REF-001 §3.7.

---

**`STK-REQ-035` — Observaciones Uncertain no cuentan para silencio**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Las observaciones Uncertain SHALL NOT contar para el silencio de un canal.

**Acceptance Criteria:**

1. [ ] 0 observaciones Uncertain contadas como silencio.

**Notes:**  
Prueba de aceptación: P-042 (REF-006, Anexo E). Texto fuente: REF-001 §3.7.

---

**`STK-REQ-036` — Alerta de ocupación inesperada**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si un canal FM monitoreado está ocupado y no está asignado en la referencia, el sistema SHALL emitir una alerta de ocupación inesperada.

**Acceptance Criteria:**

1. [ ] Ninguna alerta omitida para un canal ocupado sin asignación.

**Notes:**  
Prueba de aceptación: P-043 (REF-006, Anexo E). Texto fuente: REF-001 §3.7.

---

**`STK-REQ-037` — Alerta de sensor fuera de línea**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si no se recibe ningún registro de salud durante tres períodos de barrido, el sistema SHALL emitir una alerta de sensor fuera de línea.

**Acceptance Criteria:**

1. [ ] Ninguna alerta omitida cuando pasan tres períodos sin registro de salud.

**Notes:**  
Prueba de aceptación: P-044 (REF-006, Anexo E). Texto fuente: REF-001 §3.7.

---

**`STK-REQ-038` — Alerta de calibración no demostrada**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si la calibración no puede demostrarse en ninguna captura de un barrido, o el intervalo de verificación vence dentro de un margen declarado, el sistema SHALL emitir una alerta de calibración no demostrada.

**Acceptance Criteria:**

1. [ ] Ninguna alerta omitida cuando se cumple la condición.

**Notes:**  
Prueba de aceptación: P-045 (REF-006, Anexo E). Texto fuente: REF-001 §3.7.

---

**`STK-REQ-039` — Alerta de deriva del piso de ruido**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Si la mediana del piso de ruido se desplaza más de 6 dB en 24 h, el sistema SHALL emitir una alerta de deriva del piso de ruido.

**Acceptance Criteria:**

1. [ ] Ninguna alerta omitida cuando la mediana se desplaza más de 6 dB en 24 h.

**Notes:**  
Prueba de aceptación: P-046 (REF-006, Anexo E). Texto fuente: REF-001 §3.7.

---

**`STK-REQ-040` — Prohibición de alertas desde potencia sin límite**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Mientras no haya un límite configurado para la potencia de canal recibida, el sistema SHALL NOT emitir ninguna alerta a partir de esa potencia.

**Acceptance Criteria:**

1. [ ] 0 alertas generadas desde la potencia sin límite configurado.

**Notes:**  
Prueba de aceptación: P-047 (REF-006, Anexo E). Texto fuente: REF-001 §3.7.

#### 3.2.8 Vistas web, acceso y evidencia

---

**`STK-REQ-041` — Vista web de potencia por canal y tiempo**

| Field | Value |
|---|---|
| **Type** | `INTERFACE` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL ofrecer una vista web de la potencia por canal (frecuencia) y tiempo.

**Acceptance Criteria:**

1. [ ] Vista disponible.

**Notes:**  
Prueba de aceptación: P-048 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-042` — Vista web del espectro actual con marcadores**

| Field | Value |
|---|---|
| **Type** | `INTERFACE` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL ofrecer una vista web del espectro de potencia actual con marcadores de canal.

**Acceptance Criteria:**

1. [ ] Vista disponible.

**Notes:**  
Prueba de aceptación: P-049 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-043` — Vista web de estaciones seleccionadas en 24 h**

| Field | Value |
|---|---|
| **Type** | `INTERFACE` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL ofrecer una vista web de la potencia y el ciclo de trabajo de estaciones seleccionadas durante las últimas 24 h.

**Acceptance Criteria:**

1. [ ] Vista disponible.

**Notes:**  
Prueba de aceptación: P-050 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-044` — Vista web del estado del nodo**

| Field | Value |
|---|---|
| **Type** | `INTERFACE` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL ofrecer una vista web del estado del nodo que muestre: estado en línea, antigüedad del último barrido, deriva del piso de ruido, conteo de desbordamientos y conteo de tramas perdidas.

**Acceptance Criteria:**

1. [ ] La vista muestra las cinco magnitudes.

**Notes:**  
Prueba de aceptación: P-051 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-045` — Solo salidas liberadas en las vistas**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
En las vistas de potencia y ocupación, el sistema SHALL dibujar solo salidas liberadas; para un valor de potencia retenido pero no liberado, SHALL mostrar los estados de validez y banderas del canal.

**Acceptance Criteria:**

1. [ ] 0 valores no liberados dibujados.

**Notes:**  
Prueba de aceptación: P-052 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-046` — Presentación de alertas en la vista web**

| Field | Value |
|---|---|
| **Type** | `INTERFACE` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL presentar las alertas emitidas al personal en la vista web.

**Acceptance Criteria:**

1. [ ] La vista muestra las alertas emitidas.

**Notes:**  
Prueba de aceptación: P-053 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-047` — Evidencia técnica disponible al personal**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL entregar al personal mediciones calibradas, registros de monitoreo, indicadores de calidad, información de incertidumbre, alertas y otra evidencia técnica para su revisión.

**Acceptance Criteria:**

1. [ ] 100 % de esos elementos disponibles al personal.

**Notes:**  
Prueba de aceptación: P-040 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-067` — Acceso sin inicio de sesión ni roles**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL dar a todo usuario acceso a la vista web y a los informes guardados, y SHALL NOT restringir ese acceso por rol ni por ningún otro medio.

**Acceptance Criteria:**

1. [ ] 0 usuarios o roles sin acceso.

**Notes:**  
Prueba de aceptación: P-067 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-032` — Identificación de evidencia de tamizaje**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Todo registro, informe y tablero SHALL identificarse como evidencia de tamizaje y no como determinación de cumplimiento.

**Acceptance Criteria:**

1. [ ] 100 % de registros, informes y tableros con esa identificación.

**Notes:**  
Prueba de aceptación: P-038 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

---

**`STK-REQ-033` — Prohibición de dictamen regulatorio**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL NOT establecer por sí mismo cumplimiento ni incumplimiento regulatorio en ninguna alerta, registro o informe.

**Acceptance Criteria:**

1. [ ] 0 alertas, registros o informes que declaren cumplimiento o incumplimiento.

**Notes:**  
Prueba de aceptación: P-039 (REF-006, Anexo E). Texto fuente: REF-001 §3.8.

#### 3.2.9 Informes, almacenamiento y configuración

---

**`STK-REQ-062` — Informe de tamizaje guardado en disco**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL guardar en disco un informe de tamizaje con los resultados, los registros de fecha y hora, el tiempo de ejecución y la información de ubicación, para que el usuario lo revise.

**Acceptance Criteria:**

1. [ ] Los cuatro elementos presentes en el informe guardado.

**Notes:**  
Prueba de aceptación: P-062 (REF-006, Anexo E). Texto fuente: REF-001 §3.9.

---

**`STK-REQ-070` — Ubicación del nodo en todo informe**

| Field | Value |
|---|---|
| **Type** | `INTERFACE` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL permitir al usuario ingresar la ubicación del nodo: país, ciudad y nombre del lugar o dirección.

**Acceptance Criteria:**

1. [ ] 100 % de los informes con la ubicación ingresada.

**Notes:**  
Prueba de aceptación: P-070 (REF-006, Anexo E). Texto fuente: REF-001 §3.9.

---

**`STK-REQ-073` — Guardado del informe a medida que se produce**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
Mientras una corrida de tamizaje está en curso, el sistema SHALL guardar sus resultados en disco a medida que se producen, para que quede registro de lo hecho si el nodo se detiene.

**Acceptance Criteria:**

1. [ ] 100 % de los resultados producidos antes de una interrupción están en el informe (prueba cortando la alimentación en plena corrida).

**Notes:**  
Prueba de aceptación: P-072 (REF-006, Anexo E). Texto fuente: REF-001 §3.9.

---

**`STK-REQ-074` — Duración configurable de la corrida con mínimo de 10 min**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL permitir al usuario configurar el tiempo durante el cual se toman registros, con un mínimo de 10 minutos.

**Acceptance Criteria:**

1. [ ] El tiempo mínimo aceptado es 10 min; un valor menor se rechaza.

**Notes:**  
Prueba de aceptación: P-073 (REF-006, Anexo E). Texto fuente: REF-001 §3.9.

---

**`STK-REQ-031` — Registros de monitoreo solo en memoria**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL NOT guardar en disco los registros de monitoreo en tiempo real; solo SHALL guardar el informe de tamizaje.

**Acceptance Criteria:**

1. [ ] 0 registros de monitoreo en disco fuera del informe.

**Notes:**  
Prueba de aceptación: P-033 (REF-006, Anexo E). Texto fuente: REF-001 §3.9.

---

**`STK-REQ-075` — Límite configurable del error de asignación hasta 20 kHz**

| Field | Value |
|---|---|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL permitir al usuario ajustar el límite del error de asignación a canal, hasta un máximo de 20 kHz.

**Acceptance Criteria:**

1. [ ] El límite máximo aceptado es 20 kHz; uno mayor se rechaza.

**Notes:**  
Prueba de aceptación: P-074 (REF-006, Anexo E). Texto fuente: REF-001 §3.9.

---

**`STK-REQ-052` — Alta de otro nodo solo por configuración**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El software SHALL permitir agregar y configurar otro nodo sin reescribir código.

**Acceptance Criteria:**

1. [ ] 0 líneas de código reescritas para agregar y configurar otro nodo.

**Notes:**  
Prueba de aceptación: P-058 (REF-006, Anexo E). Texto fuente: REF-001 §3.9.

#### 3.2.10 Entorno físico, energía y costo

---

**`STK-REQ-054` — Receptor HackRF One**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El nodo SHALL usar el HackRF One como receptor.

**Acceptance Criteria:**

1. [ ] 0 nodos con otro receptor.

**Notes:**  
Prueba de aceptación: P-060 (REF-006, Anexo E). Texto fuente: REF-001 §3.10.

---

**`STK-REQ-053` — Costo máximo de 3 200 USD por nodo**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El costo de un nodo de monitoreo completo SHALL NOT exceder 3 200 dólares, sin contar las referencias de calibración ni las licencias.

**Acceptance Criteria:**

1. [ ] Costo ≤ 3 200 USD con precios a la fecha de la revisión de aceptación.

**Notes:**  
Prueba de aceptación: P-059 (REF-006, Anexo E). Texto fuente: REF-001 §3.10.

---

**`STK-REQ-063` — Operación con red eléctrica de 120 V**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El nodo SHALL operar conectado a la red eléctrica de 120 V.

**Acceptance Criteria:**

1. [ ] 100 % de las corridas de aceptación alimentadas con 120 V.

**Notes:**  
Prueba de aceptación: P-063 (REF-006, Anexo E). Texto fuente: REF-001 §3.10.

---

**`STK-REQ-072` — Operación con red eléctrica de 60 Hz**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El nodo SHALL operar conectado a la red eléctrica de 60 Hz.

**Acceptance Criteria:**

1. [ ] 100 % de las corridas de aceptación con red de 60 Hz.

**Notes:**  
Prueba de aceptación: P-069 (REF-006, Anexo E). Texto fuente: REF-001 §3.10.

---

**`STK-REQ-064` — Operación en interiores y exteriores**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `DEMONSTRATION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El nodo SHALL operar tanto en interiores como en exteriores.

**Acceptance Criteria:**

1. [ ] Cumple sus requisitos en los 2 tipos de instalación (una corrida de campo en cada uno).

**Notes:**  
Prueba de aceptación: P-064 (REF-006, Anexo E). Texto fuente: REF-001 §3.10.

---

**`STK-REQ-065` — Encerrado contra polvo y lluvia**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | IEC 60529 |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El nodo SHALL estar encerrado de modo que el polvo y la lluvia no entren.

**Acceptance Criteria:**

1. [ ] 0 ingresos de polvo o agua bajo la exposición definida (protección IP65).

**Notes:**  
Prueba de aceptación: P-065 (REF-006, Anexo E). Texto fuente: REF-001 §3.10.

---

**`STK-REQ-066` — Operación hasta 40 °C ambiente**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El nodo SHALL operar a temperaturas ambiente de hasta 40 °C.

**Acceptance Criteria:**

1. [ ] Cumple todos sus requisitos a 40 °C ambiente.

**Notes:**  
Prueba de aceptación: P-066 (REF-006, Anexo E). Texto fuente: REF-001 §3.10.

---

**`STK-REQ-071` — Sin receptor GPS**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `INSPECTION` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El nodo SHALL NOT incluir receptor GPS.

**Acceptance Criteria:**

1. [ ] 0 receptores GPS.

**Notes:**  
Prueba de aceptación: P-071 (REF-006, Anexo E). Texto fuente: REF-001 §3.10.

#### 3.2.11 Disponibilidad, reproducibilidad y validación de campo

---

**`STK-REQ-048` — Disponibilidad de 95 % en 30 días**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL estar disponible al menos el 95 % de una corrida continua de 30 días.

**Acceptance Criteria:**

1. [ ] Disponibilidad ≥ 95 % en 30 días (la corrida de campo de 72 h no verifica este requisito; la alimentación eléctrica es continua, garantizada por el usuario).

**Notes:**  
Prueba de aceptación: P-054 (REF-006, Anexo E). Texto fuente: REF-001 §3.11.

---

**`STK-REQ-049` — Definición de disponibilidad por registro completo**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `ANALYSIS` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
El sistema SHALL contarse como disponible en un instante cuando existe un registro completo de barrido dentro de los tres períodos de barrido anteriores.

**Acceptance Criteria:**

1. [ ] ≥ 95 % de los puntos de tiempo cuentan como disponibles, con la definición del requisito, en una ventana de 30 días.

**Notes:**  
Prueba de aceptación: P-055 (REF-006, Anexo E). Texto fuente: REF-001 §3.11.

---

**`STK-REQ-051` — Reproducibilidad entre dos sitios**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
La medición, el tamizaje y los informes de evidencia SHALL ser reproducibles al repetirlos en otro sitio.

**Acceptance Criteria:**

1. [ ] Concordancia entre el primer sitio y otro sitio según la regla aprobada (≥ 10 de 12 puntos, sección 5.17).

**Notes:**  
Prueba de aceptación: P-057 (REF-006, Anexo E). Texto fuente: REF-001 §3.11.

---

**`STK-REQ-061` — Validación de campo continua de 72 h**

| Field | Value |
|---|---|
| **Type** | `NON_FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `PENDING` |
| **Dependencies** | — |
| **Phase** | — |

**Description:**  
La capacidad de monitoreo SHALL validarse en campo con una corrida continua de 72 h en un sitio con una lista publicada de estaciones FM.

**Acceptance Criteria:**

1. [ ] Duración de la corrida continua ≥ 72 h; registro de una referencia independiente durante ≥ 6 h de ella.

**Notes:**  
Prueba de aceptación: P-061 (REF-006, Anexo E). Texto fuente: REF-001 §3.11.

### 3.3 Platform Constraints

_Restricciones paramétricas de los componentes COTS del inventario de §1.6._

#### 3.3.1 Receptor SDR

---

**`HWC-SDR-001` — Rango de sintonía del receptor (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Rango de sintonía del receptor |
| **Limit type** | `RANGE` |
| **Value min** | 1 MHz |
| **Value max** | 6 000 MHz |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §3.12 y §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Límite físico del HackRF One.

---

**`HWC-SDR-002` — Tasa de muestreo del receptor (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Tasa de muestreo del receptor |
| **Limit type** | `RANGE` |
| **Value min** | 2 Msps |
| **Value max** | 20 Msps |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §3.12 y §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
La adquisición desplegada usa 10 Msps.

---

**`HWC-SDR-003` — Resolución del convertidor (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Resolución del convertidor |
| **Limit type** | `FIXED` |
| **Value** | 8 bits |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §3.12 y §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-SDR-004` — Nivel máximo de entrada en el puerto de antena (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Nivel máximo de entrada en el puerto de antena |
| **Limit type** | `MAX` |
| **Value** | −5 dBm |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Por encima se daña el receptor; se mide en la puesta en marcha con P-088.

---

**`HWC-SDR-005` — Tolerancia del cristal de referencia de serie (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Tolerancia del cristal de referencia de serie |
| **Limit type** | `FIXED` |
| **Value** | ±20 ppm |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §3.12 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-SDR-006` — Ganancia máxima del LNA (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Ganancia máxima del LNA |
| **Limit type** | `MAX` |
| **Value** | 40 dB |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §3.12 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-SDR-007` — Ganancia máxima del amplificador RF (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Ganancia máxima del amplificador RF |
| **Limit type** | `MAX` |
| **Value** | 14 dB |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §3.12 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-SDR-008` — Conector de antena e impedancia (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Conector de antena e impedancia |
| **Limit type** | `FIXED` |
| **Value** | SMA hembra 50 Ω |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-SDR-009` — Ancho de banda utilizable por captura (HW-001)**

| Field | Value |
|---|---|
| **Component** | `HW-001` |
| **Parameter** | Ancho de banda utilizable por captura |
| **Limit type** | `FIXED` |
| **Value** | 8 MHz (80 % de 10 MHz) |
| **Source** | `DERIVED` |
| **Source ref** | REF-001 §5.3 |
| **Impact** | `SOFT` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Derivado del muestreo de 10 Msps.

#### 3.3.2 Placa de cómputo

---

**`HWC-CPU-001` — Núcleos y frecuencia del procesador (HW-002)**

| Field | Value |
|---|---|
| **Component** | `HW-002` |
| **Parameter** | Núcleos y frecuencia del procesador |
| **Limit type** | `FIXED` |
| **Value** | 4 núcleos Arm Cortex-A76 a 2,4 GHz |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-CPU-002` — Memoria RAM (HW-002)**

| Field | Value |
|---|---|
| **Component** | `HW-002` |
| **Parameter** | Memoria RAM |
| **Limit type** | `FIXED` |
| **Value** | 8 GB |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-CPU-003` — Interfaz de red (HW-002)**

| Field | Value |
|---|---|
| **Component** | `HW-002` |
| **Parameter** | Interfaz de red |
| **Limit type** | `FIXED` |
| **Value** | Gigabit Ethernet |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-CPU-004` — Puertos USB (HW-002)**

| Field | Value |
|---|---|
| **Component** | `HW-002` |
| **Parameter** | Puertos USB |
| **Limit type** | `FIXED` |
| **Value** | 2 USB 3.0 y 2 USB 2.0 |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-CPU-005` — Temperatura de operación de la placa (HW-002)**

| Field | Value |
|---|---|
| **Component** | `HW-002` |
| **Parameter** | Temperatura de operación de la placa |
| **Limit type** | `RANGE` |
| **Value min** | 0 °C |
| **Value max** | 70 °C |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `SOFT` |
| **Status** | `PRELIMINARY` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
El Build Package no aclara si los 70 °C son del ambiente o de la placa.

#### 3.3.3 Refrigeración

---

**`HWC-COOL-001` — Alimentación del ventilador (HW-003)**

| Field | Value |
|---|---|
| **Component** | `HW-003` |
| **Parameter** | Alimentación del ventilador |
| **Limit type** | `FIXED` |
| **Value** | 5 V |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-COOL-002` — Flujo máximo de aire (HW-003)**

| Field | Value |
|---|---|
| **Component** | `HW-003` |
| **Parameter** | Flujo máximo de aire |
| **Limit type** | `FIXED` |
| **Value** | 1,09 CFM |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `INFORMATIONAL` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

#### 3.3.4 Almacenamiento

---

**`HWC-STO-001` — Capacidad de almacenamiento (HW-004)**

| Field | Value |
|---|---|
| **Component** | `HW-004` |
| **Parameter** | Capacidad de almacenamiento |
| **Limit type** | `FIXED` |
| **Value** | 64 GB |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-STO-002` — Clase de velocidad (HW-004)**

| Field | Value |
|---|---|
| **Component** | `HW-004` |
| **Parameter** | Clase de velocidad |
| **Limit type** | `FIXED` |
| **Value** | clase 10 / UHS-I U3 |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `SOFT` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-STO-003` — Temperatura de operación de la tarjeta (HW-004)**

| Field | Value |
|---|---|
| **Component** | `HW-004` |
| **Parameter** | Temperatura de operación de la tarjeta |
| **Limit type** | `RANGE` |
| **Value min** | −40 °C |
| **Value max** | 85 °C |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-STO-004` — Resistencia de escritura (HW-004)**

| Field | Value |
|---|---|
| **Component** | `HW-004` |
| **Parameter** | Resistencia de escritura |
| **Limit type** | `FIXED` |
| **Value** | ~1 920 TBW estimados para 64 GB |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `INFORMATIONAL` |
| **Status** | `PRELIMINARY` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
El valor de 64 GB es una estimación a partir de los 3 840 TBW de 128 GB.

#### 3.3.5 Antena

---

**`HWC-ANT-001` — Rango de frecuencia de la antena (HW-005)**

| Field | Value |
|---|---|
| **Component** | `HW-005` |
| **Parameter** | Rango de frecuencia de la antena |
| **Limit type** | `RANGE` |
| **Value min** | 80 MHz |
| **Value max** | 2 GHz |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-ANT-002` — Conector e impedancia de la antena (HW-005)**

| Field | Value |
|---|---|
| **Component** | `HW-005` |
| **Parameter** | Conector e impedancia de la antena |
| **Limit type** | `FIXED` |
| **Value** | N hembra, 50 Ω |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-ANT-003` — Ganancia de la antena (HW-005)**

| Field | Value |
|---|---|
| **Component** | `HW-005` |
| **Parameter** | Ganancia de la antena |
| **Limit type** | `FIXED` |
| **Value** | 2 dBi típ. |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `INFORMATIONAL` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-ANT-004` — ROE de la antena (HW-005)**

| Field | Value |
|---|---|
| **Component** | `HW-005` |
| **Parameter** | ROE de la antena |
| **Limit type** | `MAX` |
| **Value** | 2 típ. |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `SOFT` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

#### 3.3.6 Cable de antena

---

**`HWC-CBL-001` — Longitud del cable de antena (HW-006)**

| Field | Value |
|---|---|
| **Component** | `HW-006` |
| **Parameter** | Longitud del cable de antena |
| **Limit type** | `FIXED` |
| **Value** | 3 m |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-CBL-002` — Pérdida máxima del cable (HW-006)**

| Field | Value |
|---|---|
| **Component** | `HW-006` |
| **Parameter** | Pérdida máxima del cable |
| **Limit type** | `MAX` |
| **Value** | 1,8 dB (0–3 GHz) |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `SOFT` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
La pérdida real a 88–108 MHz se estima en 0,43 dB.

---

**`HWC-CBL-003` — Conectores del cable (HW-006)**

| Field | Value |
|---|---|
| **Component** | `HW-006` |
| **Parameter** | Conectores del cable |
| **Limit type** | `FIXED` |
| **Value** | N macho a SMA macho |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

#### 3.3.7 Cable USB

---

**`HWC-USB-001` — Estándar del cable USB (HW-007)**

| Field | Value |
|---|---|
| **Component** | `HW-007` |
| **Parameter** | Estándar del cable USB |
| **Limit type** | `FIXED` |
| **Value** | USB 2.0 tipo A a Micro-B |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-USB-002` — Longitud del cable USB (HW-007)**

| Field | Value |
|---|---|
| **Component** | `HW-007` |
| **Parameter** | Longitud del cable USB |
| **Limit type** | `FIXED` |
| **Value** | 0,5 m |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

#### 3.3.8 Fuente de alimentación

---

**`HWC-PWR-001` — Tensión de entrada de la fuente (HW-008)**

| Field | Value |
|---|---|
| **Component** | `HW-008` |
| **Parameter** | Tensión de entrada de la fuente |
| **Limit type** | `RANGE` |
| **Value min** | 85 V CA |
| **Value max** | 264 V CA |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-PWR-002` — Frecuencia de entrada de la fuente (HW-008)**

| Field | Value |
|---|---|
| **Component** | `HW-008` |
| **Parameter** | Frecuencia de entrada de la fuente |
| **Limit type** | `RANGE` |
| **Value min** | 47 Hz |
| **Value max** | 63 Hz |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-PWR-003` — Salida de la fuente (HW-008)**

| Field | Value |
|---|---|
| **Component** | `HW-008` |
| **Parameter** | Salida de la fuente |
| **Limit type** | `FIXED` |
| **Value** | 5 V a 5 A (25 W) por USB-C |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-PWR-004` — Eficiencia típica de la fuente (HW-008)**

| Field | Value |
|---|---|
| **Component** | `HW-008` |
| **Parameter** | Eficiencia típica de la fuente |
| **Limit type** | `FIXED` |
| **Value** | 81 % típ. |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `INFORMATIONAL` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-PWR-005` — Temperatura de operación de la fuente (HW-008)**

| Field | Value |
|---|---|
| **Component** | `HW-008` |
| **Parameter** | Temperatura de operación de la fuente |
| **Limit type** | `RANGE` |
| **Value min** | 0 °C |
| **Value max** | 40 °C |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `SOFT` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-PWR-006` — Grado de protección de la fuente (HW-008)**

| Field | Value |
|---|---|
| **Component** | `HW-008` |
| **Parameter** | Grado de protección de la fuente |
| **Limit type** | `FIXED` |
| **Value** | IP22 |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `INFORMATIONAL` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

#### 3.3.9 Gabinete y entorno

---

**`HWC-ENV-001` — Dimensiones del gabinete (HW-009)**

| Field | Value |
|---|---|
| **Component** | `HW-009` |
| **Parameter** | Dimensiones del gabinete |
| **Limit type** | `FIXED` |
| **Value** | 300 × 400 × 210 mm |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-ENV-002` — Grado de protección del gabinete (HW-009)**

| Field | Value |
|---|---|
| **Component** | `HW-009` |
| **Parameter** | Grado de protección del gabinete |
| **Limit type** | `FIXED` |
| **Value** | IP66 / IK10 |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | IEC 60529 |
| **Clause** | — |
| **Compliance** | `PENDING` |

**Notes:**  
El gabinete es IP66; el requisito del nodo es IP65 (R-65).

---

**`HWC-ENV-003` — Temperatura de operación del gabinete (HW-009)**

| Field | Value |
|---|---|
| **Component** | `HW-009` |
| **Parameter** | Temperatura de operación del gabinete |
| **Limit type** | `RANGE` |
| **Value min** | −40 °C |
| **Value max** | 80 °C continuo |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §4.2 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-ENV-004` — Temperatura ambiente en el sitio (HW-009)**

| Field | Value |
|---|---|
| **Component** | `HW-009` |
| **Parameter** | Temperatura ambiente en el sitio |
| **Limit type** | `MAX` |
| **Value** | 40 °C |
| **Source** | `DATASHEET` |
| **Source ref** | REF-001 §3.12 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-ENV-005` — Temperatura máxima del aire interno (HW-009)**

| Field | Value |
|---|---|
| **Component** | `HW-009` |
| **Parameter** | Temperatura máxima del aire interno |
| **Limit type** | `MAX` |
| **Value** | 60 °C a 40 °C ambiente |
| **Source** | `DERIVED` |
| **Source ref** | REF-001 §4.5 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
La placa admite hasta 70 °C; el aumento permitido es 20 °C.

#### 3.3.10 Referencias de calibración

---

**`HWC-CAL-001` — Incertidumbre expandida de la fuente de calibración (HW-010)**

| Field | Value |
|---|---|
| **Component** | `HW-010` |
| **Parameter** | Incertidumbre expandida de la fuente de calibración |
| **Limit type** | `MAX` |
| **Value** | 0,5 dB (k = 2) |
| **Source** | `DERIVED` |
| **Source ref** | REF-001 §5.5 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-CAL-002` — Incertidumbre de frecuencia de la fuente de calibración (HW-010)**

| Field | Value |
|---|---|
| **Component** | `HW-010` |
| **Parameter** | Incertidumbre de frecuencia de la fuente de calibración |
| **Limit type** | `MAX` |
| **Value** | 1 ppm |
| **Source** | `DERIVED` |
| **Source ref** | REF-001 §5.5 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-CAL-003` — Independencia entre referencia de calibración y de verificación (HW-010, HW-011)**

| Field | Value |
|---|---|
| **Component** | `HW-010, HW-011` |
| **Parameter** | Independencia entre referencia de calibración y de verificación |
| **Limit type** | `FIXED` |
| **Value** | instrumento distinto con trazabilidad independiente |
| **Source** | `DERIVED` |
| **Source ref** | REF-001 §5.5 y §5.6 |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

## 4. External Interface Requirements

### 4.1 User Interfaces

La interfaz de usuario es una aplicación web de solo lectura en el puerto 8080, con cuatro vistas: potencia por canal y tiempo, espectro actual con marcadores de canal, potencia y ciclo de trabajo de hasta 10 estaciones en 24 h, y estado del nodo. Incluye la lista y descarga de informes guardados. No pide inicio de sesión ni restringe por rol. Toda página lleva la etiqueta «Screening evidence only: not a compliance determination».

### 4.2 Hardware Interfaces

| Interface | Specification |
|---|---|
| Antena–cable | N hembra a N macho, 50 Ω, 80 MHz–2 GHz. |
| Cable–receptor | SMA macho a SMA hembra, 50 Ω, 88,1–107,9 MHz. |
| Receptor–placa | USB 2.0 tipo A a Micro-B, 0,5 m, 20 MB/s sostenidos. |
| Placa–red | Gigabit Ethernet, HTTP en el puerto 8080. |
| Alimentación | USB-C con Power Delivery, 5 V / 5 A, 25 W, fuente externa al gabinete. |
| Refrigeración | Conector de ventilador de la placa, 5 V. |
| Almacenamiento | microSD industrial de 64 GB, clase 10 / UHS-I U3. |
| Calibración | Conexión manual de la fuente de referencia al puerto de antena; no hay conmutador interno. |

### 4.3 Software Interfaces

- Mensajes JSON UTF-8 por sockets Unix locales de flujo, con longitud de 4 bytes big-endian y hasta 16 MB; 33 formatos del Anexo B.
- Cliente NTP estándar para la hora UTC; no hay GPS ni reloj con batería.
- Programa de línea de comandos local para los procedimientos del operador; no es accesible desde la web.
- Sistema operativo Linux Arm de 64 bits con systemd, cgroups, sistema de archivos temporal en memoria, cliente NTP, watchdog de hardware, sin swap ni volcados de memoria.

### 4.4 Communication Interfaces

| Interface | Protocol | Direction | Data |
|---|---|---|---|
| Web del sitio | HTTP GET o HEAD, puerto 8080 | Nodo a usuario | Vistas, JSON y archivos de informe |
| Hora | NTP | Nodo a servidor de hora | Estado de hora y sincronización |
| Unidades internas | Sockets Unix de flujo | Entre procesos | JSON UTF-8 con longitud de 4 bytes |
| Almacenamiento | Sistema de archivos | Nodo a microSD | Configuración, informes, calibración y validación |

---

## 5. Non-Functional Requirements

### 5.1 Performance

El barrido se inicia cada 6 s y el intervalo entre inicios no supera 10 s (R-01). La cadena de procesamiento suma 4,98 s de los 6 s, con holgura de 1,02 s. La detección con SNR ≥ 0 dB es ≥ 95 % y la falsa alarma ≤ 5 % (R-04, R-05). El error absoluto de potencia calibrada es ≤ 3 dB (R-10). La verificación periódica usa 12 puntos y tolerancia de 1,0 dB (R-19). La adquisición sostiene 10 Msps sin pérdidas (R-57).

### 5.2 Security

La web es de solo lectura y no pide inicio de sesión ni aplica roles (R-67). No hay rutas que escriban en el nodo. El tráfico web no se cifra en esta versión. Todo registro, informe y tablero se identifica como evidencia de tamizaje y no afirma cumplimiento o incumplimiento (R-32, R-33).

### 5.3 Reliability / Availability

La disponibilidad es ≥ 95 % en una corrida continua de 30 días (R-48). Un instante cuenta como disponible si existe un registro completo de barrido dentro de los tres períodos anteriores (R-49). El supervisor reinicia procesos con escalera de 5 a 60 s, declara bucle a los cinco reinicios en 600 s y reinicia el nodo a los 1 800 s en bucle, máximo 3 veces por 24 h. El watchdog de hardware es de 15 s. Un proceso vuelve a barridos completos 72 s después de la última medición y 300 s tras un reinicio completo.

### 5.4 Maintainability

La configuración del sitio son archivos que se leen al arrancar; agregar un nodo no reescribe código (R-52). Los registros de calibración y validación son archivos persistentes que nunca se borran. El informe se escribe a medida que se produce y se recupera como interrumpido en el siguiente arranque (R-73). La bitácora del supervisor se conserva 35 días o 50 MB.

### 5.5 Portability

El software corre en Linux Arm de 64 bits con systemd y cgroups; la referencia es Raspberry Pi OS Lite de 64 bits. El lenguaje, el marco web y la biblioteca de gráficos son libres. La misma aplicación y los mismos formatos se usan en todos los nodos; solo cambian los archivos de configuración.

---

## 6. Traceability

| Block ID | Business Objective | Standard Ref | Compliance | Test Case | Component |
|---|---|---|---|---|---|
| `STK-REQ-001` | — | — | `PENDING` | P-001 | — |
| `STK-REQ-002` | — | — | `PENDING` | P-002 | — |
| `STK-REQ-069` | — | — | `PENDING` | P-068 | — |
| `STK-REQ-028` | — | — | `PENDING` | P-030 | — |
| `STK-REQ-057` | — | — | `PENDING` | P-036 | — |
| `STK-REQ-022` | — | — | `PENDING` | P-024 | — |
| `STK-REQ-023` | — | — | `PENDING` | P-025 | — |
| `STK-REQ-050` | — | — | `PENDING` | P-056 | — |
| `STK-REQ-003` | — | — | `PENDING` | P-003 | — |
| `STK-REQ-004` | — | — | `PENDING` | P-004 | — |
| `STK-REQ-005` | — | — | `PENDING` | P-005 | — |
| `STK-REQ-006` | — | — | `PENDING` | P-006 | — |
| `STK-REQ-007` | — | — | `PENDING` | P-007 | — |
| `STK-REQ-008` | — | — | `PENDING` | P-008 | — |
| `STK-REQ-059` | — | — | `PENDING` | P-009 | — |
| `STK-REQ-030` | — | — | `PENDING` | P-032 | — |
| `STK-REQ-009` | — | — | `PENDING` | P-010 | — |
| `STK-REQ-010` | — | — | `PENDING` | P-011 | — |
| `STK-REQ-011` | — | — | `PENDING` | P-012 | — |
| `STK-REQ-012` | — | — | `PENDING` | P-013 | — |
| `STK-REQ-013` | — | — | `PENDING` | P-014 | — |
| `STK-REQ-014` | — | — | `PENDING` | P-015 | — |
| `STK-REQ-029` | — | — | `PENDING` | P-031 | — |
| `STK-REQ-017` | — | — | `PENDING` | P-018 | — |
| `STK-REQ-018` | — | — | `PENDING` | P-019 | — |
| `STK-REQ-019` | — | — | `PENDING` | P-020 | — |
| `STK-REQ-020` | — | — | `PENDING` | P-021 | — |
| `STK-REQ-060` | — | — | `PENDING` | P-022 | — |
| `STK-REQ-021` | — | — | `PENDING` | P-023 | — |
| `STK-REQ-058` | — | — | `PENDING` | P-037 | — |
| `STK-REQ-055` | — | — | `PENDING` | P-034 | — |
| `STK-REQ-056` | — | — | `PENDING` | P-035 | — |
| `STK-REQ-024` | — | — | `PENDING` | P-026 | — |
| `STK-REQ-025` | — | — | `PENDING` | P-027 | — |
| `STK-REQ-026` | — | — | `PENDING` | P-028 | — |
| `STK-REQ-027` | — | — | `PENDING` | P-029 | — |
| `STK-REQ-015` | — | — | `PENDING` | P-016 | — |
| `STK-REQ-016` | — | — | `PENDING` | P-017 | — |
| `STK-REQ-034` | — | — | `PENDING` | P-041 | — |
| `STK-REQ-035` | — | — | `PENDING` | P-042 | — |
| `STK-REQ-036` | — | — | `PENDING` | P-043 | — |
| `STK-REQ-037` | — | — | `PENDING` | P-044 | — |
| `STK-REQ-038` | — | — | `PENDING` | P-045 | — |
| `STK-REQ-039` | — | — | `PENDING` | P-046 | — |
| `STK-REQ-040` | — | — | `PENDING` | P-047 | — |
| `STK-REQ-041` | — | — | `PENDING` | P-048 | — |
| `STK-REQ-042` | — | — | `PENDING` | P-049 | — |
| `STK-REQ-043` | — | — | `PENDING` | P-050 | — |
| `STK-REQ-044` | — | — | `PENDING` | P-051 | — |
| `STK-REQ-045` | — | — | `PENDING` | P-052 | — |
| `STK-REQ-046` | — | — | `PENDING` | P-053 | — |
| `STK-REQ-047` | — | — | `PENDING` | P-040 | — |
| `STK-REQ-067` | — | — | `PENDING` | P-067 | — |
| `STK-REQ-032` | — | — | `PENDING` | P-038 | — |
| `STK-REQ-033` | — | — | `PENDING` | P-039 | — |
| `STK-REQ-062` | — | — | `PENDING` | P-062 | — |
| `STK-REQ-070` | — | — | `PENDING` | P-070 | — |
| `STK-REQ-073` | — | — | `PENDING` | P-072 | — |
| `STK-REQ-074` | — | — | `PENDING` | P-073 | — |
| `STK-REQ-031` | — | — | `PENDING` | P-033 | — |
| `STK-REQ-075` | — | — | `PENDING` | P-074 | — |
| `STK-REQ-052` | — | — | `PENDING` | P-058 | — |
| `STK-REQ-054` | — | — | `PENDING` | P-060 | — |
| `STK-REQ-053` | — | — | `PENDING` | P-059 | — |
| `STK-REQ-063` | — | — | `PENDING` | P-063 | — |
| `STK-REQ-072` | — | — | `PENDING` | P-069 | — |
| `STK-REQ-064` | — | — | `PENDING` | P-064 | — |
| `STK-REQ-065` | — | IEC 60529 | `PENDING` | P-065 | — |
| `STK-REQ-066` | — | — | `PENDING` | P-066 | — |
| `STK-REQ-071` | — | — | `PENDING` | P-071 | — |
| `STK-REQ-048` | — | — | `PENDING` | P-054 | — |
| `STK-REQ-049` | — | — | `PENDING` | P-055 | — |
| `STK-REQ-051` | — | — | `PENDING` | P-057 | — |
| `STK-REQ-061` | — | — | `PENDING` | P-061 | — |
| `HWC-SDR-001` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-SDR-002` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-SDR-003` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-SDR-004` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-SDR-005` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-SDR-006` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-SDR-007` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-SDR-008` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-SDR-009` | — | — | `NOT_APPLICABLE` | — | `HW-001` |
| `HWC-CPU-001` | — | — | `NOT_APPLICABLE` | — | `HW-002` |
| `HWC-CPU-002` | — | — | `NOT_APPLICABLE` | — | `HW-002` |
| `HWC-CPU-003` | — | — | `NOT_APPLICABLE` | — | `HW-002` |
| `HWC-CPU-004` | — | — | `NOT_APPLICABLE` | — | `HW-002` |
| `HWC-CPU-005` | — | — | `NOT_APPLICABLE` | — | `HW-002` |
| `HWC-COOL-001` | — | — | `NOT_APPLICABLE` | — | `HW-003` |
| `HWC-COOL-002` | — | — | `NOT_APPLICABLE` | — | `HW-003` |
| `HWC-STO-001` | — | — | `NOT_APPLICABLE` | — | `HW-004` |
| `HWC-STO-002` | — | — | `NOT_APPLICABLE` | — | `HW-004` |
| `HWC-STO-003` | — | — | `NOT_APPLICABLE` | — | `HW-004` |
| `HWC-STO-004` | — | — | `NOT_APPLICABLE` | — | `HW-004` |
| `HWC-ANT-001` | — | — | `NOT_APPLICABLE` | — | `HW-005` |
| `HWC-ANT-002` | — | — | `NOT_APPLICABLE` | — | `HW-005` |
| `HWC-ANT-003` | — | — | `NOT_APPLICABLE` | — | `HW-005` |
| `HWC-ANT-004` | — | — | `NOT_APPLICABLE` | — | `HW-005` |
| `HWC-CBL-001` | — | — | `NOT_APPLICABLE` | — | `HW-006` |
| `HWC-CBL-002` | — | — | `NOT_APPLICABLE` | — | `HW-006` |
| `HWC-CBL-003` | — | — | `NOT_APPLICABLE` | — | `HW-006` |
| `HWC-USB-001` | — | — | `NOT_APPLICABLE` | — | `HW-007` |
| `HWC-USB-002` | — | — | `NOT_APPLICABLE` | — | `HW-007` |
| `HWC-PWR-001` | — | — | `NOT_APPLICABLE` | — | `HW-008` |
| `HWC-PWR-002` | — | — | `NOT_APPLICABLE` | — | `HW-008` |
| `HWC-PWR-003` | — | — | `NOT_APPLICABLE` | — | `HW-008` |
| `HWC-PWR-004` | — | — | `NOT_APPLICABLE` | — | `HW-008` |
| `HWC-PWR-005` | — | — | `NOT_APPLICABLE` | — | `HW-008` |
| `HWC-PWR-006` | — | — | `NOT_APPLICABLE` | — | `HW-008` |
| `HWC-ENV-001` | — | — | `NOT_APPLICABLE` | — | `HW-009` |
| `HWC-ENV-002` | — | IEC 60529 | `NOT_APPLICABLE` | — | `HW-009` |
| `HWC-ENV-003` | — | — | `NOT_APPLICABLE` | — | `HW-009` |
| `HWC-ENV-004` | — | — | `NOT_APPLICABLE` | — | `HW-009` |
| `HWC-ENV-005` | — | — | `NOT_APPLICABLE` | — | `HW-009` |
| `HWC-CAL-001` | — | — | `NOT_APPLICABLE` | — | `HW-010` |
| `HWC-CAL-002` | — | — | `NOT_APPLICABLE` | — | `HW-010` |
| `HWC-CAL-003` | — | — | `NOT_APPLICABLE` | — | `HW-010, HW-011` |

> Cada bloque de §3 aparece en esta tabla. Las pruebas de aceptación se describen en REF-006; las pruebas de calificación de hardware no se han ejecutado.
