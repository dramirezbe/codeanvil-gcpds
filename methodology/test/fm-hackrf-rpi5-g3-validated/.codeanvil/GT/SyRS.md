# Nodo de monitoreo continuo y calibrado de radiodifusión FM

## System Requirements Specification (SyRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.5 — *System requirements specification.*
>
> **Template version:** 4.0.0  
> **Creation date:** 2026-11-12  
> **Last modified:** 2026-11-12  
> **Document status:** `APPROVED`

---

## Document Metadata

| Field | Value |
|---|---|
| **Document ID** | `SYRS-FM-001` |
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
| `STRS-FM-001` | Stakeholder Requirements Specification | Contrato upstream (par G0) |
| `S1-FM-001` | S1 design document | Salida de diseño (S1) |

### Change Log

| Version | Date | Author | Change Description |
|---|---|---|---|
| 1.0.0 | 2026-11-12 | _No suministrado por el Build Package._ | Normalización S0 del Build Package |

---

## 1. Introduction

### 1.1 Purpose

Este documento especifica los requisitos técnicos del sistema para el nodo de monitoreo continuo y calibrado de radiodifusión FM, derivados del StRS. Está dirigido al equipo de desarrollo y a la verificación de aceptación. Cada bloque SYS traza a uno o más bloques del StRS y declara el método que realiza la medición o el procesamiento.

### 1.2 Scope

El SyRS cubre la adquisición de la banda FM, el estimador espectral, la calibración y verificación de amplitud, el detector de ocupación, la comparación con asignaciones, los registros, el historial, los informes, las alertas, el servicio web, la supervisión, los presupuestos de recursos, la reproducibilidad entre sitios, la seguridad de acceso, la comunicación entre unidades, los formatos de datos y el entorno físico. No cubre la determinación de cumplimiento regulatorio ni las funciones declaradas fuera de alcance en el StRS.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|---|---|
| SyRS | System Requirements Specification (este documento). |
| StRS | Stakeholder Requirements Specification, documento upstream. |
| SYS | Bloque de requisito técnico de este documento. |
| K(f) | Desplazamiento de amplitud en dB que convierte dBFS en dBm en el conector de antena. |
| dBFS | Potencia relativa a la escala completa del convertidor. |
| e_k | Exceso de potencia del canal k sobre su referencia de ruido, en dB. |
| N_k | Referencia de ruido del canal k, en dBm. |
| D_k | Potencia mínima recibida declarada para el canal k. |
| T_k | Umbral de detección del canal k: N_k + 1,5 dB. |
| En | Razón de concordancia entre sitios: abs(δ) / sqrt(W_A² + W_B²). |
| GUM | Guía para la expresión de la incertidumbre de medida. |
| AGC | Control automático de ganancia; prohibido. |

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

La sección 1 presenta el propósito, alcance, definiciones, referencias y estructura. La sección 2 define el marco de medición: catálogo de measurands, selección de métodos y mapeo normativo. La sección 3 contiene los bloques SYS agrupados por familia. La sección 4 presenta las cadenas de corrección. La sección 5 presenta los presupuestos de incertidumbre. La sección 6 lista los protocolos de campo. La sección 7 traza cada bloque SYS a sus requisitos y pruebas.

---

## 2. Measurement Framework

### 2.1 Measurand Catalog

| Measurand ID | Quantity | Unit | Method Family | StRS Traces |
|---|---|---|---|---|
| `MEAS-001` | Potencia de canal | dBm | FFT promediada e integración de 105 bins | `STK-REQ-009`, `STK-REQ-010`, `STK-REQ-011`, `STK-REQ-069` |
| `MEAS-002` | Estado de ocupación | enum | Exceso contra piso de ruido y umbrales | `STK-REQ-003` a `STK-REQ-007` |
| `MEAS-003` | Ciclo de trabajo | % | Conteo de estados por intervalo | `STK-REQ-008` |
| `MEAS-004` | Piso de ruido | dBm | Percentil 10 por paso y mediana de 10 barridos | `STK-REQ-006`, `STK-REQ-039` |
| `MEAS-005` | Frecuencia y corrección del cristal | Hz, ppm | Tono CW y FFT; corrección medida | `STK-REQ-050`, `STK-REQ-056` |
| `MEAS-006` | Tiempo UTC | µs | NTP y reloj monótono | `STK-REQ-028` |
| `MEAS-007` | Salud de la adquisición | cuentas | Contadores de desbordamiento y tramas perdidas | `STK-REQ-027` |
| `MEAS-008` | Disponibilidad | % | Registros completos de barrido en 30 días | `STK-REQ-048`, `STK-REQ-049` |
| `MEAS-009` | Concordancia entre sitios | En | Comparación de 12 puntos con k = 2 | `STK-REQ-051` |
| `MEAS-010` | Corrección de amplitud | dB | K(f) contra fuente trazable | `STK-REQ-017`, `STK-REQ-018` |

### 2.2 Method Selection and Rationale

| Method Family | Selected Method | Rejected Alternatives | Rationale |
|---|---|---|---|
| Potencia de canal | FFT de 4 096 puntos, ventana Hann, solape 50 %, promedio de 2 495 segmentos, 105 bins por canal | No suministradas por el Build Package | Incertidumbre estadística de 0,015 dB y potencia integrada por canal. |
| Ocupación | Energía contra piso de ruido verificado; Occupied si e ≥ 1,5 dB, Free candidato si e ≤ 1,0 dB, histéresis de 0,5 dB | Filtrado temporal, descartado; la decisión es por observación (REF-001 §5.7). | Falsa alarma esperada de 0,14 % y detección esperada de 99,87 % con SNR 0 dB. |
| Barrido | 3 capturas escalonadas a 10 Msps y 8 MHz útiles | 20 Msps, descartado por mayor carga | Cumple el período de 10 s y las cero pérdidas con la menor carga. |
| Calibración | Fuente trazable, 24 centros de canal, K(f) interpolada linealmente | Conmutador interno, no incluido | Trazabilidad y plano de referencia en el conector de antena. |
| Verificación | Referencia independiente, 12 puntos, tolerancia 1,0 dB | Misma fuente de calibración, prohibida por R-20 | Trazabilidad independiente y presupuesto de 0,59 dB. |
| Hora | Cliente NTP estándar y reloj monótono | GPS, prohibido por R-71; reloj con batería, no incluido | La red del sitio provee la hora y el sello UTC no depende de GPS. |
| Alertas | Reglas sobre registros e historial | Alertas desde la potencia recibida, prohibidas por R-40 | Cinco reglas definidas, sin dictamen regulatorio. |
| Web | HTTP GET o HEAD en el puerto 8080, sin autenticación | Inicio de sesión y roles, prohibidos por R-67 | Acceso abierto de solo lectura para la red del sitio. |
| Reproducibilidad | En con k = 2, 10 de 12 puntos, ningún abs(δ) > 6 dB | Promedio simple y comparación de señales de campo | La regla aprobada compara los resultados de dos sitios, no las señales recibidas. |

### 2.3 Normative-to-Method Mapping

| Normative Source | Clause | Realized By (Method) | Blocks | Compliance |
|---|---|---|---|---|
| IEC 60529 | No suministrada por el Build Package | Ensayo de polvo y chorro de agua IP65; definición adjunta en P-095 | `SYS-ENV-001` | `PENDING` |
| Sin fuente normativa adicional | — | — | Todos los SYS | `NOT_APPLICABLE` |

---

## 3. System Requirements

### 3.1 Hardware, adquisición y estimación

