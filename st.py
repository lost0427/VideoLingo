import streamlit as st
import os, sys, shutil
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from st_components.imports_and_utils import *
from core.config_utils import load_key

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")


def text_processing_section():
    username = st.session_state.get('username')
    SUB_VIDEO = os.path.join("users", username, "output", "output_sub.mp4")
    st.header(t("b. Translate and Generate Subtitles"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("WhisperX word-level transcription")}<br>
            2. {t("Sentence segmentation using NLP and LLM")}<br>
            3. {t("Summarization and multi-step translation")}<br>
            4. {t("Cutting and aligning long subtitles")}<br>
            5. {t("Generating timeline and subtitles")}<br>
            6. {t("Merging subtitles into the video")}
        """, unsafe_allow_html=True)

        if not os.path.exists(SUB_VIDEO):
            if st.button(t("Start Processing Subtitles"), key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            if load_key("burn_subtitles", username=username):
                st.video(SUB_VIDEO)
            download_subtitle_zip_button(text=t("Download All Srt Files"))
            
            if st.button(t("Archive to 'history'"), key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    with st.spinner(t("Using Whisper for transcription...")):
        step2_whisperX.transcribe()
    with st.spinner(t("Splitting long sentences...")):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
    with st.spinner(t("Summarizing and translating...")):
        step4_1_summarize.get_summary()
        if load_key("pause_before_translate", username=st.session_state.get('username')):
            input(t("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue..."))
        step4_2_translate_all.translate_all()
    with st.spinner(t("Processing and aligning subtitles...")): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    with st.spinner(t("Merging subtitles to video...")):
        step7_merge_sub_to_vid.merge_subtitles_to_video()
    
    st.success(t("Subtitle processing complete! 🎉"))
    st.balloons()

def audio_processing_section():
    username = st.session_state.get('username')
    DUB_VIDEO = os.path.join("users", username, "output", "output_dub.mp4")
    st.header(t("c. Dubbing"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("Generate audio tasks and chunks")}<br>
            2. {t("Extract reference audio")}<br>
            3. {t("Generate and merge audio files")}<br>
            4. {t("Merge final audio into video")}
        """, unsafe_allow_html=True)
        if not os.path.exists(DUB_VIDEO):
            if st.button(t("Start Audio Processing"), key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success(t("Audio processing is complete! You can check the audio files in the `output` folder."))
            if load_key("burn_subtitles", username=username):
                st.video(DUB_VIDEO) 
            if st.button(t("Delete dubbing files"), key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button(t("Archive to 'history'"), key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner(t("Generate audio tasks")): 
        step8_1_gen_audio_task.gen_audio_task_main()
        step8_2_gen_dub_chunks.gen_dub_chunks()
    with st.spinner(t("Extract refer audio")):
        step9_extract_refer_audio.extract_refer_audio_main()
    with st.spinner(t("Generate all audio")):
        step10_gen_audio.gen_audio()
    with st.spinner(t("Merge full audio")):
        step11_merge_full_audio.merge_full_audio()
    with st.spinner(t("Merge dubbing to the video")):
        step12_merge_dub_to_vid.merge_video_audio()
    
    st.success(t("Audio processing complete! 🎇"))
    st.balloons()

def main():
    with open('auth.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    authenticator.login()
    name = st.session_state.get('name')
    authentication_status = st.session_state.get('authentication_status')
    username = st.session_state.get('username')

    if authentication_status:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        user_dir = os.path.join(base_dir, "users", username)
        os.makedirs(user_dir, exist_ok=True)
        
        config_path = os.path.join(user_dir, "config.yaml")
        if not os.path.exists(config_path):
            shutil.copy(os.path.join(base_dir, "config.yaml"), config_path)

        logo_col, _ = st.columns([1,1])
        with logo_col:
            st.image("docs/logo.webp", use_column_width=True)
        st.markdown(button_style, unsafe_allow_html=True)
        welcome_text = t("Hello, welcome to VideoLingo. If you encounter any issues, feel free to get instant answers with our Free QA Agent <a href=\"https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh\" target=\"_blank\">here</a>! You can also try out our SaaS website at <a href=\"https://videolingo.io\" target=\"_blank\">videolingo.io</a> for free!")
        st.markdown(f"<p style='font-size: 20px;'>{welcome_text}</p>", unsafe_allow_html=True)
        # add settings
        with st.sidebar:
            authenticator.logout('Logout', 'main')
            st.markdown(f"<p style='font-size: 20px;'>{t('Welcome')} {name}</p>", unsafe_allow_html=True)
            page_setting()
            st.markdown(give_star_button, unsafe_allow_html=True)
        download_video_section()
        text_processing_section()
        audio_processing_section()
    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')

if __name__ == "__main__":
    main()
