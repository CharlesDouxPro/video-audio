import re
import pandas as pd
import requests
import numpy as np

def tiktok_or_instagram(url):
    if "tiktok.com" in url :
        return "tiktok"
    elif "instagram.com" in url:
        return "instagram"
    else:
        return " "
    
def is_valid_url(url):
    # Expression régulière pour vérifier que le domaine est bien TikTok ou Instagram
    pattern = r"(https?://)?(www\.)?(tiktok\.com|instagram\.com)/.*"
    if re.match(pattern, url):
        return True
    else:
        return False
    


API_KEY = 'AIzaSyCo-rjmf08Vh4sRAXdyW1Ll92ykDTHCkE4'

def get_place_details(place_name: list, nplace: int):
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
            
            current_informations = {
                "Name": name,
                "Address": address,
                "HTML_address" : html_adress,
                "Types": types,
                "Rating_count": user_rating,
                "Rate": rating
            }
            
            place_informations_list.append(current_informations)
            
            print(f"Name_{n}:", name)
            print(f"Address_{n}:", address)
            print(f"Types_{n}:", types)
            print(f"User ratings total_{n}:", user_rating)
            print(f"Rating_{n}:", rating)
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
                "place_address" : referenced_dataframe["Address"][n],
                "place_html_address" : referenced_dataframe["HTML_address"][n],
                "place_types" : referenced_dataframe["Types"][n],
                "place_rating_count" : int(referenced_dataframe["Rating_count"][n]),
                "place_rate" : float(referenced_dataframe["Rate"][n]),
                "place_city" : data["city"][0],
                "place_country" : data["country"][0],
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