---

**`SYS-HW-001` — Plataforma de hardware y receptor HackRF One**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Parameter** | Receptor HackRF One, placa Raspberry Pi 5 y referencia de frecuencia |
| **Method** | Selección de equipos COTS de REF-001 §4.2; sin GPS; corrección de frecuencia medida en la calibración |
| **Traces to** | `STK-REQ-054`, `STK-REQ-055`, `STK-REQ-056`, `STK-REQ-071`, `STK-REQ-050` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] El receptor es HackRF One; 0 nodos con otro receptor (STK-REQ-054).
2. [ ] No hay receptor GPS; 0 receptores GPS (STK-REQ-071).
3. [ ] La referencia de frecuencia de cada dispositivo y su corrección están registradas (STK-REQ-056).
4. [ ] El rango dinámico y la compresión de la configuración desplegada están documentados (STK-REQ-055).
5. [ ] El error de asignación a canal más la incertidumbre de la fuente es ≤ 5 kHz a 100 MHz (STK-REQ-050).

**Notes:**  
REF-001 §3.12, §4.2 y §5.5; HWC-SDR-*, HWC-CPU-*; pruebas P-035, P-056, P-060 y P-071.

---

**`SYS-TIM-001` — Servicio de hora UTC y sellado de barridos**

| Field | Value |
|---|---|
| **Type** | `PROCESSING` |
| **Parameter** | Marca de tiempo UTC de cada barrido |
| **Method** | Cliente NTP estándar; publicación cada 1 s; reloj monótono para el ritmo de barrido |
| **Traces to** | `STK-REQ-028`, `STK-REQ-037` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Cada barrido lleva utc_us, resolution_us y sync_state; la resolución es de 1 µs, mejor que 1 ms (STK-REQ-028).
2. [ ] El reloj se declara no sincronizado si el desfase supera 50 ms o si pasaron más de 3 600 s desde la última sincronización.
3. [ ] Un barrido nunca se retiene por falta de hora; se marca unsynced.
4. [ ] Tras un arranque se espera hasta 120 s la primera sincronización.

**Notes:**  
REF-001 §5.2; Anexo A «Servicio de hora»; E-TIME-001 a E-TIME-003.

---

**`SYS-CFG-001` — Configuración del sitio y referencia de asignación**

| Field | Value |
|---|---|
| **Type** | `CONFIGURATION` |
| **Parameter** | site-config.json y station_reference_file |
| **Method** | Carga atómica, validación de campos y SHA-256; recarga al arrancar y por orden |
| **Traces to** | `STK-REQ-016`, `STK-REQ-052`, `STK-REQ-070`, `STK-REQ-074`, `STK-REQ-075` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] La ubicación (país, ciudad, lugar o dirección) es obligatoria y va a todo informe (STK-REQ-070).
2. [ ] record_time_min acepta 10 a 43 200 min y rechaza menos de 10 min (STK-REQ-074).
3. [ ] mapping_error_limit_khz acepta 1 a 20 kHz y rechaza más de 20 kHz (STK-REQ-075).
4. [ ] Un nodo nuevo se agrega y configura sin reescribir código; el hash del software no cambia (STK-REQ-052).
5. [ ] La referencia de estaciones del sitio se carga y se usa en la comparación (STK-REQ-016).
6. [ ] El archivo se acepta o se rechaza completo; un archivo rechazado deja activa la última configuración válida.

**Notes:**  
REF-001 §5.1; Anexo B site_config/station_assignment_reference/config_status; Anexo C load_and_validate_site_config.

---

**`SYS-ACQ-001` — Adquisición escalonada y barrido de la banda FM**

| Field | Value |
|---|---|
| **Type** | `MEASUREMENT` |
| **Parameter** | Muestras I/Q, ganancias, pérdidas y saturación por barrido |
| **Method** | Tres capturas escalonadas a 10 Msps y 8 bits, 39 tramas de 131 072 muestras, ganancias fijas sin AGC |
| **Traces to** | `STK-REQ-001`, `STK-REQ-002`, `STK-REQ-022`, `STK-REQ-023`, `STK-REQ-024`, `STK-REQ-025`, `STK-REQ-026`, `STK-REQ-050`, `STK-REQ-057`, `STK-REQ-069` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Un barrido completo cubre los 199 canales y empieza cada 6 s; el intervalo entre inicios no supera 10 s (STK-REQ-001, STK-REQ-002).
2. [ ] La adquisición sostiene 10 Msps sin desbordamientos ni tramas perdidas en una corrida continua (STK-REQ-057).
3. [ ] No se usa AGC; se registran las ganancias individuales y el estado del amplificador en el 100 % de las adquisiciones (STK-REQ-022, STK-REQ-023).
4. [ ] Una muestra a plena escala marca los canales de su paso como saturados y retiene su potencia (STK-REQ-024).
5. [ ] Un desbordamiento o una trama perdida marca los 199 registros del barrido, retiene la potencia y libera ocupación Uncertain (STK-REQ-025).
6. [ ] El 100 % de las pérdidas inyectadas se cuentan como tramas perdidas (STK-REQ-026).
7. [ ] La potencia de cada canal se integra sobre 256 kHz (STK-REQ-069).
8. [ ] El error de asignación a canal más la incertidumbre de la fuente es ≤ 5 kHz a 100 MHz (STK-REQ-050).

**Notes:**  
REF-001 §5.3; Anexo A «Adquisición y barrido»; Anexo C scan_cycle; HWC-SDR-*.

---

**`SYS-EST-001` — Estimador espectral y potencia integrada por canal**

| Field | Value |
|---|---|
| **Type** | `MEASUREMENT` |
| **Parameter** | Potencia integrada por canal en dBFS y espectro reducido |
| **Method** | FFT de 4 096 puntos, ventana Hann, solape 50 %, 2 495 segmentos, 105 bins por canal, supresión de DC |
| **Traces to** | `STK-REQ-002`, `STK-REQ-050`, `STK-REQ-056`, `STK-REQ-069` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Cada canal se integra sobre 105 bins (256,347 kHz) alrededor de su centro (STK-REQ-069).
2. [ ] Los 199 canales se evalúan en cada barrido (STK-REQ-002).
3. [ ] La corrección de frecuencia del oscilador se aplica con f_true = f_nominal·(1 + c·10⁻⁶) (STK-REQ-056).
4. [ ] La cota del error de asignación a canal es 3,4648 kHz a 100 MHz y se compara con el límite configurado (STK-REQ-050).
5. [ ] La incertidumbre estadística del promedio es 0,015 dB.

**Notes:**  
REF-001 §5.4; Anexo C estimate_channel_power; Anexo A «Estimador espectral».

### 3.2 Calibración, verificación y detección

---

**`SYS-CAL-001` — Calibración de amplitud y validez de la corrección**

