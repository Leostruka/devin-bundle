# Analise: DfNppuykm7W -- Openjutsu (person-swap local via ComfyUI)

## Conteudo

Reel pt-BR divulgando `Openjutsu`: editor de video **local** que
insere a pessoa do usuario em qualquer video sem mandar nada para a
nuvem. Video + foto -> troca a pessoa principal, preservando trilha
sonora e todo o movimento original. Gratuito, roda no PC.

Pela legenda: pipeline construido sobre **ComfyUI + modelos
oficiais** (o material prometido inclui "instalacao com ComfyUI e
modelos oficiais" + regras de imagem/deepfake no Brasil). Reel e
funil de comentario ("YY6WR") -- nao ha demo tecnica alem da
descricao.

## Veredito: mapeado para capacidade existente

- O pipeline descrito (workflow ComfyUI -> gerar -> baixar artefato)
  e exatamente a superficie do `extensions/comfyui-operator/`
  (submit/history/download), endurecido no audit-r5 (loopback-only +
  path sanitization). Nenhum codigo novo e necessario -- o operator
  e agnostico ao workflow.
- Openjutsu em si e um produto externo (wrapper sobre ComfyUI);
  adota-lo seria depender de terceiro fechado -- fora do modelo
  self-hosted/open do bundle.
- Nota de dominio: deepfake/person-swap tem regulacao (legenda cita
  regras BR) -- uso legitimo exige consentimento da pessoa trocada.

## Itens implementados

- Nenhum (notes-only; capacidade ja existente).
