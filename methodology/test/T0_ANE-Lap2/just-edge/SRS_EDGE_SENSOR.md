# PROYECTO: Sensor Edge — Sistema de Monitoreo Espectral ANE

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
| **ID Documento**       | `SRS-ANE-EDGE-001`                                         |
| **Proyecto**           | Sensor Edge — Subsistema de Monitoreo Espectral (Fase 2)   |
| **Organización**       | Agencia Nacional del Espectro (ANE) — Colombia             |
| **Versión**            | 0.1.0                                                      |
| **Clasificación**      | `INTERNO`                                                  |
| **Autor(es)**          | _Por definir_                                              |
| **Revisor(es)**        | _Por definir_                                              |
| **Aprobador(es)**      | _Por definir_                                              |

### Control de Cambios

| Versión | Fecha      | Autor             | Descripción del Cambio                                  |
|---------|------------|-------------------|----------------------------------------------------------|
| 0.1.0   | 2026-10-13 | Generación asistida IA | Extracción de requisitos edge desde SRS-ANE-001 (sistema completo) |

---

## 1. Introducción

### 1.1 Propósito

Este documento especifica los requisitos del **sensor edge** como subsistema autónomo del Sistema de Monitoreo Espectral de la ANE. Cubre exclusivamente lo que corre en el nodo embebido (HackRF One + Raspberry Pi): driver SDR, pipeline DSP (PSD, FFT bins, trazas), demodulación, conectividad de red (4G/5G, WiFi, Ethernet), multiplexación GPIO, GPS, almacenamiento local, alimentación autónoma y calibración.

**Excluye:** backend cloud, frontend web, APIs de integración, base de datos centralizada de la ANE, generación de reportes, y cualquier lógica que requiera conexión activa al servidor.

### 1.2 Alcance del Sistema

El sensor edge es un nodo de monitoreo espectral autónomo basado en SDR (HackRF One) sobre Raspberry Pi. Captura, procesa y almacena localmente datos espectrales en el rango 1 MHz – 6 GHz. Opera de forma independiente con alimentación solar/batería y conectividad 4G/5G/WiFi/Ethernet.

**El sensor edge NO incluye:** interfaz gráfica web, dashboard centralizado, comparación contra BD de emisiones autorizadas, generación de reportes formales, ni API REST para consumo externo.

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
| OBW        | Occupied Bandwidth — Ancho de banda ocupado                                          |
| PSD        | Power Spectral Density — Densidad espectral de potencia                              |
| FFT        | Fast Fourier Transform — Transformada rápida de Fourier                              |
| GPIO       | General Purpose Input/Output                                                         |
| ppm        | Partes por millón                                                                    |
| SAW        | Surface Acoustic Wave (tipo de filtro)                                               |
| OTA        | Over The Air — Actualización remota de software                                      |
| CS8        | Complex Signed 8-bit — Formato de muestras IQ del HackRF                            |
| AF         | Antenna Factor — Factor de antena                                                    |

### 1.4 Referencias

| ID Ref     | Documento                                                              | Versión / Fecha     |
|------------|------------------------------------------------------------------------|---------------------|
| `REF-001`  | ITU-R SM.1537 — Automatización y requisitos de estaciones de monitoreo | Vigente             |
| `REF-002`  | ITU-R SM.1138 — Sensibilidad y selectividad de monitoreo              | Vigente             |
| `REF-003`  | ITU-T K.113 — Medición de campo eléctrico en entornos urbanos         | Vigente             |
| `REF-004`  | ITU-T K.100 — Evaluación de exposición humana a campos electromagnéticos | Vigente          |
| `REF-007`  | IEEE/ISO/IEC 29148:2018 — Requirements engineering                    | 2018                |
| `REF-FULL` | SRS-ANE-001 — SRS Sistema Completo Fase 2                             | 0.1.0 / 2026-10-13  |

### 1.5 Visión General del Documento

