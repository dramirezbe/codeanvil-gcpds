"""Build six editable Spanish slides introducing V-SIL v4; no empirical claims.

Rebuild from the repo root:
  uv run --isolated --no-project --with python-pptx==1.0.2 python methodology/slides/V-SIL_v4_presentacion.py
  libreoffice -env:UserInstallation=file:///tmp/vsil-slides-lo --headless --convert-to pdf --outdir methodology/slides methodology/slides/V-SIL_v4_presentacion.pptx

The final slide deliberately reserves blank space for future results. Speaker notes carry
scope nuances without bibliographic references. All visible text and shapes remain editable.
Rollback: remove this generator and its two generated presentation files independently.
Validation: six PDF pages, render review and blank results area; this deck is not run evidence.
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'V-SIL_v4_presentacion.pptx'
W, H = 13.333, 7.5
INK, TEAL, BLUE = '122B40', '087F78', '3B5B9A'
MUTED, LINE, WHITE, BACKGROUND = '52697C', 'DAE5ED', 'FFFFFF', 'FAFCFE'
SOFT_TEAL, SOFT_BLUE, AMBER = 'E7F5F2', 'EDF2FB', 'B77521'
FONT = 'DejaVu Sans'


def rgb(value):
    return RGBColor.from_string(value)


def no_shadow(shape):
    style = shape._element.find(qn('p:style'))
    effect = style.find(qn('a:effectRef')) if style is not None else None
    if effect is not None:
        effect.set('idx', '0')


def box(slide, x, y, w, h, fill=WHITE, stroke=LINE, rounded=False):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.line.color.rgb = rgb(stroke)
    shape.line.width = Pt(0.8)
    shape._element.spPr.append(OxmlElement('a:effectLst'))  # suppress theme drop shadow
    no_shadow(shape)
    if rounded:
        shape.adjustments[0] = 0.08
    return shape


def text(slide, x, y, w, h, value, size=20, color=INK, bold=False, align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.vertical_anchor = MSO_ANCHOR.TOP
    frame.margin_left = frame.margin_right = Inches(0.015)
    frame.margin_top = frame.margin_bottom = 0
    for index, line in enumerate(value.split('\n')):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = line
        p.alignment = align
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = rgb(color)
        p.space_after = Pt(4)
        p.line_spacing = 1.12
    return shape


def rule(slide, x, y, w, color=LINE):
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x+w), Inches(y),
    )
    line.line.color.rgb = rgb(color)
    line.line.width = Pt(1)
    no_shadow(line)


def arrow(slide, x, y, w=0.28):
    shape = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(y), Inches(w), Inches(0.26))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(TEAL)
    shape.line.fill.background()
    no_shadow(shape)


def base(deck, index, kicker, title, notes):
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(BACKGROUND)
    box(slide, 0.65, 0.39, 0.42, 0.055, TEAL, TEAL)
    text(slide, 1.19, 0.30, 9.7, 0.34, f'V-SIL v4  /  {kicker.upper()}', 11, TEAL, True)
    text(slide, 0.65, 0.92, 12.0, 1.12, title, 32, INK, True)
    rule(slide, 0.65, 7.0, 12.0)
    text(slide, 0.65, 7.13, 8.6, 0.22, 'GCPDS · Universidad Nacional de Colombia', 8.5, MUTED)
    text(slide, 11.95, 7.10, 0.7, 0.28, f'{index} / 6', 10, TEAL, True, PP_ALIGN.RIGHT)
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def main():
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(W), Inches(H)
    deck.core_properties.title = 'V-SIL v4 — Desarrollo SDR COTS con evidencia'
    deck.core_properties.subject = 'Problema, filosofía, aportes y evidencia; resultados pendientes'
    deck.core_properties.author = 'David Ramírez-Betancourt · GCPDS · Universidad Nacional de Colombia'
    deck.core_properties.keywords = 'V-SIL v4, SDR, COTS, Agile-V, verificación, evidencia'

    slide = base(deck, 1, 'Problema y contexto', 'SDR COTS exige evidencia\nmás allá de una demo',
        'V-SIL es una metodología general para software limitado por COTS; esta presentación usa SDR como contexto. '
        'El hardware comercial fija restricciones de tasa, recursos y entorno. La señal RF, el host y los enlaces '
        'afectan las observaciones. Una demo o un módulo aislado no prueban los requisitos de extremo a extremo. '
        'La asistencia por IA aumenta la necesidad de contratos y evidencia; no se afirma aquí una mejora medida. '
        'COTS: componentes comerciales disponibles.')
    text(slide, 0.65, 2.28, 12.0, 0.7,
         'El reto: demostrar requisitos de extremo a extremo\nen una plataforma y un entorno declarados.', 20, MUTED)
    labels = ['SDR comercial', 'Host COTS', 'Procesamiento', 'Enlace', 'Interfaz']
    for i, label in enumerate(labels):
        x = 0.65 + i*2.46
        box(slide, x, 3.50, 2.16, 0.78, SOFT_BLUE if i < 2 else SOFT_TEAL)
        text(slide, x+0.08, 3.73, 2.0, 0.36, label, 16, BLUE if i < 2 else TEAL, True, PP_ALIGN.CENTER)
        if i < 4:
            arrow(slide, x+2.20, 3.78, 0.21)
    issues = [
        ('Condiciones variables', 'RF, reloj y configuración\ncambian la entrada.'),
        ('Recursos finitos', 'CPU, USB y buffers\ncondicionan el tiempo real.'),
        ('Integración + IA', 'Código plausible y pruebas\naisladas no bastan.'),
    ]
    for i, (title, body) in enumerate(issues):
        x = 0.65+i*4.10
        rule(slide, x, 4.92, 3.8, TEAL)
        text(slide, x, 5.14, 3.8, 0.4, title, 18, INK, True)
        text(slide, x, 5.75, 3.8, 0.8, body, 17, MUTED)

    slide = base(deck, 2, 'Filosofía', 'Cada afirmación necesita evidencia',
        'HITL es barrera de autorización; HIL es barrera de validación. '
        'El oráculo no es el generador; se usa un contexto verificador separado y de solo lectura. '
        'G0 es la única compuerta determinista; una aprobación no anula su rechazo mecánico. '
        'Verificado no equivale a validado; las afirmaciones nombran entorno y nivel. '
        'La iteración por módulo y la trazabilidad de cambios se desarrollan en la diapositiva 4. '
        'No se atribuye certificación normativa a la metodología.')
    principles = [
        ('Requisitos como contrato', 'Ground Truth (GT), sin requisitos inventados.\nCambios con autoridad y trazabilidad.'),
        ('Generador ≠ verificador', 'Implementación y verificación separadas,\ncon criterios y vectores definidos.'),
        ('El humano conserva la decisión', 'Humano (HITL): autoriza el avance.\nHardware en el lazo (HIL): evidencia real.'),
        ('El alcance se declara', 'Verificado ≠ validado.\nCada conclusión nombra nivel y entorno.'),
    ]
    for i, (title, body) in enumerate(principles):
        x, y = 0.65+(i%2)*6.12, 2.05+(i//2)*1.87
        box(slide, x, y, 5.88, 1.62, WHITE)
        text(slide, x+0.20, y+0.19, 5.48, 0.45, title, 20, TEAL, True)
        text(slide, x+0.20, y+0.83, 5.48, 0.66, body, 15.5, MUTED)
    box(slide, 0.65, 6.03, 12.0, 0.62, INK, INK)
    text(slide, 0.85, 6.20, 11.6, 0.36, 'Requisitos → decisiones → pruebas → evidencia', 20, WHITE, True, PP_ALIGN.CENTER)

    slide = base(deck, 3, 'Flujo y decisiones', 'Un flujo con compuertas y trazabilidad',
        'Cadena: S0→G0→S1→G1→S2→G2→S3→G3. G0 verifica estructura de manera determinista; '
        'Gate H es la autorización humana posterior a G0. G1, G2 y G3 son preparados por agentes y decididos '
        'por humanos. Los reportes registran inputs y evidencia; un cambio puede volverlos obsoletos. '
        'S2/G2/S3/G3 se repite por módulos agrupados en slices topológicos en CodeAnvil. Solo G3 system PASS '
        'entrega el Prototipo Verificado. Un RFD nace en S1, G1 o G3 cuando el requisito es inviable en los '
        'COTS declarados: suspende el ciclo y devuelve la decisión al autor del Build Package. '
        'Un defecto interno vuelve al diseño, plan o código responsable; no se relaja el requisito para pasar.')
    box(slide, 0.65, 1.86, 12.0, 0.55, SOFT_BLUE, SOFT_BLUE)
    text(slide, 0.83, 2.02, 11.6, 0.3, 'ENTRADA  ·  Build Package: necesidades, límites COTS y criterios de aceptación', 16.5, BLUE)
    stages = [
        ('S0 → G0', 'Normalizar', 'Requisitos (StRS + SyRS)\nG0: estructura\nGate H: alcance'),
        ('S1 → G1', 'Diseñar', 'Subsistemas y módulos\nContratos + dependencias\nG1: diseño revisado'),
        ('S2 → G2', 'Planificar', 'PLAN.md por módulo\nCriterios + contexto\nG2: plan revisado'),
        ('S3 → G3', 'Construir y verificar', 'Contexto nuevo por módulo\nEvidencia por módulo y ruta\nG3: decisión humana'),
    ]
    for i, (ids, title, body) in enumerate(stages):
        x = 0.65+i*3.06
        box(slide, x, 2.82, 2.82, 2.27)
        text(slide, x+0.16, 3.02, 2.50, 0.4, ids, 23, TEAL, True)
        text(slide, x+0.16, 3.61, 2.52, 0.42, title, 15.2, INK, True)
        text(slide, x+0.16, 4.12, 2.52, 0.82, body, 12.5, MUTED)
        if i < 3:
            arrow(slide, x+2.86, 3.72, 0.17)
    box(slide, 0.65, 5.53, 12.0, 0.70, SOFT_TEAL, SOFT_TEAL)
    text(slide, 0.85, 5.74, 11.6, 0.35, 'SALIDA  ·  Prototipo Verificado con evidencia explícita', 21, TEAL, True, PP_ALIGN.CENTER)
    text(slide, 0.65, 6.52, 12.0, 0.3,
         'Si es inviable en COTS: solicitud de desviación (RFD) al autor; el agente no relaja el contrato.', 13.5, MUTED)

    slide = base(deck, 4, 'Aportes de v4', 'La unidad de iteración es el módulo',
        'V-SIL adapta Agile-V a una mini-V por módulo. Las capas son la estructura, no el orden de iteración. '
        'S2 ordena el backlog por dependencias y produce un PLAN.md autocontenido con requisitos, contratos, '
        'tareas y verificaciones. G2 revisa antes de implementar. S3 utiliza contexto nuevo por módulo, '
        'solo su plan y contexto necesario. G3 ejecuta en contexto verificador separado y el humano decide. '
        'Slice 0 construye bases y kit antes de módulos: Mock HAL, vectores/manifiesto, telemetría, stubs, '
        'pares falsos y drivers. La integración final verifica rutas entre subsistemas. '
        'GT vivo con deltas ADDED/MODIFIED/REMOVED/RENAMED autorizados y revisión correspondiente; '
        'no autoriza al agente a inventar o relajar requisitos. La metodología es agnóstica al agente.')
    loop = [
        ('S2', 'Plan autocontenido', 'PLAN.md + contratos'),
        ('G2', 'Microcompuerta', 'Revisión humana del plan'),
        ('S3', 'Contexto nuevo', 'Implementación acotada'),
        ('G3', 'Verificación separada', 'Evidencia + decisión humana'),
    ]
    for i, (ids, title, body) in enumerate(loop):
        x = 0.65+i*3.06
        box(slide, x, 2.02, 2.82, 1.66, SOFT_TEAL if i%2 == 0 else WHITE)
        text(slide, x+0.17, 2.20, 2.48, 0.43, ids, 26, TEAL, True)
        text(slide, x+0.17, 2.84, 2.48, 0.36, title, 14.3, INK, True)
        text(slide, x+0.17, 3.33, 2.48, 0.26, body, 10.8, MUTED)
        if i < 3:
            arrow(slide, x+2.86, 2.74, 0.17)
    text(slide, 0.65, 3.97, 12.0, 0.36, 'Repetir por módulo; agrupar por dependencias; cerrar con evidencia del sistema.', 16, TEAL)
    features = [
        ('01  Base y kit primero', 'Interfaces y stubs antes\nde los módulos reales.'),
        ('02  Orden por dependencias', 'Slices topológicos; contexto\nacotado por módulo.'),
        ('03  Integración al cierre', 'Contratos y rutas conectadas;\nno solo pruebas aisladas.'),
    ]
    for i, (title, body) in enumerate(features):
        x = 0.65+i*4.10
        rule(slide, x, 4.78, 3.8, TEAL)
        text(slide, x, 4.99, 3.8, 0.4, title, 16.3, INK, True)
        text(slide, x, 5.56, 3.8, 0.68, body, 16, MUTED)
    text(slide, 0.65, 6.52, 12.0, 0.3, 'GT vivo: cambios autorizados y trazables desde el requisito hasta la evidencia.', 14, MUTED)

    slide = base(deck, 5, 'Verificación adaptativa', 'La evidencia declara hasta dónde llega',
        'El piso VL-0 es obligatorio para cada módulo, contrato y ruta declarados. La profundidad se '
        'declara por módulo y ruta. VL-1 usa entrada sintética conocida; VL-2 usa COTS reales en el alcance '
        'ensayado y los criterios/procedimientos pertinentes. Mock-only limita las afirmaciones a VL-1; '
        'mock+real habilita VL-2, sin obligarlo para todas las partes. PIL con datos sintéticos sigue siendo '
        'VERIFICADO, no VALIDADO. Telemetría del equipo acompaña cada evidencia: recursos, temperatura, '
        'buffers y temporización, con diagnóstico de lecturas ausentes. La calibración/tolerancias se '
        'declaran cuando la conclusión las necesita. Esto no equivale a certificación ni demuestra '
        'rendimiento en hardware o enlaces no ensayados. No hay resultados experimentales en esta presentación.')
    text(slide, 0.65, 1.79, 12.0, 0.4, 'Piso VL-0 obligatorio; profundidad declarada por módulo y ruta.', 18, MUTED)
    levels = [
        ('VL-0', 'Lógica y contratos', 'Vectores deterministas\nUnitarias e integración\nRutas conectadas', 'VERIFICADO', BLUE, SOFT_BLUE),
        ('VL-1', 'SIL / Mock HAL', 'Señales sintéticas conocidas\nMétricas contra criterios\nCondiciones controladas', 'VERIFICADO\ncon datos sintéticos', TEAL, SOFT_TEAL),
        ('VL-2', 'HIL / COTS real', 'Dispositivo y enlace ensayados\nCriterios declarados\nCondiciones reales', 'VALIDADO\nen el alcance probado', AMBER, 'FCF3E6'),
    ]
    for i, (vl, title, body, claim, color, fill) in enumerate(levels):
        x = 0.65+i*4.10
        box(slide, x, 2.43, 3.80, 3.05, fill, fill)
        text(slide, x+0.19, 2.62, 3.42, 0.53, vl, 30, color, True)
        text(slide, x+0.19, 3.28, 3.42, 0.38, title, 18, INK, True)
        text(slide, x+0.19, 3.86, 3.42, 0.86, body, 14.1, MUTED)
        text(slide, x+0.19, 4.79, 3.42, 0.64, claim, 12, color, True)
    box(slide, 0.65, 5.69, 12.0, 0.56, INK, INK)
    text(slide, 0.83, 5.85, 11.6, 0.30, 'Telemetría en cada prueba: recursos, temperatura y buffers; declarar señales ausentes.', 15, WHITE)
    text(slide, 0.65, 6.53, 12.0, 0.3, 'mock-only: techo VL-1 · La aprobación final requiere evidencia de módulos y rutas del sistema.', 13.5, MUTED)

    slide = base(deck, 6, 'Espacio reservado', 'Resultados',
        'Espacio deliberadamente en blanco. Aún no hay resultados experimentales para presentar. '
        'Cuando existan, incorporar solo evidencia real por módulo/ruta y nivel, condiciones COTS, '
        'telemetría, criterios y limitaciones. No usar tests del CLI CodeAnvil ni el snapshot histórico '
        'v3 como evaluación de V-SIL v4. No añadir cifras hipotéticas ni un veredicto de aceptación.')
    text(slide, 0.65, 1.65, 12.0, 0.33, 'Evaluación pendiente; sin resultados experimentales reportados.', 14, MUTED)
    box(slide, 0.65, 2.20, 12.0, 4.50, WHITE, LINE)

    assert len(deck.slides) == 6
    for slide in deck.slides:
        for shape in slide.shapes:
            assert shape.left >= 0 and shape.top >= 0
            assert shape.left+shape.width <= deck.slide_width
            assert shape.top+shape.height <= deck.slide_height
    deck.save(OUTPUT)
    print(OUTPUT)


if __name__ == '__main__':
    main()
