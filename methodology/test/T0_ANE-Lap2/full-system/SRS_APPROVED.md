# PROYECTO: Sistema de Monitoreo Espectral — Fase 2 Optimización

## Especificación de Requisitos del Sistema (SRS)

> **Plantilla basada en:** IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering*, adaptada con elementos de ETSI EN 303 645 (Cyber Security for IoT) y estructura determinista para validación automatizada por IA.
>
> **Versión plantilla:** 1.0.0  
> **Fecha creación:** 2026-10-13  
> **Última modificación:** 2026-10-13  
> **Estado documento:** `EN_REVISIÓN`

---

## Metadatos del Documento

| Campo                  | Valor                                                      |
|------------------------|------------------------------------------------------------|
| **ID Documento**       | `SRS-ANE-001`                                              |
| **Proyecto**           | Roadmap Fase 2 — Optimización Sistema de Monitoreo Espectral |
| **Organización**       | Agencia Nacional del Espectro (ANE) — Colombia             |
| **Versión**            | 0.1.0                                                      |
| **Clasificación**      | `INTERNO`                                                  |
| **Autor(es)**          | _Por definir_                                              |
| **Revisor(es)**        | _Por definir_                                              |
| **Aprobador(es)**      | _Por definir_                                              |

### Control de Cambios

| Versión | Fecha      | Autor             | Descripción del Cambio                                  |
|---------|------------|-------------------|----------------------------------------------------------|
| 0.1.0   | 2026-10-13 | Generación asistida IA | Extracción de requisitos aprobados (verde) desde roadmap Excel |

---

## 1. Introducción

### 1.1 Propósito

Este documento especifica los requisitos aprobados para la Fase 2 de optimización del Sistema de Monitoreo Espectral de la ANE. Incluye únicamente los requisitos que fueron marcados como aprobados (color verde) en el roadmap de funcionalidades, excluyendo ítems en discusión, pospuestos o descartados.

### 1.2 Alcance del Sistema

El sistema es una plataforma de monitoreo del espectro radioeléctrico compuesta por sensores remotos basados en SDR (HackRF One sobre Raspberry Pi), una capa cloud de gestión y visualización, y herramientas de análisis espectral, cumplimiento normativo e inteligencia artificial. La Fase 2 optimiza el sistema existente (Fase 1) ampliando capacidades de análisis, conectividad, confiabilidad y cumplimiento de estándares internacionales.

**El sistema NO incluye en esta fase:** localización de emisores (DF/TDOA), medición de variables exógenas (humedad/temperatura), compensación Doppler, captura IQ avanzada, integración SIG/ArcGIS, ni detección de fallos en tecnologías específicas (LTE, 5G, DAB).

### 1.3 Definiciones, Acrónimos y Abreviaciones

| Término    | Definición                                                                           |
|------------|--------------------------------------------------------------------------------------|
| ANE        | Agencia Nacional del Espectro (Colombia)                                             |
| SDR        | Software Defined Radio — Radio Definida por Software                                 |
| RBW        | Resolution Bandwidth — Ancho de banda de resolución                                  |
| VBW        | Video Bandwidth — Ancho de banda de video                                            |
| DANL       | Displayed Average Noise Level — Nivel promedio de ruido mostrado                     |
| RDS        | Radio Data System — Sistema de datos de radio FM                                     |
| NTP        | Network Time Protocol — Protocolo de tiempo de red                                   |
| EMC        | Electromagnetic Compatibility — Compatibilidad electromagnética                      |
| TDOA       | Time Difference of Arrival                                                           |
| DF         | Direction Finding — Radiogoniometría                                                 |
| OBW        | Occupied Bandwidth — Ancho de banda ocupado                                          |
| RTT        | Round Trip Time — Tiempo de ida y vuelta de paquete IP                               |
| ITU-R      | International Telecommunication Union — Radiocommunication Sector                    |
| CEPT       | European Conference of Postal and Telecommunications Administrations                 |
| SRS        | System Requirements Specification                                                    |
| HIL        | Hardware In the Loop                                                                 |
| HITL       | Human In the Loop                                                                    |
| ppm        | Partes por millón                                                                    |
| SAW        | Surface Acoustic Wave (tipo de filtro)                                               |
| AP         | Access Point                                                                         |
| TLS/SSL    | Transport Layer Security / Secure Sockets Layer                                      |

### 1.4 Referencias

| ID Ref     | Documento                                                              | Versión / Fecha     |
|------------|------------------------------------------------------------------------|---------------------|
| `REF-001`  | ITU-R SM.1537 — Automatización y requisitos de estaciones de monitoreo | Vigente             |
| `REF-002`  | ITU-R SM.1138 — Sensibilidad y selectividad de monitoreo              | Vigente             |
| `REF-003`  | ITU-T K.113 — Medición de campo eléctrico en entornos urbanos         | Vigente             |
| `REF-004`  | ITU-T K.100 — Evaluación de exposición humana a campos electromagnéticos | Vigente          |
| `REF-005`  | CEPT/ERC/REC 70-03 — Uso compartido de espectro sin licencia          | Vigente             |
| `REF-006`  | ECC Report 260 — Protección para servicios SRD                        | Vigente             |
| `REF-007`  | IEEE/ISO/IEC 29148:2018 — Requirements engineering                    | 2018                |
| `REF-008`  | ETSI EN 303 645 — Cyber Security for Consumer IoT                     | V2.1.1 (2020-06)    |

### 1.5 Visión General del Documento

La sección 3 contiene todos los requisitos específicos aprobados, organizados por categoría funcional del sistema. La sección 4 detalla interfaces externas. La sección 5 agrupa requisitos no funcionales transversales. La sección 6 presenta la matriz de trazabilidad. La sección 7 define reglas de validación estructural para procesamiento automatizado.

---

## 2. Descripción General del Sistema

### 2.1 Perspectiva del Producto

Este sistema es una evolución (Fase 2) de la plataforma de monitoreo espectral existente de la ANE. Extiende las capacidades de sensores on-site basados en HackRF One + Raspberry Pi, agrega un componente cloud para gestión centralizada, y amplía el rango de análisis espectral, la conectividad, y el cumplimiento de estándares internacionales de la ITU.

#### 2.1.1 Diagrama de Contexto

```
┌─────────────┐      4G/5G/WiFi/ETH      ┌──────────────────┐
│  Sensor SDR  │◄────────────────────────►│   Cloud Backend   │
│  (HackRF +   │    Datos espectro,       │  (FastAPI/Node +  │
│   RPi)       │    telemetría, GPS       │   Docker)         │
└──────┬───────┘                          └────────┬──────────┘
       │                                           │
  ┌────┴────┐                                ┌─────┴──────┐
  │ Antenas  │                                │  Frontend   │
  │ GPS      │                                │  (React/Vue │
  │ Batería  │                                │   + WebGL)  │
  │ 4G/WiFi  │                                └─────┬──────┘
  └─────────┘                                       │
                                               ┌────┴─────┐
                                               │ Operador  │
                                               │ ANE       │
                                               └──────────┘
```

### 2.2 Funciones del Producto

