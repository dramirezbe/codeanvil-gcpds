# REPORTE DE PROYECTO O PROPUESTA

**Vicerrectoría de Investigación — Universidad Nacional de Colombia**

---

## INFORMACIÓN DE LA CONVOCATORA

| Campo | Detalle |
|---|---|
| Convocatoria | CONVOCATORIA CONJUNTA UNIVERSIDAD DE CALDAS, UNIVERSIDAD NACIONAL DE COLOMBIA-SEDE MANIZALES, PARA PROYECTOS DE INVESTIGACIÓN 2024 |
| Modalidad | Fortalecer las capacidades de investigación y el trabajo colaborativo entre los grupos de investigación de las universidades aliadas en esta convocatoria, a través del apoyo a proyectos que contribuyan a la solución de problemas identificados en los sectores público, social, cultural y productivo, alineado con los Objetivos de Desarrollo Sostenible. |

---

## INFORMACIÓN ACADÉMICO-ADMINISTRATIVA DEL PROYECTO

### INFORMACIÓN PRINCIPAL

| Campo | Detalle |
|---|---|
| Código del proyecto | 62848 |
| Nombre | Monitoreo SDR a exposición de IoT con alta densidad de dispositivos |
| Tipo de proyecto o programa | Proyecto o programa de investigación |
| Tipología | 2020100-Investigación aplicada |
| Estado | Activo |
| Duración del proyecto o programa (meses) | 18 |
| Tiempo de formulación | Semanas: 0 — Horas/semana: 0 |
| Proyecto relacionado (si aplica) | |
| Nombre Proyecto relacionado (si aplica) | |

### Grupo(s) de investigación (si aplica)

| ID-Hermes | Nombre | Código COL | Categoría COL | Gruplac |
|---|---|---|---|---|
| 615 | GRUPO DE CONTROL Y PROCESAMIENTO DIGITAL DE SEÑALES — 4- FACULTAD DE INGENIERÍA Y ARQUITECTURA | COL0007909 | A1 | HERMES: http://www.hermes.unal.edu.co/pages/Consultas/Grupo.jsf?idGrupo=615 — GRUPLAC: https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000001375 |

---

## INFORMACIÓN DEL DIRECTOR

| Campo | Detalle |
|---|---|
| Director | JULIO CESAR GARCIA ALVAREZ |
| Documento del director | C - 89003057 |
| E-mail del director | jcgarciaa@unal.edu.co |

### INFORMACIÓN DEL DIRECTOR DE LA RED DE COOPERACIÓN

| Campo | Detalle |
|---|---|
| Escuela/departamento del director | 4- DEPARTAMENTO DE INGENIERÍA ELÉCTRICA, ELECTRÓNICA Y COMPUTACIÓN |
| Facultad del director | 4- FACULTAD DE INGENIERÍA Y ARQUITECTURA |
| Sede del director | Manizales |
| Horas/semana de dedicación al proyecto | 6 |
| Valor de la dedicación | $56.055.024 |
| Funciones | Responsable de liderar el proyecto, definir la dirección estratégica, asegurar el cumplimiento de los objetivos científicos y técnicos, y supervisar todas las actividades de investigación. Este rol incluye la mentoría de los estudiantes involucrados y la coordinación con otros colaboradores. |

---

## DEPENDENCIAS RESPONSABLES

4- DIRECCIÓN DE INVESTIGACIÓN Y EXTENSIÓN

---

## INFORMACIÓN GENERAL

### Resumen

El Grupo de Control de Procesamiento Digital de Señales (GCPDS) planea gestionar y supervisar los niveles de exposición eléctrica para evaluar su impacto en la salud. Utilizando Radio Definido por Software (SDR), en equipos de bajo costo, se busca respaldar la adquisición de datos sobre el espectro eléctrico y realizar el procesamiento y análisis de señales en las bandas de frecuencia. El SDR permite una medición precisa de la densidad espectral y la distribución espacial de los campos eléctricos, adaptándose dinámicamente a las variaciones espectrales y facilitando un análisis detallado de los patrones de emisión y exposición. El GCPDS enfrenta desafíos en la gestión del espectro electrico, motivando la propuesta de un sistema de monitoreo para bandas de frecuencia entre 700 Mhz y 3.5 Ghz. La dispersión de datos y la necesidad de adaptarse a los avances tecnológicos, especialmente con el despliegue de redes IoT, hacen crucial la eficiencia del monitoreo. A pesar de la evolución de las herramientas de monitoreo, la implementación de redes distribuidas sigue siendo costosa debido al hardware y software necesarios. Las soluciones convencionales enfrentan limitaciones en entornos dinámicos y la creciente demanda de gestión integral del espectro para aplicaciones como radiodifusión y telefonía móvil.

La clasificación y detección de señales son desafíos tecnológicos donde los enfoques convencionales tienen limitaciones en el manejo de características de alta dimensión. El aprendizaje automático y profundo emergen como soluciones potenciales, aunque con retos en la extracción de características y manejo de ambigüedad en la clasificación de señales. El SDR ofrece una oportunidad para superar los obstáculos económicos gracias a su baja inversión inicial y flexibilidad de programación. La propuesta del proyecto se centra en desarrollar e implementar una red avanzada, multibanda y económica de monitoreo del espectro electrico. Se desarrollará un prototipo integral para monitorear la densidad de potencia del espectro (PSD) utilizando aprendizaje profundo, SDR y computadoras de bajo costo, enfocándose en la Banda en rangos de frecuencia entre 700 Mhz y 3.5 Ghz. Se evaluarán los niveles de exposición a campos electricos.

El objetivo es proporcionar una supervisión del espectro más efectiva y flexible, capaz de ajustarse a las fluctuaciones y demandas cambiantes del entorno, superando las restricciones de los sistemas centralizados tradicionales. La estrategia incluye la unificación de la información recolectada por estaciones locales en Caldas y su análisis centralizado. Modelos avanzados de aprendizaje profundo mejorarán la detección y clasificación de señales, facilitando la toma de decisiones y garantizando el cumplimiento de las normativas vigentes. El prototipo tendrá un impacto significativo en el monitoreo del espectro eléctrico, alineado con las regulaciones de la ITU-T K52. Este proyecto mejorará la capacidad de monitoreo, permitiendo un análisis preciso y eficiente del espectro y estableciendo un sistema adaptable a futuras innovaciones tecnológicas en el campo de las radiocomunicaciones.

### Descripción del problema u oportunidad a la cual responde el proyecto

El estudio se centra en la importancia de monitorear la radiación eléctrica en entornos laborales debido a su impacto potencial en la salud. Se enfoca específicamente en los niveles de radiación en espacios cerrados con alta concentración de dispositivos IoT y su efecto en la salud de los trabajadores [15]. La proliferación de tecnologías IoT en oficinas y fábricas ha generado preocupaciones sobre la exposición a campos eléctricos. La Recomendación UIT-T K.52 ofrece directrices para garantizar que las instalaciones de telecomunicaciones cumplan con los límites de seguridad según la ICNIRP.

