# [PROYECTO: _nombre_proyecto_]

## Especificación de Requisitos del Sistema (SRS)

> **Plantilla basada en:** IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering*, adaptada con elementos de ETSI EN 303 645 (Cyber Security for IoT) y estructura determinista para validación automatizada por IA.
>
> **Versión plantilla:** 1.0.0  
> **Fecha creación:** _YYYY-MM-DD_  
> **Última modificación:** _YYYY-MM-DD_  
> **Estado documento:** `BORRADOR` | `EN_REVISIÓN` | `APROBADO` | `OBSOLETO`

---

## Metadatos del Documento

| Campo                  | Valor                                    |
|------------------------|------------------------------------------|
| **ID Documento**       | `SRS-_SIGLAS_-_NNN_`                     |
| **Proyecto**           | _nombre completo del proyecto_           |
| **Organización**       | _entidad propietaria_                    |
| **Versión**            | _X.Y.Z_ (SemVer)                        |
| **Clasificación**      | `PÚBLICO` \| `INTERNO` \| `CONFIDENCIAL` |
| **Autor(es)**          | _nombre (rol)_                           |
| **Revisor(es)**        | _nombre (rol)_                           |
| **Aprobador(es)**      | _nombre (rol)_                           |

### Control de Cambios

| Versión | Fecha      | Autor        | Descripción del Cambio          |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | YYYY-MM-DD | _nombre_     | Creación inicial                 |

---

## 1. Introducción

### 1.1 Propósito

_Descripción del propósito del documento y del sistema. Indicar la audiencia objetivo._

### 1.2 Alcance del Sistema

_Nombre del sistema, qué hace y qué NO hace. Beneficios, objetivos y metas._

### 1.3 Definiciones, Acrónimos y Abreviaciones

| Término    | Definición                                              |
|------------|---------------------------------------------------------|
| _TÉRMINO_  | _Definición precisa_                                    |

### 1.4 Referencias

| ID Ref     | Documento                                               | Versión / Fecha |
|------------|---------------------------------------------------------|-----------------|
| `REF-001`  | _Título del documento referenciado_                     | _vX.Y / fecha_  |

### 1.5 Visión General del Documento

_Descripción de la estructura de las secciones siguientes._

---

## 2. Descripción General del Sistema

### 2.1 Perspectiva del Producto

_Contexto del sistema: si es nuevo, reemplazo, extensión. Relación con otros sistemas._

#### 2.1.1 Diagrama de Contexto

_Referencia a diagrama o descripción textual de las interfaces externas._

### 2.2 Funciones del Producto

_Resumen de alto nivel de las funciones principales (sin detalle de requisito)._

### 2.3 Características de los Usuarios

| Tipo de Usuario | Descripción                        | Nivel Técnico      |
|-----------------|------------------------------------|---------------------|
| _rol_           | _qué hace con el sistema_          | `BÁSICO` \| `TÉCNICO` \| `EXPERTO` |

### 2.4 Restricciones

_Restricciones regulatorias, de hardware, de interfaz, de seguridad, etc._

### 2.5 Supuestos y Dependencias

_Condiciones asumidas como verdaderas para que los requisitos sean válidos._

---

## 3. Requisitos Específicos

> **Convención de IDs:**  
> Cada requisito usa el formato `[CAT]-[SUB]-[NNN]` donde:
> - `CAT` = Categoría (3-5 letras mayúsculas). Ej: `ARQ`, `ANAL`, `CONN`, `SEG`
> - `SUB` = Subcategoría (2-4 letras). Ej: `PAR`, `MED`, `VIS`
> - `NNN` = Número secuencial de 3 dígitos, iniciando en 001
>
> **Campos obligatorios por requisito** (marcados con `*`):
>
> | Campo              | Tipo                  | Descripción                                                   |
> |--------------------|-----------------------|---------------------------------------------------------------|
> | `id`*              | string                | Identificador único. Formato: `[CAT]-[SUB]-[NNN]`            |
> | `título`*          | string (≤120 chars)   | Nombre descriptivo del requisito                               |
> | `descripción`*     | string                | Enunciado completo usando "El sistema DEBE…" / "El sistema DEBERÍA…" |
> | `tipo`*            | enum                  | `FUNCIONAL` \| `NO_FUNCIONAL` \| `INTERFAZ` \| `RESTRICCIÓN`  |
> | `prioridad`*       | enum                  | `MUST` \| `SHOULD` \| `COULD` \| `WONT` (MoSCoW)             |
> | `categoría`*       | string                | Categoría funcional del sistema                                |
> | `subcategoría`     | string                | Agrupación dentro de la categoría                              |
> | `criterio_aceptación`* | string[]          | Lista de condiciones verificables (mínimo 1)                   |
> | `verificación`*    | enum                  | `INSPECCIÓN` \| `DEMOSTRACIÓN` \| `PRUEBA` \| `ANÁLISIS`      |
> | `dependencias`     | string[]              | IDs de requisitos de los que depende                           |
> | `estándar_ref`     | string[]              | Referencias normativas aplicables                              |
> | `hardware_nuevo`   | boolean               | `true` si requiere hardware adicional                          |
> | `notas`            | string                | Observaciones internas o técnicas                              |
> | `estado`*          | enum                  | `PROPUESTO` \| `APROBADO` \| `IMPLEMENTADO` \| `VERIFICADO` \| `RECHAZADO` |
> | `fase`             | string                | Fase de implementación. Ej: `2025`, `2026`, `FASE_2`          |