El sistema proporciona: monitoreo espectral en tiempo real (1 MHz–6 GHz), detección de emisiones no autorizadas, medición de parámetros de señal (potencia, ancho de banda, modulación), demodulación FM/AM, cumplimiento normativo automatizado, gestión remota de sensores, almacenamiento forense, y generación de reportes.

### 2.3 Características de los Usuarios

| Tipo de Usuario       | Descripción                                    | Nivel Técnico |
|-----------------------|------------------------------------------------|---------------|
| Ingeniero de espectro | Configura y analiza mediciones espectrales      | `EXPERTO`     |
| Operador de monitoreo | Supervisa alertas y estado de sensores          | `TÉCNICO`     |
| Administrador TI      | Gestiona infraestructura cloud y conectividad   | `TÉCNICO`     |
| Directivo ANE         | Consulta reportes e indicadores                 | `BÁSICO`      |

### 2.4 Restricciones

- Hardware base: HackRF One como SDR primario (limitaciones de DANL y rango dinámico inherentes).
- Plataforma embebida: Raspberry Pi (bajo consumo, limitaciones de procesamiento).
- Conectividad: dependencia de cobertura 4G/5G de operadores colombianos.
- Regulatoria: cumplimiento obligatorio de recomendaciones ITU-R serie SM.

### 2.5 Supuestos y Dependencias

- La ANE provee SIM Cards de datos para conectividad móvil.
- Los sensores se despliegan en ubicaciones con alimentación eléctrica o donde la solución solar es viable.
- El backend cloud dispone de infraestructura Docker con plan de crecimiento definido.
- Las bases de datos de emisiones autorizadas de la ANE están disponibles para integración.

---

## 3. Requisitos Específicos

---

### 3.1 Análisis Espectral — Arquitectura y Seguridad

#### 3.1.1 Seguridad de la Información

---

**`ANAL-SEG-001` — Comunicaciones cifradas TLS/SSL**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ETSI EN 303 645 §5.1; `REF-008`                          |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE utilizar protocolos TLS/SSL con certificado válido en todas las comunicaciones entre sensores y backend, y entre backend y frontend. No DEBE transmitir datos en texto plano (plain text).

**Criterios de Aceptación:**

1. [ ] Todas las conexiones HTTP utilizan HTTPS con TLS ≥ 1.2.
2. [ ] Los certificados son emitidos por una CA reconocida o por la PKI interna de la ANE.
3. [ ] Una prueba de interceptación (MITM) no revela datos en claro.

**Notas:**  
Certificado válido requerido. Sin excepciones para entornos de desarrollo en producción.

---

#### 3.1.2 Compatibilidad Electromagnética

---

**`ANAL-EMC-001` — Optimización EMC del sensor**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | Sí (gasket RF)                                            |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE incorporar ajustes y filtrado en la recepción del sensor para evitar que señales espurias generadas por la propia electrónica aparezcan en los resultados de medición. Los ajustes EMC DEBEN ser ejecutables sobre la plataforma actual.

**Criterios de Aceptación:**

1. [ ] Las emisiones espurias internas del sensor son al menos 10 dB por debajo del piso de ruido operativo.
2. [ ] Se implementa blindaje RF (gasket) entre módulos internos.
3. [ ] Medición comparativa antes/después demuestra reducción de artefactos EMC.

**Notas:**  
Incluye implementación de gasket RF. Responsable análisis: Bernardo.

---

#### 3.1.3 Rango Espectral

---

**`ANAL-RNG-001` — Ampliación de rango de frecuencia**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No (HackRF One soporta el rango)                         |
| **Estándar(es)**       | ITU-R SM.1537; `REF-001`                                  |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE ampliar el rango de frecuencia del sensor para capturar emisiones desde 1 MHz hasta 6 GHz (o hasta el límite del hardware SDR).

**Criterios de Aceptación:**

1. [ ] El sistema recibe y procesa señales en el rango 1 MHz – 6 GHz.
2. [ ] La sensibilidad a 1 MHz es verificable con generador de señales calibrado.
3. [ ] La sensibilidad a 6 GHz es verificable con generador de señales calibrado.

**Notas:**  
El límite superior puede depender del modelo de antena conectada. Requiere antena específica para bandas bajas (AM desde 1 MHz).

---

**`ANAL-RNG-002` — Ancho de banda de monitoreo en tiempo real**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE tener capacidad de monitoreo en tiempo real con un ancho de banda mínimo de 20 MHz. DEBE permitir configuración manual del ancho de banda entre 6 MHz y 20 MHz, y modo automático fijo en 20 MHz.

**Criterios de Aceptación:**

1. [ ] El span de monitoreo puede configurarse entre 6 MHz y 20 MHz en pasos discretos.
2. [ ] En modo automático, el span se fija en 20 MHz.
3. [ ] La visualización en tiempo real se actualiza con latencia ≤ 1 segundo.

**Notas:**  
Manual entre 6 y 20 MHz; automático en 20 MHz.

---

### 3.2 Análisis Espectral — Parametrización

#### 3.2.1 Parámetros de Frecuencia y Resolución

---

**`ANAL-PAR-001` — Rango de frecuencia parametrizable**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-RNG-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE permitir al usuario ingresar rangos de frecuencia a analizar dentro del rango espectral disponible (span IF).

**Criterios de Aceptación:**

1. [ ] El usuario puede definir frecuencia central y span, o frecuencia inicial y final.
2. [ ] El sistema valida que el rango solicitado esté dentro de los límites del hardware.
3. [ ] Los cambios de rango se aplican en tiempo real sin reinicio del sistema.

**Notas:**  
Span IF = Rango de frecuencia en pantalla.

---

**`ANAL-PAR-002` — Configuración de RBW**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-PAR-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE permitir configurar el ancho de banda de resolución (RBW) con rango definido (span IF = RBW).

**Criterios de Aceptación:**

1. [ ] El RBW es configurable por el usuario en un conjunto de valores discretos.
2. [ ] Los rangos de RBW disponibles están documentados (≥ 6 valores).
3. [ ] El cambio de RBW actualiza la visualización en tiempo real.

**Notas:**  
Definir rangos de RBW ≥ 6 opciones.

---

**`ANAL-PAR-003` — Pasos de resolución de frecuencia**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-PAR-002`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE ofrecer pasos de cambio de resolución de 500 Hz con resolución mínima de 10 Hz.

**Criterios de Aceptación:**

1. [ ] El step de frecuencia es configurable en pasos de 500 Hz.
2. [ ] La resolución mínima alcanzable es 10 Hz.
3. [ ] La precisión del step se verifica contra generador de señales.

**Notas:**  
Ampliar gama de resoluciones en fases posteriores según demanda.

---

**`ANAL-PAR-004` — Configuración de VBW**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | Sí (filtros)                                              |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-PAR-002`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE implementar filtros de Video Bandwidth (VBW) adaptados al tipo de análisis (fino o promedio), para suavizar la señal visualizada después del procesamiento RBW.

**Criterios de Aceptación:**

1. [ ] El VBW es configurable independientemente del RBW.
2. [ ] Filtros disponibles para análisis fino y promediado.
3. [ ] La visualización muestra diferencia perceptible entre modos de filtrado.

**Notas:**  
Filtrado posterior a RBW para suavizar señal visualizada.

---

#### 3.2.2 Ubicación y Unidades

---

