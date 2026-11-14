# Build Package — Espectro web mínimo con Raspberry Pi 5 y HackRF One

## Identidad y reglas de normalización

| Campo | Valor |
|-------|-------|
| Proyecto / acrónimo | Espectro web mínimo RPi5 + HackRF / R5SPEC |
| Organización | GCPDS — Universidad Nacional de Colombia |
| Versión / fecha / clasificación | 1.0.0 / 2026-11-13 / PUBLIC |
| Autor / revisor / aprobador | D. Ramírez / responsable del laboratorio GCPDS / responsable del laboratorio GCPDS |
| Documentos derivados | STRS-R5SPEC-001 y SYRS-R5SPEC-001; versión 1.0.0, estado DRAFT |
| Objetivo OBJ-001 | Ver un espectro recibido por una HackRF conectada a la RPi5 y cambiar sus controles RX desde un navegador de la LAN. |
| Objetivo OBJ-002 | Entregar un prototipo pequeño, reproducible en mock y validable funcionalmente con hardware real en VL-2. |

Este documento es la entrada completa del caso T2; no es un reporte de ejecución.
S0 conserva los IDs siguientes, copia sus valores a los dos blueprints y no añade funciones.
Todos los STK y NRM tienen Priority MUST y Status PROPOSED; las NRM tienen Compliance PENDING.
Para STK y HWC, Standard(s) y Clause son `—`, y Compliance es NOT_APPLICABLE:
las referencias del fabricante son fuentes de límites COTS, no certificaciones normativas.
Todos los HWC tienen Status CONFIRMED: significa documentado por el fabricante, no medido aquí.
Para SYS sin NRM en sus trazas, Standard(s) es `—`; los demás citan las RFC indicadas.
Los estados de cumplimiento se evaluarán durante el flujo, nunca se presuponen COMPLIANT.

Glosario: IQ = muestras complejas en fase/cuadratura; HAL = adaptador de adquisición;
LAN = red local; DSP = procesamiento digital de señal; RSS = memoria residente;
fs = muestras complejas por segundo; fc = frecuencia central; dBFS se define en B.3.1.

## A. Producto y límites

Sistema nuevo de laboratorio para un operador técnico y un navegador Chromium o Firefox
actualizado en la misma LAN. Una RPi5 ejecuta un backend Python con captura y DSP;
ese mismo backend sirve el HTML/JS/CSS de producción compilado con Vite. El navegador
ejecuta el dashboard TypeScript. Dos paquetes: backend y dashboard; el DSP es un módulo
del backend, sin microservicio adicional. El proceso `hackrf_transfer` es un adaptador HAL.

Una sola página: gráfico de línea frecuencia/potencia relativa, siete controles RX,
botón Aplicar, modo MOCK/REAL, estado de conexión y último error. Sin waterfall, audio,
demodulación, barrido, detección de emisoras, ML, grabación IQ, cuentas, base de datos,
Docker, TLS ni acceso público. No se intenta reproducir todas las funciones de Gqrx.
No se exigen PPM, reloj externo, disparo sincronizado, ajuste IF/LO explícito ni TX.

### A.1 Entorno y hardware suministrado

| Componente | Equipo | Papel |
|------------|--------|-------|
| HW-001 | Great Scott Gadgets HackRF One | Único receptor USB, sin transmisión. |
| HW-002 | Raspberry Pi 5, variante de al menos 4 GB | Captura, DSP, API HTTP y alojamiento del dashboard compilado. |
| HW-003 | Antena pasiva de recepción con conector SMA, sin fuente RF conducida | Observación del espectro ambiente; no se presupone una emisora ni nivel conocido. |
| HW-004 | PC del operador con navegador en la misma LAN | Desarrollo, agente y visualización remota del dashboard. |

Fabricantes/modelos: HW-001, Great Scott Gadgets / HackRF One; HW-002,
Raspberry Pi Ltd / Raspberry Pi 5; HW-003 y HW-004, genéricos sin modelo impuesto.