La sección 3 contiene los requisitos específicos del sensor edge organizados por subsistema: arquitectura RF, parametrización DSP, procesamiento de señal, detección local, almacenamiento on-device, conectividad de red, antenas, potencia, health monitoring y calibración. La sección 6 presenta la trazabilidad. La sección 7 define reglas de validación estructural.

---

## 2. Descripción General del Sistema

### 2.1 Perspectiva del Producto

Este documento describe el sensor edge como subsistema del sistema completo (ver `REF-FULL`). El sensor opera como nodo autónomo de adquisición y preprocesamiento espectral. Los requisitos aquí son un subconjunto filtrado del SRS completo, incluyendo solo los que se ejecutan o residen en el nodo embebido.

#### 2.1.1 Diagrama de Contexto

```
                    ┌─────────────────────────────────────────────┐
                    │            SENSOR EDGE (RPi + HackRF)       │
                    │                                             │
 ┌─────────┐  SMA  │  ┌──────────┐   USB    ┌──────────────┐    │
 │ Antenas  │◄─────►│  │ HackRF   │◄────────►│  Raspberry   │    │
 │ (banda)  │       │  │ One      │  IQ raw  │  Pi          │    │
 └─────────┘       │  └──────────┘          │              │    │
                    │                        │  ┌─────────┐ │    │
 ┌─────────┐  UART │                        │  │ DSP     │ │    │
 │ GPS     │◄──────┤                        │  │ Pipeline│ │    │
 └─────────┘       │                        │  └─────────┘ │    │
                    │                        │  ┌─────────┐ │    │
 ┌─────────┐  GPIO │                        │  │ Storage │ │    │
 │ Mux/    │◄──────┤                        │  │ (local) │ │    │
 │ Switch  │       │                        │  └─────────┘ │    │
 └─────────┘       │                        └──────────────┘    │
                    │                               │            │
 ┌─────────┐  USB  │                          ┌────┴─────┐      │
 │ 4G/5G   │◄──────┤                          │ Failover │      │
 │ Module  │       │                          │ Network  │      │
 └─────────┘       │                          └──────────┘      │
                    │                                             │
 ┌─────────┐       │  ┌───────────────────────────────────┐      │
 │ Solar + │◄──────┤  │ Battery Manager + Charge Control  │      │
 │ Batería │       │  └───────────────────────────────────┘      │
 └─────────┘       └─────────────────────────────────────────────┘
```

### 2.2 Funciones del Producto

El sensor edge proporciona: captura de espectro en tiempo real (1 MHz–6 GHz), procesamiento DSP (FFT, PSD, trazas, RBW/VBW), demodulación FM/AM, medición de parámetros de señal (OBW, potencia de canal, modulación), detección local de intermodulaciones e interferencias, almacenamiento forense local (JSON + CS8), gestión autónoma de conectividad (failover 4G/WiFi/ETH), sincronización NTP, y monitoreo de salud del nodo.

### 2.3 Características de los Usuarios

| Tipo de Usuario       | Descripción                                    | Nivel Técnico |
|-----------------------|------------------------------------------------|---------------|
| Ingeniero de espectro | Configura parámetros del sensor vía acceso remoto | `EXPERTO`     |
| Técnico de campo      | Instala, calibra y mantiene el sensor          | `TÉCNICO`     |

### 2.4 Restricciones

- Hardware base: HackRF One como SDR primario (DANL y rango dinámico inherentes).
- Plataforma embebida: Raspberry Pi (bajo consumo, limitaciones de procesamiento).
- Conectividad: dependencia de cobertura 4G/5G de operadores colombianos.
- Alimentación: solar + batería con administrador de carga.

### 2.5 Supuestos y Dependencias

- La ANE provee SIM Cards de datos para conectividad móvil.
- Los sensores se despliegan en ubicaciones con alimentación eléctrica o donde la solución solar es viable.
- Las antenas están correctamente conectadas y calibradas para la banda de operación.

