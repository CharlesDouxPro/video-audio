import yt_dlp as yt
import whisper
import pyktok as pyk
import pandas as pd
import boto3
import spacy
import os
import ffmpeg
import easyocr
import shutil
import os

DB_CONNECTION = "postgresql://postgres.pqhcubzkrlbvljbvsmem:baw1mART4@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"
DB_PASSWORD = "baw1mART4-"

FRAME_FOLDER = "FRAMES"
RAW_DATA_FOLDER = "DATA"


def main():
    download_tiktok_audio(video_url, output_filename)
    video_audio, video_language = transcript_audio_to_text(audio_filename)
    download_and_get_tiktok_metadata(video_url, output_metadata_filename)
    video_title, video_description = extract_metadata(output_metadata_filename)
    extract_video_frames(video_title)
    reader = create_reader(video_language)
    video_frame_text = extract_text_from_frames(reader, frame_folder=FRAME_FOLDER)
    input_text = generate_input_text(video_description, video_audio, video_frame_text)
    places = forecast_places(input_text)
    print(" ")
    print("="*50)
    print(" ")
    print(f"input text from video : {input_text}")
    print(" ")
    print("="*50)
    print(" ")
    print(f"Places forecasted : {places}")
    os.remove(video_title)


def download_tiktok_audio(video_url, output_filename):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])


def transcript_audio_to_text(audio_filename):

    model = whisper.load_model("base")
    result = model.transcribe(audio_filename)
    text = result["text"]
    language = result["language"]
    print(f"text : {result["text"]}")
    print(f"language : {result["language"]}")

    return text, language

def download_and_get_tiktok_metadata(video_url, output_metadata_filename):
    pyk.save_tiktok(video_url,
                True,
                output_metadata_filename)
    
def extract_metadata(output_metadata_filename):
    data = pd.read_csv(output_metadata_filename)
    video_author = data["author_username"][0]
    video_id = data["video_id"][0]
    video_title = f"@{video_author}_video_{video_id}.mp4"
    video_description = data["video_description"][0]

    return video_title, video_description

def extract_video_frames(video_title, fps = 1):
    output_frames = f'{FRAME_FOLDER}/frame_%04d.png'
    (
        ffmpeg
        .input(video_title)
        .output(output_frames, vf=f'fps={fps}')
        .run()
    )

    print("Frames extraction done.")


def create_reader(video_language):
    reader = easyocr.Reader([video_language])
    return reader

def extract_text_from_frames(reader, frame_folder):
    video_frame_text = []
    for frame in os.listdir(frame_folder):
        result = reader.readtext(f"{frame_folder}/{frame}")
        for detection in result:
            video_frame_text.append(detection[1])

    return video_frame_text

def generate_input_text(video_description, video_audio, video_frame_text):
    generated_texts = video_description , video_audio ,  " ".join(video_frame_text)
    return generated_texts


def forecast_places(input_generated_texts):
    nlp = spacy.load("xx_ent_wiki_sm")
    doc = nlp(str(input_generated_texts))
    forecasted_places = [ent.text for ent in doc.ents if ent.label_  in ["LOC", "EVENT", "ORG", "CARDINAL", "FAC"]]
    print("forecasted places :", forecasted_places)
    return forecasted_places




if __name__ == "__main__":
    
    client = boto3.client("s3")

    os.mkdir(FRAME_FOLDER)
    os.mkdir(RAW_DATA_FOLDER)

    pd.set_option('display.max_colwidth', None)


    video_url = "https://www.tiktok.com/@michellekatzd/video/6986224560949464326?q=caf%C3%A9%20%C3%A0%20paris&t=1727969717273"  
    output_filename = f"{RAW_DATA_FOLDER}/audio"
    audio_filename = f"{RAW_DATA_FOLDER}/audio.mp3"
    output_metadata_filename=f"{RAW_DATA_FOLDER}/video_metadata.csv"

    main()

    shutil.rmtree(FRAME_FOLDER)
    shutil.rmtree(RAW_DATA_FOLDER)
    