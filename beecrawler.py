import requests
from bs4 import BeautifulSoup
import re 

class BeeCrawler:
    def __init__(self):
        self.url_base = 'https://www.beecrowd.com.br/judge'
    
    def search_username(self, username):
        url = f'{self.url_base}/search?q={username}&for=users'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        a_list = soup.select('div.search-user a')
        users_code = [a['href'].split('/')[-1] for a in a_list]
        return users_code
    
    def get_info(self, id):
        url = f'{self.url_base}/profile/{id}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        ul = soup.select('ul.pb-information li')
        user_info = {}
        user_info['username'] = soup.select_one('div.pb-username p a').text

        for li in ul:
            key, value = li.text.replace('\n','').strip().split(':')
            key = key.lower()
            user_info[key] = value
        
        user_info['points'] = int(float(user_info['points'].replace(',','')))
        user_info['id']=id
        return user_info