| Field | Value |
|---|---|
| **Type** | `MEASUREMENT` |
| **Parameter** | Potencia calibrada en dBm, corrección K(f), incertidumbre y estado de validez |
| **Method** | Calibración en el sitio contra fuente trazable; K(f) interpolada en 24 centros de canal; presupuesto de incertidumbre GUM |
| **Traces to** | `STK-REQ-009`, `STK-REQ-010`, `STK-REQ-011`, `STK-REQ-012`, `STK-REQ-013`, `STK-REQ-014`, `STK-REQ-017`, `STK-REQ-018`, `STK-REQ-021`, `STK-REQ-029`, `STK-REQ-055`, `STK-REQ-056`, `STK-REQ-058` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] El 100 % de los registros de canal-barrido lleva potencia calibrada en dBm en el conector de antena (STK-REQ-009).
2. [ ] La diferencia absoluta con una referencia independiente calificada es ≤ 3 dB en ≥ 10 canales distintos, restando la incertidumbre expandida (STK-REQ-010).
3. [ ] El 100 % de los valores lleva incertidumbre como semiancho en dB y su base (STK-REQ-011).
4. [ ] Cada salida lleva valor, incertidumbre, límite o ausencia registrada y comparación (STK-REQ-012); sin límite se registra not_configured y nunca within_limit (STK-REQ-013); un estado indeterminado no se convierte en dentro o fuera (STK-REQ-014).
5. [ ] La corrección se establece contra una fuente trazable y el registro nombra fuente, fecha e incertidumbre (STK-REQ-017).
6. [ ] El registro de calibración conserva identificador, configuración de hardware y firmware, plano de referencia, fuente y estado de validez (STK-REQ-018).
7. [ ] Solo se libera potencia en estado valid o expiring; si la corrección no puede demostrarse, la potencia se retiene (STK-REQ-021).
8. [ ] El 100 % de los registros de potencia nombra las ganancias y el registro de calibración aplicable (STK-REQ-029).
9. [ ] La configuración de medición se compara por SHA-256 al inicio de cada barrido y no se mide con una configuración distinta de la calibrada (STK-REQ-058).
10. [ ] Se documentan el rango dinámico y la compresión de la configuración desplegada (STK-REQ-055); se registra la referencia de frecuencia y su corrección (STK-REQ-056).

**Notes:**  
REF-001 §5.5; Anexo C establish_amplitude_calibration y apply_calibration_to_scan; presupuesto de incertidumbre en SyRS §5.

---

**`SYS-VER-001` — Verificación periódica con referencia independiente**

| Field | Value |
|---|---|
| **Type** | `MEASUREMENT` |
| **Parameter** | Diferencia de potencia calibrada contra referencia independiente y validez |
| **Method** | 12 puntos (6 canales × 2 niveles), 5 barridos por punto, mediana, tolerancia 1,0 dB, presupuesto 0,59 dB |
| **Traces to** | `STK-REQ-019`, `STK-REQ-020`, `STK-REQ-021`, `STK-REQ-038`, `STK-REQ-060` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] El tiempo máximo entre dos verificaciones aprobadas no supera el intervalo declarado, con mínimo 4 días (STK-REQ-019).
2. [ ] La referencia de verificación es un instrumento distinto, con trazabilidad independiente, de la que estableció la corrección; 0 verificaciones con la misma referencia (STK-REQ-020).
3. [ ] El registro de validación identifica la referencia independiente y su incertidumbre (STK-REQ-060).
4. [ ] Una verificación aprueba si las 12 diferencias están dentro de 1,0 dB y la corrección de frecuencia dentro de ±20 ppm; una verificación fallida invalida la calibración (STK-REQ-021).
5. [ ] El estado expiring dispara la alerta de calibración no demostrada (STK-REQ-038).

**Notes:**  
REF-001 §5.6; Anexo C verify_amplitude_correction; Anexo A «Verificación periódica».

---

**`SYS-DET-001` — Detector de ocupación con estados Occupied, Free y Uncertain**

| Field | Value |
|---|---|
| **Type** | `PROCESSING` |
| **Parameter** | Exceso e_k = P_k − N_k, umbrales, histéresis y ciclo de trabajo |
| **Method** | Energía contra piso de ruido verificado; Occupied si e ≥ 1,5 dB, Free candidato si e ≤ 1,0 dB, histéresis 0,5 dB; regla de adyacencia R_k |
| **Traces to** | `STK-REQ-003`, `STK-REQ-004`, `STK-REQ-005`, `STK-REQ-006`, `STK-REQ-007`, `STK-REQ-008`, `STK-REQ-030`, `STK-REQ-059` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] El 100 % de los registros canal-barrido lleva uno de los tres estados (STK-REQ-003).
2. [ ] La probabilidad de detección es ≥ 95 % con SNR ≥ 0 dB (STK-REQ-004).
3. [ ] La probabilidad de falsa alarma es ≤ 5 % en canales vacantes (STK-REQ-005).
4. [ ] Free solo si e ≤ 1,0 dB, calibración válida, captura no saturada, barrido no marcado, potencia no retenida, D_k configurada, D_k − N_k ≥ 10 dB y T_k ≤ D_k; un solo registro que viole la regla hace fallar la prueba (STK-REQ-006).
5. [ ] Si no puede liberarse Free o la validez no es válida, el estado es Uncertain; 0 % de esos registros se liberan Free (STK-REQ-007).
6. [ ] Cada canal y cada intervalo informa ciclo de trabajo y fracción Uncertain (STK-REQ-008).
7. [ ] El 100 % de los estados Free del informe puede reverificarse con las entradas guardadas (STK-REQ-030).
8. [ ] El 100 % de los registros Free muestra que no hubo detección, validez válida, margen ≥ 10 dB y umbral no superior a la potencia mínima declarada (STK-REQ-059).

**Notes:**  
REF-001 §5.7; Anexo C classify_channels y accumulate_duty_cycle.

---

**`SYS-ASG-001` — Comparación con la referencia de estaciones asignadas**

| Field | Value |
|---|---|
| **Type** | `PROCESSING` |
| **Parameter** | Resultado consistent, unassigned-occupied, assigned-free o indeterminate |
| **Method** | Tabla de decisión de REF-001 §5.8; referencia ausente o inválida deja los 199 canales indeterminate |
| **Traces to** | `STK-REQ-014`, `STK-REQ-015`, `STK-REQ-016`, `STK-REQ-036` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] El 100 % de los registros canal-barrido tiene resultado de comparación (STK-REQ-015).
2. [ ] Al menos una referencia del sitio se carga y se usa en la comparación (STK-REQ-016).
3. [ ] Una referencia ausente o inválida deja los 199 canales indeterminate y no levanta alertas desde la comparación (STK-REQ-014).
4. [ ] Un canal ocupado no asignado produce unassigned-occupied y alimenta la alerta de ocupación inesperada (STK-REQ-036).

**Notes:**  
REF-001 §5.8; Anexo C compare_with_reference.

### 3.3 Registros, informes, alertas y web

---

**`SYS-REC-001` — Construcción de registros de barrido y de salud**

| Field | Value |
|---|---|
| **Type** | `PROCESSING` |
| **Parameter** | Encabezado, 199 registros de canal y registro de salud por barrido |
| **Method** | Construcción a partir de las salidas de los módulos; campos y banderas de REF-001 §5.9 |
| **Traces to** | `STK-REQ-012`, `STK-REQ-013`, `STK-REQ-014`, `STK-REQ-024`, `STK-REQ-025`, `STK-REQ-027`, `STK-REQ-029`, `STK-REQ-030`, `STK-REQ-032`, `STK-REQ-033`, `STK-REQ-059` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Cada barrido produce 1 encabezado, 199 registros de canal y 1 registro de salud; si el barrido falla, solo el registro de salud (STK-REQ-027).
2. [ ] Cada registro de salud contiene conteo de desbordamientos, conteo de tramas perdidas y número de registros publicados (STK-REQ-027).
3. [ ] Cada registro de canal lleva potencia e incertidumbre con base, razón de retención, ganancias, registro de calibración, estado de ocupación con entradas, comparación, límite y comparación, banderas y etiqueta de evidencia (STK-REQ-012, STK-REQ-029, STK-REQ-030).
4. [ ] La comparación con el límite usa within_limit, outside_limit, indeterminate, not_configured o unavailable; sin límite se registra not_configured (STK-REQ-013, STK-REQ-014).
5. [ ] Todo registro lleva «Screening evidence only: not a compliance determination» (STK-REQ-032) y ningún texto afirma cumplimiento o incumplimiento (STK-REQ-033).
6. [ ] Las capturas saturadas y los barridos marcados se reflejan en los registros (STK-REQ-024, STK-REQ-025).
7. [ ] Los registros Free muestran las condiciones de liberación (STK-REQ-059).

