from dotenv import load_dotenv
import os 
load_dotenv()

BEEBOT_TOKEN = os.getenv("BEEBOT_TOKEN")

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters, PicklePersistence 
import logging
from beecrawler import BeeCrawler

beecrawler = BeeCrawler()

persistence = PicklePersistence(filename='db/database.json')
updater = Updater(token=BEEBOT_TOKEN, use_context=True, persistence=persistence)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bem vindo! Eu sou o Bee Watcher, eu monitoro o desenvolvimento de usuários do BeeCrowd.\nUse /help para saber mais.")

def help(update: Update, context: CallbackContext):
    text = """
    Comandos disponíveis:
    Use /addprofile username1 username2 ... para adicionar um (ou mais) novo perfil.
    Use /rmprofile username1 username2 ... para remover um (ou mais) perfil.
    Use /lsprofile para listar os perfil (usuários) cadastrados.
    Use /ranking para ver o ranking semanal.
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def addprofile_command(update: Update, context: CallbackContext):
    usernames = list(map(str.lower, context.args))
    success = []
    already_added = []
    fail = []

    for username in usernames:
        user = get_profile(username)
        if user:
            if context.chat_data.get('profiles', False) == False:
                context.chat_data['profiles'] = {}
            if context.chat_data['profiles'].get(user['id'], False):
                already_added.append(user['username'])
            else:
                success.append(user['username'])
                context.chat_data['profiles'][user['id']] = user
        else:
            fail.append(username)
    text = ''
    if len(success) == 1:
        text += f'O usuário {success[0]} foi adicionado com sucesso.\n\n'
    elif len(success) > 1:
        text += f'Os usuários {", ".join(success)} foram adicionados com sucesso.\n\n'
    if len(already_added) == 1:
        text += f'O usuário {already_added[0]} já está na lista.\n\n'
    elif len(already_added) > 1:
        text += f'Os usuários {", ".join(already_added)} já estão na lista.\n\n'
    if len(fail) == 1:
        text += f'O usuário {fail[0]} não foi encontrado.\n\n'
    elif len(fail) > 1:
        text += f'Os usuários {", ".join(fail)} não foram encontrados. Verifique os usernames\n'
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def get_profile(username):
    users_code = beecrawler.search_username(username)

    if len(users_code) == 0 or len(users_code) > 1:
        return None
    else:
        usercode = users_code[0]
        user = beecrawler.get_info(usercode)
        return user

def rmprofile_command(update: Update, context: CallbackContext):
    usernames = list(map(str.lower, context.args))
    success = []
    fail = []

    for username in usernames:
        user = get_profile(username)
        if user:
            if context.chat_data.get('profiles', False) == False:
                context.chat_data['profiles'] = {}
            if context.chat_data['profiles'].get(user['id'], False):
                success.append(user['username'])
                del context.chat_data['profiles'][user['id']]
            else:
                fail.append(user['username'])
        else:
            fail.append(username)
    text = ''
    if len(success) == 1:
        text += f'O usuário {success[0]} foi removido com sucesso.\n\n'
    elif len(success) > 1:
        text += f'Os usuários {", ".join(success)} foram removidos com sucesso.\n\n'
    if len(fail) == 1:
        text += f'O usuário {fail[0]} não está na lista.\n\n'
    elif len(fail) > 1:
        text += f'Os usuários {", ".join(fail)} não estão na lista.\n'
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def lsprofile_command(update: Update, context: CallbackContext):
    profiles_context = context.chat_data.get('profiles', {})

    if len(profiles_context) == 0:
        text = 'Não há nenhum perfil cadastrado.'
    else:
        profiles = []
        for code, user in profiles_context.items():
            profile = f'{user["username"]}'
            profile += f' [{user["university"]}]' if user['university'] else ''
            profiles.append(profile)    
        profiles.sort()
        
        text = "Profiles: \n" + '\n'.join(profiles)

    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def get_ranking(profiles):
    ranking = []
    for code, user in profiles.items():
        user_new = beecrawler.get_info(code)
        old_points = user['points']
        new_points = user_new['points']
        growth = new_points - old_points
        if growth != 0:
            profile = {
                'username': user['username'],
                'university': user['university'],
                'old_points': old_points,
                'new_points': new_points,
                'growth': growth
            }
            ranking.append(profile)
    ranking.sort(key=lambda x: x['growth'], reverse=True)
    return ranking

def ranking_text(ranking):
    text = "Ranking: \n"
    for position, user in enumerate(ranking):
        if position == 0:   text += f'🥇'
        elif position == 1: text += f'🥈'
        elif position == 2: text += f'🥉'
        text+= f'{user["username"]} '
        text+= f'[{user["university"]}]\n' if user['university'] else '\n'
        text+= f'{user["old_points"]} → {user["new_points"]} '
        text+= f'(+{user["growth"]})\n' if user['growth']>0 else f'({user["growth"]})\n'
        text+= '\n'
    return text

def ranking_command(update: Update, context: CallbackContext):
    profiles = context.chat_data.get('profiles', {})
    ranking = get_ranking(profiles)
    if len(profiles) == 0:
        text = 'Não há nenhum perfil cadastrado.'
    elif len(ranking) == 0:
        text = 'Não há nenhum perfil com pontuação alterada.'
    elif len(ranking) > 0:
        ranking = get_ranking(profiles)
        text = ranking_text(ranking)
            
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def searchprofile_command(update: Update, context: CallbackContext):
    username = ' '.join(context.args).lower()
    users_code = beecrawler.search_username(username)
    if len(users_code) == 0:
        text = f'Não encontrei nenhum usuário com o nome {username}'
    else:
        user = beecrawler.get_info(users_code[0])
        text = f'{user["username"]} '
        text+= f'[{user["university"]}]\n' if user['university'] else '\n'
        text+=f'{user["points"]} pontos'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def unknown_command(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não entendi o que você quis dizer. Use /help para saber mais.")

def set_command(update: Update, context: CallbackContext):
    username, property, value = context.args
    user = get_profile(username)
    if user:
        if property == 'points':
            value = int(value)
        context.chat_data['profiles'][user['id']][property] = value
        import json
        text = json.dumps(context.chat_data['profiles'][user['id']], indent=2)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
def create_dispatchers():
    dispatcher = updater.dispatcher
    
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    
    addprofile_handler = CommandHandler('addprofile', addprofile_command)
    dispatcher.add_handler(addprofile_handler)

    rmprofile_handler = CommandHandler('rmprofile', rmprofile_command)
    dispatcher.add_handler(rmprofile_handler)

    lsprofile_handler = CommandHandler(['lsprofile','lsprofiles'], lsprofile_command)
    dispatcher.add_handler(lsprofile_handler)

    searchprofile_handler = CommandHandler('searchprofile', searchprofile_command)
    dispatcher.add_handler(searchprofile_handler)

    ranking_handler = CommandHandler('ranking', ranking_command)
    dispatcher.add_handler(ranking_handler)

    set_handler = CommandHandler('debugset', set_command)
    dispatcher.add_handler(set_handler)
    
    unknown_handler = MessageHandler(Filters.command, unknown_command)
    dispatcher.add_handler(unknown_handler)




create_dispatchers()

updater.start_polling()
