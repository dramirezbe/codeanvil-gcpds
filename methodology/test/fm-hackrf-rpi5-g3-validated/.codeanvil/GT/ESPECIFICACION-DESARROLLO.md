# Nodo de monitoreo continuo y calibrado de radiodifusión FM
## Especificación de la solución para el equipo de desarrollo

**Contexto:** monitoreo de la banda FM (88,1 a 107,9 MHz) para la Agencia Nacional del Espectro (ANE), Colombia.
**Estado del documento:** aprobado por la persona responsable del proyecto el 12 de noviembre de 2026. Es la especificación completa de lo que hay que construir: qué debe cumplir el sistema (requisitos), cómo está diseñada la solución (diseño) y cómo se implementa cada parte (especificación).

---

## 0. Cómo leer este documento

| Si usted necesita… | Lea |
|---|---|
| Entender qué es el sistema y qué no hace | secciones 1 y 2 |
| Saber qué debe cumplir y cómo se comprobará | sección 3 |
| Entender la arquitectura, el hardware y las decisiones de diseño | sección 4 |
| Implementar un módulo concreto | sección 5 (un apartado por módulo) y los anexos |
| Saber qué archivos escribe y lee el nodo | sección 6 |
| Saber cómo se calibra, se verifica y se valida el nodo | sección 7 |
| Saber qué pruebas hay y qué falta por medir | secciones 8 y 9 |
| Saber en qué orden construir | sección 10 |

**Archivos de este documento.** Este archivo contiene la parte para leer de corrido. Los datos exhaustivos que se consultan mientras se programa están en cinco anexos, en la misma carpeta:

| Anexo | Contenido |
|---|---|
| [Anexo A](anexo-A-parametros.md) | 333 parámetros: valor, unidad, rango permitido y significado, por módulo |
| [Anexo B](anexo-B-formatos-de-datos.md) | 33 formatos de datos entre módulos, campo por campo |
| [Anexo C](anexo-C-procedimientos.md) | 29 procedimientos y algoritmos paso a paso |
| [Anexo D](anexo-D-errores.md) | 88 códigos de error: condición, respuesta, reintentos, estado final |
| [Anexo E](anexo-E-pruebas.md) | 156 pruebas con umbral, condición y casos |

**Convenciones.** «R-nn» es un requisito de la sección 3; «P-nnn» es una prueba del Anexo E. Los nombres entre comillas invertidas (`scan_period`, `capture_block`, `E-ACQ-004`) son identificadores reales de parámetros, formatos y códigos de error: se escriben igual en el código. Los textos de los anexos conservan el inglés técnico original; la redacción de este archivo está en español.

**Dos reglas que atraviesan todo el diseño y conviene tener presentes desde el principio:**

1. **El sistema entrega evidencia de tamizaje, nunca un dictamen de cumplimiento.** Todo registro, informe, vista y alerta lleva la etiqueta «Screening evidence only: not a compliance determination», y ningún texto del sistema puede afirmar cumplimiento o incumplimiento (R-32, R-33).
2. **Ante la duda, el sistema retiene y marca, no inventa.** Si una medición no puede demostrarse (calibración vencida, saturación, tramas perdidas), el valor no se libera, el estado del canal es *Uncertain* y la razón queda registrada. Nunca se rellena con un valor por defecto.

---

## 1. Qué es el sistema

Un **nodo** de monitoreo es un equipo físico que se instala en un sitio, recibe la banda FM con una antena y mide, **cada 6 segundos, la potencia calibrada de cada uno de los 199 canales** del Plan Técnico FM (100 kHz de separación). Con esa medición el nodo:

- decide si cada canal está **ocupado, libre o incierto**, con la incertidumbre de la medición;
- **compara** esa ocupación con la lista de estaciones asignadas del sitio (consistente, ocupado sin asignación, asignado pero libre, indeterminado);
- calcula el **ciclo de trabajo** de cada canal por intervalos;
- levanta cinco tipos de **alertas** (canal en silencio, ocupación inesperada, sensor fuera de línea, calibración no demostrada, deriva del piso de ruido);
- guarda un **informe de tamizaje** en disco y ofrece cuatro **vistas web** y la descarga de los informes a cualquier persona de la red del sitio, sin inicio de sesión.

Un nodo completo es: **antena → receptor HackRF One → placa Raspberry Pi 5**, más fuente de alimentación, gabinete y cables. Toda la medición y el software corren en la placa. Se pueden instalar varios nodos en distintos sitios; lo único que cambia entre ellos son los archivos de configuración (R-52).

La calidad de la medición no se asume: se **calibra en el sitio** contra una fuente de referencia trazable a un patrón y se **verifica periódicamente** con una segunda referencia independiente. Mientras la calibración no pueda demostrarse, los valores de potencia no se liberan.

## 2. Alcance

### 2.1 Lo que el sistema hace
Medición de los 199 canales por barrido; potencia en dBm con incertidumbre; decisión de ocupación con tres estados; comparación con asignaciones; ciclo de trabajo; calibración, verificación y control de validez de la calibración; cinco alertas; informe de tamizaje guardado a medida que se produce; vistas web; supervisión y reinicio automático de procesos; configuración por archivos.

### 2.2 Lo que el sistema **no** hace (decidido, no olvidado)
| No hace | Por qué |
|---|---|
| Determinar cumplimiento o incumplimiento regulatorio | Es evidencia de tamizaje (R-33); la decisión regulatoria es de las personas |
| Identificar estaciones por demodulación o RDS, ni detectar por métodos ciclo-estacionarios | Ningún requisito lo pide; queda como mejora futura |
| Medir dirección o geolocalizar (arreglo de antenas) | No hay requisito; se usa una sola antena |
| Usar GPS ni referencia de frecuencia externa | R-71 lo prohíbe; la hora viene de la red y el cristal de serie, corregido en la calibración, cumple el error de asignación a canal |
| Usar control automático de ganancia | R-22 lo prohíbe; las ganancias son fijas y se registran |
| Pedir inicio de sesión, roles o filtros de dirección; escribir algo a través de la web | R-67; la web es de solo lectura. La configuración y los procedimientos del operador se hacen en el propio nodo |
| Emitir alertas a partir de la potencia recibida | R-40; mientras no haya un límite configurado (hoy no hay ninguna fuente normativa de límite), la potencia solo se compara en el registro |
| Avisar fuera del nodo, ni avisar que el propio nodo está apagado | Las alertas se ven en la vista web; un nodo apagado no puede informar que lo está |
| Funcionar sin alimentación | No incluye batería ni UPS; los cortes de energía están fuera del alcance (R-48 supone red continua garantizada por el usuario) |
| Calibrarse por sí mismo con un conmutador interno | La fuente de calibración se conecta a mano en el puerto de antena |
| Incluir filtro de banda, LNA, atenuador o protección contra sobretensión externos | Ningún requisito los exige. Se reevalúan si aparecen saturación fuera de banda, saturación persistente cerca de transmisores o un cable de antena largo y expuesto |
| Cifrar el tráfico web | Fuera del alcance de esta versión |
| Comparar más de dos sitios en la reproducibilidad | Solo la comparación entre dos sitios |

## 3. Requisitos

Estos son los 74 requisitos que el sistema debe cumplir. Cada uno tiene un número (R-nn), el texto de lo que debe hacer, el **criterio de aceptación** con que se comprobará y la prueba que lo comprueba (P-nnn, descrita en el Anexo E). Los requisitos están agrupados por tema, no por número.

Dos convenciones que se usan en todo el documento:

- **Estado de ocupación**: cada canal en cada barrido es *Occupied* (ocupado), *Free* (libre) o *Uncertain* (incierto: el sistema no puede afirmar ninguna de las dos cosas). Nunca se convierte «incierto» en «libre» por omisión.
- **Valor liberado**: un valor de potencia o de estado solo se muestra o se usa si el módulo que lo produjo lo declara válido. Si no, se guarda con la razón por la que se retuvo y no se dibuja.

### 3.1 Cobertura, barrido y tiempo

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-01** | El sistema completa un barrido de toda la banda (todos los canales del Plan Técnico FM) con un período de barrido de 10 s como máximo. | Intervalo máximo entre inicios de barridos consecutivos ≤ 10 s en una corrida declarada (se excluye el intervalo interrumpido por un reinicio registrado del watchdog). | P-001 |
| **R-02** | En cada barrido se evalúan los 199 canales del Plan Técnico FM: del canal 1 (88,1 MHz) al canal 199 (107,9 MHz), separados 100 kHz. | 100 % de los barridos tienen un registro para cada canal. | P-002 |
| **R-69** | El sistema integra la potencia recibida de cada canal sobre un ancho de banda de 256 kHz. | Ancho de integración ≥ 256 kHz. | P-068 |
| **R-28** | Cada barrido se sella en UTC con una resolución de 1 ms o mejor. | Resolución de la marca de tiempo ≤ 1 ms. | P-030 |
| **R-57** | El sistema sostiene la adquisición a la tasa de muestreo desplegada sin desbordamientos ni tramas perdidas. | 0 eventos de pérdida de muestras o sobrecarga de búfer en una corrida continua a la tasa desplegada (banco de 60 s y corrida de campo). | P-036 |
| **R-22** | El sistema no usa control automático de ganancia. | 0 adquisiciones con AGC activado. | P-024 |
| **R-23** | Con cada adquisición se registran las ganancias individuales y el estado del amplificador. | 100 % de las adquisiciones con sus ganancias y estado de amplificador. | P-025 |
| **R-50** | Por defecto, el sistema asigna el contenido espectral a la frecuencia de canal con un error de a lo sumo 5 kHz a 100 MHz. | Error de asignación más incertidumbre expandida de la fuente ≤ 5 kHz con tonos CW en el centro de ≥ 5 canales (incluidos el más bajo y el más alto, con al menos un canal por captura). | P-056 |

### 3.2 Detección de ocupación

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-03** | Para cada canal y cada barrido se libera un estado de ocupación: Occupied (ocupado), Free (libre) o Uncertain (incierto). | 100 % de los registros de canal-barrido llevan uno de los tres estados. | P-003 |
| **R-04** | Si la relación señal/ruido de un canal ocupado es de al menos 0 dB, el canal se reporta ocupado con probabilidad de detección ≥ 95 %. | Probabilidad de detección ≥ 95 % sobre observaciones de canales ocupados con SNR ≥ 0 dB (conjunto de aceptación: ≥ 20 observaciones de ≥ 10 canales distintos, ningún canal con más del 20 % de las observaciones, referencia independiente). | P-004 |
| **R-05** | Un canal vacante se reporta como ocupado con probabilidad de falsa alarma ≤ 5 %. | Probabilidad de falsa alarma ≤ 5 % sobre observaciones de canales vacantes confirmados por una referencia independiente. | P-005 |
| **R-06** | Un canal se libera como Free solo si una señal con la potencia mínima recibida declarada quedaría al menos 10 dB por encima del nivel de ruido verificado y por encima del umbral de detección activo. | Margen mínimo entre la potencia mínima declarada y el ruido verificado en los registros liberados como Free ≥ 10 dB; un solo registro que viole la regla hace fallar la prueba. | P-006 |
| **R-07** | Si un canal no puede liberarse como Free, o su validez de ocupación no es válida, el estado es Uncertain. | 0 % de los registros sin validez o sin condiciones de liberación se liberan como Free. | P-007 |
| **R-08** | Para cada canal y cada intervalo de reporte declarado se informa el ciclo de trabajo junto con la fracción de barridos Uncertain. | 100 % de los canales con ciclo de trabajo y fracción Uncertain por cada intervalo. | P-008 |
| **R-59** | Además de lo exigido por R-62, el informe muestra, para cada canal liberado como Free, que no hubo detección, que la validez de ocupación era válida, que el margen de liberación fue de al menos 10 dB y que el umbral de detección no superó la potencia mínima declarada. | 100 % de los registros Free muestran esas condiciones de liberación. | P-009 |
| **R-30** | El informe guarda las entradas de cada estado de ocupación liberado, de modo que todo estado Free del informe pueda volver a verificarse. | 100 % de los estados Free pueden re-verificarse con las entradas guardadas. | P-032 |

