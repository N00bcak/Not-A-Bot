# Configuration for 'common' module.
log_location = "NotABot/storage/NotABot_log.txt" 
db_location = "NotABot/storage/storage.db"

# Miscellaneous
# Configuration for pin_msgs.py
PIN_MSGS_CFG = {
                "emoji_list": ['📌','📍']
                }

# Configuration for starboard.py
STARBOARD_CFG = {
                "emoji_list": ['⭐'], 
                "min_count": 12, 
                "embed_color": 0xFAD905, 
                "starboard_channel": "starboard"
                }

# Configuration for meetups_handler.py
MEETUPS_CFG = {
                "embed_color": 0x84F20F,
                "meetups_channel": "meetups-bot"
                }

# Configuration for birthday_handler.py
BIRTHDAY_CFG = {
                "embed_color": 0x05EDED,
                "birthday_channel": "birthday"
                }

# Minigames
# Configuration for blackjack.py
BLACKJACK_CFG = {
                "embed_color": 0x000000,
                "win_color": 0x1CA603,
                "lose_color": 0xE60B0B
                }