Los analizadores de espectro tradicionales son voluminosos y costosos, lo que limita su portabilidad y accesibilidad económica [6]. Esto es problemático para estudios en áreas urbanas y para monitorear redes IoT, que requieren técnicas avanzadas como spectrum sensing [17]. Aunque los SDR son una alternativa más práctica y económica, enfrentan limitaciones en rango dinámico y frecuencia máxima [68][69][70].

El monitoreo de espectro en aplicaciones IoT necesita un diseño adaptable capaz de operar en un amplio rango de frecuencias [12]. La rapidez y precisión en la medición en entornos urbanos son esenciales para identificar áreas con altos niveles de radiación y asegurar el cumplimiento normativo. Sin instrumentos adecuados, el monitoreo es ineficiente y costoso [19].

Para optimizar el monitoreo de radiación eléctrica en áreas con alta concentración de dispositivos IoT, es crucial desarrollar algoritmos avanzados de umbralización que integren técnicas de aprendizaje de máquina [28]. Estos algoritmos deben adaptarse a las fluctuaciones y complejidad de las señales, aunque los métodos comunes enfrentan dificultades bajo condiciones de baja SNR [2][27] y variaciones de dispositivos IoT [71].

La generación de mapas de campo eléctrico presenta desafíos significativos, como correlacionar la densidad de dispositivos IoT con los niveles de radiación y la medición precisa de la concentración de dispositivos [17]. También es importante interpretar los datos en relación con las frecuencias utilizadas y sus posibles efectos adversos en la salud [10].

Es esencial realizar evaluaciones exhaustivas para no subestimar los riesgos de exposición prolongada a campos eléctricos en entornos laborales, donde pueden surgir alteraciones neurológicas, trastornos del sueño y, en casos severos, un aumento en el riesgo de condiciones degenerativas o cancerígenas [9]. Además, la acumulación de carga espacial interna y las perturbaciones en la carga pueden alterar la distribución del campo eléctrico, complicando las evaluaciones de cumplimiento con las normas de seguridad [32].

### Objetivo general

Desarrollar un sistema para la evaluación de niveles de exposición humana a campos eléctricos, basado en software definido por radio (SDR) y técnicas de aprendizaje de máquina, que permita la medición de la densidad de radiación en ambientes cerrados con alta ocupación de dispositivos IoT.

---

## OBJETIVOS ESPECÍFICOS

| Objetivo específico | Medio de verificación |
|---|---|
| - Desarrollar algoritmos de umbralización y procesos cooperativos basados en métodos de aprendizaje de máquina para lidiar con la variabilidad de medida de señal en ambiente cerrados con alto índice de interferencias. | Informe científico-técnico de los algoritmos de IA. Informe científico-técnico con los resultados de pruebas y validación de los algoritmos. Informe científico-técnico con los resultados de validación y demostración del funcionamiento de los procesos cooperativos. |
| - Diseñar y construir un módulo de medida sobre SDR que permita el monitoreo espectral de redes IoT con alta densidad de dispositivos en espacios cerrados empleando técnicas de sensado espectral. | Aprobación del documento de requisitos por parte del equipo de proyecto. Revisión y aprobación del diseño por parte del equipo técnico. Pruebas de funcionamiento y validación del módulo SDR. |
| - Generar mapas espaciales de campos eléctricos mediante técnicas avanzadas de medición y análisis de datos para evaluar el cumplimiento de las normativas de exposición humana, proporcionando resultados a través de informes detallados y presentaciones técnicas en base a las entidades reguladoras y organizaciones interesadas. | Documentación y resultados de pruebas de las técnicas desarrolladas. Informes de evaluación de los mapas de campo en comparación con las normas de exposición. |

---

## RESULTADOS ESPERADOS

| Resultado | Medio de verificación | Fecha |
|---|---|---|
| - Algoritmos de umbralización funcionales. | Informe científico-técnico con los resultados de pruebas y validación de los algoritmos. | 31 de julio de 2026 |
| - Documento de requisitos del sistema. | Aprobación del documento de requisitos por parte del equipo de proyecto. | 31 de julio de 2026 |
| - Esquemas y diagramas de diseño del módulo SDR. | Revisión y aprobación del diseño por parte del equipo técnico. | 31 de julio de 2026 |
| - Mapas de campo generados y evaluados. | Informes de evaluación de los mapas de campo en comparación con las normas de exposición. | 31 de julio de 2026 |
| - Módulo SDR funcional y operativo. | Pruebas de funcionamiento y validación del módulo SDR. | 31 de julio de 2026 |
| - Procesos cooperativos integrados y operativos. | Informe científico-técnico con los resultados de validación y demostración del funcionamiento de los procesos cooperativos. | 31 de julio de 2026 |
| - Selección de algoritmos de IA. | Informe científico-técnico de los algoritmos de IA. | 31 de julio de 2026 |
| - Técnicas de sensado y mapeo desarrolladas. | Documentación y resultados de pruebas de las técnicas desarrolladas. | 31 de julio de 2026 |

---

## PRODUCTOS

| Producto | Descripción | Cantidad |
|---|---|---|
| Artículo científico o de investigación sometido o, aceptado o aprobado para publicación en revista indexada | Artículo científico o de investigación sometido o, aceptado o aprobado para publicación en revista indexada | 1 |
| TDG (Trabajo dirigido de grado) | TDG (Trabajo dirigido de grado) | 2 |

---

## REGIÓN QUE IMPACTA EL PROYECTO

| Departamento | Ciudad |
|---|---|
| Caldas | Manizales |

---

## PROPIEDAD INTELECTUAL

¿Considera que este proyecto puede generar uno de los siguientes activos de propiedad intelectual? **No**

## BIODIVERSIDAD

¿En su investigación hará uso de los recursos de la biodiversidad colombiana? **No**

## LABORATORIOS

¿Dentro de la ejecución del proyecto va hacer uso de los servicios de laboratorios? **No**

---

## CLASIFICACIÓN

| Campo | Detalle |
|---|---|
| Objetivo de desarrollo sostenible principal | Garantizar una vida sana y promover el bienestar de todos en todas las edades |
| Objetivos de desarrollo sostenible secundarios | Construir infraestructuras resilientes, promover la industrialización inclusiva y sostenible y fomentar la innovación |
| Objetivo socioeconómico | Transporte, telecomunicaciones y otras infraestructuras |

---

## ÁREAS CIENTÍFICAS/TEMÁTICAS

| Area científica y tecnológica principal - OCDE | Sub-área de la ciencia |
|---|---|
| Ingeniería y tecnología | Ingenierías eléctrica, electrónica e informática |

| Area científica y tecnológica secundaria | Sub-área de la ciencia |
|---|---|
| Ingeniería y tecnología | Otras ingenierías y tecnologías |

---

## PLAN GLOBAL DE DESARROLLO UNIVERSIDAD NACIONAL DE COLOMBIA

