# cfcoach

A personal practice coach for Codeforces and LeetCode. It reads your submission history,
shows where you fail, and builds a short plan of problems at your level. Python standard
library only; no accounts or API keys.

## Use

```
cfcoach                  analyse and build a 25-problem plan (Codeforces + LeetCode)
cfcoach --cf-only        the same, Codeforces problems only
cfcoach --lc-sync        first download your full LeetCode submission history
cfcoach --tags "dp,greedy" --total 20
cfcoach --lc NAME        set the LeetCode username ("-" forgets it)
```

At the topics prompt, Enter takes the focus topics: the ones that are common at your
rating and cost you the most failed attempts.

## How problems are chosen

- Codeforces: unsolved problems at your target rating that are really about the topic (no
  other technique tagged on them). Problems on the CP-31 sheet come first, then the
  most-solved recent ones.
- LeetCode: unsolved NeetCode 150 / Striver A2Z problems of the topic, then contest
  problems rated near your level.
- Problems you tried and never solved come back as upsolves.

The sheet lists live in `cfcoach_sheets.py`.

## Install or update

Run this in this folder after any change to the code:

```
python -m pip install .
```

The `cfcoach` command itself is `cfcoach.exe` in `%USERPROFILE%\.local\bin`. It was copied
there once from `%APPDATA%\Python\Python314\Scripts` because that folder is not on PATH.
On a new machine, do the same copy after the first install.

## Where your data lives

`%USERPROFILE%\cfcoach` holds the plans (`plan_<handle>.md`), the remembered accounts, the
synced LeetCode history (`leetcode_<name>.json`) and a cache. Deleting it loses nothing that
cannot be fetched again, except ticks you made in a plan file.

`--lc-sync` needs your `LEETCODE_SESSION` cookie. It is sent to leetcode.com only and is
never written to disk. It is a login token: do not share it.
