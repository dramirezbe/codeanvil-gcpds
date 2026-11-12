# Primero configura el acceso al hardware

Haz esta preparación antes de comenzar el trabajo remoto con el agente. Al terminar,
tu PC tendrá acceso al equipo como `codeanvil-agent` y el proyecto tendrá su propio
workspace. Después, el agente podrá preparar y probar el hardware cuando revises el
código y respondas `continue` en la pausa previa al despliegue.

Esta guía es para un equipo Linux remoto, como una Raspberry Pi. Si el dispositivo
está conectado directamente a tu PC, usa el flujo local de S2/G2; no necesita SSH
ni este alta. Los comandos manuales de esta guía los ejecutas tú en tu terminal.

## 1. Deja listo el equipo y tu PC

En el equipo remoto, activa SSH, comprueba su dirección IP o hostname y conoce el
puerto (normalmente 22). Tu PC debe poder alcanzarlo por la red. Para el primer alta
desde este PC necesitas un usuario existente que acepte contraseña por SSH y pueda
usar `sudo`. Ese usuario es el administrador del alta, no `codeanvil-agent`.

En tu PC necesitas CodeAnvil y `uv`, además de `git`, `ssh`, `ssh-keygen` y `rsync`.
El primer alta por contraseña también utiliza `sshpass`. Instala las herramientas
que falten con el gestor de tu sistema. Trabaja desde un proyecto creado con
CodeAnvil o clonado y registrado; debe existir `.codeanvil/project.yaml` con su UUID.

Comprueba primero que puedes entrar con el administrador y usar sudo. En este
ejemplo, sustituye `pi`, `raspberrypi.local` y `22` por tus datos:

```sh
ssh -t -p 22 -o PubkeyAuthentication=no -o PreferredAuthentications=password \
  pi@raspberrypi.local 'id && sudo -v'
```

Comprueba la identidad del equipo si SSH te pide confirmar su clave. Si falla la
conexión o sudo, corrige usuario, contraseña, dirección, puerto o servicio SSH antes
de seguir. Este paso manual solo hace falta para preparar el primer acceso; si
este PC ya tiene acceso dedicado al equipo, pasa al alta del proyecto.

## 2. Enlaza el equipo con el proyecto

Desde la raíz de tu proyecto, ejecuta:

```sh
codeanvil credential-setup -u pi -i raspberrypi.local --port 22
```

Introduce las contraseñas en los prompts de tu terminal. No las envíes al chat ni
las guardes en el proyecto. Si sudo usa la misma contraseña, pulsa Enter cuando
el comando te lo indique.

El comando descubre las MAC físicas, crea o reutiliza las claves de este PC,
prepara el usuario `codeanvil-agent` con sudo sin contraseña y añade las claves
públicas conservando las de otros PCs. Prepara rsync/rrsync y el workspace
`/home/codeanvil-agent/projects/<UUID-del-proyecto>`, verifica el acceso por clave
y escribe la metadata pública en `.codeanvil/project.yaml`.

No necesitas elegir `--target` ni editar rutas de claves. `-u` indica el administrador;
la MAC reconoce el equipo. En otro proyecto, repite el comando para enlazar su
workspace: reutiliza las claves de este PC. En otro PC, cada persona hace su primer
alta con el administrador para autorizar sus propias claves al mismo usuario remoto.
Las privadas se quedan en cada PC; clonar el proyecto no concede acceso por sí solo.

## 3. Conecta el MCP con tu agente

Desde el proyecto, instala y habilita el servidor:

```sh
codeanvil mcp add vsil_hil_mcp
codeanvil mcp enable vsil_hil_mcp
codeanvil mcp doctor vsil_hil_mcp
```

Si ya estaba instalado y acabas de actualizar CodeAnvil, usa
`codeanvil mcp update vsil_hil_mcp` antes de volver a habilitarlo; `enable` también
copia la skill y esta guía al proyecto. Recarga o abre una sesión del agente desde
ese proyecto para que descubra las herramientas MCP.

`mcp doctor` comprueba la instalación local del servidor. Para comprobar el acceso
real, pide al agente: «Comprueba el acceso al equipo por MCP sin desplegar ni probar
el dispositivo». Debe confirmar el usuario remoto `codeanvil-agent`, OS/arquitectura,
sudo sin contraseña, rsync y el workspace declarado accesible y escribible. Si hay
varios equipos, indica cuál de los registrados quieres usar.

## 4. Comienza el trabajo con acceso confirmado

Cuando esa comprobación funcione, el agente puede seguir el flujo de las skills.
No necesitas instalar CodeAnvil en el equipo remoto a mano para terminar el alta:
el agente actualizará herramienta, dependencias y proyecto después de la revisión
previa al hardware. Un fallo de `probe_target` porque CodeAnvil aún no está instalado
se resuelve en esa preparación; no significa que tus claves SSH estén mal.

Antes de actualizar, desplegar o ejecutar pruebas físicas, el agente te mostrará
candidato, equipo y operaciones y esperará tu `continue`. Configurar el acceso no
sustituye esa revisión. Las pausas configurables de S2 y los veredictos humanos de
G2 siguen vigentes.

## Si algo falla

| Situación | Qué hacer |
|-----------|-----------|
| No conecta por SSH | Revisa red, dirección, puerto y que SSH esté activo. |
| Rechaza contraseña o sudo | Comprueba el administrador usado en `-u`; el primer alta usa autenticación por contraseña. |
| No descubre MAC física | Comprueba que estás entrando al equipo previsto y que sus interfaces físicas son visibles; no inventes una MAC. |
| Falta una clave local de un equipo ya registrado | Restaura tus claves desde tu respaldo; no borres el almacén para forzar otras ni copies las privadas de otra persona. |
| Cambió la clave SSH del equipo | Confirma si se reinstaló o cambió el equipo y revisa el pin local antes de volver a dar acceso; no borres `known_hosts` a ciegas. |
| El agente no ve las herramientas | Repite `mcp enable`, revisa `mcp doctor` y recarga la sesión en el proyecto correcto. |
| SSH funciona, pero falta CodeAnvil remoto | El agente lo instalará después de la pausa previa al hardware. |
