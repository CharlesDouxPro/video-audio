import os
import shutil
from utils.instagram import *
from utils.tiktok import *
from utils.utils import *
from supabase import create_client, Client
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd


app = FastAPI()

class VideoRequest(BaseModel):
    video_url: str

RAW_DATA_FOLDER = "DATA"
FRAME_FOLDER = "FRAMES"
os.makedirs(FRAME_FOLDER, exist_ok=True)
os.makedirs(RAW_DATA_FOLDER, exist_ok=True)

pd.set_option('display.max_colwidth', None)
OPENAI_API_KEY = "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"
gpt_client = OpenAI(api_key=OPENAI_API_KEY)

url: str = "https://pqhcubzkrlbvljbvsmem.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxaGN1YnprcmxidmxqYnZzbWVtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjc4NzgyNDYsImV4cCI6MjA0MzQ1NDI0Nn0.5Yt2zMMm09II29COY58lXIvIQID1N7FM6JL3-B9jhdU"
supabase: Client = create_client(url, key)


@app.post("/process_video/")
def process_video(request: VideoRequest):
    video_url = request.video_url

    if is_valid_url(video_url):
        referenced_dataframe = url_exist(video_url, supabase)
        if referenced_dataframe.empty:
            platform = tiktok_or_instagram(video_url)
            if platform == "tiktok":
                places = forecast_tiktok_places(video_url, RAW_DATA_FOLDER, FRAME_FOLDER, gpt_client, supabase)
            elif platform == "instagram":
                places = forecast_instagram_places(video_url, RAW_DATA_FOLDER, FRAME_FOLDER, gpt_client, supabase)

            nplace = int(places["place_number"])
            formated_places = create_formated_places(places, nplace)
            referenced_dataframe = get_place_details(formated_places, len(formated_places)) 
            upload_to_supabase(referenced_dataframe, video_url, supabase, places)
            return {"status": "success", "message": "Video processed", "data": referenced_dataframe.head().to_json()}
        else:
            return {"status": "exists", "message": "Video URL already exists", "data": referenced_dataframe.to_json()}
    else:
        return {"status": "error", "message": "URL is not valid, are you sure this is an Instagram post or TikTok video?"}

@app.on_event("shutdown")
def clean_up():
    shutil.rmtree(FRAME_FOLDER)
    shutil.rmtree(RAW_DATA_FOLDER)
