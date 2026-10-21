import contextlib
import os
import random
import sys
import time
import textwrap


class Hero:
    max_health = 100
    attack_power = 15
    resource_name = "Focus"
    special_name = "Power Strike"
    special_cost = 3

    def __init__(self, name):
        self.name = name
        self.health = self.max_health
        self.resource = 0
        self.potions = 3
        self.level = 1
        self.experience = 0
        self.total_damage = 0
        self.evading = False

    def take_damage(self, damage):
        damage = max(0, damage)
        if self.evading:
            self.evading = False
            print(f"{self.name} slips out of the way!")
            return 0
        damage_taken = min(damage, self.health)
        self.health -= damage_taken
        return damage_taken

    def heal(self, amount):
        restored = min(max(0, amount), self.max_health - self.health)
        self.health += restored
        return restored

    def attack(self):
        return random.randint(max(1, self.attack_power - 3), self.attack_power + 3)

    def special_effect(self, enemy):
        return f"{self.name} unleashes {self.special_name}!", self.attack_power * 2

    def gain_experience(self, amount):
        self.experience += amount
        messages = [f"You gain {amount} XP ({self.experience} XP)."]
        while self.experience >= self.level * 40:
            self.experience -= self.level * 40
            self.level += 1
            self.max_health += 10
            self.attack_power += 2
            restored = self.heal(30)
            self.potions = min(5, self.potions + 1)
            messages.append(
                f"LEVEL UP! You are now level {self.level}. "
                f"Attack increased, {restored} HP restored, and you found a potion."
            )
        return messages

    def __str__(self):
        return f"{self.name} the {self.__class__.__name__} (Level {self.level})"


class Warrior(Hero):
    max_health = 130
    attack_power = 18
    resource_name = "Rage"
    special_name = "Shield Bash"

    def special_effect(self, enemy):
        enemy.stunned = True
        return "You smash the enemy with your shield and stun it!", self.attack_power * 2


class Mage(Hero):
    max_health = 90
    attack_power = 20
    resource_name = "Mana"
    special_name = "Meteor Storm"

    def special_effect(self, enemy):
        return "A storm of meteors crashes down!", self.attack_power * 3


class Rogue(Hero):
    max_health = 100
    attack_power = 22
    resource_name = "Combo"
    special_name = "Shadowstep"

    def special_effect(self, enemy):
        self.evading = True
        return "You strike from the shadows and prepare to evade!", self.attack_power * 2


class Paladin(Hero):
    max_health = 125
    attack_power = 16
    resource_name = "Faith"
    special_name = "Divine Light"

    def special_effect(self, enemy):
        restored = self.heal(25)
        return f"Divine light restores {restored} HP!", self.attack_power


class Ranger(Hero):
    max_health = 105
    attack_power = 19
    resource_name = "Focus"
    special_name = "Poisoned Arrow"

    def special_effect(self, enemy):
        enemy.poison_turns = 3
        return "Your poisoned arrow finds its mark!", self.attack_power + 8


class Enemy:
    def __init__(self, name, title, max_health, attack_power, art, reward):
        self.name = name
        self.title = title
        self.max_health = max_health
        self.health = max_health
        self.attack_power = attack_power
        self.art = art
        self.reward = reward
        self.stunned = False
        self.poison_turns = 0
        self.turns = 0

    def take_damage(self, damage):
        damage_taken = min(max(0, damage), self.health)
        self.health -= damage_taken
        return damage_taken

    def attack(self):
        return random.randint(max(1, self.attack_power - 3), self.attack_power + 3)


