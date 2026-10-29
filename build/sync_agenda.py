#!/usr/bin/env python3
"""Compare the official [un]prompted agenda with build/planner-data.json and report what changed.

Usage:
  python3 build/sync_agenda.py                      download the live agenda and workshops pages
  python3 build/sync_agenda.py AGENDA.html WS.html  use saved copies of the two pages
  add --save-json DIR                               also write the parsed agenda.json and workshops.json

This script only reports. Applying a change is a decision (see "Keeping the agenda in sync" in the
README): a replaced talk gets a new id so saved picks fall back to the suggestion, a moved talk keeps
its id, and new sessions need tags and highlights before build.py accepts them.

Python 3, no dependencies.
"""
import html
import json
import pathlib
import re
import sys
import urllib.request
from html.parser import HTMLParser

HERE = pathlib.Path(__file__).resolve().parent
AGENDA_URL = "https://unpromptedcon.org/agenda-10-2026/"
WORKSHOPS_URL = "https://unpromptedcon.org/workshops/"
UA = "Mozilla/5.0 (unprompted2-planner sync; +https://github.com/pfortuna/unprompted2-planner)"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


# ---------- HTML to text ----------

class _MD(HTMLParser):
    """Minimal HTML to Markdown for the site's WordPress/Divi markup."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.href, self.depth = [], None, 0

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "div", "tr"): self.out.append("\n\n")
        elif tag == "br": self.out.append("\n")
        elif tag in ("strong", "b"): self.out.append("**")
        elif tag in ("em", "i"): self.out.append("*")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"): self.out.append("\n\n**")
        elif tag == "ul": self.depth += 1; self.out.append("\n")
        elif tag == "li": self.out.append("\n" + "  " * (self.depth - 1) + "- ")
        elif tag == "a": self.href = dict(attrs).get("href"); self.out.append("[")

    def handle_endtag(self, tag):
        if tag in ("strong", "b"): self.out.append("**")
        elif tag in ("em", "i"): self.out.append("*")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"): self.out.append("**\n\n")
        elif tag == "ul": self.depth -= 1; self.out.append("\n\n")
        elif tag == "p": self.out.append("\n\n")
        elif tag == "a": self.out.append(f"]({self.href})" if self.href else "]"); self.href = None

    def handle_data(self, d):
        self.out.append(re.sub(r"\s+", " ", d))

    def text(self):
        t = "".join(self.out).replace(" ", " ")
        t = re.sub(r"\*\*\s*\*\*", "", t)
        t = re.sub(r"\[\]\([^)]*\)", "", t)
        t = re.sub(r"[ \t]+\n", "\n", t)
        t = re.sub(r"\n[ \t]+(?!- )", "\n", t)
        return re.sub(r"\n{3,}", "\n\n", t).strip()


def md(fragment):
    p = _MD(); p.feed(fragment); return p.text()


def plain(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


# ---------- parsers ----------

def parse_agenda(page):
    """Agenda page -> {"days": [{"label", "stages": [{"name", "items": [{"time", "title", "speakers", "abstract"?}]}]}]}"""
    labels = re.findall(r"content: '([A-Za-z]+ \d+ October 2026)'", page)
    days = []
    for di, tab in enumerate(re.split(r'<div class="et_pb_tab et_pb_tab_\d', page)[1:]):
        tab = tab.split('<div class="et_pb_module', 1)[0]
        stages = []
        for blk in re.split(r'<div class="stages stage-\d">', tab)[1:]:
            name = plain(re.search(r'<h2 class="main-daytitle"[^>]*>(.*?)</h2>', blk, re.S).group(1))
            items = []
            for row_attrs, row in re.findall(r"<tr([^>]*)>(.*?)</tr>", blk, re.S):
                tds = re.findall(r"<td([^>]*)>(.*?)</td>", row, re.S)
                if 'class="desc"' in row:          # abstract row belongs to the session above it
                    d = md(re.sub(r"<br\s*/?>", "</p><p>", tds[0][1]))
                    if d and items: items[-1]["abstract"] = d
                    continue
                if len(tds) != 2:
                    continue
                time = plain(tds[0][1]).replace(" – ", "–")
                cell = tds[1][1]
                speakers = []
                for sp in re.findall(r'<div class="speaker-part">(.*?)</div>', cell, re.S):
                    nm = plain(re.search(r'<span class="speaker">(.*?)</span>', sp, re.S).group(1))
                    rest = re.sub(r"^\s*,\s*", "", plain(re.sub(r'<span class="speaker">.*?</span>', "", sp, flags=re.S))).strip()
                    if nm: speakers.append({"name": nm, "affiliation": rest})
                cell_wo = re.sub(r'<div class="speaker-part">.*?</div>', "", cell, flags=re.S)
                m = re.search(r"<strong>(.*?)</strong>", cell_wo, re.S)
                it = {"time": time, "title": plain(m.group(1)) if m else plain(cell_wo), "speakers": speakers}
                extra = md(cell_wo.replace(m.group(0), "", 1)) if m else ""
                if extra: it["extra"] = extra          # text outside the usual markup, e.g. an unmarked speaker name
                items.append(it)
            stages.append({"name": name, "items": items})
        days.append({"label": labels[di] if di < len(labels) else f"Day {di + 1}", "stages": stages})
    return {"days": days}


SLOT_TIME = {"10:15a-12:15p": "10:15–12:15", "1:45p-3:45p": "13:45–15:45", "4:00p-6:00p": "16:00–18:00"}


def parse_workshops(page):
    """Workshops page -> [{"day", "time", "title", "room"}] (titles and rooms only, enough to spot changes)."""
    slots = re.findall(r'data-agenda-tab="([^"]+)">Day (\d) <span class="day-sub-title">([^<]+)</span>', page)
    out = []
    for sid, day, when in slots:
        start = page.index(f'id="{sid}"')
        ends = [page.find(f'id="{o}"', start + 1) for o, _, _ in slots if o != sid] + [page.find("<footer", start)]
        ends = [e for e in ends if e > start] + [len(page)]
        seg = page[start:min(ends)]
        for head in re.findall(r'<div class="et_pb_text_inner">(.*?)</div>', seg, re.S):
            lines = [plain(x) for x in re.sub(r"<br\s*/?>|</p>", "\n", head).split("\n")]
            lines = [x for x in lines if x]
            if not lines or lines[0].endswith(":"):
                continue
            m = re.match(r"(.*?)\s+[–-]\s+(Room .*)$", lines[0])
            title, room = (m.group(1), m.group(2)) if m else (lines[0], "")
            out.append({"day": int(day), "time": SLOT_TIME.get(when.strip(), when.strip()), "title": title, "room": room})
    return out


# ---------- compare ----------

# Differences the planner keeps on purpose, so they do not hide real changes. Each line of the report that
# starts with one of these prefixes is listed under "intentional" instead of being flagged.
INTENTIONAL = {
    "ONLY IN PLANNER  Day 3 S2 11:10–11:35": "the 11:10-12:00 lightning talks block is split in two halves to line up with Stage 1",
    "ONLY IN PLANNER  Day 3 S2 11:35–12:00": "second half of the lightning talks block",
    "NEW IN AGENDA    Day 3 S2 11:10–12:00": "shown as the two halves above",
    "CHANGED          Day 3 S2 16:45–17:00": "the agenda lists Hari Nagarajan outside its speaker markup; the planner keeps him as the speaker",
}

def compare(agenda, workshops, data):
    stage_key = {"Stage 1": "S1", "Stage 2": "S2", "Villages": "Villages"}
    official = {}
    for i, day in enumerate(agenda["days"], 1):
        for st in day["stages"]:
            for it in st["items"]:
                official[(i, stage_key.get(st["name"], st["name"]), it["time"])] = it
    ours = {}
    for i, day in enumerate(data["days"], 1):
        for it in day["items"]:
            ours[(i, it["stage"], it["time"])] = it
    report = []
    for k in sorted(set(official) | set(ours)):
        o, n = ours.get(k), official.get(k)
        where = f"Day {k[0]} {k[1]} {k[2]}"
        if o and not n:
            report.append(f"ONLY IN PLANNER  {where}  {o['title']}  [{o.get('id', '')}]")
        elif n and not o:
            who = ", ".join(s["name"] for s in n["speakers"]) or n.get("extra", "")
            report.append(f"NEW IN AGENDA    {where}  {n['title']}  ({who})")
        elif k[1] != "Villages":
            diffs = []
            if o["title"] != n["title"]: diffs.append(f"title {o['title']!r} -> {n['title']!r}")
            ospk = [(s.get("k") or s.get("n"), s.get("a", "")) for s in o.get("speakers", [])]
            nspk = [(s["name"], s["affiliation"]) for s in n["speakers"]]
            if ospk != nspk: diffs.append(f"speakers {ospk} -> {nspk}")
            if (o.get("abstract") or "") != (n.get("abstract") or ""): diffs.append("abstract changed")
            if diffs: report.append(f"CHANGED          {where}  [{o.get('id', '')}]  " + "; ".join(diffs))
    ow = {(w["day"], w["time"], w["title"]): w for w in data["workshops"]}
    nw = {(w["day"], w["time"], w["title"]): w for w in workshops}
    for k in sorted(set(ow) | set(nw)):
        if k not in nw: report.append(f"WORKSHOP GONE    Day {k[0]} {k[1]}  {k[2]}")
        elif k not in ow: report.append(f"WORKSHOP NEW     Day {k[0]} {k[1]}  {k[2]}  {nw[k]['room']}")
        elif ow[k].get("room", "") != nw[k]["room"]: report.append(f"WORKSHOP ROOM    Day {k[0]} {k[1]}  {k[2]}  {ow[k].get('room', '')!r} -> {nw[k]['room']!r}")
    return report


def main(argv):
    save = None
    if "--save-json" in argv:
        i = argv.index("--save-json"); save = pathlib.Path(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    if len(argv) >= 2:
        agenda_page, ws_page = (pathlib.Path(p).read_text(encoding="utf-8") for p in argv[:2])
    else:
        agenda_page, ws_page = fetch(AGENDA_URL), fetch(WORKSHOPS_URL)
    agenda, workshops = parse_agenda(agenda_page), parse_workshops(ws_page)
    if save:
        save.mkdir(parents=True, exist_ok=True)
        (save / "agenda.json").write_text(json.dumps(agenda, indent=1, ensure_ascii=False), encoding="utf-8")
        (save / "workshops.json").write_text(json.dumps(workshops, indent=1, ensure_ascii=False), encoding="utf-8")
    data = json.loads((HERE / "planner-data.json").read_text(encoding="utf-8"))
    report = compare(agenda, workshops, data)
    known = [(line, why) for line in report for pre, why in INTENTIONAL.items() if line.startswith(pre)]
    real = [line for line in report if not any(line.startswith(pre) for pre in INTENTIONAL)]
    print("\n".join(real) if real else "In sync: no differences with the official agenda.")
    if known:
        print("\nIntentional differences:")
        for line, why in known:
            print(f"  {line}\n      why: {why}")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