### 3.3 Potencia calibrada e incertidumbre

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-09** | Para cada canal y barrido se registra una potencia de canal recibida calibrada, en dBm, en el plano de referencia del receptor (el conector de antena del SDR). | 100 % de los registros con potencia calibrada en dBm. | P-010 |
| **R-10** | La potencia de canal calibrada tiene un error absoluto de a lo sumo 3 dB después de la calibración. | Diferencia absoluta con una referencia independiente calificada ≤ 3 dB, en ≥ 10 canales distintos, restando de cada diferencia su incertidumbre expandida; un canal no concluyente impide la aceptación. | P-011 |
| **R-11** | Con cada valor de potencia se informa su incertidumbre como semiancho en dB, junto con la base de esa incertidumbre. | 100 % de los valores con incertidumbre y su base. | P-012 |
| **R-12** | Cada salida requerida se entrega con su valor, su incertidumbre, el límite aplicable (o el registro de que no existe) y la comparación con ese límite. | 100 % de las salidas con valor, incertidumbre, límite o ausencia registrada, y comparación. | P-013 |
| **R-13** | Si no aplica ningún límite a la potencia de canal recibida, el sistema registra la ausencia del límite y no presenta la comparación como «dentro del límite». | 0 % de los registros sin límite presentan la comparación como dentro del límite. | P-014 |
| **R-14** | El sistema no convierte un estado de comparación indeterminado, no configurado o no evaluable en «dentro» o «fuera» del límite mediante promedios, redondeos, un intervalo pequeño o un valor por defecto. | 0 conversiones de ese tipo en los informes. | P-015 |
| **R-29** | Con cada valor de potencia calibrada, el informe guarda además el estado de ganancias usado y el identificador del registro de calibración aplicable, para poder reconstruir su procedencia. | 100 % de los registros de potencia calibrada nombran ganancias y registro de calibración. | P-031 |

### 3.4 Calibración y verificación

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-17** | Toda medición de potencia lleva una corrección de amplitud establecida contra una fuente de referencia cuyo nivel es trazable a un patrón nacional o internacional. | 100 % de las mediciones con corrección establecida contra una referencia trazable; el registro de calibración nombra la fuente, su fecha de calibración y su incertidumbre. | P-018 |
| **R-18** | Por cada calibración se conserva su identificador, la configuración de hardware y firmware aplicable, el plano de referencia, la fuente de referencia y su estado de validez. | 100 % de las calibraciones con esos cinco datos en su registro. | P-019 |
| **R-19** | El sistema permite verificar periódicamente la corrección de amplitud, a intervalos que no superen un intervalo declarado. | Tiempo máximo entre dos verificaciones aprobadas ≤ intervalo declarado (mínimo 4 días; ver la nota sobre el máximo en la sección 9). | P-020 |
| **R-20** | La referencia usada para verificar la exactitud absoluta de potencia es un instrumento distinto, y con trazabilidad independiente, de la usada para establecer la corrección. | 0 verificaciones en las que la referencia coincide con la que estableció la corrección. | P-021 |
| **R-60** | El registro de validación identifica la referencia independiente usada y su incertidumbre. | 100 % de los registros de validación con esos datos. | P-022 |
| **R-21** | Si la corrección de amplitud activa ya no puede demostrarse, el sistema marca los registros afectados y no libera sus valores de potencia. | 0 valores de potencia liberados mientras la corrección no puede demostrarse (prueba por inyección de fallos: verificación vencida, corrección derivada). | P-023 |
| **R-58** | La configuración de medición es la misma con la que se estableció la calibración activa. | 0 barridos ejecutados con una configuración distinta de la del registro de calibración activo. | P-037 |
| **R-55** | El sistema caracteriza el rango dinámico utilizable y el comportamiento de compresión del receptor para la configuración de ganancias desplegada. | Al menos una configuración desplegada con rango dinámico y compresión documentados. | P-034 |
| **R-56** | Por cada dispositivo se registra el estado de su referencia de frecuencia y la corrección necesaria para conservar la correspondencia entre espectro y frecuencia de canal. | 100 % de los dispositivos con estado de referencia de frecuencia registrado. | P-035 |

### 3.5 Calidad de la captura y salud del nodo

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-24** | Si alguna muestra cruda retenida de una captura está a plena escala del convertidor, se marcan los registros afectados como saturados y no se libera su potencia. | 0 valores de potencia liberados desde una captura con una muestra a plena escala. | P-026 |
| **R-25** | Si ocurre un desbordamiento de recepción o una pérdida de trama durante un barrido, se marcan los registros de ese barrido, no se libera su potencia y su ocupación se libera como Uncertain. | 0 potencias liberadas y 0 estados distintos de Uncertain en barridos con desbordamiento o trama perdida. | P-027 |
| **R-26** | El sistema detecta y cuenta las tramas perdidas del flujo de adquisición. | 100 % de las pérdidas inyectadas se cuentan como tramas perdidas. | P-028 |
| **R-27** | Por cada barrido se emite un registro de salud con el conteo de desbordamientos, el conteo de tramas perdidas y el número de registros publicados. | 100 % de los barridos con registro de salud que contiene los tres conteos. | P-029 |

### 3.6 Comparación con las estaciones asignadas

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-15** | En cada barrido se compara el estado de ocupación de cada canal con la referencia de asignación de estaciones del sitio, y se registra el resultado como consistent, unassigned-occupied, assigned-free o indeterminate. | 100 % de los registros de canal-barrido con resultado de comparación. | P-016 |
| **R-16** | El sistema acepta una referencia de asignación de estaciones propia del sitio y la usa para la comparación de ocupación. | Al menos una referencia del sitio cargada y usada por la comparación. | P-017 |

### 3.7 Alertas

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-34** | Si la comparación de una estación que antes estaba por encima de 90 % de ciclo de trabajo resulta assigned-free durante un número declarado de horas de emisión, se emite una alerta de canal en silencio (channel-silent). | Ninguna alerta omitida cuando se cumple la condición de silencio (las horas se declaran en la configuración, entre 0,1 y 720 h). | P-041 |
| **R-35** | Las observaciones Uncertain no cuentan para el silencio de un canal. | 0 observaciones Uncertain contadas como silencio. | P-042 |
| **R-36** | Si un canal FM monitoreado está ocupado y no está asignado en la referencia, se emite una alerta de ocupación inesperada. | Ninguna alerta omitida para un canal ocupado sin asignación. | P-043 |
| **R-37** | Si no se recibe ningún registro de salud durante tres períodos de barrido, se emite una alerta de sensor fuera de línea. | Ninguna alerta omitida cuando pasan tres períodos sin registro de salud. | P-044 |
| **R-38** | Si la calibración no puede demostrarse en ninguna captura de un barrido, o el intervalo de verificación vence dentro de un margen declarado, se emite una alerta de calibración no demostrada. | Ninguna alerta omitida cuando se cumple la condición. | P-045 |
| **R-39** | Si la mediana del piso de ruido se desplaza más de 6 dB en 24 h, se emite una alerta de deriva del piso de ruido. | Ninguna alerta omitida cuando la mediana se desplaza más de 6 dB en 24 h. | P-046 |
| **R-40** | Mientras no haya un límite configurado para la potencia de canal recibida, el sistema no emite ninguna alerta a partir de esa potencia. | 0 alertas generadas desde la potencia sin límite configurado. | P-047 |

### 3.8 Vistas web, acceso y evidencia

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-41** | El sistema ofrece una vista web de la potencia por canal (frecuencia) y tiempo. | Vista disponible. | P-048 |
| **R-42** | El sistema ofrece una vista web del espectro de potencia actual con marcadores de canal. | Vista disponible. | P-049 |
| **R-43** | El sistema ofrece una vista web de la potencia y el ciclo de trabajo de estaciones seleccionadas durante las últimas 24 h. | Vista disponible. | P-050 |
| **R-44** | El sistema ofrece una vista web del estado del nodo que muestra: estado en línea, antigüedad del último barrido, deriva del piso de ruido, conteo de desbordamientos y conteo de tramas perdidas. | La vista muestra las cinco magnitudes. | P-051 |
| **R-45** | En las vistas de potencia y ocupación solo se dibujan salidas liberadas; para un valor de potencia retenido pero no liberado se muestran los estados de validez y banderas del canal. | 0 valores no liberados dibujados. | P-052 |
| **R-46** | El sistema presenta las alertas emitidas al personal en la vista web. | La vista muestra las alertas emitidas. | P-053 |
| **R-47** | El sistema entrega al personal mediciones calibradas, registros de monitoreo, indicadores de calidad, información de incertidumbre, alertas y otra evidencia técnica para su revisión. | 100 % de esos elementos disponibles al personal. | P-040 |
| **R-67** | El sistema da a todo usuario acceso a la vista web y a los informes guardados, y no restringe ese acceso por rol ni por ningún otro medio. | 0 usuarios o roles sin acceso. | P-067 |
| **R-32** | Todo registro, informe y tablero se identifica como evidencia de tamizaje y no como determinación de cumplimiento. | 100 % de registros, informes y tableros con esa identificación. | P-038 |
| **R-33** | El sistema no establece por sí mismo cumplimiento ni incumplimiento regulatorio en ninguna alerta, registro o informe. | 0 alertas, registros o informes que declaren cumplimiento o incumplimiento. | P-039 |

### 3.9 Informes, almacenamiento y configuración

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-62** | El sistema guarda en disco un informe de tamizaje con los resultados, los registros de fecha y hora, el tiempo de ejecución y la información de ubicación, para que el usuario lo revise. | Los cuatro elementos presentes en el informe guardado. | P-062 |
| **R-70** | El sistema permite al usuario ingresar la ubicación del nodo: país, ciudad y nombre del lugar o dirección. | 100 % de los informes con la ubicación ingresada. | P-070 |
| **R-73** | Mientras una corrida de tamizaje está en curso, el sistema guarda sus resultados en disco a medida que se producen, para que quede registro de lo hecho si el nodo se detiene. | 100 % de los resultados producidos antes de una interrupción están en el informe (prueba cortando la alimentación en plena corrida). | P-072 |
| **R-74** | El sistema permite al usuario configurar el tiempo durante el cual se toman registros, con un mínimo de 10 minutos. | El tiempo mínimo aceptado es 10 min; un valor menor se rechaza. | P-073 |
| **R-31** | El sistema no guarda en disco los registros de monitoreo en tiempo real; solo se guarda el informe de tamizaje. | 0 registros de monitoreo en disco fuera del informe. | P-033 |
| **R-75** | El sistema permite al usuario ajustar el límite del error de asignación a canal, hasta un máximo de 20 kHz. | El límite máximo aceptado es 20 kHz; uno mayor se rechaza. | P-074 |
| **R-52** | El software permite agregar y configurar otro nodo sin reescribir código. | 0 líneas de código reescritas para agregar y configurar otro nodo. | P-058 |

### 3.10 Entorno físico, energía y costo

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-54** | El nodo usa el HackRF One como receptor. | 0 nodos con otro receptor. | P-060 |
| **R-53** | El costo de un nodo de monitoreo completo no excede 3 200 dólares, sin contar las referencias de calibración ni las licencias. | Costo ≤ 3 200 USD con precios a la fecha de la revisión de aceptación. | P-059 |
| **R-63** | El nodo opera conectado a la red eléctrica de 120 V. | 100 % de las corridas de aceptación alimentadas con 120 V. | P-063 |
| **R-72** | El nodo opera conectado a la red eléctrica de 60 Hz. | 100 % de las corridas de aceptación con red de 60 Hz. | P-069 |
| **R-64** | El nodo opera tanto en interiores como en exteriores. | Cumple sus requisitos en los 2 tipos de instalación (una corrida de campo en cada uno). | P-064 |
| **R-65** | El nodo está encerrado de modo que el polvo y la lluvia no entren. | 0 ingresos de polvo o agua bajo la exposición definida (protección IP65). | P-065 |
| **R-66** | El nodo opera a temperaturas ambiente de hasta 40 °C. | Cumple todos sus requisitos a 40 °C ambiente. | P-066 |
| **R-71** | El nodo no incluye receptor GPS. | 0 receptores GPS. | P-071 |

### 3.11 Disponibilidad, reproducibilidad y validación de campo

| Req. | Qué debe cumplir | Criterio de aceptación | Pruebas |
|---|---|---|---|
| **R-48** | El sistema está disponible al menos el 95 % de una corrida continua de 30 días. | Disponibilidad ≥ 95 % en 30 días (la corrida de campo de 72 h no verifica este requisito; la alimentación eléctrica es continua, garantizada por el usuario). | P-054 |
| **R-49** | El sistema se cuenta como disponible en un instante cuando existe un registro completo de barrido dentro de los tres períodos de barrido anteriores. | ≥ 95 % de los puntos de tiempo cuentan como disponibles, con la definición del requisito, en una ventana de 30 días. | P-055 |
| **R-51** | La medición, el tamizaje y los informes de evidencia son reproducibles al repetirlos en otro sitio. | Concordancia entre el primer sitio y otro sitio según la regla aprobada (≥ 10 de 12 puntos, sección 5.17). | P-057 |
| **R-61** | La capacidad de monitoreo se valida en campo con una corrida continua de 72 h en un sitio con una lista publicada de estaciones FM. | Duración de la corrida continua ≥ 72 h; registro de una referencia independiente durante ≥ 6 h de ella. | P-061 |