---

## 3. Requisitos Específicos

---

### 3.1 Arquitectura RF del Sensor

#### 3.1.1 Compatibilidad Electromagnética

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

#### 3.1.2 Rango Espectral

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
3. [ ] El pipeline DSP procesa el ancho de banda completo con latencia ≤ 1 segundo.

**Notas:**  
Manual entre 6 y 20 MHz; automático en 20 MHz.

---

### 3.2 Parametrización DSP

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
3. [ ] El cambio de RBW actualiza el pipeline DSP en tiempo real.

**Notas:**  
Definir rangos de RBW ≥ 6 opciones. RBW se implementa vía tamaño de ventana FFT.

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
El sistema DEBE implementar filtros de Video Bandwidth (VBW) adaptados al tipo de análisis (fino o promedio), para suavizar la señal procesada después del cálculo RBW.

**Criterios de Aceptación:**

1. [ ] El VBW es configurable independientemente del RBW.
2. [ ] Filtros disponibles para análisis fino y promediado.
3. [ ] La salida DSP muestra diferencia perceptible entre modos de filtrado.

**Notas:**  
Filtrado posterior a RBW para suavizar señal. Implementación digital en el pipeline DSP.

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

1. [ ] Se pueden ingresar latitud y longitud manualmente vía configuración del sensor.
2. [ ] Las coordenadas manuales se asocian a las mediciones realizadas.
3. [ ] El sistema registra si la ubicación es GPS automática o manual.

**Notas:**  
—

---

**`ANAL-PAR-006` — Conversión de unidades de medida**

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

1. [ ] Todas las unidades listadas están disponibles como parámetro de salida del sensor.
2. [ ] La conversión entre unidades es matemáticamente correcta (error < 0.01 dB).
3. [ ] El cambio de unidad se aplica a los datos de salida del pipeline DSP.

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
3. [ ] Las señales por encima del umbral se marcan en la salida de datos del sensor.

**Notas:**  
Parametrizar umbral y con base en él, definir porción del espectro de interés.

---

### 3.3 Procesamiento de Señal (DSP)

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
El sistema DEBE calcular trazas espectrales: máxima (max hold), mínima (min hold), promedio (average), y modos de detección RMS, pico y promedio.

**Criterios de Aceptación:**

1. [ ] La traza máxima retiene el valor más alto por bin de frecuencia (FFT bin).
2. [ ] La traza mínima retiene el valor más bajo por bin de frecuencia.
3. [ ] La traza promedio calcula media aritmética sobre N barridos (N configurable).
4. [ ] Los modos de detección RMS, pico y promedio son seleccionables.

**Notas:**  
Operaciones sobre FFT bins. Max hold y min hold se acumulan entre barridos sucesivos.

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
3. [ ] Los resultados se expresan en la unidad de frecuencia seleccionada.

**Notas:**  
OBW se calcula sobre los FFT bins de la PSD. –X dB donde la señal cae un X por debajo del pico.

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

1. [ ] La medición de potencia de canal es seleccionable por parámetro de configuración.
2. [ ] El ancho del canal medido es configurable hasta 20 MHz.
3. [ ] El resultado se expresa en las unidades de potencia seleccionadas.

**Notas:**  
Integración de PSD sobre los bins del canal. Limitado a 20 MHz (ancho de banda instantáneo del HackRF).

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
El sistema DEBE decodificar y extraer la información del Radio Data System (RDS) en señales FM.

**Criterios de Aceptación:**

1. [ ] El sistema decodifica campos RDS básicos (PI, PS, RT).
2. [ ] La información RDS se incluye en los datos de salida del sensor junto a la medición FM.

**Notas:**  
Decodificación RDS ejecutada en el pipeline DSP del sensor.

---

**`ANAL-MED-006` — Demodulación FM y AM**

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
El sistema DEBE demodular señales FM y AM en tiempo real, produciendo audio digital como salida.

