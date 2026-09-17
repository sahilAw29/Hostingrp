import logging
import subprocess
import os
import time
import signal
import asyncio
import random
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.request import HTTPXRequest

# --- CONFIGURATION ---
TOKEN = "8671573001:AAFHGZQHU_sZ61kNMB11Bc8nRDCLFtjEaVs"
OWNER_ID = 8695946179
ADMIN_IDS = [8695946179]
CH_LINK = "@BMW_AURA0"
OWNER_LINK = "@bmw_aura2"

# Database files
USER_DATA_FILE = "user_data.json"
FILES_DB_FILE = "files_database.json"
SETTINGS_FILE = "bot_settings.json"

# Default settings
DEFAULT_USER_LIMIT = 80
UNLIMITED = 999999

# Load/Save functions
def load_json(filename, default):
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
    except:
        pass
    return default

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# Load data
settings = load_json(SETTINGS_FILE, {"global_limit": DEFAULT_USER_LIMIT})
all_files_db = load_json(FILES_DB_FILE, {})
user_data = load_json(USER_DATA_FILE, {"users": [], "total_files": 0})

# Tracking
running_processes = {}
all_users = set(user_data.get("users", []))
approved_users = {OWNER_ID}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- HTTP Request ---
request = HTTPXRequest(
    connection_pool_size=20,
    read_timeout=30,
    write_timeout=30,
    connect_timeout=30,
    pool_timeout=30
)

# ============================================
# 🎨 BOLD MONOSPACE FONT 
# ============================================
def bold_mono(text):
    mapping = {
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲',
        'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷',
        'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼',
        'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁',
        'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘',
        'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝',
        'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢',
        'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧',
        'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',
        ' ': ' ', '.': '.', ',': ',', '!': '!', '?': '?',
    }
    result = ''
    for char in text:
        result += mapping.get(char, char)
    return result

# ============================================
# 🎯 KEYBOARDS
# ============================================
def main_menu(user_id):
    keyboard = [
        [KeyboardButton(bold_mono("📢 Updates Channel"))],
        [KeyboardButton(bold_mono("📤 Upload File")), KeyboardButton(bold_mono("📁 Check Files"))],
        [KeyboardButton(bold_mono("⚡ Bot Speed")), KeyboardButton(bold_mono("📊 Statistics"))],
        [KeyboardButton(bold_mono("📞 Contact Owner"))]
    ]
    
    if user_id == OWNER_ID or user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton(bold_mono("⚙️ Admin Panel"))])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ============================================
# 🚀 START COMMAND
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    all_users.add(user.id)
    
    user_data["users"] = list(all_users)
    save_json(USER_DATA_FILE, user_data)
    
    global_limit = settings.get("global_limit", DEFAULT_USER_LIMIT)
    files_count = len(running_processes.get(user.id, []))
    
    if user.id == OWNER_ID or user.id in ADMIN_IDS:
        display_limit = bold_mono("∞ Unlimited")
        status = bold_mono("👑 OWNER") if user.id == OWNER_ID else bold_mono("🛡️ ADMIN")
    else:
        display_limit = str(global_limit)
        status = bold_mono("🆓 FREE")
    
    welcome_text = f"""
{bold_mono('〽️ Welcome,')} {bold_mono(user.first_name)}!

{bold_mono('🆔 Your User ID:')} {user.id}
{bold_mono('✳️ Username:')} @{user.username if user.username else 'N/A'}
{bold_mono('🔰 Your Status:')} {status}
{bold_mono('📁 Files Uploaded:')} {files_count} / {display_limit}

{bold_mono('🤖 Host & run Python (.py) or JS (.js) scripts.')}
{bold_mono('👇 Use buttons or type commands.')}
    """
    
    try:
        photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            await update.message.reply_photo(
                photo=photos.photos[0][-1].file_id, 
                caption=welcome_text, 
                reply_markup=main_menu(user.id)
            )
        else:
            await update.message.reply_text(
                welcome_text, 
                reply_markup=main_menu(user.id)
            )
    except Exception as e:
        logging.error(f"Error in start: {e}")
        await update.message.reply_text(welcome_text, reply_markup=main_menu(user.id))