| Campo | Detalle |
|---|---|
| Política | Plan Global de Desarrollo 2022-2024: Proyecto cultural, científico y colectivo de nación |
| Elemento estratégico | Plan Global de Desarrollo 2022-2024: Proyecto cultural, científico y colectivo de nación |
| Línea de acción | Armonización de las funciones misionales para la formación integral |
| Programa | Armonización de las funciones misionales para la gestión del conocimiento |

---

## PALABRAS CLAVE

- APRENDIZAJE DE MAQUINA
- Prototipo Costo-eficiente
- Radio Definido por Software
- Redes WiFi
- Tecnología IoT

---

## INTEGRANTES

| Participante | Unidad | Vinculación | Horas/semana | Meses | Valor ($ dedicación) | Función | Fecha de vinculación |
|---|---|---|---|---|---|---|---|
| CESAR GERMAN CASTELLANOS DOMINGUEZ (C - 79439458) (cgcastellanosd@unal.edu.co) | 4- DEPARTAMENTO DE INGENIERÍA ELÉCTRICA, ELECTRÓNICA Y COMPUTACIÓN Grupo: | Profesor carrera docente UN | 3 | 16 | | - Evaluación de los requerimientos técnicos y operativos para habilitar un monitoreo eficiente de las bandas de interés. - Selección de la arquitectura de red más adecuada para el análisis espectral de las señales capturadas. - Impulsar la divulgación científica y académica de los avances y resultados obtenidos. | 8/05/2025 0:00 |
| CARLOS ANDRES ALTAMIRANDA GONZALEZ (C - 1007251945) (caltamiranda@unal.edu.co) | 4- FACULTAD DE INGENIERÍA Y ARQUITECTURA Grupo: | Estudiante posgrado UN | 20 | 16 | | - Desarrollo de algoritmos para la evaluación de exposición a campos electromagnéticos. - Responsable por dar impulso a la divulgación científica y académica. - Supervisión general junto con los investigadores vinculados al proyecto. - Integración de algoritmos de procesamiento de señales. - Desarrollo y optimización de modelos de aprendizaje profundo. | 16/07/2025 16:45 |
| MARTIN RAMIREZ ESPINOSA (T - 1054862227) (maramirezes@unal.edu.co) | 4- FACULTAD DE INGENIERÍA Y ARQUITECTURA Grupo: | Estudiante pregrado UN | 20 | 16 | | - Programación y calibración de sensores SDR. - Optimización y captura de datos con sensores SDR. - Pruebas exhaustivas de funcionamiento de sensores SDR. | 16/07/2025 16:45 |
| JORGE ALBERTO JARAMILLO GARZON (C - 16076495) (jajaramillog@unal.edu.co) | No disponible Grupo: | Profesor o investigador externo | 6 | 10 | | Supervisar las actividades de la investigación, asesorando a los estudiantes involucrados en el campo del análisis de información. Demás funciones que habían sido asignadas al profesor Marcelo Herrera Gonzalez. | 23/04/2026 15:00 |
| DAVID RAMIREZ BETANCOURTH (C - 1002636667) (dramirezbe@unal.edu.co) | 4- DEPARTAMENTO DE INGENIERÍA ELÉCTRICA, ELECTRÓNICA Y COMPUTACIÓN Grupo: | Estudiante pregrado UN | 20 | 16 | | - Recolección de datos del espectro electromagnético usando el dispositivo a diseñar. - Programación de sensores SDR. - Desarrollo de plataforma para visualización espectral. - Optimización de procesos vía microprocesadores. - Recolección de datos del espectro. | 16/07/2025 16:45 |

---

## HISTÓRICO DEL EQUIPO DE TRABAJO

| Documento | Nombre | Vinculación | Tipo de solicitud | Valor pagar | Fecha del cambio |
|---|---|---|---|---|---|
| (C - 1002566760) | ALEJANDRO PATIÑO BEDOYA | Estudiante pregrado UN | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | $0 | 16/07/2025 16:45 |
| (C - 1002566760) | ALEJANDRO PATIÑO BEDOYA | Estudiante pregrado UN | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | | 16/07/2025 16:45 |
| (C - 1002636667) | DAVID RAMIREZ BETANCOURTH | Estudiante pregrado UN | VINCULACIÓN AL EQUIPO DE TRABAJO | $0 | 16/07/2025 16:45 |
| (C - 1007251945) | CARLOS ANDRES ALTAMIRANDA GONZALEZ | Estudiante posgrado UN | VINCULACIÓN AL EQUIPO DE TRABAJO | $0 | 16/07/2025 16:45 |
| (T - 1054862227) | MARTIN RAMIREZ ESPINOSA | Estudiante pregrado UN | VINCULACIÓN AL EQUIPO DE TRABAJO | $0 | 16/07/2025 16:45 |
| (C - 1057782148) | JEFERSON ARANGO LOPEZ | Profesor o investigador externo | VINCULACIÓN AL EQUIPO DE TRABAJO | $0 | 19/09/2025 9:06 |
| (C - 1057782148) | JEFERSON ARANGO LOPEZ | Profesor o investigador externo | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | $0 | 23/04/2026 15:00 |
| (C - 1057782148) | JEFERSON ARANGO LOPEZ | Profesor o investigador externo | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | | 23/04/2026 15:00 |
| (C - 1060597763) | JULIAN ANDRES SALAZAR PARIAS | Estudiante posgrado UN | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | $0 | 16/07/2025 16:45 |
| (C - 1060597763) | JULIAN ANDRES SALAZAR PARIAS | Estudiante posgrado UN | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | | 16/07/2025 16:45 |
| (C - 1112631769) | LUIS FELIPE GIRALDO DIAZ | Estudiante externo | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | $0 | 23/04/2026 15:00 |
| (C - 1112631769) | LUIS FELIPE GIRALDO DIAZ | Estudiante externo | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | | 23/04/2026 15:00 |
| (C - 16076495) | JORGE ALBERTO JARAMILLO GARZON | Profesor o investigador externo | VINCULACIÓN AL EQUIPO DE TRABAJO | $0 | 23/04/2026 15:00 |
| (C - 75086953) | MARCELO HERRERA GONZALEZ | Profesor o investigador externo | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | $0 | 23/04/2026 15:00 |
| (C - 75086953) | MARCELO HERRERA GONZALEZ | Profesor o investigador externo | DESVINCULACIÓN DEL EQUIPO DE TRABAJO | | 23/04/2026 15:00 |
| (C - 79439458) | CESAR GERMAN CASTELLANOS DOMINGUEZ | Profesor carrera docente UN | VINCULACIÓN AL EQUIPO DE TRABAJO | $134.779.824 | 16/07/2025 16:45 |

---

## PRÓRROGAS EQUIPO DE TRABAJO

| Documento | Nombre | Vinculación | Valor pagar | Fecha del cambio |
|---|---|---|---|---|
| No se encontraron solicitudes relacionadas con el equipo de trabajo. | | | | |

---

## INFORMACIÓN FINANCIERA

Lugar(es) de ejecución financiera del proyecto: **5- DIRECCIÓN DE INVESTIGACIÓN Y EXTENSIÓN**

