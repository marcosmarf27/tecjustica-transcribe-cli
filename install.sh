#!/usr/bin/env bash
# TecJustiça Transcribe — Instalador
# Uso: curl -fsSL https://raw.githubusercontent.com/marcosmarf27/tecjustica-transcribe/main/install.sh | bash
#      bash install.sh [--update | --uninstall | --help]
set -euo pipefail

# ── Cores e formatação ──────────────────────────────────────────────
BOLD='\033[1m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

info()    { echo -e "${BLUE}$*${RESET}"; }
success() { echo -e "${GREEN}✓ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }
error()   { echo -e "${RED}✗ $*${RESET}"; exit 1; }
step()    { echo -e "\n${BOLD}=> $*${RESET}"; }

PACKAGE="tecjustica-transcribe"
PACKAGE_GUI="${PACKAGE}[gui]"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_URL="https://raw.githubusercontent.com/marcosmarf27/tecjustica-transcribe/main/assets/icon.svg"
DESKTOP_FILE="$DESKTOP_DIR/tecjustica-gui.desktop"
ICON_FILE="$ICON_DIR/tecjustica-transcribe.svg"

# ── Parsing de argumentos ───────────────────────────────────────────
ACTION="install"
for arg in "$@"; do
    case "$arg" in
        --update)    ACTION="update" ;;
        --uninstall) ACTION="uninstall" ;;
        --help|-h)
            echo "Uso: bash install.sh [--update | --uninstall | --help]"
            echo ""
            echo "  (sem args)    Instalar TecJustiça Transcribe"
            echo "  --update      Atualizar para a versão mais recente"
            echo "  --uninstall   Remover o programa"
            echo "  --help        Mostrar esta ajuda"
            exit 0
            ;;
        *) error "Argumento desconhecido: $arg (use --help)" ;;
    esac
done

# ── Detectar WSL2 ───────────────────────────────────────────────────
IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=true
fi

# ── Desinstalar ─────────────────────────────────────────────────────
if [ "$ACTION" = "uninstall" ]; then
    step "Desinstalando $PACKAGE"

    if command -v uv &>/dev/null; then
        uv tool uninstall "$PACKAGE" 2>/dev/null && success "Pacote removido" || warn "Pacote não estava instalado"
    else
        warn "uv não encontrado — nada para remover"
    fi

    # Remover atalho e ícone
    rm -f "$DESKTOP_FILE" "$ICON_FILE"
    success "Atalho de desktop removido"

    CONFIG_DIR="$HOME/.config/tecjustica"
    if [ -d "$CONFIG_DIR" ]; then
        echo ""
        if [ -t 0 ]; then
            read -rp "Remover configurações em $CONFIG_DIR? [s/N] " resp
            if [[ "$resp" =~ ^[sS]$ ]]; then
                rm -rf "$CONFIG_DIR"
                success "Configurações removidas"
            else
                info "Configurações mantidas em $CONFIG_DIR"
            fi
        else
            info "Configurações mantidas em $CONFIG_DIR (use interativamente para remover)"
        fi
    fi

    echo ""
    success "Desinstalação concluída"
    exit 0
fi

# ── Preflight checks ────────────────────────────────────────────────
step "Verificando sistema"

# Linux x86_64
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ]; then
    error "Arquitetura não suportada: $ARCH (necessário: x86_64)"
fi

OS=$(uname -s)
if [ "$OS" != "Linux" ]; then
    error "Sistema não suportado: $OS (necessário: Linux)"
fi
success "Linux x86_64"

if [ "$IS_WSL" = true ]; then
    info "WSL2 detectado"
else
    info "Linux nativo detectado"
fi

# GPU NVIDIA (aviso, não bloqueia)
if command -v nvidia-smi &>/dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    success "GPU NVIDIA: $GPU_NAME"
else
    warn "nvidia-smi não encontrado — a transcrição vai funcionar, mas será lenta (CPU)"
    warn "Para usar GPU, instale o driver NVIDIA: https://www.nvidia.com/drivers"
fi

# ── Instalar pacotes do sistema ─────────────────────────────────────
step "Verificando dependências do sistema"

SYSTEM_DEPS=(ffmpeg libgirepository-2.0-dev gcc libcairo2-dev pkg-config python3-dev)

# WebKit só no Linux nativo (não WSL2)
if [ "$IS_WSL" = false ]; then
    SYSTEM_DEPS+=(gir1.2-webkit2-4.1)
fi

MISSING_DEPS=()
for dep in "${SYSTEM_DEPS[@]}"; do
    status=$(dpkg-query -W -f='${db:Status-Abbrev}' "$dep" 2>/dev/null || true)
    if [[ "$status" != ii* ]]; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    info "Instalando: ${MISSING_DEPS[*]}"
    sudo apt-get update -qq
    sudo apt-get install -y -qq "${MISSING_DEPS[@]}"
    success "Dependências do sistema instaladas"