### 3.12 Restricciones de la plataforma

Límites físicos de los equipos elegidos que el diseño no puede superar:

| Límite | Valor |
|---|---|
| Rango de sintonía del receptor | 1 MHz a 6 000 MHz |
| Tasa de muestreo máxima del receptor | 20 Msps |
| Resolución del convertidor | 8 bits |
| Tolerancia del cristal de referencia de serie | ±20 ppm |
| Ganancia máxima del LNA / del amplificador RF | 40 dB / 14 dB |
| Ancho de banda necesario de una emisión FM estéreo | 256 kHz |
| Variación lenta de la potencia recibida de un enlace fijo en un día | hasta ±10 dB (no se compensa) |
| Temperatura ambiente en el sitio | hasta 40 °C |

### 3.13 Valores que el requisito deja para la implementación

Cinco requisitos dependen de un valor que no se fijó en el diseño; se declaran en la configuración o en la puesta en marcha, dentro de los límites que se indican. La sección 9 detalla cómo cerrarlos.

| Valor pendiente | Requisito | Dónde se declara | Límites |
|---|---|---|---|
| Potencia mínima recibida declarada por canal | R-06 | configuración del sitio | −130 a −5 dBm |
| Intervalo de verificación de la calibración | R-19 | registro de calibración | mínimo 345 600 s (4 días); máximo: ver la nota de la sección 9 (el valor aprobado, 3 456 000 s, no coincide con su justificación de 30 días) |
| Margen de vencimiento de la verificación | R-38 | registro de calibración | 3 600 a 604 800 s (1 h a 7 días) |
| Horas de emisión que definen un canal en silencio | R-34 | configuración (alertas) | 0,1 a 720 h |
| Regla de reproducibilidad entre sitios | R-51 | **ya cerrada**: ≥ 10 de 12 puntos, k = 2 | ver sección 5.15 |
| Severidad de exposición al polvo y la lluvia | R-65 | **ya cerrada**: protección IP65 | gabinete IP66 |

## 4. Diseño de la solución

### 4.1 Visión general

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

**Cada 6 segundos** ocurre un barrido completo:

1. El receptor captura **3 tramos** de espectro (10 MHz de muestreo cada uno, 8 MHz útiles) centrados en 90,25 / 97,75 / 105,25 MHz, que juntos cubren los 199 canales.
2. El estimador convierte las muestras en un espectro promediado y en la **potencia integrada de cada canal** sobre 256 kHz (en unidades sin calibrar, dBFS).
3. El gestor de calibración aplica la **corrección de amplitud** y entrega potencia en dBm con su incertidumbre, o retiene el valor si la calibración no puede demostrarse.
4. El detector decide **Occupied / Free / Uncertain** por canal.
5. El comparador contrasta con la **lista de estaciones asignadas**.
6. El constructor de registros arma **1 encabezado + 199 registros de canal + 1 registro de salud**.
7. Los registros van al **historial en memoria**, al **informe en disco** y al **motor de alertas**; el servicio web los lee.

### 4.2 Hardware

Cada elemento es un equipo comercial de referencia, elegido a partir de su hoja de datos: primero se descartaron las alternativas que no cumplían los requisitos y, entre las que cumplían, se prefirió la que agrega menos piezas.

| Elemento | Equipo de referencia | Características que importan | Lo que no pudo verificarse |
|---|---|---|---|
| Receptor SDR | Great Scott Gadgets HackRF One | Sintonía 1–6 000 MHz; muestreo 2–20 Msps; 8 bits; conector SMA hembra 50 Ω; entrada máxima −5 dBm (daño por encima); USB de alta velocidad alimentado por el bus | etapas y pasos de ganancia, consumo, temperatura de operación |
| Placa de cómputo | Raspberry Pi Ltd Raspberry Pi 5, 8 GB | Cuatro núcleos Arm Cortex-A76 a 2,4 GHz; 8 GB de RAM; Gigabit Ethernet; 2 USB 3.0 y 2 USB 2.0; alimentación 5 V / 5 A por USB-C con Power Delivery; temperatura de operación 0 a 70 °C | si los 70 °C son del ambiente o de la placa; consumo; rendimiento sostenido |
| Refrigeración de la placa | Raspberry Pi Ltd Raspberry Pi Active Cooler (Pi 5) | Ventilador con disipador, alimentado por el conector de ventilador de la placa (5 V), flujo máximo 1,09 CFM | temperatura de operación del ventilador, vida útil |
| Almacenamiento | Kingston Industrial microSD SDCIT2/64GBSP (64 GB, no SD adapter) | microSD industrial de 64 GB, clase 10 / UHS-I U3, −40 a 85 °C, protección ante corte de energía, resistencia 3 840 TBW (128 GB; ~1 920 TBW estimados para 64 GB) | resistencia exacta de 64 GB |
| Antena | Rohde & Schwarz HK033 VHF/UHF coaxial dipole, N female | Dipolo coaxial vertical omnidireccional 80 MHz–2 GHz, N hembra, 50 Ω, ganancia 2 dBi típ., ROE < 2 típ., polarización lineal vertical, −40 a 85 °C | grado de protección IP, precio, mástil y adaptador de mástil |
| Cable de antena | CommScope / Andrew (Amphenol) 7855829, LMR-195 jumper N male to SMA male, 3 m | Jumper LMR-195 de 3 m, N macho a SMA macho; pérdida máxima 1,8 dB (banda 0–3 GHz); ROE máx. 1,22 | pérdida real a 88–108 MHz (se estima 0,43 dB), precio |
| Cable USB receptor–placa | Lindy 36650 USB 2.0 Type A to Micro-B cable, Cromo Line, 0.5 m | USB 2.0 tipo A a Micro-B, 0,5 m, doble blindaje | tipo de alivio de tensión, temperatura, precio |
| Fuente de alimentación | Inventus Power (ELPAC) XWA0650PDA-USB-C (5A version), 65 W desktop supply; AC cord P/N 67400-277-AB sold separately | Fuente de escritorio de 65 W, entrada 85–264 V CA / 47–63 Hz, salida 5 V a 5 A (25 W) por USB-C, eficiencia típ. 81 %, 0 a 40 °C, IP22 | tipo de enchufe del cable de red (se vende aparte), precio, curva de derrateo |
| Gabinete | Fibox (IP Enclosures datasheet) ARCA-304021, polycarbonate, 300 x 400 x 210 mm, mounting plate supplied | Policarbonato 300 × 400 × 210 mm, IP66 / IK10, resistente a UV, −40 a 80 °C continuo, placa de montaje incluida | entradas de cable o prensaestopas (la hoja de datos no las indica), características térmicas |

**Decisión forzada sobre la fuente de alimentación.** El único producto leído que entrega 5,1 V / 5 A por USB-C con Power Delivery (lo que pide la placa) es un adaptador de pared o de escritorio, no una fuente para riel. Por eso **la fuente va fuera del gabinete**, en un tomacorriente seco, y solo el cable de salida de 1,52 m entra al gabinete por un prensaestopas. El calor de la fuente (unos 5,9 W) queda fuera de la caja. El cable de red con enchufe se compra aparte.

**Plano de referencia.** La potencia se calibra en el **conector de antena del receptor**. La ganancia de la antena y la pérdida del cable quedan fuera de la cantidad calibrada (R-09), pero se registran con el plano de referencia.

**Nivel de entrada.** La entrada del receptor tolera como máximo −5 dBm (por encima se daña). No hay medición del nivel real en campo: se mide en la puesta en marcha (prueba P-088) antes de la corrida de 72 h.

**Costo.** El límite es 3 200 USD por nodo, sin contar referencias de calibración ni licencias (R-53). Solo dos precios se leyeron de una fuente: el HackRF One y la Raspberry Pi 5 de 8 GB (175 USD). Los demás (antena, fuente, gabinete, enfriador, tarjeta, cables) **no tienen precio verificado**; la prueba P-094 cierra el costo con precios fechados en la compra.

### 4.3 Arquitectura de software

El software corre en la placa como **cinco unidades** (procesos) más un supervisor. Se separan para que la falla de una no arrastre a las otras: si el servicio web se cae, la medición sigue; si se reinicia la medición, el historial y el informe sobreviven.

| Unidad | Qué contiene | Qué se pierde si se reinicia |
|---|---|---|
| `measure` | adquisición, estimador, gestor de calibración, detector, comparador, constructor de registros | el barrido en curso y el suavizado del piso de ruido (10 barridos); el registro de calibración es un archivo y se vuelve a leer |
| `store_alert` | historial en memoria y motor de alertas | el historial y el estado de las alertas (empiezan vacíos) |
| `report` | escritor de informes | la corrida abierta se cierra como «interrumpida» en el siguiente arranque |
| `web` | servicio web | solo la caché de respuestas |
| `time` | servicio de hora (un cliente NTP estándar) | nada |
| supervisor | arranque, reinicio y vigilancia de las demás | — (lo reinicia el gestor de servicios del sistema; lo cubre el watchdog de hardware) |

La configuración del sitio son archivos que se leen al arrancar; no es un proceso.

**Comunicación entre unidades.** Mensajes JSON UTF-8 por *sockets* locales Unix de flujo, cada mensaje precedido por su longitud (4 bytes, big-endian), de hasta 16 MB. No se abre ningún puerto de red entre unidades. Cada consumidor valida cada mensaje contra su formato (Anexo B); tras 3 mensajes inválidos seguidos del mismo productor, ese proceso se reinicia. Los envíos nunca bloquean: si el consumidor no responde, el productor encola hasta 10 barridos (60 s) y después descarta los más antiguos.

**Sistema operativo requerido.** Linux Arm de 64 bits con gestor de servicios (systemd), grupos de control (cgroups) para límites de memoria y procesador, sistema de archivos temporal en memoria, cliente NTP, controlador del watchdog de hardware de la placa y **sin swap ni volcados de memoria** (el historial no debe llegar nunca al disco, R-31). La referencia es Raspberry Pi OS Lite de 64 bits; el requisito del sistema operativo está propuesto y no se verificó contra la página del fabricante.

**Lenguaje, marco web y biblioteca de gráficos: libres.** Ningún valor, formato ni regla depende de esa elección. Lo que sí es obligatorio: la página web no pide nada a ninguna dirección fuera del nodo (todo recurso estático está en el nodo, máximo 2 MB), y las unidades respetan los límites de memoria, procesador y prioridad de la sección 4.5.

**Programa de línea de comandos local.** Los procedimientos del operador (calibración, verificación, edición de configuración, alta de un nodo nuevo, comparación entre sitios) se ejecutan con un programa local en el propio nodo (consola o sesión remota), que lee los datos que el procedimiento pide (datos de la fuente de referencia, identificadores de certificados, nombre del operador, intervalo y margen) de un **archivo de sesión** que escribe el operador y escribe los registros del módulo. No es accesible desde la web. Su forma exacta es un detalle de codificación; sus entradas y salidas son los formatos y pasos de los Anexos B y C.

### 4.4 Decisiones de diseño

