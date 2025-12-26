"""
Módulo de documentação do sistema de configuração type-safe.

Este documento descreve a arquitetura centralizada de configurações
e como utilizá-la nos diferentes componentes da aplicação.
"""

# ============================================================================
# VISÃO GERAL
# ============================================================================
#
# O novo sistema de configuração fornece:
#
# 1. Type-Safe: Configurações validadas em tempo de desenvolvimento
# 2. Centralizado: Única fonte de verdade para todas as configurações
# 3. Estruturado: Organização lógica com dataclasses
# 4. Flexível: Suporta YAML + variáveis de ambiente
# 5. Testável: Fácil de mockar e testar
#
# ============================================================================
# ARQUITETURA
# ============================================================================
#
# src/infrastructure/config/
# ├── __init__.py              # Exports públicas
# ├── settings.py              # Dataclasses de configuração type-safe
# └── config_loader.py         # Carregador de configurações YAML + .env
#
# Componentes Principais:
#
# 1. YOLOParams
#    - Configurações específicas do modelo YOLO
#    - Valores com defaults inteligentes
#    - Conversão bidirecional Dict <-> Dataclass
#
# 2. TrackModelConfig
#    - Backend path + Parâmetros YOLO
#    - Encapsula configuração completa do modelo
#
# 3. FindfaceConfig
#    - Carrega URL e token do FindFace
#    - Valores das variáveis de ambiente (.env)
#    - Validação obrigatória de token
#
# 4. ApplicationSettings
#    - Configurações centralizadas da aplicação
#    - Combina TrackModelConfig e FindfaceConfig
#    - Método to_dict() para serialização
#
# 5. ConfigLoader
#    - Lê arquivo YAML e variáveis de ambiente
#    - Valida estrutura e conteúdo
#    - Implementa cache (singleton)
#    - Interface limpa: .load(), .reload()
#
# 6. get_settings() e reload_settings()
#    - Funções globais para acesso singleton
#    - Pattern simplificado para casos de uso comuns
#
# ============================================================================
# ESTRUTURA YAML (config.yaml)
# ============================================================================
#
# track_model:
#   backend: "models/yolo/yolo11n-pose.pt"
#   params:
#     conf: 0.05
#     iou: 0.5
#     imgsz: 1280
#     device: "cpu"  # "cpu", "cuda:0", "cuda:1", etc.
#     half: true
#     classes: [0]  # Classe 0 = pessoa
#     tracker: "custom_track.yaml"
#     stream: true
#     show: true
#     persist: false
#     verbose: false
#
# ============================================================================
# VARIÁVEIS DE AMBIENTE (.env)
# ============================================================================
#
# FINDFACE_URL=http://localhost:3185
# FINDFACE_ACCESS_TOKEN=seu-token-aqui
#
# ============================================================================
# USO BÁSICO
# ============================================================================
#
# Padrão Recomendado (Singleton):
# ─────────────────────────────────
#
#   from src.infrastructure import get_settings
#
#   settings = get_settings()  # Carrega uma única vez
#
#   # Acessar configurações type-safe
#   yolo_model_path = settings.track_model.backend
#   confidence_threshold = settings.track_model.params.conf
#   device = settings.track_model.params.device
#   findface_url = settings.findface.url
#
# Conversão para Dict (se necessário):
# ─────────────────────────────────────
#
#   config_dict = settings.to_dict()
#   yolo_config = {
#       'backend': settings.track_model.backend,
#       'params': settings.track_model.params.to_dict()
#   }
#
# ============================================================================
# USO AVANÇADO
# ============================================================================
#
# Carregador Customizado:
# ──────────────────────
#
#   from pathlib import Path
#   from src.infrastructure.config import ConfigLoader
#
#   loader = ConfigLoader(Path('custom_config.yaml'))
#   settings = loader.load()
#
# Recarregar Configurações:
# ─────────────────────────
#
#   from src.infrastructure import reload_settings
#
#   # Recarrega do disco
#   settings = reload_settings()
#
# Força reload em um loader específico:
# ──────────────────────────────────────
#
#   loader = ConfigLoader()
#   settings = loader.load(force_reload=True)
#
# Acesso Type-Safe com Autocompletar:
# ────────────────────────────────────
#
#   settings = get_settings()
#   # IDE oferece autocompletar para:
#   # - settings.track_model
#   # - settings.track_model.backend
#   # - settings.track_model.params
#   # - settings.track_model.params.conf
#   # - settings.findface
#   # - settings.findface.url
#
# ============================================================================
# INTEGRAÇÃO COM run.py
# ============================================================================
#
# A função main() agora usa o novo sistema:
#
#   def main(findface_client: FindfaceMulti) -> None:
#       # Carregar configurações type-safe
#       settings = get_settings()
#
#       # Extrair configuração YOLO
#       yolo_config = {
#           'backend': settings.track_model.backend,
#           'params': settings.track_model.params.to_dict()
#       }
#
#       # ... resto da lógica
#
# ============================================================================
# BENEFÍCIOS
# ============================================================================
#
# 1. Type Safety (Autocompletar)
#    ✓ IDE oferece sugestões para campos válidos
#    ✓ Erros detectados em tempo de desenvolvimento
#    ✓ Refatoração segura
#
# 2. Centralização
#    ✓ Uma única fonte de verdade
#    ✓ Fácil localizar onde valores são usados
#    ✓ Alterar configurações em um lugar
#
# 3. Validação
#    ✓ Arquivo YAML inválido gera erro claro
#    ✓ Configurações obrigatórias validadas
#    ✓ Defaults inteligentes para valores opcionais
#
# 4. Testabilidade
#    ✓ Mockar configurações é trivial
#    ✓ Testes não dependem de arquivo real
#    ✓ Fácil testar múltiplos cenários
#
# 5. Flexibilidade
#    ✓ Suporta YAML + .env
#    ✓ Conversão bididirecional Dict <-> Dataclass
#    ✓ Cache automático (singleton pattern)
#
# ============================================================================
# TESTES
# ============================================================================
#
# Testes do sistema de configuração:
#
#   tests/infrastructure/config/test_config_loader.py
#
#   Classes de teste:
#   - TestYOLOParams (5 testes)
#   - TestTrackModelConfig (3 testes)
#   - TestFindFaceConfig (4 testes)
#   - TestConfigLoader (6 testes)
#   - TestApplicationSettings (3 testes)
#   - TestGlobalFunctions (2 testes)
#
#   Total: 23 testes ✓
#
# Executar:
#
#   pytest tests/infrastructure/config/test_config_loader.py -v
#
# ============================================================================
# ERROS COMUNS E SOLUÇÕES
# ============================================================================
#
# 1. FileNotFoundError: config.yaml não encontrado
#    ✓ Solução: Executar aplicação do diretório raiz do projeto
#    ✓ Ou: Passar Path explícito: ConfigLoader(Path('path/to/config.yaml'))
#
# 2. ValueError: FINDFACE_ACCESS_TOKEN não definido
#    ✓ Solução: Criar arquivo .env com variáveis de ambiente
#    ✓ Ou: Exportar variáveis no shell antes de executar
#
# 3. yaml.YAMLError: Arquivo YAML inválido
#    ✓ Solução: Validar indentação e sintaxe YAML
#    ✓ Usar: https://www.yamllint.com/ para validação
#
# 4. AttributeError: Atributo não existe
#    ✓ Solução: Usar autocompletar da IDE (Ctrl+Space)
#    ✓ Verificar structure em settings.py
#
# ============================================================================
# PRÓXIMOS PASSOS
# ============================================================================
#
# Tópicos para evolução:
#
# [ ] Suporte a múltiplos ambientes (dev, prod, test)
# [ ] Validação de range para valores numéricos
# [ ] Hot-reload de configurações
# [ ] API REST para gerenciar configurações
# [ ] Logging de mudanças de configuração
#
# ============================================================================
