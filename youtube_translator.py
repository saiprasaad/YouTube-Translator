import streamlit as st
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip
from gtts import gTTS
import os
import openai
import shutil
import whisper

language_options = {
    "Spanish": "es",
    "German": "de"
}

def main():
    existing_files = ["./audio.mp3", "./video.mp4", "./translated_audio.mp3", "./translated_video.mp4"]
    for file in existing_files:
        if os.path.exists(file):
            os.remove(file)
    st.title("YouTube Translator")

    st.write("Enter YouTube video link:")
    link = st.text_input("Link")
    target_language = st.selectbox("Select Target Language", list(language_options.keys()))

    if st.button("Translate"):
        st.write("Downloading video...")
        yt = YouTube(link)
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        output_video = video_stream.download(output_path=".")
        st.write("Video downloaded successfully!")

        base, ext = os.path.splitext(output_video)
        new_file = os.path.join(os.path.dirname(output_video), "video.mp4")
        os.rename(output_video, new_file)
        st.write("Video renamed to 'video.mp4'")

        output_video_path = "./video.mp4"
        output_audio_path = "./audio.mp3"

        clip = VideoFileClip(output_video_path)
        clip.audio.write_audiofile(output_audio_path)
        clip.close()

        st.write("Transcribing audio...")
        model = whisper.load_model("base")
        result = model.transcribe("audio.mp3")
        original_text = result["text"]

        st.write("Translating text...")
        openai.api_key="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"
        prompt=f"translate this full text {language_options[target_language]}: {original_text}"

        response=openai.completions.create(
        model = "gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=3800,
        temperature=0.5
        )
        print(response)

        translated_text=response.choices[0].text

        st.write("Generating translated audio...")
        translated_audio = gTTS(text=translated_text, lang="es", slow=False)
        translated_audio.save("./translated_audio.mp3")

        translated_audio_path = "./translated_audio.mp3"
        translated_video_path = "./translated_video.mp4"

        st.write(f"Generating translated video in {target_language}...")
        video_clip = VideoFileClip(output_video_path)
        audio_clip = AudioFileClip(translated_audio_path)
        video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile(translated_video_path, codec="libx264", audio_codec="aac")

        st.write("Process completed!")

        st.write(f"Displaying generated video in {target_language}...")
        st.video(translated_video_path)

if __name__ == "__main__":
    main()
