# -*- coding: utf-8 -*-
"""生成分段配音 + timing.json"""
import asyncio, json, os, subprocess, sys
import edge_tts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from narration import SEGMENTS, VOICE

BASE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BASE, "work")
os.makedirs(WORK, exist_ok=True)

def dur(path):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","csv=p=0",path], capture_output=True, text=True)
    return float(out.stdout.strip())

async def main():
    timing = []
    for seg in SEGMENTS:
        mp3 = os.path.join(WORK, seg["id"] + ".mp3")
        await edge_tts.Communicate(seg["text"], VOICE, rate="+0%").save(mp3)
        d = dur(mp3)
        timing.append({"id": seg["id"], "station": seg["station"], "duration": d})
        print(f'{seg["id"]:>6}  站{seg["station"]:>2}  {d:6.2f}s  {len(seg["text"])} 字')
    # 拼成整条配音
    lst = os.path.join(WORK, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for seg in SEGMENTS:
            f.write(f"file '{os.path.join(WORK, seg['id'])}.mp3'\n")
    voice = os.path.join(WORK, "voice.mp3")
    subprocess.run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",lst,"-c","copy",voice,"-y"], check=True)
    with open(os.path.join(BASE, "timing.json"), "w", encoding="utf-8") as f:
        json.dump(timing, f, ensure_ascii=False, indent=2)
    total = sum(t["duration"] for t in timing)
    print(f"\n合计 {total:.1f} 秒 = {total/60:.1f} 分钟 → work/voice.mp3 + timing.json")

asyncio.run(main())
