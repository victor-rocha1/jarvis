# Projeto J.A.R.V.I.S. - Arquitetura e Planejamento

## 1. Visão Geral e Princípios
O sistema é projetado sob o padrão de **Arquitetura Modular (Desacoplada)**. O objetivo é garantir que o assistente possa iniciar de forma simples (texto no terminal) e evoluir para um sistema complexo (reconhecimento de voz, controle Bluetooth, painel HUD) sem a necessidade de reescrever o código base.

**Princípio Central:** Separação de responsabilidades. O cérebro (Gemini) nunca interage diretamente com o microfone ou com a lâmpada; ele recebe mensagens de entrada, processa lógicas e aciona ferramentas de saída.

---

## 2. As Três Camadas do Sistema

1. **Interfaces (Entrada / Saída):**
   * Como você fala com o Jarvis e como ele responde.
   * *Hoje:* Terminal (texto) e Alto-falante (Edge-TTS).
   * *Futuro:* Microfone (Wake word/Whisper) e Interface Gráfica (Electron).

2. **Core (O Núcleo / Orquestrador):**
   * O motor central do sistema.
   * Recebe a entrada da Interface, envia para a API do Gemini, gerencia o histórico de conversa (memória) e encaminha a resposta de volta para a Interface.

3. **Plugins (As Ferramentas / Habilidades):**
   * Módulos isolados que executam ações no mundo real ou digital.
   * Eles são mapeados no Gemini através do recurso de *Function Calling*.
   * *Exemplos:* Módulo Bluetooth (Geonav), Módulo Gmail, Módulo Agenda.

---

## 3. Estrutura de Diretórios Padronizada

Esta é a árvore oficial de pastas do projeto. Ela organiza o código para que novas funcionalidades sejam apenas "arquivos adicionados", e não "código alterado".

```text
jarvis_project/
│
├── main.py                  # Ponto de entrada (inicia as interfaces e o core)
├── requirements.txt         # Lista de dependências (google-genai, edge-tts, bleak, etc.)
│
├── config/                  # Arquivos de configuração
│   └── settings.py          # Chaves de API, endereços MAC, configurações gerais
│
├── core/                    # O Núcleo do sistema (Intocável)
│   ├── brain.py             # Comunicação com a API do Gemini
│   └── memory.py            # Gerenciamento do histórico da conversa
│
├── interfaces/              # Camada de comunicação com o usuário
│   ├── cli.py               # Interface de texto via Terminal
│   ├── voice_out.py         # Módulo de conversão de texto para fala (TTS)
│   └── (Futuro) audio_in.py # Módulo de escuta (Microfone/Wake Word)
│
└── plugins/                 # Funcionalidades expansíveis
    ├── base_plugin.py       # Molde padrão que todo plugin deve seguir
    ├── geonav_light.py      # Script isolado para a lâmpada Bluetooth
    └── google_suite.py      # Script isolado para Gmail e Agenda