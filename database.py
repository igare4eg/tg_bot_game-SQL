import s_taper
from s_taper.consts import *

scheme = {
    "user_id": INT + KEY,
    "nick": TEXT,
    "power": TEXT,
    "hp": INT,
    "dmg": INT,
    "lvl": INT,
    "exp": INT
}

heal_scheme = {
    "user_id": INT + KEY,
    "food": TEXT
}

db = s_taper.Taper("users", "data.db").create_table(scheme)
heals = s_taper.Taper("heals", "data.db").create_table(heal_scheme)
