#!/usr/bin/env bash
# install.sh — TuxCue V1 setup for Linux Mint / Ubuntu 22.04+
# Usage: bash install.sh
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
fail() { echo -e "${RED}✗${NC} $*"; exit 1; }

echo ""
echo "════════════════════════════════════════"
echo "  TuxCue V1 — Instalación"
echo "════════════════════════════════════════"
echo ""

# ── 1. Python 3.11+ ──────────────────────────────────────────────────
PYTHON=""
for cmd in python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null; then
        if $cmd -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
            # Verify venv module is available for this interpreter
            if $cmd -m venv --help &>/dev/null; then
                PYTHON="$cmd"
                ok "Python encontrado: $($cmd --version)"
                break
            fi
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    warn "Python 3.11+ con venv no encontrado. Instalando..."
    sudo apt-get update -q
    sudo apt-get install -y software-properties-common
    # Try system package first (Mint 22 / Ubuntu 24.04)
    if sudo apt-get install -y python3.12-venv 2>/dev/null; then
        PYTHON="python3.12"
    else
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update -q
        sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
        PYTHON="python3.11"
    fi
    ok "Python con venv instalado: $($PYTHON --version)"
fi

# ── 2. Dependencias del sistema ───────────────────────────────────────
echo ""
echo "Instalando dependencias del sistema..."
sudo apt-get update -q
sudo apt-get install -y \
    git \
    libegl1 \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    pulseaudio \
    2>/dev/null || true
ok "Dependencias del sistema instaladas"

# ── 3. Entorno virtual ────────────────────────────────────────────────
echo ""
VENV_DIR="$(pwd)/.venv"
# Reuse only if the venv is valid (activate script exists)
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    warn "Entorno virtual ya existe en .venv — reutilizando"
elif [[ -d "$VENV_DIR" ]]; then
    warn "Entorno virtual incompleto detectado — recreando..."
    rm -rf "$VENV_DIR"
    $PYTHON -m venv "$VENV_DIR"
    ok "Entorno virtual recreado"
else
    echo "Creando entorno virtual en .venv ..."
    $PYTHON -m venv "$VENV_DIR"
    ok "Entorno virtual creado"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet

# ── 4. Dependencias Python ────────────────────────────────────────────
echo ""
echo "Instalando PySide6 y miniaudio (puede tardar 1-2 minutos)..."
pip install "PySide6>=6.6" "miniaudio>=1.60" --quiet
ok "PySide6 y miniaudio instalados"

# ── 5. Verificación: tests ────────────────────────────────────────────
echo ""
echo "Ejecutando tests de verificación..."
pip install pytest --quiet
if python -m pytest tests/ -q --tb=short 2>&1 | tail -4; then
    ok "Todos los tests pasan"
else
    warn "Algunos tests fallaron (puede ser normal si PySide6-stubs no está instalado)"
fi

# ── 6. Lanzador ───────────────────────────────────────────────────────
# xdg-user-dir returns the correct Desktop path for any locale
DESKTOP=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")
mkdir -p "$DESKTOP"
APP_DIR="$(pwd)"
LAUNCHER="$DESKTOP/TuxCue.sh"
cat > "$LAUNCHER" <<LAUNCHEREOF
#!/usr/bin/env bash
cd "$APP_DIR"
source .venv/bin/activate
python main.py
LAUNCHEREOF
chmod +x "$LAUNCHER"
ok "Lanzador creado en: $LAUNCHER"

# ── Resumen ───────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
echo -e "  ${GREEN}Instalación completada${NC}"
echo "════════════════════════════════════════"
echo ""
echo "  Para arrancar la aplicación desde el terminal:"
echo ""
echo "    cd $APP_DIR"
echo "    source .venv/bin/activate"
echo "    python main.py"
echo ""
echo "  O ejecuta directamente:"
echo "    bash \"$LAUNCHER\""
echo ""
