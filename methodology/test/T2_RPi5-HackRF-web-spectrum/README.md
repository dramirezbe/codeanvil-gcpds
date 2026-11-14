# T2 — Espectro web mínimo, RPi5 + HackRF, con VL-2

Entrada: [build_package.md](build_package.md). Un gráfico de espectro, siete
controles RX y un backend Python que también sirve el dashboard Vite compilado.
La RPi5 escucha en `0.0.0.0:8000`; el navegador abre su IP LAN.

T1 es el antecedente: usa x86_64, contiene errores deliberados de triage y deja
VL-2 pendiente. T2 usa RPi5, no incluye errores sembrados y define un ensayo real
funcional de unos minutos. No depende de una emisora conocida ni de un generador.

## Usarlo

```bash
codeanvil create --name "RPi5 HackRF Web Spectrum"
cd rpi5_hackrf_web_spectrum
cp <ruta-del-repo>/methodology/test/T2_RPi5-HackRF-web-spectrum/build_package.md \
  .codeanvil/GT/build_package.md
codex
```

Elegir un ciclo y recorrer S0 → G0 → S1 → G1 → S2 → G2 con sus skills y decisiones
humanas. El único archivo que se copia como entrada es `build_package.md`; no
copiar el T1 ni los snapshots existentes. No se ha ejecutado ni aprobado G2 para T2.

VL-0/VL-1: oráculos deterministas y Mock HAL en el PC, sin hardware. En la
preparación de G2, disponer de RPi5 refrigerada, HackRF por USB y LAN; instalar y
habilitar `vsil_hil_mcp` cuando lo solicite la metodología. Marconi no es necesario.
El humano proporciona el acceso al equipo y el `continue` de hardware. No guardar
credenciales en el Build Package. La prueba de bias se hace con SMA desconectado.

## Criterios deliberadamente cómodos

- FFT fija de 1024 puntos y una única API HTTP; polling, sin WebSocket.
- Perfil base de 8 MS/s: al menos 2 espectros/s durante 30 s y huecos ≤3 s.
- Hasta 10 s para aplicar cada cambio; se permite reiniciar la captura.
- Arranque ≤15 s; RAM backend+captura ≤1 GiB.
- dBFS relativo: VL-2 no afirma potencia RF calibrada ni exactitud de sintonía.

Las fuentes oficiales y cláusulas aplicables están en A.2/A.3. Las tolerancias
son decisiones del proyecto, no valores atribuidos a las RFC. Una prueba física
puede fallar por USB, alimentación o permisos: ese diagnóstico no se sustituye
por datos mock ni por un PASS automático.