| Tema | Decisión | Razón principal |
|---|---|---|
| Topología | Un nodo mínimo: una antena, un receptor, una placa | Es la mínima que cubre todos los requisitos obligatorios |
| Receptor y placa | HackRF One (impuesto por R-54) y Raspberry Pi 5 de 8 GB (elegida por la persona responsable) | Cumplen tasa de muestreo, USB y red; la placa tiene margen de cómputo y memoria |
| Elementos RF adicionales | Ninguno (sin conmutador, protección, filtro, LNA ni atenuador) | Ningún requisito los exige; la saturación se detecta y se marca en lugar de prevenirse |
| Frecuencia de referencia | Cristal de serie del receptor, con corrección medida en la calibración | R-71 prohíbe GPS; con la corrección cumple el error de 5 kHz a 100 MHz |
| Hora | UTC por red (NTP), sin GPS ni reloj con batería | R-71; tras un arranque la hora no es válida hasta la primera sincronización y se marca |
| Barrido | Capturas escalonadas: 3 pasos a 10 Msps | Con 10 Msps se cumplen el período de 10 s y las cero pérdidas con la menor carga (20 Msps cumple también pero con la carga más alta) |
| Estimador | FFT promediada (4 096 puntos, ventana Hann, solape 50 %) | Entrega potencia integrada por canal con incertidumbre estadística de 0,015 dB |
| Detector | Energía contra un piso de ruido verificado, con una banda *Uncertain* | Cumple detección ≥ 95 % y falsa alarma ≤ 5 % con holgura |
| Calibración | En el sitio, contra fuente trazable; verificación periódica con referencia independiente | R-17, R-19, R-20; las referencias son externas y su costo queda fuera del nodo |
| Representación entre módulos | Un registro por canal y barrido con todas las entradas de cada estado | Permite volver a verificar cualquier estado *Free* (R-30) |
| Manejo de fallas | Marcar, retener y supervisar: nunca bloquear la adquisición | Una falla se marca en los registros del barrido que toca; el supervisor reinicia; el watchdog resetea un nodo congelado |
| Almacenamiento | Informe en disco; todo lo demás en memoria | R-31: no se guardan registros de monitoreo en tiempo real fuera del informe |
| Presentación | Reglas de alerta en el nodo; web ligera de solo lectura; sin inicio de sesión | R-67; sin infraestructura externa |
| Reproducibilidad | Comparar los resultados de dos sitios con una regla aprobada | R-51; no requiere funciones nuevas en el nodo |
| Fuente de alimentación | Fuera del gabinete | Único producto de 5,1 V / 5 A en USB-C con PD encontrado es de pared |

#### Decisiones que tomó la persona responsable al aprobar

Al aprobar la especificación se resolvieron ocho puntos que el diseño había dejado abiertos. Ya están incorporados en las secciones 5 y 7; se listan aquí para que el equipo sepa que fueron decisiones explícitas.

| Pregunta | Decisión |
|---|---|
| Reproducibilidad entre sitios (¿qué números completan la regla?) | k = 2; al menos **10 de 12 puntos** de comparación con *En* ≤ 1, ningún punto con diferencia mayor de 6 dB y al menos **60 observaciones vacantes** de 10 canales por sitio |
| Protección de la adquisición frente a la web | Hasta 8 solicitudes procesadas a la vez, 64 en espera hasta 30 s; descargas a 20 MB/s en total; ante saturación puede haber respuesta «ocupado» (nadie se rechaza por quién es) |
| Alerta de sensor fuera de línea | Se dispara también cuando llegan registros de salud pero todos los barridos fallan (p. ej., radio desconectada): un registro de salud cuenta solo si informa al menos 1 registro publicado; plazo de 18 s |
| Horas de emisión de la alerta de silencio | Cuenta toda hora en que el canal asignado se observa libre, sin horario de emisión; una estación que cesa legítimamente de noche genera alerta tras las horas declaradas |
| Tarjeta llena de informes | Se borran primero los segmentos cerrados de más de 30 días; si no basta, se deja de escribir el informe y **se sigue monitoreando** con el estado señalado |
| Corte de energía en plena escritura | Un resultado está «producido» cuando termina su escritura en el informe; el barrido que se estaba escribiendo al cortar no cuenta; a lo sumo 1 barrido en riesgo (el corte cae dentro de la escritura el 0,83 % del tiempo) |
| Qué es «cada salida requerida» (R-12) | La potencia calibrada del canal, el estado de ocupación y el ciclo de trabajo, con los campos de límite donde corresponda |
| Instrumentos de referencia de la calibración | Se adopta como requisito una fuente trazable y una referencia independiente, ambas con incertidumbre expandida ≤ 0,5 dB (k = 2). **Su disponibilidad efectiva debe confirmarse**; su costo queda fuera de los 3 200 USD |

### 4.5 Presupuestos de tiempo, recursos y fiabilidad

**Tiempo.** El barrido se inicia cada **6 s** en un reloj monótono (si uno se atrasa, el siguiente empieza de inmediato; un barrido de más de 7 s se marca tardío). Las capturas toman 1,83 s (3 × 0,1 s de asentamiento + 3 × 0,5112 s de captura). Toda la cadena de procesamiento de un barrido suma **4,98 s**, con una holgura de **1,02 s** respecto de los 6 s; ningún módulo puede ampliar su asignación sin reducir esa holgura. El estimador (2,5 s) y el detector (0,2 s) son los dos mayores consumos. El presupuesto está **ajustado** y debe medirse en la placa (P-087).

**Memoria (8 GB en la placa).** Suma de demandas: 1 738 MB (78 % de margen). Límites por unidad: sistema operativo 1 000 MB reservados; `measure` 256 MB; `store_alert` 768 MB (el historial tiene su propio tope de 512 MB); `report` 128 MB; `web` 256 MB; supervisor 64 MB; `time` 32 MB; sistema de archivos temporal en memoria 64 MB.

**Procesador.** Carga total estimada: 0,833 Gop/s, equivalente a ~35 % de los 4 núcleos suponiendo 4 ciclos por operación; el límite sostenido es **70 %**. Cuotas: `measure` hasta 3 núcleos, `store_alert` 1, `report` ½, supervisor ¼, `web` como máximo 1 núcleo. Prioridades (*nice*): `measure`, supervisor y `time` 0; `store_alert` y `report` 5; `web` 10 (la adquisición siempre tiene preferencia).

**Almacenamiento (tarjeta de 64 GB).** El informe ocupa unos 599 MB por día (41,6 KB por barrido); 30 días = 17,97 GB. Uso total estimado 28,5 GB (55 % de margen); el piso de espacio libre es 12,8 GB; el informe cabe unos 68 días antes de rotar y el paquete **garantiza 30 días**. Desgaste: ~2,19 TB al año contra ~1 920 TBW de la tarjeta.

**Térmico.** Calor máximo dentro del gabinete 25 W; el aire interno no debe superar 60 °C a 40 °C ambiente (la placa admite hasta 70 °C); el aumento permitido es 20 °C. La conductancia necesaria es 1,25 W/K y la estimada del gabinete 4,8 W/K (estimación, la hoja de datos no la da), para un aumento esperado de 5,2 °C. El procesador se marca con condición `thermal` a 70 °C (se limpia a 65 °C) y empieza a estrangularse a 80 °C.

**Energía.** Techo de consumo conjunto de placa, receptor y ventilador: 20 W (80 % de la salida de 25 W de la fuente).

**Disponibilidad (R-48 / R-49).** Se permite 5 % de indisponibilidad en 30 días = 2 160 min. Reparto: 540 min para la verificación periódica, 540 min para fallas y recuperación, 118 min para la calibración inicial y 962 min de reserva. El plan da 585 min de indisponibilidad planificada (**98,6 % de disponibilidad**). Los supuestos de tasa de fallas (120 reinicios de procesos y 10 reinicios completos cada 30 días) son estimaciones, no mediciones.

**Qué está medido y qué no.** Los presupuestos de tiempo, procesador, térmico y energía están **calculados, no medidos**: el diseño los marca como «sin verificar» o «ajustado» y cada uno tiene una prueba de calificación de hardware (sección 9). Nada en este documento afirma un resultado de medición.

## 5. Especificación de los módulos

Cada apartado describe un módulo: para qué sirve, qué recibe y qué entrega, cómo funciona, los valores que importan y qué no hace. Los valores completos están en el Anexo A, los formatos en el Anexo B, los pasos de los algoritmos en el Anexo C, los errores en el Anexo D y las pruebas en el Anexo E. Los módulos se presentan en el orden en que viajan los datos.

### 5.1 Configuración del sitio

**Para qué sirve.** Que un nodo se distinga de otro solo por datos, no por código (R-52). Dos archivos: `site-config.json` (la configuración del nodo) y la **referencia de asignación de estaciones** que ese archivo nombra.

**Qué contiene `site-config.json`:**

| Campo | Qué es | Valores permitidos |
|---|---|---|
| ubicación | país, ciudad y lugar o dirección (texto) | obligatorio; va a todo informe (R-70) |
| `record_time_min` | tiempo durante el cual se toman registros en una corrida cronometrada | 10 a 43 200 min; un valor menor se **rechaza** (R-74) |
| `mapping_error_limit_khz` | límite del error de asignación a canal | por defecto 5 kHz; admite de 1 a 20 kHz; uno mayor se **rechaza** (R-75) |
| `declared_min_power_dbm` | potencia mínima recibida declarada (valor general y excepciones por canal) | −130 a −5 dBm; **sin valor por defecto**: si falta, ningún canal puede liberarse como *Free* |
| `alert.silent_on_air_hours` | horas de emisión que definen un canal en silencio | 0,1 a 720 h; **sin valor por defecto**: si falta, la alerta de silencio no se evalúa |
| `received_power_limit_dbm` | límite opcional de potencia recibida (general y por canal) | −130 a −5 dBm; hoy no hay ninguna fuente normativa de límite, así que se deja ausente |
| `duty_cycle_interval_min` | intervalo del ciclo de trabajo | por defecto 60 min |
| `time_sources` | fuentes de hora por red | al menos 1 |
| `station_reference_file` | archivo de la referencia de estaciones | hasta 199 entradas (canal → nombre de estación); un canal sin entrada se considera no asignado |

**Cómo se carga.** Al arrancar, ante una orden de recarga y cada cierto tiempo mientras el archivo falte, el servicio comprueba el tamaño del archivo (máximo 1 MiB), lo interpreta como JSON, valida cada campo contra su rango y la referencia contra su formato, calcula el SHA-256 y publica el estado. **Se acepta o se rechaza el archivo completo**: nunca se aplica una configuración parcial, y un archivo rechazado deja activa la última configuración válida. Todo informe lleva el SHA-256 de la configuración, su estado y el identificador de la referencia.

**Estados:** *valid* (archivo válido), *missing* (falta: se usan valores por defecto y se reintenta), *rejected* (inválido: se mantiene la anterior) y *valid with reference invalid* (solo la referencia se rechaza; entonces toda comparación es *indeterminate*).

**Alta de un nodo nuevo.** Se instala el mismo software y se escriben los dos archivos. Se compara el hash del software antes y después: debe ser igual (0 líneas de código reescritas).

**No hace:** no ofrece editor web ni inicio de sesión (la configuración se edita en el nodo); no guarda ganancias ni parámetros de medición (son del módulo de adquisición) ni el registro de calibración ni las reglas de alerta.

**Cubre:** R-16, R-52, R-70, R-74, R-75 y los valores diferidos de R-06 y R-34.

### 5.2 Servicio de hora

**Para qué sirve.** Mantener el reloj del nodo ajustado por red y sellar cada barrido en UTC con resolución de **1 µs** (R-28 exige 1 ms o mejor). No usa GPS (R-71).

**Cómo funciona.** Un cliente NTP estándar consulta las fuentes configuradas (cada 64 a 1 024 s una vez estable). Cada **1 s** se publica un estado de hora con el instante UTC, la resolución y el estado de sincronización. El reloj se declara **no sincronizado** si el desfase estimado supera **50 ms** o si pasaron más de **3 600 s** desde la última sincronización exitosa. Al arrancar se espera hasta 120 s la primera sincronización. Un salto del reloj de más de 1 s respecto del reloj monótono se registra como «salto de reloj».

**Reglas.** Todo registro de barrido lleva `utc_us` (inicio del barrido), `resolution_us` y `sync_state`. **Un barrido nunca se retiene por la hora**: si no hay sincronización, los barridos continúan con la marca de tiempo «unsynced». El sello se toma una sola vez, al inicio de la primera captura del barrido. No hay reloj de respaldo con batería: tras un corte, la hora no es válida hasta la primera sincronización, y la calibración se considera vencida hasta entonces.

**Errores:** reloj no sincronizado, sin fuentes, salto de reloj (`E-TIME-001` a `E-TIME-003`).

### 5.3 Adquisición y barrido

**Para qué sirve.** Capturar del receptor las muestras I/Q de toda la banda, detectar pérdidas y saturación y registrar las ganancias.

**Plan de barrido.** El receptor muestrea a **10 Msps** con 8 bits (I y Q con signo). Como el ancho utilizable por captura es de 8 MHz (80 % de 10 MHz) y la banda a cubrir es de 20,056 MHz, el barrido se hace en **3 pasos** con 0,5 MHz de solape:

| Paso | Frecuencia central | Canales | Canales con espiga de continua (DC) |
|---|---|---|---|
| 1 | 90,25 MHz | 1 a 60 (88,1 a 94,0 MHz) | 22 y 23 |
| 2 | 97,75 MHz | 61 a 135 (94,1 a 101,5 MHz) | 77 y 78 |
| 3 | 105,25 MHz | 136 a 199 (101,6 a 107,9 MHz) | 172 y 173 |

