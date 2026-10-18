class Hero:
    max_health = 100

    def __init__(self, name, base_attack):
        self.name = name
        self.base_attack = base_attack
        self.__healthpoint = self.max_health

    def get_health(self):
        return self.__healthpoint

    def set_health(self, health):
        self.__healthpoint = max(0, min(self.max_health, health))
        return self.__healthpoint

    def take_damage(self, damage):
        damage_dealt = min(max(0, damage), self.__healthpoint)
        self.set_health(self.__healthpoint - damage_dealt)
        return damage_dealt

    def heal(self, amount):
        health_restored = min(max(0, amount), self.max_health - self.__healthpoint)
        self.set_health(self.__healthpoint + health_restored)
        return health_restored

    def __str__(self):
        return f"NAME: {self.name}. HP: {self.__healthpoint}"

    def attack(self):
        return self.base_attack

class Warrior(Hero):
    def attack(self):
        print("Battle axe (SLASH!)")
        return self.base_attack + 7


class Mage(Hero):
    def attack(self):
        print("Crystal Meteors (SPELL!)")
        return self.base_attack + 30


def calculate_total_damage(*args):
    return sum(args)


def main():
    print("!****HELLO MIGHTY PLAYER****!")
    print("Pick a role: Mage or Warrior")

    while True:
        player_choice = input("ENTER YOUR ROLE: ").strip().lower()
        if player_choice == "mage":
            player = Mage("Jezar", 40)
            break
        if player_choice == "warrior":
            player = Warrior("Jezar", 10)
            break
        print("Please choose Mage or Warrior.")

    enemy_orc = Warrior("Orc", 10)
    total_damage = 0

    while player.get_health() > 0 and enemy_orc.get_health() > 0:
        print("\nPick your action: 1. Attack  2. Heal  3. Flee")
        try:
            action = int(input("> "))
        except ValueError:
            print("Enter 1, 2, or 3.")
            continue

        if action == 1:
            damage = enemy_orc.take_damage(player.attack())
            total_damage = calculate_total_damage(total_damage, damage)
            print(
                f"You dealt {damage} damage. "
                f"Orc current health: {enemy_orc.get_health()}"
            )
        elif action == 2:
            restored = player.heal(10)
            print(
                f"You restored {restored} HP. "
                f"Player current health: {player.get_health()}"
            )
        elif action == 3:
            print("Player fled the battle.")
            break
        else:
            print("Enter 1, 2, or 3.")
            continue

        if enemy_orc.get_health() == 0:
            print("You defeated the orc!")
            break

        damage = player.take_damage(enemy_orc.attack())
        print(
            f"The orc dealt {damage} damage. "
            f"Player current health: {player.get_health()}"
        )
        if player.get_health() == 0:
            print("You were defeated by the orc.")

    print(f"TOTAL DAMAGE DEALT: {total_damage}")
    print(f"BATTLE STATUS: PLAYER {player} | ENEMY {enemy_orc}")


if __name__ == "__main__":
    main()
