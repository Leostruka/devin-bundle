# Capture status: HtsFKx9mAu8

Status: **BLOCKED — captions unavailable through verified endpoints**

## Verified metadata

| Field | Value | Source |
|---|---|---|
| Video ID | `HtsFKx9mAu8` | Input URL and YouTube oEmbed |
| Title | The bitter lesson | YouTube oEmbed |
| Author | Matt Pocock | YouTube oEmbed |
| Canonical URL | https://www.youtube.com/watch?v=HtsFKx9mAu8 | YouTube oEmbed request |
| Capture date | 2026-08-29 | Session date |

## Caption checks

1. The YouTube watch page returned navigation/legal content without transcript data.
2. `https://www.youtube.com/api/timedtext?type=list&v=HtsFKx9mAu8` returned an empty response.
3. `https://www.youtube.com/api/timedtext?v=HtsFKx9mAu8&lang=en` returned an empty response.
4. `youtube-transcript-api` is not installed locally.
5. `yt-dlp` is not installed locally.

No package was installed and no unverified transcript provider was used.

## Analysis gate

The plan requires available captions before structure or analysis. Because no transcript was captured:

- No transcript artifact was fabricated.
- No timestamped quotation was produced.
- No thesis, recommendation, or implication was inferred from the title.
- Structured extraction was not executed.
- Critical analysis remains blocked.

## Classification

**INCONCLUSIVE.** Metadata is verified, but the transcript precondition is unmet. This is the required fail-closed outcome from the plan.

## Sources

- Video: https://youtu.be/HtsFKx9mAu8?si=tJXCXVETxMVwBrdO
- YouTube oEmbed: https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=HtsFKx9mAu8&format=json
- YouTube timed text list: https://www.youtube.com/api/timedtext?type=list&v=HtsFKx9mAu8
- YouTube English timed text: https://www.youtube.com/api/timedtext?v=HtsFKx9mAu8&lang=en