else
    success "Todas as dependências do sistema já instaladas"
fi

# ── Instalar uv ─────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    step "Instalando uv (gerenciador de pacotes Python)"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$BIN_DIR:$PATH"
    if ! command -v uv &>/dev/null; then
        error "uv não encontrado após instalação — verifique seu PATH"
    fi
    success "uv instalado"
else
    success "uv já instalado ($(uv --version))"
fi

# ── Instalar / Atualizar pacote ─────────────────────────────────────
if [ "$ACTION" = "update" ]; then
    step "Atualizando $PACKAGE"
    uv tool install "$PACKAGE_GUI" --force --upgrade --python ">=3.10,<3.14"
    success "Atualizado com sucesso"
else
    step "Instalando $PACKAGE"
    uv tool install "$PACKAGE_GUI" --force --python ">=3.10,<3.14"
    success "Pacote instalado"
fi

# ── PyGObject no venv do uv tool (só Linux nativo) ──────────────────
if [ "$IS_WSL" = false ]; then
    step "Instalando PyGObject (interface nativa)"
    TOOL_VENV="$HOME/.local/share/uv/tools/$PACKAGE"
    if [ -d "$TOOL_VENV" ]; then
        uv pip install --python "$TOOL_VENV/bin/python" PyGObject
        success "PyGObject instalado"
    else
        warn "Venv do uv tool não encontrado em $TOOL_VENV — PyGObject não instalado"
    fi
fi

# ── Verificar PATH ──────────────────────────────────────────────────
step "Verificando PATH"

if echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
    success "$BIN_DIR está no PATH"
else
    warn "$BIN_DIR não está no PATH"
    SHELL_RC=""
    if [ -n "${ZSH_VERSION:-}" ] || [ "$(basename "$SHELL")" = "zsh" ]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.bashrc"
    fi

    if [ -f "$SHELL_RC" ] && grep -q "$BIN_DIR" "$SHELL_RC" 2>/dev/null; then
        info "Já configurado em $SHELL_RC — rode: source $SHELL_RC"
    else
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
        success "Adicionado ao $SHELL_RC"
        info "Rode: source $SHELL_RC (ou abra um novo terminal)"
    fi
    export PATH="$BIN_DIR:$PATH"
fi

# ── Verificar instalação ────────────────────────────────────────────
step "Verificando instalação"

if command -v tecjustica-transcribe &>/dev/null; then
    VERSION=$(tecjustica-transcribe --version 2>/dev/null || echo "?")
    success "tecjustica-transcribe $VERSION"
else
    error "tecjustica-transcribe não encontrado após instalação"
fi

if command -v tecjustica-gui &>/dev/null; then
    success "tecjustica-gui disponível"
else
    warn "tecjustica-gui não encontrado (pode precisar recarregar o terminal)"
fi

# ── Criar atalho de desktop ──────────────────────────────────────────
step "Criando atalho de desktop"

mkdir -p "$ICON_DIR" "$DESKTOP_DIR"

# Baixar ícone
if curl -fsSL "$ICON_URL" -o "$ICON_FILE" 2>/dev/null; then
    success "Ícone instalado"
else
    # Fallback: ícone genérico do sistema
    ICON_FILE="audio-x-generic"
    warn "Não foi possível baixar o ícone — usando ícone genérico"
fi

cat > "$DESKTOP_FILE" << DESKTOP
[Desktop Entry]
Name=TecJustiça Transcribe
Comment=Transcrição de audiências judiciais com IA
Exec=$BIN_DIR/tecjustica-gui
Icon=$ICON_FILE
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Office;
Keywords=transcrição;audiência;whisperx;justiça;
DESKTOP
chmod 644 "$DESKTOP_FILE"
success "Atalho criado — procure 'TecJustiça' no menu de aplicativos"

if [ "$IS_WSL" = true ]; then
    info "No WSL2, o atalho aparece no menu Iniciar do Windows"
fi

# ── Mensagem final ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╭──────────────────────────────────────────────────────╮${RESET}"
echo -e "${GREEN}│${RESET}  ${BOLD}TecJustiça Transcribe instalado com sucesso!${RESET}        ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}                                                      ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  Próximo passo:                                      ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}    ${BOLD}tecjustica-transcribe init${RESET}                        ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}                                                      ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  O init vai verificar GPU, pedir token HuggingFace   ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  e baixar modelos de IA (~3 GB).                     ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}                                                      ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  Depois:                                             ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}    ${BOLD}tecjustica-gui${RESET}          (interface gráfica)       ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}    ${BOLD}tecjustica-transcribe transcrever arquivo.mp4${RESET}     ${GREEN}│${RESET}"
echo -e "${GREEN}╰──────────────────────────────────────────────────────╯${RESET}"
