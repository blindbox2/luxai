import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
import operator

DIRECTIONS = Constants.DIRECTIONS
game_state = None

def get_map_info(game_state, player):
    width = game_state.map.width
    height = game_state.map.height

    resource_tiles = []
    city_tiles = []
    empty_tiles = []
    unit_locations = []

    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)

            if cell.has_resource():
                if cell.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
                if cell.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue
                resource_tiles.append(cell)
            elif cell.citytile is not None:
                city_tiles.append(cell)
            else:
                empty_tiles.append(cell)

    for unit in player.units:
        cell = game_state.map.get_cell_by_pos(unit.pos)
        unit_locations.append(cell)

    map_info = {
        "resource_tiles": resource_tiles,
        "city_tiles": city_tiles,
        "empty_tiles": empty_tiles,
        "unit_locations": unit_locations}

    return map_info


def get_closest(origin, potential_goals):    
    closest_dist = math.inf
    closest_goal = None

    for goal in potential_goals:
        dist = goal.pos.distance_to(origin.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_goal = goal

    return closest_goal


def move_to(unit, goal):
    future_position = unit.pos.direction_to(goal.pos)
    command = unit.move(future_position)
    return command, future_position


def get_possible_build_locations(empty_tiles, player):
    build_locations: list[Cell] = []

    for city in player.cities.values():
        for tile in city.citytiles:
            for empty_tile in empty_tiles:
                if tile.pos.is_adjacent(empty_tile.pos):
                    build_locations.append(empty_tile)

    return list(set(build_locations))


def calculate_fuel_worth(unit):
    fuel_amount = 0 

    fuel_amount += unit.cargo.wood * 1
    fuel_amount += unit.cargo.coal * 10
    fuel_amount += unit.cargo.uranium * 40

    return fuel_amount


def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]

    map_info = get_map_info(game_state, player)

    safe_cities = []
    unsafe_cities = []

    for city in player.cities.values():
        if city.fuel < 10 * city.light_upkeep:
            unsafe_cities.append(city)
        else:
            safe_cities.append(city)

        for city_tile in city.citytiles:
            if city_tile.can_act():
                if player.city_tile_count > len(player.units):
                    actions.append(city_tile.build_worker())
                else:
                    actions.append(city_tile.research())

    future_unit_locations = []

    for unit in player.units:
        if unit.is_worker() and unit.can_act():
            if unit.get_cargo_space_left() > 0:
                closest_resource_tile = get_closest(unit, map_info["resource_tiles"])
                command, future_position = move_to(unit, closest_resource_tile)

                if future_position not in future_unit_locations:
                    future_unit_locations.append(future_position)
                    actions.append(command)

            elif len(unsafe_cities) > 0:
                city_in_need = unsafe_cities[0]
                closest_city_tile = get_closest(unit, city_in_need.citytiles)
                command, _ = move_to(unit, closest_city_tile)
                actions.append(command)

                if city_in_need.fuel + calculate_fuel_worth(unit) > city_in_need.light_upkeep:
                    unsafe_cities.pop(0)
            elif not unit.can_build(game_state.map):
                possible_build_locations = get_possible_build_locations(map_info["empty_tiles"], player)
                if len(possible_build_locations) > 0:
                    closest_build_location = get_closest(unit, possible_build_locations)
                    command, future_position = move_to(unit, closest_build_location)

                    if future_position not in future_unit_locations:
                        future_unit_locations.append(future_position)
                        actions.append(command)
            else:
                actions.append(unit.build_city())

    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))
    
    return actions
