#!/usr/bin/env python3
"""cfcoach - analyse a Codeforces handle (and optionally a LeetCode account) and build a
short, targeted practice plan.

Standard library only. Uses the free public Codeforces API and LeetCode's public GraphQL.
    cfcoach [handle] [--lc USER] [--lc-sync] [--cf-only] [--tags "dp,greedy"] [--total 25]
Plans are saved to the "plan" folder on the Desktop as a shuffled list of bare links. Remembered accounts, the synced LeetCode
history and the cache live in ~/cfcoach.

LeetCode only publishes per-topic solve counts, the contest rating and the last 20 accepted
problems. --lc-sync downloads your whole submission history with your own login cookie
(asked for with hidden input, or read from the LEETCODE_SESSION environment variable). The
cookie is sent to leetcode.com only and never stored; the history is kept on disk.
"""
import argparse
import getpass
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from types import SimpleNamespace

from cfcoach_sheets import CP31, NEETCODE, STRIVER

API = "https://codeforces.com/api/"
LC_GRAPHQL = "https://leetcode.com/graphql"
LC_STATUS = "https://leetcode.com/api/problems/all/"
LC_SUBMISSIONS = "https://leetcode.com/api/submissions/?offset={}&limit=20"
LC_PAUSE = 2      # seconds between history pages; LeetCode rate-limits this endpoint
LC_URL = "https://leetcode.com/problems/{}/"
# Elo-style difficulty of every LeetCode contest problem, computed from contest results
LC_RATINGS = "https://raw.githubusercontent.com/zerotrac/leetcode_problem_rating/main/ratings.txt"
LC_OFFSET = 350   # without a LeetCode contest rating, assume it is this much above Codeforces
LC_RECENT = 200   # contest picks come from the newest N problems of a topic
LC_COVERED = 25   # this many LeetCode solves in a topic: assume the sheet classics are done
LC_MEDIUM, LC_HARD = 1300, 1800  # LeetCode ratings from which Mediums / Hards are the right size
SHEET_MAX = 2000  # above this target the interview sheets are too easy to be worth a slot
RECENT = 1600     # contest ids from about late 2021 on: problems in today's contest style
SHRINK = 8        # a tag's failure rate counts in full only once it has about this many problems
HOME = Path.home() / "cfcoach"  # remembered accounts, synced LeetCode history, cache
CACHE = HOME / ".cache"
LC_NAMES = HOME / "leetcode.json"  # Codeforces handle -> LeetCode username
DAY = 86400
BAD = (OSError, ValueError, KeyError, TypeError, IndexError)  # network or malformed reply
IGNORED = {None, "TESTING", "SKIPPED", "COMPILATION_ERROR"}
SHORT = {"WRONG_ANSWER": "WA", "TIME_LIMIT_EXCEEDED": "TLE", "MEMORY_LIMIT_EXCEEDED": "MLE",
         "RUNTIME_ERROR": "RE", "IDLENESS_LIMIT_EXCEEDED": "ILE", "CHALLENGED": "HACKED",
         "PRESENTATION_ERROR": "PE", "PARTIAL": "PARTIAL", "OUTPUT_LIMIT_EXCEEDED": "OLE"}
LC_VERDICT = {"Accepted": "OK", "Compile Error": "COMPILATION_ERROR"}  # others: upper snake case
DIFFICULTIES = ("Easy", "Medium", "Hard")
# Codeforces tag -> LeetCode topics (tags without a good match get Codeforces problems only)
LC_TAG = {
    "dp": {"dynamic-programming", "memoization"}, "greedy": {"greedy"}, "binary search": {"binary-search"},
    "two pointers": {"two-pointers", "sliding-window"},
    "graphs": {"graph", "breadth-first-search", "topological-sort"},
    "dfs and similar": {"depth-first-search", "breadth-first-search"},
    "shortest paths": {"shortest-path"}, "trees": {"tree", "binary-tree", "binary-search-tree"},
    "dsu": {"union-find"}, "math": {"math"}, "number theory": {"number-theory"},
    "strings": {"string"}, "hashing": {"hash-table", "rolling-hash", "hash-function"},
    "string suffix structures": {"string-matching", "suffix-array"},
    "implementation": {"simulation", "matrix"}, "brute force": {"enumeration", "backtracking"},
    "sortings": {"sorting"},
    "data structures": {"stack", "queue", "heap-priority-queue", "monotonic-stack",
                        "monotonic-queue", "segment-tree", "binary-indexed-tree", "trie",
                        "ordered-set"},
    "bitmasks": {"bit-manipulation", "bitmask"}, "combinatorics": {"combinatorics"},
    "geometry": {"geometry"}, "games": {"game-theory"},
    "divide and conquer": {"divide-and-conquer", "merge-sort"},
    "probabilities": {"probability-and-statistics"}, "interactive": {"interactive"},
}
# Codeforces tags that describe a problem's flavour rather than a technique it needs
LIGHT = {"greedy", "math", "implementation", "brute force", "constructive algorithms", "sortings",
         "strings"}
