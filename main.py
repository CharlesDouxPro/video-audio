import os
from os import environ as env
import shutil
from utils.instagram import *
from utils.tiktok import *
from utils.utils import *
from supabase import create_client, Client
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from botocore.exceptions import ClientError
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

RAW_DATA_FOLDER = "DATA"
FRAME_FOLDER = "FRAMES"

clean_and_make_dir(RAW_DATA_FOLDER)
clean_and_make_dir(FRAME_FOLDER)
clean_mp4_files("./")
app = FastAPI()

# OPENAI_ACCESS_KEY = get_secret_value('openai-access-key').get('OPENAI_API_KEY')
# SUPABASE_ACCESS_KEY = get_secret_value('supabase-access-key').get('SUPABASE_KEY')
# SUPABASE_URL = get_secret_value('supabase-url').get('SUPABASE_URL')

OPENAI_ACCESS_KEY="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"
SUPABASE_URL="https://pqhcubzkrlbvljbvsmem.supabase.co"
SUPABASE_ACCESS_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxaGN1YnprcmxidmxqYnZzbWVtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjc4NzgyNDYsImV4cCI6MjA0MzQ1NDI0Nn0.5Yt2zMMm09II29COY58lXIvIQID1N7FM6JL3-B9jhdU"

class VideoRequest(BaseModel):
    video_url: str


pd.set_option('display.max_colwidth', None)
gpt_client = OpenAI(api_key=OPENAI_ACCESS_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ACCESS_KEY)


@app.get("/")
def index():
    return {"details": "hello world!"}

@app.post("/process_video/")
def process_video(request: VideoRequest):
    video_url = request.video_url
    start = datetime.now()
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
            formatted_data = referenced_dataframe.to_dict(orient="records")
            end = datetime.now()
            time = end - start
            print("status", "success",'in', time, 'seconds')
            return {"status": "success", "message": "Video processed", "data": formatted_data}
        else:
            formatted_data = referenced_dataframe.to_dict(orient="records")
            print("status", "exists")
            return {"status": "exists", "message": "Video URL already exists", "data": formatted_data}
    else:
        print("status error")
        return {"status": "error", "message": "URL is not valid, are you sure this is an Instagram post or TikTok video?"}