**Notes:**  
REF-001 §5.9; Anexo B scan_header/channel_record/health_record.

---

**`SYS-HIS-001` — Historial en memoria para vistas y alertas**

| Field | Value |
|---|---|
| **Type** | `PROCESSING` |
| **Parameter** | Ventana de 744 h en bins de 60 s |
| **Method** | Historial en memoria, vacío en cada reinicio; sin swap ni volcados; consultas de hasta 2 000 bins por canal |
| **Traces to** | `STK-REQ-008`, `STK-REQ-031`, `STK-REQ-039`, `STK-REQ-041`, `STK-REQ-043` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] El historial cubre 744 h en bins de 60 s (44 640 bins por canal) y empieza vacío en cada reinicio (STK-REQ-031).
2. [ ] Una consulta devuelve como máximo 2 000 bins por canal y 40 000 en total.
3. [ ] La potencia de un bin proviene solo de valores liberados (STK-REQ-041, STK-REQ-043).
4. [ ] La mediana del piso de ruido de las ventanas de 60 min alimenta la alerta de deriva (STK-REQ-039).
5. [ ] El historial no se escribe a disco (STK-REQ-031).

**Notes:**  
REF-001 §5.10; Anexo C update_history; Anexo B history_bins_response/history_series_response.

---

**`SYS-REP-001` — Informe de tamizaje en disco**

| Field | Value |
|---|---|
| **Type** | `PROCESSING` |
| **Parameter** | Carpeta reports/<run_id>, header.json, scans-<hora>.csv, intervals.csv y progress.json |
| **Method** | Escritura por barrido con vuelco a la tarjeta; segmentos de 3 600 s; rotación solo si falta espacio y nunca los últimos 30 días |
| **Traces to** | `STK-REQ-030`, `STK-REQ-031`, `STK-REQ-059`, `STK-REQ-062`, `STK-REQ-070`, `STK-REQ-073`, `STK-REQ-074` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] El informe guardado contiene resultados, registros de fecha y hora, tiempo de ejecución e información de ubicación (STK-REQ-062).
2. [ ] El 100 % de los informes lleva la ubicación ingresada (STK-REQ-070).
3. [ ] El 100 % de los resultados producidos antes de una interrupción están en el informe; un corte cuesta como máximo el barrido en escritura (STK-REQ-073).
4. [ ] Una corrida cronometrada dura el tiempo configurado, con mínimo 10 min (STK-REQ-074).
5. [ ] La única información de monitoreo en disco es el informe (STK-REQ-031).
6. [ ] Cada fila de canal lleva las entradas de ocupación y las condiciones de liberación Free (STK-REQ-030, STK-REQ-059).
7. [ ] La rotación borra segmentos cerrados de más de 30 días solo si falta espacio; si no basta, se deja de escribir el informe y se sigue monitoreando.

**Notes:**  
REF-001 §5.11; Anexo C report_run_lifecycle y write_scan_to_report; Anexo B report_header/report_lines.

---

**`SYS-ALR-001` — Motor de alertas de cinco reglas**

| Field | Value |
|---|---|
| **Type** | `PROCESSING` |
| **Parameter** | channel_silent, unexpected_occupancy, sensor_offline, calibration_not_demonstrated, noise_floor_drift |
| **Method** | Reglas sobre registros e historial; crédito de silencio por observaciones; contadores de persistencia; temporizador monótono |
| **Traces to** | `STK-REQ-034`, `STK-REQ-035`, `STK-REQ-036`, `STK-REQ-037`, `STK-REQ-038`, `STK-REQ-039`, `STK-REQ-040`, `STK-REQ-046` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] La alerta channel_silent se levanta cuando el crédito llega a H × 3 600 s y el ciclo previo es > 90 % (STK-REQ-034).
2. [ ] Las observaciones Uncertain suman 0 s y no reinician el crédito de silencio (STK-REQ-035).
3. [ ] La alerta unexpected_occupancy se levanta a los 3 barridos seguidos de unassigned-occupied (STK-REQ-036).
4. [ ] La alerta sensor_offline se levanta a los 18 s sin un punto de salud (3 × 6 s) (STK-REQ-037).
5. [ ] La alerta calibration_not_demonstrated se levanta en el primer barrido con estado expiring, expired, invalid o none, o con potencia retenida por calibración (STK-REQ-038).
6. [ ] La alerta noise_floor_drift se levanta cuando |M_ahora − M_ref| > 6 dB en 24 h (STK-REQ-039).
7. [ ] Ninguna alerta se genera desde la potencia recibida sin límite configurado (STK-REQ-040).
8. [ ] Las alertas emitidas se presentan al personal en la vista web (STK-REQ-046).

**Notes:**  
REF-001 §5.12; Anexo C evaluate_scan_alerts/evaluate_history_alerts/watch_health_points.

---

**`SYS-WEB-001` — Servicio web de solo lectura y cuatro vistas**

| Field | Value |
|---|---|
| **Type** | `INTERFACE` |
| **Parameter** | Vistas /power, /spectrum, /stations, /status, /alerts y descarga de informes |
| **Method** | HTTP GET o HEAD en el puerto 8080; recursos locales; solo valores liberados; sin inicio de sesión |
| **Traces to** | `STK-REQ-032`, `STK-REQ-033`, `STK-REQ-041`, `STK-REQ-042`, `STK-REQ-043`, `STK-REQ-044`, `STK-REQ-045`, `STK-REQ-046`, `STK-REQ-047`, `STK-REQ-067` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Las cuatro vistas están disponibles: potencia por canal y tiempo, espectro actual con marcadores, estaciones seleccionadas en 24 h y estado del nodo (STK-REQ-041 a STK-REQ-044).
2. [ ] La vista de estado muestra las cinco magnitudes: estado en línea, antigüedad del último barrido, deriva del piso de ruido, conteo de desbordamientos y conteo de tramas perdidas (STK-REQ-044).
3. [ ] Solo se dibujan salidas liberadas; un valor retenido se muestra con validez y banderas, nunca como 0 o último valor (STK-REQ-045).
4. [ ] Las alertas emitidas se muestran al personal (STK-REQ-046).
5. [ ] Los cinco elementos de evidencia son accesibles: mediciones calibradas, registros, indicadores de calidad, incertidumbre y alertas (STK-REQ-047).
6. [ ] Todo usuario de la red del sitio accede sin inicio de sesión y sin restricción por rol (STK-REQ-067).
7. [ ] Toda página y respuesta lleva la etiqueta de evidencia de tamizaje y no afirma cumplimiento (STK-REQ-032, STK-REQ-033).

**Notes:**  
REF-001 §5.13; Anexo C serve_view_request/serve_report_file/refresh_page; Anexo B web_view_data/web_request.

### 3.4 Supervisión, recursos, reproducibilidad y seguridad

---

**`SYS-SUP-001` — Supervisión, reinicio y watchdog**

