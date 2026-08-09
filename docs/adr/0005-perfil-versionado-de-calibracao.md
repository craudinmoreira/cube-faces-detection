# ADR 0005: persistir um perfil de calibração versionado

## Status

Aceita.

## Contexto

Guardar somente o centro LAB impede avaliar se uma cor foi observada de forma
consistente. O antigo `calibration.json` também não identifica o seu formato,
o que torna futuras extensões frágeis.

## Decisão

Novas calibrações usam `schema_version: 2`. Cada cor registra centro LAB,
desvio-padrão por canal, percentis 50/90/95 das distâncias, quantidade e duração
das amostras. O arquivo também registra data UTC e índice da câmera.

A classificação atual continua usando a distância LAB já existente. Arquivos
legados, compostos diretamente por centros LAB, são carregados com um aviso de
recalibração. Arquivos inválidos mostram aviso explícito e usam os centros
padrão.

## Consequências

- Há dados objetivos para comparar ΔE00, Mahalanobis e limiares adaptativos.
- A troca do formato não interrompe usuários que já calibraram o programa.
- Erros de JSON ou schema deixam de ser silenciosos.
