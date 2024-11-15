
import requests 
import pandas as pd
from bs4 import BeautifulSoup
from utils.utils import *
from utils.tiktok import *


def forecast_web_places(url,gpt_client):
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    h1 = soup.findAll('h1')
    h2 = soup.findAll('h2')
    h3 = soup.findAll('h3')
    h4 = soup.findAll('h4')
    h5 = soup.findAll('h5')
    h6 = soup.findAll('h6')
    p = soup.findAll('p')
    span = soup.findAll('span')
    titles = [h1,h2,h3,h4,h5,h6,span,p]

    list_of_titles = []
    for title in titles:
        for n in range(len(title)):
            list_of_titles.append(title[n].text)
    print(list_of_titles)
    input_text = ' '.join(list_of_titles)
    cleaned_text = clean_text(str(input_text))
    new = remove_duplicates(cleaned_text)
    new = preprocess_text(new)
    output = nlp_forecast(gpt_client, str(new))
    print(output)
    dico = eval(output)
    data = pd.DataFrame(dico, index=[0])

    return data