**`ANAL-PAR-005` — Ingreso manual de coordenadas GPS**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE permitir el ingreso manual de coordenadas de ubicación del sensor cuando el GPS automático no esté disponible o se requiera corrección.

**Criterios de Aceptación:**

1. [ ] El usuario puede ingresar latitud y longitud manualmente.
2. [ ] Las coordenadas manuales se asocian a las mediciones realizadas.
3. [ ] El sistema indica visualmente si la ubicación es GPS automática o manual.

**Notas:**  
—

---

**`ANAL-PAR-006` — Parametrización de unidades de medida**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE permitir la selección y conversión entre unidades de medida: Frecuencia (Hz, kHz, MHz, GHz), Potencia (dBm, dBmV, dBµV, V, W) y Campo eléctrico y densidad de potencia (V/m, W/m², dBµV/m).

**Criterios de Aceptación:**

1. [ ] Todas las unidades listadas están disponibles en la interfaz de configuración.
2. [ ] La conversión entre unidades es matemáticamente correcta (error < 0.01 dB).
3. [ ] El cambio de unidad actualiza todas las visualizaciones simultáneamente.

**Notas:**  
—

---

#### 3.2.3 Umbrales y Detección

---

**`ANAL-PAR-007` — Umbrales de análisis y detección**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE permitir parametrizar umbrales de detección e integrar algoritmos con capacidad para distinguir entre piso de ruido y ocupación de señales, con el fin de definir la porción del espectro de interés.

**Criterios de Aceptación:**

1. [ ] El usuario puede definir un umbral de potencia en dBm para detección de señales.
2. [ ] El algoritmo distingue automáticamente piso de ruido de señales activas.
3. [ ] Las señales por encima del umbral se destacan visualmente en la interfaz.

**Notas:**  
Parametrizar umbral y con base en él, definir porción del espectro de interés.

---

### 3.3 Análisis Espectral — Medición y Visualización

#### 3.3.1 Indicadores y Trazas

---

**`ANAL-MED-001` — Indicadores espectrales (trazas)**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1537; `REF-001`                                  |
| **Dependencias**       | `ANAL-PAR-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE presentar trazas espectrales: máxima (max hold), mínima (min hold), promedio (average), y modos de detección RMS, pico y promedio.

**Criterios de Aceptación:**

1. [ ] La traza máxima retiene el valor más alto por bin de frecuencia.
2. [ ] La traza mínima retiene el valor más bajo por bin de frecuencia.
3. [ ] La traza promedio calcula media aritmética sobre N barridos (N configurable).
4. [ ] Los modos de detección RMS, pico y promedio son seleccionables.

**Notas:**  
—

---

**`ANAL-MED-002` — Marcadores espectrales**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-MED-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE agregar marcadores individuales y tipo delta sobre la medición espectral, con un mínimo de cuatro marcadores simultáneos.

**Criterios de Aceptación:**

1. [ ] Se pueden colocar al menos 4 marcadores simultáneamente.
2. [ ] Cada marcador muestra frecuencia y potencia.
3. [ ] Los marcadores delta muestran ΔPotencia y ΔFrecuencia entre dos puntos.

**Notas:**  
Cada marcador muestra: freq, power. Delta muestra: ΔPower y ΔFreq.

---

#### 3.3.2 Mediciones de Señal

---

**`ANAL-MED-003` — Medición de ancho de banda ocupado**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1537; `REF-001`                                  |
| **Dependencias**       | `ANAL-MED-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE medir el ancho de banda ocupado (OBW) mediante los métodos de –X dB y 99%.

**Criterios de Aceptación:**

1. [ ] Método –X dB: mide el ancho donde la señal cae X dB por debajo del pico (X configurable).
2. [ ] Método 99%: mide el espectro que contiene el 99% de la potencia de la señal.
3. [ ] Los resultados se muestran en la unidad de frecuencia seleccionada.

**Notas:**  
OBW = espectro que contiene el 99% de la señal. –X dB donde la señal cae un X por debajo del pico.

---

**`ANAL-MED-004` — Potencia de canal (hasta 20 MHz)**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-RNG-002`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE realizar mediciones de potencia de canal para emisiones de hasta 20 MHz de ancho de banda.

**Criterios de Aceptación:**

1. [ ] La medición de potencia de canal es seleccionable por el usuario.
2. [ ] El ancho del canal medido es configurable hasta 20 MHz.
3. [ ] El resultado se expresa en las unidades de potencia seleccionadas.

**Notas:**  
Mediciones de potencia de canal limitadas a 20 MHz en esta fase. Más de 20 MHz en fase posterior.

---

#### 3.3.3 Radiodifusión Sonora

---

**`ANAL-MED-005` — Lectura de RDS en FM**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE decodificar y presentar la información del Radio Data System (RDS) en señales FM.

**Criterios de Aceptación:**

1. [ ] El sistema decodifica campos RDS básicos (PI, PS, RT).
2. [ ] La información RDS se muestra en la interfaz junto a la señal FM.

**Notas:**  
Requiere que la ANE confirme la funcionalidad (columna ANE: SI).

---

**`ANAL-MED-006` — Demodulación y escucha FM y AM**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-RNG-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE demodular y permitir la escucha de señales FM y AM en tiempo real.

**Criterios de Aceptación:**

1. [ ] El audio FM se demodula con calidad audible.
2. [ ] El audio AM se demodula con calidad audible (desde 1 MHz con HackRF One).
3. [ ] La escucha está disponible tanto local como remotamente vía streaming.

**Notas:**  
AM solo se puede con HackRF One desde 1 MHz en adelante; requiere antena adicional.

---

**`ANAL-MED-007` — Medición de modulación AM y FM**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-MED-006`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE medir directamente la profundidad de modulación AM y la excursión de frecuencia FM.

**Criterios de Aceptación:**

1. [ ] La profundidad de modulación AM se presenta como porcentaje.
2. [ ] La excursión de frecuencia FM se presenta en kHz.
3. [ ] Los valores se actualizan en tiempo real durante la demodulación.

**Notas:**  
AM solo desde 1 MHz en adelante con HackRF One; requiere antena adicional.

---

### 3.4 Cumplimiento Normativo — Detección y Alertas

#### 3.4.1 Emisiones No Autorizadas

---

**`NORM-DET-001` — Detección de emisiones no autorizadas**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1537; `REF-001`                                  |
| **Dependencias**       | `ANAL-PAR-007`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE detectar y alertar automáticamente sobre emisiones no autorizadas comparando con la base de datos de la entidad.

**Criterios de Aceptación:**

1. [ ] El sistema compara emisiones detectadas contra la BD de emisiones autorizadas de la ANE.
2. [ ] Genera alerta automática cuando detecta una emisión no registrada.
3. [ ] La alerta incluye frecuencia, potencia, timestamp y ubicación del sensor.

**Notas:**  
Requiere integración con BD de la ANE.

---

**`NORM-DET-002` — Incumplimiento de ancho de banda autorizado**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1537; `REF-001`                                  |
| **Dependencias**       | `NORM-DET-001`, `ANAL-MED-003`                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE detectar y alertar cuando una emisión autorizada exceda los límites de ancho de banda permitidos según la BD de la entidad.

**Criterios de Aceptación:**

