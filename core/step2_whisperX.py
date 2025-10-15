import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich import print as rprint
import subprocess

from core.config_utils import load_key
from core.all_whisper_methods.demucs_vl import demucs_main
from core.all_whisper_methods.audio_preprocess import process_transcription, convert_video_to_audio, split_audio, save_results, compress_audio
from core.step1_ytdlp import find_video_files

import streamlit as st
import requests
from urllib.parse import urljoin

def enhance_vocals(vocals_ratio=2.50):
    username = st.session_state.get('username')
    ENHANCED_VOCAL_PATH = os.path.join("users", username, "output", "audio", "enhanced_vocals.mp3")
    
    AUDIO_DIR = os.path.join("users", username, "output", "audio")
    RAW_AUDIO_FILE = os.path.join(AUDIO_DIR, "raw.mp3")
    VOCAL_AUDIO_FILE = os.path.join(AUDIO_DIR, "vocal.mp3")

    """Enhance vocals audio volume"""
    if not load_key("demucs",username=username):
        return RAW_AUDIO_FILE
        
    try:
        print(f"[cyan]🎙️ Enhancing vocals with volume ratio: {vocals_ratio}[/cyan]")
        ffmpeg_cmd = (
            f'ffmpeg -y -i "{VOCAL_AUDIO_FILE}" '
            f'-filter:a "volume={vocals_ratio}" '
            f'"{ENHANCED_VOCAL_PATH}"'
        )
        subprocess.run(ffmpeg_cmd, shell=True, check=True, capture_output=True)
        
        return ENHANCED_VOCAL_PATH
    except subprocess.CalledProcessError as e:
        print(f"[red]Error enhancing vocals: {str(e)}[/red]")
        return VOCAL_AUDIO_FILE  # Fallback to original vocals if enhancement fails
    
def transcribe():
    username = st.session_state.get('username')
    AUDIO_DIR = os.path.join("users", username, "output", "audio")
    CLEANED_CHUNKS_EXCEL_PATH = os.path.join("users", username, "output", "log", "cleaned_chunks.xlsx")
    RAW_AUDIO_FILE = os.path.join(AUDIO_DIR, "raw.mp3")

    if os.path.exists(CLEANED_CHUNKS_EXCEL_PATH):
        rprint("[yellow]⚠️ Transcription results already exist, skipping transcription step.[/yellow]")
        return
    
    # step0 Convert video to audio
    username = st.session_state.get('username')
    video_file = find_video_files(username=username)
    convert_video_to_audio(video_file)

    # step1 Demucs vocal separation:
    if load_key("demucs", username=username):
        demucs_main()
    
    # step2 Compress audio
    choose_audio = enhance_vocals() if load_key("demucs", username=username) else RAW_AUDIO_FILE
    
    base_path = os.path.join("users", username, "output", "audio")
    WHISPER_FILE = os.path.join(base_path, "for_whisper.mp3")

    whisper_audio = compress_audio(choose_audio, WHISPER_FILE)    
    
    # step4 Transcribe audio
    all_results = []
    if not load_key("parakeet", username=username):
        if load_key("whisper.runtime", username=username) == "local":
            from core.all_whisper_methods.whisperX_local import transcribe_audio as ts
            rprint("[cyan]🎤 Transcribing audio with local model...[/cyan]")
        else:
            from core.all_whisper_methods.whisperX_302 import transcribe_audio_302 as ts
            rprint("[cyan]🎤 Transcribing audio with 302 API...[/cyan]")
        # step3 Extract audio
        segments = split_audio(whisper_audio)
        for start, end in segments:
            result = ts(whisper_audio, start, end)
            all_results.append(result)
    else:
        from core.all_whisper_methods.parakeet import parakeet_transcribe as para
        # step3 Extract audio
        target_len = int(load_key("target_len"))

        segments = split_audio(whisper_audio, target_len=target_len)

        reload_interval = int(load_key("reload_interval"))
        count = 0

        parakeet_url = load_key("parakeet_url", username=username)
        load_model_url = urljoin(parakeet_url, 'load_model')
        unload_model_url = urljoin(parakeet_url, 'unload_model')

        requests.post(load_model_url)

        for start, end in segments:
            print(whisper_audio)
            print(start)
            print(end)
            result = para(whisper_audio, username, start, end)
            all_results.append(result)
            count += 1

            if count % reload_interval == 0:
                print(f"已完成 {count} 次转录，重新加载模型中...")
                requests.post(unload_model_url)
                requests.post(load_model_url)

        requests.post(unload_model_url)

    
    # step5 Combine results
    combined_result = {'segments': []}
    for result in all_results:
        combined_result['segments'].extend(result['segments'])
    
    # step6 Process df
    df = process_transcription(combined_result)
    save_results(df)
        
if __name__ == "__main__":
    transcribe()
