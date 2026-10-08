# Del REM Nacional al Mapa Interior — Edición Banda Única ISM 2.4 GHz

**Documento de diseño conceptual | Arquitectura de Sistemas Inteligentes (variante mono-banda)**

**Premisa rectora reformulada:** restringir el análisis a la banda ISM 2.4 GHz (2400–2483.5 MHz) no es un simple cambio de filtro: **redefine la variable objetivo, elimina el confusor dominante del diseño multibanda y sustituye el contraste espectral inter-banda por un contraste intra-banda y temporal**. La cadena física se simplifica y se purifica:

> *Distribución de emisores locales (APs WiFi, BLE, Zigbee, hornos microondas) + geometría del recinto + actividad humana → canal 2.4 GHz (pérdida de trayectoria + multitrayecto + ocupación) → señal observada por el SDR*

Todo lo que antes llegaba "de afuera" por bandas celulares desaparece del problema. El sistema ya no estima *exposición electromagnética total*, sino **exposición generada por el ecosistema IoT local** — que es, exactamente, la pregunta declarada del Proyecto Hermes. Este es el primer acto metodológico: **declarar explícitamente el re-alcance de la variable objetivo** antes de construir nada.

---

## 0. Tabla Delta: qué cambia, qué sobrevive, qué se gana

| Dimensión | Diseño multibanda (análisis previo) | Diseño 2.4 GHz ISM | Veredicto |
|---|---|---|---|
| Variable objetivo | EMF total (suma cuadrática inter-banda, Ec. 1 del macro) | E_ISM (suma cuadrática intra-banda por subcanal) | **Re-alcance**, no pérdida |
| Brújula endógeno/exógeno | Ratio celular/ISM | **Perdida** → sustituida por ratios de subcanal (BLE/WiFi) + contraste temporal noche/día | Sustitución estructural |
| Conflación distancia/potencia | Alta (celdas de cientos de W conviven con mW) | **Comprimida**: la regulación homogeneiza el EIRP (clase ~100 mW en la banda) | Ganancia |
| Proxy de geometría | Fading + ratios inter-banda (conflados con absorción material dependiente de frecuencia) | Rizado espectral intra-banda **puro** (la absorción de materiales es ~constante en 83.5 MHz) | Ganancia metrológica |
| Proxy de densidad | Duty cycle multibanda | Duty cycle **desagregado por protocolo** (beacons/advertencias/datos/microondas) | Ganancia de resolución causal |
| Evaluación normativa | Niveles de referencia por frecuencia | Nivel único: ~61 V/m público / ~137 V/m ocupacional (ICNIRP 2020, 2–300 GHz) | Simplificación |
| Confusor exógeno | Downlink celular penetrando el recinto | Eliminado (residuo: WiFi de vecinos a través de muros) | **Ganancia central** |
| Nueva capacidad | — | Firmas de protocolo → separación de **tres factores latentes**: infraestructura, densidad IoT, actividad humana | Nueva |
| Reclamo científico perdido | — | Ya no puede afirmarse nada sobre *exposición total* del recinto | Limitación declarada |

---

## 1. Exploración Conceptual: Adaptación de Variables (Macro → Micro, Banda ISM)

### 1.1 Tabla de traducción de variables (edición 2.4 GHz)

| Variable macro | Proxy ISM 2.4 GHz | Observable SDR | Fundamento |
|---|---|---|---|
| **Distance** | PSD por subcanal + ratios entre subcanales | Energía integrada en WiFi ch. 1/6/11 (2412/2437/2462 MHz), canales de publicidad BLE (2402/2426/2480 MHz), canales Zigbee (11–26) | La señal *contiene* la distancia; el modelo la de-conflaciona |
| **BUILT-V/S/H** | Estadística de canal intra-banda | Rizado espectral sobre los 83.5 MHz, ancho de coherencia, factor K por subcanal, varianza temporal | La geometría queda codificada sin dispersión material espuria |
| **POP** | Duty cycle por protocolo | Cadencia de beacons (~100 ms), energía en canales BLE-adv, ráfagas de datos, firma de horno microondas (~2450–2460 MHz) | Cada protocolo es un "censo" de una clase de dispositivo |
| **SMOD** | Tipología del recinto por huella ISM | Clustering del vector (PSD + fading + duty) | Análogo categórico replicado en escala de sala |