**Criterios de Aceptación:**

1. [ ] El audio FM se demodula con calidad audible.
2. [ ] El audio AM se demodula con calidad audible (desde 1 MHz con HackRF One).
3. [ ] El audio demodulado se almacena localmente o se transmite como stream.

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

1. [ ] La profundidad de modulación AM se calcula como porcentaje.
2. [ ] La excursión de frecuencia FM se calcula en kHz.
3. [ ] Los valores se actualizan en tiempo real durante la demodulación.

**Notas:**  
AM solo desde 1 MHz en adelante con HackRF One; requiere antena adicional.

---

### 3.4 Detección Local (Edge)

#### 3.4.1 Verificación de Parámetros de Señal

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
2. [ ] Las intermodulaciones presuntas se marcan en la salida de datos espectrales.
3. [ ] La verificación IF se realiza automáticamente.

**Notas:**  
Cubre AM, FM y banda aeronáutica (108–137 MHz). Cálculo local sobre FFT bins.

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
2. [ ] Se genera registro local con datos de frecuencia, potencia y duración.
3. [ ] La detección opera de forma continua sin intervención externa.

**Notas:**  
Umbral de detección: >3 dB del nivel promedio. Procesamiento local en el pipeline DSP.

---

#### 3.4.2 Extracción de Audio

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
El sistema DEBE demodular y extraer audio de señales FM y AM, almacenándolo localmente para uso posterior en verificación y análisis forense.

**Criterios de Aceptación:**

1. [ ] El audio extraído se almacena localmente en formato estándar (WAV o MP3).
2. [ ] El archivo de audio se asocia a metadatos de la medición (frecuencia, timestamp, ubicación).

**Notas:**  
AM solo desde 1 MHz con HackRF One; requiere antena adicional.

---

### 3.5 Almacenamiento Local

---

**`FORN-ALM-001` — Almacenamiento histórico local para análisis forense**

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
El sistema DEBE proveer almacenamiento histórico local para análisis forense, incluyendo datos de espectro con timestamp y ubicación GPS.

**Criterios de Aceptación:**

1. [ ] Los datos de monitoreo se almacenan localmente con timestamp y coordenadas GPS.
2. [ ] Los datos históricos son consultables por rango de fecha, frecuencia y ubicación.
3. [ ] La integridad de los datos almacenados es verificable (checksum o hash).

**Notas:**  
Con hardware actual.

---

**`FORN-ALM-003` — Almacenamiento expandido en sensor**

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
El sistema DEBE adicionar espacio de almacenamiento al sensor para permitir almacenar archivos CS8 (IQ raw) para posterior uso como evidencia forense.

**Criterios de Aceptación:**

1. [ ] El sensor cuenta con almacenamiento adicional accesible.
2. [ ] Los archivos CS8 se almacenan con metadatos (timestamp, frecuencia, coordenadas).
3. [ ] El almacenamiento local es accesible remotamente para descarga.

**Notas:**  
Incluir valor de la solución de almacenamiento a usar (SSD/microSD de alta capacidad).

---

### 3.6 Conectividad Edge

#### 3.6.1 Interfaces de Red

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
Actualmente requiere apertura del equipo para acceder al puerto.

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
El sistema DEBE implementar un sistema de conexión y enrutamiento a red IP automático, usando los distintos canales disponibles (failover/prioridad entre 4G/5G, WiFi y Ethernet).

**Criterios de Aceptación:**

1. [ ] El sistema selecciona automáticamente el canal de red disponible con mayor prioridad.
2. [ ] El failover entre canales ocurre sin intervención manual.
3. [ ] El orden de prioridad es configurable.

**Notas:**  
—

---

#### 3.6.2 Soporte y GPS

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
El sistema DEBE permitir acceso remoto IP al sensor y actualización de software OTA (Over The Air).

**Criterios de Aceptación:**

