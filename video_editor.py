from __future__ import annotations
import logging, subprocess
from pathlib import Path
from typing import Any
from config import Settings
logger=logging.getLogger(__name__)
class VideoEditingError(RuntimeError): pass

def render_short(*,script:dict[str,Any],voiceover:dict[str,Any],clips:list[dict[str,Any]],settings:Settings)->Path:
    out=(settings.output_dir/_safe_filename(script["title"])).with_suffix(".mp4"); tmp=settings.temp_dir; concat=tmp/"concat.txt"; ass=tmp/"captions.ass"; parts=[]; ts=voiceover["scene_timings"]
    if len(clips)!=len(ts) or len(clips)!=len(script.get("scenes",[])): raise ValueError("Each scene needs one clip and timing entry.")
    try:
        for clip,t in zip(clips,ts):
            part=tmp/("rendered_%02d.mp4"%clip["scene_number"]); _run([settings.ffmpeg_binary,"-y","-i",str(clip["path"]),"-t","%.3f"%(t["end"]-t["start"]),"-vf","scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d"%(settings.video_width,settings.video_height,settings.video_width,settings.video_height),"-r",str(settings.video_fps),"-an","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(part)],"scene"); parts.append(part)
        concat.write_text("".join("file '%s'\\n"%p.as_posix() for p in parts),encoding="utf-8"); joined=tmp/"joined.mp4"; _run([settings.ffmpeg_binary,"-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(joined)],"join")
        _write_ass(ass,script["scenes"],ts,settings.video_width,settings.video_height); _run([settings.ffmpeg_binary,"-y","-i",str(joined),"-i",str(voiceover["audio_path"]),"-vf","ass="+_path(ass),"-map","0:v:0","-map","1:a:0","-shortest","-c:v","libx264","-c:a","aac","-movflags","+faststart",str(out)],"render")
    except (OSError,subprocess.SubprocessError) as exc: raise VideoEditingError("FFmpeg could not render the short.") from exc
    return out

def _run(cmd:list[str],action:str)->None:
    try: subprocess.run(cmd,check=True,capture_output=True,text=True)
    except FileNotFoundError as exc: raise OSError("FFmpeg executable was not found.") from exc
    except subprocess.CalledProcessError as exc: raise subprocess.SubprocessError("Failed while %s: %s"%(action,(exc.stderr or "")[-1000:])) from exc

def _write_ass(path:Path,scenes:list[dict[str,Any]],ts:list[dict[str,Any]],w:int,h:int)->None:
    head="""[Script Info]
ScriptType: v4.00+
PlayResX: %d
PlayResY: %d
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Shorts,Arial,58,&H00FFFFFF,&H00FFFFFF,&H00101010,&H99000000,1,0,0,0,100,100,0,0,3,4,2,2,90,90,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""%(w,h); rows=[]
    for scene,t in zip(scenes,ts): rows.append("Dialogue: 0,%s,%s,Shorts,,0,0,0,,%s"%(_time(t["start"]),_time(t["end"]),_esc(_caption(scene["narration"]))))
    path.write_text(head+"\n".join(rows)+"\n",encoding="utf-8")
def _caption(text:str)->str:
    words=text.strip().split(); lines=[]; line=""
    for word in words:
        if line and len(line)+len(word)+1>34: lines.append(line); line=""
        line+=(" " if line else "")+word
    if line: lines.append(line)
    if len(lines)>2: mid=(len(lines)+1)//2; lines=[" ".join(lines[:mid])," ".join(lines[mid:])]
    return r"\N".join(lines)
def _esc(text:str)->str: return text.replace("\\","\\\\").replace("{","\\{").replace("}","\\}")
def _time(v:float)->str:
    n=max(0,int(round(v*100))); h,r=divmod(n,360000); m,r=divmod(r,6000); s,c=divmod(r,100); return "%d:%02d:%02d.%02d"%(h,m,s,c)
def _path(p:Path)->str: return str(p.resolve()).replace("\\","/").replace(":","\\:")
def _safe_filename(title:str)->str: return "_".join("".join(c if c.isalnum() or c in " -_" else "_" for c in title).split())[:80] or "youtube_short"
