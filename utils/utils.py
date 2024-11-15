import re
import pandas as pd
import requests
import numpy as np
import boto3
import json
import os
import shutil
import glob


def get_secret_value(key_name):
    client = boto3.client('secretsmanager', region_name='eu-west-3')

    secret_key = f"spotit-prod-{key_name}"
    response = client.get_secret_value(SecretId=secret_key)
    secret_dict = json.loads(response['SecretString'])

    return secret_dict

def tiktok_or_instagram(url):
    if "tiktok.com" in url :
        return "tiktok"
    elif "instagram.com" in url:
        return "instagram"
    else:
        return "web"
    
def is_valid_url(url):
    pattern = r"(https?://)?(www\.)/.*"
    if re.match(pattern, url):
        return True
    else:
        return False
    


def build_photo_url(photo_reference, api_key, max_width=400):
    base_url = "https://maps.googleapis.com/maps/api/place/photo"
    return f"{base_url}?photoreference={photo_reference}&maxwidth={max_width}&key={api_key}"

def encoded_types(types):
    for type in types:
        if type is ['colloquial_area', 'administrative_area_level_0','administrative_area_level_1','administrative_area_level_2','administrative_area_level_3','administrative_area_level_4','administrative_area_level_5','administrative_area_level','administrative_area']:
            type = 'territory'
        elif type is ['tourist attraction']:
            type = 'tourist attraction'
        elif type is ['point_of_interest']:
            type = 'point of interest'
        elif type is ['art_gallery']:
            type = 'art gallery'
        elif type is ['meal_takeaway']:
            type = 'restaurant'
    return types

def get_pictures(details, API_KEY):
    photos = [build_photo_url(photo.get('photo_reference'), API_KEY) for photo in details.get('photos', [])]
    if len(photos) == 0:
        photos = ['https://pqhcubzkrlbvljbvsmem.supabase.co/storage/v1/object/public/assets/noImageAvailable.png?t=2024-11-07T11%3A10%3A54.812Z']
    return photos

def get_place_details(place_name: list, nplace: int, API_KEY: str):
    place_informations_list = []
    print(nplace)
    for n in range(nplace):
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={place_name[n]}&key={API_KEY}"
        response = requests.get(url)
        results = response.json().get('results', [])
        
        if results:
            place = results[0]
            place_id = place['place_id']
            
            details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}"
            details_response = requests.get(details_url)
            details = details_response.json().get('result', {})
            
            name = details.get('name')
            address = details.get('formatted_address')
            html_adress = details.get("adr_address")
            types = details.get('types')
            user_rating = details.get('user_ratings_total')
            rating = details.get('rating')
            photos = [build_photo_url(photo.get('photo_reference'), API_KEY) for photo in details.get('photos', [])]
            maps_url = details.get('url')
            geometry = details.get('geometry', {})
            location = geometry.get('location', {})
            place_lon = location.get('lng')
            place_lat = location.get('lat')
            business_status = details.get('business_status')



            
            current_informations = {
                "Name": name,
                "Address": address,
                "HTML_address" : html_adress,
                "Types": encoded_types(types),
                "Rating_count": user_rating,
                "Rate": rating,
                "Pictures" : photos,
                "Maps_url" : maps_url,
                'Longitude' : place_lon,
                'Latitude' : place_lat,
                'Status' : business_status
            }
            
            place_informations_list.append(current_informations)
            
            print(f"Name_{n}:", name)
            print(f"Address_{n}:", address)
            print(f"Types_{n}:", types)
            print(f"User ratings total_{n}:", user_rating)
            print(f"Rating_{n}:", rating)
            print(f"Maps_url_{n}:", maps_url)
            print(f"Pictures_{n}:", photos)
            print(""" 
                  
                  -------- 
                  
                  """)
        else:
            print(f"No place found for '{place_name[n]}'.")

    place_informations = pd.DataFrame(place_informations_list)
    place_informations.fillna(0, inplace=True)

    
    return place_informations


def create_formated_places(data, nplaces):
    research_places = []
    for n in range(1, nplaces+1):
        if data['city'][0] == 'Various cities':
            formated_adress = data[f"place_{n}"][0] +" "+ data["country"][0]
        else : 
            formated_adress = data[f"place_{n}"][0] +" "+ data["city"][0] +" "+ data["country"][0]
        research_places.append(formated_adress)
    
    print(research_places)
    return research_places

def upload_to_supabase(referenced_dataframe, video_url, supabase, data):
    for n in range(len(referenced_dataframe)):
        response = (
            supabase.table("referenced_places")
            .insert({
                "video_url": video_url,
                "place_name" : referenced_dataframe["Name"][n],
                "placeAddress" : referenced_dataframe["Address"][n],
                "place_html_address" : referenced_dataframe["HTML_address"][n],
                "placeTypes" : referenced_dataframe["Types"][n],
                "place_rating_count" : int(referenced_dataframe["Rating_count"][n]),
                "place_rate" : float(referenced_dataframe["Rate"][n]),
                "place_city" : data["city"][0],
                "place_country" : data["country"][0],
                "place_pictures" : referenced_dataframe["Pictures"][n],
                "place_map_url" : referenced_dataframe["Maps_url"][n],
                'placeLat' : referenced_dataframe['Latitude'][n],
                'placeLon': referenced_dataframe['Longitude'][n],
                'latitude' : referenced_dataframe['Latitude'][n],
                'longitude': referenced_dataframe['Longitude'][n],
                'imageUrl' : referenced_dataframe['Pictures'][n][0],
                'title' : referenced_dataframe["Name"][n],
                })
            .execute()
        )



def upload_raw_to_supabase(video_url, video_description, video_frame_text,video_audio,cleaned_text,data, supabase, nplace):
    list_of_places = []
    for i in range(1, nplace+1):
        list_of_places.append(data[f"place_{i}"][0])
    response = (
        supabase.table("generated_text")
        .insert({
            "video_url": video_url,
            "video_description_text" : video_description,
            "video_frame_text" : video_frame_text ,
            "video_audio_text" : video_audio,
            "video_cleaned_text" : cleaned_text,
            "place_number" : int(data["place_number"][0]),
            "place_city" : data["city"][0],
            "place_country" : data["country"][0],
            "output" : list_of_places
            })
        .execute()
    )

def url_exist(video_url, supabase):
    response = (
        supabase.table("referenced_places")
        .select("*")
        .eq("video_url", video_url)
        .execute()
    )

    if response.data:
        data = pd.DataFrame(response.data)
        print(f"L'URL existe dans la base de données. Nombre d'entrées : {len(data)}")
    else:
        data = pd.DataFrame() 
        print("L'URL n'existe pas dans la base de données.")
    print(f"taille du df :" + str(len(data)))
    return data


def clean_and_make_dir(path):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)



def clean_mp4_files(folder_path):
    mp4_files = glob.glob(os.path.join(folder_path, "*.mp4"))
    
    for file_path in mp4_files:
        os.remove(file_path)


def clean_all(data_folder, frame_folder, video_path):
    clean_and_make_dir(data_folder)
    clean_and_make_dir(frame_folder)
    clean_mp4_files(video_path)