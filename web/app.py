"""PodForge Web UI — FastAPI application serving a dark-themed podcast generator."""

import os
import uuid
import time
import asyncio
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Load environment variables from ~/.hermes/.env
# ---------------------------------------------------------------------------
_env_file = Path.home() / ".hermes" / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="PodForge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Job store  {job_id: {status, progress_message, duration, output_path, error}}
# ---------------------------------------------------------------------------
jobs: dict[str, dict] = {}

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    topic: Optional[str] = None
    url: Optional[str] = None
    style: str = "casual"
    speakers: int = 2
    tts_backend: str = "edge"

# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------
def _run_generation(job_id: str, topic: str, url: str, style: str, speakers: int, tts_backend: str):
    """Synchronous function executed in a thread."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["progress_message"] = "Starting pipeline..."
    t0 = time.time()
    output_path = str(OUTPUT_DIR / f"{job_id}.mp3")
    try:
        from podforge.pipeline import run_pipeline
        jobs[job_id]["progress_message"] = "Generating podcast — this may take a few minutes..."
        result = run_pipeline(
            topic=topic or None,
            url=url or None,
            style=style,
            speakers=speakers,
            tts_backend=tts_backend,
            output=output_path,
        )
        elapsed = round(time.time() - t0, 1)
        jobs[job_id].update(
            status="done",
            progress_message="Podcast ready!",
            duration=elapsed,
            output_path=output_path,
        )
    except Exception as exc:
        elapsed = round(time.time() - t0, 1)
        jobs[job_id].update(
            status="error",
            progress_message=f"Error: {exc}",
            duration=elapsed,
            error=traceback.format_exc(),
        )

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.post("/api/generate")
async def generate(req: GenerateRequest):
    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "status": "queued",
        "progress_message": "Queued...",
        "duration": 0,
        "output_path": None,
        "error": None,
    }
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        _run_generation,
        job_id,
        req.topic or "",
        req.url or "",
        req.style,
        req.speakers,
        req.tts_backend,
    )
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def status(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    j = jobs[job_id]
    return {
        "status": j["status"],
        "progress_message": j["progress_message"],
        "duration": j["duration"],
    }


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    j = jobs[job_id]
    if j["status"] != "done" or not j.get("output_path"):
        return JSONResponse({"error": "Not ready"}, status_code=400)
    return FileResponse(
        j["output_path"],
        media_type="audio/mpeg",
        filename=f"podforge-{job_id}.mp3",
    )

# ---------------------------------------------------------------------------
# HTML UI
# ---------------------------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>PodForge — AI Podcast Generator</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{
  min-height:100vh;
  font-family:'Segoe UI',system-ui,-apple-system,sans-serif;
  background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
  color:#e0e0e0;
  display:flex;align-items:center;justify-content:center;
  padding:2rem;
}
.card{
  background:rgba(255,255,255,.06);
  backdrop-filter:blur(12px);
  border:1px solid rgba(255,255,255,.1);
  border-radius:20px;
  padding:2.5rem;
  width:100%;max-width:520px;
  box-shadow:0 8px 32px rgba(0,0,0,.4);
}
h1{
  text-align:center;font-size:1.8rem;margin-bottom:.3rem;
  background:linear-gradient(90deg,#a78bfa,#60a5fa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.subtitle{text-align:center;font-size:.85rem;color:#9ca3af;margin-bottom:1.8rem}
label{display:block;font-size:.85rem;color:#c4b5fd;margin-bottom:.3rem;margin-top:1rem}
input[type=text],select{
  width:100%;padding:.7rem 1rem;border:1px solid rgba(255,255,255,.15);
  border-radius:10px;background:rgba(255,255,255,.07);color:#e0e0e0;
  font-size:.95rem;outline:none;transition:border .2s;
}
input:focus,select:focus{border-color:#a78bfa}
.tts-toggle{display:flex;gap:.5rem;margin-top:.4rem}
.tts-toggle label{
  flex:1;text-align:center;padding:.55rem;border-radius:10px;cursor:pointer;
  border:1px solid rgba(255,255,255,.15);font-size:.85rem;transition:.2s;
  margin:0;color:#c4b5fd;
}
.tts-toggle input{display:none}
.tts-toggle input:checked+span{background:rgba(167,139,250,.25);border-color:#a78bfa}
.tts-toggle label:has(input:checked){background:rgba(167,139,250,.2);border-color:#a78bfa}
.btn{
  width:100%;margin-top:1.5rem;padding:.8rem;border:none;border-radius:12px;
  background:linear-gradient(135deg,#7c3aed,#3b82f6);color:#fff;
  font-size:1rem;font-weight:600;cursor:pointer;transition:opacity .2s;
  display:flex;align-items:center;justify-content:center;gap:.5rem;
}
.btn:hover{opacity:.9}
.btn:disabled{opacity:.5;cursor:not-allowed}
.spinner{
  width:18px;height:18px;border:2px solid rgba(255,255,255,.3);
  border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;
  display:none;
}
@keyframes spin{to{transform:rotate(360deg)}}
.progress{
  margin-top:1rem;text-align:center;font-size:.85rem;color:#9ca3af;
  min-height:1.2rem;
}
.result{
  margin-top:1.2rem;display:none;flex-direction:column;gap:.7rem;
  align-items:center;
}
audio{width:100%;border-radius:10px}
.dl-btn{
  padding:.5rem 1.5rem;border-radius:10px;border:1px solid #a78bfa;
  background:transparent;color:#a78bfa;cursor:pointer;font-size:.85rem;
  text-decoration:none;transition:.2s;
}
.dl-btn:hover{background:rgba(167,139,250,.15)}
.error{color:#f87171;margin-top:.8rem;font-size:.85rem;text-align:center}
.speakers-row{display:flex;align-items:center;gap:1rem}
.speakers-row input{width:70px;text-align:center}
</style>
</head>
<body>
<div class="card">
  <h1>🎙️ PodForge</h1>
  <p class="subtitle">AI-Powered Podcast Generator</p>

  <label for="topic">Topic or URL</label>
  <input type="text" id="topic" placeholder="e.g. Quantum Computing or https://..." autocomplete="off"/>

  <label for="style">Conversation Style</label>
  <select id="style">
    <option value="casual">🗣️ Casual</option>
    <option value="academic">🎓 Academic</option>
    <option value="debate">⚔️ Debate</option>
    <option value="storytelling">📖 Storytelling</option>
  </select>

  <div class="speakers-row">
    <div style="flex:1">
      <label for="speakers">Speakers</label>
      <input type="text" id="speakers" value="2"/>
    </div>
  </div>

  <label>Text-to-Speech Engine</label>
  <div class="tts-toggle">
    <label><input type="radio" name="tts" value="edge" checked/>🆓 Edge (Free)</label>
    <label><input type="radio" name="tts" value="elevenlabs"/>⭐ ElevenLabs (Premium)</label>
  </div>

  <button class="btn" id="genBtn" onclick="generate()">
    <div class="spinner" id="spinner"></div>
    <span id="btnText">Generate Podcast</span>
  </button>

  <div class="progress" id="progress"></div>
  <div class="error" id="error"></div>

  <div class="result" id="result">
    <audio controls id="player"></audio>
    <a class="dl-btn" id="dlBtn" download>⬇ Download MP3</a>
  </div>
</div>

<script>
let pollTimer=null;

async function generate(){
  const topic=document.getElementById('topic').value.trim();
  if(!topic){document.getElementById('error').textContent='Please enter a topic or URL.';return}
  const isUrl=topic.startsWith('http://') || topic.startsWith('https://');
  const style=document.getElementById('style').value;
  const speakers=parseInt(document.getElementById('speakers').value)||2;
  const tts=document.querySelector('input[name=tts]:checked').value;

  // Reset UI
  document.getElementById('error').textContent='';
  document.getElementById('result').style.display='none';
  document.getElementById('spinner').style.display='block';
  document.getElementById('genBtn').disabled=true;
  document.getElementById('btnText').textContent='Generating...';
  document.getElementById('progress').textContent='Starting...';

  try{
    const r=await fetch('/api/generate',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        topic:isUrl?null:topic,
        url:isUrl?topic:null,
        style,speakers,tts_backend:tts
      })
    });
    const d=await r.json();
    if(!d.job_id) throw new Error('No job_id returned');
    pollStatus(d.job_id);
  }catch(e){
    resetBtn();
    document.getElementById('error').textContent='Failed to start: '+e.message;
  }
}

function pollStatus(jid){
  if(pollTimer) clearInterval(pollTimer);
  pollTimer=setInterval(async()=>{
    try{
      const r=await fetch('/api/status/'+jid);
      const d=await r.json();
      document.getElementById('progress').textContent=d.progress_message+(d.duration?' ('+d.duration+'s)':'');
      if(d.status==='done'){
        clearInterval(pollTimer);
        resetBtn();
        const res=document.getElementById('result');
        const player=document.getElementById('player');
        const dl=document.getElementById('dlBtn');
        player.src='/api/download/'+jid;
        dl.href='/api/download/'+jid;
        res.style.display='flex';
      }else if(d.status==='error'){
        clearInterval(pollTimer);
        resetBtn();
        document.getElementById('error').textContent=d.progress_message;
      }
    }catch(e){console.error(e)}
  },2000);
}

function resetBtn(){
  document.getElementById('spinner').style.display='none';
  document.getElementById('genBtn').disabled=false;
  document.getElementById('btnText').textContent='Generate Podcast';
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8099)
