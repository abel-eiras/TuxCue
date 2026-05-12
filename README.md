# 🎭 TuxCue

Un reproductor de audio para regidores y técnicos de sonido en producciones teatrales. Sin florituras, sin secuenciación automática, sin las mil funciones que no vas a usar. Solo tus pistas, tus cues y control total sobre cada una de ellas.

<p align="left">
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/PySide6_(Qt6)-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6"/>
<img src="https://img.shields.io/badge/miniaudio-FF6B35?style=for-the-badge&logo=soundcloud&logoColor=white" alt="miniaudio"/>
<img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux"/>
</p>

---

## 🎬 Por qué existe esto

Si alguna vez has intentado usar VLC, Audacity o cualquier reproductor convencional para manejar los efectos de sonido de una obra de teatro durante una función, sabes lo que es sufrir. Cuando el director te pide "música de entrada, trueno a los 30 segundos, y que el ambiente de lluvia no pare" al mismo tiempo, no hay forma elegante de hacerlo con un reproductor normal.

TuxCue nace de esa necesidad: un cartwall polifónico donde cada pista es independiente, puedes disparar y parar lo que quieras cuando quieras, ajustar el volumen en tiempo real sin cortes y organizar los cues exactamente como aparecen en el guion.

---

## ✨ Qué hace (V1)

- **Polifonía real** — N pistas sonando a la vez sin limitación de software
- **Play / Stop por pista** — independientes entre sí, sin afectarse
- **Loop por pista** — la pista vuelve a empezar sola al terminar
- **Volumen individual en tiempo real** — el slider mueve la ganancia mientras el audio suena, sin reiniciar
- **Duración automática** — detectada al cargar el fichero (WAV, FLAC, MP3, OGG)
- **Drag & drop interno** — reordena las filas según el guion arrastrando
- **Drag & drop externo** — arrastra ficheros desde el explorador directamente a la tabla
- **Filtro por nombre** — busca en tiempo real entre tus cues
- **Filtro por duración** — aísla ambient tracks, efectos cortos, etc.
- **Sesiones `.tuxcue.json`** — guarda y carga: orden, nombres, volúmenes y loops
- **Nombre editable** — haz doble clic en la columna Nombre para renombrar una pista
- **Pistas no encontradas marcadas en rojo** — si mueves los ficheros de sitio, la aplicación no se rompe, te avisa

---

## 🚀 Instalación (Linux Mint / Ubuntu 22.04+)

```bash
# 1. Clona el repositorio
git clone https://github.com/abel-eiras/TuxCue.git
cd TuxCue

# 2. Lanza el instalador (crea el entorno virtual, instala dependencias y un lanzador en el Escritorio)
bash install.sh
```

El script se encarga de todo: Python 3.11+, entorno virtual, PySide6, miniaudio y las librerías del sistema necesarias. Al terminar tendrás un `TuxCue.sh` en el Escritorio.

**Para actualizar a la última versión:**
```bash
cd TuxCue
git pull
```
No hace falta reinstalar; el entorno virtual ya existe.

### Arranque manual desde terminal
```bash
cd TuxCue
source .venv/bin/activate
python main.py
```

---

## 🎛️ Cómo usarlo

1. **Carga tus pistas** — arrástralas desde el explorador de archivos a la tabla, o usa el menú File
2. **Renombra** — doble clic en el nombre para que coincida con tu guion
3. **Ajusta volúmenes** — mueve el slider antes o durante la función
4. **Activa Loop** en las pistas de ambiente que deban repetirse
5. **Reordena** — arrastra las filas para que sigan el orden del guion
6. **Guarda la sesión** — `Ctrl+S` → `funcion_sabado_noche.tuxcue.json`
7. En la siguiente función: `Ctrl+O`, selecciona el fichero y todo está como lo dejaste

---

## 🗂️ Estructura del proyecto

```
TuxCue/
├── src/
│   ├── core/          # Track, AudioController, interfaces, sesiones
│   ├── audio/         # AudioEngine (miniaudio, sin Qt), probe_duration
│   └── gui/           # MainWindow, tabla, delegates, filtros
├── tests/             # 120 tests (pytest, offscreen)
├── docs/              # PRD, arquitectura, stack, decisiones y lecciones
├── main.py
└── install.sh
```

El motor de audio (`src/audio`) no importa Qt en absoluto. El `AudioController` es la única capa que traduce callbacks de audio a señales Qt. Así el motor es testeable sin pantalla y portable a otros backends si algún día hace falta.

---

## 🗺️ Roadmap

| Versión | Estado | Qué incluye |
|---------|--------|-------------|
| **V1.0** | ✅ Listo | Cartwall completo: polifonía, filtros, drag & drop, sesiones |
| **V1.1** | 🔜 Próximo | VU meter global, waveform thumbnail por pista, exportar lista de cues |
| **V2.0** | 💭 Futuro | Línea de tiempo (mini-DAW), automatización de volumen, grupos/buses |

---

## 🧪 Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -q
```

120 tests, todos en modo offscreen (sin necesidad de display físico).

---

## 📋 Formatos de audio compatibles

WAV · FLAC · MP3 · OGG/Vorbis

---

*Hecho con Python, Qt6, miniaudio y demasiado café. Para Linux.*