1. [ ] El sistema mide el OBW de emisiones autorizadas y compara contra límites de la BD.
2. [ ] Genera alerta cuando el ancho de banda medido excede el autorizado.
3. [ ] El reporte incluye el ancho de banda medido vs. el autorizado.

**Notas:**  
Requiere BD de la ANE con límites de ancho de banda por emisión.

---

**`NORM-DET-003` — Incumplimiento de potencia autorizada**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1537; `REF-001`                                  |
| **Dependencias**       | `NORM-DET-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE detectar y alertar cuando una emisión autorizada exceda los límites de potencia autorizados/legales.

**Criterios de Aceptación:**

1. [ ] El sistema mide la potencia de emisiones autorizadas y compara contra límites de la BD.
2. [ ] Genera alerta cuando la potencia medida excede la autorizada.
3. [ ] El margen de tolerancia de la comparación es configurable.

**Notas:**  
Requiere BD de la ANE con límites de potencia por emisión.

---

#### 3.4.2 Servicios Adicionales AM/FM/Aeronáuticos

---

**`NORM-SRV-001` — Cuantificación de modulación AM y FM (cumplimiento)**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-MED-007`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE cuantificar la profundidad de modulación AM y la excursión de frecuencia FM para verificación de cumplimiento normativo en servicios de radiodifusión.

**Criterios de Aceptación:**

1. [ ] Los valores medidos se comparan contra límites regulatorios configurables.
2. [ ] El sistema genera alerta cuando los parámetros exceden los límites.

**Notas:**  
AM solo desde 1 MHz con HackRF One; requiere antena adicional.

---

**`NORM-SRV-002` — Extracción de audio para verificación**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-MED-006`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE demodular y extraer audio de señales FM y AM para uso en verificación de cumplimiento y análisis forense.

**Criterios de Aceptación:**

1. [ ] El audio extraído se puede almacenar en formato estándar (WAV o MP3).
2. [ ] El archivo de audio se asocia a metadatos de la medición (frecuencia, timestamp, ubicación).

**Notas:**  
AM solo desde 1 MHz con HackRF One; requiere antena adicional.

---

#### 3.4.3 Verificación de Parámetros de Señal

---

**`NORM-VER-001` — Detección de intermodulaciones**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-MED-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE detectar intermodulaciones, incluyendo identificación de presuntas intermodulaciones en AM, FM y banda de servicio móvil aeronáutico (108 MHz–137 MHz), y verificación de frecuencia intermedia (IF).

**Criterios de Aceptación:**

1. [ ] El sistema calcula productos de intermodulación de orden 2 y 3 para emisiones detectadas.
2. [ ] Las intermodulaciones presuntas se marcan en la visualización espectral.
3. [ ] La verificación IF se realiza automáticamente.

**Notas:**  
Cubre AM, FM y banda aeronáutica (108–137 MHz). ANE confirma (SI).

---

**`NORM-VER-002` — Detección de interferencias**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-PAR-007`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE detectar interferencias definidas como señales que exceden en más de 3 dB el nivel promedio del canal o banda.

**Criterios de Aceptación:**

1. [ ] Se detectan señales >3 dB sobre el nivel promedio como posibles interferencias.
2. [ ] Se genera alerta automática con datos de frecuencia, potencia y duración.
3. [ ] El control remoto permite verificación en tiempo real.

**Notas:**  
Umbral de detección: >3 dB del nivel promedio. ANE confirma (SI).

---

### 3.5 Herramientas de Gestión

#### 3.5.1 Monitoreo de Infraestructura

---

**`GEST-MON-001` — Monitoreo de sensores y estaciones remotas**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE medir y alertar sobre variables de salud de sensores (disco, RAM, CPU, temperatura) usando las variables disponibles en el sistema operativo.

**Criterios de Aceptación:**

1. [ ] Se monitorean al menos: uso de disco, RAM, CPU y temperatura.
2. [ ] Se generan alertas cuando las variables superan umbrales configurables.
3. [ ] El estado de cada sensor se visualiza en un dashboard centralizado.

**Notas:**  
—

---

**`GEST-MON-002` — Monitoreo de red y conectividad**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE medir y alertar sobre la calidad de conexión IP, incluyendo RTT, estado de canal (Alive/Not Alive), ancho de banda disponible y pérdida de paquetes.

**Criterios de Aceptación:**

1. [ ] Se mide RTT periódicamente (intervalo configurable).
2. [ ] Se detecta estado Alive/Not Alive de cada sensor.
3. [ ] Se genera alerta cuando RTT o pérdida de paquetes exceden umbrales.

**Notas:**  
—

---

#### 3.5.2 Programación y Reportes

---

**`GEST-PRG-001` — Escaneo programado de espectro**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1537; `REF-001`                                  |
| **Dependencias**       | `ANAL-PAR-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE permitir programar escaneos parametrizados de espectro (frecuencia, RBW, VBW, duración) y permitir su posterior revisión.

**Criterios de Aceptación:**

1. [ ] El usuario puede programar escaneos con parámetros definidos (frecuencia, RBW, VBW, duración, repetición).
2. [ ] Los resultados de escaneos programados se almacenan para revisión posterior.
3. [ ] Los escaneos se ejecutan en la hora programada con tolerancia ≤ 1 minuto.

**Notas:**  
ANE confirma (SI).

---

**`GEST-REP-001` — Generación automática de informes**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-MED-001`, `NORM-DET-001`                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE generar automáticamente informes y reportes de administración del espectro usando las variables de monitoreo definidas, con formatos específicos definidos por la entidad.

**Criterios de Aceptación:**

1. [ ] Al menos un formato de reporte está implementado según especificaciones de la ANE.
2. [ ] Los reportes incluyen datos de espectro, alertas, ubicación y timestamp.
3. [ ] Los reportes se generan bajo demanda y/o automáticamente en horarios configurados.

**Notas:**  
Más formatos de reportes en fases subsiguientes.

---

### 3.6 Análisis Forense y Almacenamiento

---

**`FORN-ALM-001` — Almacenamiento histórico para análisis forense**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1537; `REF-001`                                  |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE proveer almacenamiento histórico local y centralizado para análisis forense, sancionatorio o histórico, incluyendo datos de espectro con timestamp y ubicación.

**Criterios de Aceptación:**

1. [ ] Los datos de monitoreo se almacenan con timestamp y coordenadas GPS.
2. [ ] Los datos históricos son consultables por rango de fecha, frecuencia y ubicación.
3. [ ] La integridad de los datos almacenados es verificable.

**Notas:**  
Con hardware actual. ANE confirma (SI).

---