### FUENTES DE FINANCIACION

| Fuente de financiación | Tipo | Naturaleza | Valor especie ($) | Valor efectivo ($) |
|---|---|---|---|---|
| UNIVERSIDAD NACIONAL DE COLOMBIA | Interna | Pública | $0 | $50.000.000 |
| UNIVERSIDAD DE CALDAS | Externa | Nacional | $27.898.560 | $50.000.000 |

### PROPUESTA DE FINANCIACIÓN CÁTALOGO VIGENTE

| Fuente de financiación | Cuenta | Objeto | Subordinal / Rubro | Descripción | Valor especie ($) | Valor efectivo ($) | Total ($) |
|---|---|---|---|---|---|---|---|
| UNIVERSIDAD DE CALDAS | Cuenta: Contrapartidas | Objeto: Contrapartidas | Gastos de Personal - Contrapartida | Contrapartida | $27.898.560 | $0 | $27.898.560 |
| UNIVERSIDAD DE CALDAS | Cuenta: Adquisición De Bienes Y Servicios | Objeto: Activos Fijos | Equipo Y Aparatos De Radio, Televisión Y Comunicaciones | Gasto | $0 | $40.000.000 | $40.000.000 |
| UNIVERSIDAD DE CALDAS | Cuenta: Adquisición De Bienes Y Servicios | Objeto: Activos Fijos | Maquinaria De Oficina, Contabilidad E Informática | Gasto | $0 | $10.000.000 | $10.000.000 |
| UNIVERSIDAD NACIONAL DE COLOMBIA | Cuenta: Adquisición De Bienes Y Servicios | Objeto: Activos Fijos | Maquinaria De Oficina, Contabilidad E Informática | Gasto | $0 | $20.000.000 | $20.000.000 |
| UNIVERSIDAD NACIONAL DE COLOMBIA | Cuenta: Gastos De Comercialización Y Producción | Objeto: Adquisición De Servicios | Servicios De Investigación Y Desarrollo | Gasto | $0 | $30.000.000 | $30.000.000 |

### PROPUESTA DE FINANCIACIÓN CATÁLOGO ANTERIOR

| Fuente de financiación | Subordinal / Rubro | Valor especie ($) | Valor efectivo ($) | Total ($) |
|---|---|---|---|---|

### ENTIDADES PARTICIPANTES

| Entidad | Tipo | Valor especie ($) | Valor efectivo ($) |
|---|---|---|---|
| INFERENCE S.A.S | Externa | $15.000.000 | $0 |
| DUNDERLAB S.A.S | Externa | $15.000.000 | $0 |
| OPEN BUSINESS CONSULTING S.A.S | Externa | $15.000.000 | $0 |

### VALOR TOTAL

| Concepto | Valor |
|---|---|
| Valor financiado fuente externa | $50.000.000 |
| Valor en especie fuente externa | $27.898.560 |
| Valor entidades participantes | $45.000.000 |
| Personal docente | $56.055.024 |
| Personal administrativo | $0 |
| Contrapartida en efectivo/valor financiado interno | $50.000.000 |
| Contrapartida en especie fuente interna | $0 |
| **Valor total del proyecto** | **228,953,584** |

---

## INFORMACIÓN ESPECÍFICA

### CIUDADES

Manizales

---

## Metodología propuesta

Para el desarrollo del objetivo específico 1, la metodología se basa en una serie de actividades bien definidas. Primero, se realizará un análisis de requisitos del sistema SDR, donde se identificarán y documentarán los requisitos técnicos y funcionales. Esto incluye la recopilación de requisitos de usuario y especificaciones técnicas, así como la evaluación del hardware y software disponibles. Posteriormente, se procederá al diseño del módulo SDR, creando un diseño detallado para el monitoreo espectral con el dispositivo USRP B200 Mini y una antena TG.62.A113, procesando los datos con una Jetson Nano. Las tareas en esta fase abarcan el desarrollo de diagramas de arquitectura del sistema, la selección de componentes de hardware y software, y la elaboración de esquemas y diagramas de circuitos. Finalmente, se llevará a cabo la construcción y configuración del módulo SDR, lo cual implica la adquisición de los componentes necesarios, el montaje y ensamblaje del hardware, y la instalación y configuración del software.

En cuanto al objetivo específico 2, la metodología incluye la investigación y selección de algoritmos de inteligencia artificial adecuados para la umbralización y procesos cooperativos, enfocados en la adición de densidad espectral en zonas de alta ocupación de tecnologías IoT. Este proceso comenzará con una revisión de la literatura y tecnologías existentes, seguida de la selección de algoritmos basados en criterios de rendimiento y aplicabilidad. Luego, se desarrollarán los algoritmos de umbralización, incorporando técnicas avanzadas de inteligencia artificial para mejorar la precisión en la medición de radiación y reducir el riesgo de falsas alarmas. Este enfoque utiliza una estrategia de detección cooperativa para optimizar el procesamiento de señales y análisis de datos. La última fase en este objetivo será la implementación de procesos cooperativos basados en IA, diseñando y probando estos procesos en el entorno SDR y finalmente integrándolos con el módulo SDR.

Para el objetivo específico 3, la metodología se enfocará en el desarrollo de técnicas de sensado y mapeo, utilizando tecnología como el Jetson Nano para facilitar el procesamiento eficiente de datos en tiempo real. Se investigarán métodos avanzados de sensado espacial y se desarrollarán algoritmos para la generación de mapas de campo. Las técnicas desarrolladas permitirán la creación de representaciones visuales detalladas y precisas de los campos de medida. Luego, se generarán y evaluarán mapas de campo de medida, explorando el uso de métodos de interpolación y muestreo selectivo para optimizar la distribución de los puntos de medición, reduciendo así el esfuerzo y coste asociados al proceso de mapeo sin comprometer la precisión y resolución de los datos recogidos. Esto demostrará la eficacia de la interpolación de Kriging y el muestreo selectivo para minimizar los puntos de medición necesarios en la generación de mapas de exposición al campo eléctrico en entornos interiores.

---

## Antecedentes y marco teórico

Existen algunos desafíos relacionados en la monitoreo y gestión de las emisiones radioeléctricas, por ejemplo, el desarrollo de sistemas de multipropósito y de bajo costo para realizar el escaneo y análisis efectivo de los servicios evaluando aspectos fundamentales como la ocupación del espectro y los niveles de exposición a Campos eléctrico.

Este estudio aborda las preocupaciones sobre los peligros de la exposición a campos eléctricos generados por la creciente proliferación de dispositivos IoT en entornos laborales como oficinas y fábricas[11]. Se enfoca en los niveles de radiación en espacios cerrados con alta concentración de estos dispositivos y su efecto en la salud de los trabajadores, subrayando la importancia de monitorear la radiación eléctrica en estos entornos debido a su impacto potencial en la salud [5].

