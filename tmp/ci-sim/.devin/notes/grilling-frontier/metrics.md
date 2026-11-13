# Grilling frontier round simulation

| fixture | behavior | turns | covered | omitted | blocked | total |
|---|---|---|---|---|---|---|
| independent.json | old: whole frontier | 0 | 0 ([]) | 6 (['A', 'B', 'C', 'D', 'E', 'F']) | True | 6 |
| independent.json | new: chunk at 4 | 2 | 6 (['A', 'B', 'C', 'D', 'E', 'F']) | 0 ([]) | False | 6 |
| dependent.json | old: whole frontier | 6 | 6 (['A', 'B', 'C', 'D', 'E', 'F']) | 0 ([]) | False | 6 |
| dependent.json | new: chunk at 4 | 6 | 6 (['A', 'B', 'C', 'D', 'E', 'F']) | 0 ([]) | False | 6 |
| mixed.json | old: whole frontier | 0 | 0 ([]) | 7 (['A', 'B', 'C', 'D', 'E', 'F', 'G']) | True | 7 |
| mixed.json | new: chunk at 4 | 2 | 7 (['A', 'B', 'C', 'D', 'E', 'F', 'G']) | 0 ([]) | False | 7 |
