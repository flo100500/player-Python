from typing import List
from models.game_state import GameState
from models.player_action import PlayerAction
from models.base import Base
from models.position import Position
import math

def is_our_base_id(gameState : GameState, id : int) -> bool:
    for base in gameState.bases:
        if base.uid == id:
            return base.player == gameState.game.player
    return False
        
def get_base_from_id(gameState : GameState, id) -> Base:
    for base in gameState.bases:
        if base.uid == id:
            return base

def calc_distance(base1 : Base, base2 : Base) -> int:
    return int(math.sqrt((base1.position.x - base2.position.x)**2 + (base1.position.y - base2.position.y)**2 + (base1.position.z - base2.position.z)**2))

def calc_distances_to_bases(gameState : GameState, selected_base : Base) -> dict[int, int]:
    results = {}
    for base in gameState.bases:
        results[base.uid] = calc_distance(base, selected_base)
    return results

def get_nearest_enemy_base(gameState : GameState, distances_to_bases : dict[int,int]) -> int:
    base_id_of_current_min = 0
    current_min = 100000
    for base_id, distance in distances_to_bases.items():
        base = get_base_from_id(gameState, base_id)
        if distance < current_min and distance != 0 and base.player != gameState.game.player:
            base_id_of_current_min = base_id
            current_min = distance
    return base_id_of_current_min

def check_for_enemy_attack(gameState:GameState) -> dict[int, tuple[int,int]]:
    attack_on_base_dict : dict[int, tuple[int,int]] = {}
    for action in gameState.actions:
        if not is_our_base_id(gameState, action.dest):
            continue
        base : Base = get_base_from_id(gameState, action.dest)
        time_until_attack = action.progress.distance - action.progress.traveled
        if get_base_from_id(gameState, action.src).player == gameState.game.player:
            attack_on_base_dict[base.uid] = (-action.amount, time_until_attack)
        else:
            attack_on_base_dict[base.uid] = (action.amount, time_until_attack)
    return attack_on_base_dict

def help_bits_needed(gamestate: GameState, attack_on_bases_dict:dict, base: Base) -> int:
    amount = -base.population
    for attacked_base_id, values in attack_on_bases_dict.items():
        if attacked_base_id == base.id:
            amount += values[0]
    return amount

def find_middle(bases : list[Base]) -> Position:
    x, y, z = 0, 0, 0
    for base in bases:
        x += base.position.x
        y += base.position.y
        z += base.position.z
    n_bases = len(bases)
    x /= n_bases
    y /= n_bases
    z /= n_bases
    return Position(x, y, z)

def find_rand_direction(gamestate: GameState, all_bases, our_bases) -> Position:
    middle = find_middle(all_bases)
    our_middle = find_middle(our_bases)

    x = our_middle.x - middle.x
    y = our_middle.y - middle.y
    z = our_middle.z - middle.z

    return Position(x, y, z)


def calc_angle(a : Position, b : Position) -> float:
    return math.acos((a.x * b.x + a.y * b.y + a.z * b.z) / (math.sqrt(a.x**2 + a.y**2 + a.z**2) * math.sqrt(b.x**2 + b.y**2 + b.z**2)))

# def get_list_of_bases_how_need_help(gameState : GameState) -> list[int]:
#     for base in gameState.bases:
#         if base.player != 7:
#             continue
        

def decide(gameState: GameState) -> List[PlayerAction]:
    playeractions_list = []

    all_bases = gameState.bases
    our_bases : list[Base] = []
    for base in all_bases:
        if is_our_base_id(gameState, base.uid):
            our_bases.append(base)

    our_middle = find_middle(our_bases)

    attack_on_bases = check_for_enemy_attack(gameState)
    rand_direction = find_rand_direction(gameState, all_bases, our_bases)

    targets = []
    i : int = 0
    while len(targets) < 4 and i != 100:
        i += 1
        for our_base in our_bases:
            distances_to_bases : dict[int,int] = calc_distances_to_bases(gameState, our_base)
            print(distances_to_bases)
            for base_id, distance in distances_to_bases.items():
                if distance == i and base_id not in targets and not is_our_base_id(gameState, base_id):
                    targets.append(base_id)

    min_score_base = None
    for target_id in targets:
        min_score = 100000
        min_score_base = None
        target : Base = get_base_from_id(gameState, target_id)
        x = target.position.x - our_middle.x
        y = target.position.y - our_middle.y
        z = target.position.z - our_middle.z
        score = target.population + 3 * calc_angle(rand_direction, Position(x,y,z))
        if min_score > score:
            min_score = score
            min_score_base = target

    remaining_bits : dict[Base:int] = {}
    for our_base in our_bases:
        remaining_bits[our_base] = -help_bits_needed(gameState, attack_on_bases, our_base) - gameState.config.base_levels[our_base.level].max_population/2

    sum_remaining_bits = sum(remaining_bits.values())

            
    if sum_remaining_bits > 0:
        for our_base in our_bases:
            wanted_player_num = gameState.config.base_levels[our_base.level].max_population/2
            if our_base.population > wanted_player_num  and calc_distance(our_base, min_score_base) <= gameState.config.paths.grace_period:
                playeractions_list.append(PlayerAction(our_base.uid, min_score_base.uid, our_base.population - wanted_player_num))
            elif our_base.population > wanted_player_num*1.5 and our_base.level >= len(gameState.config.base_levels):
                playeractions_list.append(PlayerAction(our_base.uid, min_score_base.uid, our_base.population - wanted_player_num))
            elif our_base.population > wanted_player_num:
                playeractions_list.append(PlayerAction(our_base.uid, our_base.uid, our_base.population - wanted_player_num))

    return playeractions_list