**`FORN-ALM-002` — Almacenamiento en servidores ANE**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `FORN-ALM-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE almacenar resultados de monitoreo programado en servidores locales (en tierra) de la ANE, con capacidad para conservar archivos JSON y opcionalmente archivos CS8 (IQ raw).

**Criterios de Aceptación:**

1. [ ] Los resultados se transmiten y almacenan en servidores de la ANE.
2. [ ] El formato JSON está documentado y es parseable.
3. [ ] La decisión de almacenar CS8 es configurable según recursos disponibles.

**Notas:**  
ANE define según recursos si almacenan solo JSON o también archivos CS8.

---

**`FORN-ALM-003` — Almacenamiento en sensores**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | Sí                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE adicionar espacio de almacenamiento a los sensores para permitir almacenar archivos CS8 para posterior uso como evidencia forense.

**Criterios de Aceptación:**

1. [ ] Los sensores cuentan con almacenamiento adicional accesible.
2. [ ] Los archivos CS8 se almacenan con metadatos (timestamp, frecuencia, coordenadas).
3. [ ] El almacenamiento local es accesible remotamente para descarga.

**Notas:**  
Incluir valor de la solución de almacenamiento a usar.

---

### 3.7 Conectividad y Soporte Remoto

#### 3.7.1 Interfaces de Red

---

**`CONN-RED-001` — Módulo 4G/5G**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | Sí                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE agregar o cambiar el módulo de conexión móvil para soportar SIM Card de datos entregada por la ANE, con suministro de datos multioperador (no limitado a un solo operador).

**Criterios de Aceptación:**

1. [ ] El módulo soporta redes 4G y 5G.
2. [ ] Funciona con SIM Cards de al menos 2 operadores colombianos.
3. [ ] La conexión se establece automáticamente al encender el sensor.

**Notas:**  
Actualmente usa módulo 4.5G limitado a Movistar. Nuevo módulo debe ser multioperador.

---

**`CONN-RED-002` — Conexión WiFi**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `SHOULD`                                                  |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE habilitar conexión WiFi en el sensor, configurable vía cable Ethernet.

**Criterios de Aceptación:**

1. [ ] El sensor se conecta a redes WiFi configuradas.
2. [ ] La configuración WiFi se realiza inicialmente por cable Ethernet.
3. [ ] La conexión WiFi se usa como canal alternativo de comunicación.

**Notas:**  
La configuración inicial debe ser vía cable Ethernet.

---

**`CONN-RED-003` — Puerto Ethernet accesible**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `INSPECCIÓN`                                              |
| **Hardware nuevo**     | Sí                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE proveer acceso a un puerto Ethernet de fácil acceso, sin requerir apertura del equipo.

**Criterios de Aceptación:**

1. [ ] El puerto Ethernet es accesible externamente sin herramientas.
2. [ ] El puerto soporta velocidad mínima de 100 Mbps.

**Notas:**  
Actualmente requiere apertura del equipo para acceder al puerto. ANE confirma (SI).

---

**`CONN-RED-004` — Auto-routing de red**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `CONN-RED-001`, `CONN-RED-002`, `CONN-RED-003`            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE implementar un sistema de conexión y enrutamiento a red IP automático, usando los distintos canales disponibles (un esquema de failover/prioridad entre 4G/5G, WiFi y Ethernet).

**Criterios de Aceptación:**

1. [ ] El sistema selecciona automáticamente el canal de red disponible con mayor prioridad.
2. [ ] El failover entre canales ocurre sin intervención manual.
3. [ ] El orden de prioridad es configurable.

**Notas:**  
—

---

#### 3.7.2 Soporte y GPS

---

**`CONN-SOP-001` — Acceso remoto y actualización de software**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `CONN-RED-004`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE permitir acceso remoto IP a los sensores y actualización de software OTA (Over The Air).

**Criterios de Aceptación:**

1. [ ] Se puede acceder remotamente al sensor vía SSH o equivalente seguro.
2. [ ] La actualización de software se realiza sin acceso físico al sensor.
3. [ ] El proceso de actualización incluye rollback automático en caso de fallo.

**Notas:**  
ANE confirma (SI).

---

**`CONN-GPS-001` — Redundancia de ubicación GPS**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-PAR-005`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE seguir enviando ubicación por GPS independientemente de la parametrización manual, proporcionando redundancia.

**Criterios de Aceptación:**

1. [ ] El GPS continúa reportando ubicación automática incluso cuando hay coordenadas manuales configuradas.
2. [ ] Ambas fuentes de ubicación se almacenan en los registros de medición.

**Notas:**  
—

---

**`CONN-GPS-002` — Exactitud GPS**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | Sí                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE contar con precisión horizontal GPS aproximada de 3 metros a cielo abierto.

**Criterios de Aceptación:**

1. [ ] Precisión horizontal ≤ 3 m (CEP 50%) en condiciones de cielo abierto.
2. [ ] La precisión se verifica contra receptor GPS de referencia.

**Notas:**  
Puede requerir cambio de hardware GPS.

---

### 3.8 Antenas y Medición de Radiación

#### 3.8.1 Antenas

---

**`ANTE-ANT-001` — Nuevas antenas para bandas específicas**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `INSPECCIÓN`                                              |
| **Hardware nuevo**     | Sí                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-RNG-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE incorporar antenas específicas para recepción de señales con el fin de optimizar la visualización de la señal en diferentes bandas.

**Criterios de Aceptación:**

1. [ ] Antena específica para TDT.
2. [ ] Verificación de antena para frecuencias > 2 GHz (telefonía móvil downlink).
3. [ ] Cada antena tiene factor de antena (AF) documentado y calibrado.

**Notas:**  
Bandas prioritarias: 1. TDT, 2. Verificar > 2 GHz telefonía móvil (downlink), 3. Evaluar antenas adicionales según necesidad.

---

**`ANTE-ANT-002` — Antena activa para radiación no ionizante**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | Sí                                                        |
| **Estándar(es)**       | ITU-T K.113, K.100; `REF-003`, `REF-004`                  |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE incorporar una antena activa con rango de frecuencia hasta 6 GHz, con filtro SAW, respuesta plana y factor de antena conocido, para medición de radiación no ionizante.

**Criterios de Aceptación:**

1. [ ] Rango de frecuencia de la antena activa cubre hasta 6 GHz.
2. [ ] Incluye filtro SAW.
3. [ ] Respuesta en frecuencia plana (variación ≤ 2 dB en todo el rango).
4. [ ] Factor de antena documentado por el fabricante.

**Notas:**  
ANE confirma (SI). Requiere hardware nuevo.

---

#### 3.8.2 Medición de Radiación No Ionizante

---

**`ANTE-RNI-001` — Unidades de medida para radiación**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-T K.113, K.100; `REF-003`, `REF-004`                  |
| **Dependencias**       | `ANTE-ANT-002`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE adoptar las siguientes unidades de medida para radiación no ionizante: densidad de potencia (S = W/m²), intensidad de campo magnético (A/m), intensidad de campo eléctrico (V/m), dBµV/m, y dBA/m.

**Criterios de Aceptación:**

1. [ ] Todas las unidades listadas están disponibles como opción de visualización.
2. [ ] Las conversiones entre unidades son correctas.

**Notas:**  
—

---

**`ANTE-RNI-002` — Medición de intensidad de campo**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-T K.113, K.100; `REF-003`, `REF-004`                  |
| **Dependencias**       | `ANTE-ANT-002`, `ANTE-RNI-001`                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE medir nivel e intensidad de campo eléctrico, incluyendo los datos de antena caracterizada (factor de antena AF) para su cálculo.

**Criterios de Aceptación:**

1. [ ] La medición de campo usa el factor de antena (AF) de la antena conectada.
2. [ ] La fórmula aplicada es: E [V/m] = V_medido [V] × AF.
3. [ ] Los resultados se presentan en V/m y dBµV/m.