ENCOUNTERS = [
    {
        "name": "Goblin Scout",
        "title": "The Watcher in the Woods",
        "health": 55,
        "attack": 10,
        "reward": 30,
        "art": r"""
                    /\_/\\
             ______/ o.o \______
            / .---. \ ^ / .---. \
           / /     \ \_/ /     \ \
          | |  .-.  \___/  .-.  | |
          | | (o )  /   \  ( o) | |
          | |  `-' / /^\ \ `-'  | |
          |  \    / /_\ \    /  |
           \  `--/  |||  \--'  /
            \    \  |||  /    /
             `.___\_|||_/___.'
                  /_/ \_\
             ____/ /   \ \____
            /_____/\___/\_____\
""",
    },
    {
        "name": "Cave Troll",
        "title": "The Bridge Keeper",
        "health": 85,
        "attack": 14,
        "reward": 45,
        "art": r"""
                  .-=========-.
              .-''  _       _  ``-.
            .'     (o)     (o)      `.
           /       .---. .---.         \
          |       /  _  V  _  \         |
          |      |  (o)   (o)  |        |
          |      |     .-.     |        |
           \      \   (___)   /        /
        .---`-.    `-._____.-'    .-`---.
       /  .--. `-.____/||| \____.-' .--.  \
      /__/    \______/ ||| \______/    \__\
          |     |    /_|_|_\    |     |
          |_____|   /_______\   |_____|
          /_____\  /_________\  /_____\
""",
    },
    {
        "name": "Orc Champion",
        "title": "The Arena of Bones",
        "health": 110,
        "attack": 17,
        "reward": 60,
        "art": r"""
                 /^^^^^^^^^^\
            ____/  .------.  \____
           /   .---|  oo  |---.   \
          /   /    |  /\  |    \   \
         |   |     |  \/  |     |   |
         |   |  .--|  __  |--.  |   |
         |   | /   \`----'/   \ |   |
         |   \ \___/|  |\ \___/ /   |
          \   `----/|__|\`----'     /
           `-.___ / /||\ \ ____.--'
               /__/ |||| \__\
             _/___\_||||_/___\_
            /  _   /____\   _   \
           /__/ \_/______\_/ \___\
              |____|    |____|
""",
    },
    {
        "name": "Skeleton Knight",
        "title": "The Forgotten Crypt",
        "health": 100,
        "attack": 16,
        "reward": 55,
        "art": r"""
                   .-=========-.
                .-'  .-------.  `-.
               /    /  .---.  \     \
              |    |  /     \  |     |
              |    | | (o o) | |     |
              |    | |   ^   | |     |
               \    \ \ `-' / /     /
           .----`-.  `-.___.-'  .-'----.
          /   _   _`--./|||\.--'_   _   \
         /___/ \_/ \___|||||___/ \_/ \___\
               |   /___|||||___\   |
          .----|--/   /_|||_\   \--|----.
         /     | /___/  |||  \___\ |     \
        /______|/____\_ ||| _/____\|______\
            /_____\    /_|_\    /_____\
           /_______\  /_____\  /_______\
""",
    },
    {
        "name": "Swamp Hydra",
        "title": "The Mire of Many Heads",
        "health": 135,
        "attack": 18,
        "reward": 70,
        "art": r"""
            /\                   /\                   /\
           (  )                 (  )                 (  )
            ||                   ||                   ||
         .--||--.             .--||--.             .--||--.
        /  (oo)  \           /  (oo)  \           /  (oo)  \
       |   /^^\   |         |   /^^\   |         |   /^^\   |
        \  \__/  /           \  \__/  /           \  \__/  /
         `-.||.-'             `-.||.-'             `-.||.-'
            ||                   ||                   ||
       _____||___________________||___________________||_____
      /     ||                   ||                   ||     \
     /      ||       /\____/\    ||                   ||      \
    |       ||      /  o  o  \   ||                   ||       |
    |       ||      |   \__/  |  ||                   ||       |
     \      ||      \________/   ||                   ||      /
      `-----||--------/____\-----||-------------------||-----'
            ||       /| || |\    ||
           /__\     /_|_||_|_\  /__\
          /____\      /_||_\   /____\
""",
    },
    {
        "name": "Ancient Dragon",
        "title": "The Last Ember",
        "health": 175,
        "attack": 21,
        "reward": 90,
        "art": r"""
                              /=======/|
                     /=======/======/ |
            ________/=======/______/   |
           /        /=======/      /|  |
          /  /\    /=======/  /\  / |  |
         /  /  \__/=======/__/  \/  |  |
        /  /   .----.____.----.     /   |
       |  |   /  .-.  __  .-.  \   |    |
       |  |  |  (o  )/  \(  o)  |  |    |
        \  \  \  `-' \__/ `-'  /  /     |
         \  `-.`-.   /\   .-' .-'      /
          \    `--\_/  \_/--'         /
           `---.____\__/____.---------'
                  \  FIRE /
                   \_____/
               ____/| /\ |\____
              /____/|/  \|\____\
             /_____|/____\|_____\
                /__/      \__\
               /__/        \__\
""",
    },
    {
        "name": "THE CREATOR \"JEZAR\"",
        "title": "The End of All Things",
        "health": 240,
        "attack": 24,
        "reward": 200,
        "art": r"""
                     .-^^^^^^^^^-.
                  .-' / / \ \ `-.
                .'  / /___\ \  `.
               /  .-'  |  `-.  \
              /  / .---------. \  \
             |  | /  .-----.  \ |  |
             |  || /  / \  \ ||  |
             |  |||  (o) (o)  |||  |
             |  |||   \___/   |||  |
             |  || \  `-'  / ||  |
             |  | \ `-----' / |  |
              \  \ `-.____.-' /  /
               `.\   `---'   /.'
                 `-._ || _.-'
                    \ || /
                  .-' || `-.
                 / .--||--. \
                | /   ||   \ |
                || .--||--. ||
                ||| JEZAR |||
                |||_______|||
                 \ \     / /
                  `.\___/.'
                    /___\
""",
    },
]

