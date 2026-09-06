# -*- coding: utf-8 -*-
"""从 narration.py + timing.json 生成 SRT:按中文标点断句,按字数比例分配时间"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from narration import SEGMENTS
BASE = os.path.dirname(os.path.abspath(__file__))
TEXT = {s["id"]: s["text"] for s in SEGMENTS}

def split_sentences(text, max_len=22):
    parts = re.split(r'([。！？])', text)
    sents, buf = [], ''
    for p in parts:
        buf += p
        if p in '。！？': sents.append(buf.strip()); buf = ''
    if buf.strip(): sents.append(buf.strip())
    out = []
    for s in sents:
        if len(s) <= max_len: out.append(s); continue
        sub = re.split(r'([，、：；——])', s); b2 = ''
        for sp in sub:
            if len(b2) + len(sp) > max_len and b2: out.append(b2.strip()); b2 = sp
            else: b2 += sp
        if b2.strip(): out.append(b2.strip())
    merged = []
    for s in out:
        if merged and len(s) < 6: merged[-1] += s
        else: merged.append(s)
    return merged

def fmt(sec):
    h=int(sec//3600); m=int((sec%3600)//60); s=int(sec%60); ms=int((sec%1)*1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

timing = json.load(open(os.path.join(BASE,"timing.json"), encoding="utf-8"))
lines, idx, t0 = [], 1, 0.0
for t in timing:
    text = TEXT.get(t["id"], "")
    if not text: t0 += t["duration"]; continue
    sents = split_sentences(text)
    total = sum(len(s) for s in sents) or 1
    cur = t0
    for s in sents:
        d = t["duration"] * len(s) / total
        lines += [str(idx), f"{fmt(cur)} --> {fmt(cur+d)}", s, ""]
        idx += 1; cur += d
    t0 += t["duration"]
open(os.path.join(BASE,"subtitles.srt"),"w",encoding="utf-8").write("\n".join(lines))
print(f"生成 {idx-1} 条字幕 → subtitles.srt")