**Notas:**  
Factor de antena AF = V_medido / E.

---

### 3.9 Potencia y Autonomía

---

**`POWR-AUT-001` — Módulos de alimentación autónoma**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | Sí                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE integrar módulos de alimentación autónoma mediante soluciones sostenibles, como sistemas híbridos de energía solar y batería, con administrador de batería.

**Criterios de Aceptación:**

1. [ ] El sensor opera con alimentación solar + batería sin fuente externa.
2. [ ] Incluye administrador de batería con indicador de carga.
3. [ ] El diseño del panel solar es discreto (no llamativo).

**Notas:**  
Administrador de batería, carga solar pequeña no llamativa. Responsable: Bernardo.

---

### 3.10 Exactitud y Confiabilidad

#### 3.10.1 Sincronización y Calibración

---

**`CONF-SIN-001` — Sincronización NTP**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `CONN-RED-004`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE sincronizarse a reloj de red NTP para etiquetado temporal de muestreos.

**Criterios de Aceptación:**

1. [ ] El sensor sincroniza con servidor NTP al establecer conexión de red.
2. [ ] La desviación temporal es ≤ 100 ms respecto al servidor NTP.
3. [ ] El estado de sincronización es visible en la interfaz de monitoreo.

**Notas:**  
ANE confirma (SI).

---

**`CONF-CAL-001` — Procedimientos de calibración**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `ANÁLISIS`                                                |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE incluir procesos de calibración de frecuencias, ganancia de recepción, IQ balance y corrección de offset DC.

**Criterios de Aceptación:**

1. [ ] Procedimiento documentado de calibración de frecuencia.
2. [ ] Procedimiento documentado de calibración de ganancia.
3. [ ] Procedimiento documentado de corrección de IQ balance y offset DC.
4. [ ] Cada calibración genera un certificado o registro con fecha y resultado.

**Notas:**  
—

---

#### 3.10.2 Caracterización del Sistema

---

**`CONF-CAR-001` — DANL (Displayed Average Noise Level)**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1138; `REF-002`                                  |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE tener un DANL mínimo de –100 dBm en el rango de operación.

**Criterios de Aceptación:**

1. [ ] El DANL medido es ≤ –100 dBm en al menos el 90% del rango de frecuencia.
2. [ ] La medición se realiza con carga de 50Ω y se documenta por banda.

**Notas:**  
Limitaciones conocidas del HackRF: no tiene atenuador calibrado ni ruido de referencia conocido. El compromiso es caracterizar el sistema y dar valores que permitan determinar la fiabilidad de las medidas.

---

**`CONF-CAR-002` — Rango dinámico**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1138; `REF-002`                                  |
| **Dependencias**       | `CONF-CAR-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE tener un rango dinámico mínimo de ≥ 80 dB.

**Criterios de Aceptación:**

1. [ ] Rango dinámico medido ≥ 80 dB en prueba de dos tonos.
2. [ ] La medición se documenta con setup de prueba y resultados.

**Notas:**  
—

---

**`CONF-CAR-003` — Exactitud de frecuencia**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE tener exactitud de frecuencia máxima de ± 2 ppm.

**Criterios de Aceptación:**

1. [ ] Error de frecuencia medido ≤ ± 2 ppm contra referencia calibrada.
2. [ ] La medición se realiza a temperatura ambiente (20–25 °C).

**Notas:**  
—

---

**`CONF-CAR-004` — Delta aging (envejecimiento del oscilador)**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `ANÁLISIS`                                                |
| **Hardware nuevo**     | Sí (cambio de oscilador posible)                          |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `CONF-CAR-003`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE especificar y cumplir un drift de frecuencia por envejecimiento ≤ 1 ppm por año.

**Criterios de Aceptación:**

1. [ ] El oscilador seleccionado tiene especificación de aging ≤ 1 ppm/año.
2. [ ] Se documenta el tipo de oscilador y su especificación de aging.

**Notas:**  
HackRF arranca con 20–50 ppm de error, no compensado. Posible cambio de oscilador. Depende del tipo de oscilador usado.

---

**`CONF-CAR-005` — Precisión de amplitud**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `NO_FUNCIONAL`                                            |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `PRUEBA`                                                  |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE tener una precisión de amplitud típica de ± 1 dB, considerando estabilidad, linealidad y respuesta plana.

**Criterios de Aceptación:**

1. [ ] Error de amplitud ≤ ± 1 dB en al menos el 90% del rango de frecuencia.
2. [ ] La linealidad de amplitud se verifica en pasos de 10 dB.

**Notas:**  
Limitaciones del HackRF: no AGC ni atenuadores calibrados, no prefiltros, ruido imagen presente.

---

### 3.11 Exportación e Integración

---

**`INTG-EXP-001` — Exportación de datos CSV, JSON y XML**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE exportar datos en formato CSV, JSON y XML para el procesamiento de resultados en monitoreos de espectro.

**Criterios de Aceptación:**

1. [ ] Los tres formatos (CSV, JSON, XML) están disponibles para exportación.
2. [ ] Los archivos exportados incluyen metadatos (timestamp, ubicación, parámetros de medición).
3. [ ] Los esquemas JSON y XML están documentados.

**Notas:**  
ANE confirma (SI).

---

**`INTG-API-001` — API estándar**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL`                                               |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `DEMOSTRACIÓN`                                            |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | —                                                         |
| **Dependencias**       | `ANAL-SEG-001`                                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE proveer APIs con formato de intercambio de información estándar (mínimo JSON), conforme a estándares internacionales de gestión del espectro.

**Criterios de Aceptación:**

1. [ ] La API está documentada (OpenAPI/Swagger o equivalente).
2. [ ] El formato de intercambio principal es JSON.
3. [ ] La API implementa autenticación y autorización.

**Notas:**  
Revisar funciones basadas en estándares ITU para interoperabilidad.

---

### 3.12 Cumplimiento de Estándares

---

**`ESTD-ITU-001` — Cumplimiento recomendaciones ITU-R**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `RESTRICCIÓN`                                             |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `ANÁLISIS`                                                |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-R SM.1537, SM.1138; `REF-001`, `REF-002`              |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE cumplir con las recomendaciones de la ITU-R, incluyendo pero no limitado a: SM.1537 (requisitos de estaciones de monitoreo: precisión, tiempo de respuesta, capacidad de escaneo, almacenamiento) y SM.1138 (sensibilidad, selectividad).

**Criterios de Aceptación:**

1. [ ] Se documenta la conformidad punto por punto contra SM.1537.
2. [ ] Se documenta la conformidad punto por punto contra SM.1138.
3. [ ] Los gaps de conformidad se identifican y se planifica su resolución.

**Notas:**  
SM.1537: precisión, tiempo de respuesta, capacidad de escaneo, almacenamiento. SM.1138: sensibilidad, selectividad.

---

**`ESTD-ITU-002` — Cumplimiento estándares CEPT/ERC**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `RESTRICCIÓN`                                             |
| **Prioridad**          | `SHOULD`                                                  |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `ANÁLISIS`                                                |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | CEPT/ERC/REC 70-03, ECC Report 260; `REF-005`, `REF-006`  |
| **Dependencias**       | —                                                         |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBERÍA integrar estándares técnicos de organismos internacionales, tales como CEPT/ERC/REC 70-03 (uso compartido de espectro sin licencia) y ECC Report 260 (protección para servicios SRD).