ENEMY_COLORS = {
    "Goblin Scout": "\033[92m",
    "Cave Troll": "\033[32m",
    "Orc Champion": "\033[91m",
    "Skeleton Knight": "\033[37m",
    "Swamp Hydra": "\033[96m",
    "Ancient Dragon": "\033[93m",
    'THE CREATOR "JEZAR"': "\033[95m",
}

ADVENTURER_FRAMES = (
    (
        "   /\\",
        "  /__\\",
        "  (o )",
        "-/|\\---->",
        " / \\",
        "/   \\",
    ),
    (
        "   /\\",
        "  /__\\",
        "  (o )",
        "-/|\\===>",
        "  /\\",
        " _/  \\_",
    ),
)

HERO_ART = {
    "Warrior": (
        "    .-^-.",
        "   /|===|\\",
        "  | (o.o) |",
        "  |  \\_/  |",
        "  /|=====|\\",
        " /_|_____|_\\",
        "   /     \\",
    ),
    "Mage": (
        "      /\\",
        "     /__\\",
        "    /_**_\\",
        "   ( o  o )",
        "    \\_==_/",
        "    /|==|\\",
        "   /_|__|_\\",
    ),
    "Rogue": (
        "    .----.",
        "   /      \\",
        "  /  .--.  \\",
        " |  /o  o\\  |",
        " |  \\_^^_/  |",
        "  \\_/|==|\\_/",
        "    /_||_\\",
    ),
    "Paladin": (
        "    .-*-.",
        "   /  |  \\",
        "  | .---. |",
        "  |( o o )|",
        "  | \\_^_/ |",
        "  /|==+==|\\",
        " /_|_____|_\\",
    ),
    "Ranger": (
        "     .---.",
        "    /_____\\",
        "   /  o o  \\",
        "  |    ^    |",
        "   \\  ---  /",
        "  /|\\     /|",
        " /_|_\\   /_|",
    ),
}

ROLE_TYPES = {
    "Warrior": Warrior,
    "Mage": Mage,
    "Rogue": Rogue,
    "Paladin": Paladin,
    "Ranger": Ranger,
}

ROLE_DESCRIPTIONS = {
    "Warrior": "The steadfast defender. Shield Bash stuns an enemy.",
    "Mage": "A master of magic. Meteor Storm deals massive damage.",
    "Rogue": "A swift shadow. Shadowstep avoids the next attack.",
    "Paladin": "A holy guardian. Divine Light restores your health.",
    "Ranger": "A deadly hunter. Poisoned Arrow damages over time.",
}

VICTORY_TIPS = (
    "Each normal attack adds one charge toward your special.",
    "Potions restore up to 40 HP. Save them for wounds worth healing.",
    (
        "A stunned foe loses its turn. The Warrior's Shield Bash can "
        "create that opening."
    ),
    "The Mage's Meteor Storm hits for triple attack power.",
    "Shadowstep lets a Rogue avoid the enemy's next strike.",
    "A Ranger's poison keeps dealing damage after the arrow lands.",
    "The Ancient Dragon and the Creator unleash stronger attacks every third turn.",
)


def health_bar(current, maximum, width=20):
    filled = max(0, min(width, round(width * current / maximum)))
    if current / maximum > 0.5:
        color = "\033[92m"
    elif current / maximum > 0.25:
        color = "\033[93m"
    else:
        color = "\033[91m"
    bar = f"|{'=' * filled}{'.' * (width - filled)}| {current}/{maximum} HP"
    if sys.stdout.isatty():
        return f"{color}{bar}\033[0m"
    return bar


def special_charge_status(hero):
    charges, progress = divmod(hero.resource, hero.special_cost)
    return (
        f"{hero.resource_name}: {hero.resource} "
        f"({charges} ready, {progress}/{hero.special_cost} toward next)"
    )


def clear_screen():
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