# techniques that are part of a topic rather than a different one
FAMILY = {"math": {"number theory", "combinatorics", "geometry", "probabilities"},
          "graphs": {"dfs and similar", "shortest paths", "trees", "dsu"},
          "dfs and similar": {"graphs", "trees"}, "trees": {"graphs", "dfs and similar"},
          "shortest paths": {"graphs"}, "dsu": {"graphs"}}
# LeetCode topics that rule a Codeforces tag out: a BFS over a binary tree is no graph problem
LC_NOT = {"graphs": {"tree", "binary-tree"}}
SHEETS = [("NC", "NeetCode 150", NEETCODE), ("A2Z", "Striver A2Z", STRIVER)]
LC_CATALOG_QUERY = "{ allQuestions { questionFrontendId title titleSlug difficulty isPaidOnly" \
                   " topicTags { slug } } }"
LC_USER_QUERY = """query q($u: String!) {
  matchedUser(username: $u) {
    username
    submitStatsGlobal {
      acSubmissionNum { difficulty count submissions }
      totalSubmissionNum { difficulty submissions }
    }
    tagProblemCounts {
      advanced { tagSlug problemsSolved }
      intermediate { tagSlug problemsSolved }
      fundamental { tagSlug problemsSolved }
    }
  }
  userContestRanking(username: $u) { attendedContestsCount rating topPercentage }
  recentAcSubmissionList(username: $u, limit: 20) { titleSlug }
}"""
COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ

_last_call = 0.0


def c(text, code):
    return f"\033[{code}m{text}\033[0m" if COLOR else str(text)


def bold(t): return c(t, "1")
def dim(t): return c(t, "2")
def red(t): return c(t, "31")
def cyan(t): return c(t, "36")


# ---------------------------------------------------------------- network

class NoRedirect(urllib.request.HTTPRedirectHandler):
    """urllib copies every header, cookies included, to wherever a redirect points.
    Refusing redirects keeps the login cookie on the address it was meant for."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_no_redirect = urllib.request.build_opener(NoRedirect)


def fetch(url, body=None, cookie=None):
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://leetcode.com/"}
    if cookie:
        headers["Cookie"] = cookie
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    send = _no_redirect.open if cookie else urllib.request.urlopen
    with send(req, timeout=60) as r:
        return r.read().decode("utf-8")


def fresh(path, ttl):
    return path.exists() and time.time() - path.stat().st_mtime < ttl


def cached(name, ttl, load):
    """Text from load(), cached on disk. A stale copy beats nothing when the network fails."""
    path = CACHE / name
    if not fresh(path, ttl):
        try:
            path.write_text(load(), encoding="utf-8")
        except BAD:
            if not path.exists():
                raise
    return path.read_text(encoding="utf-8")


def api(method, cache_ttl=0, **params):
    """Call the Codeforces API (max 1 request / 2s), optionally caching on disk."""
    global _last_call
    cache = CACHE / f"{method}.json"
    if cache_ttl and fresh(cache, cache_ttl):
        return json.loads(cache.read_text(encoding="utf-8"))

    url = API + method + ("?" + urllib.parse.urlencode(params) if params else "")
    err = "unknown error"
    for attempt in range(4):
        time.sleep(max(0.0, 2.0 - (time.time() - _last_call)))
        _last_call = time.time()
        try:
            data = json.loads(fetch(url))
            if data.get("status") == "OK":
                if cache_ttl:
                    cache.write_text(json.dumps(data["result"]), encoding="utf-8")
                return data["result"]
            err = data.get("comment", err)
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read()).get("comment", str(e))
            except ValueError:
                err = str(e)
            if e.code == 400:  # bad handle etc. - retrying will not help
                break
        except (OSError, ValueError) as e:
            err = str(e)
        time.sleep(2 * attempt)
    sys.exit(red(f"Codeforces API failed ({method}): {err}"))


# ---------------------------------------------------------------- LeetCode

def sheet_index():
    """slug -> {"where": {sheet label: position}, "tags": Codeforces tags its section trains}."""
    index = {}
    for label, _, sections in SHEETS:
        pos = 0
        for _, cf_tags, slugs in sections:
            for slug in slugs.split():
                e = index.setdefault(slug, {"where": {}, "tags": set(), "mixed": False})
                e["where"].setdefault(label, pos)
                e["mixed"] |= cf_tags == "*"
                e["tags"].update(t for t in cf_tags.split(",") if t and t != "*")
                pos += 1
    return index


SHEET = sheet_index()
SHEET_TAGS = set().union(*(e["tags"] for e in SHEET.values()))


def lc_ratings():
    """LeetCode problem id -> contest difficulty rating. Empty if unavailable."""
    try:
        text = cached("lc_ratings.txt", 7 * DAY, lambda: fetch(LC_RATINGS))
        rows = (line.split("\t") for line in text.splitlines()[1:])
        return {r[1]: float(r[0]) for r in rows if len(r) > 1}
    except BAD:
        return {}


def lc_catalog():
    """Every LeetCode problem with its topics. Empty if LeetCode is unreachable."""
    def load():
        text = fetch(LC_GRAPHQL, {"query": LC_CATALOG_QUERY})
        json.loads(text)["data"]["allQuestions"][0]  # refuse to cache an error reply
        return text
    try:
        qs = json.loads(cached("lc_catalog.json", 7 * DAY, load))["data"]["allQuestions"]
        return [dict(q, tags={t["slug"] for t in q["topicTags"] or []}) for q in qs]
    except BAD:
        return []


def lc_names():
    try:
        return json.loads(LC_NAMES.read_text(encoding="utf-8"))
    except BAD:
        return {}


def history_path(name):
    return HOME / f"leetcode_{name.lower()}.json"


def lc_history(name):
    """The synced submission history of a LeetCode account, or None.
    {"complete": bool, "synced": time, "submissions": [[id, slug, status, time], ...]}"""
    try:
        data = json.loads(history_path(name).read_text(encoding="utf-8"))
        data["complete"], data["synced"], data["submissions"]
        return data
    except BAD:
        return None


def ask_session():
    print(bold("\nLeetCode shows your full submission history only to you, so a login cookie is needed:"))
    print("  1. Open leetcode.com in your browser, logged in, and press F12.")
    print("  2. Application tab (Storage in Firefox) > Cookies > https://leetcode.com")
    print("  3. Copy the Value of LEETCODE_SESSION and paste it here.")
    print(dim("  It goes to leetcode.com only and is not saved. It is a login token: never share it."))
    raw = getpass.getpass("LEETCODE_SESSION (hidden, then Enter): ")
    found = re.search(r"LEETCODE_SESSION=([^;\s]+)", raw)
    return (found.group(1) if found else raw).strip().strip("\"'")


def lc_page(offset, cookie):
    """One page (20) of the cookie owner's submission history, or an error string."""
    try:
        page = json.loads(fetch(LC_SUBMISSIONS.format(offset), cookie=cookie))
        return page if "submissions_dump" in page else str(page.get("detail", page))[:200]
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code} {e.read()[:200].decode('utf-8', 'replace')}"
    except BAD as e:
        return str(e) or type(e).__name__


