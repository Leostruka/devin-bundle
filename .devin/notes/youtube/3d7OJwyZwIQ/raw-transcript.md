# Raw transcript: 3d7OJwyZwIQ (whisper.cpp ggml-base, lang=pt)

> Local ASR by `extensions/asr/transcribe.py` on the yt-dlp audio track.
> Segments: 238. sha256(text)=0de92bc06bcca0ea

[0.0s - 5.1s] Existe uma empresa chamada Liquid AI, que lança modelos opensorce um atrás do outro.
[5.1s - 8.0s] E são modelos pequenos que você consegue rodar em qualquer hardware.
[8.0s - 12.2s] E a verdade é que eu queria que tivesse vídeo sobre Liquid AI aqui, quase todo dia.
[12.2s - 14.2s] Que acho tudo que ela faz incrível.
[14.2s - 17.5s] Quer dizer, mais ou menos, eu acho incrível no papel.
[17.5s - 21.7s] Mas toda vez que eu vou experimentar, fica um pouquinho abaixo da minha expectativa.
[21.7s - 25.8s] E eu acabo não trazendo para o canal, mas isso acaba hoje.
[25.8s - 29.7s] Porque hoje a gente tem um modelo que vale a pena falar sobre.
[29.7s - 33.2s] Vamos lá para a tela para eu te falar mais sobre o LFM3.
[33.2s - 36.6s] LFM3 é a nova família de modelos da Liquid AI.
[36.6s - 41.5s] E nesse momento eles lançaram alguns modelos ali com 2 bilhões de parâmetros e com 1.7.
[41.5s - 44.3s] Ou seja, modelos pequenininhos que rodam até no celular.
[44.3s - 46.0s] Só que dessa vez eles se superaram.
[46.0s - 49.7s] E eu estou falando aqui, ó, do LFM3 Omni.
[49.7s - 53.7s] Isso quer dizer que é um modelo que ele aceita não só texto comentada,
[53.7s - 56.1s] mas também áudio, imagem e etc.
[56.1s - 61.6s] Mas o mais legal é que a gente vai ver aqui hoje é que esse modelo não consegue só entender um áudio.
[61.6s - 63.8s] Ele consegue gerar um áudio também.
[63.8s - 66.8s] E isso abre um leque de possibilidades incríveis.
[66.8s - 71.0s] Então aqui a gente vai ter o LFM3.1.7, que é um modelo só de texto.
[71.0s - 75.8s] Vai ter o LFMVL2B, que é um modelo com capacidade de visão.
[75.8s - 81.8s] A gente tem o LFM3 áudio 2B, que é um modelo com capacidade de escutar e falar também.
[81.8s - 83.9s] E na verdade, esse é um modelo que a gente vai ver hoje.
[83.9s - 88.6s] Tem o LFM Omni 2B também e o D1 Omni 2B.
[88.6s - 90.2s] Isso daqui é um modelo de decisão.
[90.2s - 91.4s] Tipo de évita, ligado.
[91.4s - 94.2s] E assim, provavelmente a gente vai ter modelos maiores.
[94.2s - 96.4s] Esses modelos de 2B são só inícios.
[96.4s - 99.4s] Vamos dar uma olhadinha aqui no vídeo de lançamento deles.
[99.4s - 100.2s] Vem lá, não vi.
[113.9s - 135.6s] .
[135.6s - 140.5s] Então essa multimodalidade dele permite esse tipo de coisa, que a gente faz uma pergunta via áudio.
[140.5s - 145.1s] E ele consiga entregar para a gente uma resposta via áudio também ouvia a texto.
[145.1s - 147.8s] Só que essa resposta é baseada no que ele está vendo.
[147.8s - 151.9s] Então a gente entregou para ele uma imagem, um áudio e recebeu a resposta.
[151.9s - 152.8s] Isso é muito legal.
[152.8s - 161.6s] E é claro, ele aceita múltiplas línguas, incluindo português.
[164.3s - 173.9s] Há um modelo com capacidade de chamar todos. Então ele tem um bom do Colin.
[173.9s - 186.4s] Find a flight from Boston San Francisco for this Friday the 30th.
[186.4s - 191.0s] I'm looking for flights from Boston to San Francisco on October 30, 2026.
[191.0s - 195.2s] Let's do the bail-in flight at 825.
[195.2s - 199.1s] I have the bail-in flight at 825 am.
[199.1s - 201.9s] I'd like a window seat that's away from the bathroom, please.
[201.9s - 205.1s] I see you want a window seat away from the bathroom.
[205.1s - 206.1s] Looks good.
[206.1s - 207.1s] Book it.
[207.1s - 209.4s] I'm confirming your booking now.
[209.4s - 211.1s] Aqui eu preciso fazer um disclaimer.
[211.1s - 216.1s] Eu não confiaria no modelo de 2B para a gente para comprar uma passagem para mim.
[216.1s - 223.3s] E eu preciso testar mais, mas até então, o LFM2 mesmos maiores, eu sempre travava ali
[223.3s - 226.7s] quando eu queria usar ele um pouquinho mais complexo.
[226.7s - 230.4s] Mas o que eu estou vendo aqui, que o LFM3 está vendo mais forte.
[230.4s - 234.2s] Tomar aqui as versões maiores dele, realmente consigam fazer isso.
[246.1s - 260.6s] Então, a ideia é que é legal isso, seria, por exemplo, se você está no seu lá ou não óculos.
[260.6s - 261.6s] Imagina?
[261.6s - 262.6s] Cara.
[262.6s - 267.0s] Vou fazer alguma coisa com esse modelo para o Apple Vision.
[267.0s - 271.8s] Vai ficar muito maneiro, a gente vai poder tirar um print assim do que está rolando e falar
[271.8s - 272.8s] com o modelo.
[272.8s - 277.5s] Se você quer um comentário para saber se você quer ver esse vídeo, porque eu quero fazer.
[277.5s - 279.6s] Mas se você tiver alguém para assistir também.
[279.6s - 281.1s] Cara, isso é legal demais.
[281.1s - 282.4s] Isso não óculos, hein?
[282.4s - 282.6s] Legal demais.
[302.8s - 316.4s] A parte mais importante, né?
[316.4s - 317.9s] Open weights!
[317.9s - 321.0s] Cara, tem toda coisa legal, já que eu consegui imaginar isso aqui.
[321.0s - 324.7s] E olha só vários caras já lançam em vários formatos.
[324.7s - 328.5s] Isso aqui é algo que eles fazem muito bem, porque uma das coisas que a liquida faz é apoiar
[328.5s - 329.5s] o open source.
[329.5s - 333.1s] É liberar os pesos e liberar em vários formatos.
[333.1s - 338.1s] A gente pode rodar FPE8, TNV4, MLX ou NNX.
[338.1s - 340.2s] Cara, muito legal, muito, muito, muito legal.
[340.2s - 342.4s] Vamos dar uma olhada na licença rapidamente.
[342.4s - 345.1s] A gente vai usar aqui o 2B, então vamos olhar isso.
[345.1s - 350.0s] Então olha só, essa daqui é uma licença própria deles, é a LFM Open license, tá?
[350.0s - 353.6s] Então, não é a parte dos pontos zero, você não pode usar para qualquer coisa.
[353.6s - 356.4s] Não é a MIT, que são licenças mais abertas.
[356.4s - 361.1s] Então, aqui, olha, quando a gente procura que "commercial use limitation" quer dizer que
[361.1s - 366.9s] você pode usar de forma comercial desde que você não é cedo ao threshold, que é de
[366.9s - 368.5s] 10 milhões de dólares por ano.
[368.5s - 373.6s] Então, seja, dá para usar esse modelo nas nossas aplicações, nos nossos aplicativos.
[373.6s - 376.1s] Mas você deve estar se perguntando, "igual, por que você está tão empolgado?
[376.1s - 377.6s] O que esse modelo consegue fazer?"
[377.6s - 380.0s] Que bom que você pergunta isso, porque a gente vai ver agora.
[380.0s - 383.8s] Primeira coisa, voz, né, "text to speed".
[383.8s - 386.5s] Isso daqui é o modelo que ele consegue falar coisas.
[386.5s - 391.9s] E aqui, a ideia não é uma clonagem de voz, não é você criar uma voz para um conteúdo,
[391.9s - 395.1s] aqui é simplesmente você conseguir ler algo de fato, tá?
[395.1s - 397.1s] E vamos ver se ele faz bem em português.
[397.1s - 401.0s] Vamos lá, vamos colocar a frase simples aqui para a gente ouvir em português, tá?
[401.0s - 405.2s] Voz feminina, vamos gerar a voz aqui, ó, e a geração é relativamente rápida.
[405.2s - 408.6s] Olá, meu nome é Nina, em que posso ajudar?
[408.6s - 412.1s] Mesmo eu não tenho colocado a interrogação e nem entendeu que isso aqui seria uma pergunta
[412.1s - 413.1s] legal.
[413.1s - 414.6s] O que é a voz masculina, tá?
[414.6s - 415.6s] Vamos ouvir agora?
[415.6s - 417.7s] Ah, meu nome é Nina, em que posso ajudar?
[417.7s - 419.7s] Ok, ok, ok, ok.
[419.7s - 424.4s] Vamos colocar idioma em português, mas agora a frase inglês, vamos botar marcos, para
[424.4s - 426.8s] ver se ele vai falar meio que em português, né?
[426.8s - 428.9s] "Hello, my name is Marcos.
[428.9s - 429.9s] How can I help?"
[429.9s - 430.9s] "Marcos."
[430.9s - 432.2s] Acho que o Marcos ficou meio espanhol.
[432.2s - 434.3s] "Hello, my name is Marcos.
[434.3s - 435.3s] How can I help you?"
[435.3s - 436.6s] Mas o resto do inglês ficou bom.
[436.6s - 439.3s] Se a gente mudar aqui pra inglês, a voz é dar um pouco diferente, ó.
[439.3s - 441.3s] "Hello, my name is Marcos.
[441.3s - 442.3s] How can I help you?"
[442.3s - 451.2s] "A gente tem vários idiomas aqui, tá até aqui, ok.
[451.2s - 455.6s] Como eu falei, isso daqui não é um modelo pra você gerar um áudio, pra um conteúdo, etc.
[455.6s - 459.1s] O que a gente quer saber é se ele consegue falar, principalmente, se você consegue falar
[459.1s - 460.1s] rápido.
[460.1s - 461.1s] E nisso ele é muito bom.
[461.1s - 466.9s] Porque uma das paradas é a gente conseguir fazer streaming da voz enquanto ele tá gerando
[466.9s - 467.9s] o texto ainda.
[467.9s - 473.9s] E isso desbloquei o nosso JARVIS, né, ou a nossa JARVIS, já que a voz de stream é uma voz
[473.9s - 474.9s] feminina.
[474.9s - 478.6s] Só que, se eu tentar falar em português com ela, que ela vai me entender, só que ela não
[478.6s - 482.3s] fala português, ela fala inglês, ela vai responder em português só com o sotaque.
[482.3s - 483.5s] "Vamos ver aqui, como é que fica?"
[483.5s - 485.5s] "Hola, aí, como é que tá?"
[485.5s - 487.5s] "Tudo bem?
[487.5s - 488.5s] Como você está?"
[488.5s - 489.9s] "Ah, eu tô muito bem aqui.
[489.9s - 491.8s] Muito melhor agora falando com você."
[491.8s - 496.0s] "Fico muito bem.
[496.0s - 497.0s] Obrigado."
[497.0s - 502.6s] Então ela responde com esse sotaque, né, "Fico muito bem, obrigada, mas se a gente
[502.6s - 508.7s] falar com ela inglês, para isso a gente precisa mudar aqui, para inglês, né, e vamos lá."
[508.7s - 511.1s] Eu posso inclusive, na verdade, falar com ela em português.
[511.1s - 515.5s] É o seguinte, me conta alguma coisa sobre LLMS.
[515.5s - 523.6s] "Sure, LLMs are a type of neural processing unit developed by Nvidia that uses analog technology
[523.6s - 528.4s] to accelerate AI workloads, offering higher efficiency and lower power consumption compared
[528.4s - 529.9s] to traditional digital chips.
[529.9s - 534.7s] They're designed to run machine learning models faster and more energy efficiently, making
[534.7s - 537.8s] them useful for edge devices and data centers alike.
[537.8s - 540.3s] Let me know if you'd like more details.
[540.3s - 545.7s] "Mas só em vídeo consegue usar isso tem outros fabricantes, outras placas que a gente consegue
[545.7s - 546.7s] usar?"
[546.7s - 553.5s] "Não, other manufacturers also produce LM-based accelerators.
[553.5s - 559.3s] Companies such as Intel, Amdol, and Google have their own LM or tensor processing units,
[559.3s - 562.7s] and there are third-party designs that mimic the functionality.
[562.7s - 565.9s] So you can find LM-support from many different chipmakers."
[565.9s - 573.3s] "Cara, muito bom saber disso, né, me fala sobre modelos de geração de áudio.
[573.3s - 578.3s] Qual a diferença deles para LLMS?"
[578.3s - 582.9s] Audio generation models are built to create new sound from text or other inputs, while
[582.9s - 589.1s] LLMS are designed to accelerate existing machine learning tasks like inference and model training.
[589.1s - 594.7s] As a result, audio generators focus on producing high-quality sound synthesis, often using techniques
[594.7s - 600.6s] such as waveform synthesis or neural text-to-sound models, whereas LLMS handle tasks like convolutional
[600.6s - 604.8s] neural networks for image or video processing and large language model inference.
[604.8s - 610.3s] "Ok, I'm going to stop here to stop my hearing, and here we can even transcribe what
[610.3s - 614.3s] we talked about, and even I'm talking about LM portuguese, we can transcribe what we talked about here in
[614.3s - 622.5s] English." "Cara, muito bom saber disso, né, me fala sobre modelos de geração de áudio.
[622.5s - 626.9s] Aqui, a gente está no modo de streaming, tem outros dois modos aqui que a gente vai ver,
[626.9s - 631.6s] mas no modo de streaming, uma coisa que vai ficar clara da diferença desse modo por
[631.6s - 636.2s] os outros, é a latência, é o tempo que leva para ela responder depois que a gente fala com ela."
[636.2s - 641.4s] Então olha só, "Opa! Beleza? É, me fala um pouquinho, eu estou pensando em criar um canal do YouTube,
[641.4s - 648.5s] que dica que você me dá." "First, pick and niche you passionate about, then plan a few video ideas
[648.5s - 653.5s] and set up your channel with a clear brand. Make sure you have reliable equipment and a consistent
[653.5s - 657.9s] upload schedule that keep viewers engaged. Promote it on social media, and interact with
[657.9s - 662.2s] the community to grow your audience." "O que eu quero destacar aqui o tempo que leva
[662.2s - 666.0s] entre eu terminar de falar, ela começa a me responder muito rápido, porque a gente está usando
[666.0s - 672.1s] modelos de streaming, se a gente mudar aqui, ainda funciona, mas fica um pouco diferente."
[672.1s - 678.3s] "Oh, estou querendo criar um canal do YouTube e me fala o que que eu devo fazer."
[678.3s - 683.0s] Olha, está pensando ali agora, tá? E ela só vai começar a falar depois que todo o texto
[683.0s - 689.3s] tivesse ido produzido. "First, sign in to your Google account. Go to the YouTube Studio Dashboard
[689.3s - 694.5s] and start a new channel. Give it a name, choose a custom background, and fill in the channel
[694.5s - 700.2s] subscription. You can also add your first video, set the privacy setting, and then publish it."
[700.2s - 704.8s] "A qualidade do áudio ela mudou um pouco, a voz mudou um pouco, né? Aqui eu consigo escolher
[704.8s - 709.6s] esse, eu quero voz masculina, voz feminina, por exemplo. Mais em termos de estar a teja o que
[709.6s - 716.5s] você pode me falar. Olha, ele vai um tempo ali processando e quando termina ele me fala."
[716.5s - 723.5s] Sure, start by signing into your Google account, then go to YouTube Studio and click Create
[723.5s - 728.7s] a new channel. Follow the prompts to name your channel. Choose a background, write a
[728.7s - 732.2s] description, and add your first video before publishing."
[732.2s - 737.0s] "Ok, por que isso daqui é importante? Esse modo teoricamente é pior, né? Mais primeiro,
[737.0s - 742.0s] ele me permite escolher uma voz feminina ou masculina, mas ele também me permite escolher
[742.0s - 745.3s] a língua de uma forma que a língua, de fato, funciona. Então vamos lá."
[745.3s - 750.7s] "Oh, estou procurando uma placa aqui para rodar um modelo de 10 bilhões de parâmetros. Quantos
[750.7s - 757.6s] de gabar de ser essa placa tem que ter." Essa placa precisaria de círculo de 30 GB de espaço.
[757.6s - 763.1s] "Oh, é que legal, né? Ele me mandou agora em português aqui, e respondeu em português. Desculpe,
[763.1s - 767.7s] eu estava falando com outra pessoa aqui. É o seguinte, tá? Mas eu vou conseguir rodar
[767.7s - 773.1s] sem quantização ou conquantização e falar um pouco sobre isso." Pode rodar sem quantização
[773.1s - 777.9s] ou conquantização e conta um pouco sobre isso. "Ele basicamente repetiu o que eu falei,
[777.9s - 781.9s] né? Mas tudo bem." "E responde o que eu perguntei e não repete que eu falei, porra."
[781.9s - 788.4s] Sem quantização, a quantização não muda nada no resultado. Conquantização, o modelo é convertido
[788.4s - 793.2s] para um formato de baixo resolução, o que pode afetar a precisão dos resultados.
[793.2s - 797.9s] "Ok, se confundir um pouco aqui de onde a gente queria chegar, mas respondeu em português
[797.9s - 802.1s] respondeu bem. A gente pode escolher aqui a voz feminina e também vai conseguir conversar
[802.1s - 807.0s] com a voz feminina. Se eu quiser baixar um modelo para rodar localmente, onde que eu posso
[807.0s - 814.0s] ir?" Você pode procurar moduras em lojas de artesanato, marketplace ornãe ou fábricas locais.
[814.0s - 819.1s] Se precisar, cita como a Etsy ou plataformas de venda local, também tem opções.
[819.1s - 827.5s] "Nara, moldura, era modelos de LLM." Entendi, modelos de len. Você pode procurar eles em lojas
[827.5s - 832.8s] de artesanato, marketplace ornãe. "É, tá, tá um pouquinho confuso. Vamos de novo."
[832.8s - 838.7s] "Eu quiser baixar um modelo de LLM, um large language model, em qual site que eu posso ir?"
[838.7s - 844.8s] Sim, o LLM é um modelo de linguagem de grande escala. "Mas onde posso baixar ele?"
[844.8s - 850.5s] Você pode download o GPT-45 model de OpenAI Website ou de Hugging Face.
[850.5s - 856.1s] O oficial site oferece fretear e sample checkpoints, e o Hugging Face Repositório tem pre-traindo
[856.1s - 884.7s] e o repositor de Hugging Face tem versões predrenadas que você pode rodar localmente.
[884.7s - 889.2s] Esse daqui é um modelo de 2 bilhões de parâmetros, tá? Então ele não tem tanto conhecimento
[889.2s - 894.3s] assim. Algumas coisas que ele vai responder vai estar errado. Só que, aqui, GPT-45 não posso
[894.3s - 898.3s] baixar no Hugging Face. Se a gente desce esse acessor, ele é ferramentos e poderia fazer
[898.3s - 902.7s] essa busca na internet. E a demorar um pouquinho mais para a resposta mais daria para fazer.
[902.7s - 906.4s] O que eu quero mostrar aqui é que dá para a gente usar. Dessa forma, a gente tem um pouquinho
[906.4s - 910.3s] mais de dele do que com streaming, mas a gente desbloqueia as outras línguas. Daria até
[910.3s - 918.9s] para falar aqui, espanhol. Olá, como estás? Olá, como estás? Muy bien.
[918.9s - 931.0s] Perfecto. Em que ter puelo ajudar hoje? Não iria. Eu sei nada, espanhol. Nada, nada. Mas é isso,
[931.0s - 935.2s] tá vendo? Dá para brincar bastante aqui. E como a gente pode ver esse modelo, então vai
[935.2s - 941.6s] poder ser usado como "text to speech". Como "speech to text", ele consegue identificar o que
[941.6s - 944.9s] a gente está falando. Deixa eu ver inclusive o seguinte, ó. E olha, ele está me ouvindo
[944.9s - 949.2s] eu falando em português. E aí, não entendi em inglês, porque eu quero saber se
[949.2s - 953.9s] o translation vai ser em inglês ou em português. Ok? Olha, então aqui é uma outra coisa que
[953.9s - 957.5s] eu vou testar aqui, ele está me ouvindo, estou falando em português, porque eu quero saber
[957.5s - 963.3s] se o translation vai ser em inglês ou em português, ok? Então ele consegue não só
[963.3s - 968.1s] transcrever alguma coisa, mas transcrever em múltiplas línguas, isso é muito legal. Lembrando,
[968.1s - 971.9s] esse é um modelo de 2 bilhões de parâmetros. Se a gente quantizar ele pouquinho ali, dá para
[971.9s - 977.5s] colocar ele dentro de um app tranquilamente. Inclusive eu já tenho vários planos. Eu estou muito empolgado
[977.5s - 982.1s] com essa nova família aqui do LFN. Bem, esse daqui não é um modelo que vai conseguir fazer um
[982.1s - 987.0s] joguinho para você, mas você poderia colocar ele num joguinho, poderia colocar ele num joguinho
[987.0s - 992.6s] que vai reconhecer a voz do usuário, poderia colocar ele num joguinho que vai falar coisas,
[992.6s - 997.7s] dependendo de alguma ação ou de alguma coisa que acontece, né, afinal de contas, é uma LLM também,
[997.7s - 1002.7s] não é só um modelo de textual speech, você consegue gerar um texto e fazer com que ele fale. Então eu
[1002.7s - 1008.0s] quero saber de você, deixa aqui nos comentários três coisas que você faria usando esse modelo. Se você
[1008.0s - 1013.2s] não pensou sobre isso, pensa agora e deixa aqui nos comentários, é um bom exercício para a gente
[1013.2s - 1019.9s] brincar com modelos diferentes. Eu vejo que muita gente só sabe usar chat, pt, opus e etc. Então fica aqui
[1019.9s - 1024.5s] a dica para você ficar de olho em outros modelos também, porque eles têm capacidades completamente
[1024.5s - 1031.1s] parentes e eles cabem devaises completamente diferentes em situações completamente diferentes. Agora,
[1031.1s - 1035.5s] se você quiser ver um modelo de textual speech, que esse sim, esse gera áudio que dá para usar
[1035.5s - 1041.2s] em conteúdo, mas ele é mais pesado também. Vai ser dar uma olhada aqui ó, drama 3, bravo, bravo, bravo,
[1041.2s - 1046.4s] se você quiser ver um app que a gente gerou em imagens, os áudios, tudo cunhar dá uma olhada nesse
[1046.4s - 1051.6s] vídeo aqui. Tirei muito ter usado drama 3, mas ele não estava disponível quando a gente estava
[1051.6s - 1055.1s] desenvolver. Se você quiser aprender sobre como desenvolver com inteligência artificial, aí
[1055.1s - 1061.6s] 60 dedos nesse link aqui ó, e a para devs, um curso feita exatamente para vocês trair mais
[1061.6s - 1065.7s] de modelos mais baratos. Então clica lá a ver se é para você se inscreve e te veja lá
[1065.7s - 1069.6s] deles. E se tiver algum modelo que você queira, deixa aqui embaixo de comentários, vou ficando
[1069.6s - 1070.8s] por aqui até o próximo vídeo. Valeu.