La Recomendación UIT-T K.52 ofrece directrices y métodos de evaluación para asegurar que las instalaciones de telecomunicaciones respeten los límites de seguridad, basándose en criterios establecidos por la Comisión Internacional sobre Protección contra las Radiaciones No Ionizantes (ICNIRP). En entornos con alta concentración de dispositivos IoT, es crucial desarrollar un sistema de radio definido por software (SDR) que permita la medición precisa de la radiación eléctrica. El SDR se presenta como una alternativa portátil y económica a los analizadores de espectro tradicionales, adecuada para estudios de propagación en áreas urbanas [13].

El diseño de un SDR optimizado para aplicaciones IoT facilitará evaluaciones precisas en un rango de frecuencias de 700 MHz a 3.5 GHz, cubriendo las bandas de operación más críticas[19]. La capacidad de estos instrumentos para realizar cientos de mediciones rápidamente sin sacrificar la precisión es invaluable en entornos urbanos, ayudando a identificar áreas con altos niveles de radiación y garantizando el cumplimiento de las normativas vigentes [18].

Para optimizar el monitoreo y control de la radiación eléctrica en áreas cerradas con alta concentración de dispositivos IoT, es fundamental desarrollar algoritmos avanzados de umbralización que integren técnicas de aprendizaje de máquina[5]. Estos algoritmos permiten adaptar los umbrales de detección de manera dinámica en respuesta a las fluctuaciones y la complejidad de las señales y el ruido, extrayendo patrones útiles de datos históricos y actuales [4].

Algoritmos basados en aprendizaje automático, que utilizan un enfoque cooperativo con intercambio de información entre múltiples sensores, pueden integrar datos de diversas fuentes para mejorar la detección y minimizar falsas alarmas, incrementando así la robustez y precisión en el monitoreo de radiación en zonas densamente equipadas con dispositivos IoT[28]. Este método colaborativo no solo mejora la exactitud de la detección, sino que también adapta los sistemas de monitoreo a las variaciones del entorno, asegurando mediciones confiables y precisas, cruciales para la seguridad y eficiencia operativa [5].

La generación de mapas de campo eléctrico es crucial para evaluar el cumplimiento de las normativas sobre exposición humana a campos eléctricos. Este análisis detallado implica correlacionar la densidad de dispositivos IoT con los niveles de radiación que emiten y su impacto en la salud. Examinar la concentración de dispositivos en espacios cerrados y su relación con los niveles de radiación observados permite una comprensión más profunda de las frecuencias utilizadas y sus posibles efectos adversos en la salud, basándose en estudios científicos y médicos [14].

---

## Resultados esperados.

Desarrollo de una sistema para el monitoreo niveles de exposición de campos eléctricos, validada en entornos reales.
Prototipo funcional del sistema de monitoreo - TRL 7

Registro de software desarrollado ante la Dirección Nacional de Derecho de Autor, validando la propiedad intelectual del desarrollo TRL 7. Se creará un repositorio accesible que contendrá los instaladores, el código fuente, manuales y otros documentos de soporte necesarios.

Con respecto a los estudiantes de pregrado vinculados al proyecto, se elaborarán informes que detallan tanto las actividades realizadas como los avances y descubrimientos obtenidos.

En el caso de los estudiantes de maestría, se proporcionará un resumen exhaustivo y un informe técnico que documenten el trabajo y los hallazgos innovadores logrados durante su participación en el proyecto.

---

## Consideraciones Éticas

El proyecto de monitoreo SDR de la exposición a IoT con alta densidad de dispositivos presenta varias consideraciones éticas esenciales que deben abordarse para asegurar la integridad y responsabilidad social de la investigación.

-Privacidad y Confidencialidad: La recolección de datos en entornos laborales y públicos puede implicar la captura de información sensible sobre individuos y empresas. Es fundamental garantizar que todos los datos recolectados se manejen con estricta confidencialidad y se almacenen de manera segura. Además, se deben implementar medidas para anonimizar los datos personales y asegurar que la información utilizada no pueda ser rastreada hasta individuos específicos sin su consentimiento expreso.

-Consentimiento Informado: Los participantes en el estudio, especialmente los trabajadores en los entornos monitoreados, deben ser plenamente informados sobre la naturaleza del proyecto, los objetivos, los riesgos potenciales y los beneficios esperados. Deben otorgar su consentimiento libre e informado antes de que cualquier dato sea recolectado. Esto también incluye la capacidad de los participantes para retirar su consentimiento en cualquier momento sin repercusiones negativas.

-Impacto en la Salud: La investigación debe priorizar la seguridad y el bienestar de los participantes. Dado que el estudio se enfoca en la exposición a campos eléctricos, es crucial asegurar que las metodologías utilizadas no incrementen los niveles de radiación a los que están expuestos los individuos. Además, cualquier hallazgo que sugiera un riesgo para la salud debe ser comunicado de inmediato a las autoridades pertinentes y a los participantes, junto con recomendaciones para mitigar esos riesgos.

-Transparencia y Divulgación: Los resultados del estudio deben ser compartidos de manera transparente con todas las partes interesadas, incluidas las comunidades locales, autoridades de salud, y organismos reguladores. La divulgación de los resultados debe hacerse de manera accesible y comprensible, permitiendo que las partes interesadas tomen decisiones informadas sobre la exposición a campos eléctricos y las medidas de protección necesarias.

-Responsabilidad Social: Es fundamental que el proyecto se conduzca con un alto sentido de responsabilidad social, considerando el impacto más amplio en la comunidad y el medio ambiente. Esto incluye evaluar y minimizar cualquier posible repercusión negativa del despliegue de tecnologías de monitoreo en los entornos estudiados.

- Cumplimiento Normativo: El proyecto debe adherirse a todas las leyes y regulaciones locales e internacionales relacionadas con la investigación, la protección de datos, y la seguridad laboral. Además, debe seguir las directrices establecidas por la Comisión Internacional sobre Protección contra las Radiaciones No Ionizantes (ICNIRP) y otras organizaciones relevantes para garantizar la seguridad y bienestar de los participantes.

Evaluación y Mitigación de Riesgos: Antes del inicio del proyecto, se debe realizar una evaluación exhaustiva de riesgos para identificar posibles impactos negativos y desarrollar estrategias de mitigación. Este proceso debe ser continuo, con revisiones periódicas durante todo el proyecto para ajustar las medidas de mitigación según sea necesario.

Al adherirse a estas consideraciones éticas, el proyecto no solo promoverá la integridad científica y la responsabilidad social, sino que también garantizará la confianza y el apoyo de la comunidad y las partes interesadas en los resultados obtenidos.

---

## Areas temáticas

- Tecnologías convergentes e industrias 4.0.
- Tecnologías Convergentes (nano, info y cognotecnología) e Industrias 4.0 IA CiberArtes, Cultura y Patrimonio

---

## ACTIVIDADES Y CRONOGRAMA