Topología: HW-003 → SMA de HW-001; HW-001 → USB de HW-002; HW-002 ↔ HW-004 por LAN.
USB transporta I/Q int8: 16 MB/s nominales a 8 MS/s y 40 MB/s a 20 MS/s; son
tasas calculadas, no mediciones ni promesas de cero pérdidas. La LAN transporta
solo espectros JSON y controles HTTP; no IQ. Se requiere Ethernet de 100 Mb/s o
superior y conectividad local estable; no se exige una tasa LAN medida inicialmente.

RPi5 con refrigeración activa, fuente oficial USB-C de 27 W, Raspberry Pi OS de 64 bits,
Python 3.12 o superior y acceso USB para el usuario que ejecuta el backend.
`hackrf_info` y `hackrf_transfer` proceden del paquete de sistema HackRF/libhackrf.
El equipo de desarrollo dispone de uv, Node y pnpm para compilar Vite. La RPi5
recibe el build ya compilado y no necesita un servidor Vite ni Node durante la operación.
IP, MAC, credenciales y comprobaciones de equipos se obtienen en la preparación
de G2 de la metodología; no son datos faltantes de este Build Package.

### A.2 Fuentes oficiales recuperadas de la web

Consulta: 2026-11-13. Los límites de rendimiento elegidos para T2 son del proyecto;
ninguna RFC impone los tiempos, FPS o tolerancias numéricas de este ejemplo.

