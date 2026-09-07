# tactiq.io free youtube transcript
# O MÍNIMO que um dev precisa saber sobre segurança
# https://www.youtube.com/watch/aGVN6aHKkE0

00:00:00.000 Eu não sou um cara de se eu não sou um
00:00:02.120 cara de segurança da informação. Eu sou
00:00:03.919 dev, né? Fui deve a maioria da minha
00:00:05.160 carreira, sou CTO atualmente. E eu tô
00:00:07.000 aqui para te falar que segurança
00:00:08.160 responsabilidade de todo mundo. Lógico.
00:00:10.679 A última palavra sobre segurança é do
00:00:12.759 cara de segurança, mas segurança não é
00:00:14.879 uma feature, não é um conjunto de
00:00:16.800 features, não é algo que você contrata
00:00:18.920 alguém para configurar e do nada tá tudo
00:00:21.240 seguro. Segurança é acima de tudo,
00:00:23.680 cultura de segurança, né? Segurança é
00:00:25.480 você não clicar em e-mails duvidosos,
00:00:27.080 você não clicar em links duvidosos.
00:00:29.160 Segurança você usar multifactor
00:00:31.480 authentication nas contas importantes da
00:00:33.440 empresa. Segurança você não comitar a
00:00:35.960 senha do banco de dados no GitHub. Hoje
00:00:38.239 a gente vai falar de cinco práticas,
00:00:40.120 cinco recomendações que foram tiradas
00:00:42.280 diretamente do Pragmatic Programmer para
00:00:44.320 transformar você em um dev que se
00:00:46.039 importa um pouco mais com segurança.
Antes disso, eu vou te falar do
00:00:48.840 patrocínio de hoje, que é a abac. Olha
00:00:51.000 só essa thumbnail aqui. Eu não vou usar
00:00:52.520 thumbnail gerada por EA, tá? Mas enfim,
00:00:54.520 essa até legalzinha. Ela foi gerada com
00:00:56.199 o Nano Banana Pro, que é um modelo que
00:00:57.800 geralmente é pago, tá? Se você tiver a
00:00:59.879 subscription de apenas por mês, você vai
00:01:02.640 ter acesso ao Nano Banana Pro. Você vai
00:01:04.159 ter acesso ao chat aqui com basicamente
00:01:06.040 todos os modelos de A, incluindo, né, o
00:01:07.600 GPT 2.5 com Finking, o Gemini 3 Pro, o
00:01:10.200 Nano Banana Pro, que é esse que gerou
00:01:11.840 essa imagem aqui, né, gera imagens muito
00:01:13.360 boas, o Cloud Opus 4.5, você vai ter
00:01:16.200 acesso também a ideia que é o code ll,
00:01:18.560 né, que tem o agente aqui do lado que
00:01:19.759 pode fazer alterações no seu código,
00:01:21.280 funciona mais ou menos como curso, tá?
00:01:23.159 Isso na mesma subscription de
00:01:25.159 se você vê meus vídeos, né, eu já falei
00:01:26.400 bastante da aba aqui, você já deve ter
00:01:28.119 visto eu, por exemplo, usando o page da
00:01:30.560 cu para fazer uma suitch de testes
00:01:32.520 compreensiva para testar o meu site. Aí
00:01:34.280 ele deu um resultado aqui dos testes e
00:01:36.079 tal. Cara, ferramental muito poderoso,
00:01:37.600 tem muitas coisas. Você tem o chat, você
00:01:39.280 tem o dpagent que pode fazer MVPs, pode
00:01:41.439 fazer testes, pode agir que nem um Kway,
00:01:43.040 pode agir que nem um usuário, pode fazer
00:01:44.360 1 milhão de coisas. Aqui você tem o code
00:01:45.920 LLM, que é a IDE, você tem uma
00:01:47.479 infinidade de ferramentas, na verdade
00:01:49.000 você tem agente de código na CLI, enfim,
00:01:51.560 tem muita, muita, muita coisa. O link
00:01:53.159 para abusar vai est na descrição, apenas
00:01:54.880 $10 por mês. 10 na cotação atual é mais
00:01:57.880 barato que praticamente todas as outras
00:01:59.360 e tá, vai ser R 50 e poucos reais.
00:02:01.200 Enfim, tem custando $2 aí. Bom, vamos
00:02:03.799 pra nossa primeira dica. Primeiríssima,
00:02:05.360 talvez a mais importante dica pra
00:02:06.960 segurança para programadores é isso
00:02:08.800 daqui, minimizar a área de superfície. O
00:02:11.280 que que é a área de superfície, né? é a
00:02:13.120 superfície de contato, por exemplo, é o
00:02:15.080 quanto de código existe, o quantas
00:02:17.959 partes existem, o quantas partes
00:02:19.920 encostam em quantas partes e o quanto
00:02:21.560 isso encosta no mundo real. Por exemplo,
00:02:23.519 complexidade de código, né? Se você tem
00:02:25.360 1 milhão de linhas de código, é 1 milhão
00:02:27.200 de linhas onde pode possivelmente morar
00:02:29.040 um bug, morar um exploit, morar uma
00:02:30.640 vulnerabilidade. Complexidade de código
00:02:32.760 é superfície de contato. Inputs do
00:02:34.720 usuário, qualquer tipo de input do
00:02:36.560 usuário é alguma maneira de superfície
00:02:38.519 de contato. É alguma possível
00:02:40.360 vulnerabilidade. A gente tem aquela
00:02:41.920 comic do Xcase. A pessoa foi entrar o
00:02:44.640 digitar o nome de um estudante ali num
00:02:46.720 sisteminha e o estudante, o aluno
00:02:48.640 chamava Robert. Vírguldrop table
00:02:51.319 students, né? E se você executar isso
00:02:53.159 aqui no banco de dados, você tentar
00:02:54.400 adicionar esse nome aqui no banco de
00:02:55.560 dados sem tratar esse input, é isso aqui
00:02:57.920 basicamente é scell, tá? Tudo que o seu
00:03:00.159 usuário te mandar, você pode pensar que
00:03:02.840 pode ter uma vulnerabilidade ali de
00:03:04.440 alguma maneira, né? Pode ter algum
00:03:05.920 exploit ali, pode ter algum código
00:03:07.640 malicioso, pode ter algum arquivo
00:03:09.239 malicioso, algo nesse sentido. Então,
00:03:11.400 trata com muita cautela tudo que o
00:03:12.959 usuário usar como input em qualquer
00:03:14.560 lugar. Pode ser o nome dele, pode ser o
00:03:15.959 e-mail dele, pode ser o password dele.
00:03:17.480 Você tem que sanetizar, né? sempre tá
00:03:19.519 limpando ali os inputs do usuário para
00:03:21.239 poder utilizar isso aí de alguma forma.
00:03:22.920 Serviços não autenticados. End points
00:03:25.040 públicos. Como assim? Se você tem o seu
00:03:26.799 banco de dados aqui, perdão, seu banco
00:03:28.239 de dados não, né? Seu backend aqui,
00:03:29.959 servidorzinho de backend. Esse servidor
00:03:31.439 de backend, muito provavelmente, eles
00:03:33.400 põe aqui uma API, né? Uma API que vai
00:03:35.480 ser consumida pelo frontend. E essa API
00:03:37.480 vai ter uma série de end points aqui.
00:03:39.480 Cada end point que não requer
00:03:41.439 autenticação é um possível vetor de
00:03:43.200 ataque que um bot pode spamar para fazer
00:03:45.480 DDOS. Ele pode tentar varrer os dados
00:03:47.360 disponíveis, ele pode tentar procurar
00:03:48.959 por um exploit em cada um desses end
00:03:51.319 pointzinhos aqui que não requer
00:03:52.640 autenticação. Então é interessante que
00:03:53.879 você pensar nisso aqui como sempre
00:03:55.680 possíveis vulnerabilidades, né? Lógico,
00:03:57.640 fechar esses end points não
00:03:59.599 necessariamente torna eles seguros a
00:04:01.200 DDOS e diversos outros tipos de coisa.
00:04:03.599 Você precisa de mais ferramentas aqui.
00:04:05.040 Mas enfim, é um bom começo expor poucos
00:04:07.720 end points ao público, né? O mínimo
00:04:10.319 possível, sempre o mínimo possível. Um
00:04:12.000 erro que é muito comum também, que eu
00:04:13.079 vejo quando você volta e meia é isso
00:04:14.360 aqui, ó. Você tem aqui um S3. Dentro
00:04:16.720 desse S3 você disponibiliza que as URL
00:04:20.199 sejam públicas, né? Então você tem a URL
00:04:21.680 aqui que é, sei lá, S3.Aama,
00:04:24.360 sei lá o qu barra umu ID aqui. E
00:04:27.040 qualquer pessoa que acessar essa URL vai
00:04:29.680 conseguir acessar o o arquivo que tá
00:04:31.680 dentro de desses S3, tá? Eu já vi essa
00:04:33.199 vulnerabilidade muito presente em vários
00:04:35.160 casos. Você pode pensar, pô, qual que é
00:04:36.520 o problema aqui, né? Eu tenho um uinguém
00:04:39.160 vai adivinhar o meu UI. Raciocínio, OK,
00:04:41.800 um raciocínio bem pensado, você é uma
00:04:43.479 pessoa muito inteligente, porém você tem
00:04:44.960 que se tocar que URLs não são como
00:04:46.919 passwords. O seu, o seu browser não
00:04:49.360 trata ela com a mesma segurança que ele
00:04:51.120 trata uma password, né? Vai ficar ali no
00:04:52.639 seu histórico. Isso que pode ser
00:04:53.960 cacheado, isso que vai est no histórico
00:04:55.080 do seu roteador, isso que vai est no
00:04:56.199 histórico de um monte de coisa pela
00:04:57.639 internet. A URL ela não é tratada
00:05:00.000 nativamente como algo é sensível, como
00:05:02.440 um dado sensível, tá? Então o seu S3
00:05:04.880 também precisa ter autenticação, né?
00:05:06.280 Quando você tá lidando com documentos
00:05:07.840 sensíveis. Na verdade, sempre deveria
00:05:09.680 ter, porque senão alguém pode novamente
00:05:11.280 fazer um DDS aqui, vai te causar um
00:05:12.919 custo bacana. Outro exemplo disso, né,
00:05:14.880 eu vi uma vez já numa, eu vou, vou
00:05:16.680 abstrair um pouco aqui, tá? Vi uma vez
00:05:18.000 alguns serviços que eram tipo assim, ó,
00:05:19.360 se você tiver aqui barrapi barra sei lá
00:05:21.720 o qu, imagens barra13
00:05:24.960 e aí você dá um get aqui, o seu backend
00:05:28.080 te retorna aquela imagem. Eh, ok.
00:05:30.360 Interessante. E a a vulnerabilidade
00:05:32.280 consistia em simplesmente você mudar
00:05:34.120 isso daqui, né, para pô, 1 2 3,
00:05:36.240 provavelmente é um ID sequencial, 1 2 3
00:05:38.759 4, enter aí retornava outra imagem. 1 2
00:05:41.560 3 4 5, retornava outra imagem, 1 2 6,
00:05:44.319 outra imagem, 1 2 7 outra imagem. E
00:05:46.440 assim a pessoa conseguia varrer todas as
00:05:48.479 imagens que estavam ali naquele serviço,
00:05:49.960 né? Já vi isso acontecer. Então, tome
00:05:51.800 cuidado com todos os possíveis vetores
00:05:53.840 de ataque aqui, né? Muita área de
00:05:55.199 superfície. Outra coisa que você tem que
00:05:56.639 tomar cuidado, né? A gente falou sobre
00:05:57.800 serviços não autenticados, mas serviços
00:05:59.919 autenticados também, né? Hoje em dia
00:06:01.600 você tem que muitas coisas conversam com
00:06:03.600 outras coisas. Você tem que o backend,
00:06:05.400 de repente você tem múltiplos backends,
00:06:06.800 né? Múltiplos backends se conversando
00:06:08.560 ali. Um conversa com outro, outro
00:06:10.160 conversa com um, eles conversam com o
00:06:11.880 seu banco de dados. Aqui todos esses
00:06:14.120 backends podem conter vulnerabilidades e
00:06:16.280 podem ser um vetor de ataque pro seu
00:06:18.000 atacante entrar nele e começar a fazer
00:06:20.319 coisas maliciosas ali. Você pode ter que
00:06:22.199 de repente um desses backends, cara, sei
00:06:23.919 lá, vazou uma chave de SSH para se
00:06:26.120 conectar aqui, né? Ou então os passwords
00:06:28.039 para entrar no barra admin desse outro
00:06:30.720 backend aqui, ele é muito simples, é
00:06:32.520 para entrar no barra admin aqui, alguém
00:06:34.080 esqueceu que a senha era, sei lá, nome
00:06:36.280 da empresa 2016, saca? E aí ficou assim
00:06:39.360 para sempre. E aí sei lá, de repente em
00:06:40.960 2018 algum funcionário anotou isso aí em
00:06:42.800 algum lugar e vazou, sabe? Tudo isso
00:06:44.800 daqui são vetores de ataque, tá? Então
00:06:47.000 toma muito cuidado. Imagina, né? Pô,
00:06:48.599 essa máquina aqui tá rodando há 10 anos.
00:06:50.199 O quanto de vulnerabilidade que pode ter
00:06:51.919 aqui, cara? Bom, e se inputs são vetores
00:06:54.080 de ataque, você vai ficar surpreso. Mas
00:06:56.080 outputs também, né? A gente falou aqui
00:06:57.520 do do exemplo disso daqui. Isso aqui é
00:06:58.919 basicamente um output representando uma
00:07:00.800 vulnerabilidade, mas cara, você pode ter
00:07:02.440 que, por exemplo, com seu log, né, pode
00:07:04.039 ser um vetor de ataque, dependendo do
00:07:05.319 que você tá logando ali no seu browser,
00:07:07.240 no seu serviço, enfim, se você tá
00:07:08.639 logando dados sensíveis, se você tá
00:07:10.759 logando senhas ou esse tipo de coisa,
00:07:12.520 isso daqui é uma possível
00:07:14.039 vulnerabilidade, é um possível vetor de
00:07:15.639 ataque. Um dos outputs que as pessoas
00:07:17.360 não pensam, eu vou te dar um exemplo bem
00:07:19.199 só para você ver o tamanho da da
00:07:21.000 complexidade, tá? Imagina que a minha
00:07:22.520 senha é gato 1 2 3 4 5, tá? Essa é a
00:07:25.280 minha senha. Existiu uma vulnerabilidade
00:07:27.240 aí, uma vulnerabilidade conhecidíssima
00:07:28.960 que consistia no seguinte fato. Bom, a
00:07:32.000 minha senha é gato 1 2 3 4 5, né? O
00:07:33.879 algoritmo que checa a minha senha, ele
00:07:36.400 acabava checando tipo assim, letra por
00:07:38.520 letra, né? Eu tô simplificando aqui como
00:07:39.800 é que funciona, tá? Mas ele acaba, ele
00:07:41.560 acaba checando letra por letra. Checa
00:07:43.440 uma, checa outra, checa outra, checa
00:07:44.759 outra, enfim, vai checar letra por
00:07:46.199 letra, né? Então eu entrava, eu testava
00:07:48.800 as seguintes senhas, né? A, a, a a b a c
00:07:52.800 a até eu chegar no g a a, né? E aí cada
00:07:56.960 senha que eu testava me dava um tempo de
00:07:58.680 resposta. Vou imaginar que isso aqui
00:07:59.680 demorou 0.01
00:08:01.840 ms senha aqui de baixo também 0.01 mos.
00:08:04.919 Essa aqui também 0.01 ms até que a senha
00:08:07.280 G A AA ela demorou 0.03 ms como assim?
00:08:11.720 Como o algoritmo de checar senha, ele
00:08:13.720 checava sequencialmente, letra por
00:08:15.240 letra, né? Bom, na primeira senha ele
00:08:16.800 via que o A não era a primeira letra, já
00:08:18.440 retornava. Na segunda ele via que o B
00:08:20.240 não era a primeira letra, já retornava.
00:08:21.720 Quando chegou no G, A, a A, eu descobri,
00:08:24.199 né? G, aí checa o A, aí checa o T. Esse
00:08:26.879 demorou mais do que as outras. Então, a
00:08:28.319 gente sabe que a senha aqui começa com
00:08:31.000 G, pelo menos. É, eu testo combinações a
00:08:33.320 partir do G, depois eu testo combinações
00:08:35.200 a partir do GA, Gat, GTO. Aí eu vou
00:08:37.599 checando combinação por combinação e
00:08:39.479 dessa maneira, na verdade, para eu
00:08:41.120 descobrir qual é a senha, né? Eu não
00:08:42.399 preciso checar 26 x 26 x 26, enfim, esse
00:08:45.600 número gigante de senha. Eu preciso
00:08:46.959 checar 26 + 26 vezes mais 26 vezes mais
00:08:51.279 26. E eu muito rapidamente quebrava essa
00:08:53.680 senha, né? Para você ver, até o tempo de
00:08:56.320 resposta que demora pro seu servidor dar
00:08:58.279 pode ser um vetor de ataque. Lógico,
00:08:59.920 você não tá nem aí para isso, você não
00:09:00.800 vai pensar nisso aqui no seu dia a dia.
00:09:01.959 Ninguém vai pensar nisso aqui no seu dia
00:09:03.399 a dia, tá? Eu tô só te expondo, tô só te
00:09:06.279 dizendo a infinidade de possíveis
00:09:09.240 vetores de ataques aqui. Até o tempo de
00:09:12.040 resposta pode dar uma uma informação que
00:09:14.600 vai gerar uma vulnerabilidade. Vamos pro
00:09:16.240 dois. Princípio de menor privilégio.
00:09:18.640 Bom, o seu serviço aqui, ele deve ter o
00:09:20.079 privilégio exato que ele precisa para
00:09:22.000 fazer as tarefas dele e não mais, nada
00:09:24.200 mais. Não só o seu serviço, como também
00:09:25.720 os funcionários da empresa, como também
00:09:27.120 pessoas que interagem com a IPI da
00:09:28.760 empresa, todo mundo tem que ter o menor
00:09:30.560 privilégio possível para executar aquilo
00:09:32.240 que a pessoa deve fazer ou que o serviço
00:09:34.079 deve fazer. Imagina o seguinte, né?
00:09:35.399 Imagina nosso mesmo exemplo aqui dos
00:09:36.880 backends, que esse backend aqui tinha
00:09:39.040 alguma uma vulnerabilidade porque ele
00:09:40.440 era um serviço muito antigo e tal, mas
00:09:42.240 por sorte esse backend ele pode só tem a
00:09:45.000 permissão para ler do banco de dados,
00:09:46.720 ele tem apenas read. Mesmo que tenha
00:09:48.519 vazado, mesmo que alguém conseguiu
00:09:50.480 acessar isso daqui com SSH vazado e tal,
00:09:52.959 a pessoa apenas conseguiu ler do banco
00:09:54.839 de dados, não conseguiu modificar nada.
00:09:56.839 Um pouco do dano foi contido, né? Não
00:09:58.440 todo dano, mas foi menos pior. Princípio
00:10:00.399 de menor privilégio diz respeito a isso.
00:10:02.200 Tudo deve ter o mínimo de privilégio
00:10:04.000 possível. Os usuários que t admin na sua
00:10:05.920 empresa não devem poder fazer
00:10:06.760 absolutamente tudo, né? Você tem que ver
00:10:08.160 exatamente o que que a pessoa precisa
00:10:09.600 para fazer aquele trabalho e fazer só
00:10:11.240 aquilo. Isso vale também pros usuários,
00:10:12.959 tá? Os usuários estão interagindo com a
00:10:14.240 sua PI. Enfim, princípio do menor
00:10:16.000 privilégio, vai prevenir que coisas
00:10:17.640 ruins aconteça, né? Outro exemplo disso
00:10:19.079 daqui, o seu banco de dados, por
00:10:20.320 exemplo, só que tudo provavelmente vai
00:10:22.320 est dentro de uma VPC, né? VC. Muitas
00:10:25.120 das vezes, em muitas empresas, não
00:10:26.640 existe nenhum motivo razoável para
00:10:28.880 alguém conseguir acessar esse banco de
00:10:30.680 dados de fora da VPC. O seu frontend não
00:10:33.279 deve conseguir acessar o banco de dados.
00:10:34.839 Isso não deve ser possível. Alguém que
00:10:36.800 tá fora da VPC não deve conseguir
00:10:38.480 acessar o banco de dados, né? Aí você
00:10:39.720 fala: &quot;Pô, galego, mas minha empresa é
00:10:40.920 um pouquinho mais antiga, né? preciso
00:10:42.079 acessar o banco de dados para rodar as
00:10:43.720 migrations e tal, não roda automático,
00:10:45.360 não tem problema. O que você pode fazer?
00:10:47.519 Você pode ter uma máquina aqui, né, uma
00:10:48.959 S2zinha aqui. Aí o seu dev, ele vai
00:10:51.639 acessar essa S2 aqui dentro SSH e vai
00:10:54.800 então fazer ali a comunicação com o
00:10:57.000 banco de dados bonitinho. Esse carinha
00:10:58.720 aqui não é recomendado que ele fora da
00:11:01.399 VPC consiga usar as credenciais aqui,
00:11:03.560 né? Consiga usar o password aqui para
00:11:05.000 acessar direto o end point do banco. Não
00:11:06.480 é recomendado. Esse é o princípio do
00:11:08.079 menor privilégio. Três aqui os nossos
00:11:09.839 defaults, né? nossos defaults seguros.
00:11:12.079 Que que é um default seguro? Você tá
00:11:13.399 digitando ali sua senha, gato 1 2 3 4,
00:11:15.480 só que a sua senha tá aparecendo assim,
00:11:16.880 ó. Asterisco, asterisco, asterisco. Isso
00:11:18.519 aqui é um default seguro. O usuário, ele
00:11:20.720 pode clicar no botão, né? Geralmente tem
00:11:22.760 um olhozinho aqui, né? Bem bonitinho.
00:11:24.519 Ele pode clicar nesse olho aqui para
00:11:26.200 visualizar a senha, mas o default é
00:11:28.120 seguro. Quando você vai lá na na WS, né?
00:11:30.240 Eu vou lá na WS, eu vou deletar a minha
00:11:32.240 S2, eu clico aqui no botãozinho delete.
00:11:34.639 Que que o botãozinho delite faz? Ele
00:11:35.880 deleta S2? Não, ele não deleta S2. Ele
00:11:38.320 abre uma caixinha aqui para mim que
00:11:39.760 fala: &quot;Você tem certeza?&quot; Digite tenho
00:11:43.160 certeza. Aí você tem que digitar ali na
00:11:44.720 caixinha, né? Tenho certeza que quero
00:11:46.079 doletar serviço tal, tal, tal. Que isso?
00:11:48.000 Isso é um defol seguro. Você tá
00:11:49.160 prevenindo o usuário de fazer alguma
00:11:50.920 ação possivelmente destrutiva. Ações
00:11:53.279 destrutivas, como por exemplo, mostrar
00:11:55.200 sua senha pode ser algo destrutivo ou
00:11:57.040 deletar uma C2 pode ser algo destrutivo.
00:11:59.000 O padrão tem que ser seguro, né? Por
00:12:00.880 padrão, quando você entra numa empresa,
00:12:02.720 geralmente a sua conta ali do Google,
00:12:04.240 né, que tem vários acessos, a empresa
00:12:05.839 vai falar: &quot;Olha, a primeira coisa que
00:12:07.000 você tem que fazer é mudar o password de
00:12:08.600 padrão e ativar o 2FA, ativar o to
00:12:11.279 factory authentication, né? Tu tem uma
00:12:13.160 semana para fazer isso.&quot; Isso é um
00:12:14.399 padrão, é um default seguro. Se a sua
00:12:16.160 empresa não força todos os funcionários
00:12:18.120 a ter 2 FA, eu sei, é chato, tá? Eu
00:12:19.680 também não gosto de 2FA, mas enfim, se a
00:12:21.199 empresa não força isso, o padrão poderia
00:12:23.360 ser mais seguro. O padrão não é seguro o
00:12:24.839 suficiente. O quarto é bem simples, tá?
00:12:26.240 É criptografada dos sensíveis. Tipo, lá
00:12:27.880 no banco de dados você vai armazenar o,
00:12:29.279 pô, dados bancários de um usuário,
00:12:30.680 acende um usuário e tal, é tudo
00:12:32.000 criptografado, joga tudo através de
00:12:33.680 algoritmo de Hash e tal, usa os padrões
00:12:35.360 de criptografia, né? Você não vai
00:12:36.680 inventar criptografia em casa, mas
00:12:38.600 enfim, criptografa os dados sensíveis. E
00:12:41.120 o quinto é sempre fazer updates de
00:12:43.199 segurança o mais rápido possível. Aqui
00:12:45.680 você provavelmente vai querer ter uma
00:12:46.839 ferramenta que te avise que tem um novo
00:12:49.079 update de segurança em tal serviço que
00:12:51.279 você tá usando. O GitHub faz isso em
00:12:52.920 algum nível, né? Tem lá o Dependabot.
00:12:55.000 Depend bot vai te avisar, ó, essa versão
00:12:56.959 aqui do React que você acabou de comitar
00:12:58.519 tem uma vulnerabilidade. Você tem que
00:12:59.920 atualizar aí o React para tal versão.
00:13:01.639 Eh, outra recomendação, né, um pouco
00:13:02.839 mais interessante que essa, de repente,
00:13:04.279 é você utilizar um Sast, que é static
00:13:07.560 application security testing, né? Que
00:13:10.279 que é esse nome complexo? Quer dizer, é
00:13:11.600 um software, né? Um dos mais usados aqui
00:13:12.760 é o Sonar Cube. Eu acho que é assim que
00:13:14.199 se escreve sonar cube. É um jeito meio
00:13:15.880 estranho, tá? Que escreve, tipo, não é
00:13:17.480 com, eu não, não é com c, eu acho que é
00:13:19.160 com q. Enfim, você vai achar aqui, ó.
00:13:21.040 Sonar cube é assim mesmo. Que que esse
00:13:22.760 carinha aqui vai fazer para você? Ele
00:13:24.440 pode te alertar, por exemplo, quando
00:13:25.680 você tá executando um código que o que o
00:13:27.240 cliente te manda, né? A gente falou lá
00:13:28.360 de scell injection, ele pode, né? Ele
00:13:30.279 faz aqui s de stética, ele faz uma
00:13:32.800 análise estática de código que pode ver
00:13:34.639 que, pô, seu código aqui tem uma
00:13:36.360 possível vulnerabilidade para scell
00:13:37.880 injection, muda isso aí. Seu código tá
00:13:39.519 vulnerável a XSS, né? Crosside
00:13:41.800 scripting, muda isso daí. Então, né?
00:13:43.440 Isso daqui é uma ferramenta que vai te
00:13:44.639 ajudar ali a manter um pouco mais a
00:13:46.199 segurança do código de maneira estática
00:13:47.880 ainda, né? Isso aqui ainda não resolve
00:13:49.880 seu problema, tá? Porque não vai
00:13:51.199 resolver muita coisa. Geralmente você
00:13:52.519 vai querer ainda utilizar isto aqui
00:13:54.120 aliado a umna web application firewall.
00:13:57.560 São duas coisas diferentes para
00:13:58.680 propósitos totalmente diferentes que
00:14:00.440 contribuem na nossa cultura de
00:14:02.000 segurança, porque novamente segurança
00:14:03.440 não é uma ferramenta. Uma diquinha aqui
00:14:05.040 bem interessante, lembra que eu falei
00:14:06.440 aqui, né, de passwords de banco de dados
00:14:08.040 e tal, essas senhas, esses passwords
00:14:10.759 jamais podem ser comitados na sua Code
00:14:12.839 base. Jamais. Se você comitou uma senha
00:14:14.880 na Code base, altera essa senha
00:14:16.240 imediatamente. Ah, galera, então como
00:14:17.680 que eu faço, né? Como que o meu banco de
00:14:19.120 dados vai acessar ali a minha meu
00:14:20.959 backend vai acessar ali meu banco de
00:14:21.959 dados? Bom, localmente, né, na sua
00:14:23.199 máquina local, você vai ter um ponto ENV
00:14:24.480 e um pon. Example ou ponto exemple ponv,
00:14:27.839 eu nunca lembro. Eu acho que é ponto
00:14:29.320 exemple ou ponto env, né? Isso daqui,
00:14:31.360 esse ponto ENV aqui que vai ter alguma
00:14:33.160 credencial, possivelmente não de
00:14:34.920 produção. Você não quer ter esse
00:14:35.839 credencialis de produção na sua máquina,
00:14:37.279 nunca vai ser comitado. Ele vai est até
00:14:38.680 no gitnore. Git ignore vai est mandando
00:14:40.320 você não comitar isso daqui. Esse aqui o
00:14:41.680 exemplo pode comentar aí. Bom, dentro
00:14:43.440 desse ponto você vai ter lá, né, DB
00:14:45.560 password, open AI, API key, né? E aqui
00:14:48.959 igual H 23 API aqui, aqui uns valor
00:14:51.480 aleatório. Como que a minha aplicação
00:14:53.079 vai ter acesso a essa informação aqui se
00:14:55.079 ela não vai estar cometada? Só que você
00:14:56.759 vai armazenar numa ferramenta específica
00:14:58.399 para isso, né? Que que é uma ferramenta
00:14:59.519 específica para isso? Pode ser o GitHub
00:15:01.079 Secrets, que quando a sua aplicação for
00:15:03.160 deployada, ele vai injetar essas
00:15:05.160 variáveis ali na aplicação, né, de
00:15:06.440 alguma maneira. Aí você não vai ter
00:15:07.839 acesso a ela, quer dizer, você vai vai
00:15:09.959 poder modificar ela se quiser, né? Só
00:15:11.320 que você não vai poder mais ver esses
00:15:13.040 secrets, que é muito bom, muito positivo
00:15:14.680 pra segurança. Uma vez que eles estão
00:15:15.759 gerados, eles não são mais visíveis, né?
00:15:17.959 Você não consegue mais visualizar ali
00:15:19.199 essa informação. Tem também o WS Secrets
00:15:20.880 Manager. Você vai utilizar alguma
00:15:22.440 ferramenta específica para manter esses
00:15:24.320 segredos que vai, tipo assim, entre
00:15:25.839 aspas, injetar esses segredos na sua
00:15:27.440 aplicação, na hora da aplicação rodar. E
00:15:28.839 pra gente terminar aqui com uma com uma
00:15:30.000 história engraçada, né? É uma história
00:15:31.120 que que talvez seja real, talvez não
00:15:32.720 seja real, tá? Uma história, digamos
00:15:33.959 assim, puramente fictícia, talvez. É,
00:15:36.160 meus advogados me recomendaram falar que
00:15:37.519 é uma história puramente fictícia. Você
00:15:38.959 tem uma empresa aqui que tinha um
00:15:40.519 servição assim, né? Vou imaginar, pô,
00:15:42.079 esse serviço aqui tá tá bacana. Vamos só
00:15:43.560 desenhar aqui também uma parte que é
00:15:44.959 muito importante para esse nosso serviço
00:15:46.199 aqui, ó, frontend, né? Bacana. Nessa
00:15:48.160 empresa tinha um dev principal que era
00:15:49.440 muito bom e um CTO que não era tão bom
00:15:51.560 assim, né? Mas o CTO, pô, fundou a
00:15:53.519 empresa com outros dois, outras duas
00:15:55.360 pessoas não técnicas do CTO construiu
00:15:57.720 parte daquele produto, mas ele era,
00:15:59.519 digas de passagem, como deve, horrível.
00:16:01.839 Eram três sócios, né? E o City era o
00:16:03.360 único dev o único sócio técnico dessa
00:16:05.800 empresa. Enfim, contrataram uma equipe,
00:16:07.279 tal, contrataram o dev ali principal
00:16:08.800 para ajudar em algumas partes do backend
00:16:10.600 e o dev principal começou a notar
00:16:12.279 algumas coisas estranhas. Ele notou, por
00:16:14.319 exemplo, tipo assim, seria muito
00:16:15.639 estranho se o password do banco de dados
00:16:18.000 tivesse sido comitado, né? Se ele, se o
00:16:20.720 se o ponto ENV tivesse sido comitado.
00:16:22.680 Então, pô, imagina, comitei um ponto ENV
00:16:24.560 na code base que contém o P do banco de
00:16:26.240 dados. Estranho, né? Ruim. Mas se essa
00:16:28.880 informação aqui não vazou, parece que tá
00:16:30.600 OK. Parece que não tem problema muito
00:16:31.759 grande. Seria um pouco pior ainda se de
00:16:34.279 repente não fosse nenhum ponto env, né?
00:16:35.680 Se esse password tivesse hardoded em
00:16:38.480 vários locais do banco de dados e esse
00:16:41.120 código acessava ali diretamente o banco
00:16:43.240 de dados, né? Com o password hard coded.
00:16:45.319 Cara, loucura isso daqui, muito loucura.
00:16:47.759 Mas bom, novamente, né? Se o seu GitHub
00:16:50.160 tá privado, seu código tá privado e com
00:16:52.480 sorte ninguém na empresa vazou esse
00:16:54.480 código, né? Com sorte isso aqui não
00:16:56.240 vazou para lugar nenhum. OK. É [risadas]
00:16:59.160 extremamente preocupante, mas é dos
00:17:01.440 males o menor, né? Dá pra gente corrigir
00:17:03.079 isso aqui com facilidade até. Agora,
00:17:05.039 seria muito chocante, mas muito chocante
00:17:08.039 mesmo, se o password fosse hard coded,
00:17:10.439 né? Codado direto, não backend, mas no
00:17:13.199 front end e o próprio front end fizer
00:17:15.679 essas requisições direto pro banco de
00:17:17.839 dados e o banco de dados, meu Deus,
00:17:19.839 parece que é brincadeira isso aqui,
00:17:21.679 retornasse direto pro Seria chocante,
00:17:24.480 né? Seria uma loucura se isso aqui
00:17:26.000 acontecesse, né? Tipo assim, as
00:17:27.280 credenciais aqui, eu peço hoje do banco
00:17:28.799 de dados ali no próprio browser do
00:17:30.679 usuário, no próprio browser, no próprio
00:17:32.559 Google Chrome do usuário, o cara faz a
00:17:34.880 requisição direto lá pro banco de dados,
00:17:36.919 né? Bizarro. Muito doido, cara. É bom.
00:17:39.160 É, é uma história, claramente isso aqui
00:17:40.840 nunca aconteceu em lugar nenhum. É uma
00:17:42.320 história puramente fictícia. Puramente
00:17:44.720 nada disso aqui aconteceu. Essa história
00:17:46.760 fictícia termina com aquele City sendo
00:17:49.160 demitido, o dev principal da empresa
00:17:51.960 sendo promovido a City. ETV principal,
00:17:54.280 né? Depois de promovido City, ele mesmo
00:17:56.280 teve que montar uma equipe de
00:17:57.240 desenvolvimento para vir e corrigir ali
00:17:59.120 o backend que o antigo City tinha
00:18:00.520 deixado. E aí ele contratou um Dev
00:18:02.120 Senior para ser o braço direito dele.
00:18:03.720 Bom, logicamente não fui eu. Eu nunca
00:18:05.440 trabalhei numa empresa assim, tá? Essa
00:18:06.720 história é totalmente fictícia. Mas é é
00:18:08.840 loucura, né? Quando você menos espera,
00:18:10.440 essas coisas acontecem com você, mas não
00:18:12.360 acontecem comigo. Tá?
