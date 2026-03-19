# tecjustica-transcribe

CLI para transcrição de audiências judiciais com WhisperX e diarização de falantes.

Transcreve vídeos MP4 gerando texto com timestamps e identificação de quem está falando (Juiz, Promotor, Advogado, etc. — identificados como SPEAKER_00, SPEAKER_01...).

## Requisitos do Sistema

### Sistema Operacional

| SO | Suporte | Observações |
|----|---------|-------------|
| **Ubuntu/Debian (WSL2)** | ✅ Testado | Recomendado para usuários Windows |
| **Ubuntu/Debian nativo** | ✅ Compatível | Instalação direta |
| **Windows nativo** | ❌ Não suportado | Use WSL2 (veja [Guia WSL2](#guia-rápido-windows-com-wsl2)) |
| **macOS** | ❌ Não suportado | Requer GPU NVIDIA (CUDA) |

> **Usuários Windows**: instale o [WSL2](https://learn.microsoft.com/pt-br/windows/wsl/install) com Ubuntu. O WSL2 acessa a GPU NVIDIA do Windows automaticamente.

### Hardware

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **GPU NVIDIA** | 6 GB VRAM (ex: RTX 3050) | 8 GB+ VRAM (ex: RTX 3060, RTX 4060) |
| **RAM** | 8 GB | 16 GB |
| **Disco** | 10 GB livres (para modelos de IA) | 15 GB+ |

> GPUs AMD e Intel **não são compatíveis**. É necessária uma GPU NVIDIA com suporte a CUDA.

### Software

| Dependência | Como instalar | Verificar |
|-------------|---------------|-----------|
| **Driver NVIDIA** | [nvidia.com/drivers](https://www.nvidia.com/drivers) ou Windows Update | `nvidia-smi` |
| **CUDA** | Instalado automaticamente junto com o PyTorch | `python3 -c "import torch; print(torch.cuda.is_available())"` |
| **ffmpeg** | `sudo apt install ffmpeg` | `ffmpeg -version` |
| **Python 3.10–3.13** | `sudo apt install python3.12` | `python3 --version` |
| **uv** (gerenciador recomendado) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv --version` |

> Não sabe se está tudo certo? Rode `tecjustica-transcribe init` após instalar — ele verifica tudo e mostra o que está faltando.

### Token HuggingFace (necessário para identificar falantes)

A diarização (identificar quem está falando) usa o modelo [pyannote](https://huggingface.co/pyannote/speaker-diarization-community-1), que exige um token **gratuito** do HuggingFace:

1. Crie uma conta em https://huggingface.co/join
2. Acesse https://huggingface.co/pyannote/speaker-diarization-community-1 e clique em **"Agree and access repository"**
3. Gere um token do tipo **"Read"** em https://huggingface.co/settings/tokens

O comando `init` vai pedir esse token e salvá-lo na sua máquina.

> **Sem o token**, você ainda pode transcrever usando `--sem-diarizacao` — a transcrição funciona normalmente, só não identifica os falantes.

## Instalação

```bash
curl -fsSL https://raw.githubusercontent.com/marcosmarf27/tecjustica-transcribe/main/install.sh | bash
```

O script instala automaticamente: Python, dependências, ffmpeg e o app.

Após instalar, execute:

```bash
tecjustica-transcribe init    # configurar GPU e token HuggingFace
tecjustica-gui                # abrir interface gráfica
```

### Atualizar para versão mais recente

```bash
curl -fsSL https://raw.githubusercontent.com/marcosmarf27/tecjustica-transcribe/main/install.sh | bash -s -- --update
```

Ou, se já tem o script localmente:

```bash
bash install.sh --update
```

### Desinstalar

```bash
curl -fsSL https://raw.githubusercontent.com/marcosmarf27/tecjustica-transcribe/main/install.sh | bash -s -- --uninstall
```

## Passo a Passo: Do Zero à Transcrição

### 1. Verificar requisitos (só precisa rodar uma vez)

```bash
tecjustica-transcribe init
```

O `init` verifica seu sistema, baixa os modelos de IA (~3 GB no primeiro uso) e pede o token HuggingFace:

```
╭──────────────── TecJustiça Transcribe — Diagnóstico ─────────────────╮
│ Python            ✅ 3.12.3                                          │
│ Driver NVIDIA     ✅ 591.44                                          │
│ CUDA              ✅ 12.8                                            │
│ GPU               ✅ NVIDIA GeForce RTX 3050 6GB Laptop GPU (6.0 GB) │
│ ffmpeg            ✅ 6.1.1                                           │
│ Token HuggingFace ✅ hf_pcgK...                                      │
╰──────────────────────────────────────────────────────────────────────╯
✅ Tudo pronto para transcrever!
```

Se algum item mostrar ❌, resolva antes de transcrever (veja [Solução de Problemas](#solução-de-problemas)).

### 2. Transcrever

```bash
# Com identificação de falantes (~13 min para 1h de vídeo)
tecjustica-transcribe transcrever audiencia.mp4

# Sem identificar falantes, mais rápido (~2 min para 1h de vídeo)
tecjustica-transcribe transcrever audiencia.mp4 --sem-diarizacao

# Escolher pasta de saída (padrão: ./transcricoes/)
tecjustica-transcribe transcrever audiencia.mp4 --output ./minha-pasta
```

> **Usuários WSL2**: os arquivos do Windows ficam em `/mnt/c/`. Exemplo:
> ```bash
> # Arquivo em C:\Users\marcos\Downloads\audiencia.mp4
> tecjustica-transcribe transcrever /mnt/c/Users/marcos/Downloads/audiencia.mp4
> ```

### 3. Resultado

Os arquivos são salvos na pasta `./transcricoes/` (relativa a onde você rodou o comando):

| Arquivo | Formato | Para que serve |
|---------|---------|----------------|
| `audiencia.txt` | Texto puro com `[SPEAKER_00]` | Leitura e análise |
| `audiencia.srt` | Legendas com timestamps | Abrir em players (VLC, etc.) |
| `audiencia.json` | Dados completos por palavra | Integração com outros sistemas |

Exemplo do `.txt`:
```
[SPEAKER_02]
Boa tarde, meu nome é Fabriziane, eu sou juiz aqui na violência doméstica.

[SPEAKER_00]
Boa tarde, senhora Neide, meu nome é Vinícius, eu sou promotor de justiça.

[SPEAKER_04]
Boa tarde, tudo bem.
```

## Solução de Problemas

| Problema | Solução |
|----------|---------|
| `nvidia-smi` não encontrado | Instale o driver NVIDIA: [nvidia.com/drivers](https://www.nvidia.com/drivers) |
| CUDA não disponível | Verifique se o driver NVIDIA é compatível com CUDA 12+. No WSL2, atualize o driver do Windows |
| Erro de memória (OOM) | Feche outros programas (especialmente navegadores). Tente `--sem-diarizacao` |
| Token HuggingFace negado (403) | Aceite os termos em [huggingface.co/pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1) |
| ffmpeg não encontrado | `sudo apt install ffmpeg` |
| `uv: command not found` | Instale o uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` e depois `source ~/.bashrc` |
| Transcrição muito lenta | Verifique se está usando GPU (`init` deve mostrar GPU ✅). CPU é 10x mais lento |

## Guia Rápido: Windows com WSL2

Se você usa Windows e nunca usou WSL2, siga estes passos:

```bash
# 1. Abrir PowerShell como Administrador e instalar WSL2
wsl --install
# Reinicie o computador quando solicitado
```

```bash
# 2. Abrir o Ubuntu (WSL2) e instalar tudo com um comando
curl -fsSL https://raw.githubusercontent.com/marcosmarf27/tecjustica-transcribe/main/install.sh | bash

# 3. Configurar (só uma vez — pede o token HuggingFace)
tecjustica-transcribe init

# 4. Transcrever! (arquivo do Windows acessível via /mnt/c/)
tecjustica-transcribe transcrever /mnt/c/Users/SeuUsuario/Downloads/audiencia.mp4
```

> **Dica**: No WSL2, `C:\Users\marcos\Downloads\` vira `/mnt/c/Users/marcos/Downloads/`