Son 60 + 75 + 64 = 199 canales, cada uno medido exactamente una vez. En cada paso se espera 0,1 s a que se asiente la sintonía y se capturan **39 tramas de 131 072 muestras** (0,5112 s). El paso 2 se mide 0,611 s después del paso 1 y el paso 3 a 1,222 s.

**Ganancias fijas, sin AGC** (R-22): amplificador de entrada 0 dB, primera etapa 16 dB, banda base 16 dB. Cada captura registra las ganancias y `agc_enabled = false` (R-23).

**Detección de pérdidas** (R-24, R-25, R-26). Dos comprobaciones por captura: (1) todo desbordamiento o error de transferencia reportado se cuenta; (2) se cuentan las tramas recibidas y `dropped_frames = 39 − recibidas`. Cualquier conteo distinto de cero **marca el barrido completo**: los 199 registros llevan la bandera, la potencia se retiene y la ocupación es *Uncertain*. Una captura con una muestra a plena escala marca como saturados solo los canales de su paso. Tras 3 barridos marcados seguidos, el supervisor reinicia el proceso de medición.

**Ritmo.** Un barrido empieza cada 6 s en el reloj monótono. Si uno se atrasa, el siguiente empieza de inmediato, sin recuperar. Un barrido de más de 7 s se marca tardío.

**Si el receptor desaparece** (USB desconectado): se cierra el flujo y se reabre, hasta 10 intentos con 1 s de espera; no se producen barridos y el registro de salud muestra 0 registros publicados; pasados los 10 intentos el proceso se detiene y lo reinicia el supervisor.

**No hace:** no estima espectros, no aplica calibración, no decide ocupación; no usa barrido continuo por firmware.

**Cubre:** R-01, R-02, R-22 a R-26, R-57.

### 5.4 Estimador espectral

**Para qué sirve.** Convertir las muestras en la **potencia integrada de cada canal** y en un espectro reducido.

**Algoritmo** (procedimiento `estimate_channel_power`, Anexo C):

1. Convertir cada muestra a complejo `x = (I + jQ)/128` y restar la media de la captura.
2. Por cada tramo: 2 495 segmentos de 4 096 muestras con salto de 2 048 (solape 50 %), ventana **Hann**, FFT, potencia `|X|²/(4096·Σw²)` con `Σw² = 1536`.
3. Promediar los 2 495 espectros bin a bin.
4. **Suprimir la espiga de continua**: los bins a ±3 del centro se reemplazan por la media de los bins de ±4 a ±6.
5. Calcular la frecuencia real del oscilador local con la corrección de calibración (`f_true = f_nominal·(1 + c·10⁻⁶)`) y, para cada canal, sumar la potencia promediada sobre **105 bins** (256,347 kHz) alrededor de su centro (bins separados 2 441,40625 Hz).
6. Pasar a dBFS: `10·log10(suma)`.
7. Marcar `dc_adjacent` en los canales cuya ventana contiene un bin reemplazado (agregan 0,5 dB de incertidumbre) y calcular la cota del error de asignación a canal (3,4648 kHz a 100 MHz) para compararla con el límite configurado.
8. Reducir a 819 puntos por paso (promedio de a 4 bins) para el espectro mostrado.

Las ventanas de canales adyacentes comparten 64 de 105 bins. La incertidumbre estadística del promedio es 0,015 dB. El estimador debe consumir un bloque dentro del tiempo del búfer en anillo de la adquisición (0,839 s). Tiempo asignado: 2,5 s por barrido (el mayor consumo de la cadena; hay que medirlo en la placa, P-077).

**Entrada lateral:** `estimator_control` (corrección de frecuencia en ppm, con signo positivo si la frecuencia real es mayor que la nominal, y estado de la referencia de frecuencia), que produce el gestor de calibración.

**No hace:** no aplica la calibración ni entrega dBm; no decide ocupación; no mide por sí mismo el error del cristal (entrega la estimación del tono que usan la calibración y la verificación).

**Cubre:** R-02, R-09 (junto con la calibración), R-50, R-56, R-69.

### 5.5 Calibración de amplitud

**Para qué sirve.** Convertir dBFS en **dBm en el conector de antena** y demostrar que esa conversión es válida.

**Qué se calibra:** (1) el desplazamiento de amplitud K(f), en dB, de dBFS a dBm; (2) el rango dinámico y la compresión con las ganancias desplegadas (R-55); (3) el error de frecuencia del cristal del receptor (R-56); (4) el piso de ruido del receptor por canal, con el puerto terminado (entrada del detector).

**Equipo externo** (fuera del costo del nodo, R-53): una fuente CW de 88 a 108 MHz con nivel trazable (incertidumbre expandida ≤ 0,5 dB, k = 2) y frecuencia ≤ 1 ppm, una terminación de 50 Ω y un cable de pérdida medida. **Debe ser un instrumento distinto del de la verificación**, con trazabilidad independiente (R-20).

**Procedimiento `establish_amplitude_calibration`** (118 min, lo ejecuta el operador): precalentar 30 min con el puerto terminado; registrar identidad y datos del certificado (se rechaza si están incompletos); medir el piso de ruido en 10 barridos; medir la pérdida del cable; barrer el rango dinámico en el canal 100 de −100 a −20 dBm en pasos de 5 dB; fijar los límites del rango; fijar el nivel de referencia `L_ref = rango_alto − 10 dB` (entre −70 y −30 dBm); medir el desplazamiento en **24 centros de canal**; verificar aceptación; escribir el registro.

**Desplazamiento.** En cada punto, `K = L − P_dBFS` donde `L = nivel de la fuente − pérdida del cable` y `P_dBFS` es la mediana de 5 barridos. Entre puntos del mismo paso, K se interpola linealmente en dB contra la frecuencia; los extremos de cada paso son puntos de calibración (no hay extrapolación). Puntos: paso 1 canales 1, 11, 21, 31, 41, 51, 60; paso 2 canales 61, 71, 81, 91, 101, 111, 121, 131, 135; paso 3 canales 136, 141, 151, 161, 171, 181, 191, 199. **Aplicación:** `potencia_dBm = potencia_dBFS + K(f_canal)`.

**Incertidumbre expandida (k = 2)**, suma cuadrática de: fuente 0,5; desadaptación 0,3; cable 0,1; estadística 0,015; interpolación 0,5; deriva 1,0; linealidad 0,2 dB → **1,28 dB** (1,37 dB para canales con bin de continua reemplazado). Límite de aceptación 2,5 dB (los 3 dB de R-10 menos los 0,5 dB de la fuente). La base de la incertidumbre que se escribe con cada valor es el identificador del certificado de la fuente y este presupuesto.

**Rango dinámico.** El nivel de compresión es el primer nivel cuya potencia medida queda 1 dB por debajo de la recta de pendiente 1 ajustada en la parte baja. `rango_alto = mín(compresión, saturación) − 3 dB` (o −20 dBm si no se alcanza ninguna); `rango_bajo` = nivel más bajo que está al menos 10 dB sobre el piso de ruido. Por encima de `rango_alto` la potencia se retiene; por debajo de `rango_bajo` se libera con la bandera `near_noise_floor`.

**Frecuencia.** `c` = mediana de `(f_est − f_nominal)/f_nominal × 10⁶` en ppm; debe cumplir |c| ≤ 20 ppm, si no el estado es `out_of_limit`.

**Validez de la calibración** (estados): *valid* hasta `verified_until` menos el margen de vencimiento; *expiring* hasta `verified_until`; *expired* después; *invalid* tras una verificación fallida, un cambio de configuración o un registro cuyo checksum falla; *none* si no existe registro. **Solo en *valid* y *expiring* se libera la potencia.** Tras un reinicio con el reloj sin sincronizar, el estado es *expired* hasta sincronizar.

| Estado | Evento | Acción | Siguiente |
|---|---|---|---|
| none | la calibración se aprueba | escribir y activar el registro | valid |
| valid | se llega a `verified_until` − margen | publicar *expiring* | expiring |
| expiring | se llega a `verified_until` | retener la potencia | expired |
| valid / expiring / expired | verificación aprobada | fijar `verified_until` | valid |
| cualquiera | la configuración difiere de la del registro | detener los barridos | invalid |
| cualquiera | la verificación falla | retener la potencia | invalid |
| expired / invalid | se repite la calibración y se aprueba | nuevo registro | valid |

**Configuración.** La configuración de medición (tasa de muestreo, frecuencias centrales, ganancias, parámetros del estimador, identidad del equipo y del software) se resume con SHA-256, que se guarda en el registro y se **compara al inicio de cada barrido**. Si difiere, los barridos se detienen: no se mide nunca con una configuración distinta de la calibrada (R-58).

**Registro de calibración.** Archivo en disco, uno por calibración, **nunca se borra**; guarda identificador, configuración de hardware y firmware, plano de referencia, fuente, intervalo y margen declarados, `verified_until` y estado de validez (R-18).

**No hace:** no verifica contra una referencia independiente (módulo 5.6); no decide ocupación; no tiene conmutador interno (la fuente se conecta a mano).

**Cubre:** R-09, R-10, R-11, R-17, R-18, R-21, R-55, R-56, R-58.

### 5.6 Verificación periódica

**Para qué sirve.** Demostrar cada cierto tiempo que la corrección sigue siendo válida, usando una **referencia independiente**: un instrumento distinto del que estableció la corrección, con número de serie, certificado y cadena de trazabilidad distintos y con la declaración del operador de que no comparten ningún patrón (R-20). El registro de validación nombra la referencia y su incertidumbre (R-60).

**Procedimiento `verify_amplitude_correction`** (39 min: 10 de preparación, 12 puntos × 2 min, 5 de registro). Se aplican 2 niveles (el de referencia y 20 dB por debajo) en 6 canales (16, 46, 76, 126, 146, 186; dos por paso, ninguno es punto de calibración, de modo que se prueba la interpolación). En cada punto: esperar 30 s, tomar 5 barridos, mediana de la potencia calibrada y `diferencia = potencia − nivel aplicado en el plano de referencia`. **Aprueba** si todas las diferencias están dentro de **1,0 dB** (la holgura de deriva del presupuesto de incertidumbre) con una incertidumbre de medición de 0,59 dB. Con eso el presupuesto de 1,28 dB sigue válido hasta la próxima verificación. Una verificación aprobada fija `verified_until`; una fallida invalida la calibración.

**Intervalo y margen.** El valor del intervalo se declara en el registro de calibración dentro de estos límites: **mínimo 4 días** (345 600 s: las verificaciones pueden usar a lo sumo el 25 % del presupuesto de indisponibilidad de R-48, y cada una dura 39 min); **máximo** según la nota de la sección 9; margen de vencimiento entre 1 h y 7 días y siempre menor que el intervalo. La justificación del valor declarado es del operador y se escribe en el registro. Cada verificación genera un **registro de validación** (archivo, nunca se borra).

**Salidas:** el estado de validez activo (leído por el motor de alertas y por el constructor de registros) y, si procede, una nueva corrección de frecuencia para el estimador. El estado *expiring* (que dispara la alerta de R-38) empieza en `verified_until` menos el margen; *expired* en `verified_until`.

**Cubre:** R-19, R-20, R-60.

### 5.7 Detector de ocupación

**Para qué sirve.** Decidir, por canal y por barrido, **Occupied, Free o Uncertain**, con las razones y las entradas guardadas para poder volver a verificar la decisión.

**Estadístico.** Para el canal k: potencia calibrada `P_k` y referencia de ruido `N_k` (dBm); **exceso `e_k = P_k − N_k`** (dB). Es una razón, así que el desplazamiento de calibración se cancela. Una señal con SNR 0 dB duplica la potencia: `e = 3,01 dB`.

**Referencia de ruido.** Por paso, a partir del espectro calibrado: tomar los puntos dentro de 3,6 MHz del centro del paso (737), quitar 5 puntos a cada lado del oscilador (quedan 726), tomar el 10 % más bajo (73 puntos), promediar su potencia lineal, convertir del ancho de punto (9 765,625 Hz) a la ventana de 256,347 kHz sumando 14,19 dB, y guardar la mediana de los últimos 10 barridos. Para cada canal, `N_k` = referencia del paso + (piso almacenado del canal − mediana del piso almacenado del paso). La referencia se verifica: no puede quedar más de 3 dB por debajo del piso almacenado del receptor ni más de 30 dB por encima; si falla, el paso se considera no fiable.