| Field | Value |
|---|---|
| **Type** | `PROCESSING` |
| **Parameter** | Contadores de progreso, escalera de reinicios y estado del nodo |
| **Method** | Supervisor de cinco unidades; contador cada 1 s, unidad colgada a los 10 s; watchdog de hardware de 15 s |
| **Traces to** | `STK-REQ-021`, `STK-REQ-024`, `STK-REQ-025`, `STK-REQ-026`, `STK-REQ-027`, `STK-REQ-037`, `STK-REQ-048`, `STK-REQ-049` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Una unidad sin cambio de contador durante 10 s se mata y se reinicia; measure publica barrido o salud al menos cada 12 s (STK-REQ-048).
2. [ ] La escalera de esperas es 5, 10, 20, 40 y 60 s; cinco reinicios en 600 s declaran bucle y a los 1 800 s se reinicia el nodo, máximo 3 veces por 24 h.
3. [ ] El watchdog de hardware es de 15 s y el bucle del supervisor lo alimenta cada 5 s.
4. [ ] El estado del nodo (starting, measuring, measuring_degraded, not_measuring) se publica cada 1 s y un estado de más de 5 s se trata como supervisor no responde.
5. [ ] Un proceso vuelve a producir barridos completos 72 s después de la última medición y 300 s tras un reinicio completo (STK-REQ-048).
6. [ ] La disponibilidad se cuenta según STK-REQ-049 y se evalúa con compute_availability (STK-REQ-049).
7. [ ] La cadena marcar-retener-supervisar cubre calibración no demostrable, saturación, desbordamiento, trama perdida y falta de salud (STK-REQ-021, STK-REQ-024 a STK-REQ-027, STK-REQ-037).

**Notes:**  
REF-001 §5.14; Anexo C start_node/supervise_processes/stop_node; Anexo D.

---

**`SYS-RES-001` — Presupuestos de tiempo, recursos y fiabilidad**

| Field | Value |
|---|---|
| **Type** | `QUALITY` |
| **Parameter** | Tiempo por barrido, memoria, procesador, almacenamiento, energía y disponibilidad |
| **Method** | Asignaciones de REF-001 §4.5 y Anexo A; límites por unidad aplicados al arrancar; compute_availability |
| **Traces to** | `STK-REQ-001`, `STK-REQ-037`, `STK-REQ-048`, `STK-REQ-049`, `STK-REQ-057`, `STK-REQ-061`, `STK-REQ-066`, `STK-REQ-072`, `STK-REQ-073` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] La cadena de un barrido suma 4,98 s de los 6 s, con holgura de 1,02 s; un barrido de más de 7 s se marca tardío (STK-REQ-001).
2. [ ] El consumo conjunto de placa, receptor y ventilador no supera 20 W (80 % de 25 W).
3. [ ] La carga sostenida del procesador no supera 70 %; la memoria suma 1 738 MB con 78 % de margen.
4. [ ] El informe ocupa unos 599 MB por día y 30 días = 17,97 GB; el piso de espacio libre es 12,8 GB.
5. [ ] La disponibilidad de 30 días es ≥ 95 % y se evalúa con la definición de STK-REQ-049 (STK-REQ-048, STK-REQ-049).
6. [ ] La corrida de campo de 72 h se valida con el procedimiento run_field_validation (STK-REQ-061).
7. [ ] El nodo opera a 40 °C ambiente y con red de 60 Hz (STK-REQ-066, STK-REQ-072).

**Notes:**  
REF-001 §4.5, §5.16 y §9.2; Anexo A «Presupuesto de recursos/tiempo/fiabilidad»; Anexo C monitor_temperature/apply_resource_limits/compute_availability/run_field_validation.

---

**`SYS-RPL-001` — Reproducibilidad entre sitios**

| Field | Value |
|---|---|
| **Type** | `QUALITY` |
| **Parameter** | En = /δ/ / sqrt(W_A² + W_B²), 12 puntos y 60 observaciones vacantes |
| **Method** | Comparación de 12 puntos (6 canales × 2 niveles), k = 2, regla aprobada de 10 de 12 puntos y ningún /δ/ > 6 dB |
| **Traces to** | `STK-REQ-051`, `STK-REQ-052`, `STK-REQ-061` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] La comparación usa 12 puntos y concuerda si En ≤ 1; el criterio se cumple con ≥ 10 de 12 puntos y ningún |δ| > 6 dB (STK-REQ-051).
2. [ ] Cada sitio cumple detección ≥ 95 % y falsa alarma ≤ 5 % sobre su conjunto de aceptación con ≥ 60 observaciones vacantes (STK-REQ-051).
3. [ ] Los informes de ambos sitios están completos.
4. [ ] Los elementos idénticos (paquete, formatos, ajustes, umbrales, procedimientos y clase de referencia) se comparan; una diferencia rechaza la comparación (E-REP-001).
5. [ ] La repetición en otro sitio se hace con el mismo software y solo cambia la configuración (STK-REQ-052).
6. [ ] La validación de campo de 72 h con referencia independiente ≥ 6 h es el insumo de cada sitio (STK-REQ-061).

**Notes:**  
REF-001 §5.15 y §7.6; Anexo C repeat_at_another_site/compare_two_sites.

---

**`SYS-SEC-001` — Acceso abierto y clasificación de evidencia**

| Field | Value |
|---|---|
| **Type** | `QUALITY` |
| **Parameter** | Control de acceso, etiqueta de evidencia y vocabulario prohibido |
| **Method** | Web de solo lectura sin autenticación; etiqueta fija; lista de palabras prohibidas |
| **Traces to** | `STK-REQ-032`, `STK-REQ-033`, `STK-REQ-047`, `STK-REQ-067` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Todo usuario de la red del sitio accede a la vista web y a los informes guardados; 0 usuarios o roles sin acceso (STK-REQ-067).
2. [ ] Todo registro, informe y tablero se identifica como evidencia de tamizaje (STK-REQ-032).
3. [ ] Ninguna alerta, registro o informe declara cumplimiento o incumplimiento; los textos se comparan contra la lista de palabras prohibidas (STK-REQ-033).
4. [ ] Los cinco elementos de evidencia están disponibles al personal (STK-REQ-047).
5. [ ] El tráfico web no se cifra en esta versión y no hay escritura a través de la web.

**Notes:**  
REF-001 §5.9, §5.13 y §2.2; Anexo C serve_view_request.

### 3.5 Comunicación, datos y entorno

---

**`SYS-IPC-001` — Comunicación entre unidades**

| Field | Value |
|---|---|
| **Type** | `PROTOCOL` |
| **Parameter** | Mensajes JSON UTF-8 por sockets Unix de flujo con longitud de 4 bytes |
| **Method** | Longitud big-endian de 4 bytes, mensajes de hasta 16 MB, validación contra Anexo B, 3 mensajes inválidos reinician al productor |
| **Traces to** | `STK-REQ-027`, `STK-REQ-031`, `STK-REQ-052`, `STK-REQ-057` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Cada mensaje es JSON UTF-8 precedido por su longitud en 4 bytes big-endian, de hasta 16 MB.
2. [ ] No se abre ningún puerto de red entre unidades; solo sockets Unix locales.
3. [ ] Cada consumidor valida cada mensaje contra su formato del Anexo B; tras 3 mensajes inválidos seguidos del mismo productor, ese proceso se reinicia.
4. [ ] Los envíos no bloquean; si el consumidor no responde, el productor encola hasta 10 barridos (60 s) y descarta los más antiguos.
5. [ ] La comunicación no escribe registros de monitoreo a disco (STK-REQ-031) y soporta la adquisición sin pérdidas (STK-REQ-057).