def lc_sync(session):
    """Download the cookie owner's whole submission history to disk; returns their username.
    Later syncs only read the pages that are new."""
    cookie = "LEETCODE_SESSION=" + session
    try:
        name = json.loads(fetch(LC_STATUS, cookie=cookie))["user_name"]
    except BAD:
        name = ""
    if not name:
        print(red("LeetCode did not accept that cookie (expired, or not copied in full); "
                  "continuing with public data."))
        return None
    old = lc_history(name) or {"complete": False, "submissions": []}
    subs = {s[0]: s for s in old["submissions"]}
    offset, pause, complete, error = 0, LC_PAUSE, False, ""
    while True:
        if sys.stdout.isatty():
            print(dim(f"\r  Syncing LeetCode history of {name}: {offset} submissions read..."),
                  end="", flush=True)
        page = lc_page(offset, cookie)
        for attempt in range(1, 5):  # rate-limited: back off, then go slower for the rest
            if not isinstance(page, str):
                break
            pause = 5
            time.sleep(10 * attempt)
            page = lc_page(offset, cookie)
        if isinstance(page, str):
            complete, error = old["complete"] and offset == 0, page
            break
        dump = page["submissions_dump"]
        known = any(d["id"] in subs for d in dump)
        for d in dump:
            subs[d["id"]] = [d["id"], d["title_slug"], d["status_display"], d["timestamp"]]
        offset += 20
        if not dump or not page.get("has_next") or (old["complete"] and known):
            complete = True
            break
        time.sleep(pause)
    data = {"user": name, "complete": complete, "synced": int(time.time()),
            "submissions": sorted(subs.values(), key=lambda d: d[3])}
    history_path(name).write_text(json.dumps(data), encoding="utf-8")
    new = len(subs) - len(old["submissions"])
    print(("\r" if sys.stdout.isatty() else "")
          + f"  LeetCode history of {name}: {len(subs)} submissions ({new} new).".ljust(70))
    if error:
        print(red(f"  LeetCode stopped answering at submission {offset}: {error}\n"
                  "  What arrived is saved; run cfcoach --lc-sync again to finish."))
    return name


def lc_analyze(history, catalog, ratings):
    """Per-problem records of a synced history, shaped like analyze()'s, tagged with the
    Codeforces tags that match each problem's LeetCode topics."""
    by_slug = {q["titleSlug"]: q for q in catalog}
    subs = []
    for _, slug, status, when in history["submissions"]:
        q = by_slug.get(slug)
        if not q:
            continue
        p = {"contestId": "lc:", "index": slug, "name": q["title"],
             "tags": sorted(cf_tags(q["tags"]))}
        if q["questionFrontendId"] in ratings:
            p["rating"] = ratings[q["questionFrontendId"]]
        subs.append({"creationTimeSeconds": when, "problem": p, "author": {},
                     "verdict": LC_VERDICT.get(status) or status.upper().replace(" ", "_")})
    return analyze(subs)


