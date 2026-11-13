# Raw transcript: 1kQ_1_QL5Es (whisper.cpp ggml-base, lang=pt)

> Local ASR by `extensions/asr/transcribe.py` on the yt-dlp audio track
> (EN source video; ASR rendered pt-flavored text -- names mangled).
> Segments: 154. sha256(text)=2665402f006ad623

[0.0s - 5.3s] Microsoft built a tool que fixa o seu token usage e é o nome de token economizor.
[5.3s - 8.4s] E, interestingly, esse tool faz o melhor do que usar.
[8.4s - 10.6s] Então, ele saiu mais tokens em dia.
[10.6s - 13.5s] Ele pode encontrar esses saívings em place que você nunca pensou.
[13.5s - 16.5s] Ainda que você já usa outras tools para salvar tokens.
[16.5s - 24.8s] Mas o nosso token não era um capo que não expectamos. Então, nós changemos o seu mesmo para mudar o capo. E, quando testamos como essa tool se ajudou ao actualizar,
[24.8s - 27.0s] ele saiu mais de um pouco de tokens.
[27.0s - 31.5s] Se esse é o primeiro tempo, estamos com o seu companheiro software e esse é o nosso canal AI Labs.
[31.5s - 39.2s] E, em este vídeo, vamos mostrar como o token economizor custa o seu token usage, como usar ele e usar ele e como fixar o problema.
[39.2s - 44.4s] Agora, o token economizor é um token que faz o seu agente usar mais tokens em cada casco.
[44.4s - 49.2s] Once you install it, every session you run in a project cost less than it would without it,
[49.2s - 51.2s] and you don't have to change the way you work.
[51.2s - 54.9s] Now, you might think there are already a lot of tools that save tokens.
[54.9s - 58.2s] We've covered a few of them on our channel, too, and graphed as one of them.
[58.2s - 59.7s] So, why would you need another one?
[59.7s - 64.4s] Graphed and a lot of other tools make a map of all the files in your project before you start.
[64.4s - 70.0s] That way, when the agent needs something, it can find it right away instead of wasting tokens looking for it.
[70.0s - 75.3s] But token economizer works a little differently, instead of making a map, it learns from how you work.
[75.3s - 81.3s] It watches every session, and the commands your agent runs in it, and it keeps track of where tokens are being wasted.
[81.3s - 84.3s] Then, it cuts that waste out of the sessions that come after.
[84.3s - 89.3s] Now, Microsoft also shared all the results from their own tests, along with the data behind them.
[89.3s - 94.9s] They gave the agent 277 real bugs to fix from six real projects on GitHub,
[94.9s - 98.2s] and they had it fix each project's bugs one after another.
[98.2s - 103.5s] They did that on five different setups across Claude code, Codex, and GitHub co-pilot.
[103.5s - 107.5s] On every one of those setups, the tasks cost less with the tool than without it.
[107.5s - 115.5s] On Claude code, Sonnet 5 costs 23.6% less, and Opus 4.8 costs 30.9% less.
[115.5s - 118.2s] And this tool didn't affect the performance of any model.
[118.2s - 123.0s] Sonnet actually fixed one more bug out of every 100 than it did without the tool,
[123.0s - 127.1s] because with fewer tokens in every message, it could stay focused on the task.
[127.1s - 132.0s] But before we move forward, it would be great if you subscribe to the channel and hit the "hi" button.
[132.0s - 135.2s] This small gesture of support goes a long way for us.
[135.2s - 139.5s] But before we install token economizer, let's understand how it actually works.
[139.5s - 146.1s] And to see how this tool actually reduce your token usage, you first need to understand what's actually using up the tokens.
[146.1s - 151.3s] Every time you message your agent, it sends a request to the model that generates the answers for you.
[151.3s - 153.5s] But it doesn't just send your prompt to the model.
[153.5s - 159.8s] Since models don't remember things on their own, you also need to send them extra context about everything in your project.
[159.8s - 167.1s] So every request carries the instructions, the agent always follows, and the list of every tool it can use to work on your project.
[167.1s - 172.6s] It also carries the MCP tools and skills you've added along with the whole conversation up to that point.
[172.6s - 178.6s] But when you keep working on the same project, a lot of the context being sent to the model is stuff it doesn't even need.
[178.6s - 181.5s] All of that stays in the context and waste tokens.
[181.5s - 184.2s] Your agent also wastes tokens on mistakes.
[184.2s - 191.4s] It fixes a mistake in one session, but the next time you run it in the same project, it has to learn the same thing again by failing at it.
[191.4s - 194.7s] On top of that, it carries around tools it never even uses.
[194.7s - 198.8s] Token economizer finds these places where your agent wastes tokens.
[198.8s - 203.2s] It watches the sessions you've opened in that project, and it fixes three things in them.
[203.2s - 210.3s] The first one is the mistakes Claude keeps making again and again in your project, like running a tool or a command that doesn't work.
[210.3s - 214.1s] Claude doesn't remember what worked and what didn't from one session to the next.
[214.1s - 219.8s] So every time, it'll try the same command that didn't work and then spend tokens trying to fix the same mistake.
[219.8s - 223.3s] This is where the tool helps, because it looks out for mistakes like this.
[223.3s - 228.9s] When it sees Claude making the same mistake multiple times, it writes it down as a fact about your project.
[228.9s - 231.1s] These facts are called micro skills.
[231.1s - 235.7s] Once a few more sessions confirm that a fact is right, the tool saves it for that project.
[235.7s - 241.8s] Whenever you start a new session, it gives the agent that information is something it already knows to be true about your work.
[241.8s - 246.0s] That way your agent already knows this didn't work before, so it doesn't try it again.
[246.0s - 248.2s] The second one is the tools you never use.
[248.2s - 251.0s] Claude loads a lot of tools into every session.
[251.0s - 257.4s] If one of them doesn't get used across 10 of your messages over at least two sessions, the tool turns it off for that project.
[257.4s - 259.9s] That way it stops getting sent with every message.
[259.9s - 268.3s] Microsoft's own numbers show this one saves the most tokens, because it reduces the tools that are being sent at each turn, but it does this without asking you.
[268.3s - 276.3s] So you won't even know it took a tool out of your context window, but there's a command that shows you the tools it turned off and will show you that command later in the video.
[276.3s - 278.2s] The third one is when Claude gets stuck.
[278.2s - 283.7s] Sometimes an agent works on a task and can't find a way to do it, so it keeps trying things that don't work.
[283.7s - 289.8s] And sometimes it keeps going for way longer than Claude usually takes to answer one of your messages in that project.
[289.8s - 293.8s] When the tool sees this, it asks a model to check if Claude is really stuck.
[293.8s - 299.1s] Only if it is, the tool tells Claude wants to try something different, so it doesn't stay stuck in a loop.
[299.1s - 303.5s] If Claude is still stuck after that, the tool tells you to press escape and stop it.
[303.5s - 305.4s] It never stops Claude by itself.
[305.4s - 318.7s] But before we install it, let's have a word by our sponsor, Data Impulse. We had Claude code build a tool to check where our site ranks in other countries and Google blocked it almost immediately, because every request came from the same place.
[318.7s - 323.0s] A VPN wouldn't help here because we needed multiple countries in real volume.
[323.0s - 325.1s] That's where Data Impulse comes in.
[325.1s - 334.6s] It's a proxy network with 90 million plus IPs across 195 countries, and the dashboard shows how many are live in each one before you pick.
[334.6s - 340.9s] We pointed our tool at it, and the agent could search from the US, Germany, and Japan, like someone sitting there.
[340.9s - 345.0s] Nothing got blocked, and we had real rankings for every country in minutes.
[345.0s - 347.6s] You can hold the same IP for up to two hours.
[347.6s - 353.5s] You only pay for the traffic you buy, and it never expires, and residential proxies are $1 per gigabyte.
[353.5s - 357.3s] When something breaks, you get actual people on support 24/7.
[357.3s - 360.8s] We've been running our own builds on it for a while, and it just works.
[360.8s - 366.4s] You can grab the $1 per gigabyte deal at dataimpulse.com, the links in the description.
[366.4s - 371.8s] Now, this tool is actually a plugin that's available for Claude code X and a few other AI agents.
[371.8s - 377.4s] And to install this tool, you just need to go to their GitHub repo and scroll down to the install section.
[377.4s - 380.1s] The install commands for all the agents are listed there.
[380.1s - 386.4s] So you can just copy the command for the agent you're using and paste it into your terminal, and it will be installed for you.
[386.4s - 391.4s] When you open Claude code and run the plugin command, you'll see token economizer in your list.
[391.4s - 393.2s] It adds a few commands and hooks.
[393.2s - 397.9s] The hooks run on their own at set times, like when a session starts or when you send a message.
[397.9s - 403.1s] These hooks are how the plugin runs the three things we went through earlier without you having to do anything.
[403.1s - 408.2s] The microskills we talked about get handed to Claude by a hook that runs at the start of every session.
[408.2s - 410.9s] So Claude already has all the facts for your project.
[410.9s - 415.5s] While Claude is working on your prompt, another hook checks on it after every tool it uses,
[415.5s - 418.7s] and that's how the plugin knows when Claude is stuck and needs a push.
[418.7s - 424.0s] And once the session ends, the plugin looks back over everything that happened in it, all on its own.
[424.0s - 429.0s] That's where it learns new facts for next time and keeps count of the tools that never got used.
[429.0s - 434.5s] Now, once you've installed this tool and run its config command, you'll see that most of its features are turned on,
[434.5s - 437.5s] but microskills are turned off when you first install it.
[437.5s - 449.3s] Microskills are off for two reasons. The first reason is to save your limit. Once it's on, every three sessions it asks a model to read through your recent sessions and write the facts, and that uses some of your own limit.
[449.3s - 455.0s] And the second reason is safety. The facts it writes come from whatever the commands in your project print out,
[455.0s - 460.1s] and Claude reads them at the start of every session as if they were true facts about your project.
[460.1s - 465.7s] So if you download a project from someone else, whoever made it could hide instructions in what its commands print.
[465.7s - 472.3s] Those instructions would end up in the facts, and Claude would treat them as true in every session unless you change them yourself.
[472.3s - 477.6s] This is basically what's known as a prompt injection. That's why Microsoft leaves the choice to you.
[477.6s - 483.8s] But for your own projects, you should turn it on, because in Microsoft's tests, it was the feature that saved a lot of tokens.
[483.8s - 490.3s] So if you want to turn on microskills, you need to run the token economizer config command and set microskills to on.
[490.3s - 493.0s] And that way, you'll be able to use this feature.
[493.0s - 500.1s] But even with microskills turned on, there's one problem with this tool. As we said earlier, it learns from the way you use your agent.
[500.1s - 505.6s] So when you first install it, it hasn't learned anything yet, which means it won't save you anything at first.
[505.6s - 509.1s] To see results, you'd have to use it on the same project for a while.
[509.1s - 515.9s] And that's true, even for projects you've already been working on for a long time, because if you install it now, it has nothing to learn from.
[515.9s - 521.4s] So you have to wait before it starts paying off, and at first it can even cost you more while it's still learning.
[521.4s - 528.3s] In Microsoft's own tests, almost every project cost more with the plugin at first, and only got cheaper by the sixth task.
[528.3s - 535.7s] And this happens in every single project, because the plugin learns each project on its own, and nothing carries over from one to the next.
[535.7s - 543.5s] But Cloud Code already saves all your sessions in the main.cloud folder for 30 days, so you can use those past sessions to fix this.
[543.5s - 547.5s] So to fix the problem, you just need to ask Cloud Code to change the tool.
[547.5s - 560.3s] We gave it the repo and asked it to change the tool, so that when it starts, instead of starting from a blank state with no memory of what happened before, it goes through the session history that Cloud stores in the main.cloud folder first.
[560.3s - 564.0s] It should use that as the starting point, instead of starting from scratch.
[564.0s - 568.7s] If you want to make this change yourself, you can pause here and copy the prompt from the screen.
[568.7s - 575.3s] When you give it that prompt, it will start working on the changes in the repo, and once it's done, the tool will be ready for use.
[575.3s - 585.4s] It changed the repo so that when you open the first session after installing this version, it starts a task that runs in the background, and goes through the sessions you've run before in the same folder.
[585.4s - 590.5s] Then it keeps everything it learned from those sessions as its starting point, instead of starting blank.
[590.5s - 594.7s] If Cloud didn't install it for use everywhere, ask Cloud to make that change.
[594.7s - 599.6s] Once it's done, all your projects can benefit from the context saved from previous sessions.
[599.6s - 608.0s] This won't do anything for a brand new project, because there's no history to read, but for the projects you're already working on, it means the plugin doesn't start from zero.
[608.0s - 613.6s] So to see if it actually saves anything, we installed our change version and used it on a demo project.
[613.6s - 616.7s] This tool comes with a few commands that show you what it's doing.
[616.7s - 618.5s] The first one is the status command.
[618.5s - 623.2s] This is the command you run whenever you want to know what the plugin is doing in the project you're in.
[623.2s - 630.1s] It shows how many sessions it has learned from, how many tokens those sessions used, and what each of its features has done so far.
[630.1s - 638.7s] In our project, it had already learned from four sessions, and the stuck check hadn't needed to step in once, but it already had a long list of tools it could turn off.
[638.7s - 644.2s] The status command also shows how many microskills facts it's handing Cloud at the start of every session.
[644.2s - 649.1s] So to see what it's actually telling Cloud for your project, you need to run the microskills command.
[649.1s - 654.7s] It lists the facts the plugin hands Cloud at the start of every session, and the ones it's still checking.
[654.7s - 660.1s] The status command also lists the tools the plugin is turning off, but it only gives you their names.
[660.1s - 663.7s] So to see why each tool is on that list, you run the toolprune command.
[663.7s - 671.3s] It lists every tool it's turning off in that project, and next to each one, it shows how many sessions and messages went by without that tool being used.
[671.3s - 678.9s] On our project, 276 tools had gone unused across all four sessions, and since the plugin turns them off without telling you,
[678.9s - 683.7s] this command is the place to check whenever Cloud suddenly can't do something it used to do.
[683.7s - 690.0s] But a long list of tools doesn't tell you how much it actually saves you, so that's what the toolprune measure command is for.
[690.0s - 696.0s] It counts how many tokens every message takes with all your tools, and how many it takes with only the ones you use.
[696.0s - 706.7s] On our project, every message went from about 34,300 tokens down to about 24,400, which is about 29% less on every single message.
[706.7s - 709.4s] But what if Claude needs one of those tools later?
[709.4s - 717.8s] A tool the plugin turned off stays off in that project, so you can just run the toolprune restore command with the name of the tool, and it gives that tool back.
[717.8s - 721.3s] And once you've given a tool back, the plugin won't turn it off again.
[721.3s - 727.5s] When we tested it on another app, we first ran five sessions on it with the plugin on, so that it had something to learn from.
[727.5s - 730.6s] In those sessions, it turned off 303 tools.
[730.6s - 739.2s] Then we gave Claude three new tasks on that app and ran each one twice, once with the plugin and once without. Both runs started from the exact same code.
[739.2s - 743.3s] Without the plugin, Claude took 99 steps to finish all three tasks.
[743.3s - 748.4s] With the plugin, it took 79 steps, and the whole thing cost about 21% less.
[748.4s - 750.7s] Both versions also passed the same checks.
[750.7s - 756.3s] So in the first sessions, when the plugin hadn't learned anything yet, it cost a little more than a session without it.
[756.3s - 763.1s] The saving started showing up in later sessions once it had learned something, so you're going to see more of a difference as you keep using it.
[763.1s - 768.5s] Now, if you want to use the changed and refined tool, you can get it on AI Labs Pro, which is our community.
[768.5s - 774.8s] So if you found value in what we do and want to support the channel, this is the best way to do it, the links in the description.
[774.8s - 776.6s] That brings us to the end of this video.
[776.6s - 783.1s] If you'd like to support the channel and help us keep making videos like this, you can do so by using the super thanks button below.
[783.1s - 786.1s] Thank you for watching and I will see you in the next one.
