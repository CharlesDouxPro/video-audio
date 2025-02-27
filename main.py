from os import environ as env
from utils.instagram import *
from utils.tiktok import *
from utils.utils import *
from utils.web import *
from supabase import create_client, Client
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
from openai import OpenAI


RAW_DATA_FOLDER = "DATA"
FRAME_FOLDER = "FRAMES"


app = FastAPI()

clean_all(RAW_DATA_FOLDER, FRAME_FOLDER, './')

OPENAI_ACCESS_KEY = get_secret_value('openai-access-key').get('OPENAI_API_KEY')
SUPABASE_ACCESS_KEY = get_secret_value('supabase-access-key').get('SUPABASE_KEY')
SUPABASE_URL = get_secret_value('supabase-url').get('SUPABASE_URL')
GOOGLE_API_KEY = get_secret_value('google-access-key').get('GOOGLE_API_KEY')


class VideoRequest(BaseModel):
    url: str


pd.set_option('display.max_colwidth', None)
gpt_client = OpenAI(api_key=OPENAI_ACCESS_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ACCESS_KEY)


@app.get("/")
def index():
    return {"details": "hello world!"}

@app.post("/process_video/")
def process_video(request: VideoRequest):
    clean_all(RAW_DATA_FOLDER, FRAME_FOLDER, './')
    url = request.url
    start = datetime.now()
    referenced_dataframe = url_exist(url, supabase)
    if referenced_dataframe.empty:
        platform = tiktok_or_instagram(url)
        print(platform)
        if platform == "tiktok":
            places = forecast_tiktok_places(url, RAW_DATA_FOLDER, FRAME_FOLDER, gpt_client, supabase)
        elif platform == "instagram":
            places = forecast_instagram_places(url, RAW_DATA_FOLDER, FRAME_FOLDER, gpt_client, supabase)
        elif platform == "web":
            places = forecast_web_places(url, gpt_client)
        nplace = int(places["place_number"])
        if nplace == 0:
            return {"status": "warning", "message": "No place found", "data": " "}
        else:
            formated_places, city = create_formated_places(places, nplace)
            referenced_dataframe = get_place_details(formated_places, len(formated_places), GOOGLE_API_KEY, city) 
            upload_to_supabase(referenced_dataframe, url, supabase, places)
            formatted_data = referenced_dataframe.to_dict(orient="records")
            end = datetime.now()
            time = end - start
            print("status", "success",'in', time, 'seconds')
            clean_all(RAW_DATA_FOLDER, FRAME_FOLDER, './')
            print('refere')
            return {"status": "success", "message": "Video processed", "data": formatted_data}
    else:
        formatted_data = referenced_dataframe.to_dict(orient="records")
        print("status", "exists")
        clean_all(RAW_DATA_FOLDER, FRAME_FOLDER, './')
        return {"status": "exists", "message": "Video URL already exists", "data": formatted_data}