### 1.2 PSD como sustituto de la "distancia" — versión purificada

En el diseño multibanda, la PSD conflaba distancia con potencia de transmisión en un rango de cientos de W (macroceldas) a mW (IoT). En 2.4 GHz ISM ocurre algo notable: **la regulación hace el trabajo de homogeneización**. Todos los emisores legales de la banda están en la clase de potencia ~100 mW (WiFi/Zigbee) o inferior (BLE, típicamente ~10 mW o menos). Esto comprime la varianza de potencia de fuente y convierte la PSD en un estimador de proximidad mucho más limpio.

La estructura que reemplaza a la "brújula celular/ISM" es una **micro-brújula intra-banda**, con lógica de decisión por subcanal:

- **PSD alta con cadencia regular de beacons (~100 ms)** → proximidad a AP WiFi (infraestructura).
- **Energía concentrada en los tres canales de publicidad BLE (2402/2426/2480 MHz), con ocupación FHSS esparcida** → densidad local de dispositivos IoT de baja potencia.
- **Energía con ráfagas erráticas y entropía temporal alta en canales WiFi de datos** → tráfico humano (streaming, transferencias).
- **Ruido de banda ancha impulsoso centrado en ~2450–2460 MHz** → horno microondas: interferente y, simultáneamente, **firma de actividad humana** (pico horario de almuerzo).

Y se añade el sustituto más elegante del contraste espectral perdido: el **contraste temporal como experimento natural**. En horas no ocupadas (noche/fin de semana), la banda ISM contiene el "piso" de infraestructura + IoT siempre activo (beacons, telemetría Zigbee). En horas ocupadas, se suma el tráfico humano. La diferencia día–noche **aísla la componente de actividad** — un instrumento causal que el diseño multibanda no tenía y que reemplaza parcialmente el ratio de frecuencias perdido.

**Inversión conceptual clave respecto al macro:** el estudio nacional necesitaba GIS para *calcular* la distancia a cada antena; en 2.4 GHz interior, la distancia está *dentro de la señal* (los beacons son balizas de localización gratuitas), pero conflacionada con la densidad de fuentes — y esa de-conflación es precisamente la tarea delegada al modelo.

**Veredicto: alta viabilidad, mejorada** respecto al diseño multibanda.

### 1.3 Varianza de fading como sustituto del "volumen/geometría" — versión purificada

Aquí la restricción de banda produce una **mejora metrológica sustancial**. En el diseño multibanda, comparar PSD entre 700 MHz y 3.5 GHz mezclaba geometría con absorción material dependiente de frecuencia. En 83.5 MHz alrededor de 2.45 GHz, la absorción de los materiales de construcción es aproximadamente constante: **el rizado espectral intra-banda queda dominado por la estructura de multitrayecto del canal, no por la dispersión del material**. La geometría del recinto se observa en estado casi puro.

El argumento cuantitativo cierra bien a esta frecuencia:

- λ ≈ 12.5 cm, comparable a las escalas de mobiliario y particiones → el canal es **hipersensible a la geometría** del recinto.
- Dispersión temporal típica en interiores: decenas de ns → ancho de coherencia del orden de unidades a decenas de MHz → dentro de los 83.5 MHz caben **varias celdas de coherencia**: el rizado a lo ancho de la banda es directamente legible como huella del delay spread, y este crece con las dimensiones y reflectividad de la sala. La coherencia espectral funciona como **"metro de RF" del recinto**, ahora sin contaminación de dispersión material.
- El factor K por subcanal separa LOS dominante (pasillo) de dispersión densa (sala compartimentada).

**Confounder específico de 2.4 GHz que debe gestionarse:** el cuerpo humano (≈ bolsa de agua) absorbe fuertemente a esta frecuencia — la sombra corporal genera fading temporal profundo. Esto amenaza la separación geometría/actividad, pero la mitigación es de diseño experimental, no de algoritmo: **campañas en régimen desocupado** (geometría pura) vs. **ocupado** (geometría + actividad), convirtiendo el confusor en la tercera variable latente del sistema (Sección 1.4).

**Veredicto: alta viabilidad, con la purificación intra-banda como ventaja sobre el diseño multibanda.**

### 1.4 Duty cycle como sustituto de la "densidad poblacional/dispositivos" — versión desagregada por protocolo

El duty cycle multibanda era un agregado. En 2.4 GHz ISM es **descomponible por firma de protocolo**, lo que convierte un proxy único en tres:

1. **Piso de infraestructura:** beacons WiFi de cadencia regular — densidad de APs, no de usuarios.
2. **Densidad IoT:** energía en canales de publicidad BLE + ocupación FHSS esparcida + cadencia periódica de telemetría (Zigbee) — proporcional al inventario de dispositivos activos.
3. **Actividad humana:** ráfagas de datos de alta entropía + contraste día/noche + firma de microondas.

Estadísticos por familia: duty por subcanal, tasa de eventos, regularidad temporal (autocorrelación y periodicidad — la telemetría IoT es periódica; el tráfico humano no), entropía de ocupación, contraste entre regímenes horarios. La no-estacionariedad horaria, antes vista como limitación, es ahora **el eje experimental que separa los tres factores latentes**.

**Veredicto: alta viabilidad, con resolución causal superior al diseño multibanda.**

### 1.5 Riesgos específicos de la banda única

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Horno microondas (ruido impulsivo ~2450 MHz) | Contaminación de PSD y duty | Detección por firma espectral-temporal y enmascaramiento; registro como feature de actividad |
| Saturación/congestión ISM en entornos densos | Elevación del piso de ruido | Convertir el fenómeno en señal: el piso de ruido elevado es en sí un indicador de densidad |
| Pérdida del reclamo de exposición total | Alcance científico reducido | Declaración explícita de alcance: "exposición atribuible al ecosistema IoT/ISM" |
| Fading de pequeña escala (λ = 12.5 cm) | Variabilidad no reproducible punto a punto | Promediado espacial en micro-retícula por punto (ver Fase 1) |
| Ancho de banda instantánea del SDR (~56 MHz) < banda ISM (83.5 MHz) | Cobertura incompleta por captura única | Barrido segmentado en 2–3 sub-capturas, o priorización de subcanales informativos |
| WiFi exógeno de recintos vecinos | Contaminación en salas limítrofes | Campañas con control de regímenes; feature de "leakage" por muros compartidos |
| Ausencia de 5/6 GHz WiFi | Subestimación del ecosistema inalámbrico moderno | Documentar escalabilidad del marco (es banda-paramétrico) con re-caracterización física por banda |

---

## 2. Traducción Metodológica y Tecnológica (Banda ISM)

### 2.1 Líneas base: los ensambles ligeros — argumentos que sobreviven y se refuerzan

Los tres argumentos del análisis multibanda (evidencia empírica del macro para datos tabulares, economía energética en Jetson Nano, compatibilidad TreeSHAP exacta) **sobreviven intactos y se refuerzan**: al restringir a 2.4 GHz, el conjunto de características se vuelve aún más tabular y engineered (subcanales, protocolos, estadísticos de canal), que es el terreno donde RF/XGBoost dominaron el estudio nacional.

Se añaden dos baselines adicionales que el diseño mono-banda habilita:

- **Baseline físico-clásico:** modelo de pérdida de trayectoria log-distancia con atenuación por muros, alimentado con las distancias estimadas por RSSI de beacons. Es el análogo del "modelo tradicional de señal" que el artículo base afirmaba superar — y el umbral que cualquier modelo de ML debe superar para justificarse.
- **Baseline lineal regularizado en dominio dB:** con la homogeneidad de EIRP de la banda y la compresión de la conflación potencia-distancia, las relaciones log-espaciales son más linealizables; si un modelo lineal en features dB aproxima al ensamble, la navaja de Occam vuelve a actuar.

**La pregunta científica del benchmark se mantiene:** *¿la estructura cruda tiempo-frecuencia contiene información que las features ingenierizadas pierden?* — con la ventaja añadida de que en 2.4 GHz las features de protocolo son tan informativas que la barra para el Deep Learning sube. Arquitectura de producción recomendada: la cascada de tres niveles del análisis previo (ensamble en línea continua → modelo profundo por evento → explicación bajo demanda), ahora operando en una sola banda.

### 2.2 XAI: SHAP frente a la normativa — la atribución tri-factorial

**Redefinición del expediente regulatorio.** Con banda única, ITU-T K.52 e ICNIRP 2020 colapsan a un nivel de referencia único (del orden de 61 V/m para público general y 137 V/m ocupacional en 2–300 GHz; coherente con los niveles de acción de la Directiva 2013/35/EU citada por Hermes). La descomposición normativa se simplifica — pero surge una obligación de honestidad dosimétrica:

> **Un transmisor de clase 100 mW EIRP produce campos del orden de 1–2 V/m a un metro.** La exposición ISM interior realista típica se sitúa órdenes de magnitud por debajo del nivel de referencia. El sistema, correctamente diseñado, no es un detector de excedencias: es un **cartógrafo de exposición relativa y un atribuidor de causas**.

Esto no debilita el proyecto — lo reposiciona con precisión científica: el valor regulatorio y epidemiológico está en (a) el **cociente de exposición** E_ISM/nivel de referencia como métrica continua, (b) la identificación y atribución de hotspots, y (c) el **monitoreo de tendencias como indicador temprano** ante el crecimiento de densidad IoT — exactamente la motivación de exposición crónica de baja intensidad que el propio Hermes declara (alteraciones del sueño, efectos neurológicos en su literatura de soporte).

**La pregunta central adquiere ahora estructura tri-factorial**, con lógica de decisión SHAP local:

| Peso dominante en atribución SHAP | Factor causal | Mitigación accionable |
|---|---|---|
| Energía en canales BLE-adv, ocupación FHSS, cadencia periódica | **Densidad de dispositivos IoT** | Segmentación de clústeres, programación de telemetría |
| RSSI de beacons elevado, energía de canal con regularidad | **Infraestructura (APs)** | Reubicación/potencia de AP, planificación de canales |
| Entropía de ráfagas, contraste día/noche, firma de microondas | **Actividad humana** | Políticas de uso, distribución de carga temporal |
| Fading profundo, K bajo, rizado espectral rico, con ocupación baja | **Geometría del recinto** | Materiales absorbentes, redistribución de mobiliario |

Note la ganancia respecto al análisis multibanda: la pregunta era binaria (dispositivos vs. geometría); la banda ISM con desagregación por protocolo la convierte en **cuaternaria** (dispositivos, infraestructura, actividad, geometría) — porque la banda contiene las firmas de protocolo que las bandas celulares anonimizaban.

**Rigor indispensable (sin cambios):** SHAP atribuye al modelo, no a la física. El cierre de bucle intervenir → re-medir → verificar es lo que convierte la atribución en evidencia defendible. Los contrfactuals cuantificados cambian de vocabulario: *"si la energía del canal BLE-adv se reduce a la mitad, el cociente de exposición del hotspot cae X%"* — guía de mitigación medible.

**Estrategia en el borde (sin cambios, reforzada):** explicación dirigida por eventos (calcular SHAP solo cuando el cociente de exposición supera una fracción de umbral de vigilancia, p. ej. 5–10% del nivel de referencia — no 50%, coherente con el realismo dosimétrico), con reportes globales por lotes.

### 2.3 Interpolación espacial: kriging con pre-procesamiento obligatorio

El marco conceptual del análisis multibanda sobrevive (variogramas por zona, kriging universal, híbrido regression-kriging, mapa de incertidumbre que dirige el muestreo selectivo), pero la banda única impone **tres adaptaciones específicas**:

1. **Separación obligatoria de escalas espaciales.** A λ = 12.5 cm, el campo instantáneo fluctúa de forma no reproducible entre puntos separados centímetros (fading de pequeña escala). Kriging es válido sobre el **campo de media local (shadowing)**, cuya distancia de descorrelación interior es del orden de metros. Protocolo: cada "punto" de medición = micro-retícula promediada (decenas de muestras espaciales en un volumen del orden del cuerpo humano, práctica estándar de evaluación de exposición), dejando el campo de gran escala limpio para la interpolación.

2. **Drift dominado por la infraestructura.** El campo ISM es una superposición de gradientes locales alrededor de APs y clústeres de dispositivos. En el híbrido regression-kriging, el componente determinista (drift) puede alimentarse con el **mapa de RSSI de beacons** — la infraestructura misma provee la covariable externa del kriging. El residuo interpolado captura la estructura local que el modelo no explica.

3. **Cartografía condicionada por régimen temporal.** El campo es función del estado de ocupación. Producto cartográfico dual: **mapa de régimen desocupado** (piso: infraestructura + IoT siempre activo + geometría) y **mapa de régimen ocupado** (suma con actividad). La **diferencia entre ambos** es un mapa de exposición atribuible a actividad humana — un producto cartográfico nuevo, imposible en el diseño multibanda estático del macro, y directamente relevante para la evaluación de exposición laboral.