**Notes:**  
REF-001 §4.3; Anexo B (33 formatos).

---

**`SYS-DAT-001` — Formatos de datos y archivos persistentes**

| Field | Value |
|---|---|
| **Type** | `PROTOCOL` |
| **Parameter** | 33 esquemas JSON del Anexo B y archivos del nodo |
| **Method** | Versionado de formatos; validación de esquema; escritura atómica; retención de calibración y validación |
| **Traces to** | `STK-REQ-018`, `STK-REQ-031`, `STK-REQ-052`, `STK-REQ-060`, `STK-REQ-062`, `STK-REQ-070`, `STK-REQ-073`, `STK-REQ-074`, `STK-REQ-075` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Los 33 formatos del Anexo B se usan con su versión declarada y los cambios menores agregan campos opcionales; los mayores cambian significado o tabla de valores.
2. [ ] Los archivos del nodo son site-config.json, la referencia de estaciones, reports/<run_id>/, calibration/, validation/, la bitácora del supervisor y el sistema de archivos temporal en memoria.
3. [ ] Los registros de calibración y validación nunca se borran; la única información de monitoreo en disco es el informe (STK-REQ-031, STK-REQ-018, STK-REQ-060).
4. [ ] La configuración y la referencia se validan contra sus esquemas y se aceptan o rechazan completas (STK-REQ-052, STK-REQ-070, STK-REQ-074, STK-REQ-075).
5. [ ] El informe se escribe con nombres temporales y renombrado atómico para header.json y progress.json (STK-REQ-073).
6. [ ] Cada informe lleva la ubicación y la etiqueta de evidencia (STK-REQ-062, STK-REQ-070).

**Notes:**  
REF-001 §6; Anexo B; Anexo C report_run_lifecycle.

---

**`SYS-ENV-001` — Entorno físico, energía y costo**

| Field | Value |
|---|---|
| **Type** | `CONSTRAINT` |
| **Parameter** | Alimentación 120 V/60 Hz, temperatura, IP65, interiores/exteriores y costo |
| **Method** | Instalación en gabinete IP66 con fuente externa; verificación por pruebas P-063 a P-066, P-071, P-094 |
| **Traces to** | `STK-REQ-053`, `STK-REQ-054`, `STK-REQ-063`, `STK-REQ-064`, `STK-REQ-065`, `STK-REQ-066`, `STK-REQ-071`, `STK-REQ-072` |
| **Standard(s)** | IEC 60529 |

**Acceptance Criteria:**

1. [ ] El nodo opera conectado a 120 V y 60 Hz; el 100 % de las corridas de aceptación se alimenta así (STK-REQ-063, STK-REQ-072).
2. [ ] El nodo opera en interiores y exteriores y cumple sus requisitos en ambos (STK-REQ-064).
3. [ ] El gabinete impide el ingreso de polvo y lluvia bajo la exposición definida (IP65); 0 ingresos (STK-REQ-065).
4. [ ] El nodo opera a 40 °C ambiente y cumple todos sus requisitos (STK-REQ-066).
5. [ ] El nodo no incluye receptor GPS (STK-REQ-071) y usa HackRF One (STK-REQ-054).
6. [ ] El costo de un nodo completo no excede 3 200 USD, sin referencias de calibración ni licencias (STK-REQ-053).

**Notes:**  
REF-001 §3.10, §3.12, §4.2 y §4.5; Anexo E P-063 a P-066, P-071, P-094 y P-095; HWC-ENV-* y HWC-PWR-*.

---

## 4. Correction Chains

| Block | Correction | Model / Source | Applied Where |
|---|---|---|---|
| `SYS-CAL-001` | Plano de referencia en el conector de antena del receptor | REF-001 §4.2 y §5.5 | Aplicación de K(f) a la potencia de canal |
| `SYS-CAL-001` | Pérdida del cable de calibración | Medida en establish_amplitude_calibration | Cálculo de L = nivel de la fuente − pérdida del cable |
| `SYS-CAL-001` | Corrección de frecuencia del cristal c en ppm | Mediana de (f_est − f_nominal)/f_nominal × 10⁶ | Estimador y mapeo de frecuencia de canal |
| `SYS-CAL-001` | Ganancia de antena y pérdida del cable de antena | Fuera de la cantidad calibrada (R-09); se registran con el plano de referencia | No se aplican a la potencia de canal |
| `SYS-EST-001` | Supresión de la espiga de continua | Bins a ±3 del centro reemplazados por la media de ±4 a ±6 | Espectro y potencia de canal |
| `SYS-DET-001` | Referencia de ruido N_k | Percentil 10 por paso más el piso almacenado del canal | Exceso e_k = P_k − N_k |
| `SYS-VER-001` | Diferencia contra la referencia independiente | 12 puntos, mediana de 5 barridos, tolerancia 1,0 dB | Aprobación de la verificación |
| `SYS-RPL-001` | En entre dos sitios | δ = D_A − D_B; W = sqrt(U² + u²); En = abs(δ) / sqrt(W_A² + W_B²) | Criterio de reproducibilidad |

---

## 5. Uncertainty Budgets

| Measurand | Component | Source u(x) | Distribution | Sensitivity c | Standard u |
|---|---|---|---|---|---|
| Potencia de canal calibrada | Fuente de referencia | 0,5 dB | No declarada por el Build Package | 1 | 0,5 dB |
| Potencia de canal calibrada | Desadaptación | 0,3 dB | No declarada por el Build Package | 1 | 0,3 dB |
| Potencia de canal calibrada | Cable | 0,1 dB | No declarada por el Build Package | 1 | 0,1 dB |
| Potencia de canal calibrada | Estadística | 0,015 dB | No declarada por el Build Package | 1 | 0,015 dB |
| Potencia de canal calibrada | Interpolación | 0,5 dB | No declarada por el Build Package | 1 | 0,5 dB |
| Potencia de canal calibrada | Deriva | 1,0 dB | No declarada por el Build Package | 1 | 1,0 dB |
| Potencia de canal calibrada | Linealidad | 0,2 dB | No declarada por el Build Package | 1 | 0,2 dB |
| Potencia de canal calibrada | Total (suma cuadrática) | — | — | — | 1,28 dB (k = 2) |
| Potencia de canal con DC adyacente | Total con +0,5 dB | 0,5 dB | No declarada por el Build Package | 1 | 1,37 dB (k = 2) |
| Detección de ocupación | Referencia de ruido | 0,503 dB | Gaussiana, según REF-001 §5.7 | 1 | 0,503 dB |
| Verificación de amplitud | Incertidumbre de medición | 0,59 dB | No declarada por el Build Package | 1 | 0,59 dB (k = 2) |
| Comparación entre sitios | Denominador de En | 1,99 dB | No declarada por el Build Package | 1 | 1,99 dB |

> El Build Package declara los componentes y la suma cuadrática; no declara la distribución ni la sensibilidad de cada componente. La incertidumbre expandida de la potencia calibrada es 1,28 dB (k = 2) y 1,37 dB para canales con bin de continua reemplazado. La verificación usa 0,59 dB y la comparación entre sitios usa 1,99 dB en el denominador de En.

---

## 6. Field Measurement Protocols