---

### 3.1 [_CATEGORÍA 1: Nombre_]

#### 3.1.1 [_Subcategoría 1.1_]

---

**`[CAT]-[SUB]-[NNN]` — _Título del requisito_**

| Campo                  | Valor                                                     |
|------------------------|-----------------------------------------------------------|
| **Tipo**               | `FUNCIONAL` \| `NO_FUNCIONAL` \| `INTERFAZ` \| `RESTRICCIÓN` |
| **Prioridad**          | `MUST` \| `SHOULD` \| `COULD`                             |
| **Estado**             | `APROBADO`                                                |
| **Verificación**       | `INSPECCIÓN` \| `DEMOSTRACIÓN` \| `PRUEBA` \| `ANÁLISIS`  |
| **Hardware nuevo**     | `Sí` / `No`                                               |
| **Estándar(es)**       | _Referencias normativas_                                   |
| **Dependencias**       | _IDs de requisitos previos_                                |
| **Fase**               | _Fase de implementación_                                   |

**Descripción:**  
El sistema DEBE _[acción verificable con parámetros cuantitativos cuando aplique]_.

**Criterios de Aceptación:**

1. [ ] _Condición verificable 1_
2. [ ] _Condición verificable 2_

**Notas:**  
_Observaciones técnicas o de implementación._

---

_[Repetir bloque para cada requisito]_

---

## 4. Requisitos de Interfaces Externas

### 4.1 Interfaces de Usuario
### 4.2 Interfaces de Hardware
### 4.3 Interfaces de Software
### 4.4 Interfaces de Comunicación

---

## 5. Requisitos No Funcionales

### 5.1 Rendimiento
### 5.2 Seguridad
### 5.3 Fiabilidad / Disponibilidad
### 5.4 Mantenibilidad
### 5.5 Portabilidad

---

## 6. Trazabilidad

_Matriz de trazabilidad de requisitos contra objetivos de negocio, casos de prueba o componentes del sistema._

| ID Requisito  | Objetivo de Negocio | Caso de Prueba | Componente    |
|---------------|---------------------|----------------|---------------|
| `[CAT]-[SUB]-[NNN]` | _OBJ-NNN_     | _TC-NNN_       | _componente_  |

---

## 7. Validación Estructural (para IA)

> Esta sección define las reglas que un validador automatizado DEBE verificar contra este documento.

### 7.1 Reglas de Formato

| Regla ID | Regla                                                                 | Severidad |
|----------|-----------------------------------------------------------------------|-----------|
| `V-001`  | Cada requisito DEBE tener un `id` único con formato `[A-Z]{3,5}-[A-Z]{2,4}-\d{3}` | `ERROR`   |
| `V-002`  | Cada requisito DEBE tener todos los campos marcados con `*`           | `ERROR`   |
| `V-003`  | El campo `descripción` DEBE iniciar con "El sistema DEBE" o "El sistema DEBERÍA" | `WARNING` |
| `V-004`  | El campo `criterio_aceptación` DEBE tener al menos 1 elemento         | `ERROR`   |
| `V-005`  | Los valores de `tipo` DEBEN ser uno de: `FUNCIONAL`, `NO_FUNCIONAL`, `INTERFAZ`, `RESTRICCIÓN` | `ERROR`   |
| `V-006`  | Los valores de `prioridad` DEBEN seguir MoSCoW: `MUST`, `SHOULD`, `COULD`, `WONT` | `ERROR`   |
| `V-007`  | Los valores de `verificación` DEBEN ser: `INSPECCIÓN`, `DEMOSTRACIÓN`, `PRUEBA`, `ANÁLISIS` | `ERROR`   |
| `V-008`  | Los valores de `estado` DEBEN ser: `PROPUESTO`, `APROBADO`, `IMPLEMENTADO`, `VERIFICADO`, `RECHAZADO` | `ERROR`   |
| `V-009`  | Las `dependencias` referenciadas DEBEN existir como IDs en el documento | `ERROR`   |
| `V-010`  | El `título` no DEBE exceder 120 caracteres                            | `WARNING` |
| `V-011`  | No DEBEN existir IDs duplicados en todo el documento                   | `ERROR`   |
| `V-012`  | Cada sección 3.x DEBE contener al menos un requisito                   | `WARNING` |

### 7.2 Reglas Semánticas

| Regla ID | Regla                                                                 | Severidad |
|----------|-----------------------------------------------------------------------|-----------|
| `S-001`  | Requisitos con `prioridad: MUST` DEBEN tener `criterio_aceptación` con valores cuantitativos | `WARNING` |
| `S-002`  | Requisitos con `hardware_nuevo: true` DEBEN especificar el componente en notas | `WARNING` |
| `S-003`  | Requisitos con `estándar_ref` no vacío DEBEN citar documentos listados en §1.4 | `WARNING` |
| `S-004`  | No DEBE haber dependencias circulares entre requisitos                 | `ERROR`   |

---

## Anexo A — Estándares de Referencia

_Lista consolidada de estándares normativos citados en los requisitos._

## Anexo B — Glosario Extendido

_Términos técnicos específicos del dominio._

---

> **Nota de uso:** Esta plantilla está diseñada para ser procesada por herramientas de validación automatizada (IA o scripts). Los bloques de requisitos siguen un formato tabular fijo que permite parsing determinista. Los enums restringen valores válidos. Las reglas de §7 definen el contrato de validación.