**Criterios de Aceptación:**

1. [ ] Se documenta la aplicabilidad de CEPT/ERC/REC 70-03 al sistema.
2. [ ] Se documenta la aplicabilidad de ECC Report 260 al sistema.

**Notas:**  
CEPT/ERC/REC 70-03: uso compartido de espectro sin licencia (433 MHz, 2.4 GHz). ECC Report 260: protección para servicios SRD.

---

**`ESTD-RNI-001` — Cumplimiento campo eléctrico ITU-T K.113/K.100**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `RESTRICCIÓN`                                             |
| **Prioridad**          | `MUST`                                                    |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `ANÁLISIS`                                                |
| **Hardware nuevo**     | No                                                        |
| **Estándar(es)**       | ITU-T K.113, K.100; `REF-003`, `REF-004`                  |
| **Dependencias**       | `ANTE-ANT-002`, `ANTE-RNI-002`                            |
| **Fase**               | 2025–2026                                                 |

**Descripción:**  
El sistema DEBE cumplir con ITU-T K.113 y K.100 para la medición del campo eléctrico en entornos urbanos y la evaluación de exposición humana a campos electromagnéticos.

**Criterios de Aceptación:**

1. [ ] El procedimiento de medición de campo eléctrico sigue las directrices de K.113.
2. [ ] Los niveles de exposición se evalúan conforme a K.100.
3. [ ] Los resultados de medición incluyen incertidumbre de medida.

**Notas:**  
ANE confirma (SI). Normas para medir campo eléctrico en zonas urbanas y evaluar exposición humana.

---

## 4. Requisitos de Interfaces Externas

### 4.1 Interfaces de Usuario

El frontend se desarrollará en React.js (o Vue.js) con bibliotecas de visualización D3.js/Plotly.js y aceleración WebGL para renderizado espectral en tiempo real.

### 4.2 Interfaces de Hardware

- SDR: HackRF One (USB, interfaz SPI interna)
- Plataforma embebida: Raspberry Pi
- GPS: módulo GPS con precisión ≤ 3 m
- Antenas: conectores SMA para antenas específicas por banda y antena activa
- Conectividad: módulo 4G/5G con SIM, WiFi, Ethernet RJ45
- Alimentación: panel solar + batería + administrador de carga

### 4.3 Interfaces de Software

- Backend: FastAPI o Node.js con WebSockets
- Contenedores: Docker
- BD emisiones autorizadas: integración con BD de la ANE
- API: REST/JSON, documentada con OpenAPI

### 4.4 Interfaces de Comunicación

- Sensor ↔ Cloud: HTTPS (TLS ≥ 1.2), WebSockets seguros
- Protocolos de red: TCP/IP sobre 4G/5G, WiFi, Ethernet
- NTP para sincronización temporal
- SSH para acceso remoto de mantenimiento

---

## 5. Requisitos No Funcionales

### 5.1 Rendimiento

- Monitoreo en tiempo real con latencia ≤ 1 segundo en visualización.
- Ancho de banda de monitoreo hasta 20 MHz instantáneo.
- Escaneos programados ejecutados con tolerancia ≤ 1 minuto.

### 5.2 Seguridad

- Todas las comunicaciones cifradas con TLS ≥ 1.2 (`ANAL-SEG-001`).
- Autenticación por tokens para API (`INTG-API-001`).
- Gestión segura de sesiones.

### 5.3 Fiabilidad / Disponibilidad

- Auto-routing de red para alta disponibilidad de conectividad (`CONN-RED-004`).
- Almacenamiento local en sensor para operación ante pérdida de conectividad (`FORN-ALM-003`).

### 5.4 Mantenibilidad

- Actualización de software OTA (`CONN-SOP-001`).
- Acceso remoto SSH para diagnóstico.
- Procedimientos de calibración documentados (`CONF-CAL-001`).

### 5.5 Portabilidad

- Arquitectura Docker para backend cloud.
- APIs estándar JSON para interoperabilidad.

---

## 6. Trazabilidad

| ID Requisito     | Categoría              | Estándar Ref              | Hardware Nuevo |
|------------------|------------------------|---------------------------|----------------|
| `ANAL-SEG-001`   | Seguridad              | ETSI EN 303 645           | No             |
| `ANAL-EMC-001`   | EMC                    | —                         | Sí             |
| `ANAL-RNG-001`   | Rango Espectral        | ITU-R SM.1537             | No             |
| `ANAL-RNG-002`   | Ancho de Banda         | —                         | No             |
| `ANAL-PAR-001`   | Parametrización        | —                         | No             |
| `ANAL-PAR-002`   | Parametrización        | —                         | No             |
| `ANAL-PAR-003`   | Parametrización        | —                         | No             |
| `ANAL-PAR-004`   | Parametrización        | —                         | Sí             |
| `ANAL-PAR-005`   | GPS                    | —                         | No             |
| `ANAL-PAR-006`   | Unidades               | —                         | No             |
| `ANAL-PAR-007`   | Detección              | —                         | No             |
| `ANAL-MED-001`   | Medición               | ITU-R SM.1537             | No             |
| `ANAL-MED-002`   | Medición               | —                         | No             |
| `ANAL-MED-003`   | Medición               | ITU-R SM.1537             | No             |
| `ANAL-MED-004`   | Medición               | —                         | No             |
| `ANAL-MED-005`   | Radiodifusión          | —                         | No             |
| `ANAL-MED-006`   | Radiodifusión          | —                         | No             |
| `ANAL-MED-007`   | Radiodifusión          | —                         | No             |
| `NORM-DET-001`   | Cumplimiento           | ITU-R SM.1537             | No             |
| `NORM-DET-002`   | Cumplimiento           | ITU-R SM.1537             | No             |
| `NORM-DET-003`   | Cumplimiento           | ITU-R SM.1537             | No             |
| `NORM-SRV-001`   | Radiodifusión          | —                         | No             |
| `NORM-SRV-002`   | Radiodifusión          | —                         | No             |
| `NORM-VER-001`   | Verificación           | —                         | No             |
| `NORM-VER-002`   | Verificación           | —                         | No             |
| `GEST-MON-001`   | Gestión                | —                         | No             |
| `GEST-MON-002`   | Gestión                | —                         | No             |
| `GEST-PRG-001`   | Gestión                | ITU-R SM.1537             | No             |
| `GEST-REP-001`   | Gestión                | —                         | No             |
| `FORN-ALM-001`   | Almacenamiento         | ITU-R SM.1537             | No             |
| `FORN-ALM-002`   | Almacenamiento         | —                         | No             |
| `FORN-ALM-003`   | Almacenamiento         | —                         | Sí             |
| `CONN-RED-001`   | Conectividad           | —                         | Sí             |
| `CONN-RED-002`   | Conectividad           | —                         | No             |
| `CONN-RED-003`   | Conectividad           | —                         | Sí             |
| `CONN-RED-004`   | Conectividad           | —                         | No             |
| `CONN-SOP-001`   | Soporte                | —                         | No             |
| `CONN-GPS-001`   | GPS                    | —                         | No             |
| `CONN-GPS-002`   | GPS                    | —                         | Sí             |
| `ANTE-ANT-001`   | Antenas                | —                         | Sí             |
| `ANTE-ANT-002`   | Antenas                | ITU-T K.113, K.100        | Sí             |
| `ANTE-RNI-001`   | Radiación NI           | ITU-T K.113, K.100        | No             |
| `ANTE-RNI-002`   | Radiación NI           | ITU-T K.113, K.100        | No             |
| `POWR-AUT-001`   | Potencia               | —                         | Sí             |
| `CONF-SIN-001`   | Sincronización         | —                         | No             |
| `CONF-CAL-001`   | Calibración            | —                         | No             |
| `CONF-CAR-001`   | Caracterización        | ITU-R SM.1138             | No             |
| `CONF-CAR-002`   | Caracterización        | ITU-R SM.1138             | No             |
| `CONF-CAR-003`   | Caracterización        | —                         | No             |
| `CONF-CAR-004`   | Caracterización        | —                         | Sí             |
| `CONF-CAR-005`   | Caracterización        | —                         | No             |
| `INTG-EXP-001`   | Exportación            | —                         | No             |
| `INTG-API-001`   | Integración            | —                         | No             |
| `ESTD-ITU-001`   | Estándares             | ITU-R SM.1537, SM.1138    | No             |
| `ESTD-ITU-002`   | Estándares             | CEPT/ERC/REC 70-03        | No             |
| `ESTD-RNI-001`   | Estándares             | ITU-T K.113, K.100        | No             |

