import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import base64
from moviepy.editor import *
import pandas as pd
import whisper
import ffmpeg
import easyocr
import re
from openai import OpenAI
from utils.utils import upload_raw_to_supabase





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
    video = VideoFileClip(filepath)
    video.audio.write_audiofile(f"{RAW_DATA_FOLDER}/audio.mp3")
    video_time = video.duration
    return video_time

def download_instagram_post(post_url, RAW_DATA_FOLDER):
    shortcode = post_url.split("/")[-2]
    description = get_post_description(post_url)
    api_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    response = requests.get(api_url, headers=headers)
    
    if response.status_code != 200:
        print("Impossible to fetch post data.")
        return

    media_data = response.json()['graphql']['shortcode_media']
    if media_data['is_video']:
        video_url = media_data['video_url']
        video_title = os.path.join(RAW_DATA_FOLDER, f"{shortcode}.mp4")
        download_file(video_url, video_title)
        video_time = convert_video_to_audio(video_title,RAW_DATA_FOLDER)
    else:
        if 'edge_sidecar_to_children' in media_data:
            for edge in media_data['edge_sidecar_to_children']['edges']:
                node = edge['node']
                if node['is_video']:
                    video_url = node['video_url']
                    video_title = os.path.join(RAW_DATA_FOLDER, f"{node['id']}.mp4")
                    download_file(video_url, video_title)
                    video_time = convert_video_to_audio(video_title)
                else:
                    image_url = node['display_url']
                    video_title = os.path.join(RAW_DATA_FOLDER, f"{node['id']}.jpg")
                    download_file(image_url, video_title)
        else:
            image_url = media_data['display_url']
            video_title = os.path.join(RAW_DATA_FOLDER, f"{shortcode}.jpg")
            download_file(image_url, video_title)
    return description, video_time, video_title

def transcript_audio_to_text(audio_filename, is_music):
    if is_music is False : 
        model = whisper.load_model("base")
        result = model.transcribe(audio_filename)
        text = result["text"]
        print(f"text : {result["text"]}")
        return text
    else:
        return ""
    
def extract_video_frames(video_title , video_time,FRAME_FOLDER, fps = 1):
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


def nlp_forecast(client, text): 
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "You are usefull to seek places in a text with their city and country"
        }
      ]
    },
        {
            "role": "user",
            "content": (
            """
            Instructions:
                - Given the text at the end, find all the places to visit quote in this text. 
                - Take also care to the Name of the places who can be brand
                - Return the number of places you find
                - Return the city of these places in English
                - Return the country of these places in English
                - Do not return the same place multiple time
                - Return only in the python dictionary format like below
                - Do not include any additional formatting, such as markdown code blocks


            {
            "place_number" : "<number of places>",
            "place_1" : "<first place you find in the text>",
            "place_2" : "<second place you find in the text>", 
            ...,
            "place_n" : "<the nth place you find in the text>
            "city" :" <the city of these places>", 
            "country" : "<the country of these places>"
             },

             
            The text could be bad formated but just focus to find similitude with the places you know 
            There is the text to analyse :
            """ + text
            )
        }
    ]
    )
    output = completion.choices[0].message.content
    print(output)
    return output

def forecast_instagram_places(video_url, RAW_DATA_FOLDER, FRAME_FOLDER, gpt_client, supabase):
    video_description, video_time, video_title = download_instagram_post(video_url, RAW_DATA_FOLDER)
    print(video_title)
    video_audio = transcript_audio_to_text(f"{RAW_DATA_FOLDER}/audio.mp3", False)
    print(f"video time : {video_time} seconds")
    extract_video_frames(video_title, video_time, FRAME_FOLDER)
    reader = create_reader()
    video_frame_text = extract_text_from_frames(reader, frame_folder=FRAME_FOLDER, video_time=video_time)
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
