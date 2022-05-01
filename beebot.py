import os 
import argparse
import profile

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--debug', '-d', help='Debug', action='store_true', default=False)
config = arg_parser.parse_args()


if not config.debug:
    BEEBOT_TOKEN = os.getenv("BEEBOT_TOKEN")
else:
    BEEBOT_TOKEN = os.getenv("BEEBOT_TOKEN_DEBUG")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters, PicklePersistence 
import logging

from beecrawler import BeeCrawler
import beepodium
import judgelinks

beecrawler = BeeCrawler()

persistence = PicklePersistence(filename='db/database.json')
updater = Updater(token=BEEBOT_TOKEN, use_context=True, persistence=persistence)
job_queue = updater.job_queue

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bem vindo! Eu sou o Bee Watcher, eu monitoro o desenvolvimento de usuários do BeeCrowd.\nUse /help para saber mais.")

def stop_command(update: Update, context: CallbackContext):
    text = "Obrigado por usar o Bee Watcher! Até mais!"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def help_command(update: Update, context: CallbackContext):
    text = "🏆 Visualização do Ranking Semanal\n"
    text += "/ranking\n\n"
    
    text += "🔎Visualização de problemas:\n"
    text += "/problems id1, id2, ...\n"
    text += "*Atualmente só funciona para questões do Beecrowd, UVa, AtCoder, CodeForces e SPOJ.\n\n"

    text += "📜Gerenciar participantes:\n"
    text += "/addprofile username1 username2 ... - adiciona um (ou mais) novo perfil.\n"
    text += "/rmprofile username1 username2 ... - remove um (ou mais) perfil.\n"
    text += "/lsprofile - lista perfis cadastrados.\n"
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def addprofile_command(update: Update, context: CallbackContext):
    usernames = list(map(str.lower, context.args))
    if len(usernames) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Nenhum usuário foi informado. Use /addprofile username1 username2 ...')
        return
    
    
    success = []
    already_added = []
    fail = []

    for username in usernames:
        user = beecrawler.get_profile_info(username=username)
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

