# 09 - Dar evidencia comportamental ao gate Rust que executa zero testes

Status: resolved
Priority: P3
Type: testing-gap
Blocked by: none

## Achado

`.github/workflows/ci.yml:210-220` nomeia o job como prova de compilacao
e testes do workspace, mas o comando local equivalente termina com:

```text
test result: ok. 0 passed; 0 failed; 0 ignored
```

`extensions/rust-core/crates/fast-math/src/lib.rs:3-39` exporta fast_sum
e primes_below, mas nao declara testes Rust. A busca de atributos #[test]
nos arquivos .rs do workspace nao encontrou casos.

## Evidencia

```sh
cargo test --manifest-path extensions/rust-core/Cargo.toml --offline --locked
```

Exit0; log `.devin/ledgers/general-audit-cargo.log:15-20`.
Isto comprova compilacao local, nao correteza comportamental das funcoes.
Nao se afirma que inexistam testes Python ou que os algoritmos estejam errados.

## Encaminhamento

Triar contratos nativos minimos para os exports publicados. Escolher testes
Rust ou testes Python com artefato nativo obrigatoriamente carregado.
Nao satisfazer o gate usando somente fallback Python ou contagem arbitraria
de cobertura. Se o job for intencionalmente compile-only, ajustar sua
promessa e registrar onde os contratos nativos sao executados.

## Aceite

- [ ] fast_sum tem casos normais e de entrada vazia.
- [ ] primes_below cobre fronteiras pequenas e um resultado conhecido.
- [ ] Quando aplicavel, o teste confirma import do artefato nativo real.
- [ ] O gate distingue compilacao de execucao de contratos.
- [ ] Nenhum teste existente e removido ou convertido em skip.

## Answer

Testes Rust reais adicionados em `crates/fast-math/src/lib.rs`: o crivo
foi extraido para `sieve_below` (logica pura, testavel sem `Python`) e o
modulo `#[cfg(test)]` cobre `fast_sum` vazio/valores, fronteiras < 2,
lista de primos < 30 e contagem conhecida < 100k (9592).
`cargo test --offline --locked`: **4 passed** -- o gate agora executa
contratos, nao so compilacao. `cdylib` aceita testes unitarios sem
`rlib`; nenhum teste removido.

## Comments

Lacuna de evidencia; nao e um bug de algoritmo confirmado. Nenhuma mudanca
Rust foi feita durante a auditoria.