**Umbrales.** *Occupied* si `e_k ≥ 1,5 dB`; *Free* (candidato) si `e_k ≤ 1,0 dB`; entre 1,0 y 1,5 dB es *Uncertain*. Histéresis 0,5 dB: un canal ocupado en el barrido anterior sigue ocupado mientras `e_k ≥ 1,0 dB`. No hay filtrado temporal (la decisión es por observación). Con un error de la referencia de ruido de 0,503 dB (gaussiano) la **falsa alarma esperada es 0,14 %** (límite 5 %) y la **detección esperada con SNR 0 dB es 99,87 %** (mínimo 95 %); las dos estimaciones fallarían juntas si la incertidumbre de la referencia de ruido llegara a 0,91 dB.

**Canales adyacentes.** Dos canales a menos de 2 canales de distancia se solapan. Un canal con `e_k ≥ 1,5 dB` que tiene un vecino (a ≤ 2 canales) que también lo supera solo es *Occupied* si **su propia portadora se ve**: `R_k` = razón entre la densidad media de los 7 puntos centrales y la de los 12 puntos de los flancos ≥ 0 dB. Un valle (un canal vacío entre dos estaciones) da `R < 0` y el estado *Uncertain* (`uncertain_adjacent_leakage`): nunca un falso ocupado y nunca *Free*. Límite declarado: un canal ocupado débil junto a uno mucho más fuerte queda *Uncertain*, lo que cuenta como no detección.

**Liberar como Free** (R-06, R-59). Solo si se cumplen **todas**: `e_k ≤ 1,0 dB`; calibración *valid* o *expiring*; captura no saturada, barrido no marcado y potencia no retenida; potencia mínima declarada `D_k` configurada para el canal; `D_k − N_k ≥ 10 dB`; y el umbral de detección `T_k = N_k + 1,5 dB` no supera `D_k`. Si falta la potencia mínima declarada, el estado es *Uncertain* (`E-DET-002`); si el margen es menor de 10 dB, *Uncertain* con la razón `uncertain_margin_below_10db`.

**Uncertain** (R-07): siempre que no pueda ser *Free* o la validez no sea válida: calibración no válida o por vencer, potencia retenida, barrido marcado, captura saturada, sin datos, referencia de ruido no fiable, entrada inválida. Las razones son códigos. Una potencia cerca del piso de ruido **no** hace incierto al canal (los canales vacíos están en el piso por definición; la decisión usa el exceso). La variación lenta de ±10 dB de una señal en el día no se compensa: el estado se decide con el exceso actual.

**Ciclo de trabajo** (R-08). En cada intervalo declarado (por defecto 60 min, alineado a múltiplos UTC): `ciclo = 100·n_ocupado/(n_ocupado + n_libre)` (nulo si el denominador es 0) y `fracción_incierta = 100·n_incierto/n_barridos`. A 6 s por barrido, 60 min son 600 barridos.

**Salidas:** el estado de cada canal con razón, validez y entradas (potencia, ruido, exceso, umbral, mínimo declarado, margen); el informe del ciclo de trabajo por intervalo cerrado; la mediana del piso de ruido que usa la alerta de deriva.

**Cubre:** R-03, R-04, R-05, R-06, R-07, R-08, R-30, R-59.

### 5.8 Comparador con asignaciones

**Para qué sirve.** Contrastar el estado de ocupación de cada canal con la lista de estaciones asignadas (R-15, R-16).

| Referencia | Estado de ocupación | Resultado |
|---|---|---|
| válida, canal asignado | Occupied | `consistent` |
| válida, canal no asignado | Free | `consistent` |
| válida, canal no asignado | Occupied | `unassigned-occupied` |
| válida, canal asignado | Free | `assigned-free` |
| válida | Uncertain | `indeterminate` |
| ausente o inválida | cualquiera | `indeterminate` |

Cada resultado es uno de **4 valores**. *Uncertain* nunca se convierte en veredicto (R-14). El identificador de la referencia y la bandera `reference_used` van en cada resultado. Una recarga de la referencia reemplaza la tabla en el siguiente límite de barrido, nunca dentro de uno. Si falta la referencia o el resultado de ocupación, los 199 canales quedan `indeterminate` y no se levanta ninguna alerta desde la comparación. Tiempo asignado: 0,01 s por barrido.

`unassigned-occupied` alimenta la alerta de ocupación inesperada; `assigned-free` (solo con estados *Free*, nunca *Uncertain*) alimenta la alerta de silencio.

### 5.9 Registros de escaneo y de salud

**Para qué sirve.** Armar, por barrido, los registros que consumen el historial, el informe y las alertas.

**Qué se produce por barrido:** **1 encabezado** (hasta 4 096 bytes), **199 registros de canal** (hasta 1 024 bytes cada uno) y **1 registro de salud** (hasta 1 024 bytes). Si el barrido falla, se produce solo el registro de salud (con 0 registros publicados).

**Qué lleva cada registro de canal:** potencia calibrada y su incertidumbre con la base, razón por la que se retuvo (`power.withheld_reason`), ganancias y registro de calibración aplicable (R-29), estado de ocupación con todas sus entradas (R-30), comparación con la asignación, **límite y su comparación**, banderas y la etiqueta de evidencia de tamizaje. Potencia con resolución de 0,01 dB. Texto libre de hasta 256 bytes.

**Comparación con el límite de potencia** (R-12, R-13, R-14): una de `within_limit` (cuando `P + U ≤ L`), `outside_limit`, `indeterminate`, `not_configured` y `unavailable`. Mientras no haya límite configurado se registra `not_configured` y **nunca** se presenta como «dentro del límite». Los estados indeterminado, no configurado o no evaluable nunca se convierten en dentro o fuera.

**Registro de salud:** conteo de desbordamientos, de tramas perdidas y de registros publicados (R-27), capturas saturadas, fallos de resintonía, barrido o estimador tardío, mediana del piso de ruido, y los estados de calibración, de hora y de configuración. El encabezado de cada barrido y el informe llevan además el SHA-256 de la configuración, el identificador de la referencia y la ubicación.

**Etiqueta y vocabulario.** Todo registro lleva «Screening evidence only: not a compliance determination». Los textos se comparan contra una **lista de palabras prohibidas** (por ejemplo «compliant», «non-compliant», «violation», «infringement», «illegal», «unlawful») para que ninguna salida afirme un dictamen (R-33).

**Cubre:** R-12, R-13, R-14, R-27, R-29, R-32, R-33.

### 5.10 Historial en memoria

**Para qué sirve.** Alimentar las vistas web y la alerta de deriva con los registros recientes, **sin escribirlos nunca a disco** (R-31).

**Reglas.** Ventana de **744 h** (31 días) en bins de **60 s** (44 640 bins por canal). El historial **empieza vacío en cada reinicio** y expone `history_start_utc_us`; una vista o alerta que pida más historia de la que existe debe decir «insufficient history». La potencia de un bin proviene solo de valores liberados. Una consulta devuelve como máximo 2 000 bins por canal y 40 000 en total (por rango de tiempo, hasta 20 000 entradas). El sistema operativo no debe tener swap ni volcados de memoria. El informe en disco **no se vuelve a leer** hacia el historial.

Tras un reinicio, las vistas de 24 h están completas de nuevo a las 24 h y la alerta de deriva a las 25 h.

**Cubre:** R-31, R-39, R-41, R-43.

### 5.11 Escritor de informes

**Para qué sirve.** Guardar en disco el **informe de tamizaje** a medida que se producen los resultados (R-62, R-73).

**Estructura.** Una corrida es una carpeta `reports/<run_id>/` con: `header.json` (ubicación, registros de fecha y hora, tiempo de ejecución, modo de corrida, identificadores de configuración y calibración, manifiesto de segmentos), segmentos `scans-<hora>.csv` (los resultados: líneas de encabezado de barrido, de canal y de salud), `intervals.csv` (ciclo de trabajo por intervalo) y `progress.json`. Cada fila de canal lleva todas las entradas de su estado de ocupación (R-30) y las condiciones de liberación de *Free* (R-59).

**Guardado a medida que se produce.** Tras cada barrido las líneas se añaden al segmento abierto y se **vuelcan a la tarjeta**; un corte de energía cuesta como máximo el barrido que se estaba escribiendo. `progress.json` se actualiza cada 60 s. En el siguiente arranque, la corrida abierta se cierra desde `progress.json` con `interrupted = true`. Los segmentos se cierran cada 3 600 s con su SHA-256 en el manifiesto; un segmento sin terminar o corrupto se marca, **nunca se repara**. El encabezado y el progreso se escriben con nombre temporal y se renombran (atomicidad).

**Corrida cronometrada o continua.** Una corrida cronometrada dura el tiempo configurado (mínimo 10 min) y se cierra con su tiempo de ejecución; una continua se cierra solo por una orden de parada o una interrupción.

**Espacio.** Cada 60 s se comprueba el espacio libre. Por debajo del piso (12,8 GB) se borran los segmentos cerrados más antiguos de las corridas más antiguas, **pero nunca los últimos 30 días**; si no basta, **se deja de escribir el informe pero se sigue monitoreando** y se marca (`report_state = stopped`).

**Tamaños.** Fila de canal 200 B; barrido 41 600 B; día 599,04 MB; segmento de 600 barridos 24,96 MB.

**Otros archivos.** Los registros de calibración y de validación (carpetas `calibration/` y `validation/`) viven en la misma tarjeta y este módulo **nunca los borra**.

**Permisos.** El escritor escribe; el servicio web solo lee.

**No hace:** no escribe nada más a disco (R-31); no comprime, cifra ni envía el informe a otro lugar.

**Cubre:** R-31, R-62, R-70, R-73, R-74.

### 5.12 Motor de alertas

**Para qué sirve.** Levantar **cinco tipos de alerta, y ningún otro**, por reglas sobre los registros. Ninguna lee la potencia recibida, así que R-40 se cumple por construcción. Las alertas y el estado del motor son **volátiles**: empiezan vacíos en cada reinicio (`engine_start_utc_us`) y no se escriben a disco.

**Canal en silencio** (`channel_silent`, R-34, R-35). El silencio se cuenta a partir de **observaciones, nunca del tiempo transcurrido**. Por cada canal con estación en la referencia se lleva un «crédito de silencio» en segundos:

- Cada bin cerrado de 1 minuto (10 barridos) se lee una vez, 10 s después de su final. Un bin con **al menos 3 barridos Occupied** es activo: pone el crédito en 0, anota el final del bin como último activo y borra una alerta de silencio activa. Se piden 3 y no 1 para que el 0,14 % de falsa alarma del detector no termine una racha.
- En otro caso, cada barrido *assigned-free* del bin suma **6 s** al crédito. Un barrido *Uncertain*, *indeterminate* o ausente suma 0 s y **no reinicia** el crédito: las observaciones inciertas nunca cuentan para el silencio. Un bin con 5 barridos *assigned-free* y 5 *Uncertain* acredita 30 s, no 60 s.
- **Ciclo de trabajo previo.** La primera vez que una racha recibe crédito, el motor lee los 1 440 bins (24 h) anteriores al último bin activo y calcula el ciclo de trabajo. El estado es *busy* si ese ciclo es **mayor de 90 %** (estricto) y al menos 50 % de los 14 400 barridos de la ventana fueron *Occupied* o *Free*; *not_busy* si no supera 90 %; *insufficient_history* si la historia no alcanza o no se cumple la proporción. Se decide una vez por racha.
- La alerta se levanta **una vez por racha** cuando el crédito llega a `H × 3 600 s`, siendo `H` las horas de emisión declaradas en `alert.silent_on_air_hours`, y el estado es *busy*. Mientras `H` esté ausente la regla no se evalúa (estado `not_configured`), pero los créditos siguen acumulándose, de modo que un valor declarado después se aplica de inmediato. Como la referencia no lleva horario de emisión, **toda hora observada *assigned-free* cuenta como hora de emisión** (decisión de la persona responsable).
- Límites declarados: tras un reinicio el motor está vacío y una racha necesita 24 h de historia anterior; un bin activo suelto termina una racha con probabilidad 4,7 × 10⁻⁴ por canal-día.

**Ocupación inesperada** (`unexpected_occupancy`, R-36). Un canal con comparación `unassigned-occupied` suma 1 a su cuenta de persistencia; cualquier otro valor la pone en 0. A los **3 barridos seguidos** se levanta la alerta (12 s después del primero). Con 3 barridos las falsas alertas esperadas son 0,0079 por día (una en 127 días); con 2 serían 5,6 por día. Mientras la referencia no esté disponible la regla se congela.

