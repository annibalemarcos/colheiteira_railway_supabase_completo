# Concorrência e calibração

## O que foi alterado

- Adicionada a configuração **Concorrência do lote** no painel, com valores de 1 a 3.
- O padrão é **1**, recomendado para Railway e para a primeira rodada de validação.
- Com concorrência 2 ou 3, novos sites continuam sendo iniciados com pausas aleatórias.
- O Lighthouse possui trava exclusiva: nunca existem duas auditorias Chromium simultâneas no mesmo processo.
- Links e imagens tiveram a concorrência interna reduzida e limitada.

## Calibração da nota

Pesos atuais:

| Plugin | Peso |
|---|---:|
| Lighthouse | 2.4 |
| SEO | 1.5 |
| Links | 1.3 |
| Imagens | 1.2 |
| Ortografia | 0.7 |
| Redes sociais | 0.3 |

O relatório agora inclui:

- `coverage`: percentual do peso efetivamente concluído;
- `confidence`: alta, média ou baixa;
- `rankable`: informa se o ranking é comparável;
- `analysis_status`: `complete` ou `partial`.

Abaixo de 80% de cobertura, a nota permanece disponível como provisória, mas o ranking fica **Inconclusivo**. Falha de plugin não vira vantagem matemática para o site.

## Plugins ajustados para Railway

- **Ortografia:** usa `pyspellchecker` em Python puro; não abre servidores Java nem portas locais.
- **Lighthouse:** timeout de 180 segundos, até duas tentativas, perfil Chrome isolado, encerramento da árvore de processos e flags para `/dev/shm` limitado.
- **Links:** bloqueios 401/403/429 e falhas de rede entram como indeterminados, não como links quebrados.
- **Imagens:** pontuação gradual, amostragem limitada e sem dupla penalização do mesmo arquivo.
- **Redes sociais:** analisa Open Graph, Twitter Card, canonical e links presentes na página; não tenta raspar perfis externos.
- **SEO:** penalizações graduais e menos dependência de regras rígidas de tamanho.

## Recomendação de uso

No Railway:

```text
Concorrência: 1
Pausa mínima: 8 s
Pausa máxima: 25 s
```

Depois de confirmar estabilidade, teste concorrência 2. Use 3 apenas em uma instância com memória suficiente.
