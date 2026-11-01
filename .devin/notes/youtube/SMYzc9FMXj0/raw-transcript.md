# Raw transcript: SMYzc9FMXj0 (whisper.cpp ggml-base, lang=en)

> Local ASR by `extensions/asr/transcribe.py` on the yt-dlp audio track.
> Segments: 188. sha256(text)=235fab5e12f8ca0b

[0.0s - 3.2s] Imagine asking an AI to write a short summary.
[3.2s - 7.2s] It produces the first word, then the next, then the next.
[7.2s - 9.9s] Each word depends on what came before it.
[9.9s - 13.0s] That step-by-step process is how most language models
[13.0s - 14.9s] generate text.
[14.9s - 17.1s] Now imagine a different approach.
[17.1s - 19.9s] First, sketch the shape of the whole answer,
[19.9s - 23.4s] then fill in the details in a handful of passes.
[23.4s - 27.6s] That's the idea behind next concept modeling, or Ncm,
[27.6s - 31.3s] a text generation method from Stanford's hazy research team.
[31.3s - 34.5s] In the team's paper, Ncm matches a diffusion model's
[34.5s - 40.0s] summary quality on one benchmark while running up to 31 times faster.
[40.0s - 43.6s] That number is real, but it's easy to misunderstand.
[43.6s - 46.7s] The comparison is against a diffusion language model,
[46.7s - 50.6s] not chat GPT or a standard word-by-word model.
[50.6s - 54.3s] And Ncm is a research system, not a ready-made replacement
[54.3s - 56.8s] for the chatbot's most people use.
[56.8s - 59.4s] So what is Ncm doing differently?
[59.4s - 61.3s] Where does the speed up come from?
[61.3s - 65.7s] And what can the papers results tell us about the future of text generation?
[65.7s - 69.2s] Let's start with the bottleneck Ncm is trying to change.
[69.2s - 73.1s] Most large language models use auto-regressive generation.
[73.1s - 76.2s] Auto-regressive means each new token is predicted
[76.2s - 78.4s] using the tokens that came before it.
[78.4s - 82.9s] The model writes the first token, then uses that token to predict the second.
[82.9s - 86.5s] It adds the second token to the context, predicts the third,
[86.5s - 88.0s] and continues.
[88.0s - 91.3s] That gives the model a clear order for constructing a sentence,
[91.3s - 95.3s] but it also means the next step must wait for the current one.
[95.3s - 100.1s] As the answer gets longer, the model repeats that process again and again.
[100.1s - 104.0s] Even if the GPU can perform a lot of calculations in parallel,
[104.0s - 108.4s] the generation sequence still has to move forward one token at a time.
[108.4s - 111.8s] One reason this can be slow is that during generation,
[111.8s - 116.3s] the model has to repeatedly work with its parameters and the growing context.
[116.3s - 120.4s] The exact bottleneck depends on the model, hardware, and serving setup,
[120.4s - 124.7s] but the sequential nature of token generation is one important limit.
[124.7s - 128.8s] Researchers have explored ways to generate multiple positions at once.
[128.8s - 131.2s] Diffusion language models are one approach.
[131.2s - 134.8s] They begin with a sequence of masked or incomplete positions
[134.8s - 137.4s] and refine them over several passes.
[137.4s - 138.9s] But there's a trade-off.
[138.9s - 141.9s] Fewer refinement passes can mean worse quality,
[141.9s - 145.7s] while each pass may process a large part of the sequence again.
[145.7s - 148.3s] NCM tries a different strategy.
[148.3s - 152.5s] Generate a structured representation from course to fine.
[152.5s - 157.6s] NCM is not a new kind of transformer that has replaced transformers altogether.
[157.6s - 161.9s] It uses a transformer, but changes what the transformer predicts
[161.9s - 164.4s] and the order in which it predicts it.
[164.4s - 167.1s] Instead of predicting the next word in a sentence,
[167.1s - 170.8s] NCM predicts discrete codes arranged in levels.
[170.8s - 174.1s] The first levels give a course representation of the text.
[174.1s - 178.0s] Later levels add information that was missing from the earlier ones.
[178.0s - 180.7s] A useful analogy is drawing a picture.
[180.7s - 182.9s] You might first block in the large shapes,
[182.9s - 185.3s] then add smaller shapes and shading,
[185.3s - 187.6s] then finish with fine details.
[187.6s - 192.8s] You don't need to decide the exact position of every eyelash before you know where the face is.
[192.8s - 197.4s] NCM aims to give a model a similar way to organize text generation.
[197.4s - 200.9s] It creates a rough representation of the whole sequence first,
[200.9s - 203.5s] then adds detail and stages.
[203.5s - 209.2s] The word "concept" can make this sound like the model is writing abstract ideas before words.
[209.2s - 211.6s] That's not quite what the paper means.
[211.6s - 216.9s] In NCM, a concept is a code in a learned multi-scale representation.
[216.9s - 220.9s] The codes are intended to capture information at different levels of detail.
[220.9s - 224.1s] They aren't necessarily human readable ideas or sentences.
[224.1s - 227.6s] NCM has two main components.
[227.6s - 231.2s] A multi-scale tokenizer and a transformer generator.
[231.2s - 236.1s] The tokenizer is based on a multi-scale residual VQ VAE.
[236.1s - 241.8s] In plain language, it learns to represent a passage of text as a stack of discrete codes.
[241.8s - 244.4s] The first level is short and coarse.
[244.4s - 249.5s] Each later level contains more positions and adds information that earlier levels missed.
[249.5s - 252.5s] The final level reaches the full sequence length.
[252.5s - 256.0s] When the codes are combined and decoded, they reconstruct text.
[256.0s - 259.1s] Training then happens in two stages.
[259.7s - 264.4s] Stage one, teach the tokenizer to encode and reconstruct text.
[264.4s - 268.4s] The tokenizer learns to turn text into a hierarchy of codes,
[268.4s - 271.2s] then decode those codes back into text.
[271.2s - 276.5s] The goal is for the hierarchy to retain enough information that the final reconstruction is accurate.
[276.5s - 281.2s] Stage two, train the generator to predict those codes.
[281.2s - 286.5s] The tokenizer is frozen and a transformer learns to generate its levels in order.
[286.5s - 290.4s] At each level, it predicts all the codes at that level in parallel,
[290.4s - 293.4s] conditioned on the information represented by the earlier levels.
[293.4s - 300.3s] At generation time, the tokenizer's decoder turns the completed representation back into text.
[300.3s - 304.4s] That means the model doesn't write a finished paragraph during its first pass.
[304.4s - 307.9s] It builds the representation that will eventually decode into one.
[307.9s - 313.2s] Both NCM and diffusion models generate text through multiple passes.
[313.2s - 316.2s] The difference is what happens during those passes.
[316.2s - 320.4s] A diffusion language model typically revisits a sequence as it refines it.
[320.4s - 326.1s] Depending on the method, each pass may process many or all of the output positions.
[326.1s - 329.4s] NCM generates a sequence of levels.
[329.4s - 334.0s] Early levels contain fewer positions. Later levels contain more.
[334.0s - 337.1s] It predicts a level and moves on to the next one.
[337.1s - 341.2s] It doesn't repeatedly revise the entire sequence in the same way.
[341.2s - 343.5s] Here's the short version.
[343.5s - 350.8s] Diffusion repeatedly refines a sequence, while NCM predicts a hierarchy of increasingly detailed representations.
[350.8s - 357.3s] That difference helps explain why NCM can use fewer function evaluations or NFEs.
[357.3s - 361.3s] An NFE is one model evaluation during generation.
[361.3s - 365.9s] But counting evaluations alone doesn't tell us how long a method will take.
[365.9s - 370.5s] One pass may be more expensive than another and implementations differ.
[371.0s - 374.4s] The paper therefore also reports wall clock comparisons.
[374.4s - 378.0s] The idea is not that every NCM passes free.
[378.0s - 382.8s] It's that the early passes can be cheaper because they operate on shorter levels.
[382.8s - 388.2s] The 31 times figure comes from the paper's ex-sum summarization experiment.
[388.2s - 394.6s] The researchers generated summaries using NCM and a diffusion baseline called Aurora LM.
[395.2s - 402.0s] They report that NCM achieved comparable Rouge L quality while running 31 times faster in their measured setup.
[402.0s - 411.2s] The benchmark generated 1,024 sequences at a batch size of 16 on a single NVIDIA H100SX NGPU.
[411.2s - 413.2s] That's an important result.
[413.2s - 415.8s] It is also a specific result.
[415.8s - 420.6s] It does not mean that NCM is 31 times faster than ChatGPT.
[420.6s - 424.9s] It does not mean every NCM task runs 31 times faster.
[425.3s - 431.2s] And it does not establish that NCM is faster than standard auto regressive models on every workload.
[431.2s - 438.0s] The comparison is between NCM and a diffusion language model on a particular summarization benchmark
[438.0s - 440.2s] using the author's experimental setup.
[440.2s - 442.7s] The paper reports other results too.
[442.7s - 451.1s] On the LM1B language modeling benchmark, NCM achieved better generative perplexity than the strongest diffusion baseline
[451.1s - 457.6s] while running 21 times faster. On open web text, the author's report that NCM was competitive
[457.6s - 461.5s] with the strongest diffusion baseline while running 10 times faster.
[461.5s - 467.3s] These comparisons are evidence that the approach can be efficient on several research tasks.
[467.3s - 469.5s] They're not a universal speed guarantee.
[469.5s - 473.6s] One of the most striking results in the paper is Sudoku.
[473.6s - 480.7s] Sudoku has global constraints. A number placed in one square affects what can go in many other squares.
[481.2s - 484.8s] A method that commits to individual output positions in order
[484.8s - 488.3s] may find that earlier choices make later choices difficult.
[488.3s - 493.1s] NCM's course-to-find process gives it a different generation structure.
[493.1s - 498.0s] It can build a representation of the whole puzzle solution across levels
[498.0s - 501.0s] rather than producing one final answer from left to right.
[501.0s - 507.6s] In the paper's Sudoku experiments, NCM outperformed the auto regressive and diffusion baselines
[507.6s - 513.1s] across the tested difficulty levels while using fewer function evaluations than the compared methods.
[513.1s - 519.1s] That result is interesting because it shows the method isn't only about generating fluid sentences.
[519.1s - 525.1s] The authors are also testing whether a hierarchy of representations can help with structured tasks
[525.1s - 527.4s] that require a globally consistent answer.
[527.4s - 533.6s] But Sudoku is a controlled benchmark. Strong performance there doesn't automatically mean
[533.6s - 538.7s] NCM will reason better across the broad range of tasks people give general-purpose assistance.
[538.7s - 544.5s] The paper also evaluates German to English translation using WMT14.
[544.5s - 548.4s] Here, a single headline number wouldn't tell the whole story.
[548.4s - 552.4s] Translation quality is assessed with metrics such as blue,
[552.4s - 556.8s] and results depend on the model, decoding strategy, and evaluation setup.
[556.8s - 562.5s] The authors report that NCM can improve its output using minimum Bayes risk decoding,
[562.5s - 569.4s] or MBR. In simplified terms, the system generates multiple candidate translations and selects one
[569.4s - 574.9s] based on how well it agrees with the others. Generating candidates and comparing them costs
[574.9s - 579.3s] additional compute. That makes this a useful example of a broader point.
[579.3s - 584.7s] Fast generation can be paired with extra inference time work to improve quality,
[584.7s - 589.9s] but that work still has a cost. When you see a result for a new generation method,
[589.9s - 593.6s] check both the quality measure and the inference budget used to obtain it.
[593.6s - 598.8s] NCM is a promising research direction, but several questions remain.
[598.8s - 605.8s] Scale is an open question. The paper studies generators up to 725 million parameters
[605.8s - 611.1s] in its scaling experiments. That is enough to investigate the method, but it doesn't establish
[611.1s - 615.5s] how NCM will behave at the sizes of today's largest deployed language models.
[616.1s - 621.8s] The authors report that scaling improved quality in their experiments, but testing much larger systems
[621.8s - 629.4s] is still necessary. The output format is structured and bounded. NCM generates through a defined hierarchy,
[629.4s - 635.1s] and the experiments use task-specific configurations. That's different from demonstrating a flexible
[635.1s - 640.8s] assistant that can smoothly answer with one sentence, then a page, then a longer report in the same
[640.8s - 647.8s] general-purpose system. Results are benchmark-specific. A speed-up on summarization does not tell us the
[647.8s - 654.8s] speed-up for translation, chat, code, or long-form writing. Each task has different quality requirements
[654.8s - 660.9s] and computational costs. Reconstruction quality matters. The tokenizer must preserve
[660.9s - 666.5s] the information needed to recover the original text. If details are lost in the representation,
[666.5s - 672.0s] the generator can't reliably restore them later. This is especially important for names,
[672.0s - 678.4s] numbers, and other exact details. And finally, the comparison depends on the bass lines and setup.
[678.4s - 684.4s] Wall-clock performance can change with batch size, sequence length, hardware, and software
[684.4s - 689.8s] implementation. A compelling research result should be replicated and tested on the workloads people
[689.8s - 696.4s] actually care about. Can you download and run NCM? The situation is more nuanced than the
[696.4s - 702.6s] attached article's 5-byte file section suggests. There are now published NCM checkpoints on hugging
[702.6s - 710.3s] face for tasks including X-Sum, WMT-14 German to English, Sudoku, Tiny Stories, and LM-1B.
[710.3s - 717.1s] The same checkpoint listing marks open webtext as pending. So it would be misleading to say that no
[717.1s - 722.5s] NCM models are downloadable. But a downloadable research checkpoint isn't the same thing as a
[722.5s - 729.4s] convenient general-purpose chatbot. The released models are organized around specific tasks and datasets.
[729.4s - 733.7s] You'll need to follow the project's code and configuration to run the relevant model,
[733.7s - 738.8s] and the checkpoints don't establish that there's a drop-in NCM assistant that the breadth and tooling
[738.8s - 745.6s] of a current general-purpose LLM. The right takeaway is, some research checkpoints are available,
[745.6s - 755.2s] but that does not make NCM a ready-made chat GPT replacement. Is NCM still an LLM? Yes. NCM changes the
[755.2s - 761.6s] generation procedure and representation, but it still uses a transformer to model and generate text.
[761.6s - 769.6s] So the claim that NCM ends LLMs misunderstands the result. NCM is better understood as an alternative
[769.6s - 775.2s] approach to text generation within the broader language model research landscape. It challenges
[775.2s - 781.2s] a familiar assumption that text must always be generated one token at a time from left to right.
[781.2s - 787.6s] It doesn't show that autoregressive models are obsolete or that every future assistant will use NCM.
[787.6s - 795.4s] What developers should take away? There are three practical lessons here. First, the 31-times speedup
[795.4s - 801.8s] is a meaningful research result, but it applies to a specific comparison. NCM versus a diffusion
[801.8s - 808.9s] baseline on X-SUM summarization under the author's reported setup. Second, the method's central idea
[808.9s - 815.6s] is course-to-find generation. A model predicts a short, low-detail representation first then adds
[815.6s - 821.6s] progressively finer levels. This offers a different way to trade off generation speed, compute,
[821.6s - 828.4s] and output quality. Third, the most useful next step is independent testing. If you're evaluating
[828.4s - 834.1s] NCM for a real application, compare it with your current baseline on the same hardware at the same
[834.1s - 839.6s] batch size and with the same quality checks. Include the outputs that are hardest to get right,
[839.6s - 846.3s] such as numbers, names, and long responses. NCM doesn't settle the future of language models.
[846.3s - 851.8s] It gives researchers a new way to study how text can be generated, and a strong set of results
[851.8s - 857.1s] worth investigating further. If you found this video helpful, please like and subscribe for more
[857.1s - 862.2s] clear breakdowns of the latest AI research. And let me know in the comments. Do you think
[862.2s - 868.2s] course-to-find generation could become a practical alternative for everyday AI tools? Thanks for watching!
