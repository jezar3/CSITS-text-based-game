import os
import random
import sys
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
          ,      ,
         /(.-""-.)\
     |\  \/      \/  /|
     | \ / =.  .= \ / |
     \ (   o\/o   ) /
      \_`-.__.-'_/
        /  ||  \
       /___||___\
""",
    },
    {
        "name": "Cave Troll",
        "title": "The Bridge Keeper",
        "health": 85,
        "attack": 14,
        "reward": 45,
        "art": r"""
         .-------.
        / .--.   \
       | (o  o)  |
       |   __    |
        \ '___' /
         /|   |\
        /_|___|_\
""",
    },
    {
        "name": "Orc Champion",
        "title": "The Arena of Bones",
        "health": 110,
        "attack": 17,
        "reward": 60,
        "art": r"""
          __,__
         /     \
        |  o o  |
        |   ^   |
       /|  ___  |\
      /_|_/   \_|_\
         /| |\
        /_| |_\
""",
    },
    {
        "name": "Skeleton Knight",
        "title": "The Forgotten Crypt",
        "health": 100,
        "attack": 16,
        "reward": 55,
        "art": r"""
             .-.
            (o.o)
             |=|
            __|__
           /|   |\
          /_|___|_\
            /   \
           _|   |_
""",
    },
    {
        "name": "Swamp Hydra",
        "title": "The Mire of Many Heads",
        "health": 135,
        "attack": 18,
        "reward": 70,
        "art": r"""
             /\     /\
        /\  (  )   (  )  /\
       (  \  \/     \/  /  )
        \  \  /\___/\  /  /
         \  \/  o o  \/  /
          \    \_^_/    /
           \___________/
             /|     |\
            /_|_____|_\
""",
    },
    {
        "name": "Ancient Dragon",
        "title": "The Last Ember",
        "health": 175,
        "attack": 21,
        "reward": 90,
        "art": r"""
                   /           /
             /' .,/ \         / \ .' /
            /     |  \       /  |     \
           /      |   \_____/   |      \
          /_______|   /  _  \   |_______\
                  \  | (o) |  /
                   \  \___/  /
                    \_______/
                    /|     |\
                   /_|_____|_\
""",
    },
    {
        "name": "THE CREATOR \"JEZAR\"",
        "title": "The End of All Things",
        "health": 240,
        "attack": 24,
        "reward": 200,
        "art": r"""
              .-=========-.
             /  .-===-.   \
            |  /  o o  \   |
            | |    ^    |  |
            |  \  ___  /   |
             \  '-----'   /
          ____'._______.'____
         /       | |       \
        /____    | |    ____\
             \___|_|___/
              /  JEZAR  \
             /___________\
""",
    },
]


def health_bar(current, maximum, width=20):
    filled = round(width * current / maximum)
    return f"|{'=' * filled}{'.' * (width - filled)}| {current}/{maximum} HP"


def clear_screen():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def format_art(art, width=58):
    lines = (line.strip() for line in textwrap.dedent(art).strip().splitlines())
    return "\n".join(line.center(width).rstrip() for line in lines)


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
    print(f"ENCOUNTER {encounter_number}: {enemy.title}")
    print(f"{enemy.name} appears!")
    print(format_art(art))
    print(f"{hero} | HP {health_bar(hero.health, hero.max_health)}")
    print(
        f"{enemy.name} | HP {health_bar(enemy.health, enemy.max_health)}"
    )
    print(
        f"{hero.resource_name}: {hero.resource}/3  |  "
        f"Potions: {hero.potions}  |  "
        f"Special: {hero.special_name}"
    )


def player_turn(hero, enemy):
    print("\n[A]ttack  [S]pecial  [P]otion  [I]nspect  [F]lee")
    action = input("> ").strip().lower()

    if action in ("a", "attack", "1"):
        damage = enemy.take_damage(hero.attack())
        hero.total_damage += damage
        hero.resource = min(3, hero.resource + 1)
        print(f"You strike the {enemy.name} for {damage} damage.")
        return True

    if action in ("s", "special", "2"):
        if hero.resource < hero.special_cost:
            print(
                f"Not enough {hero.resource_name}. "
                f"Attack to build up your special ({hero.resource}/3)."
            )
            return False
        hero.resource -= hero.special_cost
        message, damage = hero.special_effect(enemy)
        print(message)
        if damage:
            dealt = enemy.take_damage(damage)
            hero.total_damage += dealt
            print(f"You deal {dealt} damage.")
        return True

    if action in ("p", "potion", "3"):
        if hero.potions == 0:
            print("You have no healing potions left.")
            return False
        if hero.health == hero.max_health:
            print("You are already at full health.")
            return False
        hero.potions -= 1
        restored = hero.heal(40)
        print(f"You drink a potion and recover {restored} HP.")
        return True

    if action in ("i", "inspect", "4"):
        print(f"\n{hero}: {hero.health}/{hero.max_health} HP")
        print(
            f"{hero.resource_name}: {hero.resource}/3 | "
            f"Potions: {hero.potions} | Attack: {hero.attack_power}"
        )
        print(
            f"{enemy.name}: {enemy.health}/{enemy.max_health} HP | "
            f"Attack: about {enemy.attack_power} damage"
        )
        print("Build 3 resource with attacks to unleash your special.")
        return False

    if action in ("f", "flee", "5"):
        print("You retreat from the adventure.")
        return None

    print("Choose A, S, P, I, or F.")
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
    while hero.health > 0 and enemy.health > 0:
        clear_screen()
        show_status(hero, enemy, encounter_number, encounter["art"])
        result = player_turn(hero, enemy)
        if result is None:
            return "fled"
        if result is False:
            continue
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


def main():
    random.seed()
    print_title()
    print("A blight is spreading from the mountain. The realm needs a hero.")

    while True:
        name = input("\nWhat is your name, adventurer? ").strip()
        if name:
            break
        print("Your name cannot be empty.")

    hero = choose_hero(name)
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
        if index < len(ENCOUNTERS):
            input("\nPress Enter to continue...")

    print(f"\n{'=' * 58}")
    if result == "victory":
        print(r"""
     /\        /\        /\        /\
    /  \  /\  /  \  /\  /  \  /\  /  \
   /____\/__\/____\/__\/____\/__\/____\
       THE KINGDOM IS SAFE. YOU ARE A LEGEND.
""")
    elif result == "defeat":
        print("YOUR QUEST ENDS HERE")
    else:
        print("THE QUEST WILL WAIT FOR YOUR RETURN.")

    print(f"Hero: {hero}")
    print(f"Encounters won: {victories}/{len(ENCOUNTERS)}")
    print(f"Total damage dealt: {hero.total_damage}")
    print(f"Potions remaining: {hero.potions}")
    print(f"Final health: {hero.health}/{hero.max_health}")


if __name__ == "__main__":
    main()