def lc_user(username, catalog, ratings):
    """A LeetCode account's public profile, plus its full history when one has been synced."""
    try:
        body = {"query": LC_USER_QUERY, "variables": {"u": username}}
        data = json.loads(fetch(LC_GRAPHQL, body))["data"]
        user = data["matchedUser"]
        stats = user["submitStatsGlobal"]
        ac = {d["difficulty"]: d for d in stats["acSubmissionNum"]}
        sent = sum(d["submissions"] for d in stats["totalSubmissionNum"] if d["difficulty"] == "All")
        solved = {d: ac[d]["count"] for d in ("All", *DIFFICULTIES)}
        accepted = 100 * ac["All"]["submissions"] // sent if sent else None
        tags = {t["tagSlug"]: t["problemsSolved"]
                for group in user["tagProblemCounts"].values() for t in group}
    except BAD:
        return None
    contest = data.get("userContestRanking") or {}
    done = {s["titleSlug"] for s in data.get("recentAcSubmissionList") or []}
    history = lc_history(user["username"])
    try:
        probs = lc_analyze(history, catalog, ratings) if history else {}
        last = {}  # slug -> time of the latest submission
        for _, slug, _, when in history["submissions"] if history else []:
            last[slug] = max(when, last.get(slug, 0))
    except BAD:
        history, probs, last = None, {}, {}
    done |= {st["p"]["index"] for st in probs.values() if st["solved"]}
    failed = {st["p"]["index"]: last[st["p"]["index"]] for st in probs.values() if not st["solved"]}
    return {"name": user["username"], "solved": solved, "accepted": accepted, "tags": tags,
            "rating": contest.get("rating"), "contests": contest.get("attendedContestsCount", 0),
            "top": contest.get("topPercentage"), "done": done, "failed": failed, "probs": probs,
            "history": history, "exact": bool(history and history["complete"])}


def cf_tags(topics):
    """The Codeforces tags that a LeetCode problem with these topics counts toward."""
    return {tag for tag, want in LC_TAG.items()
            if topics & want and not topics & LC_NOT.get(tag, set())}


def lc_count(tag, lc):
    """Problems solved on LeetCode in the topics matching a Codeforces tag, or None."""
    topics = LC_TAG.get(tag)
    return max(lc["tags"].get(t, 0) for t in topics) if topics else None


def lc_item(q):
    return (q["title"], LC_URL.format(q["titleSlug"]))


def sheet_picks(tag, target, k, free, used):
    """Unsolved NeetCode 150 / Striver A2Z classics on the topic, most canonical first.
    target is on LeetCode's rating scale and decides which difficulties are worth a slot."""
    if k <= 0:
        return []
    order = ["Easy", "Medium"] if target < LC_MEDIUM else ["Medium"] if target < LC_HARD \
        else ["Hard", "Medium"]
    cand = []
    for q in free:
        e = SHEET.get(q["titleSlug"])
        if not e or q["difficulty"] not in order or q["titleSlug"] in used:
            continue
        # the sheets' own sections decide the topic; LeetCode's topics only fill the gaps
        topical = tag in cf_tags(q["tags"])
        if tag in e["tags"] or (topical and (e["mixed"] or tag not in SHEET_TAGS)):
            # fitting difficulty first, then problems on both sheets, then sheet order
            key = (order.index(q["difficulty"]), -len(e["where"]), min(e["where"].values()))
            cand.append((key, q))
    take = [q for _, q in sorted(cand, key=lambda x: x[0])[:k]]
    used.update(q["titleSlug"] for q in take)
    return [lc_item(q) for q in take]


def contest_picks(target, k, pool, ratings, used):
    """Recent LeetCode contest problems on the topic, rated closest to the target."""
    def num(q):
        return int(q["questionFrontendId"]) if q["questionFrontendId"].isdigit() else 0

    def rating(q):
        return ratings[q["questionFrontendId"]]

    recent = sorted(pool, key=num, reverse=True)[:LC_RECENT]
    rated = [q for q in recent if q["questionFrontendId"] in ratings and q["titleSlug"] not in used]
    take = sorted(rated, key=lambda q: abs(rating(q) - target))[:max(0, k)]
    used.update(q["titleSlug"] for q in take)
    return [lc_item(q) for q in take]


# ---------------------------------------------------------------- analysis

def pid(p):
    return f"{p.get('contestId', p.get('problemsetName', ''))}{p['index']}"


def url(p):
    cid = p.get("contestId")
    if cid is None:
        return "https://codeforces.com/problemsets/acmsguru"
    if cid >= 100000:
        return f"https://codeforces.com/gym/{cid}/problem/{p['index']}"
    return f"https://codeforces.com/problemset/problem/{cid}/{p['index']}"


def round100(x):
    return int(min(3500, max(800, round(x / 100) * 100)))