@contextlib.contextmanager
def windows_quick_edit_disabled():
    if os.name != "nt" or not sys.stdin.isatty():
        yield
        return

    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetStdHandle.argtypes = [ctypes.c_uint32]
    kernel32.GetStdHandle.restype = ctypes.c_void_p
    kernel32.GetConsoleMode.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    kernel32.GetConsoleMode.restype = ctypes.c_int
    kernel32.SetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel32.SetConsoleMode.restype = ctypes.c_int

    input_handle = kernel32.GetStdHandle(ctypes.c_uint32(-10).value)
    original_mode = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(input_handle, ctypes.byref(original_mode)):
        raise ctypes.WinError(ctypes.get_last_error())

    quick_edit_mode = 0x0040
    extended_flags_mode = 0x0080
    interactive_mode = (original_mode.value | extended_flags_mode) & ~quick_edit_mode
    if not kernel32.SetConsoleMode(input_handle, interactive_mode):
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        yield
    finally:
        if not kernel32.SetConsoleMode(input_handle, original_mode.value):
            raise ctypes.WinError(ctypes.get_last_error())


@contextlib.contextmanager
def terminal_keys():
    if os.name == "nt":
        with windows_quick_edit_disabled():
            yield
        return

    import termios
    import tty

    file_descriptor = sys.stdin.fileno()
    previous_settings = termios.tcgetattr(file_descriptor)
    try:
        tty.setcbreak(file_descriptor)
        yield
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, previous_settings)


def poll_key():
    if os.name == "nt":
        import msvcrt

        if not msvcrt.kbhit():
            return None
        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            arrow = msvcrt.getwch()
            return {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT"}.get(
                arrow, None
            )
        if key == "\r":
            return "ENTER"
        if key == "\x03":
            raise KeyboardInterrupt
        return key.lower()

    import select

    ready, _, _ = select.select([sys.stdin], [], [], 0)
    if not ready:
        return None
    key = sys.stdin.read(1)
    if key == "\n":
        return "ENTER"
    if key == "\x1b":
        ready, _, _ = select.select([sys.stdin], [], [], 0.01)
        if ready and sys.stdin.read(1) == "[":
            ready, _, _ = select.select([sys.stdin], [], [], 0.01)
            if ready:
                return {"A": "UP", "B": "DOWN", "C": "RIGHT", "D": "LEFT"}.get(
                    sys.stdin.read(1)
                )
        return "ESC"
    if key == "\x03":
        raise KeyboardInterrupt
    return key.lower()