| Protocol ID | Applies To (Blocks) | Setup | Calibration | Execution |
|---|---|---|---|---|
| PROTO-001 | load_and_validate_site_config | `SYS-CFG-001` | Arranque, recarga o archivo ausente; tarjeta legible y time_status disponible. | No aplica. | Validar campos y referencia; publicar site_config y config_status; si falla, mantener la configuración anterior. |
| PROTO-002 | add_and_configure_another_node | `SYS-CFG-001`, `SYS-RPL-001` | Mismo paquete de software y mismas referencias de hardware. | No aplica. | Escribir site-config.json y referencia; comparar el hash antes y después; 0 líneas reescritas. |
| PROTO-003 | scan_cycle | `SYS-ACQ-001` | SDR abierto, ganancias aplicadas, configuración válida o por defecto, time_status disponible. | No aplica. | 3 capturas escalonadas a 10 Msps; publicar capture_block y acquisition_counters; inicio cada 6 s. |
| PROTO-004 | estimate_channel_power | `SYS-EST-001` | capture_block y acquisition_counters del barrido; estimator_control presente o corrección cero. | No aplica. | FFT 4 096/Hann/50 %, 105 bins; publicar channel_power_scan y spectrum_snapshot. |
| PROTO-005 | establish_amplitude_calibration | `SYS-CAL-001` | Nodo en configuración desplegada; antena desconectada; fuente trazable ≤0,5 dB y ≤1 ppm; terminación 50 Ω; cable medido; fuente distinta de la verificación. | Precalentar 30 min; medir piso de ruido, pérdida de cable, rango dinámico y 24 centros de canal. | Calcular K(f), verificar aceptación y escribir calibration_record y estimator_control (118 min). |
| PROTO-006 | apply_calibration_to_scan | `SYS-CAL-001` | calibration_record activo cargado o none. | No aplica. | potencia_dBm = potencia_dBFS + K(f_canal); retener si la calibración no se demuestra; publicar calibrated_channel_power y calibrated_spectrum. |
| PROTO-007 | classify_channels | `SYS-DET-001` | calibrated_channel_power, calibrated_spectrum y acquisition_counters; site_config activo. | No aplica. | Calcular e_k, umbrales, histéresis y regla de adyacencia; publicar occupancy_scan. |
| PROTO-008 | accumulate_duty_cycle | `SYS-DET-001` | occupancy_scan del barrido. | No aplica. | Contar estados por intervalo alineado a UTC; publicar duty_cycle_report. |
| PROTO-009 | verify_amplitude_correction | `SYS-VER-001` | Calibración activa; antena desconectada; referencia independiente ≤0,5 dB; terminación 50 Ω; reloj sincronizado. | 2 niveles × 6 canales; esperar 30 s; 5 barridos por punto; mediana. | Aprobar si las 12 diferencias son ≤1,0 dB y c ≤20 ppm; fijar verified_until; escribir validation_record (39 min). |
| PROTO-010 | compare_with_reference | `SYS-ASG-001` | config_status y station_assignment_reference disponibles; la referencia puede faltar. | No aplica. | Aplicar la tabla de decisión; publicar assignment_comparison_scan. |
| PROTO-011 | build_records | `SYS-REC-001` | Salidas del mismo scan_id: time, config, capture, counters, power, calibrated, occupancy y comparison. | No aplica. | Armar 1 encabezado, 199 registros de canal y 1 registro de salud; publicar. |
| PROTO-012 | update_history | `SYS-HIS-001` | Guardia de arranque: sin swap ni volcados de memoria. | No aplica. | Agregar a bins de 60 s y a la serie por barrido; nunca escribir a disco. |
| PROTO-013 | report_run_lifecycle | `SYS-REP-001` | Tarjeta montada en lectura/escritura; configuración cargada. | No aplica. | Abrir y cerrar corridas; segmentos cada 3 600 s; comprobar espacio cada 60 s. |
| PROTO-014 | write_scan_to_report | `SYS-REP-001` | Corrida y segmento abiertos. | No aplica. | Añadir las líneas del barrido y volcar a la tarjeta; ≤0,05 s. |
| PROTO-015 | evaluate_scan_alerts | `SYS-ALR-001` | Motor iniciado; site_config y config_status legibles. | No aplica. | Actualizar salud, calibración y unassigned-occupied; levantar o borrar alertas. |
| PROTO-016 | evaluate_history_alerts | `SYS-ALR-001` | Motor e historial en ejecución. | No aplica. | Cada minuto +10 s: crédito de silencio y deriva del piso; levantar o borrar alertas. |
| PROTO-017 | watch_health_points | `SYS-ALR-001`, `SYS-SUP-001` | Motor iniciado. | No aplica. | Cada 1 s: si no hay punto de salud en 18 s, alerta sensor_offline. |
| PROTO-018 | repeat_at_another_site | `SYS-RPL-001` | Sitio A con calibración válida, verificación aprobada e informe de 72 h; mismas referencias de hardware. | Mismo procedimiento de calibración y verificación en el sitio B. | Instalar, configurar, calibrar y correr 76 h en el sitio B; guardar cross_site_comparison. |
| PROTO-019 | compare_two_sites | `SYS-RPL-001` | Insumos del paso 4 de repeat_at_another_site. | Misma regla k = 2 en ambos sitios. | Calcular En y los tres criterios; escribir cross_site_comparison. |
| PROTO-020 | start_node | `SYS-SUP-001` | Alimentación y tarjeta legibles. | No aplica. | Arrancar consumidores antes que productores; recuperar corrida abierta; primer barrido completo ≤300 s. |
| PROTO-021 | supervise_processes | `SYS-SUP-001` | start_node paso 2. | No aplica. | Cada 1 s: contadores, escalera de 5 a 60 s, bucle y reinicio; publicar supervisor_status. |
| PROTO-022 | stop_node | `SYS-SUP-001` | Supervisor en ejecución. | No aplica. | Cerrar corrida y marcar parada ordenada; 40 s. |
| PROTO-023 | serve_view_request | `SYS-WEB-001` | Servicio iniciado con límites; fuentes legibles. | No aplica. | GET o HEAD en 8080; solo valores liberados; etiqueta de evidencia; ≤2 s. |
| PROTO-024 | serve_report_file | `SYS-WEB-001` | serve_view_request pasos 1 y 2; report_listing legible. | No aplica. | Enviar /reports/<run_id>/<file> sin cambios; todo usuario. |
| PROTO-025 | refresh_page | `SYS-WEB-001` | Página servida por el servicio web en el navegador. | No aplica. | Refrescar cada 6 s o 60 s según la vista; dibujar solo lo recibido; barra de alertas y etiqueta. |
| PROTO-026 | monitor_temperature | `SYS-RES-001` | Supervisor en ejecución. | No aplica. | Cada 10 s leer la temperatura y marcar la condición thermal; no detener nada. |
| PROTO-027 | apply_resource_limits | `SYS-RES-001` | Sistema operativo arriba. | No aplica. | Fijar memoria, procesador y prioridad por unidad y el sistema temporal en memoria antes de arrancar las unidades. |
| PROTO-028 | compute_availability | `SYS-RES-001` | Informe y bitácora de una corrida continua de 30 días. | No aplica. | Contar puntos disponibles según R-49; ≥95 % en 30 días. |
| PROTO-029 | run_field_validation | `SYS-RPL-001`, `SYS-RES-001` | Nodo calibrado y verificado; sitio con lista publicada; referencia independiente instalada. | Calibración y verificación vigentes. | Corrida continua ≥72 h; referencia independiente ≥6 h; planificar 76 h. |

---

## 7. Traceability

