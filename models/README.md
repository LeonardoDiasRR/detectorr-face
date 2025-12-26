# Modelos de Detecção

Artefatos de infraestrutura contendo modelos pré-treinados para detecção de faces e corpos.

## YOLO (You Only Look Once)

Modelos de detecção baseados em YOLO para pose estimation e detecção de objetos.

### Arquivos

- **yolo11n-pose.pt** - YOLO11 Nano com pose estimation
  - Tamanho: Reduzido, otimizado para velocidade
  - Uso: Detecção de faces com landmarks em tempo real
  - Entrada: Imagem RGB (640x640)
  - Saída: Bounding boxes + landmarks (17 pontos de corpo)

### Carregamento

```python
from ultralytics import YOLO

# Carregar modelo
model = YOLO('models/yolo/yolo11n-pose.pt')

# Executar inferência
results = model.predict(source='caminho/imagem.jpg')
```

### Referências

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- [YOLO Pose Documentation](https://docs.ultralytics.com/tasks/pose/)