Anisotropía por pasillos y no-estacionaridad entre salas se gestionan como en el análisis previo (estratificación por zona, variogramas direccionales).

---

## 3. Plan de Implementación Estratégica (Edición Banda ISM 2.4 GHz)

Mantiene la lógica cíclica del diseño original; las fases se re-especifican.

### Fase 1: Estrategia de Adquisición de Datos y Prototipado RF (≈ meses 1–7)

| Componente | Diseño conceptual (2.4 GHz) |
|---|---|
| **Recinto piloto** | Oficina/laboratorio con alta densidad IoT; inventario documentado solo como metadato de validación de proxies |
| **Cadena instrumental** | USRP B200 Mini + antena + Jetson Nano. **Ventaja mono-banda:** un único factor de antena por calibrar y verificación de linealidad en un rango espectral reducido — la calibración se simplifica y se hace más trazable. Verificación cruzada contra sonda isotrópica de referencia en puntos testigo |
| **Cobertura espectral** | Barrido segmentado de los 83.5 MHz (el ancho instantáneo del SDR es insuficiente para captura única): segmentos alineados con WiFi 1/6/11 + canales BLE-adv como sub-bandas prioritarias; resolución suficiente para resolver el rizado intra-banda (varias celdas de coherencia dentro de la banda) |
| **Protocolo de punto** | Malla 0.5–1 m (resuelve el shadowing, cuya descorrelación es de metros); 3 alturas (0.5/1.1/1.7 m); **micro-retícula de promediado espacial por punto** para eliminar fading de pequeña escala; ventana temporal por punto de minutos (capturar cadencia de beacons y ráfagas), promediado conservador al estilo CEPT/ECC |
| **Diseño de regímenes** | Bloques ocupado/desocupado, día/noche, días hábiles/fin de semana — **el eje experimental que separa los tres factores latentes**. Registro de eventos de microondas |
| **Ground truth** | Subconjunto con instrumento de referencia; resto por estimación SDR calibrada |
| **Esquema de datos** | Tabla "punto × ventana temporal × sub-banda" con coordenadas, estadísticos crudos y régimen como metadato |

**Criterio de éxito:** incertidumbre de calibración acotada en banda única; dataset v1 con cobertura completa de regímenes temporales y segmentos espectrales.

### Fase 2: Ingeniería de Características (≈ meses 4–10, solapada)

Cinco familias (la cuarta es nueva respecto al diseño multibanda):

1. **Familia PSD por subcanal:** energía integrada por canal WiFi, por canal BLE-adv, por canal Zigbee; picos; **pendiente del rizado intra-banda**; ratios entre clases de subcanal (BLE/WiFi como micro-brújula de densidad local vs. infraestructura).
2. **Familia fading:** varianza temporal por subcanal, factor K por subcanal, **ancho de coherencia estimado desde la correlación espectral intra-banda**, profundidad del rizado.
3. **Familia ocupación por protocolo:** duty por subcanal, tasa de eventos, periodicidad/autocorrelación (separa telemetría periódica de tráfico errático), entropía de ocupación, **contraste entre regímenes temporales** (el feature estrella del diseño), firma de microondas como covariable binaria.
4. **Familia exposición:** agregados cuadráticos intra-banda por subcanal — espejo de la Ec. 1 del macro, con granularidad sub-banda.
5. **Reglas transversales:** dominio dB para features de potencia; z-score por campaña; protocolo de atípicos (eventos de microondas como clase etiquetada, no como ruido descartado); preservación de la identificabilidad por subcanal para la descomposición normativa.

**Bucle de validación conceptual:** correlacionar fading intra-banda contra geometría documentada; energía BLE-adv contra inventario de dispositivos; contraste día/noche contra registros de ocupación.

### Fase 3: Entrenamiento, Selección de Modelos y Explicabilidad (≈ meses 8–15)