def rmprofile_command(update: Update, context: CallbackContext):
    usernames = list(map(str.lower, context.args))
    if len(usernames) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Nenhum usuário foi informado. Use /rmprofile username1 username2 ...')
        return

    success = []
    fail = []

    for username in usernames:
        user = beecrawler.get_profile_info(username=username)
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
        user_new = beecrawler.get_profile_info(code)
        old_points = user['points']
        new_points = user_new['points']
        growth = new_points - old_points
        if growth != 0:
            profile = {
                'username': user['username'],
                'university': user['university'],
                'avatar': user['avatar'],
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
    chat_id = update.effective_chat.id
    profiles = context.chat_data.get('profiles', {})
    ranking = get_ranking(profiles)
    if len(profiles) == 0:
        text = 'Não há nenhum perfil cadastrado.'
    elif len(ranking) == 0:
        text = 'Não há nenhum perfil com pontuação alterada.'
    elif len(ranking) > 0:
        ranking = get_ranking(profiles)
        text = ranking_text(ranking)
    context.bot.send_message(chat_id=chat_id, text=text)


def searchprofile_command(update: Update, context: CallbackContext):
    username = ' '.join(context.args).lower()
    users_code = beecrawler.search_username(username)
    if len(users_code) == 0:
        text = f'Não encontrei nenhum usuário com o nome {username}'
    else:
        user = beecrawler.get_profile_info(users_code[0])
        text = f'{user["username"]} '
        text+= f'[{user["university"]}]\n' if user['university'] else '\n'
        text+=f'{user["points"]} pontos'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def problem_command(update: Update, context: CallbackContext):
    problems_ids = ''.join(context.args)
    problems_ids = problems_ids.replace(' ', '')
    problems_ids = problems_ids.split(',')
    if len(problems_ids) == 0:
        text = 'Nenhum problema foi informado. Use /problem problem1'
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        return

    problems = []
    fails = []
    for problem_id in problems_ids:
        try:
            problem = judgelinks.get_problem(problem_id)
        except:
            problem = None

        if problem:
            problems.append(problem)
        else:
            fails.append(problem_id)
    if len(fails) == 1:
        text = f'O problema {fails[0]} não foi encontrado.'
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    elif len(fails) > 1:
        text = f'Os problemas {", ".join(fails)} não foram encontrados.'
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    if len(problems) >= 1:
        text = 'Problems: \n'
        keyboard = []
        for problem in problems:
            text += f'{problem["id"]} - {problem["title"]}\n'
            keyboard.append([InlineKeyboardButton(f'{problem["short_id"]} - {problem["title"]}', url=problem["url"])])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
            

def unknown_command(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não entendi o que você quis dizer. Use /help para saber mais.")

def set_command(update: Update, context: CallbackContext):
    username, property, value = context.args
    user = beecrawler.get_profile_info(username=username)
    if user:
        if property == 'points':
            value = int(value)
        context.chat_data['profiles'][user['id']][property] = value
        import json
        text = json.dumps(context.chat_data['profiles'][user['id']], indent=2)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
def get_command(update:Update, context:CallbackContext):
    import json 
    text = json.dumps(context.chat_data, indent=2)
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def update_ranking(chat_id):
    dispatcher = updater.dispatcher
    chat_data = dispatcher.chat_data[chat_id]
    new_profiles = beecrawler.bulk_profile_info(chat_data['profiles'].keys())
    for profile in new_profiles:
        chat_data['profiles'][profile['id']] = profile
    dispatcher.update_persistence()

def weekly_ranking(context: CallbackContext):
    for chat_id, chat_data in updater.persistence.get_chat_data().items():
        ranking = get_ranking(chat_data['profiles'])
        if len(ranking) == 0:
            text = '😴'
        else:
            text = ranking_text(ranking)
            imgPodium = beepodium.create_podium(*ranking[:3])
            
            update_ranking(chat_id)
            context.bot.send_photo(chat_id=chat_id, photo=imgPodium)
        context.bot.send_message(chat_id=chat_id, text=text)
        
def test_command(update: Update, context: CallbackContext):
    print(update.effective_chat.id)
    if update.effective_chat.id == 262931805:
        weekly_ranking(context)

def create_dispatchers():
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    help_handler = CommandHandler('help', help_command)
    dispatcher.add_handler(help_handler)

    
    addprofile_handler = CommandHandler('addprofile', addprofile_command)
    dispatcher.add_handler(addprofile_handler)

    rmprofile_handler = CommandHandler(['rmprofile', 'rmprofiles'], rmprofile_command)
    dispatcher.add_handler(rmprofile_handler)

    lsprofile_handler = CommandHandler(['lsprofile','lsprofiles'], lsprofile_command)
    dispatcher.add_handler(lsprofile_handler)

    searchprofile_handler = CommandHandler('searchprofile', searchprofile_command)
    dispatcher.add_handler(searchprofile_handler)

    ranking_handler = CommandHandler('ranking', ranking_command)
    dispatcher.add_handler(ranking_handler)

    problem_handler = CommandHandler(['problem', 'problems'], problem_command)
    dispatcher.add_handler(problem_handler)

    if config.debug:
        set_handler = CommandHandler('set', set_command)
        dispatcher.add_handler(set_handler)
        get_handler = CommandHandler('get', get_command)
        dispatcher.add_handler(get_handler)

    test_handler = CommandHandler('test', test_command)
    dispatcher.add_handler(test_handler)


    stop_handler = CommandHandler('stop', stop_command)
    dispatcher.add_handler(stop_handler)
    
    unknown_handler = MessageHandler(Filters.command, unknown_command)
    dispatcher.add_handler(unknown_handler)

def create_jobs():
    from datetime import time 
    job_queue = updater.job_queue

    job_queue.run_daily(weekly_ranking, days=[4], time=time(hour=20, minute=0)) #17h

create_dispatchers()
create_jobs()

updater.start_polling()
updater.idle()
