# 08 - Nao mascarar toda falha do whitespace check em pushes

Status: resolved
Priority: P3
Type: ci-quality
Blocked by: none

## Achado

`.github/workflows/ci.yml:156-162` executa git diff --check estritamente
em pull requests, mas acrescenta || true no caminho de push.
Consequentemente, falhas de whitespace e erros de Git nesse caminho
nao fazem o step falhar. O check nao garante o mesmo resultado nos eventos.

## Evidencia

```sh
python .devin/scratch/general-audit/reproduce.py ci-mask
```

A fonte contem:

```sh
git diff --check "${{ github.event.before }}..${{ github.sha }}" || true
```

O controle isolado false || true termina com exit0. E verificacao estatica
e da semantica do shell, nao execucao de um workflow remoto ou novo push.
O caminho de PR nao tem esse mascaramento.

## Correcao solicitada

Propagar falhas reais do check. Se o before SHA ausente/zerado exigir
tratamento especial, selecionar uma faixa alternativa explicitamente em
vez de ignorar todas as falhas com || true.

## Aceite

- [ ] Diff com whitespace invalido causa falha em push e PR.
- [ ] Diff limpo retorna sucesso.
- [ ] Primeiro push/before zerado tem comportamento definido e testado.
- [ ] Erro inesperado de Git nao e convertido em sucesso silencioso.
- [ ] Nenhuma politica de protecao de branch e relaxada.

## Comments

Finding de qualidade do CI; nao demonstra falha dos demais gates.
