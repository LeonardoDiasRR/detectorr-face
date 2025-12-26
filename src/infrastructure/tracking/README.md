"""
Módulo de Gerenciamento de Tracks

Documentação do sistema de registamento de tracks para gerenciamento
de objetos rastreados em tempo real.
"""

# TrackRegistry - Gerenciamento de Tracks em Tempo Real

## 📋 Visão Geral

O `TrackRegistry` é um sistema de gerenciamento de tracks (objetos rastreados) para
aplicações de visão computacional em tempo real. Ele mantém informações sobre os
objetos detectados e rastreados pelo modelo YOLO durante o processamento de streaming
de vídeo.

### Padrão de Design

Implementa a **Arquitetura Hexagonal (Portas e Adaptadores)**:

```
┌─────────────────────────────────────────────────┐
│        Application Layer (Portas)               │
│   - TrackRegistry (interface/contrato)          │
└─────────────────────────────────────────────────┘
              ↓                ↑
┌─────────────────────────────────────────────────┐
│      Infrastructure Layer (Adaptadores)         │
│   - InMemoryTrackRegistry                       │
│   - (Futura: DatabaseTrackRegistry, etc)       │
└─────────────────────────────────────────────────┘
```

## 🏗️ Estrutura

### Interface: `TrackRegistry`

**Localização:** `src/application/tracking/track_registry.py`

Define o contrato que todo adaptador de storage deve implementar:

```python
class TrackRegistry(ABC):
    @abstractmethod
    def register(self, camera_id: str, track_id: int, track: Any) -> None:
        """Registra ou atualiza um track"""
        pass
    
    @abstractmethod
    def get(self, camera_id: str, track_id: int) -> Optional[Any]:
        """Recupera um track específico"""
        pass
    
    @abstractmethod
    def get_by_camera(self, camera_id: str) -> Iterable[Any]:
        """Recupera todos os tracks de uma câmera"""
        pass
    
    @abstractmethod
    def remove(self, camera_id: str, track_id: int) -> None:
        """Remove um track"""
        pass
    
    @abstractmethod
    def clear_camera(self, camera_id: str) -> None:
        """Remove todos os tracks de uma câmera"""
        pass
```

### Implementação: `InMemoryTrackRegistry`

**Localização:** `src/infrastructure/tracking/in_memory_track_registry.py`

Implementação eficiente usando memória para acesso ultra-rápido:

```python
class InMemoryTrackRegistry(TrackRegistry):
    """
    Armazenamento em memória com estrutura:
    _tracks = {
        "camera_001": {
            1: track_object,
            2: track_object,
            ...
        },
        "camera_002": { ... }
    }
    """
```

#### Características:
- ✅ Complexidade O(1) para operações básicas
- ✅ Ideal para processamento em tempo real
- ✅ Thread-safe para operações individuais
- ✅ Organizado por câmera para queries rápidas
- ✅ Métodos auxiliares para monitoramento

## 📊 Uso

### Exemplo Básico

```python
from src.infrastructure.tracking.in_memory_track_registry import InMemoryTrackRegistry

# 1. Instanciar
registry = InMemoryTrackRegistry()

# 2. Registrar track
registry.register("cam_001", 1, {"center": (100, 100), "conf": 0.95})

# 3. Recuperar track
track = registry.get("cam_001", 1)

# 4. Listar tracks de câmera
all_tracks = list(registry.get_by_camera("cam_001"))

# 5. Remover track
registry.remove("cam_001", 1)

# 6. Limpar câmera
registry.clear_camera("cam_001")
```

### Integração com Use Case

```python
class ProcessCameraStreamingUseCase:
    def __init__(self, track_registry: TrackRegistry):
        self.track_registry = track_registry
    
    def process_frame(self, camera_id: str, yolo_results):
        # Atualizar tracks no registry
        for detection in yolo_results.boxes:
            track_id = int(detection.id)
            track_data = {
                "bbox": detection.xyxy,
                "confidence": detection.conf,
            }
            self.track_registry.register(camera_id, track_id, track_data)
    
    def on_camera_disconnect(self, camera_id: str):
        # Limpar tracks quando câmera desconecta
        self.track_registry.clear_camera(camera_id)
```

## 🧪 Testes

### Localização
- `tests/infrastructure/tracking/test_in_memory_track_registry.py` - 22 testes
- `tests/infrastructure/tracking/test_track_registry_interface.py` - 6 testes

### Cobertura

```
✅ Operações básicas (register, get, remove)
✅ Operações por câmera (get_by_camera, clear_camera)
✅ Múltiplos tracks e câmeras
✅ Casos extremos (vazio, inexistente)
✅ Validação de inputs
✅ Métodos auxiliares
✅ Independência de instâncias
```

### Executar Testes

```bash
# Testes específicos
pytest tests/infrastructure/tracking/ -v

# Com cobertura
pytest tests/infrastructure/tracking/ --cov=src/infrastructure/tracking

# Exemplo rápido
pytest tests/infrastructure/tracking/test_in_memory_track_registry.py::TestInMemoryTrackRegistry::test_register_and_get_single_track -v
```

## 📈 Métodos Auxiliares

### `get_camera_tracks_count(camera_id: str) -> int`

Retorna número de tracks ativos de uma câmera.

```python
count = registry.get_camera_tracks_count("cam_001")
print(f"Tracks ativos: {count}")
```

### `get_all_cameras_stats() -> dict`

Retorna estatísticas de todos os tracks.

```python
stats = registry.get_all_cameras_stats()
# Output: {'cam_001': 5, 'cam_002': 3, 'cam_003': 0}
```

## 🚀 Próximos Passos

### Possíveis Extensões

1. **DatabaseTrackRegistry**
   - Persistência em banco de dados
   - Histórico de tracks
   - Queries complexas

2. **RedisTrackRegistry**
   - Distribuído
   - Cache com TTL
   - Multi-instance support

3. **Monitoramento**
   - Métricas de tracks por câmera
   - Alertas de anomalias
   - Dashboard de rastreamento

## ⚙️ Considerações de Design

### Thread Safety
- Operações individuais são thread-safe
- Para operações complexas (múltiplas chamadas), usar lock externo

```python
with lock:
    registry.register(cam_id, track_id, data)
    other_operation()
```

### Limpeza de Memória
- Implementação atual cresce indefinidamente
- Recomenda-se implementar TTL ou limpeza periódica

```python
# Futura: Auto-limpeza
registry.register(camera_id, track_id, track_data, ttl=30)  # 30 segundos
```

### Performance
- **Get/Register/Remove:** O(1)
- **Get by Camera:** O(n) onde n = tracks na câmera
- **Clear Camera:** O(1)

## 📝 Exemplos Completos

Veja `src/infrastructure/tracking/examples.py` para exemplos práticos de:
- Uso básico
- Múltiplas câmeras
- Integração com Use Case

## 🔍 Validações

O registro valida:
- ✅ `camera_id` não vazio/None
- ✅ `track_id` é inteiro
- ✅ Operações com dados inexistentes (não lançam erro)

## 📚 Referências

- **Padrão Hexagonal:** https://alistair.cockburn.us/hexagonal-architecture/
- **YOLO Tracking:** https://docs.ultralytics.com/modes/track/
- **Python ABC:** https://docs.python.org/3/library/abc.html