1. [ ] Se puede acceder remotamente al sensor vía SSH o equivalente seguro.
2. [ ] La actualización de software se realiza sin acceso físico al sensor.
3. [ ] El proceso de actualización incluye rollback automático en caso de fallo.

**Notas:**  
—

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

### 3.7 Antenas y Medición de Radiación

#### 3.7.1 Antenas

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
El sistema DEBE incorporar antenas específicas para recepción de señales con el fin de optimizar la recepción en diferentes bandas.

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
Requiere hardware nuevo.

---

#### 3.7.2 Medición de Radiación No Ionizante

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

1. [ ] Todas las unidades listadas están disponibles como salida del sensor.
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

### 3.8 Potencia y Autonomía

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

### 3.9 Health Monitoring del Sensor

---

**`GEST-MON-001` — Monitoreo de salud del sensor**

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
El sistema DEBE medir y registrar variables de salud del sensor (disco, RAM, CPU, temperatura) usando las variables disponibles en el sistema operativo.

**Criterios de Aceptación:**

1. [ ] Se monitorean al menos: uso de disco, RAM, CPU y temperatura.
2. [ ] Se generan alertas locales cuando las variables superan umbrales configurables.
3. [ ] Los datos de health se almacenan localmente con timestamp.

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
El sistema DEBE medir y registrar la calidad de conexión IP, incluyendo RTT, estado de canal (Alive/Not Alive), ancho de banda disponible y pérdida de paquetes.

**Criterios de Aceptación:**

1. [ ] Se mide RTT periódicamente (intervalo configurable).
2. [ ] Se detecta estado Alive/Not Alive de cada interfaz de red.
3. [ ] Se genera registro local cuando RTT o pérdida de paquetes exceden umbrales.

**Notas:**  
—

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
El sistema DEBE permitir programar escaneos parametrizados de espectro (frecuencia, RBW, VBW, duración) que se ejecuten localmente en el sensor y almacenen resultados para posterior recuperación.

**Criterios de Aceptación:**

1. [ ] Se pueden programar escaneos con parámetros definidos (frecuencia, RBW, VBW, duración, repetición).
2. [ ] Los resultados de escaneos programados se almacenan localmente.
3. [ ] Los escaneos se ejecutan en la hora programada con tolerancia ≤ 1 minuto.

**Notas:**  
Scheduler local en el sensor (cron o equivalente).

---

### 3.10 Exactitud y Calibración

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
3. [ ] El estado de sincronización es consultable localmente.

**Notas:**  
—

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
Limitaciones conocidas del HackRF: no tiene atenuador calibrado ni ruido de referencia conocido.

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
HackRF arranca con 20–50 ppm de error, no compensado. Posible cambio de oscilador.

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

## 4. Requisitos de Interfaces Externas

### 4.1 Interfaces de Hardware

- SDR: HackRF One (USB, interfaz SPI interna)
- Plataforma embebida: Raspberry Pi
- GPS: módulo GPS con precisión ≤ 3 m (UART/USB)
- Antenas: conectores SMA para antenas específicas por banda y antena activa
- Módulo 4G/5G: conexión USB con SIM slot
- WiFi: integrado en RPi o módulo USB externo
- Ethernet: RJ45 accesible externamente
- GPIO: multiplexación para switch de antenas y control de periféricos
- Alimentación: panel solar + batería + administrador de carga
- Almacenamiento: SSD/microSD adicional para CS8

### 4.2 Interfaces de Software

- Driver SDR: libhackrf / SoapySDR
- Pipeline DSP: procesamiento FFT, PSD, filtrado RBW/VBW
- Scheduler: cron o equivalente para escaneos programados
- Network manager: failover automático entre interfaces de red
- NTP client: sincronización temporal

### 4.3 Interfaces de Comunicación

