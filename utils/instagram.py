import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from moviepy import *
import pandas as pd
import whisper
import ffmpeg
import easyocr
import re
from utils.utils import *


def download_file(url, file_path):
    response = requests.get(url, stream=True)
    with open(file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
    print(f"Download : {file_path}")

def get_post_description(post_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(post_url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    description = soup.find('meta', {'property': 'og:description'})['content']
    driver.quit()
    print(f"Post description : {description}")
    return description

def convert_video_to_audio(filepath,RAW_DATA_FOLDER ):
    try:
        video = VideoFileClip(filepath)
        video.audio.write_audiofile(f"{RAW_DATA_FOLDER}/audio.mp3")
        video_time = video.duration
        print('video tiùme' , video_time)
        return video_time
    except Exception:
        return 0


def download_instagram_post(post_url, RAW_DATA_FOLDER):
    shortcode = post_url.split("/")[-2]
    print(shortcode)
    description = get_post_description(post_url)
    api_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
    print(api_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    
    response = requests.get(api_url, headers=headers)
    video_time, video_title = None, None  # Initialisation par défaut
    try:
        media_data = response.json()['graphql']['shortcode_media']
        if media_data['is_video']:
            print('in a video')
            video_url = media_data['video_url']
            video_title = os.path.join(RAW_DATA_FOLDER, f"{shortcode}.mp4")
            download_file(video_url, video_title)
            video_time = convert_video_to_audio(video_title, RAW_DATA_FOLDER)
        else:
            if 'edge_sidecar_to_children' in media_data:
                print('carrousel')
                for edge in media_data['edge_sidecar_to_children']['edges']:
                    node = edge['node']
                    if node['is_video']:
                        video_url = node['video_url']
                        video_title = os.path.join(RAW_DATA_FOLDER, f"{node['id']}.mp4")
                        download_file(video_url, video_title)
                        video_time = convert_video_to_audio(video_title, RAW_DATA_FOLDER)
                    else:
                        image_url = node['display_url']
                        video_title = os.path.join(RAW_DATA_FOLDER, f"{node['id']}.jpg")
                        download_file(image_url, video_title)
            else:
                print('no carrousel')
                image_url = media_data['display_url']
                video_title = os.path.join(RAW_DATA_FOLDER, f"{shortcode}.jpg")
                download_file(image_url, video_title)
                
        return description, video_time, video_title
    except Exception as e:
        print('ERROR DUE TO : ', str(e))
        return "", 0, "" 


def transcript_audio_to_text(audio_filename, is_music):
    if is_music is False : 
        model = whisper.load_model("base")
        result = model.transcribe(audio_filename)
        text = result["text"]
        return text
    else:
        return ""
    
def extract_video_frames(video_title ,FRAME_FOLDER, fps = 1):
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


def extract_text_from_frames(reader, frame_folder):
    video_frame_text = []
    for frame in os.listdir(frame_folder):
        result = reader.readtext(f"{frame_folder}/{frame}")
        for detection in result:
            video_frame_text.append(detection[1])
    print( video_frame_text)
    return video_frame_text


def generate_input_text(video_description, video_audio, video_frame_text):
    generated_texts = video_description , video_audio ,  " ".join(video_frame_text)
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
    video_description, video_time, video_title = download_instagram_post(video_url, RAW_DATA_FOLDER)
    print(video_title)
    try:
        video_audio = transcript_audio_to_text(f"{RAW_DATA_FOLDER}/audio.mp3", False)
    except Exception as e:
        video_audio = None
    print(f"video time : {video_time} seconds")
    extract_video_frames(video_title, FRAME_FOLDER)
    reader = create_reader()
    video_frame_text = extract_text_from_frames(reader, frame_folder=FRAME_FOLDER)
    input_text = generate_input_text(video_description, video_audio, video_frame_text)
    cleaned_text = clean_text(str(input_text))
    new = remove_duplicates(cleaned_text)
    new = preprocess_text(new)
    print("preprocessed text : " + new)
    output = nlp_forecast(gpt_client, str(input_text))
    dico = eval(output)
    data = pd.DataFrame(dico, index=[0])
    print(data.head())
    upload_raw_to_supabase(video_url, video_description, video_frame_text, video_audio, new, data, supabase, int(data["place_number"]))

    return data