# ============================================
# 📁 CHECK FILES
# ============================================
async def check_files_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    files = running_processes.get(user_id, [])
    
    if not files:
        await update.message.reply_text(
            f"{bold_mono('📁 Your files:')}\n\n{bold_mono('No active scripts running.')}"
        )
        return

    text = f"{bold_mono('📁 Your files:')}\n\n{bold_mono('Click to manage.')}"
    
    keyboard = []
    for idx, f in enumerate(files):
        status = "🟢 Running" if f['proc'] and f['proc'].poll() is None else "🔴 Stopped"
        file_ext = "py" if f['name'].endswith('.py') else "js"
        btn_text = f"{f['name']} ({file_ext}) - {status}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"manage_{idx}")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================
# ⚙️ CONTROL PANEL
# ============================================
async def control_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, file_idx):
    query = update.callback_query
    user_id = query.from_user.id
    file_data = running_processes[user_id][file_idx]
    
    status = "🟢 Running" if file_data['proc'] and file_data['proc'].poll() is None else "🔴 Stopped"
    
    text = f"""
{bold_mono('⚙️ Controls for:')} {file_data['name']} {bold_mono('of User')} {user_id}
{bold_mono('Status:')} {status}
    """

    keyboard = [
        [
            InlineKeyboardButton(bold_mono("🛑 Stop"), callback_data=f"stop_{file_idx}"),
            InlineKeyboardButton(bold_mono("🔄 Restart"), callback_data=f"restart_{file_idx}")
        ],
        [
            InlineKeyboardButton(bold_mono("🗑 Delete"), callback_data=f"delete_{file_idx}"),
            InlineKeyboardButton(bold_mono("📜 Logs"), callback_data=f"logs_{file_idx}")
        ],
        [InlineKeyboardButton(bold_mono("🔙 Back to Files"), callback_data="back_to_files")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================
# 📤 FILE UPLOAD HANDLER - FINAL VERSION
# ============================================
async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    user = update.effective_user
    
    if not doc.file_name.endswith(('.py', '.js')):
        await update.message.reply_text(
            f"{bold_mono('❌ Invalid File!')}\n\n{bold_mono('Only .py and .js files are supported.')}"
        )
        return

    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
        global_limit = settings.get("global_limit", DEFAULT_USER_LIMIT)
        files_count = len(running_processes.get(user_id, []))
        
        if files_count >= global_limit:
            await update.message.reply_text(
                f"{bold_mono('❌ Limit Reached!')}\n\n{bold_mono(f'You can only host {global_limit} files. Delete some files first.')}"
            )
            return

    try:
        # Animation with progress bars
        anim_msg = await update.message.reply_text(f"⚡ {bold_mono('Initializing...')}")
        await asyncio.sleep(0.5)

        # Downloading
        await anim_msg.edit_text(f"📥 {bold_mono('Downloading...')}\n{bold_mono('█▒▒▒▒▒▒▒▒▒')} 10%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"📥 {bold_mono('Downloading...')}\n{bold_mono('███▒▒▒▒▒▒')} 30%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"📥 {bold_mono('Downloading...')}\n{bold_mono('█████▒▒▒▒')} 50%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"📥 {bold_mono('Downloading...')}\n{bold_mono('███████▒▒')} 70%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"📥 {bold_mono('Downloading...')}\n{bold_mono('█████████')} 90%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"📥 {bold_mono('Downloading...')}\n{bold_mono('██████████')} 100%")
        await asyncio.sleep(0.5)

        # Processing
        await anim_msg.edit_text(f"🔧 {bold_mono('Processing...')}\n{bold_mono('█▒▒▒▒▒▒▒▒▒')} 10%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🔧 {bold_mono('Processing...')}\n{bold_mono('███▒▒▒▒▒▒')} 30%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🔧 {bold_mono('Processing...')}\n{bold_mono('█████▒▒▒▒')} 50%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🔧 {bold_mono('Processing...')}\n{bold_mono('███████▒▒')} 70%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🔧 {bold_mono('Processing...')}\n{bold_mono('█████████')} 90%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🔧 {bold_mono('Processing...')}\n{bold_mono('██████████')} 100%")
        await asyncio.sleep(0.5)

        # Launching
        await anim_msg.edit_text(f"🚀 {bold_mono('Launching...')}\n{bold_mono('█▒▒▒▒▒▒▒▒▒')} 10%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🚀 {bold_mono('Launching...')}\n{bold_mono('███▒▒▒▒▒▒')} 30%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🚀 {bold_mono('Launching...')}\n{bold_mono('█████▒▒▒▒')} 50%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🚀 {bold_mono('Launching...')}\n{bold_mono('███████▒▒')} 70%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🚀 {bold_mono('Launching...')}\n{bold_mono('█████████')} 90%")
        await asyncio.sleep(0.8)
        await anim_msg.edit_text(f"🚀 {bold_mono('Launching...')}\n{bold_mono('██████████')} 100%")
        await asyncio.sleep(0.5)

        # Actual file download
        file = await context.bot.get_file(doc.file_id)
        file_path = f"user_{user_id}_{doc.file_name}"
        await file.download_to_drive(file_path)
        
        # Create log file and start process
        log_file = open(f"{file_path}.log", "w")
        cmd = ["python", file_path] if file_path.endswith('.py') else ["node", file_path]
        process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
        
        # Store process
        if user_id not in running_processes: 
            running_processes[user_id] = []
        
        file_info = {
            "name": doc.file_name,
            "proc": process,
            "path": file_path,
            "log": log_file,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        running_processes[user_id].append(file_info)
        
        # Save to database
        file_id = f"{user_id}_{doc.file_name}_{int(time.time())}"
        all_files_db[file_id] = {
            "user_id": user_id,
            "username": user.username if user.username else "NoUsername",
            "name": doc.file_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "running",
            "path": file_path
        }
        save_json(FILES_DB_FILE, all_files_db)
        
        user_data["total_files"] = user_data.get("total_files", 0) + 1
        save_json(USER_DATA_FILE, user_data)
        
        # Animation delete karo
        await anim_msg.delete()
        
        # SUCCESS MESSAGE
        await update.message.reply_text(
            f"✅ {bold_mono('Python script Running......')}"
        )
        
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        await update.message.reply_text(
            f"{bold_mono('❌ Error:')}\n\n{str(e)}"
        )

# ============================================
# 🎯 CALLBACK HANDLER
# ============================================
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    await query.answer()
    
    if data == "back_to_files":
        files = running_processes.get(user_id, [])
        text = f"{bold_mono('📁 Your files:')}\n\n{bold_mono('Click to manage.')}"
        keyboard = []
        for idx, f in enumerate(files):
            status = "🟢 Running" if f['proc'] and f['proc'].poll() is None else "🔴 Stopped"
            file_ext = "py" if f['name'].endswith('.py') else "js"
            btn_text = f"{f['name']} ({file_ext}) - {status}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"manage_{idx}")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "back_to_admin":
        await show_admin_panel(update, context)
        return
    
    if data == "back_to_main":
        await start(update, context)
        return
    
    if data.startswith("manage_"):
        idx = int(data.split("_")[1])
        await control_panel(update, context, idx)
    
    elif data.startswith("stop_"):
        idx = int(data.split("_")[1])
        if user_id in running_processes and idx < len(running_processes[user_id]):
            proc = running_processes[user_id][idx]['proc']
            if proc and proc.poll() is None:
                proc.terminate()
            for file_id, file_info in all_files_db.items():
                if file_info["user_id"] == user_id and file_info["name"] == running_processes[user_id][idx]['name']:
                    file_info["status"] = "stopped"
                    save_json(FILES_DB_FILE, all_files_db)
                    break
            await query.edit_message_text(f"{bold_mono('🛑 Process Stopped!')}")
            await asyncio.sleep(1)
            await control_panel(update, context, idx)
    
    elif data.startswith("restart_"):
        idx = int(data.split("_")[1])
        if user_id in running_processes and idx < len(running_processes[user_id]):
            proc = running_processes[user_id][idx]['proc']
            if proc and proc.poll() is None:
                proc.terminate()
            file_path = running_processes[user_id][idx]['path']
            log_file = open(f"{file_path}.log", "w")
            cmd = ["python", file_path] if file_path.endswith('.py') else ["node", file_path]
            running_processes[user_id][idx]['proc'] = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
            running_processes[user_id][idx]['log'] = log_file
            for file_id, file_info in all_files_db.items():
                if file_info["user_id"] == user_id and file_info["name"] == running_processes[user_id][idx]['name']:
                    file_info["status"] = "running"
                    save_json(FILES_DB_FILE, all_files_db)
                    break
            await query.edit_message_text(f"{bold_mono('🔄 Process Restarted!')}")
            await asyncio.sleep(1)
            await control_panel(update, context, idx)
    
    elif data.startswith("delete_"):
        idx = int(data.split("_")[1])
        if user_id in running_processes and idx < len(running_processes[user_id]):
            keyboard = [[
                InlineKeyboardButton(bold_mono("✅ Confirm"), callback_data=f"confirm_del_{idx}"),
                InlineKeyboardButton(bold_mono("❌ Cancel"), callback_data=f"manage_{idx}")
            ]]
            await query.edit_message_text(
                f"{bold_mono('⚠️ Are you sure?')}\n\n{bold_mono('This action cannot be undone.')}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif data.startswith("confirm_del_"):
        idx = int(data.split("_")[2])
        if user_id in running_processes and idx < len(running_processes[user_id]):
            file_data = running_processes[user_id][idx]
            if file_data['proc'] and file_data['proc'].poll() is None:
                file_data['proc'].terminate()
            if 'log' in file_data:
                file_data['log'].close()
            if os.path.exists(file_data['path']):
                os.remove(file_data['path'])
            log_path = f"{file_data['path']}.log"
            if os.path.exists(log_path):
                os.remove(log_path)
            for file_id, file_info in list(all_files_db.items()):
                if file_info["user_id"] == user_id and file_info["name"] == file_data['name']:
                    del all_files_db[file_id]
                    save_json(FILES_DB_FILE, all_files_db)
                    break
            running_processes[user_id].pop(idx)
            await query.edit_message_text(f"{bold_mono('🗑 File Deleted Successfully!')}")
            await asyncio.sleep(1)
            await check_files_menu(update, context)
    
    elif data.startswith("logs_"):
        idx = int(data.split("_")[1])
        if user_id in running_processes and idx < len(running_processes[user_id]):
            file_path = running_processes[user_id][idx]['path']
            log_file = f"{file_path}.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.read()[-1500:]
                await query.message.reply_text(f"{bold_mono('📜 Log Output:')}\n\n{logs}")
            else:
                await query.message.reply_text(f"{bold_mono('📜 No logs available.')}")
            await control_panel(update, context, idx)
    
    elif data == "admin_panel":
        await show_admin_panel(update, context)
    elif data == "admin_users":
        await admin_users(update, context)
    elif data == "admin_all_files":
        await admin_all_files(update, context)
    elif data == "admin_user_files":
        await admin_user_files(update, context)
    elif data == "admin_limit":
        await admin_change_limit(update, context)
    elif data == "admin_stats":
        await admin_stats(update, context)
    elif data.startswith("view_user_files_"):
        target_user = int(data.split("_")[3])
        await view_user_files(update, context, target_user)

# ============================================
# 👑 ADMIN PANEL FUNCTIONS
# ============================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{bold_mono('⛔ Access Denied!')}\n\n{bold_mono('Only owners and admins can access this panel.')}")
        return
    total_files = sum(len(files) for files in running_processes.values())
    running = 0
    for files in running_processes.values():
        for f in files:
            if f['proc'] and f['proc'].poll() is None:
                running += 1
    global_limit = settings.get("global_limit", DEFAULT_USER_LIMIT)
    text = f"""
{bold_mono('⚙️ ADMIN CONTROL PANEL')}
━━━━━━━━━━━━━━━━━━━━━━
{bold_mono('👑 Owner ID:')} {OWNER_ID}
{bold_mono('👥 Total Users:')} {len(all_users)}
{bold_mono('📁 Total Files:')} {total_files}
{bold_mono('🟢 Running:')} {running}
{bold_mono('🔴 Stopped:')} {total_files - running}
{bold_mono('📊 Global Limit:')} {global_limit} {bold_mono('files/user')}
━━━━━━━━━━━━━━━━━━━━━━
{bold_mono('Select an option:')}
    """
    keyboard = [
        [InlineKeyboardButton(bold_mono("👥 View All Users"), callback_data="admin_users")],
        [InlineKeyboardButton(bold_mono("📁 ALL Hosted Files"), callback_data="admin_all_files")],
        [InlineKeyboardButton(bold_mono("👤 User's Files"), callback_data="admin_user_files")],
        [InlineKeyboardButton(bold_mono("📊 Change Global Limit"), callback_data="admin_limit")],
        [InlineKeyboardButton(bold_mono("📈 System Stats"), callback_data="admin_stats")],
        [InlineKeyboardButton(bold_mono("🔙 Back to Main"), callback_data="back_to_main")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
        await query.edit_message_text(f"{bold_mono('⛔ Access Denied!')}")
        return
    total_files = sum(len(files) for files in running_processes.values())
    running = 0
    for files in running_processes.values():
        for f in files:
            if f['proc'] and f['proc'].poll() is None:
                running += 1
    global_limit = settings.get("global_limit", DEFAULT_USER_LIMIT)
    text = f"""
{bold_mono('⚙️ ADMIN CONTROL PANEL')}
━━━━━━━━━━━━━━━━━━━━━━
{bold_mono('👑 Owner ID:')} {OWNER_ID}
{bold_mono('👥 Total Users:')} {len(all_users)}
{bold_mono('📁 Total Files:')} {total_files}
{bold_mono('🟢 Running:')} {running}
{bold_mono('🔴 Stopped:')} {total_files - running}
{bold_mono('📊 Global Limit:')} {global_limit} {bold_mono('files/user')}
━━━━━━━━━━━━━━━━━━━━━━
{bold_mono('Select an option:')}
    """
    keyboard = [
        [InlineKeyboardButton(bold_mono("👥 View All Users"), callback_data="admin_users")],
        [InlineKeyboardButton(bold_mono("📁 ALL Hosted Files"), callback_data="admin_all_files")],
        [InlineKeyboardButton(bold_mono("👤 User's Files"), callback_data="admin_user_files")],
        [InlineKeyboardButton(bold_mono("📊 Change Global Limit"), callback_data="admin_limit")],
        [InlineKeyboardButton(bold_mono("📈 System Stats"), callback_data="admin_stats")],
        [InlineKeyboardButton(bold_mono("🔙 Back to Main"), callback_data="back_to_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = f"{bold_mono('👥 ALL USERS')}\n\n"
    users_list = list(all_users)
    for uid in users_list:
        files = len(running_processes.get(uid, []))
        status = "👑" if uid == OWNER_ID else "🛡️" if uid in ADMIN_IDS else "👤"
        text += f"{status} {bold_mono(str(uid))} - {files} {bold_mono('files')}\n"
    keyboard = [
        [InlineKeyboardButton(bold_mono("🔙 Back to Admin"), callback_data="admin_panel")],
        [InlineKeyboardButton(bold_mono("🏠 Main Menu"), callback_data="back_to_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_all_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = f"{bold_mono('📁 ALL HOSTED FILES')}\n\n"
    if not all_files_db:
        text += f"{bold_mono('No files hosted yet.')}"
    else:
        files_list = list(all_files_db.values())
        for file_info in files_list:
            user = file_info["user_id"]
            name = file_info["name"]
            status = "🟢" if file_info["status"] == "running" else "🔴"
            date = file_info["date"][:10]
            text += f"{status} {bold_mono(name)} - {bold_mono('User:')} {user} ({date})\n"
    keyboard = [
        [InlineKeyboardButton(bold_mono("🔙 Back to Admin"), callback_data="admin_panel")],
        [InlineKeyboardButton(bold_mono("🏠 Main Menu"), callback_data="back_to_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_user_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = f"{bold_mono('👤 SELECT USER TO VIEW FILES')}\n\n"
    keyboard = []
    users_list = list(all_users)[:20]
    for uid in users_list:
        files = len(running_processes.get(uid, []))
        if files > 0:
            status = "👑" if uid == OWNER_ID else "🛡️" if uid in ADMIN_IDS else "👤"
            btn_text = f"{status} {uid} ({files} files)"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"view_user_files_{uid}")])
    keyboard.append([InlineKeyboardButton(bold_mono("🔙 Back to Admin"), callback_data="admin_panel")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def view_user_files(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user):
    query = update.callback_query
    text = f"{bold_mono(f'📁 Files of User {target_user}')}\n\n"
    user_files = [f for f in all_files_db.values() if f["user_id"] == target_user]
    if not user_files:
        text += f"{bold_mono('No files found for this user.')}"
    else:
        for file_info in user_files:
            name = file_info["name"]
            status = "🟢" if file_info["status"] == "running" else "🔴"
            date = file_info["date"]
            text += f"{status} {bold_mono(name)} - {date}\n"
    keyboard = [
        [InlineKeyboardButton(bold_mono("🔙 Back to User List"), callback_data="admin_user_files")],
        [InlineKeyboardButton(bold_mono("🏠 Main Menu"), callback_data="back_to_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_change_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    current = settings.get("global_limit", DEFAULT_USER_LIMIT)
    text = f"""
{bold_mono('📊 CHANGE GLOBAL FILE LIMIT')}
{bold_mono('Current Limit:')} {current} {bold_mono('files per user')}
{bold_mono('Admin/Owner:')} {bold_mono('∞ Unlimited')}
{bold_mono('Enter new limit (number):')}
    """
    await query.message.reply_text(text)
    context.user_data["awaiting_limit"] = True

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    total_files = sum(len(files) for files in running_processes.values())
    running = 0
    stopped = 0
    for files in running_processes.values():
        for f in files:
            if f['proc'] and f['proc'].poll() is None:
                running += 1
            else:
                stopped += 1
    text = f"""
{bold_mono('📈 SYSTEM STATISTICS')}
━━━━━━━━━━━━━━━━━━━━━━
{bold_mono('👥 Total Users:')} {len(all_users)}
{bold_mono('👑 Owner ID:')} {OWNER_ID}
{bold_mono('🛡️ Admins:')} {len(ADMIN_IDS)}
━━━━━━━━━━━━━━━━━━━━━━
{bold_mono('📁 Total Files:')} {total_files}
{bold_mono('🟢 Running:')} {running}
{bold_mono('🔴 Stopped:')} {stopped}
━━━━━━━━━━━━━━━━━━━━━━
{bold_mono('📊 Global Limit:')} {settings.get('global_limit', DEFAULT_USER_LIMIT)}
{bold_mono('📅 Last Updated:')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━
    """
    keyboard = [
        [InlineKeyboardButton(bold_mono("🔙 Back to Admin"), callback_data="admin_panel")],
        [InlineKeyboardButton(bold_mono("🏠 Main Menu"), callback_data="back_to_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================
# 📝 TEXT HANDLER
# ============================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if context.user_data.get("awaiting_limit"):
        try:
            new_limit = int(text)
            if new_limit > 0:
                settings["global_limit"] = new_limit
                save_json(SETTINGS_FILE, settings)
                await update.message.reply_text(
                    f"{bold_mono('✅ Global Limit Updated!')}\n\n{bold_mono(f'All users can now host {new_limit} files.')}\n\n{bold_mono('Admins/Owner have unlimited access.')}"
                )
                del context.user_data["awaiting_limit"]
            else:
                await update.message.reply_text(f"{bold_mono('❌ Invalid number!')}\n\n{bold_mono('Please enter a positive number.')}")
        except ValueError:
            await update.message.reply_text(f"{bold_mono('❌ Invalid number!')}\n\n{bold_mono('Please enter a valid number.')}")
        return
    
    if text == bold_mono("📢 Updates Channel"):
        await update.message.reply_text(f"{bold_mono('📢 Join Our Channel:')}\n\n{CH_LINK}")
    elif text == bold_mono("📤 Upload File"):
        await update.message.reply_text(f"{bold_mono('📤 Upload Your File:')}\n\n{bold_mono('Send .py or .js file')}")
    elif text == bold_mono("📁 Check Files"):
        await check_files_menu(update, context)
    elif text == bold_mono("⚡ Bot Speed"):
        start_time = time.time()
        msg = await update.message.reply_text(f"{bold_mono('⚡ Checking...')}")
        ms = (time.time() - start_time) * 1000
        await msg.edit_text(f"{bold_mono('⚡ Bot Speed:')}\n\n⏱️ {ms:.2f} ms")
    elif text == bold_mono("📊 Statistics"):
        total_files = sum(len(files) for files in running_processes.values())
        running = 0
        for files in running_processes.values():
            for f in files:
                if f['proc'] and f['proc'].poll() is None:
                    running += 1
        await update.message.reply_text(
            f"{bold_mono('📊 Statistics')}\n\n"
            f"{bold_mono('👥 Users:')} {len(all_users)}\n"
            f"{bold_mono('📁 Total Files:')} {total_files}\n"
            f"{bold_mono('🟢 Running:')} {running}\n"
            f"{bold_mono('🔴 Stopped:')} {total_files - running}"
        )
    elif text == bold_mono("📞 Contact Owner"):
        await update.message.reply_text(f"{bold_mono('📞 Contact Owner:')}\n\n{OWNER_LINK}")
    elif text == bold_mono("⚙️ Admin Panel"):
        await admin_panel(update, context)

# ============================================
# 🚀 MAIN FUNCTION
# ============================================
def main():
    try:
        app = Application.builder().token(TOKEN).request(request).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(handle_callbacks))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
        
        print("✅" + "="*50)
        print("🚀 NX NOBITA HOSTING BOT")
        print("="*50)
        print(f"👑 Owner ID: {OWNER_ID}")
        print(f"🛡️ Admins: {len(ADMIN_IDS)}")
        print("="*50)
        print("🤖 Bot is running...")
        print("✅ Progress Bar Animation Working")
        print("="*50)
        
        app.run_polling(
            poll_interval=0.5,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print("🔄 Restarting in 5 seconds...")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()
