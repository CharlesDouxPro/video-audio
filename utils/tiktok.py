import yt_dlp as yt
import whisper
import pyktok as pyk
import pandas as pd
import os
import ffmpeg
import easyocr
import os
from collections import Counter
import re
from utils.utils import *

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
    print(video_url)
    with yt.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def transcript_audio_to_text(audio_filename, is_music):
    if is_music is False : 
        model = whisper.load_model("base")
        result = model.transcribe(audio_filename)
        text = result["text"]


        return text
    else:
        return "", " "


def get_tiktok_metadata(video_url, output_metadata_filename):
    pyk.save_tiktok(video_url,
                False,
                output_metadata_filename)
    

def extract_metadata(output_metadata_filename):
    data = pd.read_csv(output_metadata_filename)
    video_author = data["author_username"][0]
    video_id = data["video_id"][0]
    video_time = data["video_duration"][0]
    video_title = f"@{video_author}_video_{video_id}.mp4"
    video_description = data["video_description"][0]
    return video_title, video_description, video_time


def download_video(video_url, output_metadata_filename, video_time):
    if video_time <= 150:
        pyk.save_tiktok(video_url,
                True,
                output_metadata_filename)


def extract_video_frames(video_title , video_time, FRAME_FOLDER, fps = 1):
    if video_time > 150:
        print("Video too long, no video extraction")
        return 
    else:
        output_frames = f'{FRAME_FOLDER}/frame_%04d.png'
        (
            ffmpeg
            .input(video_title)
            .output(output_frames, vf=f'fps={fps}')
            .run()
        )

        print("Frames extraction done.")


def create_reader():
    reader = easyocr.Reader(['en','fr','es','it','de'])
    return reader


def extract_text_from_frames(reader, frame_folder, video_time):
    if video_time > 150 : 
        print("no frame extraction")
        return " "
    else:
        video_frame_text = []
        for frame in os.listdir(frame_folder):
            result = reader.readtext(f"{frame_folder}/{frame}")
            for detection in result:
                video_frame_text.append(detection[1])
        print( video_frame_text)
        return video_frame_text


def clean_text_list(text_list):
    return text_list

def generate_input_text(video_description, video_audio, video_frame_text):

    video_frame_text = " ".join(video_frame_text)
    print(f"""


            video description : {video_description}



            video audio : {video_audio}



            video_frame_text : {video_frame_text}



          """)
    generated_texts = video_description  + "\n" + video_audio + "\n" + video_frame_text
    print(generated_texts)
    return generated_texts



def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'[@#]\w+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s,.\'’-]', '', text) 
    return text


def remove_duplicates(text):
    words = text.split()
    seen = set()
    unique_words = []
    for word in words:
        if word not in seen:
            unique_words.append(word)
            seen.add(word)
    
    return ' '.join(unique_words)

def preprocess_text(text):
    cleaned_text = re.sub(r"[^\w\s,]", "", text)
    cleaned_text = re.sub(r",+", ",", cleaned_text)
    cleaned_text = cleaned_text.replace(",,", ",")  
    cleaned_text = cleaned_text.strip()
    return cleaned_text


def forecast_tiktok_places(video_url, RAW_DATA_FOLDER, FRAME_FOLDER, gpt_client, supabase):
    download_tiktok_audio(video_url, f"{RAW_DATA_FOLDER}/audio")
    video_audio = transcript_audio_to_text(f"{RAW_DATA_FOLDER}/audio.mp3", False)
    get_tiktok_metadata(video_url, f"{RAW_DATA_FOLDER}/video_metadata.csv")
    video_title, video_description, video_time = extract_metadata(f"{RAW_DATA_FOLDER}/video_metadata.csv")
    print(f"video time : {video_time} seconds")
    download_video(video_url, f"{RAW_DATA_FOLDER}/video_metadata.csv", video_time)
    extract_video_frames(video_title, video_time,FRAME_FOLDER)
    reader = create_reader()
    video_frame_text = extract_text_from_frames(reader, frame_folder=FRAME_FOLDER, video_time=video_time)
    input_text = generate_input_text(video_description, video_audio, video_frame_text)
    output = nlp_forecast(gpt_client, str(input_text))
    dico = eval(output)
    data = pd.DataFrame(dico, index=[0])
    print(data.head())
    upload_raw_to_supabase(video_url, video_description, video_frame_text, video_audio, input_text, data, supabase, int(data["place_number"]))
    return data




