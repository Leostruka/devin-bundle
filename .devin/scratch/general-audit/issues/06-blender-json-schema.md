# 06 - Conter mensagens JSON validas com formato invalido no servidor Blender

Status: resolved
Priority: P2
Type: reliability
Blocked by: none

## Achado

`extensions/blender-operator/blender_server.py:67-68` chama req.get sem
validar que req seja um objeto. O loop :104-111 captura JSONDecodeError,
mas JSON como [] ou null e sintaticamente valido. A excecao de _handle
escapa do loop de atendimento em vez de produzir uma resposta de erro.

## Evidencia

```sh
python .devin/scratch/general-audit/reproduce.py protocol
```

Com bpy substituido por um stub, _handle(json.loads('[]')) gera
AttributeError; ping com objeto valido funciona como controle.
Nenhuma porta e aberta e nenhum codigo via op=exec e executado.
A ausencia de contencao no loop e constatada diretamente na fonte.

## Correcao solicitada

Validar o envelope antes de acessar campos e conter erros por mensagem.
Retornar erro tipado para raiz escalar/lista/null sem derrubar atendimento.
Preservar bind privado, protocolo de identidade e a thread exigida por bpy.

## Aceite

- [ ] [], null, numeros e strings recebem erro JSON previsivel.
- [ ] Uma mensagem invalida nao impede ping valido subsequente.
- [ ] Campos op/id/code invalidos nao escapam como traceback do servidor.
- [ ] A correcao nao executa codigo durante validacao.
- [ ] Gate: `python -m pytest tests/test_camera_blocking.py -q`.

## Answer

`_handle` agora rejeita envelopes nao-dict com erro tipado antes de
`req.get`, e o loop de `serve` protege `resp["id"]`/shutdown com
`isinstance(req, dict)`. Uma linha invalida nao encerra a conexao; `ping`
valido subsequente continua respondendo. Testes em
`tests/test_camera_blocking.py` (`_load_server` stub de bpy): 68 passed;
reprodutor `protocol` nao confirma mais o defeito.

## Comments

Nao se afirma autenticacao por nonce: o protocolo atual e loopback-only,
e os checks do cliente representam identidade/ownership, nao autorizacao.
