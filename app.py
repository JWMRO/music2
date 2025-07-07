# app.py
import os, re, shlex, subprocess
from pathlib import Path

import streamlit as st
import yt_dlp
import time
from pydub import AudioSegment
from io import BytesIO
# ---------- Streamlit 頁面設定 ----------
st.set_page_config(page_title="Demucs Audio Separator", page_icon="🎵")
st.title(" Demucs 音源分離器")
st.write("輸入 YouTube 連結 → 自動下載並用 Demucs 分離聲部。")

# ---------- 1) 先顯示「本次 Session 已分離過的歌曲」 ----------
if "history" in st.session_state and st.session_state["history"]:
    st.sidebar.markdown("##  歷史分離音檔")
    for clean_title, sep_dir in st.session_state["history"].items():
        with st.sidebar.expander(clean_title, expanded=False):
            for part in ["vocals", "drums", "bass", "other"]:
                p = Path(sep_dir) / f"{part}.wav"
                if p.exists():
                    with open(p, "rb") as f:
                        st.download_button(
                            f"下載 {part}", f, file_name=f"{clean_title}_{part}.wav",
                            key=f"{clean_title}_{part}_side"
                        )

# ---------- 2) 如果剛分離完或重整頁面，需要顯示「最近一次音檔」 ----------
if "current_sep" in st.session_state:
    sep_dir = Path(st.session_state["current_sep"])
    clean_title = sep_dir.name
    if sep_dir.exists():
        st.markdown("###  分離後音軌 (最近一次)")
        for part in ["vocals", "drums", "bass", "other"]:
            p = sep_dir / f"{part}.wav"
            if p.exists():
                st.audio(str(p), format="audio/wav")
                with open(p, "rb") as f:
                    st.download_button(
                        f"下載 {part}.wav", f, file_name=f"{clean_title}_{part}.wav",
                        key=f"{clean_title}_{part}_main"
                    )
        st.divider()
        
        #-----混音器
        st.markdown("### 混音控制面板")
        selected_tracks = st.multiselect(
            "選擇要混音的音軌",
            options=["vocals", "drums", "bass", "other"],
            default=["vocals", "drums", "bass", "other"]
        )
        
        preserve_tracks = st.toggle("在伺服器上保留混音音檔 (方便分享或重複使用)", value=False)
        
        if st.button("🔊 播放混音音軌") and selected_tracks:
            combined = None
            for part in selected_tracks:
                part_path = sep_dir / f"{part}.wav"
                if part_path.exists():
                    track = AudioSegment.from_file(part_path)
                    if combined is None:
                        combined = track
                    else:
                        combined = combined.overlay(track)

            if combined:
                buf = BytesIO()
                combined.export(buf, format="wav")

                st.audio(buf, format="audio/wav")
                st.download_button("⬇ 下載混音音軌", buf.getvalue(), file_name=f"{clean_title}_mix.wav")

                if preserve_tracks:
                    mix_dir = Path("separated/htdemucs") / clean_title
                    mix_dir.mkdir(parents=True, exist_ok=True)
                    mix_path = mix_dir / "mix_preview.wav"
                    combined.export(mix_path, format="wav")
                    st.success(f" 混音已儲存：{mix_path}")

# ---------- 3) 讓使用者輸入連結並按 Start ----------

youtube_url = st.text_input(
    "YouTube 連結", placeholder="https://www.youtube.com/watch?v=example"
)

if st.button("Start Separate") and youtube_url:
    progress = st.progress(0, text="準備分離音源中…")

    # ---- 3‑A. 下載音檔到 downloads/ ----
    downloads = Path("downloads")
    downloads.mkdir(exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "restrictfilenames": True,
        "outtmpl": str(downloads / "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }  
     }

    progress.progress(10, "正在下載音檔…")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)

    progress.progress(30, "轉換為 WAV…")
    time.sleep(0.5)
    wav_path = Path(info["requested_downloads"][0]["filepath"]).with_suffix(".wav")
    assert wav_path.exists(), f"{wav_path} 下載的音檔不存在！"
    clean_title = wav_path.stem

    # ---- 3‑B. Demucs 分離 ----
    sep_dir = Path("separated/htdemucs") / clean_title
    if not sep_dir.exists():
        progress.progress(50, "首次分離，啟動 Demucs… , 請稍候… , 這會用到一些時間")
        time.sleep(0.5)
        cmd = [
            str(Path(os.sys.executable)),
            "-m", "demucs",
            str(wav_path)
        ]
        subprocess.run(cmd, check=True)
        progress.progress(80, "Demucs 完成，準備結果…")
    else:
        progress.progress(80, "已分離過，直接載入結果…")

    # ---- 3‑C. 更新 session_state、顯示結果 ----
    st.session_state.setdefault("history", {})[clean_title] = str(sep_dir)
    st.session_state["current_sep"] = str(sep_dir)
    progress.progress(100, "完成！下載區已更新")
    time.sleep(0.5)
    st.rerun()
