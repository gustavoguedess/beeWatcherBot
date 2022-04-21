import requests
from bs4 import BeautifulSoup

from beecrawler import BeeCrawler
beecrawler = BeeCrawler()

def get_problem(id):
    id = str(id).lower()
    if id.startswith('bee') or id.startswith('uri'):
        return beecrawler.get_problem(id)
    elif id.startswith('cf'):
        return codeforces_get_problem(id)
    elif id.startswith('spoj'):
        return spoj_get_problem(id)
    elif id.startswith('atc'):
        return atcoder_get_problem(id)
    elif id.startswith('uva'):
        return uva_get_problem(id)
    else:
        return None

def codeforces_get_problem(id_complete):
    id = id_complete.replace('cf','')
    contest, question = id[:-1], id[-1]
    if not contest.isnumeric() or not question.isalpha():
        return None
    if not question: question = ''

    url = f'https://codeforces.com/contest/{contest}/problem/{question}'
    response = requests.get(url)
    if response.status_code != 200:
        url = f'https://codeforces.com/problemset/problem/{contest}/{question}'
        response = requests.get(url)
    if response.status_code != 200:
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    problem = {}
    problem['judge'] = 'CodeForces'
    problem['short_judge'] = 'CF'
    problem['id'] = contest + question.upper()
    problem['short_id'] = problem['short_judge'] + ' ' + problem['id']
    problem['title'] = soup.select_one('div.title').text.strip()
    problem['url'] = url
    return problem

def spoj_get_problem(id_complete):
    id = id_complete[len('spoj'):]
    if not id.isalpha():
        return None
    id = id.upper()
    url = f'https://www.spoj.com/problems/{id}/'
    response = requests.get(url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    problem = {}
    problem['judge'] = 'SPOJ'
    problem['short_judge'] = 'SPOJ'
    problem['id'] = id.upper()
    problem['short_id'] = problem['short_judge'] + ' ' + problem['id']
    problem['title'] = soup.select_one('h2.problem-statement').text.strip()
    problem['url'] = url
    return problem

def atcoder_get_problem(id_complete):
    id = id_complete[len('atc'):]
    contest, question = id[:-1], id[-1]

    if not contest.isalnum() or not question.isalpha():
        return None

    url = f'https://atcoder.jp/contests/{contest}/tasks/{contest}_{question}'
    response = requests.get(url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    problem = {}
    problem['judge'] = 'AtCoder'
    problem['short_judge'] = 'AtC'
    problem['id'] = contest.upper() + question.upper()
    problem['short_id'] = problem['short_judge'] + ' ' + problem['id']
    problem['title'] = soup.select_one('span.h2', text=True).text.strip()
    problem['url'] = url
    return problem

def uva_get_problem(id_complete):
    id = id_complete[len('uva'):]
    if not id.isnumeric():
        return None
        
    url = f'https://uhunt.onlinejudge.org/api/p/num/{id}'
    response = requests.get(url)
    if response.status_code != 200:
        return None
    pid = response.json()['pid']
    title = response.json()['title']
    url = f'https://onlinejudge.org/index.php?option=com_onlinejudge&Itemid=8&category=24&page=show_problem&problem={pid}'

    problem = {}
    problem['judge'] = 'UVA'
    problem['short_judge'] = 'UVA'
    problem['id'] = id
    problem['short_id'] = problem['short_judge'] + ' ' + problem['id']
    problem['title'] = title
    problem['url'] = url
    return problem