| Ref | Documento y sección usada |
|-----|---------------------------|
| REF-001 | [IETF RFC 8259, diciembre 2017](https://www.rfc-editor.org/rfc/rfc8259.html), §6 Numbers, §8.1 Character Encoding y §10 Generators. |
| REF-002 | [IETF RFC 9110, junio 2022](https://www.rfc-editor.org/rfc/rfc9110.html), §9.2.1 Safe Methods, §9.3.1 GET y §9.3.3 POST. |
| REF-003 | [Great Scott Gadgets, HackRF One](https://hackrf.readthedocs.io/en/stable/hackrf_one.html), Features y Maximum input power. |
| REF-004 | [Great Scott Gadgets, Setting Gain Controls for RX](https://hackrf.readthedocs.io/en/stable/setting_gain.html), Gain controls. |
| REF-005 | [Great Scott Gadgets, Sampling Rate and Baseband Filters](https://hackrf.readthedocs.io/en/stable/sampling_rate.html). |
| REF-006 | [Great Scott Gadgets, libhackrf](https://github.com/greatscottgadgets/hackrf/blob/main/host/libhackrf/src/hackrf.c), tabla `max2837_ft`; [hackrf_transfer](https://github.com/greatscottgadgets/hackrf/blob/main/host/hackrf-tools/src/hackrf_transfer.c), opciones RX y salida `-r -`. |
| REF-007 | [Raspberry Pi Ltd, Raspberry Pi 5](https://www.raspberrypi.com/products/raspberry-pi-5/), especificaciones del producto. |
| REF-008 | [Raspberry Pi Ltd, Frequency management and thermal control](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#frequency-management-and-thermal-control), protección térmica hasta 85 °C. |

### A.3 Obligaciones normativas adoptadas

Son obligaciones de interoperabilidad de software adoptadas por el proyecto. No
constituyen una certificación RF ni se les atribuyen límites de precisión espectral.

| ID | Título y obligación SHALL | Standard(s) / Clause | Criterio de aceptación |
|----|---------------------------|----------------------|------------------------|
| NRM-JSON-001 | JSON interoperable: la API SHALL generar JSON válido UTF-8, sin BOM ni valores NaN/Infinity. | RFC 8259 / §6, §8.1, §10 | Un parser estricto acepta todas las respuestas JSON de B.4; el vector de ceros produce números finitos. |
| NRM-HTTP-001 | Lecturas sin reconfiguración: GET SHALL consultar estado/espectro; los cambios de parámetros se solicitarán por POST. | RFC 9110 / §9.2.1, §9.3.1, §9.3.3 | Cinco GET consecutivos conservan parámetros y revisión de configuración; un POST válido cambia ambos. La adquisición continua puede seguir avanzando. |

### A.4 Requisitos del interesado

La Description de cada bloque es la frase SHALL de la segunda columna. La última
columna es su Acceptance Criteria. Dependencies es `—` salvo los IDs explícitos indicados.

| ID | Título y necesidad SHALL | Type | Verification | Dependencies | Criterio de aceptación |
|----|--------------------------|------|--------------|--------------|------------------------|
| STK-WEB-001 | Dashboard LAN: el sistema SHALL servir en la RPi5 una sola página con espectro y los siete controles RX. | FUNCTIONAL | DEMONSTRATION | HWC-RPI-001 | Abre por la IP LAN en puerto 8000, dibuja espectros y permite Aplicar sin recargar la página. |
| STK-SDR-001 | Captura real y mock: el sistema SHALL obtener IQ del modo seleccionado y mostrar su espectro relativo. | FUNCTIONAL | TEST | HWC-SDR-001, HWC-SDR-002, HWC-SDR-003 | Los oráculos B.4 pasan en mock; PROTO-001 obtiene IQ real y espectros nuevos con la HackRF en VL-2. |
| STK-CTL-001 | Controles RX: el sistema SHALL validar y aplicar los siete parámetros de B.2, mostrando los valores aceptados. | FUNCTIONAL | TEST | HWC-SDR-004, HWC-SDR-005, HWC-SDR-006 | Cada cambio válido de B.4/B.5 entrega un espectro de la nueva revisión en ≤10 s; un valor inválido se rechaza sin cambiar parámetros ni revisión. |
| STK-OPS-001 | Arranque y fallo visibles: el sistema SHALL arrancar completo con un comando y mostrar desconexión o fallo sin simular datos reales. | NON_FUNCTIONAL | TEST | — | Primer espectro en ≤15 s, error visible en ≤10 s, y Ctrl+C detiene backend/captura y libera puerto/USB en ≤10 s. |
| STK-PER-001 | Fluidez modesta: el sistema SHALL mantener una actualización útil en el perfil base real. | NON_FUNCTIONAL | TEST | HWC-RPI-001 | Tras calentamiento ≤15 s, en 30 s hay ≥60 secuencias distintas observadas y ningún intervalo entre secuencias nuevas supera 3 s; RSS del backend y su captura ≤1 GiB. |
| STK-SAF-001 | Operación RX: el sistema SHALL limitar su HAL a recepción y arrancar con amplificador RF y bias-tee apagados. | CONSTRAINT | INSPECTION | HWC-SDR-007 | No hay ruta TX; la captura usa `-r`, nunca `-t` ni `-c`; el estado inicial tiene amp=false y bias=false y se respetan las condiciones de PROTO-001. |

### A.5 Restricciones COTS

Component y Source ref se copian literalmente. Para cada RANGE, las dos cifras
son Value min y Value max; para los demás tipos, toda la celda es Value.

| ID | Component | Parameter | Limit type | Value o Value min … Value max | Source | Source ref | Impact |
|----|-----------|-----------|------------|-------------------------------|--------|------------|--------|
| HWC-SDR-001 | HW-001 | Frecuencia central | RANGE | 1 000 000 Hz … 6 000 000 000 Hz | DATASHEET | REF-003, Features | HARD |
| HWC-SDR-002 | HW-001 | Muestreo complejo admitido por el equipo | RANGE | 2 000 000 sample/s … 20 000 000 sample/s | DATASHEET | REF-003, Features; REF-005 recomienda ≥8 MS/s | HARD |
| HWC-SDR-003 | HW-001 | Formato de muestras | FIXED | I y Q int8 con signo, intercalados, 2 bytes por muestra compleja | DRIVER_API | REF-006, hackrf_transfer RX | HARD |
| HWC-SDR-004 | HW-001 | Ganancia LNA y VGA | ENUM | LNA={0,8,16,24,32,40} dB; VGA={0,2,4,…,62} dB | DATASHEET | REF-004, Gain controls | HARD |
| HWC-SDR-005 | HW-001 | Ancho del filtro baseband | ENUM | {1.75,2.5,3.5,5,5.5,6,7,8,9,10,12,14,15,20,24,28} MHz | DRIVER_API | REF-006, max2837_ft | HARD |
| HWC-SDR-006 | HW-001 | Amplificador RF y alimentación SMA | ENUM | RF={off,on}, ganancia nominal aproximada 11 dB; bias={off,on}, alimentación 3.0–3.3 V y máximo 50 mA | DATASHEET | REF-003, Features; REF-004, Gain controls | HARD |
| HWC-SDR-007 | HW-001 | Potencia RF máxima admisible en la entrada | MAX | −5 dBm | DATASHEET | REF-003, Maximum input power | HARD |
| HWC-RPI-001 | HW-002 | RAM de la variante seleccionada | MIN | 4 GB | DATASHEET | REF-007, variantes y especificaciones | HARD |
| HWC-RPI-002 | HW-002 | Límite de protección térmica del SoC | MAX | 85 °C | DATASHEET | REF-008, Frequency management and thermal control | HARD |

## B. Contrato técnico suficiente para S1/S2

### B.1 Ejecución y límites de diseño

HAL mode: `mock+real`. VL-0/VL-1 se ejecutan en el PC de desarrollo con Mock HAL;
VL-2 usa la RPi5 y su HackRF. No se exige acceso al equipo durante S0/S1/G1/S2.
La integración remota seguirá `vsil_hil_mcp` y la preparación pre-G2 de las skills.
No se exige GNU Radio ni Marconi: la FFT con NumPy es suficiente para este caso.

Python ≥3.12 con uv, FastAPI/Uvicorn y NumPy; dashboard TypeScript/Vite con pnpm.
HTML Canvas 2D basta para el gráfico. Los nombres internos de módulos se deciden
en S1. Un solo proceso servidor HTTP con un trabajador Uvicorn, sin reload.
Real HAL: ejecutar `hackrf_transfer -r -` como subproceso con argumentos separados,
leer continuamente stdout binario y drenar stderr, conservando solo datos recientes.
No implementar un driver USB, bindings propios de libhackrf ni un buffer IQ histórico.

El producto entregado SHALL tener estos comandos desde la raíz, con dependencias
ya instaladas: `./run.sh mock` y `./run.sh real`. Ambos sirven la UI compilada y la API
en `0.0.0.0:8000`; abrir `http://127.0.0.1:8000/` localmente o `http://<IP-de-la-RPi5>:8000/`
desde la LAN. `0.0.0.0` es la dirección de escucha, no la URL del navegador.
El comando de compilación será `pnpm build`; su salida Vite se incluye en la entrega.
Las dependencias/build se preparan antes del arranque, nunca se descargan por visita.

### B.2 Los siete controles RX y sus valores iniciales

| Clave API | Valores aceptados por T2 | Inicial | Opción hackrf_transfer |
|-----------|--------------------------|---------|------------------------|
| fc_hz | Entero de 1 000 000 a 6 000 000 000 Hz | 100 000 000 | -f |
| fs_hz | {8 000 000,10 000 000,12 500 000,16 000 000,20 000 000} sample/s | 8 000 000 | -s |
| bb_bw_hz | Los 16 valores de HWC-SDR-005 convertidos a Hz | 1 750 000 | -b |
| lna_db | {0,8,16,24,32,40} dB | 16 | -l |
| vga_db | Entero par de 0 a 62 dB | 16 | -g |
| amp | Booleano | false | -a, convertir a 0/1 |
| bias | Booleano | false | -p, convertir a 0/1 |

T2 limita fs a cinco perfiles ≥8 MS/s por REF-005; no promete ofrecer las tasas
inferiores del dispositivo. No se clampa ni redondea: fuera de rango, fuera de
rejilla, campos desconocidos, booleanos usados como enteros o campos ausentes → HTTP 422.
Se valida el objeto completo antes de tocar la captura. No se exige que fc±fs/2
quede en el rango de sintonía: el límite del fabricante aplica a fc. Filtros mayores
que fs pueden seleccionarse; no se afirma rechazo de alias ni precisión analógica.

### B.3 Especificaciones y trazabilidad

| ID | Type / Parameter | Method | Traces to | Standard(s) | Acceptance Criteria |
|----|------------------|--------|-----------|-------------|---------------------|
| SYS-DSP-001 | PROCESSING / espectro relativo dBFS y eje Hz | Fórmula B.3.1 y conversión IQ | STK-SDR-001, HWC-SDR-001, HWC-SDR-002, HWC-SDR-003 | — | GV-1/GV-2/GV-3; 1024 valores finitos y eje con paso fs/1024. |
| SYS-CTL-001 | PROCESSING / configuración RX | B.2, validación completa, reinicio controlado de la captura y revisión monotónica | STK-CTL-001, STK-SAF-001, HWC-SDR-004, HWC-SDR-005, HWC-SDR-006, HWC-SDR-007 | — | GV-4, escenarios SC-2/SC-3 y cambios de PROTO-001; nunca se mezclan IQ viejo y parámetros nuevos. |
| SYS-API-001 | PROTOCOL / HTTP y JSON | Endpoints B.3.2, serialización estricta y polling | STK-WEB-001, NRM-JSON-001, NRM-HTTP-001 | RFC 8259 §6/§8.1/§10; RFC 9110 §9.2.1/§9.3.1/§9.3.3 | GV-3/GV-5 y SC-3: JSON finito, GET sin reconfigurar, POST válido aplicado. |
| SYS-UI-001 | QUALITY / visualización y arranque | Vite estático servido por backend, Canvas y controles B.1/B.2 | STK-WEB-001, STK-OPS-001 | — | SC-1/SC-4; URL LAN accesible sin servidor Node, unidades Hz/MHz y dBFS visibles, error/mode visibles. |
| SYS-PER-001 | QUALITY / cadencia, memoria y cierre | Último espectro disponible, polling 200 ms, medición monotónica en el observador y telemetría | STK-PER-001, STK-OPS-001, HWC-RPI-001, HWC-RPI-002 | — | Cadencia y RSS de STK-PER-001 a 8 MS/s; cierre y tiempos de STK-OPS-001; envolvente B.6. |

#### B.3.1 DSP fijo, pequeño y con oráculo

N=1024. Convertir pares IQ: `x=(I+j*Q)/128`. Ventana Hann periódica:
`w[n]=0.5-0.5*cos(2*pi*n/N)`, n=0…1023. Por cada espectro usar un bloque reciente
completo, calcular `X=fftshift(fft(x*w))` y
`P=10*log10(max(abs(X)**2/sum(w)**2,1e-12))`, máximo aplicado por bin.
Bin k: `fc+(k-512)*fs/1024`, k=0…1023. La unidad es dBFS por bin, relativa a un
tono complejo de amplitud 1; no dBm, PSD/Hz ni intensidad de campo.
Objetivo de publicación: 5 espectros/s, sin procesar cada muestra recibida.
Se permite descartar bloques antiguos intencionalmente para mostrar datos recientes.
El DC real puede ser visible; no hay requisito de quitarlo ni de estimar ruido.

Mock HAL de producto: bloques deterministas con tono `0.5*exp(j*2*pi*128*n/1024)`,
cuantizado por `clip(round(128*real/imag),-128,127)` a int8. Acepta y recuerda los
siete parámetros; ajusta el eje con fc/fs, sin simular ganancias ni filtros analógicos.
El preview mock no depende de archivos de `verification/`.

#### B.3.2 API y estados mínimos

`GET /api/status`: mode (`mock` o `real`), state (`starting`, `running` o `error`),
params (objeto B.2), revision (entero), error (texto o null).
`GET /api/spectrum`: HTTP 200 con `seq`, `revision`, `fc_hz`, `fs_hz` y
`power_dbfs` (1024 números); HTTP 503 si no hay espectro vigente.
Cada FFT publicada incrementa seq; GET no lo incrementa. Evitar caché HTTP del espectro.
`POST /api/config`: los siete campos B.2; HTTP 200 tras recibir IQ con esa
configuración y aumentar revision, o HTTP 503 y estado error si falla el equipo.
Después de reconfigurar, descartar datos anteriores antes de publicar la nueva revisión.
Una configuración válida puede pausar el gráfico ≤10 s; no se exige cambio sin cortes.
La UI muestra valores confirmados por el backend, no presenta el formulario como readback RF.
Un fallo real no cambia a Mock HAL: muestra error; recuperar permite reintentar Aplicar.

### B.4 Oráculos VL-0 y escenarios VL-1

Las expectativas son del autor, previas a la implementación. Versionar entradas y
expectativas en el kit; no regenerar el esperado a partir de la salida del producto.

| ID | Entrada | Resultado esperado |
|----|---------|--------------------|
| GV-1 | Bytes int8 [127,-128,0,64] | Complejos [0.9921875−1j, 0+0.5j], error absoluto ≤1e-6 por componente. |
| GV-2 | Complejos exactos `0.5*exp(j*2*pi*64*n/1024)`, n=0…1023, a fs=8 MS/s y fc=100 MHz | Pico en bin 576, frecuencia 100.5 MHz, nivel −6.0206±0.5 dBFS. Se prueba DSP sin cuantización. |
| GV-3 | 1024 complejos cero | Todos los bins −120±0.01 dBFS; respuesta JSON estricta sin NaN/Infinity. |
| GV-4 | Configuración inicial; luego lna_db=24; luego lna_db=33 | Primer cambio válido: lna=24 y revisión nueva. Segundo: HTTP 422, lna sigue 24 y revisión intacta. |
| GV-5 | Cinco GET; POST con fc_hz=101 000 000 y otros seis campos iniciales | Los GET no cambian params/revision; POST válido cambia fc y revision; espectro nuevo conserva 1024 bins. |
| SC-1 | `./run.sh mock`, página y API desde un navegador | MOCK visible; pico del tono cuantizado en bin 640±1 y nivel −6.02±1 dBFS; plot, controles y valores activos visibles. |
| SC-2 | En mock, cambiar una vez cada campo usando valores de B.5 | Cada respuesta y espectro nuevo reflejan su revisión; ningún acceso a USB ni afirmación sobre respuesta RF simulada. |
| SC-3 | Enviar por separado fc=0, fs=1 000 000, bb=4 000 000, lna=33, vga=3, amp=2, bias="yes" | Siete HTTP 422, sin cambios de configuración ni reinicios de captura. |
| SC-4 | Inyectar fallo de la HAL mock tras haber recibido un espectro; Ctrl+C al finalizar | UI muestra error y no muestra el último cuadro como vivo; no cambia de modo; cierre completo en ≤10 s. |

### B.5 VL-2 real — PROTO-001

Aplica a SYS-DSP-001, SYS-CTL-001, SYS-API-001, SYS-UI-001 y SYS-PER-001.
Es una validación funcional del camino HackRF→RPi5→HTTP→navegador. No certifica
exactitud RF, ganancia, ancho analógico, ruido, ausencia de pérdidas ni calibración.

Preparación: RPi5 disponible, un HackRF, conexión LAN, firmware/host compatibles,
permisos USB y build Vite servido por el backend. Sin generador ni instrumental
calibrado. Usar SMA sin conectar durante la secuencia de controles, incluido bias:
el ensayo de alimentación es solo aceptación del comando, no medición de su tensión.
El puerto no se conecta a una fuente RF conducida; no se usa para demostrar el límite −5 dBm.
Desactivar bias antes de conectar la antena pasiva para la observación opcional.
El ruido propio del receptor basta; no se condiciona PASS a encontrar una emisora.

1. El padre G2 revisa candidato/kit y operaciones, obtiene el `continue` obligatorio
   y prepara el equipo conforme a la skill. Registrar `hackrf_info` y configuración.
2. Arrancar `./run.sh real` en la RPi5. Capturar argv real y stderr del adaptador,
   número de bytes IQ recibidos y las respuestas HTTP. El número de bytes debe crecer;
   cada espectro procede de un bloque IQ completo. REAL/running y primera trama ≤15 s.
3. Con el perfil inicial, observar la API por 30 s a intervalos de 200 ms:
   ≥60 seq distintas, hueco máximo entre nuevas secuencias ≤3 s, 1024 valores finitos
   por trama y RSS total backend+subproceso ≤1 GiB. Medir tiempos con un único reloj
   monotónico del observador, sin restar relojes de RPi y PC. Registrar telemetría de la RPi5.
4. Partiendo siempre del perfil inicial, cambiar solo un campo y restaurar antes
   del siguiente: fc=101 000 000; fs=10 000 000; bb=2 500 000; lna=24; vga=18;
   amp=true; bias=true. Cada caso: comando del driver sin error y un bloque IQ nuevo
   con revisión nueva en ≤10 s. Restaurar amp/bias=false. Estos siete casos prueban
   aceptación y continuidad; no miden la ganancia, frecuencia ni alimentación físicas.
5. Probar un perfil adicional fs=20 000 000, bb=5 000 000 y demás valores iniciales:
   debe producir al menos una trama nueva en ≤10 s. Solo el perfil de 8 MS/s tiene
   requisito de cadencia sostenida; no se exige recorrer todo el espacio de parámetros.
6. Desde el PC LAN abrir la UI servida por la RPi5: REAL visible, gráfico actualizándose,
   siete controles y Aplicar funcionales; guardar evidencia de navegador o captura de pantalla.
   Repetir SC-3 por HTTP en real: rechazos sin reinicio. Ctrl+C y verificar liberación
   de procesos/puerto/USB dentro de 10 s; `hackrf_info` vuelve a abrir el dispositivo.

Guardar comandos, resultados y `measurement.json` v2 por intento según G2, con
requirement_id de SYS correspondiente, criterio y pass/fail/inconclusive.
Un argv o un eco de parámetros sin IQ nuevo no prueba funcionamiento físico.
La comprobación sintética de bin/nivel sigue siendo evidencia VL-0/VL-1;
la captura y el control reales son las afirmaciones VL-2. El humano decide G2.

### B.6 Correcciones, tolerancias y decisiones de método

SyRS §4: no hay cadena de corrección RF, factor de antena ni conversión a dBm.
No se aplica calibración externa porque las conclusiones VL-2 son funcionales.
SyRS §5: copiar las tolerancias de B.4/B.5 y su justificación: paso digital
fs/1024=7812.5 Hz a 8 MS/s, bin conocido sintético, y reloj monotónico con
resolución registrada ≤10 ms frente a límites de 3/10/15 s. No atribuir a la
HackRF la exactitud de ese eje nominal ni inventar un presupuesto RF/GUM.
SyRS §6: copiar PROTO-001 de B.5, con Setup/Calibration/Execution y sus criterios.

Familias y alternativas para SyRS §2.2: FFT Hann de un bloque frente a Welch
(menor código, solo espectro visual); polling HTTP frente a WebSocket (suficiente
para 5 Hz); reinicio de captura frente a reconfiguración USB en vivo (se admite
pausa de 10 s); tonos deterministas frente a emisoras de referencia (oráculo
repetible sin transmisor). El mapeo normativo de §2.3 usa SYS-API-001 y las dos NRM.
Catálogo de magnitudes: MEAS-001, eje nominal Hz y nivel relativo dBFS (SYS-DSP-001);
MEAS-002, estado de controles (SYS-CTL-001); MEAS-003, cadencia/huecos s y RSS bytes
(SYS-PER-001). Interfaces
externas: SMA/USB/LAN de A.1 y API B.3.2. Requisitos no funcionales: STK-OPS-001 y
STK-PER-001. Las tablas A.3–A.5 y B.3 aportan la trazabilidad de ambos documentos.

Envolvente de SDD §1.7 en la RPi5: RSS backend+captura ≤1 GiB (margen sobre
HWC-RPI-001), temperatura SoC ≤80 °C (margen de proyecto frente a HWC-RPI-002),
intervalo entre espectros nuevos ≤3 s. CPU y avisos de pérdidas del driver son
diagnósticos informativos; el descarte intencional de bloques no se cuenta como
fallo de captura. Muestreo de telemetría: 1 s; presupuesto del colector ≤128 MiB
RSS y media ≤10 % de un núcleo. En VL-0/VL-1, la envolvente local tiene el mismo
presupuesto RSS, cadencia y colector; temperatura/CPU son informativas y se registra
el COTS real del PC. Superar un límite o perder telemetría exige diagnosticar y
decidir repetir/continuar con las afirmaciones aún sustentadas; nunca inventar ceros.
