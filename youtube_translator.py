import streamlit as st
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip
from gtts import gTTS
import io
import openai
import os
import whisper
import tempfile

# Language options for translation
language_options = {
    "Spanish": "es",
    "German": "de"
}

def main():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    st.title("YouTube Translator")

    st.write("Enter YouTube video link:")
    link = st.text_input("Link")
    target_language = st.selectbox("Select Target Language", list(language_options.keys()))

    if st.button("Translate"):
        st.write("Downloading video...")
        yt = YouTube(link)
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        # Download video to buffer
        video_buffer = io.BytesIO()
        video_stream.stream_to_buffer(video_buffer)
        video_buffer.seek(0)
        st.write("Video downloaded successfully!")

        st.write("Extracting audio from video...")
        # Write video buffer to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video_file:
            temp_video_file.write(video_buffer.getvalue())
            temp_video_file_name = temp_video_file.name

        # Process the video file
        video_clip = VideoFileClip(temp_video_file_name)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            video_clip.audio.write_audiofile(temp_audio_file.name, codec='pcm_s16le')
            temp_audio_file_name = temp_audio_file.name
        video_clip.close()

        # Load audio file for transcription
        model = whisper.load_model("base")
        result = model.transcribe(temp_audio_file_name)
        original_text = result["text"]

        st.write("Translating text...")
        openai.api_key = openai_api_key
        prompt = f"translate this full text to {language_options[target_language]}: {original_text}"

        response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=3800,
            temperature=0.5
        )

        translated_text = response.choices[0].text.strip()

        st.write("Generating translated audio...")
        translated_audio = gTTS(text=translated_text, lang=language_options[target_language], slow=False)
        
        # Save translated audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_translated_audio_file:
            translated_audio.save(temp_translated_audio_file.name)
            temp_translated_audio_file_name = temp_translated_audio_file.name

        st.write(f"Generating translated video in {target_language}...")
        # Load translated audio from the temporary file
        translated_audio_clip = AudioFileClip(temp_translated_audio_file_name)

        video_clip = VideoFileClip(temp_video_file_name)
        video_clip = video_clip.set_audio(translated_audio_clip)

        final_video_buffer = io.BytesIO()
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as final_video_file:
            video_clip.write_videofile(final_video_file.name, codec="libx264", audio_codec="aac")
            final_video_file.seek(0)
            final_video_buffer.write(final_video_file.read())
        final_video_buffer.seek(0)

        st.write("Process completed!")
        st.write(f"Displaying generated video in {target_language}...")
        st.video(final_video_buffer.getvalue())

if __name__ == "__main__":
    main()