- HackRF ↔ RPi: USB 2.0 (480 Mbps, IQ raw a 20 MS/s × 8 bit = 40 MB/s)
- GPS ↔ RPi: UART/USB (NMEA sentences)
- 4G/5G ↔ RPi: USB (AT commands + data)
- GPIO: control de mux de antenas, LEDs de estado, sensores de batería

---

## 5. Requisitos No Funcionales

### 5.1 Rendimiento

- Pipeline DSP con latencia ≤ 1 segundo para 20 MHz de ancho de banda.
- Resolución de frecuencia mínima: 10 Hz.
- Escaneos programados ejecutados con tolerancia ≤ 1 minuto.

### 5.2 Fiabilidad

- Auto-routing de red para alta disponibilidad de conectividad (`CONN-RED-004`).
- Almacenamiento local ante pérdida de conectividad (`FORN-ALM-003`).
- NTP sync con ≤ 100 ms de desviación (`CONF-SIN-001`).

### 5.3 Mantenibilidad

- Actualización de software OTA (`CONN-SOP-001`) con rollback.
- Acceso remoto SSH para diagnóstico.
- Procedimientos de calibración documentados (`CONF-CAL-001`).

### 5.4 Exactitud

- DANL ≤ –100 dBm (`CONF-CAR-001`).
- Rango dinámico ≥ 80 dB (`CONF-CAR-002`).
- Exactitud de frecuencia ± 2 ppm (`CONF-CAR-003`).
- Precisión de amplitud ± 1 dB (`CONF-CAR-005`).

---

## 6. Trazabilidad

| ID Requisito     | Subsistema Edge          | Estándar Ref              | Hardware Nuevo |
|------------------|--------------------------|---------------------------|----------------|
| `ANAL-EMC-001`   | Arquitectura RF          | —                         | Sí             |
| `ANAL-RNG-001`   | Rango Espectral          | ITU-R SM.1537             | No             |
| `ANAL-RNG-002`   | Ancho de Banda           | —                         | No             |
| `ANAL-PAR-001`   | Parametrización DSP      | —                         | No             |
| `ANAL-PAR-002`   | Parametrización DSP      | —                         | No             |
| `ANAL-PAR-003`   | Parametrización DSP      | —                         | No             |
| `ANAL-PAR-004`   | Parametrización DSP      | —                         | Sí             |
| `ANAL-PAR-005`   | GPS                      | —                         | No             |
| `ANAL-PAR-006`   | Unidades                 | —                         | No             |
| `ANAL-PAR-007`   | Detección                | —                         | No             |
| `ANAL-MED-001`   | DSP / Trazas             | ITU-R SM.1537             | No             |
| `ANAL-MED-003`   | DSP / OBW                | ITU-R SM.1537             | No             |
| `ANAL-MED-004`   | DSP / Potencia canal     | —                         | No             |
| `ANAL-MED-005`   | DSP / RDS                | —                         | No             |
| `ANAL-MED-006`   | DSP / Demodulación       | —                         | No             |
| `ANAL-MED-007`   | DSP / Modulación         | —                         | No             |
| `NORM-VER-001`   | Detección local          | —                         | No             |
| `NORM-VER-002`   | Detección local          | —                         | No             |
| `NORM-SRV-002`   | Audio forense            | —                         | No             |
| `FORN-ALM-001`   | Almacenamiento local     | ITU-R SM.1537             | No             |
| `FORN-ALM-003`   | Almacenamiento local     | —                         | Sí             |
| `CONN-RED-001`   | Conectividad             | —                         | Sí             |
| `CONN-RED-002`   | Conectividad             | —                         | No             |
| `CONN-RED-003`   | Conectividad             | —                         | Sí             |
| `CONN-RED-004`   | Conectividad             | —                         | No             |
| `CONN-SOP-001`   | Mantenimiento            | —                         | No             |
| `CONN-GPS-001`   | GPS                      | —                         | No             |
| `CONN-GPS-002`   | GPS                      | —                         | Sí             |
| `ANTE-ANT-001`   | Antenas                  | —                         | Sí             |
| `ANTE-ANT-002`   | Antenas                  | ITU-T K.113, K.100        | Sí             |
| `ANTE-RNI-001`   | Radiación NI             | ITU-T K.113, K.100        | No             |
| `ANTE-RNI-002`   | Radiación NI             | ITU-T K.113, K.100        | No             |
| `POWR-AUT-001`   | Potencia                 | —                         | Sí             |
| `GEST-MON-001`   | Health monitoring        | —                         | No             |
| `GEST-MON-002`   | Health monitoring        | —                         | No             |
| `GEST-PRG-001`   | Scheduler local          | ITU-R SM.1537             | No             |
| `CONF-SIN-001`   | Sincronización           | —                         | No             |
| `CONF-CAL-001`   | Calibración              | —                         | No             |
| `CONF-CAR-001`   | Caracterización          | ITU-R SM.1138             | No             |
| `CONF-CAR-002`   | Caracterización          | ITU-R SM.1138             | No             |
| `CONF-CAR-003`   | Caracterización          | —                         | No             |
| `CONF-CAR-004`   | Caracterización          | —                         | Sí             |
| `CONF-CAR-005`   | Caracterización          | —                         | No             |

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
| Total de requisitos              | 42    |
| Requisitos FUNCIONAL             | 33    |
| Requisitos NO_FUNCIONAL          | 9     |
| Requisitos RESTRICCIÓN           | 0     |
| Prioridad MUST                   | 41    |
| Prioridad SHOULD                 | 1     |
| Requieren hardware nuevo         | 10    |
| Con referencia a estándares      | 10    |