| Block ID | Parameter | Standard Ref | StRS Traces | Test Case |
|---|---|---|---|---|
| `SYS-HW-001` | Receptor HackRF One, placa Raspberry Pi 5 y referencia de frecuencia | — | `STK-REQ-054`, `STK-REQ-055`, `STK-REQ-056`, `STK-REQ-071`, `STK-REQ-050` | P-060, P-034, P-035, P-071, P-056 |
| `SYS-TIM-001` | Marca de tiempo UTC de cada barrido | — | `STK-REQ-028`, `STK-REQ-037` | P-030, P-044 |
| `SYS-CFG-001` | site-config.json y station_reference_file | — | `STK-REQ-016`, `STK-REQ-052`, `STK-REQ-070`, `STK-REQ-074`, `STK-REQ-075` | P-017, P-058, P-070, P-073, P-074 |
| `SYS-ACQ-001` | Muestras I/Q, ganancias, pérdidas y saturación por barrido | — | `STK-REQ-001`, `STK-REQ-002`, `STK-REQ-022`, `STK-REQ-023`, `STK-REQ-024`, `STK-REQ-025`, `STK-REQ-026`, `STK-REQ-050`, `STK-REQ-057`, `STK-REQ-069` | P-001, P-002, P-024, P-025, P-026, P-027 … |
| `SYS-EST-001` | Potencia integrada por canal en dBFS y espectro reducido | — | `STK-REQ-002`, `STK-REQ-050`, `STK-REQ-056`, `STK-REQ-069` | P-002, P-056, P-035, P-068 |
| `SYS-CAL-001` | Potencia calibrada en dBm, corrección K(f), incertidumbre y estado de validez | — | `STK-REQ-009`, `STK-REQ-010`, `STK-REQ-011`, `STK-REQ-012`, `STK-REQ-013`, `STK-REQ-014`, `STK-REQ-017`, `STK-REQ-018`, `STK-REQ-021`, `STK-REQ-029`, `STK-REQ-055`, `STK-REQ-056`, `STK-REQ-058` | P-010, P-011, P-012, P-013, P-014, P-015 … |
| `SYS-VER-001` | Diferencia de potencia calibrada contra referencia independiente y validez | — | `STK-REQ-019`, `STK-REQ-020`, `STK-REQ-021`, `STK-REQ-038`, `STK-REQ-060` | P-020, P-021, P-023, P-045, P-022 |
| `SYS-DET-001` | Exceso e_k = P_k − N_k, umbrales, histéresis y ciclo de trabajo | — | `STK-REQ-003`, `STK-REQ-004`, `STK-REQ-005`, `STK-REQ-006`, `STK-REQ-007`, `STK-REQ-008`, `STK-REQ-030`, `STK-REQ-059` | P-003, P-004, P-005, P-006, P-007, P-008 … |
| `SYS-ASG-001` | Resultado consistent, unassigned-occupied, assigned-free o indeterminate | — | `STK-REQ-014`, `STK-REQ-015`, `STK-REQ-016`, `STK-REQ-036` | P-015, P-016, P-017, P-043 |
| `SYS-REC-001` | Encabezado, 199 registros de canal y registro de salud por barrido | — | `STK-REQ-012`, `STK-REQ-013`, `STK-REQ-014`, `STK-REQ-024`, `STK-REQ-025`, `STK-REQ-027`, `STK-REQ-029`, `STK-REQ-030`, `STK-REQ-032`, `STK-REQ-033`, `STK-REQ-059` | P-013, P-014, P-015, P-026, P-027, P-029 … |
| `SYS-HIS-001` | Ventana de 744 h en bins de 60 s | — | `STK-REQ-008`, `STK-REQ-031`, `STK-REQ-039`, `STK-REQ-041`, `STK-REQ-043` | P-008, P-033, P-046, P-048, P-050 |
| `SYS-REP-001` | Carpeta reports/<run_id>, header.json, scans-<hora>.csv, intervals.csv y progress.json | — | `STK-REQ-030`, `STK-REQ-031`, `STK-REQ-059`, `STK-REQ-062`, `STK-REQ-070`, `STK-REQ-073`, `STK-REQ-074` | P-032, P-033, P-009, P-062, P-070, P-072 … |
| `SYS-ALR-001` | channel_silent, unexpected_occupancy, sensor_offline, calibration_not_demonstrated, noise_floor_drift | — | `STK-REQ-034`, `STK-REQ-035`, `STK-REQ-036`, `STK-REQ-037`, `STK-REQ-038`, `STK-REQ-039`, `STK-REQ-040`, `STK-REQ-046` | P-041, P-042, P-043, P-044, P-045, P-046 … |
| `SYS-WEB-001` | Vistas /power, /spectrum, /stations, /status, /alerts y descarga de informes | — | `STK-REQ-032`, `STK-REQ-033`, `STK-REQ-041`, `STK-REQ-042`, `STK-REQ-043`, `STK-REQ-044`, `STK-REQ-045`, `STK-REQ-046`, `STK-REQ-047`, `STK-REQ-067` | P-038, P-039, P-048, P-049, P-050, P-051 … |
| `SYS-SUP-001` | Contadores de progreso, escalera de reinicios y estado del nodo | — | `STK-REQ-021`, `STK-REQ-024`, `STK-REQ-025`, `STK-REQ-026`, `STK-REQ-027`, `STK-REQ-037`, `STK-REQ-048`, `STK-REQ-049` | P-023, P-026, P-027, P-028, P-029, P-044 … |
| `SYS-RES-001` | Tiempo por barrido, memoria, procesador, almacenamiento, energía y disponibilidad | — | `STK-REQ-001`, `STK-REQ-037`, `STK-REQ-048`, `STK-REQ-049`, `STK-REQ-057`, `STK-REQ-061`, `STK-REQ-066`, `STK-REQ-072`, `STK-REQ-073` | P-001, P-044, P-054, P-055, P-036, P-061 … |
| `SYS-RPL-001` | En = /δ/ / sqrt(W_A² + W_B²), 12 puntos y 60 observaciones vacantes | — | `STK-REQ-051`, `STK-REQ-052`, `STK-REQ-061` | P-057, P-058, P-061 |
| `SYS-SEC-001` | Control de acceso, etiqueta de evidencia y vocabulario prohibido | — | `STK-REQ-032`, `STK-REQ-033`, `STK-REQ-047`, `STK-REQ-067` | P-038, P-039, P-040, P-067 |
| `SYS-IPC-001` | Mensajes JSON UTF-8 por sockets Unix de flujo con longitud de 4 bytes | — | `STK-REQ-027`, `STK-REQ-031`, `STK-REQ-052`, `STK-REQ-057` | P-029, P-033, P-058, P-036 |
| `SYS-DAT-001` | 33 esquemas JSON del Anexo B y archivos del nodo | — | `STK-REQ-018`, `STK-REQ-031`, `STK-REQ-052`, `STK-REQ-060`, `STK-REQ-062`, `STK-REQ-070`, `STK-REQ-073`, `STK-REQ-074`, `STK-REQ-075` | P-019, P-033, P-058, P-022, P-062, P-070 … |
| `SYS-ENV-001` | Alimentación 120 V/60 Hz, temperatura, IP65, interiores/exteriores y costo | IEC 60529 | `STK-REQ-053`, `STK-REQ-054`, `STK-REQ-063`, `STK-REQ-064`, `STK-REQ-065`, `STK-REQ-066`, `STK-REQ-071`, `STK-REQ-072` | P-059, P-060, P-063, P-064, P-065, P-066 … |