def draw_fantasy_scene(frame, width=62, height=9, color="\033[96m"):
    canvas = [[" "] * width for _ in range(height)]
    castle = (
        "   ^       ^",
        "  /|\\     /|\\",
        "  |||  _  |||",
        "  ||| | | |||",
        " _|||_|_|_|||_",
    )
    castle_x = max(0, width - len(castle[0]) - 3)
    castle_y = max(0, height - len(castle) - 1)
    for row, line in enumerate(castle):
        for column, char in enumerate(line):
            x = castle_x + column
            y = castle_y + row
            if x < width and char != " ":
                canvas[y][x] = char

    for index in range(9):
        x = (index * 17 - frame * (index % 3 + 1)) % width
        y = (index * 7 + frame // 2) % max(1, height - 2)
        canvas[y][x] = "*" if (frame + index) % 3 == 0 else "."

    hero = ADVENTURER_FRAMES[frame % len(ADVENTURER_FRAMES)]
    hero_x = max(0, min(width - max(map(len, hero)), 6 + frame % 3 - 1))
    hero_y = max(0, height - len(hero) - 1)
    for row, sprite_line in enumerate(hero):
        y = hero_y + row
        for column, char in enumerate(sprite_line):
            x = hero_x + column
            if 0 <= x < width and y < height - 1 and char != " ":
                canvas[y][x] = char

    torch_x = width - 3
    for row, char in enumerate(("*", "|", "|")):
        y = height - 4 + row
        if 0 <= y < height - 1 and torch_x < width:
            canvas[y][torch_x] = char

    scene = "\n".join("".join(row) for row in canvas)
    print(f"{color}{scene}\033[0m")
    print("\033[90m" + "_" * width + "\033[0m")


def show_start_screen():
    if not sys.stdout.isatty():
        return True

    os.system("")
    frame = 0
    logo = (
        " _____ __  __ ____  _____ ____  _____ _   _ _____ _____",
        "| ____|  \\/  | __ )| ____|  _ \\|  ___| \\ | | ____|__  /",
        "|  _| | |\\/| |  _ \\|  _| | |_) | |_  |  \\| |  _|   / /",
        "| |___| |  | | |_) | |___|  _ <|  _| | |\\  | |___ / /_",
        "|_____|_|  |_|____/|_____|_| \\_\\_____|_| \\_|_____/_/(_)",
    )
    with terminal_keys():
        while True:
            sys.stdout.write("\033[2J\033[H")
            gold = "\033[93m"
            bright = "\033[97m"
            cyan = "\033[96m"
            pulse = "\033[95m" if frame % 2 else "\033[91m"
            print(gold + "+" + "-" * 60 + "+")
            print("|" + " " * 60 + "|")
            for line in logo:
                print("|" + line.center(60) + "|")
            print("|" + " " * 60 + "|")
            subtitle = "THE EMBERFALL CHRONICLES"
            print(
                "|"
                + " " * ((60 - len(subtitle)) // 2)
                + pulse
                + subtitle
                + gold
                + " " * ((60 - len(subtitle) + 1) // 2)
                + "|"
            )
            print("|" + " " * 60 + "|")
            print("+" + "-" * 60 + "+" + "\033[0m")
            print()
            print(cyan + "  A HERO'S JOURNEY | SEVEN FOES | ONE FINAL CREATOR" + "\033[0m")
            print()
            print("\033[1;97m" + "  USE HEADPHONES".center(62) + "\033[0m")
            print()
            print("\033[90m" + "For the best experience".center(62) + "\033[0m")
            print()
            omen = "\033[1;91m" if (frame // 4) % 2 == 0 else "\033[31m"
            print(omen + "TIP: YOUR CHOICES HAVE CONSEQUENCES".center(62) + "\033[0m")
            print()
            draw_fantasy_scene(frame)
            print()
            print(bright + "  Press ENTER to begin your adventure" + "\033[0m")
            print("\033[90m  Press Q to quit\033[0m")
            sys.stdout.flush()
            key = poll_key()
            if key == "ENTER":
                return True
            if key == "q":
                return False
            frame += 1
            time.sleep(0.16)


def animated_class_choice(name):
    selected = 0
    frame = 0
    role_names = list(ROLE_TYPES)
    with terminal_keys():
        while True:
            role_name = role_names[selected]
            hero_type = ROLE_TYPES[role_name]
            sys.stdout.write("\033[2J\033[H")
            print("\033[93m+" + "-" * 60 + "+")
            print("|" + "              CHOOSE YOUR HERO              ".center(60) + "|")
            print("+" + "-" * 60 + "+\033[0m")
            print()
            print(f"  Name: {name}")
            print("  Use UP/DOWN arrows or 1-5, then press ENTER.")
            for index, role in enumerate(role_names):
                marker = ">" if index == selected else " "
                color = "\033[93m" if index == selected else "\033[37m"
                print(f"  {color}{marker} {index + 1}. {role:<10} {ROLE_DESCRIPTIONS[role]}\033[0m")
            print()
            art = HERO_ART[role_name]
            pose = frame % 2
            for index, art_line in enumerate(center_art_lines(art, width=62).splitlines()):
                if pose and index == len(art) - 1:
                    art_line = art_line.replace("/", "|")
                print(f"\033[96m{art_line}\033[0m")
            print(
                f"  HEALTH {hero_type.max_health}   ATTACK {hero_type.attack_power}"
                f"   SPECIAL {hero_type.special_name}"
            )
            draw_fantasy_scene(frame, height=8)
            sys.stdout.flush()

            key = poll_key()
            if key in ("UP", "LEFT"):
                selected = (selected - 1) % len(role_names)
            elif key in ("DOWN", "RIGHT"):
                selected = (selected + 1) % len(role_names)
            elif key in ("1", "2", "3", "4", "5"):
                selected = int(key) - 1
            elif key == "ENTER":
                return ROLE_TYPES[role_names[selected]](name)
            elif key == "q":
                return None
            frame += 1
            time.sleep(0.16)


def center_art_lines(lines, width):
    art_width = max(map(len, lines), default=0)
    padding = " " * max(0, (width - art_width) // 2)
    return "\n".join(f"{padding}{line.rstrip()}" for line in lines)


def format_art(art, width=58):
    lines = textwrap.dedent(art).strip("\n").splitlines()
    return center_art_lines(lines, width)


def animate_journey_scene():
    if not sys.stdout.isatty():
        return

    for frame_number in range(24):
        clear_screen()
        print("  THROUGH THE RUINS")
        print()
        draw_fantasy_scene(frame_number, width=58, height=10)
        time.sleep(0.12)


def animate_attack(enemy, special=False, incoming=False):
    if not sys.stdout.isatty():
        return

    width = 78
    color = ENEMY_COLORS.get(enemy.name, "\033[91m")
    heading = (
        f"{enemy.name.upper()} ATTACKS!"
        if incoming
        else "SPECIAL ATTACK!" if special else "YOUR ATTACK!"
    )
    enemy_lines = textwrap.dedent(enemy.art).strip("\n").splitlines()
    enemy_width = max(map(len, enemy_lines), default=0)
    hero_lines = ("  O  ", " /|\\ ", " / \\ ")
    impact_frames = (
        ("                 .", "                  *", "                 ."),
        ("               * * *", "              * BOOM *", "               * * *"),
        ("             .  *  .  *", "           *  CRASH!  *", "             *  .  *  ."),
    )

    travel_frames = 15
    total_frames = 24
    canvas_height = max(15, len(enemy_lines) + 4)
    hero_y = canvas_height - 5
    for frame_number in range(total_frames):
        clear_screen()
        canvas = [[" "] * width for _ in range(canvas_height)]
        incoming_x = width - enemy_width - 5
        hero_x = 5 + min(frame_number // 5, 3) * 2
        enemy_x = incoming_x
        if travel_frames <= frame_number < travel_frames + 3:
            enemy_x -= 2
        elif travel_frames + 3 <= frame_number < travel_frames + 6:
            enemy_x += 2

        for row, line in enumerate(hero_lines):
            for column, char in enumerate(line):
                x = hero_x + column
                if 0 <= x < width and char != " ":
                    canvas[hero_y + row][x] = char

        for row, line in enumerate(enemy_lines):
            for column, char in enumerate(line):
                x = enemy_x + column
                y = row + 1
                if 0 <= x < width and 0 <= y < canvas_height and char != " ":
                    canvas[y][x] = char

        projectile_frame = min(frame_number // 3, 4)
        projectile_x = (
            incoming_x - 3 - projectile_frame * 8
            if incoming
            else hero_x + 9 + projectile_frame * 8
        )
        if frame_number < travel_frames:
            projectile = "<==" if incoming else ("==>*==>" if special else "---->")
            projectile_y = hero_y + 1
            for column, char in enumerate(projectile):
                x = projectile_x + column
                if 0 <= x < width:
                    canvas[projectile_y][x] = char
        else:
            impact_frame = min((frame_number - travel_frames) // 3, 2)
            effect_lines = impact_frames[impact_frame]
            effect_y_start = max(1, hero_y - 3)
            for row, line in enumerate(effect_lines):
                effect_y = effect_y_start + row
                effect_x = max(0, min(width - len(line), incoming_x - 8))
                canvas[effect_y][effect_x:effect_x + len(line)] = line

        print(f"\033[97m{heading.center(width)}\033[0m")
        print()
        for row_number, row in enumerate(canvas):
            line = "".join(row).rstrip()
            if row_number in range(1, min(canvas_height, 1 + len(enemy_lines))):
                print(f"{color}{line}\033[0m")
            elif frame_number >= 5 and row_number in range(max(1, hero_y - 3), hero_y):
                print(f"\033[93m{line}\033[0m")
            else:
                print(line)
        print("\033[90m" + "_" * width + "\033[0m")
        time.sleep(0.09)


def print_title():
    print(r"""
  _____ _   _ _____ _____ _____ _____ _____
 |  ___| | | |  __ \_   _|_   _|  ___|  __ \
 | |__ | | | | |  \/ | |   | | | |__ | |  \/
 |  __|| | | | | __  | |   | | |  __|| |
 | |___| |_| | |_\ \_| |_  | | | |___| |
 \____/ \___/ \____/\___/  \_/ \____/ \_|
          THE EMBERFALL CHRONICLES
""")


def choose_hero(name):
    if sys.stdout.isatty() and sys.stdin.isatty():
        return animated_class_choice(name)

    roles = {
        "1": Warrior,
        "2": Mage,
        "3": Rogue,
        "4": Paladin,
        "5": Ranger,
        "warrior": Warrior,
        "mage": Mage,
        "rogue": Rogue,
        "paladin": Paladin,
        "ranger": Ranger,
    }
    descriptions = {
        "1": "Warrior  - toughest fighter; Shield Bash stuns foes",
        "2": "Mage     - fragile spellcaster; Meteor Storm deals massive damage",
        "3": "Rogue    - nimble striker; Shadowstep evades the next hit",
        "4": "Paladin  - sturdy healer; Divine Light restores health",
        "5": "Ranger   - precise hunter; Poisoned Arrow deals damage over time",
    }
    print("\nChoose your hero:")
    for description in descriptions.values():
        print(f"  {description}")
    while True:
        choice = input("> ").strip().lower()
        hero_type = roles.get(choice)
        if hero_type is not None:
            return hero_type(name)
        print("Choose 1-5, or enter a class name.")


def show_status(hero, enemy, encounter_number, art):
    print(f"\n{'=' * 58}")
    print(f"\033[1;93mENCOUNTER {encounter_number}: {enemy.title}\033[0m")
    color = ENEMY_COLORS.get(enemy.name, "")
    reset = "\033[0m" if color and sys.stdout.isatty() else ""
    if color and sys.stdout.isatty():
        print(f"{color}{format_art(art)}{reset}")
    else:
        print(format_art(art))
    print("\n\033[1;92mYOUR HERO\033[0m")
    print(f"  {hero}")
    print(f"  Health:  {health_bar(hero.health, hero.max_health)}")
    print(f"  {special_charge_status(hero)}")
    print(f"  Potions: {hero.potions}")
    print(f"  Special: {hero.special_name}")
    print(f"\n\033[1;91mENEMY: {enemy.name}\033[0m")
    print(f"  Health:  {health_bar(enemy.health, enemy.max_health)}")


def player_turn(hero, enemy, show_menu=True):
    if show_menu:
        print("\n\033[1;96mYOUR TURN\033[0m")
        print("  \033[1;91mA\033[0m  \033[91mAttack the enemy\033[0m")
        print(
            f"  \033[1;95mS\033[0m  \033[95mUse {hero.special_name} "
            f"({hero.resource // hero.special_cost} ready)\033[0m"
        )
        print("  \033[1;92mP\033[0m  \033[92mDrink a health potion\033[0m")
        print("  \033[1;94mF\033[0m  \033[94mFlee from the fight\033[0m")
    action = input("\033[1;96m>\033[0m ").strip().lower()

    if action in ("a", "attack", "1"):
        animate_attack(enemy)
        damage = enemy.take_damage(hero.attack())
        hero.total_damage += damage
        hero.resource += 1
        print(f"You strike the {enemy.name} for {damage} damage.")
        return True

    if action in ("s", "special", "2"):
        if hero.resource < hero.special_cost:
            print(
                f"\033[1;93mNot enough {hero.resource_name}.\033[0m "
                f"Attack to build up your special "
                f"({hero.resource}/{hero.special_cost} charge points)."
            )
            return False
        hero.resource -= hero.special_cost
        message, damage = hero.special_effect(enemy)
        animate_attack(enemy, special=True)
        print(message)
        if damage:
            dealt = enemy.take_damage(damage)
            hero.total_damage += dealt
            print(f"You deal {dealt} damage.")
        return True

    if action in ("p", "potion", "3"):
        if hero.potions == 0:
            print("\033[1;91mYou have no healing potions left.\033[0m")
            return False
        if hero.health == hero.max_health:
            print(
                f"\033[1;93mHP is already full "
                f"({hero.health}/{hero.max_health}). "
                "Your potion was not used.\033[0m"
            )
            return False
        hero.potions -= 1
        restored = hero.heal(40)
        print(f"You drink a potion and recover {restored} HP.")
        return True

    if action in ("f", "flee", "5"):
        print("You retreat from the adventure.")
        return None

    print("\033[1;91mChoose A, S, P, or F.\033[0m")
    return False


def enemy_turn(hero, enemy):
    if enemy.poison_turns:
        poison_damage = enemy.take_damage(8)
        hero.total_damage += poison_damage
        enemy.poison_turns -= 1
        print(f"Poison deals {poison_damage} damage to the {enemy.name}.")
        if enemy.health == 0:
            print(f"The {enemy.name} falls to the poison!")
            return

    if enemy.stunned:
        enemy.stunned = False
        print(f"The {enemy.name} is stunned and misses its turn!")
        return

    if hero.evading:
        hero.take_damage(0)
        return

    enemy.turns += 1
    damage = enemy.attack()
    if enemy.name == "Ancient Dragon" and enemy.turns % 3 == 0:
        damage += 12
        print("The dragon unleashes a devastating fire breath!")
    elif enemy.name == 'THE CREATOR "JEZAR"' and enemy.turns % 3 == 0:
        damage += 18
        print("THE CREATOR JEZAR rewrites reality with a world-shattering strike!")
    else:
        print(f"The {enemy.name} attacks!")
    animate_attack(enemy, incoming=True)
    damage_taken = hero.take_damage(damage)
    print(f"You take {damage_taken} damage.")


def fight(hero, encounter, encounter_number):
    enemy = Enemy(
        encounter["name"],
        encounter["title"],
        encounter["health"],
        encounter["attack"],
        encounter["art"],
        encounter["reward"],
    )
    animate_journey_scene()
    while hero.health > 0 and enemy.health > 0:
        clear_screen()
        show_status(hero, enemy, encounter_number, encounter["art"])
        show_menu = True
        while True:
            result = player_turn(hero, enemy, show_menu=show_menu)
            if result is not False:
                break
            show_menu = False
        if result is None:
            return "fled"
        if enemy.health == 0:
            print(f"\n{enemy.name} is defeated!")
            return "victory"
        enemy_turn(hero, enemy)
        if enemy.health == 0:
            print(f"\n{enemy.name} is defeated!")
            return "victory"
        if hero.health == 0:
            print(f"\n{hero.name} has fallen...")
            return "defeat"
    return "defeat"


def claim_victory_boon(hero):
    print("\n\033[1;91mTHE DARKNESS OFFERS A BOON. CHOOSE WISELY.\033[0m")
    print(
        f"  1  Mend your wounds: restore up to 30 HP "
        f"(currently {hero.health}/{hero.max_health})"
    )
    if hero.potions < 5:
        print(f"  2  Salvage a potion: gain 1 (currently {hero.potions}/5)")
    else:
        print("  2  Salvage a potion: unavailable (satchel full)")
    print(
        f"  3  Sharpen your weapon: +2 attack power "
        f"(currently {hero.attack_power})"
    )

    while True:
        choice = input("\nChoose your boon (1-3): ").strip().lower()
        if choice in ("1", "mend"):
            restored = hero.heal(30)
            print(f"You recover {restored} HP.")
            return
        if choice in ("2", "potion"):
            if hero.potions >= 5:
                print("Your potion satchel is full. Choose another boon.")
                continue
            hero.potions += 1
            print(f"You salvage a potion. Potions: {hero.potions}/5.")
            return
        if choice in ("3", "sharpen"):
            hero.attack_power += 2
            print(f"Your attack power rises to {hero.attack_power} for this run.")
            return
        print("Choose 1, 2, or 3.")


def play_game():
    if not sys.stdout.isatty():
        print_title()
    print("A blight is spreading from the mountain. The realm needs a hero.")
    print("=" * 58)
    print('Create your hero, defeat the enemies, and face THE CREATOR "Jezar".')
    print("Combat actions: A attack | S special | P potion | F flee")
    print("=" * 58)

    while True:
        name = input("\nWhat is your name, adventurer? ").strip()
        if name:
            break
        print("Your name cannot be empty.")

    hero = choose_hero(name)
    if hero is None:
        return False
    print(f"\nWelcome, {hero.name} the {hero.__class__.__name__}!")
    result = "victory"
    victories = 0

    for index, encounter in enumerate(ENCOUNTERS, start=1):
        result = fight(hero, encounter, index)
        if result != "victory":
            break
        victories += 1
        print("Victory!")
        for message in hero.gain_experience(encounter["reward"]):
            print(message)
        tip = VICTORY_TIPS[(victories - 1) % len(VICTORY_TIPS)]
        print(f"\n\033[1;91mTHE DARKNESS WHISPERS: {tip}\033[0m")
        claim_victory_boon(hero)
        if index < len(ENCOUNTERS):
            input("\nPress Enter to continue...")

    print(f"\n\033[1;96m{'=' * 58}\033[0m")
    if result == "victory":
        print("\033[1;92m" + r"""
     /\        /\        /\        /\
    /  \  /\  /  \  /\  /  \  /\  /  \
   /____\/__\/____\/__\/____\/__\/____\
       THE KINGDOM IS SAFE. YOU ARE A LEGEND.
""" + "\033[0m")
    elif result == "defeat":
        print("\033[1;91mYOUR QUEST ENDS HERE\033[0m")
    else:
        print("\033[1;94mTHE QUEST WILL WAIT FOR YOUR RETURN.\033[0m")

    print(f"\033[96mHero:\033[0m \033[97m{hero}\033[0m")
    print(
        f"\033[96mEncounters won:\033[0m "
        f"\033[93m{victories}/{len(ENCOUNTERS)}\033[0m"
    )
    print(f"\033[96mTotal damage dealt:\033[0m \033[95m{hero.total_damage}\033[0m")
    print(f"\033[96mAttack power:\033[0m \033[91m{hero.attack_power}\033[0m")
    print(f"\033[96mPotions remaining:\033[0m \033[92m{hero.potions}\033[0m")
    health_color = (
        "\033[92m"
        if hero.health > hero.max_health // 2
        else "\033[93m"
        if hero.health > 0
        else "\033[91m"
    )
    print(
        f"\033[96mFinal health:\033[0m "
        f"{health_color}{hero.health}/{hero.max_health}\033[0m"
    )
    return True


def main():
    random.seed()
    with windows_quick_edit_disabled():
        while True:
            if not show_start_screen():
                print("Thanks for playing!")
                return
            clear_screen()
            completed = play_game()
            if not completed:
                print("Thanks for playing!")
                return
            while True:
                choice = input("\n[R]etry or [Q]uit? ").strip().lower()
                if choice in ("r", "retry", "y", "yes"):
                    break
                if choice in ("q", "quit", "n", "no"):
                    print("Thanks for playing!")
                    return
                print("Choose R to try again or Q to quit.")
            random.seed()


if __name__ == "__main__":
    main()