---

## Anexo A — Requisitos Excluidos (pertenecen al sistema completo)

Los siguientes requisitos del SRS completo (`REF-FULL`) fueron excluidos por depender del backend cloud, frontend web, BD centralizada de la ANE, API REST, o generación de reportes:

| ID Excluido      | Razón de exclusión                                            |
|------------------|---------------------------------------------------------------|
| `ANAL-SEG-001`   | TLS/SSL entre sensor y backend (protocolo servidor)           |
| `ANAL-MED-002`   | Marcadores espectrales (interacción UI frontend)              |
| `NORM-DET-001`   | Detección emisiones no autorizadas (requiere BD ANE)          |
| `NORM-DET-002`   | Incumplimiento ancho de banda (requiere BD ANE)               |
| `NORM-DET-003`   | Incumplimiento potencia (requiere BD ANE)                     |
| `NORM-SRV-001`   | Cuantificación modulación cumplimiento (compara vs BD ANE)    |
| `NORM-VER-001`   | _(incluido — detección local)_                                |
| `NORM-VER-002`   | _(incluido — detección local)_                                |
| `GEST-REP-001`   | Generación automática de informes (backend)                   |
| `FORN-ALM-002`   | Almacenamiento en servidores ANE (infraestructura servidor)   |
| `CONN-SOP-001`   | _(incluido — OTA y SSH son edge)_                             |
| `INTG-EXP-001`   | Exportación CSV/JSON/XML (integración backend)                |
| `INTG-API-001`   | API estándar REST (backend)                                   |
| `ESTD-ITU-001`   | Cumplimiento ITU-R (meta-requisito documental)                |
| `ESTD-ITU-002`   | Cumplimiento CEPT/ERC (meta-requisito documental)             |
| `ESTD-RNI-001`   | Cumplimiento K.113/K.100 (meta-requisito documental)          |

---

> **Nota de uso:** Este documento es un subconjunto del SRS completo (SRS-ANE-001) filtrado para incluir únicamente los requisitos que se ejecutan o residen en el nodo sensor edge (HackRF One + Raspberry Pi). Las dependencias internas se mantienen consistentes — ningún requisito incluido depende de uno excluido. Para el sistema completo, consultar `REF-FULL`.