| Actividad | Responsable | Mes inicial | Duración |
|---|---|---|---|
| Evaluación de Requerimientos Técnicos y Operativos:Determinación de las necesidades técnicas y operativas para el monitoreo de bandas de interés. | JULIO CESAR GARCIA ALVAREZ | 1 | 2 |
| Recolección de Datos del Espectro | JULIO CESAR GARCIA ALVAREZ | 2 | 4 |
| Programación y calibración de Sensores SDR | JULIO CESAR GARCIA ALVAREZ | 2 | 6 |
| Impulso a la Divulgación Científica y Académica | JULIO CESAR GARCIA ALVAREZ | 3 | 15 |
| Pruebas Exhaustivas de Funcionamiento de Sensores SDR | JULIO CESAR GARCIA ALVAREZ | 8 | 2 |
| Integración de Algoritmos de Procesamiento de Señales | JULIO CESAR GARCIA ALVAREZ | 10 | 2 |
| Implementación de Procesos Cooperativos Basados en IA | JULIO CESAR GARCIA ALVAREZ | 11 | 4 |
| Optimización y Captura de Datos con Sensores SDR | JULIO CESAR GARCIA ALVAREZ | 12 | 2 |
| Desarrollo de Algoritmos para la Evaluación de Exposición a Campos Electromagnéticos | JULIO CESAR GARCIA ALVAREZ | 13 | 3 |
| Selección Detallada de Arquitecturas de Red para Análisis Espectral | JULIO CESAR GARCIA ALVAREZ | 13 | 5 |
| Desarrollo y Optimización de Modelos de Aprendizaje Profundo | JULIO CESAR GARCIA ALVAREZ | 14 | 4 |
| Integración y Operación de Modelos | JULIO CESAR GARCIA ALVAREZ | 15 | 3 |
| Generación y Evaluación de Mapas de Campo de Medida | JULIO CESAR GARCIA ALVAREZ | 15 | 3 |

---

## BIBLIOGRAFÍA

[11] Muhammad Saifullah, Bajwa, I. S., Ibrahim, M., Asghar, M., & Bicocchi, N. (2022). IoT-Enabled Intelligent System for the Radiation Monitoring and Warning Approach. Mobile Information Systems, 2022, Article 2769958.

[13] Ranjbar, M., & otros. (2021). Energy efficiency of full-duplex cognitive radio in low-power regimes under imperfect spectrum sensing. Mobile Networks and Applications.

[16] Subray, S., Tschimben, S., & Gifford, K. (2021). Towards Enhancing Spectrum Sensing: Signal Classification Using Autoencoders. IEEE Access, 9, 82288–82299.

[17] Tuta, L., Panait-Radu, F., Ardelean, F., Gorgoteanu, D., & Rosu, G. (2023). SDR-Based Portable System for Evaluating Exposure to Ambient Electromagnetic Fields. Electronics, 12(24), Article 5003.

[3] Ataman, F. (2021). The Spectrum Sensing Techniques and Methods. International Research in Engineering Sciences, 156.

[5] Hossain, M. A., & otros. (2021). Machine Learning-Based Cooperative Spectrum Sensing in Dynamic Segmentation Enabled Cognitive Radio Vehicular Network. Energies, 14(4), 1169.

[7] Latifoğlu, F. (2020). A novel singular spectrum analysis-based multi-objective approach for optimal FIR filter design using artificial bee colony algorithm. Neural Computing and Applications, 32(17), 13323–13341.

[10] Martínez-González, A., Monzó-Cabrera, J., Martínez-Sáez, A. J., & Lozano-Guerrero, A. J. (2022). Minimization of measuring points for the electric field exposure map generation in indoor environments by means of Kriging interpolation and selective sampling. Environmental Research, 212, 113577.

[12] Poveda, H., Navarro, K., Merchan, F., Ramos, E., & González González, D. (2021). A Software Defined Radio-Based Prototype for Wireless Metrics Studies in IoT Applications. Wireless Personal Communications, 120(3), 2291-2306.

[14] Ren, S., & otros. (2021). An Adaptive Compressive Wideband Spectrum Sensing Algorithm Based on Least Squares Support Vector Machine. IEEE Access.

[15] Rugeles Uribe, J. de J., Guillen, E. P., & Cardoso, L. S. (2022). A technical review of wireless security for the internet of things: Software defined radio perspective. Journal of King Saud University - Computer and Information Sciences, 34(7), 4122-4134.

[18] Wang, J., & otros. (2021). Multiantenna-Assisted Wideband Spectrum Sensing Based on Sub-Nyquist Sampling. IEEE Wireless Communications Letters.

[19] Wright, D. P., & Ball, E. A. (2020). Highly Portable, Low-Cost SDR Instrument for RF Propagation Studies. IEEE Transactions on Instrumentation and Measurement, 69(8), 5446-5457.

[1] AbuAli, N., Khan, M. B., Ullah, F., Hayajneh, M., Ullah, H., & Mumtaz, S. (2024). Software defined radio frequency sensing framework for Internet of Medical Things. Information Fusion, 103, 102106.

[20] Ćarić, M.L., Draganić, A., Orović, I., & otros. (2023). Combining Gradient-Based and Thresholding Methods for Improved Signal Reconstruction Performance. J Sign Process Syst, 95, 643–656.

[21] Peñaloza, M. L. S., & Vesga, C. B. (2021). Hacia una gestión innovadora del espectro radioeléctrico en Colombia: acceso dinámico y mejores prácticas. Las TIC y las Sociedad Digital. Doce años después la Ley. Tomo I Modernización para el Sector TIC y sus recursos esenciales.

[22] Gummineni, M., & Polipalli, T. R. (2020). Implementation of reconfigurable transceiver using GNU Radio and HackRF One. Wireless Personal Communications, 112(2), 889-905.

[23] Alarcon, O. C., Suaña, J. A. R., Montoya, J. J. M., & Aguilar, M. D. G. (2021). Estudio de uso de Radio Definida por Software RTL-SDR y HackRF One para Recepción de FM. Revista Científica Investigación Andina, 20(2).

[24] Vazquez, J. A. E. (2023). Nvidia Jetson nano, un mini pc para desarrollo de robótica e inteligencia artificial. Inicio, 1(1), 1-4.