**Sensor fuera de línea** (`sensor_offline`, R-37). Un «punto de salud» es un registro de salud con al menos **1 registro publicado** y sin inconsistencia (así un sensor que falla en todos los barridos no cuenta como vivo). Un temporizador monótono se reinicia con cada punto de salud y arranca con el motor; cada 1 s el vigilante levanta la alerta cuando el temporizador llega a **3 × 6 s = 18 s** (como mucho 19 s tras el último punto). Se borra tras 3 puntos de salud consecutivos. El reloj monótono no depende de la sincronización de hora.

**Calibración no demostrada** (`calibration_not_demonstrated`, R-38). La condición se cumple en un barrido cuando el estado de calibración es *expiring*, *expired*, *invalid* o *none*, o cuando alguno de los 199 registros tiene un `power.withheld_reason` de calibración (`not_demonstrated`, `expired`, `config_mismatch`, `invalid`). Se levanta en el primer barrido con la condición y lleva el estado, las razones, `verified_until_utc_us` y `expiry_margin_s`.

**Deriva del piso de ruido** (`noise_floor_drift`, R-39). Cada minuto el motor pide las medianas del piso de ruido de dos ventanas de **60 min** (600 barridos): la que termina en el bin procesado y la que terminó 24 h antes. Cada una necesita al menos 50 % de valores no nulos; la historia debe alcanzar 25 h atrás. Se levanta cuando `|M_ahora − M_ref|` supera **6 dB** (estricto).

**Cómo se borran.** Silencio: cuando un bin activo termina la racha. Sensor: como se dijo. Ocupación inesperada y calibración: tras 10 barridos seguidos sin la condición (60 s). Deriva: tras 10 evaluaciones por minuto seguidas sin ella (10 min). **Ninguna alerta se borra solo por el paso del tiempo.**

**Textos** (plantilla fija, hasta 256 bytes, comparados con la lista de palabras prohibidas):

- `channel_silent`: «Channel <n> (<station>): assigned station observed free for <h> h; duty cycle was <d> % in the 24 h before.»
- `unexpected_occupancy`: «Channel <n>: signal observed on a channel with no station assigned in reference <reference_id>.»
- `sensor_offline`: «No measuring scan reported for <s> s.»
- `calibration_not_demonstrated`: «Calibration not demonstrated: state <state>.»
- `noise_floor_drift`: «Median noise floor shifted by <x> dB over 24 h.»

Todo evento lleva `screening_evidence = true` y ningún texto afirma un dictamen. El motor guarda hasta 1 000 eventos recientes y a lo sumo 401 alertas activas.

**No hace:** no muestra las alertas (módulo 5.13); no envía nada fuera del nodo; no avisa de que el propio nodo está apagado.

**Cubre:** R-34 a R-40.

### 5.13 Servicio web

**Para qué sirve.** Mostrar a **cualquier persona de la red del sitio**, con solo un navegador y **sin inicio de sesión**, las vistas del nodo y los informes (R-41 a R-47, R-67).

**Características.** Unidad aparte (`web`), **solo lectura**, método GET o HEAD únicamente; no tiene rol, token, filtro de dirección ni ninguna ruta que escriba algo. Puerto **8080**. Todos los recursos de la página (hasta 2 MB) están en el nodo; la página no pide nada a otra dirección. Todo instante mostrado es UTC.

**Rutas:**

| Ruta | Contenido |
|---|---|
| `/` | redirige a `/power` |
| `/power` (`/api/power-map`) | **Vista 1**: potencia por canal y tiempo (R-41) |
| `/spectrum` (`/api/spectrum`) | **Vista 2**: espectro actual con marcadores de canal (R-42) |
| `/stations` (`/api/stations`) | **Vista 3**: potencia y ciclo de trabajo de estaciones seleccionadas en 24 h (R-43) |
| `/status` (`/api/status`) | **Vista 4**: estado del nodo (R-44) |
| `/alerts` (`/api/alerts`) | alertas activas con su evidencia, eventos recientes y estado de las cinco reglas (R-46) |
| `/reports`, `/reports/<run_id>/<file>` | listado y descarga de los informes guardados (R-67) |
| `/api/latest-scan` | los 199 registros del último barrido tal como se liberaron (R-47) |
| `/static/<recurso>` | archivos de la página |

**Encabezado fijo en toda página** (no se puede ocultar): la etiqueta «Screening evidence only: not a compliance determination», el identificador del nodo, la ubicación y la hora UTC de la respuesta con el estado de sincronización (señalado si no está sincronizada). Toda respuesta lleva `evidence_label`, `screening_evidence = true` y el encabezado HTTP `X-Screening-Evidence: true`. Los archivos de informe llevan la etiqueta dentro (R-32).

**Regla de liberación** (R-45). El servidor solo pone en una respuesta valores liberados: una potencia solo si `power.withheld_reason` es ninguno; un estado *Occupied* o *Free* solo con validez *valid*. Una potencia no liberada va como `null` con su razón y banderas. La página la dibuja como celda rayada o hueco con la razón en el cuadro de ayuda, **nunca como 0, valor por defecto o último valor**. Si un registro de origen rompe la regla, el valor se descarta y se cuenta el evento (`E-WEB-009`).

**Las cuatro vistas:**

- **Vista 1, potencia por frecuencia y tiempo.** Mapa con los 199 canales (frecuencia `88,1 + 0,1 × (n − 1)` MHz, nombre de la estación al lado si la referencia lo tiene) y el tiempo en columnas. La persona elige 1, 6 o 24 h (por defecto 24 h) con bins de 60, 300 o 600 s respectivamente. Escala de color fija −130 a −5 dBm (los mismos colores todos los días y en todos los sitios). Los bins sin valor liberado se rayan con la razón de retención más frecuente; una tira fina muestra las proporciones *Occupied / Free / Uncertain*. Se refresca cada 60 s.
- **Vista 2, espectro actual.** El último barrido: los tres pasos de 819 puntos unidos en una línea en 94,0 y 101,5 MHz (centro de los solapes), escala fija −130 a −5 dBm y 199 marcadores de canal. Cada marcador muestra el estado de ocupación con razón y validez, la potencia con su incertidumbre cuando está liberada, y las banderas. Si un paso está retenido, su línea no se dibuja y los marcadores muestran las banderas. Se refresca cada 6 s.
- **Vista 3, estaciones seleccionadas.** La persona elige hasta **10** estaciones por nombre o canales por número. Para cada una: potencia media liberada y ciclo de trabajo por bins de 300 s durante 24 h (288 bins), el ciclo de las 24 h completas y la fracción *Uncertain*. Sin selección la vista pide elegir (no es un error).
- **Vista 4, estado del nodo.** Las cinco magnitudes de R-44, todas leídas y ninguna recalculada: estado en línea (falso mientras haya alerta de sensor fuera de línea); antigüedad del último barrido (resaltada si es de 18 s o más); deriva del piso de ruido con las dos medianas (o «insufficient history»); conteo de desbordamientos y de tramas perdidas (valor del último registro y suma de las últimas 24 h). Además muestra estado de calibración, de hora y de configuración, identificador de la referencia, el instante de arranque del motor de alertas y del historial, y el estado del nodo del supervisor.

**Presentación de alertas** (R-46). Una barra en toda página muestra el número de alertas activas y escribe hasta 5; el resto se cuenta con un enlace a `/alerts`. Sin alertas dice «no active alert» y lista toda regla cuyo estado no sea «evaluando» (`not_configured`, `insufficient_history`, `reference_unavailable`, `input_missing`), **para que una regla que no puede ejecutarse no parezca tranquila**. La respuesta de alertas nunca se guarda en caché; la barra se refresca cada 6 s.

**Protección de la adquisición** (decisión de la persona responsable): máximo **8 solicitudes procesadas a la vez**, **64 en espera** hasta 30 s, después una respuesta «ocupado» (503 con `Retry-After` de 10 s); máximo 2 descargas a la vez y **20 MB/s** en total; nadie se rechaza por quién es. Límite de la unidad: 256 MB de memoria, 1 núcleo, prioridad 10. Cada respuesta debe armarse en 2 s como máximo. Solicitud de hasta 8 192 bytes y sin cuerpo.

**Evidencia para revisión** (R-47). Mediciones calibradas (potencias liberadas, `/api/latest-scan`), registros de monitoreo (los 199 registros y los archivos del informe), indicadores de calidad (validez, razón, banderas), incertidumbre (semiancho y base) y alertas: los cinco elementos son accesibles.

**No hace:** no calcula ocupación, deriva, alertas ni calibración (los lee; la única suma que hace es el ciclo de 24 h de una estación a partir de los conteos de bins); no cambia nada en el nodo; no cifra.

### 5.14 Supervisión y manejo de errores

**Para qué sirve.** Que una falla nunca detenga el monitoreo sin que se vea, y que el nodo se recupere solo. Tres capas, ninguna bloquea la adquisición: (1) el módulo que produce un dato **marca** el fallo en los registros que toca; (2) el **supervisor reinicia** lo que se detuvo o se colgó; (3) el **watchdog de hardware** resetea un nodo congelado.

**Reglas de vigilancia:**

- Cada unidad incrementa un contador de progreso al menos cada **1 s**; sin cambio durante **10 s** se declara colgada, se mata y se reinicia. La unidad `measure` debe publicar un barrido o un registro de salud al menos cada **12 s** mientras el nodo debe estar midiendo.
- **Escalera de reinicios:** esperas de 5, 10, 20, 40 y 60 s (tope 60 s); el supervisor nunca se rinde. Cinco reinicios de un proceso en 600 s lo declaran **en bucle**; si permanece en bucle 1 800 s, se **reinicia el nodo** (máximo 3 reinicios por 24 h; después solo sigue reiniciando procesos). Un proceso que corre 600 s sin caer se considera sano y su espera vuelve a 5 s.
- **Watchdog de hardware:** 15 s; el bucle del supervisor lo alimenta cada 5 s, solo cuando el bucle realmente corrió.
- La unidad `web` se sondea con una solicitud a `/`. La temperatura del procesador se lee cada 10 s y se **marca** (condición `thermal`), sin detener nada.
- **Estado del nodo** publicado cada 1 s: *starting*, *measuring*, *measuring_degraded*, *not_measuring*; con `power_released` (si se están liberando potencias), el estado de cada unidad y las condiciones activas. Un consumidor trata un estado de más de 5 s como «supervisor no responde».
- **Bitácora de eventos** en la tarjeta: se conservan 35 días y 50 MB como máximo, líneas de hasta 256 bytes.
- **Recuperación:** un proceso vuelve a producir barridos completos 72 s después de la última medición; tras un reinicio completo, 300 s.

**Cadena «marcar, retener, supervisar»** para los requisitos de falla: calibración no demostrable (R-21) → la potencia es `null` con razón y la ocupación *Uncertain*, más la alerta; muestra saturada (R-24) → solo se marcan los canales de su paso; desbordamiento o trama perdida (R-25, R-26) → los 199 registros del barrido marcados, potencia retenida, ocupación *Uncertain*, y reinicio tras 3 barridos marcados; todo barrido (R-27) → un registro de salud, aunque sea de un barrido fallido; sin registro de salud 3 períodos (R-37) → alerta a los 18 s (el supervisor reinicia `measure` a los 12 s sin barrido); proceso detenido o nodo congelado (R-48) → escalera de reinicios, reinicio del nodo y watchdog.

**Catálogo de errores:** todos los códigos del paquete (88) y su estado final están en el Anexo D; los códigos nuevos de otros módulos usan su propia área, nunca `E-SUP`.

**Cubre:** R-21, R-24 a R-27, R-37, R-48.

### 5.15 Reproducibilidad entre sitios

**Para qué sirve.** Demostrar que la medición, el tamizaje y los informes se reproducen al repetirlos en **otro sitio** (R-51). No agrega ninguna función al nodo: la comparación la hace la persona con los registros guardados.

**Qué debe ser idéntico en los dos sitios:** el paquete de software (SHA-256 y versión), las versiones de formatos, los ajustes de adquisición y estimador, los umbrales del detector, los pasos de los procedimientos de calibración y verificación y la **clase** de la referencia independiente (incertidumbre ≤ 0,5 dB, k = 2). **Difiere a propósito:** identificador del nodo, ubicación, referencia de estaciones, las unidades de receptor y placa, los instrumentos de referencia, los operadores y las verdades de campo. Una diferencia en un elemento idéntico hace inexplicable cualquier desacuerdo, así que **la comparación se rechaza** (`E-REP-001`) y primero se corrige el sitio.

**Tres criterios; el resultado es `agree` solo si los tres se cumplen:**

