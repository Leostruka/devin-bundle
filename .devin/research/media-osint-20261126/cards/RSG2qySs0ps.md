# Card: RSG2qySs0ps - TypeScript Parameters utility type

URL: https://www.youtube.com/shorts/RSG2qySs0ps | channel: Matt Pocock | date: 20250601

VISUAL: `frames/RSG2qySs0ps_01.jpg`/`_02.jpg` show VS Code with library function `funcFromALibrary(a: string, b: number, extractMePlease: {d: boolean; e: string[]})`. The author applies `Parameters<typeof funcFromALibrary>` producing a tuple, then indexes `[2]`, `[0]`, `[1]` to extract object/string/number types. Captions exist at `captions_raw/RSG2qySs0ps.en.vtt`.

CITED: TypeScript `Parameters` utility type; library authors failing to export useful types; wrapper components/functions.

CLAIMS: `Parameters<typeof fn>` yields a tuple of function parameter types and tuple indexing extracts individual parameter types. This is observed in the editor and is standard TypeScript behavior. No market/performance claims.

PAIN-VOCAB: "not exporting all of the types"; "you don't control this code"; "extract out a type from a function you don't control" (`transcript_digest.md` lines 225-240).

BUNDLE-RELEVANCE: Small, concrete addition for `typescript-node`: utility-type extraction patterns (`Parameters`, `ReturnType`, `Awaited`, tuple indexing) when dependency types are not exported. Low effort, high educational value; no architectural impact.

EVIDENCE-QUALITY: observed=5 self-reported=0 unverified=0