def analyze(subs):
    """Collapse submissions into one record per problem. Wrong = failures before first AC."""
    probs = {}
    for s in sorted(subs, key=lambda s: s["creationTimeSeconds"]):
        v = s.get("verdict")
        if v in IGNORED:
            continue
        st = probs.setdefault(pid(s["problem"]), {
            "p": s["problem"], "solved": False, "wrong": 0, "verdicts": Counter(),
            "live": False, "live_solved": False})
        live = s["author"].get("participantType") in ("CONTESTANT", "OUT_OF_COMPETITION")
        st["live"] |= live
        if v == "OK":
            st["solved"] = True
            st["live_solved"] |= live
        elif not st["solved"]:
            st["wrong"] += 1
            st["verdicts"][v] += 1
    return probs


def tag_stats(probs):
    tags = defaultdict(lambda: {"solved": 0, "unsolved": 0, "wrong": 0, "first": 0,
                                "ratings": [], "verdicts": Counter(), "live_fail": 0})
    for st in probs.values():
        for t in st["p"].get("tags", []):
            if t.startswith("*"):
                continue
            g = tags[t]
            g["solved" if st["solved"] else "unsolved"] += 1
            g["wrong"] += st["wrong"]
            g["verdicts"] += st["verdicts"]
            g["first"] += st["solved"] and st["wrong"] == 0
            g["live_fail"] += st["live"] and not st["live_solved"]
            if st["solved"] and "rating" in st["p"]:
                g["ratings"].append(st["p"]["rating"])
    for g in tags.values():
        g["tried"] = g["solved"] + g["unsolved"]
        top = sorted(g["ratings"])[-3:]
        g["level"] = sum(top) / len(top) if len(top) == 3 else None
        # failed attempts per problem, with never-solved problems counted double
        g["struggle"] = (g["wrong"] + 2 * g["unsolved"]) / g["tried"]
    return dict(tags)


def profile(info, history, probs):
    solved = [st for st in probs.values() if st["solved"]]
    rated = [st["p"]["rating"] for st in solved if "rating" in st["p"]]
    live_ok = [st["p"]["rating"] for st in solved if st["live_solved"] and "rating" in st["p"]]
    live_fail = [st for st in probs.values() if st["live"] and not st["live_solved"]]
    trend = sum(h["newRating"] - h["oldRating"] for h in history[-5:])
    rating = info.get("rating")
    base = rating if rating else (median(rated) if rated else 800)
    if trend <= -75:  # on a losing streak: consolidate one step lower
        base -= 100
    return {
        "rating": rating, "max": info.get("maxRating"), "rank": info.get("rank", "unrated"),
        "contests": len(history), "trend": trend, "solved": len(solved),
        "live_median": median(live_ok) if live_ok else None,
        "live_fail": len(live_fail), "upsolved": sum(st["solved"] for st in live_fail),
        "verdicts": sum((st["verdicts"] for st in probs.values()), Counter()),
        "base": round100(base),
    }


# ---------------------------------------------------------------- plan

def tag_center(tag, tags, base):
    """Target rating for a topic: halfway between the user's level and their best solves
    there, but at most one step above their level - a few hard solves are outliers."""
    g = tags.get(tag)
    if g is None or g["level"] is None:
        return round100(base - 200)
    return round100(min(base + 100, max(base - 200, (base + g["level"]) / 2)))


def tag_share(problems, base):
    """How often each tag appears in recent problems around the user's level."""
    lo, hi = max(800, base - 100), base + 300
    band = [p for p in problems
            if lo <= p.get("rating", 0) <= hi and p.get("contestId", 0) >= RECENT]
    count = Counter(t for p in band for t in p["tags"] if not t.startswith("*"))
    return {t: n / len(band) for t, n in count.items()}, lo, hi