1. **Potencia calibrada en 12 puntos** (6 canales × 2 niveles, los de la verificación). Para cada punto, `D_s = diferencia` de cada sitio; `W_s = √(U_s² + u_s²)` (U: incertidumbre que reporta el nodo, 1,28 dB; u: incertidumbre de medición de la validación, 0,59 dB); `δ = D_A − D_B`; `En = |δ| / √(W_A² + W_B²)`. Un punto concuerda si **En ≤ 1**. El criterio se cumple si **al menos 10 de los 12 puntos concuerdan** (83,3 %) y **ningún |δ| supera 6 dB**. Con dos nodos buenos, un par se acepta en el 98,5 % de las repeticiones; un sesgo de 3 dB entre sitios se acepta con probabilidad inferior a 10⁻⁶.
2. **Tamizaje de cada sitio** en una corrida de 72 h: detección ≥ 95 % y falsa alarma ≤ 5 % sobre su propio conjunto de aceptación (≥ 20 observaciones ocupadas con SNR ≥ 0 dB, ≥ **60 observaciones vacantes**, de ≥ 10 canales distintos, ningún canal con más del 20 % de su denominador).
3. **Completitud de los informes.**

Las dos correcciones de frecuencia no se comparan entre sí (dos cristales difieren); cada una debe estar dentro de ±20 ppm. El resultado se escribe en un archivo (`cross_site_comparison`) que conserva la persona.

**No hace:** no cambia ningún parámetro de otro módulo; no compara señales de campo recibidas en los dos lugares (son distintas); no juzga más de dos sitios.

**Cubre:** R-51.

### 5.16 Presupuestos de tiempo, recursos y fiabilidad

Estos tres módulos **no agregan funciones ni formatos**: suman y comprueban las asignaciones de los demás. Sus cifras están en la sección 4.5 y en el Anexo A (grupos «Presupuesto de tiempo», «Presupuesto de recursos» y «Fiabilidad y disponibilidad»).

- **Tiempo:** la cadena de un barrido suma 4,98 s de los 6 s. Alerta de sensor fuera de línea a lo sumo 19 s después del último punto de salud; en pantalla a lo sumo 25,1 s. Intervalo planificado entre barridos: 7 s (límite 10 s).
- **Recursos:** límites de memoria, procesador y prioridad por unidad (sección 4.5), aplicados al arrancar; cuatro errores `E-RES-001` a `E-RES-004`.
- **Fiabilidad:** reparto de la disponibilidad (sección 4.5); procedimiento `compute_availability` para evaluar R-48 y R-49 sobre el informe y la bitácora del supervisor; procedimiento `run_field_validation` para R-61.

**Cubre:** R-01, R-37, R-48, R-49, R-57, R-61, R-66, R-72, R-73.

## 6. Archivos y datos del nodo

| Qué | Dónde | Quién escribe | Se borra |
|---|---|---|---|
| Configuración del sitio | `site-config.json` | el operador, en el nodo | nunca automáticamente |
| Referencia de estaciones | el archivo que nombra `station_reference_file` | el operador | nunca automáticamente |
| Informe de tamizaje | `reports/<run_id>/` (`header.json`, `scans-<hora>.csv`, `intervals.csv`, `progress.json`) | escritor de informes | rotación de segmentos de más de 30 días solo si falta espacio |
| Registros de calibración | `calibration/` (uno por calibración; `active.json` es el estado activo) | gestor de calibración | **nunca** |
| Registros de validación | `validation/` (uno por verificación) | módulo de verificación | **nunca** |
| Bitácora del supervisor | archivos de eventos en la tarjeta | supervisor | 35 días / 50 MB |
| Archivos temporales y contadores de progreso | sistema de archivos en memoria (64 MB) | todas las unidades | al apagar |
| Historial, alertas y caché web | **solo memoria** | `store_alert`, `web` | al reiniciar la unidad |

La **única** información de monitoreo en disco es el informe (R-31). Los registros de calibración y validación son datos persistentes del equipo, no registros de monitoreo.

## 7. Operación del nodo

Los procedimientos de esta sección los ejecuta una persona con el programa de línea de comandos local (sección 4.3), no la web.

### 7.1 Puesta en marcha de un nodo nuevo

1. Instalar el hardware (sección 4.2): antena en mástil, cable de 3 m al receptor, receptor a la placa por USB, placa con enfriador en el gabinete, fuente **fuera** del gabinete en un tomacorriente seco.
2. Instalar el software idéntico al de los demás nodos y verificar su SHA-256.
3. Escribir `site-config.json` y la referencia de estaciones del sitio; comprobar que la configuración queda *valid*.
4. **Medir el nivel máximo en el puerto de antena** con la antena y el cable reales del sitio (prueba P-088): debe ser ≤ −5 dBm; si no, el receptor puede dañarse y hay que atenuar.
5. **Calibrar** (7.2) y declarar los valores pendientes de la sección 9.
6. Iniciar la corrida de tamizaje (7.4).

### 7.2 Calibración inicial (118 min)
Antes de la primera corrida, y de nuevo tras cualquier cambio de la configuración de medición o del equipo. Procedimiento `establish_amplitude_calibration`: ver sección 5.5 y Anexo C. Requiere la fuente trazable y la terminación de 50 Ω.

### 7.3 Verificación periódica (39 min)
A intervalos que no superen el intervalo declarado. Procedimiento `verify_amplitude_correction`: ver sección 5.6 y Anexo C. Requiere la **referencia independiente**. Una verificación aprobada renueva `verified_until`; una fallida invalida la calibración y obliga a recalibrar.

### 7.4 Corrida de tamizaje
Cronometrada (el tiempo configurado, mínimo 10 min) o continua. Cada corrida genera su carpeta en `reports/`. Antes de empezar, la ubicación debe estar configurada (R-70).

### 7.5 Validación de campo de 72 h
Corrida **continua de al menos 72 h** (se planifican 76 h para absorber la recuperación de un proceso) en un sitio con **lista publicada de estaciones FM**, con una **referencia independiente registrando al menos 6 h** de ella. Se acepta una brecha de hasta 300 s entre corridas del informe (tras una parada). Procedimiento `run_field_validation`. Esta corrida **no** verifica la disponibilidad de 30 días (R-48), que se evalúa con una corrida continua de 30 días y el procedimiento `compute_availability` (la alimentación debe ser continua, garantizada por el usuario).

### 7.6 Repetición en otro sitio (reproducibilidad)
Procedimientos `repeat_at_another_site` y `compare_two_sites`, ver sección 5.15.

## 8. Pruebas y aceptación

El plan tiene **156 pruebas** (Anexo E):

| Nivel | Cantidad | Para qué |
|---|---|---|
| Aceptación | 74 | una por requisito: comprueba el criterio de aceptación de la sección 3 |
| Calificación de hardware | 21 | medir en el equipo real lo que el diseño solo calcula (tiempos, carga, temperatura, consumo, nivel de entrada, ingreso de polvo y agua, costo) |
| Procedimiento | 6 | análisis y procedimientos de operador (disponibilidad, validación de campo, reproducibilidad) |
| Integración | 33 | módulos trabajando juntos |
| Unitarias | 22 | vectores de prueba por módulo |

Cada requisito tiene su prueba en la columna «Pruebas» de la sección 3. Cada prueba da un umbral, la condición y al menos un caso nominal, uno de error y uno de borde.

**Estado:** el diseño y las pruebas están definidos y aprobados. **Ninguna prueba de calificación de hardware se ha ejecutado**; el documento no contiene resultados de medición.

## 9. Pendientes para la implementación

### 9.1 Valores que se declaran al implementar
| Valor | Dónde | Límites |
|---|---|---|
| Potencia mínima recibida declarada por canal | `declared_min_power_dbm` | −130 a −5 dBm |
| Intervalo de verificación | registro de calibración | mínimo 345 600 s; ver 9.4 para el máximo |
| Margen de vencimiento | registro de calibración | 3 600 a 604 800 s |
| Horas de silencio | `alert.silent_on_air_hours` | 0,1 a 720 h |

Hasta que se declaren: sin potencia mínima declarada **ningún canal se libera como *Free***; sin horas de silencio **no se evalúa la alerta de silencio**.

### 9.2 Pruebas de calificación de hardware por ejecutar
| Qué comprobar | Prueba | Umbral |
|---|---|---|
| Sin desbordamientos ni tramas perdidas a 10 Msps (20 MB/s), 1 h | P-075 | 0 eventos |
| Estimador en la placa | P-077 | ≤ 2,5 s por barrido |
| Detector en la placa | P-078 | ≤ 0,2 s |
| Escritura y vuelco de un barrido a la tarjeta | P-079 | ≤ 0,05 s |
| Evaluación de alertas | P-080 | ≤ 0,22 s |
| 8 clientes web sin afectar la adquisición | P-081, P-082 | 0 eventos; respuesta ≤ 2 s |
| Procesador del supervisor y de todo el nodo | P-083, P-084 | ≤ 25 %; ≤ 70 % |
| Temperatura a 40 °C ambiente (cámara, ≥ 6 h) | P-085 | aire interno ≤ 60 °C; procesador < 80 °C sin estrangular |
| Consumo del conjunto | P-086 | ≤ 20 W |
| Cadena de procesamiento de un barrido (72 h) | P-087 | ≤ 6 s (**ajustada**: holgura de 1,02 s) |
| Nivel máximo en el puerto de antena | P-088 | ≤ −5 dBm |
| Detección con SNR 0 dB sin LNA externo | P-089 | ≥ 95 % |
| Error de asignación a canal a 40 °C | P-090 | ≤ 5 kHz |
| Canal débil junto a uno 20 dB más fuerte | P-091 | ≥ 95 % |
| Pasos de ganancia y rango del receptor (no figuran en ninguna hoja de datos) | P-092 | medir |
| Ingreso de agua y polvo en entradas de cable y montaje | P-093 | 0 |
| Costo del nodo completo con precios fechados | P-094 | ≤ 3 200 USD |
| Significado de IP65 (IEC 60529) | P-095 | adjuntar la definición |

### 9.3 Cosas por confirmar
- **Instrumentos de referencia.** Confirmar que se dispone de una fuente trazable y de una referencia independiente de 0,5 dB (k = 2). Su costo está fuera de los 3 200 USD. Con instrumentos de 1,0 dB la incertidumbre total pasaría de 1,28 a ~1,6 dB (todavía bajo el límite de 2,5 dB), pero el margen de R-10 bajaría de 1,72 a ~1,4 dB y habría que cambiar parámetros; sin instrumentos no se puede calibrar.
- **Costo.** Solo se leyeron los precios del receptor y de la placa; el resto se confirma en P-094.
- **Mástil, adaptador de mástil, prensaestopas y cable de red con enchufe:** no están especificados; hay que elegirlos y probar el ingreso de agua y polvo (P-093).
- **Sistema operativo:** el requisito está propuesto (Raspberry Pi OS Lite de 64 bits como candidato) y el watchdog de hardware no figura en la hoja de datos consultada.
- **Valores propuestos, no declarados:** umbrales de reproducibilidad (ya aprobados por la persona responsable), límites del servicio web, márgenes de planificación, tasas de falla supuestas (120 reinicios de procesos y 10 reinicios completos cada 30 días), conductancia térmica del gabinete (4,8 W/K) y 4 ciclos de procesador por operación.
- **Cristal y temperatura:** la tolerancia del cristal de serie no es su deriva con la temperatura hasta 40 °C; el error de asignación a canal debe demostrarse con esa deriva (P-090).

### 9.4 Inconsistencia detectada en el valor máximo del intervalo de verificación
La justificación del límite máximo del intervalo de verificación dice «30 días, la duración de la corrida continua de R-48», pero el valor numérico aprobado es **3 456 000 s, que son 40 días**; 30 días son **2 592 000 s**. Es un error de cálculo del paquete aprobado (30 × 86 400 = 2 592 000). El intervalo mínimo (4 días = 345 600 s) está bien calculado. **Hay que decidir cuál es el máximo vigente**: si prevalece la justificación, el máximo es 2 592 000 s; si prevalece el número, 3 456 000 s. Mientras tanto, el valor práctico seguro es declarar un intervalo de **30 días o menos**.

## 10. Orden de implementación sugerido

Cada módulo depende de los anteriores:

1. Configuración del sitio, servicio de hora y hardware (montaje y calificación).
2. Adquisición y barrido → estimador espectral.
3. Calibración de amplitud → detector de ocupación → comparador.
4. Constructor de registros → historial en memoria y escritor de informes.
5. Verificación periódica → motor de alertas.
6. Servicio web.
7. Supervisión, presupuestos de recursos y de fiabilidad.
8. Calificación del hardware, validación de campo de 72 h, repetición en otro sitio.

---

*Fin del documento principal. Los anexos A a E están en la misma carpeta.*