[25] Escobar Molina, M. C. (2023). Comparativa de plataformas Raspberry PI 4 y Jetson Nano para aplicaciones de agricultura de precisión (Bachelor's thesis).

[26] Del Barrio, A. A., Manzano, J. P., Maroto, V. M., Villarín, Á., Pagán, J., Zapater, M., ... & Hermida, R. (2023). HackRF+ GNU Radio: A software-defined radio to teach communication theory. The International Journal of Electrical Engineering & Education, 60(1), 23-40.

[27] He, M., Feng, L. & Zhao, D. A method to enhance SNR based on CEEMDAN and the interval thresholding in φ_OTDR systems. Appl. Phys. B 126, 97 (2020).

[28] Kansal, P., Gangadharappa, . & Kumar, A. An Efficient Composite Two-Tier Threshold Cooperative Spectrum Sensing Technique for 5G Systems. Arab J Sci Eng 47, 2865–2879 (2022).

[29] T. A. A. Santana, H. D. de Andrade, I. S. Queiroz Júnior, and I. B. Tavares da Silva, "Comparison of spatial interpolation methods to determine exposure ratio to electric fields in urban environments," Electron. Lett., vol. 53, no. 18, pp. 1250–1252, 2017.

[2] Astaiza, E., & otros. (2017). Efficient Wideband Spectrum Sensing Based on Compressive Sensing and Multiband Signal Covariance. IEEE Latin America Transactions, 15(3), 393-399.

[30] M. Röösli, P. Frei, E. Mohler, and K. Hug, "Systematic review on the health effects of exposure to radiofrequency electromagnetic fields from mobile phone base stations," Bull. World Health Organ., vol. 88, pp. 887–896, 2010.

[31] International Commission on Non-Ionizing Radiation Protection, "Guidelines for limiting exposure to electromagnetic fields (100 kHz to 300 GHz)," Health Phys., vol. 118, no. 5, pp. 483-524, May 2020.

[32] IEEE, "IEEE Standard for Safety Levels with Respect to Human Exposure to Electric, Magnetic, and Electromagnetic Fields, 0 Hz to 300 GHz - Redline," 2019.

[33] R. F. Cleveland and J. J. L. Ulcek, "Questions and answers about biological effects and potential hazards of Radiofrequency electromagnetic fields," Off. Eng. Technol. Fed. Commun. Comm, vol. 36, 1999.

[34] Directive 2013/35/EU of the European Parliament and of the Council of 26 June 2013 on the Minimum Health and Safety Requirements Regarding the Exposure of Workers to the Risks Arising from Physical Agents (Electromagnetic Fields).

[35] M. Pinheiro, T. Maranhão, M. Bernardo Filho, et al., "Assessment of non-ionizing radiation from radio frequency energy emitters in the urban area of Natal city, Brazil," Sci. Res. Essays, vol. 10, no. 2, pp. 79–85, 2015.

[36] J. Shan, W. Shao, H. Xue, Y. Xu, and D. Mao, "The method of electromagnetic environment map construction based on Kriging spatial interpolation," in Proceedings of the International Conference on Information Systems and Computer Aided Education (ICISCAE), IEEE, Changchun, China, pp. 212–217, 2018.

[37] J. Gonzalez-Rubio, A. Najera, E. Arribas, "Comprehensive personal RF-EMF exposure map and its potential use in epidemiological studies," Environ. Res., vol. 149, pp. 105–112, 2016.

[38] H. D. de Andrade, A. L. de Figueiredo, B. R. Fialho da S., J. L. Paiva de S., I. Queiroz Júnior, M. E. T. Sousa, "Analysis and development of an electromagnetic exposure map based in spatial interpolation," Electron. Lett., vol. 56, no. 8, pp. 373–375, 2020.

[39] Robert, H., Paul, B., Simona, M., & Annamaria, S. (2021, June). Real time broadband electromagnetic spectrum monitoring system based on software defined radio technology. In 2021 9th International Conference on Modern Power Systems (MPS) (pp. 1-6). IEEE.PMLR.

[40] H. Sallouha, A. Chiumento, and S. Pollin, "Aerial vehicles tracking using noncoherent crowdsourced wireless networks," IEEE Trans. Veh. Technol., vol. 70, no. 10, pp. 10780–10791, Oct. 2021.

[41] Y. Ben-Aboud, M. Ghogho, S. Pollin, and A. Kobbane, "Electrosmog monitoring using low-cost software-defined radio dongles," IEEE Access, vol. 9, pp. 107149–107158, 2021.

[42] B. Reynders, R. Iyare, S. Rajendran, V. Volskiy, G. A. Vandenbosch, and S. Pollin, "Using cheap RTL-SDRs for measuring electrosmog," in Proc. IEEE Symp. Commun. Veh. Technol., 2018, pp. 1–2.

[43] R. Getz, "ADALM PLUTO overview." Oct. 2021. [Online]. Available: https://wiki.analog.com/university/tools/pluto

[44] "USRP™ E312 battery operated." Data Sheet, Ettus Res., Austin, TX, USA, Jan. 2019.

[45] "RTL-SDR blog V3 datasheet." Feb. 2018. [Online]. Available: https://www.rtl-sdr.com

[46] M. B. Perotoni, L. Ferreira, and A. Maniçoba, "Low-cost measurement of electromagnetic Leakage in domestic appliances using software-defined radios," Revista Brasileira de Ensino de Física, vol. 44, Feb. 2022, Art. no. e20220009.

[47] H. Robert, B. Paul, M. Simona, and S. Annamaria, "Real time broadband electromagnetic spectrum monitoring system based on software defined radio technology," in Proc. 9th Int. Conf. Modern Power Syst. (MPS), 2021, pp. 1–6.

[48] C. Carciofi, A. Garzia, S. Valbonesi, A. Gandolfo, and R. Franchelli, "RF electromagnetic field levels extensive geographical monitoring in 5G scenarios: Dynamic and standard measurements comparison," in Proc. Int. Conf. Technol. Entrepreneurship (ICTE), 2020, pp. 1–6.

[49] S. Aerts et al., "In situ assessment of 5G NR massive MIMO base station exposure in a commercial network in Bern, Switzerland," Appl. Sci., vol. 11, no. 8, p. 3592, 2021.

[4] Golvaei, M., & Fakharzadeh, M. (2021). A Fast Soft Decision Algorithm for Cooperative Spectrum Sensing. IEEE Transactions on Circuits and Systems II: Express Briefs, 68(1), 241–245.

[50] R. Iyare, V. Volskiy, and G. A. E. Vandenbosch, "Study of the correlation between outdoor and indoor electromagnetic exposure near cellular base stations in Leuven, Belgium," Environ. Res., vol. 168, pp. 428–438, Jan. 2019.

[51] "Electrosense: A distributed sensor network for crowd-sourced spectrum monitoring." 2022. [Online]. Available: https://electrosense.org/

[52] G. Marconi, "Radio telegraphy," J. Amer. Inst. Elect. Eng., vol. 41, no. 8, pp. 561–570, 1922.

[53] R. A. Fessenden, "Wireless telephony," Proc. Amer. Inst. Elect. Eng., vol. 27, no. 7, pp. 1283–1358, 1908.

[54] J. Merritt, G. Wylde, and K. Bettinger, State of the Connected World 2020 Edition INSIGHT REPORT, World Econ. Forum, Cologny, Switzerland, Dec. 2020.

[55] C. L. Russell, "5 G wireless telecommunications expansion: Public health and environmental implications," Environ. Res., vol. 165, pp. 484–495, Aug. 2018.

[56] A. Balmori, "Electrosmog and species conservation," Sci. Total Environ., vol. 496, pp. 314–316, Oct. 2014.

[57] M. L. Pall, "Wi-Fi is an important threat to human health," Environ. Res., vol. 164, pp. 405–416, Jul. 2018.

[58] M. Salovarda and K. Malaric, "Measurements of electromagnetic smog," in Proc. IEEE Mediterr. Electrotechn. Conf. (MELECON), May 2006, pp. 470–473.

[59] W. H. Bailey, B. R. T. Cotts, and P. J. Dopart, "Wireless 5G Radiofrequency technology—An overview of small cell exposures, standards and science," IEEE Access, vol. 8, pp. 140792–140797, 2020.

[60] "ICNIRP Website." International Commission on Non-Ionising Radiation Protection. Jul. 2021. [Online]. Available: https://www.icnirp.org

[61] International Commission on Non-Ionizing Radiation Protection (ICNIRP), "Guidelines for limiting exposure to electromagnetic fields (100 kHz to 300 GHz)," Health Phys., vol. 118, no. 5, pp. 483–524, Mar. 2020, doi: 10.1097/HP.0000000000001210.

[62] T. G. Crainic, B. Di Chiara, M. Nonato, and L. Tarricone, "Tackling electrosmog in completely configured 3G networks by parallel cooperative meta-heuristics," IEEE Wireless Commun., vol. 13, no. 6, pp. 34–41, Dec. 2006.

[63] EMC Near-Field Probes for Oscilloscopes, Rohde Schwarz, Munich, Germany, 2022.

[64] M. Kanda and L. D. Driver, "An isotropic electric-field probe with tapered resistive dipoles for broad-band use, 100 kHz to 18 GHz," IEEE Trans. Microw. Theory Techn., vol. 35, no. 2, pp. 124–130, Feb. 1987.

[65] J. A. Shaw, "Radiometry and the Friis transmission equation," Amer. J. Phys., vol. 81, no. 1, pp. 33–37, 2013.

[66] J. Fayos-Fernandez, F. Victoria-Gonzalez, A. M. Martinez-Gonzalez, A. Morote-Marco, and D. Sanchez-Hernandez, "Effect of spectrum analyzer filtering on electromagnetic dosimetry assessment for UMTS base stations," IEEE Trans. Instrum. Meas., vol. 57, no. 6, pp. 1154–1165, Jun. 2008.

[67] D. Gabor, "Theory of communication. Part 1: The analysis of information," J. Inst. Elect. Eng. III, Radio Commun. Eng., vol. 93, no. 26, pp. 429–441, 1946.

[68] A. Pini, "The Fundamentals of Software-Defined Radio," DigiKey, 30-Jun-2020. [Online]. Available: https://www.digikey.com/en/articles/learn-the-fundamentals-of-software-defined-radio-and-how-to-use-it-with-a-low-cost-module. [Accessed: 29-Jul-2024].

[69] "Software Defined Radio Use Case for Spectrum Monitoring," Everything RF. [Online]. Available: https://www.everythingrf.com/articles/software-defined-radio-use-case-for-spectrum-monitoring. [Accessed: 29-Jul-2024].

[6] Kassri, N., Ennouaary, A., Bah, S., & Baghdadi, H. (2021). A Review on SDR, Spectrum Sensing, and CR-based IoT in Cognitive Radio Networks. International Journal of Advanced Computer Science and Applications, 12(6).

[70] "Advantages of SDR | Disadvantages of SDR," RF Wireless World. [Online]. Available: https://www.rfwireless-world.com/Terminology/Advantages-and-Disadvantages-of-SDR.html. [Accessed: 29-Jul-2024].

[71] X. Liu, C. Sun, M. Zhou, C. Wu, B. Peng and P. Li, "Reinforcement Learning-Based Multislot Double-Threshold Spectrum Sensing With Bayesian Fusion for Industrial Big Spectrum Data," in IEEE Transactions on Industrial Informatics, vol. 17, no. 5, pp. 3391-3400, May 2021, doi: 10.1109/TII.2020.2987421. keywords: {Sensors;Signal to noise ratio;Bayes methods;Informatics;Learning (artificial intelligence);Real-time systems;Cognitive industrial system (CIS);idle probability;industrial big spectrum data;reinforcement learning (RL);spectrum sensing},

[72] Salud y bienestar | Agenda 2030 en América Latina y el Caribe. (agenda2030lac.org).

[73] Programa De Las Naciones Unidas Para El Desarrollo. (www.undp.org).

[74] Objetivo 3 | Objetivos de Desarrollo Sostenible. (ods.cr).

[75] Sustainable Development Goal 3: Salud y bienestar | Naciones Unidas en Ecuador. (ecuador.un.org).

[8] Lipski, M. V., Kompella, S., & Narayanan, R. M. (2021). Practical Implementation of Adaptive Threshold Energy Detection using Software Defined Radio. IEEE Transactions on Aerospace and Electronic Systems, 57(2), 1227-1241.

[9] Liu, X., Yan, X., Zhang, S., & otros. (2021). The Effects of Electromagnetic Fields on Human Health: Recent Advances and Future. J Bionic Eng, 18, 210–237.

---

## ARCHIVOS ADJUNTOS

- ANEXO_1_PROPIEDAD_INTELECTUAL.docx
- ANEXO_2_AVAL_GRUPOS_DE_INVESTIGACION_UCALDAS.pdf
- ANEXO_2_AVAL_GRUPOS_DE_INVESTIGACION_UNAL.pdf
- ANEXO_3_DEFINICION_DE_ROLES.pdf
- ANEXO_4_Aval_horas_docente_Julio_Cesar_Garcia_Mz.FIAR.1.190-113-24.pdf
- ANEXO_5_PROFESORES_PARTICIPANTES.pdf
- ANEXO_7_PRESENTACION_PROPUESTA.pdf
- ANEXO_8_PRESENTACION_PROFESORES_GI_GCPDS.pdf
- ANEXO_8_PRESENTACION_PROFESORES_GI_IA.pdf
- ANEXO_9_COMPROMISO_ENTIDAD_EXTERNA_DUNDERLAB.pdf
- ANEXO_9_COMPROMISO_ENTIDAD_EXTERNA_INFERENCE.pdf
- ANEXO_9_COMPROMISO_ENTIDAD_EXTERNA_OPENBCO.pdf
- AVAL_CONSEJO_DE_FACULTAD_UCALDAS_2024-II-00007891.pdf
- ANEXO_6_DOCUMENTO_TECNICO.pdf
- ANEXO_10_TITULARIDAD_DE_BIENES.pdf
- ANEXO_1_62848_PROPIEDAD_INTELECTUAL_firm.pdf

---

## DECLARACIÓN DEL RESPONSABLE

Yo, JULIO CESAR GARCIA ALVAREZ investigador(a) principal del proyecto: Monitoreo SDR a exposición de IoT con alta densidad de dispositivos declaro:

- Conozco los términos de referencia de la convocatoria: CONVOCATORIA CONJUNTA UNIVERSIDAD DE CALDAS, UNIVERSIDAD NACIONAL DE COLOMBIA-SEDE MANIZALES, PARA PROYECTOS DE INVESTIGACIÓN 2024 .

- Que junto con todos los participantes de este proyecto aceptamos y cumplimos todos los requisitos estipulados en los términos de referencia y renunciamos a cualquier reclamación por ignorancia o errónea interpretación de estos documentos

**JULIO CESAR GARCIA ALVAREZ**
**RESPONSABLE DEL PROYECTO**