- **Validación:** splits temporales bloqueados (campañas tempranas → selección; tardías → evaluación independiente); CV de 5 pliegues × 10 repeticiones (50 pares, como el macro); **leave-one-room-out** para generalización espacial; y un split adicional por régimen temporal (entrenar en desocupado, evaluar en ocupado y viceversa) para probar la robustez de los factores latentes.
- **Suite comparativa:** modelo físico-clásico log-distancia (baseline nulo), lineal regularizado en dB, kNN, DT, RF, XGBoost, LightGBM, red pequeña, y el modelo profundo de Hermes sobre estructura cruda tiempo-frecuencia. Métricas: RMSE/MSE + MAE + R², más métricas de detección de hotspots (definidos como fracción del nivel de referencia, dada la honestidad dosimétrica de la Sección 2.2), con manejo explícito del desbalance.
- **Benchmarking en el borde:** latencia/memoria/energía por inferencia en Jetson Nano; el argumento energético pesa más al ser monitoreo continuo mono-banda.
- **SHAP:** TreeSHAP global para el contraste científico refinado — ¿ocupa la energía BLE-adv el lugar de la población? ¿el rizado intra-banda el del volumen? ¿el RSSI de beacons el de la distancia? — y SHAP local dirigido por eventos con bitácora persistida, estructurada para la **matriz tri-factorial + geometría** de la Sección 2.2.

### Fase 4: Mapeo Espacial y Evaluación Normativa (≈ meses 13–18)

**Flujo cartográfico:**

> Pre-procesamiento de media espacial → variografía por zona y por régimen → kriging híbrido con drift de RSSI de beacons → mapa de predicción + incertidumbre → muestreo selectivo iterativo → **cartografía dual** (régimen desocupado / ocupado) + **mapa de diferencia** (exposición por actividad)

**Cruce normativo — reposicionado con honestidad dosimétrica:**
- Cociente de exposición continuo E_ISM / nivel de referencia (ICNIRP 2020, ITU-T K.52; niveles de acción de la Directiva 2013/35/EU para el contexto laboral), con promediado temporal y espacial según práctica de evaluación.
- Clasificación de zonas no como *conforme/excedencia* sino como **gradiente de exposición relativa + hotspot ranking**.
- **Informe de atribución por hotspot** (matriz tri-factorial + geometría vía SHAP) con contrfactual cuantificado y verificación por re-medición.
- **Monitoreo de tendencias** como indicador temprano ante crecimiento de densidad IoT — el entregable regulatorio con mayor valor prospectivo, alineado con la motivación de exposición crónica de Hermes.

### Riesgos transversales actualizados

| Riesgo | Severidad | Estrategia |
|---|---|---|
| Microondas como interferente | Media | Firma espectral-temporal; feature explícita |
| Congestión ISM elevando piso de ruido | Media | Convertir en indicador de densidad; ventanas largas |
| Reclamo de exposición total insostenible | Alta (científica) | Alcance declarado: exposición atribuible a ecosistema ISM |
| Fading de pequeña escala no promediado | Alta | Micro-retícula espacial obligatoria por punto |
| Sobreajuste por correlación espacial/temporal | Alta | Splits bloqueados + leave-one-room-out + split por régimen |
| Deriva de calibración | Media | Puntos testigo permanentes en banda única |

---

## Síntesis de cierre

Restringir Hermes a la banda ISM 2.4 GHz **sacrifica amplitud a cambio de nitidez causal**. Se pierde el reclamo de exposición total y la brújula espectral celular/ISM, pero se gana: (1) la **eliminación del confusor exógeno dominante**, dejando la pregunta central de Hermes (¿dispositivos o geometría?) en condiciones de identificabilidad casi de laboratorio; (2) un proxy de geometría **purificado** — el rizado intra-banda codifica multitrayecto sin dispersión material espuria, y a λ = 12.5 cm el canal es hipersensible a la morfología del recinto; (3) un proxy de densidad **desagregado por protocolo** que eleva la pregunta de atribución de binaria a cuaternaria (dispositivos, infraestructura, actividad, geometría); y (4) un instrumento causal nuevo — el **contraste temporal entre regímenes de ocupación** — que sustituye experimentalmente el contraste de frecuencias perdido.

El realismo dosimétrico obliga, además, a un acto de honestidad que fortalece el proyecto: los niveles ISM interiores estarán órdenes de magnitud por debajo de los límites de referencia, y por tanto el producto científico correcto no es el detector de excedencias, sino el **sistema de exposición relativa, atribución causal y vigilancia de tendencias** — que es precisamente donde el trío SDR + ensambles ligeros + SHAP rinde al máximo, y donde el Proyecto Hermes tiene su contribución original frente al mapeo REM nacional que lo inspiró.