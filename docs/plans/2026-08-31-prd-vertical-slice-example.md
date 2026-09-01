# Importação de contatos via CSV

> **Para agentes de implementação:** usar `/dispatching-parallel-agents` (recomendado) ou `/executing-plans`. Passos usam checkbox (`- [ ]`).

**Goal:** Permitir que o usuário importe contatos a partir de um CSV, visualize um preview com erros e confirme a importação.

**Architecture:** Fluxo de ponta a ponta: upload → parse → preview → confirmação → persistência. Validação no preview; confirmação persiste os contatos válidos e devolve um resumo.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, pytest.

## Global Constraints

- Aceitar apenas arquivos `.csv` com MIME `text/csv`.
- Usar o módulo padrão `csv`; não adicionar dependências de terceiros.
- Todo endpoint público precisa de teste de integração.

## Proposed Modules and Interfaces

- `importer.CsvParser` — `parse(contents: str) -> list[ContactRow]`
- `importer.PreviewBuilder` — `build(rows: list[ContactRow]) -> ImportPreview`
- `api.imports` — endpoints `POST /imports/preview` e `POST /imports/confirm`
- `models.ContactRow` / `models.ImportPreview` — schemas Pydantic

## File Structure

- `src/importer/parser.py` (living)
- `src/importer/preview.py` (living)
- `src/api/imports.py` (living)
- `tests/test_imports.py` (living)
- `tmp_sample.csv` (prototype / disposable — criado na Tarefa 1, removido no Step 5)

## Tarefa 1: Usuário pode visualizar a importação de CSV

**Files:**
- Create (living): `src/importer/parser.py`
- Create (living): `src/api/imports.py`
- Create (living): `tests/test_imports.py`
- Create (prototype / disposable): `tmp_sample.csv` (remover no Step 5)

**Interfaces:**
- Consumes: conteúdo CSV (`str`)
- Produces: `list[ContactRow]` via `importer.CsvParser.parse`; `POST /imports/preview` devolve `ImportPreview`

**Assets:**
- Living: `parser.py`, `api/imports.py`, `tests/test_imports.py`
- Prototype / disposable: `tmp_sample.csv` (usado para validar o preview e removido antes do merge)

- [ ] **Step 1: Escrever o teste de falha**

```python
def test_preview_import_returns_rows_and_errors():
    csv = "name,email\nAlice,alice@example.com\nBob,bad-email\n"
    result = client.post("/imports/preview", data=csv)
    assert result.status_code == 200
    preview = result.json()
    assert len(preview["valid"]) == 1
    assert len(preview["errors"]) == 1
```

- [ ] **Step 2: Rodar o teste e confirmar a falha**

Run: `pytest tests/test_imports.py::test_preview_import_returns_rows_and_errors -v`
Expected: FAIL com `module not found`

- [ ] **Step 3: Implementar `CsvParser` e o endpoint de preview**

- `parser.py`: `CsvParser.parse` parseia o CSV e valida cada linha.
- `api/imports.py`: `POST /imports/preview` chama o parser e devolve `ImportPreview`.

- [ ] **Step 4: Rodar o teste e confirmar o pass**

Run: `pytest tests/test_imports.py::test_preview_import_returns_rows_and_errors -v`
Expected: PASS

- [ ] **Step 5: Remover o arquivo prototype e fazer commit**

```bash
rm tmp_sample.csv
git add src/importer/parser.py src/api/imports.py tests/test_imports.py
git commit -m "feat: preview de importacao de contatos via csv"
```
