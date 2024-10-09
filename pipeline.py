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
from utils.instagram import *
from utils.tiktok import *

RAW_DATA_FOLDER = "DATA"
FRAME_FOLDER = "FRAMES"

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
    