---

## 7. Validación Estructural (para IA)

> Esta sección define las reglas que un validador automatizado DEBE verificar contra este documento.

### 7.1 Reglas de Formato

| Regla ID | Regla                                                                 | Severidad |
|----------|-----------------------------------------------------------------------|-----------|
| `V-001`  | Cada requisito DEBE tener un `id` único con formato `[A-Z]{3,5}-[A-Z]{2,4}-\d{3}` | `ERROR`   |
| `V-002`  | Cada requisito DEBE tener todos los campos obligatorios: Tipo, Prioridad, Estado, Verificación, Descripción, Criterios de Aceptación | `ERROR`   |
| `V-003`  | El campo Descripción DEBE iniciar con "El sistema DEBE" o "El sistema DEBERÍA" | `WARNING` |
| `V-004`  | Los Criterios de Aceptación DEBEN tener al menos 1 elemento verificable | `ERROR`   |
| `V-005`  | Los valores de Tipo DEBEN ser uno de: `FUNCIONAL`, `NO_FUNCIONAL`, `INTERFAZ`, `RESTRICCIÓN` | `ERROR`   |
| `V-006`  | Los valores de Prioridad DEBEN seguir MoSCoW: `MUST`, `SHOULD`, `COULD`, `WONT` | `ERROR`   |
| `V-007`  | Los valores de Verificación DEBEN ser: `INSPECCIÓN`, `DEMOSTRACIÓN`, `PRUEBA`, `ANÁLISIS` | `ERROR`   |
| `V-008`  | Los valores de Estado DEBEN ser: `PROPUESTO`, `APROBADO`, `IMPLEMENTADO`, `VERIFICADO`, `RECHAZADO` | `ERROR`   |
| `V-009`  | Las Dependencias referenciadas DEBEN existir como IDs en el documento | `ERROR`   |
| `V-010`  | No DEBEN existir IDs duplicados en todo el documento                   | `ERROR`   |
| `V-011`  | Cada sección 3.x DEBE contener al menos un requisito                   | `WARNING` |

### 7.2 Reglas Semánticas

| Regla ID | Regla                                                                 | Severidad |
|----------|-----------------------------------------------------------------------|-----------|
| `S-001`  | Requisitos con Prioridad `MUST` DEBEN tener Criterios de Aceptación con valores cuantitativos cuando aplique | `WARNING` |
| `S-002`  | Requisitos con Hardware nuevo `Sí` DEBEN especificar el componente en Notas | `WARNING` |
| `S-003`  | Requisitos con Estándar(es) no vacío DEBEN citar documentos listados en §1.4 | `WARNING` |
| `S-004`  | No DEBE haber dependencias circulares entre requisitos                 | `ERROR`   |

### 7.3 Estadísticas del Documento

| Métrica                          | Valor |
|----------------------------------|-------|
| Total de requisitos              | 53    |
| Requisitos FUNCIONAL             | 39    |
| Requisitos NO_FUNCIONAL          | 11    |
| Requisitos RESTRICCIÓN           | 3     |
| Prioridad MUST                   | 51    |
| Prioridad SHOULD                 | 2     |
| Requieren hardware nuevo         | 11    |
| Con referencia a estándares      | 18    |

---

## Anexo A — Estándares de Referencia

| Estándar               | Organismo | Título / Alcance                                                      |
|------------------------|-----------|-----------------------------------------------------------------------|
| ITU-R SM.1537          | ITU       | Automatización y requisitos de estaciones de monitoreo del espectro    |
| ITU-R SM.1138          | ITU       | Sensibilidad y selectividad de equipos de monitoreo                   |
| ITU-T K.113            | ITU       | Medición de campo eléctrico en entornos urbanos                       |
| ITU-T K.100            | ITU       | Evaluación de exposición humana a campos electromagnéticos            |
| CEPT/ERC/REC 70-03     | CEPT      | Uso compartido de espectro sin licencia                               |
| ECC Report 260         | CEPT      | Protección para servicios SRD                                         |
| IEEE/ISO/IEC 29148:2018| IEEE/ISO  | Requirements engineering — Procesos del ciclo de vida                 |
| ETSI EN 303 645        | ETSI      | Cyber Security for Consumer IoT                                       |

## Anexo B — Glosario Extendido

| Término             | Definición                                                                                  |
|---------------------|---------------------------------------------------------------------------------------------|
| HackRF One          | SDR de bajo costo, rango 1 MHz – 6 GHz, 20 MHz de ancho de banda instantáneo               |
| Raspberry Pi        | Computadora de placa única (SBC) usada como plataforma embebida del sensor                  |
| CS8                 | Formato de archivo de muestras IQ (Complex Signed 8-bit)                                    |
| Span IF             | Rango de frecuencia visible en pantalla / bajo análisis                                      |
| OBW                 | Occupied Bandwidth — Ancho de banda que contiene un porcentaje definido de la potencia total |
| Factor de Antena (AF)| Relación entre campo eléctrico incidente y voltaje en terminales de la antena (V/m ÷ V)    |
| Gasket RF           | Junta de blindaje electromagnético para aislamiento entre compartimentos                     |
| Failover            | Conmutación automática a un canal de respaldo ante falla del canal principal                 |
| OTA                 | Over The Air — Actualización remota de software sin acceso físico                            |

---

> **Nota de uso:** Este documento contiene únicamente los requisitos marcados como aprobados (verde) en el archivo Excel de roadmap "Resumen_Funcionalidades_ANE_Fase_2_lastEDITEDB.xlsx". Los ítems marcados en amarillo (en discusión), dorado (interés futuro), azul (por analizar), negro (fase posterior) u otros colores fueron excluidos deliberadamente.