def build_topic(tag, center, n, c):
    """n problems for one topic, as (name, link) pairs: sheet classics, LeetCode contest
    problems, upsolves, then Codeforces problems below, at and above the target rating."""
    def rank(p):
        """Best first: problems that are really about this topic (no other technique tagged
        on them), then problems on the CP-31 sheet, then the most widely solved."""
        other_technique = any(t != tag and t not in LIGHT and t not in FAMILY.get(tag, ())
                              for t in p["tags"])
        return (other_technique, pid(p) not in CP31, -c.popularity.get(pid(p), 0))

    def pick(lo, hi, k):
        lo, hi = max(800, lo), max(800, hi)
        cand = [p for p in c.problems
                if tag in p["tags"] and lo <= p.get("rating", 0) <= hi
                and pid(p) not in c.probs and pid(p) not in c.used
                and p["name"] not in c.solved_names and p["name"] not in c.used
                and not any(t.startswith("*") for t in p["tags"])]
        # outside the sheet, prefer problems in today's contest style
        pool = [p for p in cand if pid(p) in CP31 or p.get("contestId", 0) >= RECENT]
        take = []
        for p in sorted(pool if len(pool) >= k else cand, key=rank):
            # a problem shared by two parallel contests has two ids, one name
            if len(take) < k and p["name"] not in {q["name"] for q in take}:
                take.append(p)
        c.used.update(pid(p) for p in take)
        c.used.update(p["name"] for p in take)
        return [(p["name"], url(p)) for p in take]

    free = [q for q in c.catalog if not q["isPaidOnly"]
            and q["titleSlug"] not in c.done and q["titleSlug"] not in c.used]
    pool = [q for q in free if tag in cf_tags(q["tags"])]
    k = min(3, n // 6)  # LeetCode slots besides the classics
    target = c.lc_base + center - c.base  # the same step up or down, on LeetCode's scale
    # LeetCode problems the user tried and never solved come before new ones
    retry = [q for q in pool if q["titleSlug"] in c.failed
             and (q["difficulty"] != "Hard" or target >= LC_HARD)]
    retry = sorted(retry, key=lambda q: -c.failed[q["titleSlug"]])[:k]
    c.used.update(q["titleSlug"] for q in retry)
    # plenty of LeetCode solves here but no way to see which: do not re-suggest the classics
    covered = c.lc and not c.lc["exact"] and (lc_count(tag, c.lc) or 0) >= LC_COVERED
    if covered and center < SHEET_MAX and c.catalog:
        print(dim(f"  {tag}: {lc_count(tag, c.lc)} LeetCode solves here, so sheet classics are "
                  "skipped (run cfcoach --lc-sync to pick only unsolved ones)."))
    classics = [] if covered or center >= SHEET_MAX else sheet_picks(tag, target, n // 3, free, c.used)
    contest = contest_picks(target, k - len(retry), pool, c.ratings, c.used)

    # unfinished problems within reach, nearest to the target first
    reach = [st["p"] for st in c.probs.values()
             if not st["solved"] and tag in st["p"].get("tags", [])
             and st["p"]["name"] not in c.solved_names and pid(st["p"]) not in c.used
             and center - 300 <= st["p"].get("rating", 0) <= center + 200]
    reach = sorted(reach, key=lambda p: abs(p["rating"] - center))[:n // 5]
    c.used.update(pid(p) for p in reach)

    rest = n - len(classics) - len(contest) - len(reach) - len(retry)
    side = rest // 4
    return (classics + contest + [(p["name"], url(p)) for p in reach] + [lc_item(q) for q in retry]
            + pick(center - 200, center - 100, side)       # warm-up
            + pick(center, center + 100, rest - 2 * side)  # core
            + pick(center + 200, center + 300, side))      # stretch


# ---------------------------------------------------------------- output

def fail_line(verdicts):
    total = sum(verdicts.values())
    parts = [f"{SHORT.get(v, v)} {100 * n // total}%" for v, n in verdicts.most_common(3)]
    return "  failed submissions: " + ", ".join(parts)


def show_profile(handle, pr):
    print()
    print(bold("Codeforces " + handle), dim(f"({pr['rank']})"))
    if pr["rating"]:
        sign = "+" if pr["trend"] >= 0 else ""
        print(f"  rating {bold(pr['rating'])} (max {pr['max']})   contests {pr['contests']}"
              f"   last 5: {sign}{pr['trend']}")
    line = f"  solved {pr['solved']}"
    if pr["live_median"]:
        line += f"   typical in-contest solve: {int(pr['live_median'])}"
    if pr["live_fail"]:
        pct = 100 * pr["upsolved"] // pr["live_fail"]
        line += f"   failed in contest: {pr['live_fail']}, upsolved {pct}%"
    print(line)
    if pr["verdicts"]:
        print(fail_line(pr["verdicts"]))
    print(f"  practice level used for the plan: {bold(pr['base'])}")


def show_lc(lc, lc_base):
    s = lc["solved"]
    print()
    print(bold("LeetCode " + lc["name"]))
    line = f"  solved {s['All']} (Easy {s['Easy']}, Medium {s['Medium']}, Hard {s['Hard']})"
    if lc["accepted"] is not None:
        line += f"   accepted {lc['accepted']}% of submissions"
    print(line)
    if lc["rating"]:
        print(f"  contest rating {bold(round(lc['rating']))} (top {lc['top']}%)"
              f"   contests {lc['contests']}")
    h = lc["history"]
    if h:
        unsolved = sum(not st["solved"] for st in lc["probs"].values())
        day = time.strftime("%Y-%m-%d", time.localtime(h["synced"]))
        print(f"  full history (synced {day}): {len(h['submissions'])} submissions on "
              f"{len(lc['probs'])} problems   tried but never solved: {unsolved}")
        verdicts = sum((st["verdicts"] for st in lc["probs"].values()), Counter())
        if verdicts:
            print(fail_line(verdicts))
        for label, name, _ in SHEETS:
            on = [slug for slug, e in SHEET.items() if label in e["where"]]
            print(f"  {name}: {sum(slug in lc['done'] for slug in on)}/{len(on)} done")
        if not h["complete"]:
            print(red("  The last sync was cut short, so this history has gaps; "
                      "run cfcoach --lc-sync again."))
    else:
        print(dim("  LeetCode publishes only your last 20 solves. Run cfcoach --lc-sync to load "
                  "your full submission history."))
    print(f"  LeetCode rating used for the plan: {bold(lc_base)}")


def show_tags(rows, tags, focus, lc=None, title=None, note="", freq=None):
    print()
    if title:
        print(bold(title))
    head = f"{'#':>3}  {'tag':<26}{'solved':>7}{'unsolved':>9}{'wrong':>7}{'wrong/prob':>11}" \
           f"{'1st try':>9}{'level':>7}" + (f"{'freq':>6}" if freq else "") \
           + (f"{'LC':>5}" if lc else "") + "  top fail"
    print(bold(head))
    print(dim("-" * len(head)))
    for i, t in enumerate(rows, 1):
        g = tags.get(t)
        mark = "   <- focus" if t in focus else ""
        if g is None:  # nothing submitted in this topic on this site
            line = f"{i:>3}  {t:<26}{'-':>7}"
            print(red(line + mark) if mark else dim(line))
            continue
        first = f"{100 * g['first'] // g['tried']}%"
        level = str(round100(g["level"])) if g["level"] else "-"
        fail = SHORT.get(g["verdicts"].most_common(1)[0][0], "?") if g["verdicts"] else "-"
        line = f"{i:>3}  {t:<26}{g['solved']:>7}{g['unsolved']:>9}{g['wrong']:>7}" \
               f"{g['wrong'] / g['tried']:>11.2f}{first:>9}{level:>7}"
        if freq:
            line += f"{round(100 * freq.get(t, 0)):>5}%"
        if lc:
            n = lc_count(t, lc)
            line += f"{'-' if n is None else n:>5}"
        line += f"  {fail}"
        print(red(line + mark) if mark else line)
    print(dim("wrong = failed submissions before first AC.  level = avg of your 3 hardest solves"
              + note + "." + ("  LC = solved on LeetCode in that topic." if lc else "")))


def pick_tags(rows, all_tags, focus, preset, total):
    while True:
        raw = preset if preset is not None else input(
            bold("\nTopics to practice") + f" (numbers or names, comma-separated; Enter = the focus topics)."
            f"\n{total} problems are split across them: ")
        chosen, bad = [], []
        for tok in (x.strip().lower() for x in raw.split(",")):
            if tok.isdigit() and 1 <= int(tok) <= len(rows):
                chosen.append(rows[int(tok) - 1])
            elif tok in all_tags:
                chosen.append(tok)
            elif tok:
                bad.append(tok)
        if not raw.strip():
            return focus
        if chosen and not bad:
            return list(dict.fromkeys(chosen))
        print(red("Not recognised: " + ", ".join(bad or ["(nothing)"])))
        if preset is not None:
            sys.exit(1)


def render(handle, pr, items):
    """Print the plan and return the file's text: bare links only, one per line, in random
    order, so that nothing gives away a problem's topic or rating before it is solved."""
    random.shuffle(items)
    md = [link for _, link in items]
    print("\n" + bold(f"{len(items)} problems in random order; names, topics and ratings are hidden on purpose"))
    for link in md:
        print("  " + link)
    tips = ["Give each problem up to 45 minutes. If you are stuck, read the editorial and write "
            "the solution yourself.",
            "After every failed submission, write one line on why it failed before fixing it.",
            "On Codeforces, untick Settings > General > \"Show tags for unsolved problems\", or "
            "each problem page shows its topic and rating.",
            "Re-run this tool when you finish: solved problems drop out and levels update."]
    if pr["live_fail"] and pr["upsolved"] * 2 < pr["live_fail"]:
        tips.insert(0, "You upsolve under half of what you fail in contests. After each contest, "
                       "solve the first problem you could not.")
    print("\n" + bold("How to use this"))
    for t in tips:
        print("  - " + t)
    return "\n".join(md) + "\n"


# ---------------------------------------------------------------- main

def desktop():
    """The user's Desktop folder. Windows can relocate it (into OneDrive, for example)."""
    try:
        import winreg
        key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            return Path(os.path.expandvars(winreg.QueryValueEx(k, "Desktop")[0]))
    except (ImportError, OSError):
        return Path.home() / "Desktop"


def run():
    ap = argparse.ArgumentParser(description="Codeforces practice coach")
    ap.add_argument("handle", nargs="?")
    ap.add_argument("--lc", metavar="NAME", help='LeetCode username to analyse too ("-" to forget it)')
    ap.add_argument("--lc-sync", action="store_true",
                    help="download your full LeetCode submission history (asks for your login cookie)")
    ap.add_argument("--cf-only", action="store_true",
                    help="plan with Codeforces problems only (no LeetCode or sheet problems)")
    ap.add_argument("--tags", help='comma-separated tags, skips the prompt (e.g. "dp,greedy")')
    ap.add_argument("--total", type=int, default=25, help="problems in the whole plan (default 25)")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.system("")  # enables ANSI colours on Windows consoles

    CACHE.mkdir(parents=True, exist_ok=True)
    saved = HOME / "handle.txt"
    last = saved.read_text(encoding="utf-8").strip() if saved.exists() else ""
    hint = f" [{last}]" if last else ""
    handle = args.handle or input(f"Codeforces handle{hint}: ").strip() or last
    print(dim("Fetching your Codeforces history..."))
    found = api("user.info", handles=handle)
    if not found:
        sys.exit(red(f"No Codeforces user named {handle!r}"))
    info = found[0]
    handle = info["handle"]
    saved.write_text(handle, encoding="utf-8")
    subs = api("user.status", handle=handle)
    history = api("user.rating", handle=handle)
    problemset = api("problemset.problems", cache_ttl=DAY)
    problems = problemset["problems"]
    popularity = {pid(s): s["solvedCount"] for s in problemset["problemStatistics"]}

    probs = analyze(subs)
    tags = tag_stats(probs)
    pr = profile(info, history, probs)
    show_profile(handle, pr)

    names = lc_names()
    session = os.environ.get("LEETCODE_SESSION") or (ask_session() if args.lc_sync else "")
    name = lc_sync(session) if session else None  # the cookie knows whose account it is
    if name is None:
        name = args.lc if args.lc is not None else names.get(handle)
    if name is None and not args.handle:
        name = input("LeetCode username (Enter to skip; add later with --lc NAME): ").strip()
    name = "" if name == "-" else name
    print(dim("Fetching LeetCode data..."))
    catalog, ratings = lc_catalog(), lc_ratings()
    lc = lc_user(name, catalog, ratings) if name else None
    if name and not lc:
        print(red(f"LeetCode user {name!r} not found (or LeetCode unreachable); continuing without it."))
    elif name is not None and names.get(handle) != name:
        LC_NAMES.write_text(json.dumps({**names, handle: name}), encoding="utf-8")
    if not catalog:
        print(dim("LeetCode is unreachable; the plan will use Codeforces only."))
    rated = lc and lc["rating"] and lc["contests"] >= 3
    lc_base = round(lc["rating"]) if rated else pr["base"] + LC_OFFSET
    if lc:
        show_lc(lc, lc_base)

    # with a synced LeetCode history, both sites count
    lc_tags = tag_stats(lc["probs"]) if lc else {}
    both = tag_stats({**probs, **lc["probs"]}) if lc_tags else tags
    everything = list({**probs, **(lc["probs"] if lc else {})}.values())
    mean = sum(st["wrong"] + 2 * (not st["solved"]) for st in everything) / max(1, len(everything))
    share, lo, hi = tag_share(problems, pr["base"])

    def priority(t):
        """Failed attempts per problem, pulled toward the user's average while the sample is
        small, times how often the tag comes up at the user's level."""
        g = both.get(t) or {"wrong": 0, "unsolved": 0, "tried": 0}
        failing = (g["wrong"] + 2 * g["unsolved"] + SHRINK * (mean or 1)) / (g["tried"] + SHRINK)
        return failing * share.get(t, 0)

    def order(t):
        g = tags.get(t) or lc_tags.get(t)
        return (t not in tags, -(g["wrong"] if g else -1), t)

    rows = sorted(set(both) | {t for t, f in share.items() if f >= 0.1}, key=order)
    focus = sorted(rows, key=priority, reverse=True)[:3]
    if both:
        show_tags(rows, tags, focus, None if lc_tags else lc, "Codeforces" if lc_tags else None,
                  freq=share)
        print(dim(f"freq = share of recent problems rated {lo}-{hi} with that tag.  "
                  "focus = common at your level and costing you failed attempts."))
        hot = [t for t in sorted(tags, key=lambda t: -tags[t]["live_fail"])[:3] if tags[t]["live_fail"]]
        if hot:
            print("Most failed during contests: " + ", ".join(hot))
        if lc_tags:
            show_tags(rows, lc_tags, focus, title="LeetCode, grouped by the matching Codeforces topic",
                      note=" (LeetCode contest scale)")
            print(dim("focus is judged on both sites together.  LeetCode topics with no Codeforces "
                      "counterpart (plain arrays, linked lists, SQL) are left out."))
    else:
        print("\nNo judged submissions yet - starting you on the basics.")

    all_tags = {t for p in problems for t in p["tags"] if not t.startswith("*")}
    total = max(1, args.total)
    chosen = pick_tags(rows, all_tags, focus, args.tags, total)[:total]

    print(dim("Picking problems..."))
    ctx = SimpleNamespace(
        problems=problems, popularity=popularity, probs=probs, used=set(),
        solved_names={st["p"]["name"] for st in probs.values() if st["solved"]},
        catalog=[] if args.cf_only else catalog, ratings=ratings, lc=lc, done=lc["done"] if lc else set(),
        failed=lc["failed"] if lc else {},
        base=pr["base"], lc_base=lc_base)
    centers = {t: tag_center(t, tags, pr["base"]) for t in chosen}
    plan = []
    for i, t in enumerate(sorted(chosen, key=lambda t: centers[t])):  # easiest target first
        share = total // len(chosen) + (i < total % len(chosen))
        plan += build_topic(t, centers[t], share, ctx)

    folder = desktop() / "plan"
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"plan_{handle}.md"
    out.write_text(render(handle, pr, plan), encoding="utf-8")
    print(f"\nSaved checklist to {bold(out)}")


def main():
    try:
        run()
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
