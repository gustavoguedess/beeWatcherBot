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
        users = []
        for a in a_list:
            user = {}
            user['username'] = a.text
            user['id'] = a['href'].split('/')[-1]
            users.append(user)
        return users

    def get_id_from_username(self, username):
        users = self.search_username(username)
        for user in users:
            if user['username'] == username:
                return user['id']
        return None
        
    def get_profile_info(self, id:str=None, username:str=None):
        if id is None and username is None: return None
        if id is None: id = self.get_id_from_username(username)
        if id is None: return None
        

        url = f'{self.url_base}/profile/{id}'
        response = requests.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        ul = soup.select('ul.pb-information li')
        user_info = {}
        user_info['username'] = soup.select_one('div.pb-username p a').text
        user_info['avatar'] = soup.select_one('div.pb-avatar img')['src']

        for li in ul:
            key, value = li.text.replace('\n','').strip().split(':')
            key = key.lower()
            user_info[key] = value
        
        user_info['points'] = int(float(user_info['points'].replace(',','')))
        user_info['id']=id
        return user_info

    def bulk_profile_info(self, ids:list):
        users = []
        for id in ids:
            user = self.get_profile_info(id)
            if user:
                users.append(user)
        return users

    def get_problem(self, id_complete:str):
        id_complete = id_complete.replace('uri', 'bee')

        id = id_complete.replace('bee','')
        if not id.isnumeric():
            return None
        id = int(id)

        url = f'https://www.beecrowd.com.br/repository/UOJ_{id}_en.html'
        response = requests.get(url)
        if response.status_code != 200:
            url = f'https://www.beecrowd.com.br/repository/UOJ_{id}.html'
            response = requests.get(url)
        if response.status_code != 200:
            url = f'https://www.beecrowd.com.br/repository/UOJ_{id}_pt.html'
            response = requests.get(url)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')

        problem = {}
        problem['judge'] = 'Beecrowd'
        problem['short_judge'] = 'Bee'
        problem['id'] = str(id)
        problem['short_id'] = problem['short_judge'] + ' ' + problem['id']
        problem['title'] = soup.select_one('h1').text
        problem['url'] = url

        return problem
