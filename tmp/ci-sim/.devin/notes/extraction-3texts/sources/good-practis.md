# tactiq.io free youtube transcript
# Práticas do Akita com IA. Deu bom? (Boas Práticas de IA)
# https://www.youtube.com/watch/ytTJtfg9HCw

00:00:00.000 Eu vou separar esse vídeo meio que em
00:00:01.760 duas partes, porque ficaria um vídeo
00:00:03.280 muito longo. Então essa que você tá
00:00:04.839 assistindo agora é a primeira parte em
00:00:06.279 que eu vou explicar os bons conceitos e
00:00:07.839 as boas práticas para se usar IA durante
00:00:10.800 o desenvolvimento de software. Nesse
00:00:12.679 vídeo eu vou te entregar o que fazer, o
00:00:14.879 que não fazer e dicas de produtividade e
00:00:17.760 assertividade. Você vai ser um vídeo que
00:00:19.240 eu imagino que vá durar uns 25 minutos,
00:00:21.640 talvez. E um pouco depois eu vou lançar
00:00:23.800 um vídeo em que eu vou fazer isso daqui
00:00:25.519 na prática, que vai ser um vídeo um
00:00:26.960 pouco mais longo, um pouco menos
00:00:28.119 conciso. Então eu prefiro explicar isso
00:00:29.880 agora, passar cada um por cada um desses
00:00:32.000 conceitos para você entender eles bem,
00:00:34.040 para você praticar por conta própria,
00:00:36.160 para depois a gente trabalhar um pouco
00:00:37.600 isso daqui, né, mostrando num projeto
00:00:39.760 real. Antes disso, vou te falar do
00:00:40.879 patrocínio de hoje, que é a Abacus AI.
00:00:42.680 Abacus é simplesmente um ferramental
00:00:45.000 completo de IA. Que que isso quer dizer?
00:00:47.160 Quer dizer que eles têm um chat com
00:00:48.800 todos os modelos aqui de A. Você pode
00:00:50.559 usar o Nano Banana 2, o Nano Banana Pro,
00:00:53.120 você pode usar o GPT 4.5, GPT5 e, enfim,
00:00:56.480 você pode usar esses diversos modelos
00:00:58.960 para, por exemplo, gerar imagens, para,
00:01:00.760 por exemplo, gerar vídeo, para, por
00:01:02.120 exemplo, gerar falas, né, áudio, para
00:01:03.879 executar tarefa, você pode utilizar na
00:01:05.438 criação de apps. Não apenas isso, Abacus
00:01:08.159 tem aqui do ladinho, ó, a Agent
00:01:10.040 Sessions. O Agent da Abacus é um agente
00:01:12.560 que por conta própria faz muita coisa.
00:01:14.960 Ele consegue criar aplicações inteiras
00:01:17.119 do zero, ele consegue fazer MVPs do
00:01:18.759 zero. Você tem vários exemplos aqui no
00:01:20.560 próprio site da Abacus com os prompts
00:01:22.920 inclusive que você pode copiar esse
00:01:24.880 prompt aqui, colar no agent e obter um
00:01:27.159 resultado similar, né? Então ele faz
00:01:29.799 sites aqui, fez aqui um aplicativo
00:01:31.520 também de finanças pessoais, tá? Abucos
00:01:33.880 tem também uma versão deles do OpenCAW
00:01:36.799 que você pode fazer o deploy do Opencla
00:01:38.680 muito rapidamente e utilizar. Ela tem
00:01:40.399 também uma IDE que tem um agente de
00:01:42.920 código integrado ali que você pode
00:01:44.759 promptar o agente, ele vai
00:01:45.799 automaticamente fazer alterações no
00:01:47.240 código. Enfim, é um ferramental muito
00:01:49.600 completo. Por 10 por mês não existe,
00:01:52.200 acredito que nada comparável a isso, tá?
00:01:54.560 Porque se você pagar outra e a
00:01:56.479 separadamente, ela não vai ter todo esse
00:01:58.280 ferramental. De repente você paga uma
00:01:59.920 para ter acesso ao chat, outra para
00:02:01.399 fazer aplicativos, outra para outra
00:02:02.719 coisa. Aqui na aba custa tudo completo
00:02:04.520 por apenas $10 por mês e o link vai est
00:02:06.520 aqui na descrição, tá? Vale bastante a
00:02:07.920 pena. Bom, antes da gente começar aqui,
00:02:09.399 da onde que eu tirei isso? Primeiro,
00:02:10.639 vamos ser sincero aqui, né? Primeira
00:02:12.640 fonte é vozes da minha cabeça. Minha
00:02:14.040 cabeça como alguém que trabalha com
00:02:15.440 tecnologia mais ou menos 8 a 10 horas
00:02:18.319 por dia todos os dias, mais ou menos de
00:02:20.400 segunda a sábado. Eu tô nesse mercado,
00:02:21.800 tô na área de software há 12 anos já,
00:02:24.319 profissionalmente há 10 anos. Eu sou
00:02:26.000 City numa empresa dos Estados Unidos
00:02:27.319 agora. E desde dezembro eu tenho usado
00:02:28.959 IA bastante intensivamente durante o
00:02:31.000 processo de produção de código, porque
00:02:32.519 eu acredito que acelera o meu
00:02:33.640 desenvolvimento, tá bom? Além de vozes
00:02:35.959 da minha cabeça, que é uma fonte
00:02:37.560 muitíssimo importante, a gente tem
00:02:39.200 outras fontes também. Eu li todos os
00:02:41.800 artigos do Akita sobre a. Então, a gente
00:02:44.519 tem também o Akita aqui como uma fonte.
00:02:46.680 Eu conversei bastante com esse carinha
00:02:48.080 aqui, que é o SAM, o SAM da aula
00:02:49.480 inclusive de soft, se você quiser. O
00:02:52.200 perfil dele vai est aqui na descrição,
00:02:53.360 tá? Eu recomendo demais. O S é um cara
00:02:55.000 que manja muito e me ensinou muita coisa
00:02:57.080 também. E existem diversas outras fontes
00:02:58.879 que eu fui acompanhando ao longo do
00:03:00.080 tempo, né? artigos, vídeos,
00:03:01.480 especialistas em a, etc, etc, pra compor
00:03:04.519 aqui um conhecimento bastante útil. Bom,
00:03:06.720 vamos lá. A questão para mim aqui é a
00:03:08.400 seguinte. Primeira coisa que a gente vai
00:03:09.720 precisar falar, e isso daqui eu tô
00:03:11.040 puxando diretamente de um dos artigos do
00:03:12.680 Akita, tá? É o tal do mito do One Shot
00:03:14.879 Prom. O que que é esse mito? Criou-se no
00:03:16.680 imaginário das pessoas a ideia de que se
00:03:19.560 a gente fizer um monte de maluquí,
00:03:23.640 engenharia e skills e plugins, etc, etc,
00:03:27.040 a gente vai conseguir ter uma IA que
00:03:28.519 resolve tudo em one shot, basicamente em
00:03:31.760 um prompt. E para tarefas muito simples,
00:03:33.560 isso até é verdade, não é um mito, é uma
00:03:35.200 realidade, tá? Eu consigo efetivamente
00:03:38.959 para tarefas muito simples, quase que
00:03:40.640 90% das vezes resolver elas com um único
00:03:42.959 prompt e o código vai est adequado,
00:03:45.360 talvez de uma revisada e tal, mas enfim.
00:03:46.879 A ideia é você entender que isso é um
00:03:48.599 mito e não necessariamente perseguir
00:03:50.599 isso daqui como objetivo. Esse One Shot
00:03:52.599 Prompt até vai nos linkar com uma das
00:03:55.079 skills mais populares de todos os tempos
00:03:58.239 para agentes de A que surgiu com uma
00:03:59.879 popularidade gigantesca agora que é o
00:04:01.799 seguinte, você tem esse repositório aqui
00:04:03.079 do Match Podc que tem 93.000 1000
00:04:05.640 estrelas no GitHub. Claro, não quer
00:04:07.599 dizer muita coisa, mas meio que quer
00:04:08.959 também, né? É muita coisa. E uma das
00:04:10.439 skills mais populares é essa skill de
00:04:12.560 Grillomy. Que que é a skill de Gommy
00:04:14.040 aqui, né? Vamos traduzir aqui para ficar
00:04:15.480 no no bom português, para facilitar a
00:04:17.040 leitura. Entreviste-me incansavelmente
00:04:19.040 sobre cada aspecto desse plano até
00:04:20.600 chegarmos a um entendimento mútuo. E aí
00:04:22.440 continua um pouquinho, né? É essa a
00:04:23.800 ideia. Ao invés de a gente tentar algo
00:04:26.240 com one shot, a gente vai substituir
00:04:28.360 isso por um modelo mais parecido com o
00:04:30.680 tal do Groomy, que nada mais é que ao
00:04:32.720 invés de você tentar o prompute
00:04:34.400 perfeito, aí às vezes não vai se
00:04:36.199 compreender, às vezes você não vai fazer
00:04:37.759 ser entendido, você conversa quase como
00:04:39.600 se fosse outra pessoa e vocês chegam no
00:04:41.400 entendimento. É muito interessante um
00:04:43.199 detalhe aqui que eu acabei percebendo ao
00:04:44.840 longo do tempo que as e as se importam
00:04:47.000 com intenção, principalmente os modelos
00:04:48.880 mais novos com o thinking ali mais
00:04:50.560 avançado, né? Se você botar o heavy
00:04:52.759 thinking, o pensamento mais pesado, é
00:04:54.600 interessante você elucidar qual o
00:04:56.440 objetivo final daquilo, porque às vezes
00:04:59.000 uma descrição de implementação pode
00:05:01.000 levar para um caminho errôneo para ir.
00:05:02.639 Então, se você deixar claro qual que é a
00:05:03.960 intenção, aonde que aquela feature vai,
00:05:05.800 como que ela vai afetar o usuário, isso
00:05:07.639 costuma
00:05:09.240 diminuir um pouquinho a quantidade de
00:05:11.800 coisas que vai para um caminho
00:05:13.440 totalmente sem noção. E aqui eu quero
00:05:15.759 pegar esses conceitos aqui e trabalhar
00:05:17.560 isso num fluxograma, porque a maneira
00:05:19.800 com que a gente tá imaginando, quer
00:05:21.520 dizer, com que muitas pessoas estão
00:05:23.160 imaginando e trabalhando com IAS, é a
00:05:24.759 seguinte: existe aqui uma ISO ou então
00:05:29.160 uma tesc. Eu vou pegar essa eixo ou essa
00:05:31.600 tesca, eu vou jogar aqui pro meu, vamos
00:05:33.880 falar em português alto e claro, né?
00:05:35.960 Cloud Code ou Codex, que é o que tá todo
00:05:37.759 mundo usando. Cloud Code ou Codex vão
00:05:39.479 cuspir um código e eu aqui vou revisar
00:05:42.400 esse código. Ou então eu e o Code Rabbit
00:05:45.280 vamos revisar esse código. Code Rabbit é
00:05:47.120 uma extensão muito popular que acopla
00:05:48.960 ali no GitHub e revisa seus códigos.
00:05:51.440 Ambos vamos revisar esse código, voltar
00:05:53.479 com feedback pro cloud até que isso
00:05:55.199 daqui tá pronto para ser emergeado. Isso
00:05:57.039 daqui tá perfeitamente OK. Não tem nada
00:05:59.319 de errado nesse fluxo aqui, mas na minha
00:06:01.639 opinião tem como a gente mudar um
00:06:04.000 pouquinho esse loop, utilizar tanto o GM
00:06:06.639 quanto uma conversa inteligente com a
00:06:08.400 pegar essa tesca aqui e adicionar um
00:06:11.039 pouquinho de coisa aqui, não muito, que
00:06:13.199 vai ser o seguinte, a gente vai pegar
00:06:14.840 essa tesca, eu, ao invés de só revisar o
00:06:16.599 código, eu e meu amigo Cloud Code Codex
00:06:19.840 vamos conversar com o objetivo de criar
00:06:22.599 um PRD. E a gente pode utilizar a skill
00:06:25.000 do Grommy aqui no mesmo repositório do
00:06:27.160 match lá tem uma skill de PRD ou você
00:06:28.960 pode catar uma skill de PRD onde você
00:06:31.400 quiser. E quando a gente chegar na
00:06:32.759 conclusão de que esse PRD é tá legal, é
00:06:34.800 o que de fato vai ser implementado, aí a
00:06:37.039 gente vai jogar esse PRD, né, para que
00:06:38.800 ele seja feito aqui para fazer o código
00:06:40.759 de fato. Agora, um detalhe importante é
00:06:42.160 que tem um um uma questão fina aqui que
00:06:44.880 é o seguinte. Isso aqui eu puxei do San,
00:06:46.360 aquele cara que eu falei, que eu mostrei
00:06:47.599 o Twitter ali, né? que eu recomendei se
00:06:48.800 conversar com ele, que ele que é um cara
00:06:50.440 muito competente, eu também. Acabamos
00:06:52.960 observando que pequenos costumam ser
00:06:55.479 melhores. Quer dizer, na o bem dizer
00:06:58.199 aqui da engenharia de software sempre
00:06:59.720 soube disso, perr pequenos costumam ser
00:07:01.400 menores. Até fiz uma palestra sobre isso
00:07:03.120 em Florianópolis. A questão então é que
00:07:05.440 essa issue e tesque aqui, né, você
00:07:08.000 precisa ter um certo tato para saber que
00:07:10.160 isso vai se traduzir num PR de mais ou
00:07:12.479 menos 300 ali linhas. E isso aqui pode
00:07:16.680 estar dentro. Aqui a nomenclatura vai
00:07:18.319 variar muito de empresa para empresa,
00:07:19.840 tá? Vocês podem chamar do que vocês
00:07:21.479 quiserem. Isso daqui pode ser uma Epic,
00:07:23.039 isso aqui pode ser uma Milestone, isso
00:07:24.960 aqui pode ser uma story, sei lá o quê.
00:07:26.599 Sinceramente, eu não dou a mínima para
00:07:28.560 esses nomes. Acho que é tudo uma
00:07:30.120 invenção aí meio doida, mas o fato é uma
00:07:32.840 tarefa muito grande que vai levar mais
00:07:34.479 do que, sei lá, 500 linhas de código
00:07:36.199 para ser resolvida, ela precisa ser
00:07:38.680 quebrada em subtarefas, né? Ela precisa
00:07:40.680 ser feito de uma maneira concisa. E essa
00:07:43.720 épic aqui ou milestone ou store ou que
00:07:45.639 quer que seja inteiro, vai ter que ter
00:07:47.479 um processo de quebrar isso em tesques
00:07:49.440 pequenas que tem tem limites claros, né?
00:07:52.639 Se a gente não tiver clareza em onde que
00:07:55.560 acaba uma tesca, onde que começa a
00:07:56.840 outra, vai acabar tendo muito
00:07:57.919 retrabalho. Então isso aqui é um
00:08:00.520 detalheo que é para você ser específico
00:08:03.000 nas boundaries aqui, né? Que a gente
00:08:04.440 chama de fronteiras.
00:08:06.520 Se for uma API, qual que é o input
00:08:09.159 output dessa API? Qual que é o input,
00:08:11.000 output desse serviço? Quais, né, o que
00:08:13.080 que a gente vai trabalhar aqui, quem que
00:08:14.639 faz as migrações do banco de dados e
00:08:16.080 tal, né? Qual tarefa para cada coisa?
00:08:17.520 Então eu tomo um cuidado adicional nessa
00:08:19.240 criação de tarefas aqui, tá? Que é muito
00:08:21.159 importante. Isso costuma ajudar na minha
00:08:23.440 assertividade, que se eu mandar uma
00:08:24.759 tarefa gigantesca pro cloud Code, pro
00:08:26.400 Codex fazer, eu não vou falar que eles
00:08:27.560 não conseguem, eles até conseguem, mas
00:08:30.599 ela não sai do jeito que eu quero. Ela
00:08:32.399 não sai do jeito que maior agrega valor
00:08:33.880 pro cliente. Ela não sai do jeito,
00:08:35.799 digamos assim, correto. Muito bem. Você
00:08:37.719 vai ter então o seu resultado final
00:08:39.440 aqui, que são tickets super bem
00:08:41.719 definidos com a intenção, né, com o o no
00:08:46.600 ticket é interessante que você inclua o
00:08:49.360 por que esse ticket tá sendo feito. E
00:08:51.080 como eu falei, uma tarefa pequena com
00:08:53.080 pouco contexto pode ser mal interpretada
00:08:54.959 pela IA eisso vai aumentar o seu
00:08:57.160 trabalho aqui na hora de revisar e
00:08:59.120 repromptar o cloud depois. Existe também
00:09:01.000 agora questões durante o trabalho do
00:09:04.640 próprio cloud, durante o trabalho do
00:09:06.560 próprio Codex, que é o seguinte: ah, TDD
00:09:08.519 é bom, é, os devs não faziam TDD porque
00:09:10.399 eles não queriam, mas agora o Cloud pode
00:09:11.800 fazer por você TDD e não vai te custar
00:09:13.839 muito a mais, vai custar um pouquinho de
00:09:15.360 token a mais, mas, pô, convenhamos. Você
00:09:17.320 pode então criar um ferramental de TDD
00:09:19.640 ali que nada não vai nada além de um
00:09:23.160 script, né? um alguma forma para ir,
00:09:26.279 algum handler para ir a rodar esses
00:09:28.279 testes e incluir isso daqui no agents
00:09:31.839 pmmd ou então cloud. MD. Que que é o
00:09:34.920 cloud.m agents.md. Lá no root do seu
00:09:37.680 projeto, né? No seu projeto você vai ter
00:09:39.360 lá o barra source, você vai ter o seu
00:09:41.519 ponen env, você vai ter também um
00:09:43.560 agents.m. Agents.md é um arquivo em MD,
00:09:47.000 em Markdown, que vai incluir um pré
00:09:50.040 prompt. Isso vai ser incluído em todos
00:09:52.200 os prompts que você fizer pro seu cloud
00:09:53.920 code ou codex. Quer ver um exemplo de um
00:09:55.600 MD? Eu vou pegar um aqui que eu esbarrei
00:09:57.560 nesse MD no Twitter aqui faz um tempinho
00:10:00.279 e eu achei razoável, tá? Isso daqui, ó,
00:10:03.000 só para você olhar, ele tá em inglês,
00:10:04.640 então eu vou clicar aqui para traduzir
00:10:05.880 para português, tá? Mas geralmente eu
00:10:07.079 trabalho em inglês com os agents.
00:10:08.839 Traduzindo para português, você tem
00:10:10.760 aqui, né, o arquivo é cloud.md e ele dá
00:10:12.640 aqui várias regras. Por que que não
00:10:13.920 traduziu esse MD? Bom, tá, vamos
00:10:15.160 traduzir ao vivo. É, regra número um,
00:10:17.200 pense antes de codar. E tá escrito aqui,
00:10:19.240 né? Declare suas presunções
00:10:21.200 explicitamente. Estiver incerto,
00:10:23.440 pergunte ao invés de adivinhar.
00:10:25.000 Simplicidade. Primeiro, o menor código
00:10:27.040 possível que resolve problema. Mudanças
00:10:29.399 cirúrgicas e go driven execution, né? E
00:10:32.959 execução baseada em objetivos, testes
00:10:35.519 que verificam intenção e não apenas
00:10:37.480 comportamento, etc, etc. Tá? Você vai
00:10:39.519 criar ao longo do tempo um ponto MD
00:10:41.680 desses que vai seguindo as regras que
00:10:43.040 você gosta. Esse aqui é um exemplo
00:10:44.800 perfeitamente razoável para começar.
00:10:46.200 Para cada projeto, você vai querer ter
00:10:47.920 algumas guidelines também. Por exemplo,
00:10:49.680 num meu ags.md que eu trabalho com
00:10:51.880 Typescript, eu explicitamente mando a IA
00:10:54.560 nunca usar N, nunca usar N. Eu
00:10:57.480 explicitamente mando i a rodar os
00:10:59.079 linters, né? Rodar os linters após
00:11:00.760 terminar a tarefa. E assim por diante.
00:11:02.079 Você vai criando regrinhas, vai
00:11:02.959 adicionando ali no ages.m, tá? Isso tudo
00:11:04.880 para falar que TDD é uma das opções de
00:11:07.200 regrinhas que você pode adicionar. Aí
00:11:08.480 outra regrinha muito legal é a gente
00:11:10.240 trabalhar com APIs detalhadas. Qual que
00:11:12.639 é a questão aqui? O desenvolvimento web,
00:11:14.360 sejamos sinceros aqui, é o
00:11:15.560 desenvolvimento de Crude. Crude é o
00:11:17.399 desenvolvimento de uma API e um backend.
00:11:18.920 Se a sua API tá super bem detalhada em
00:11:21.279 qual que é o input, qual que é o output
00:11:23.560 e o que que vai acontecer, a SUIA
00:11:25.160 consegue ler isso daqui e trabalhar em
00:11:27.320 cima disso. Então o detalhamento de uma
00:11:28.680 API ele é muito bom, né? você cria uma
00:11:30.399 uma tesque ali para explicar como é que
00:11:32.040 a PI funciona. Isso daqui pode se
00:11:34.279 traduzir também para uma open API spec
00:11:37.000 ou algo nesse sentido. Tem feito
00:11:39.399 bastante sentido na época da EA você
00:11:41.079 focar nesse tipo de documentação, porque
00:11:42.920 primeiro dá muito menos trabalho.
00:11:44.639 Segundo que isso daqui é um contexto
00:11:47.279 muito bom para EA. Joga esse Open API
00:11:50.360 Speck como contexto pra própria EA que
00:11:52.880 ela vai novamente tender a se perder
00:11:54.720 menos para criar, né? Se você cria a
00:11:56.880 especificação da API de como é pra API
00:11:58.920 ser feita e aí manda aí a fazer o
00:12:01.320 trabalho de criar essa API, como ela já
00:12:03.680 tem especificação, melhora um pouco.
00:12:05.200 Esse acaba sendo o fluxo geral. As
00:12:06.720 tarefas e as tarefas, as ferramentas
00:12:08.480 mais importantes que eu uso. Hoje em dia
00:12:09.959 tem sido o Codex porque ele é mais
00:12:12.000 barato, tá? O Cloud Code eu estouro 200
00:12:14.959 muito rápido, enquanto o Codex eu não
00:12:17.839 estouro o de $2. Então isso aqui é muito
00:12:20.199 bom, tá? Eu não tô aim pagar 200 já é R$
00:12:23.240 1.000, né? Eu já pago R$ 1.000 já. Eu
00:12:24.880 não tô muito a fim de pagar mais do que
00:12:26.079 isso. E o Code Rabbit pra revisão de
00:12:27.880 código. Eu acho que essa interação aqui
00:12:29.720 de código e Code Rabbit é muito boa. E
00:12:31.880 aqui existem alguns pequenos detalhes
00:12:34.079 que podem acelerar o nosso processo que
00:12:35.920 a gente vai ver no próximo vídeo na
00:12:37.519 prática, que é o seguinte, pequeno
00:12:39.279 detalhe é você ter uma skillzinha que
00:12:42.160 você consegue e se conectar de repente
00:12:44.560 com MCP no GitHub, no Gira, no Liner, no
00:12:47.800 Slike, onde quer que seja, você conecta
00:12:49.440 o seu MCP ali. Inclusive eu acho que os
00:12:51.720 MCPs mais úteis, cara, são esses, tá?
00:12:55.079 Eh, eu li o que o S falou também dos
00:12:57.199 MCPs que ele acha mais úteis e parece
00:12:59.639 que a gente concorda que eu não vejo
00:13:01.040 muita utilidade na maioria deles, me
00:13:03.120 parece. Para mim é GitHub e o Tesk
00:13:05.279 Manager são os dois mais importantes
00:13:06.880 porque eles aceleram, você precisa
00:13:09.800 clicar less para fazer o trabalho, tipo
00:13:11.680 isso, né? Você consegue com uma maior
00:13:13.680 facilidade puxar as tesques aqui para
00:13:15.920 serem feitas. Pode ter comandos aqui,
00:13:17.600 skills, etc., que manda puxar uma tesque
00:13:19.519 lá. E quando a tesque chega aqui no
00:13:22.240 momento em que ela tá sendo revisada
00:13:23.720 pelo Code Rabbit, você consegue antes
00:13:25.240 que você ser humano revise, tem umas
00:13:27.199 maneiras de automatizar essas indas e
00:13:29.360 vindas que as mudanças feitas, tipo, as
00:13:31.600 sugestões sugeridas pelo Code Rabbit
00:13:34.199 voltam aqui pro Codex e depois isso
00:13:36.360 volta aqui pro código. O Code Rabbit vai
00:13:37.959 e volta, vai e volta. Você tem essas
00:13:39.680 indas e vindas sem precisar muito do seu
00:13:41.519 input e você depois passa ali uma
00:13:44.519 revisão final, tá? Isso daqui pode
00:13:46.079 ajudar. preciso trazer um vídeo
00:13:47.040 mostrando isso aqui na prática, porque
00:13:48.600 não é a coisa mais trivial do mundo, mas
00:13:51.519 ela é perfeitamente fazível, tipo, é um
00:13:53.199 setup levemente chatinho, tá? Então, meu
00:13:54.800 querido, você vai olhar tudo isso daqui,
00:13:56.759 você vai pensar: &quot;Caramba, eu sou um
00:13:57.880 gênio, eu vou implementar tudo isso e
00:14:01.040 vai ficar show, vai sair perfeito.&quot;
00:14:02.920 Quase, quase. E agora eu preciso te
00:14:05.440 falar o que não fazer. Aí, antes de eu
00:14:06.600 falar o que não fazer, tá? É, vamos,
00:14:08.959 vamos combinar aqui só entre nós, tá?
00:14:10.519 Testes estão muito baratos. Adiciona um
00:14:11.880 monte de teste, manda aí, ah, não
00:14:13.399 deletar testes, né? Ela nunca pode
00:14:15.240 deletar um teste sem que você aceite que
00:14:17.320 o delete, escreve isso aí nos MDS e etc.
00:14:19.720 Você pode também ter os eh precommit,
00:14:23.519 né? Então, quando você manda a fazer e
00:14:25.279 comitar algo, lógico, você não vai
00:14:26.839 deixar a comitar na main porque a sua
00:14:28.360 branch main vai est protegida. Você vai
00:14:30.440 só deixar ela comitar em branches que
00:14:32.839 não são críticas, logicamente, quando
00:14:35.440 ela tentar comitar, ela consegue ler ali
00:14:37.759 o precommit hook e ver se passou ou não
00:14:39.759 passou. Então você pode botar um step
00:14:41.279 que ela é obrigada a testar e ver se
00:14:43.759 passa o teste antes de conseguir
00:14:44.920 comitar. Então isso tá legal. Se você
00:14:46.560 quiser fazer muita loucura com ya, cara,
00:14:49.040 cria um dev contêiner. A gente no meu
00:14:51.480 vídeo de Half Loops, eu te mostrei como
00:14:53.360 fazer isso daqui. Então você procura aí
00:14:55.000 no no YouTube Augusto Galego Half Loops
00:14:56.839 e tem um vídeo de como você botar dentro
00:14:58.440 de uma caixinha que ela não vai destruir
00:14:59.800 completamente seu computador porque se
00:15:01.360 você rodar é com tipo assim dangerously
00:15:04.240 skip permissions o tempo todo, alguma
00:15:05.920 hora a vai deletar uma pasta aí do seu
00:15:07.959 computador e vai se ferrar. acontece. É
00:15:10.079 raro, mas né, se você tiver fazendo 100,
00:15:13.800 200 promptos por dia e o raro vai acabar
00:15:16.399 acontecendo, né? Fazer o quê? Perceba
00:15:18.160 uma coisa, essa descrição aqui te deu
00:15:21.000 também uma quantidade de trabalho muito
00:15:22.519 grande. Você pode pensar, né, pô, mas a
00:15:24.360 IA vai fazer a maior parte do trabalho?
00:15:26.320 Não, a IA vai fazer a maior parte do
00:15:27.839 código. Você consegue enxergar como a
00:15:29.880 criação dessas tesques é uma tarefa
00:15:31.440 muito grande, a revisão desse código é
00:15:32.759 uma tarefa muito grande. Todo esse setup
00:15:34.319 é uma tarefa. Conversar com EA para
00:15:36.519 fazer ela entender, né? Para se fazer
00:15:38.199 ser entendido. Uma tarefa grande,
00:15:40.040 entender a coach base, entender a
00:15:41.040 documentação, entender o que o cliente
00:15:42.120 quer, entender sei lá o quê. Tá ferrado,
00:15:43.519 cara. Você tá muito ferrado. Isso daqui
00:15:45.680 vai te acelerar, mas não vai te
00:15:46.720 facilitar a vida, eu acho. Acho que a
00:15:48.000 gente complicou sua vida. Enfim, que não
00:15:49.959 fazer, né? Você vai pegar um gosto por
00:15:51.720 skills e agents.md, né? Então aqui, ó,
00:15:54.920 skills e agents pmmd. Você vai amar isso
00:15:58.399 daqui. Você vai chegar num ponto que
00:15:59.560 você vai ter uma que os seus prompetos
00:16:01.920 vão ter tipo assim 1000 linhas. Não faz
00:16:04.480 isso, tá? Não faz, não vai funcionar.
00:16:06.480 Tipo, tudo que tiver lá no meio das 1
00:16:08.240 milhão de linhas que você escreveu, vai
00:16:09.519 ser meio que esquecido. Então, cara,
00:16:11.759 somente importante, porque quanto mais
00:16:13.440 informação você adicionar, mais aquela
00:16:15.079 informação vai ser diluída no contexto
00:16:17.199 da IA, ao ponto de que ela ignora todas
00:16:19.720 as suas instruções, tá? Ai meu Deus,
00:16:21.279 acabou a bateria do meu teclado.
00:16:24.240 Vamos digitar no PC mesmo. Você tem
00:16:25.920 também, cara, uma ideia tipo assim de
00:16:28.519 cuspir código, cusp token, etc. Toma
00:16:31.560 cuidado com overengine engineering, toma
00:16:32.880 cuidado com o tal de token maxing. Isso
00:16:35.440 aqui não ajuda ninguém, tá?
00:16:37.040 Sinceramente, você tá gastando mais
00:16:39.399 tokens, não quer dizer absolutamente
00:16:40.600 nada. Quer dizer, quer dizer que você ou
00:16:42.920 sua empresa tá gastando mais dinheiro.
00:16:44.040 É, é, a gente sabe a a assim, há décadas
00:16:47.240 na engenharia de software que linhas de
00:16:48.639 COD não são boas. Na verdade, elas são
00:16:50.000 ruins. Quanto menos código possível para
00:16:53.880 resolver um problema, melhor. Claro, não
00:16:55.959 vamos cair num code golf aqui, né? Mas
00:16:57.600 pouco código é melhor do que muito
00:16:58.800 código. Token Maxing leva a muito
00:17:00.959 código, muito código prolixo, repetido,
00:17:02.959 que vai sinceramente deteriorar sua
00:17:04.799 codebase e acabar introduzindo mais
00:17:07.319 vulnerabilidades, mais dependências, uma
00:17:09.119 usabilidade pior pro usuário, mais
00:17:10.679 lentidão. Não faz o menor sentido isso.
00:17:13.160 Foca na simplicidade. Eu tava
00:17:14.480 conversando com o CEO da empresa esses
00:17:15.760 dias e ele precisava de um documento
00:17:17.480 especificando o que que uma feitature
00:17:18.720 faz.
00:17:19.720 E ele falou para mim: &quot;Olha, se você
00:17:21.160 conseguir, me traz um documento de uma
00:17:24.199 até duas páginas&quot;. Eu sei que vai ser
00:17:26.079 mais difícil, provavelmente mais fácil
00:17:27.400 fazer um documento de seis, sete páginas
00:17:28.960 explicando a feature, mas um de uma a
00:17:30.640 duas vai ser muito melhor, porque na a
00:17:32.360 nossa precisão é algo extremamente
00:17:33.840 valioso. Enfim, eu também eh tentei, de
00:17:36.320 repente é é skichum minha, mas para mim
00:17:39.400 existe um nível de paralelismo em que eu
00:17:42.039 me torno um gargalo tão grande que eu
00:17:44.120 preciso começar a abandonar tudo. Porque
00:17:46.520 é o seguinte, se eu tenho, digamos
00:17:48.640 assim, cinco agentes rodando em
00:17:51.679 paralelo, eles vão produzindo uma
00:17:53.240 velocidade tão alta que eu não tenho
00:17:56.000 tempo para trabalhar nisso daqui, né? Na
00:17:58.760 minha criação de tarefas aqui, eu não
00:18:00.440 tenho tempo para trabalhar nisso daqui,
00:18:02.280 que é a revisão do código. Eu tenho
00:18:04.280 tempo só para ficar fazendo malabarismo
00:18:06.919 aqui de agentes. Para mim, pessoalmente,
00:18:09.480 um agente é bom, dois é ótimo, três pode
00:18:11.640 ser útil em alguns tipos de contexto,
00:18:13.919 quando, por exemplo, um deles tá fazendo
00:18:15.240 um buck fix muito simples, um deles tá
00:18:17.440 gerando uma especificação de uma API e
00:18:19.039 um deles tá trabalhando uma feature
00:18:20.240 importante. Beleza, eu consigo manejar
00:18:22.799 isso na minha cabeça. Passou de quatro,
00:18:24.360 cara, eu me perdi, eu não consigo mais
00:18:26.200 trabalhar. Quem tá trabalhando é os
00:18:27.320 agentes. Tô jogando malabarismo pro alto
00:18:29.400 e rezando para dar tudo certo. Então
00:18:30.840 isso é o que não fazer. Dito tudo isso,
00:18:32.960 gravado esse vídeo, eu precisava falar
00:18:34.840 tudo isso aqui para você, pra gente
00:18:36.360 conseguir prosseguir, tá? Um dos
00:18:37.919 próximos vídeos que vai sair aqui no
00:18:39.080 canal, não sei se exatamente o próximo,
00:18:40.960 vai ser a gente vendo algumas dessas
00:18:42.679 coisas na prática. Se você, né, já tem
00:18:44.320 esse traquejo aqui com traquejo, se é
00:18:46.799 uma palavra, acho que sim, né? Se você
00:18:49.080 já tem essa habilidade aqui, essa
00:18:51.280 prática com a você provavelmente
00:18:52.840 entendeu tudo que eu falei, o que é
00:18:54.080 muito bom. Se você não entendeu, hora
00:18:56.080 perfeita para pesquisar e aprender
00:18:57.440 algumas dessas coisas. Se você quiser,
00:18:59.039 claro, não sou seu pai. E a gente vai ao
00:19:00.760 longo do um ou dois vídeos que eu vou
00:19:03.200 fazer a partir daqui. V isso daqui com
00:19:05.400 um pouco mais de calma na prática, né?
00:19:07.240 pedaço a pedaço até a gente conseguir
00:19:09.200 encaixar tudo isso. Eu acho que isso é
00:19:10.520 um vídeo importante, acho que é um
00:19:11.360 conceito importante. Acho que eu trouxe
00:19:12.600 aqui como usar IA sem focar muito no
00:19:14.280 hype e tal e falando, compartilhando com
00:19:16.799 vocês como que eu tenho visto essa
00:19:18.640 prática se dá no meu dia a dia, me
00:19:21.240 espelhando naqueles que eu acho que são
00:19:23.400 boas referências, tá bom? Por exemplo, o
00:19:25.480 Sun que eu falei, trabalha na Monastic,
00:19:27.000 é uma empresa que tá crescendo
00:19:29.280 absurdamente gigantesca.
00:19:32.000 e ele me falou alguns dos números, eu
00:19:33.520 não posso compartilhar aqui, mas enfim,
00:19:35.000 saiba que esse cara faz código de alta
00:19:37.039 disponibilidade, código que lida ali com
00:19:40.080 muitas requisições e muito volume. E
00:19:43.120 saiba que durante esse último ano eles
00:19:45.880 melhoraram praticamente todas as
00:19:47.679 métricas importantes da empresa. Então
00:19:49.720 isso daqui funciona, tá? Não, não é um
00:19:52.000 hype vazio, isso daqui funciona. A gente
00:19:53.280 pode debater se seria possível fazer
00:19:55.159 isto aqui sem IA, né? Acho que até que
00:19:58.799 sim, mas eu acho que assim é mais
00:20:01.200 rápido. Enfim, se você gostou do vídeo,
00:20:02.640 lançamos esse mês um curso completo de
00:20:04.559 system designer, demorou mais de um ano
00:20:06.440 para ser produzido e você pode comprar e
00:20:08.559 assistir o curso inteiro e se você não
00:20:10.280 gostar, eu te dou até um mês para pedir
00:20:12.120 reembolso, né? Você tem um mês aí para
00:20:13.679 assistir todas as aulas. Se você tiver
00:20:15.960 tempo nesse um mês, né, que é muita
00:20:17.400 coisa aqui, como você tá vendo, tipo,
00:20:18.760 tem quantos são os módulos, são 17
00:20:22.240 módulos. É muita coisa. System design tá
00:20:25.520 super importante agora na na época da
00:20:27.320 IA, né? Vai até te ajudar com tudo isso
00:20:29.919 daqui que eu te contei agora, né? Com
00:20:31.520 toda essa parte aqui, né? Principalmente
00:20:33.240 na parte da criação das tescas aqui,
00:20:35.600 definir as fronteiras de cada tarefa e
00:20:37.120 tal. Tá importantíssimo também o sistema
00:20:38.720 design para
00:20:40.039 passar entrevistas de emprego,
00:20:41.360 principalmente pra gringa. Esse é o
00:20:42.880 curso mais aguardado. As pessoas me
00:20:44.280 pedem isso há pelo menos um ano e meio,
00:20:47.240 acho, mais até, na verdade, uns dois
00:20:49.320 anos.
00:20:50.600 E tá finalmente aqui depois de um ano
00:20:52.400 produzindo isso daqui, mais alguns meses
00:20:54.080 aí refinando e terminando ele. Temos o
00:20:56.000 curso completo do System Design. O link
00:20:58.200 para esse curso vai est na descrição.
00:20:59.840 Lançamos ele esse mês. Momento perfeito
00:21:02.080 para você aprender e se aprofundar
00:21:03.400 nesses conceitos. Esse curso é feito
00:21:05.120 para quem é junior, pleno e sior. Quem é
00:21:08.000 assim muito sénior há muito tempo já viu
00:21:10.080 tudo isso daqui, talvez não seja para
00:21:11.640 você. E quem ainda não é júnior, ainda
00:21:14.440 não teve o primeiro emprego, ainda não
00:21:16.159 teve o primeiro estágio, definitivamente
00:21:17.799 não é para você, tá? Pra Júnior, a gente
00:21:19.320 até é didático suficiente para conseguir
00:21:21.039 te ensinar isso daqui, mas para quem
00:21:22.520 ainda não começou a trabalhar na área,
00:21:24.360 eu acho que não faz muito sentido, tá
00:21:25.640 bom?
