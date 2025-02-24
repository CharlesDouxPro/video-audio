import requests
import os
from moviepy.editor import *
import pandas as pd
import whisper
import ffmpeg 
import easyocr
import re
from utils.utils import *
import instaloader

L = instaloader.Instaloader()


def download_file(url, file_path):
    response = requests.get(url, stream=True)
    with open(file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
    print(f"Download : {file_path}")

def convert_video_to_audio(filepath,RAW_DATA_FOLDER ):
    try:
        video = VideoFileClip(filepath)
        video.audio.write_audiofile(f"{RAW_DATA_FOLDER}/audio.mp3")
        video_time = video.duration
        return video_time
    except Exception:
        return 0
    
def get_post_metadata(post_url):
    type_p = post_url.split("/")
    shortcode = post_url.split("/")[-2]
    post_type = post_type(post_url)[3]
    return type_p, shortcode


def download_instagram_post(post_url, RAW_DATA_FOLDER):
    shortcode = post_url.split("/")[-2]
    media_titles = []
    print(shortcode)
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    description = post.caption
    print(description)
    if post.typename == "GraphSidecar":
        print("Carrousel détecté")
        for index, sidecar in enumerate(post.get_sidecar_nodes()):
            media_url = sidecar.display_url
            filename = os.path.join(RAW_DATA_FOLDER, f"{shortcode}_{index}")
            L.download_pic(filename, media_url, post.date_utc)
            media_titles.append(f"{filename}.jpg")
            print(f"Téléchargé : {filename} ({'image'})")
        is_video = False
    else:
        filename = os.path.join(RAW_DATA_FOLDER, f"{shortcode}")
        L.download_pic(filename, post.video_url, post.date_utc)
        filename = f"{filename}.mp4"
        media_titles.append(filename)
        is_video = True

    return description, 0, media_titles, is_video



def transcript_audio_to_text(audio_filename : list, is_music):
    if is_music is False : 
        model = whisper.load_model("base")
        result = model.transcribe(audio_filename)
        text = result["text"]
        return text
    else:
        return ""
    
def extract_video_frames(media_title ,FRAME_FOLDER, fps = 1):
    print(media_title)
    output_frames = f'{FRAME_FOLDER}/frame_%04d.png'
    (
        ffmpeg
        .input(media_title)
        .output(output_frames, vf=f'fps={fps}')
        .run()
    )
    print("Frames extraction done.")

def create_reader():
    reader = easyocr.Reader(['en','fr','es','it','de'])
    return reader


def extract_text_from_frames(reader, frame_folder):
    video_frame_text = []
    for frame in os.listdir(frame_folder):
        result = reader.readtext(f"{frame_folder}/{frame}")
        for detection in result:
            video_frame_text.append(detection[1])
    return video_frame_text

from collections import Counter

def clean_text_list(text_list):
    filtered_words = [word for word in text_list if not re.fullmatch(r"[\W\d]+", word)]
    cleaned_words = [re.sub(r"[^\w\sÀ-ÿ']", "", word).strip() for word in filtered_words]
    cleaned_words = [word for word in cleaned_words if len(word) > 2]
    corrected_text = " ".join(cleaned_words)
    words = corrected_text.split()
    word_counts = Counter(words)
    final_text = " ".join([word for word in words if word_counts[word] < 3])
    return final_text

def generate_input_text(video_description, video_audio, video_frame_text):

    video_frame_text = clean_text_list(video_frame_text)
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


def forecast_instagram_places(video_url, RAW_DATA_FOLDER, FRAME_FOLDER, gpt_client, supabase):
    video_description, video_time, media_title, is_video = download_instagram_post(video_url, RAW_DATA_FOLDER)
    try:
        video_audio = transcript_audio_to_text(media_title[0], False)
    except Exception:
        video_audio = ""
    print(f"video time : {video_time} seconds")
    extract_video_frames(media_title[0], FRAME_FOLDER)
    reader = create_reader()
    video_frame_text = extract_text_from_frames(reader, frame_folder=(FRAME_FOLDER if is_video else RAW_DATA_FOLDER))
    input_text = generate_input_text(video_description, video_audio, video_frame_text)
    print("preprocessed text : " + input_text)
    output = nlp_forecast(gpt_client, str(input_text))
    dico = eval(output)
    data = pd.DataFrame(dico, index=[0])
    print(data.head())
    upload_raw_to_supabase(video_url, video_description, video_frame_text, video_audio, input_text, data, supabase, int(data["place_number"]))

    return data
