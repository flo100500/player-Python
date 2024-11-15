from typing import List
from models.game_state import GameState
from models.player_action import PlayerAction
from models.base import Base
from models.game_state import GameState
import math

TEAM_ID : int = 7

def is_our_base_id(gameState : GameState, id : int) -> bool:
    for base in gameState.bases:
        if base.uid == id:
            return base.player == TEAM_ID
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
        if distance < current_min and distance != 0 and base.player != TEAM_ID:
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
        attack_on_base_dict[base.uid] = (action.amount, time_until_attack)
    return attack_on_base_dict

def help_bits_needed(gamestate: GameState, attack_on_bases_dict:dict, baseuid: int) -> int:
    base : Base = get_base_from_id(gamestate, baseuid)
    amount = -base.population
    for attacked_base_id, values in attack_on_bases_dict.items():
        if attacked_base_id == baseuid:
            amount += values[0]
    return amount

# def get_list_of_bases_how_need_help(gameState : GameState) -> list[int]:
#     for base in gameState.bases:
#         if base.player != 7:
#             continue
        

def decide(gameState: GameState) -> List[PlayerAction]:
    playeractions_list = []

    attack_on_bases = check_for_enemy_attack(gameState)

    for base in gameState.bases:
        if base.player != TEAM_ID:
            continue
        distances_to_bases = calc_distances_to_bases(gameState, base)
        nearest_enemy_base_id = get_nearest_enemy_base(gameState, distances_to_bases)
        distance = calc_distance(base, get_base_from_id(gameState, nearest_enemy_base_id))
        grace = gameState.config.paths.grace_period
        death_rate = gameState.config.paths.death_rate
        deat_players = (distance - grace) * death_rate if grace < distance else 0

        max_population = gameState.config.base_levels[base.level].max_population
        population_0_75 = int(0.75 * max_population)

        if base.population > population_0_75 and help_bits_needed(gameState, attack_on_bases, base.uid) <= 10 and not deat_players:
            playeractions_list.append(PlayerAction(base.uid, nearest_enemy_base_id, base.population - population_0_75))
        elif  base.population >= max_population:
            if deat_players and not len(gameState.config.base_levels) - 1 == base.level:
                playeractions_list.append(PlayerAction(base.uid, base.uid, base.population - max_population + gameState.config.base_levels[base.level].spawn_rate))
            else:
                amount = base.population - max_population + gameState.config.base_levels[base.level].spawn_rate
                if amount > death_rate:
                    playeractions_list.append(PlayerAction(base.uid, nearest_enemy_base_id, amount))
                else:
                    playeractions_list.append(PlayerAction(base.uid, nearest_enemy_base_id, death_rate))

    return playeractions_list
