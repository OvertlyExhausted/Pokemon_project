"""
Pandas translation of the PySpark Pokemon Team Builder notebook.

WHY THIS EXISTS
----------------
The original code used Spark SQL tables running on a cluster. 
None of the actual logic needs distributed computing, so this version
swaps every Spark call for a pandas equivalent so you can run and test it locally

HOW "TABLES" ARE SIMULATED
---------------------------
- Read-only source tables (genN, pokemon_master) -> read directly from the CSVs.
- Tables the original code WROTE to with .saveAsTable() (poke_team, pokemon_team)
  -> written to/read back from CSV files in WRITE_DIR, so state persists across
  function calls the same way it did in Databricks.
"""

import os
import random
import pandas as pd

# Anchor to this script's own location (NOT the terminal's current working directory).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

READ_DIR = os.path.join(SCRIPT_DIR, "..", "Data", "pokemon_datasets")

# Folder where "tables" this script writes to (poke_team, pokemon_team) get stored.
WRITE_DIR = os.path.join(SCRIPT_DIR, "..", "Data", "pokemon_datasets")
os.makedirs(WRITE_DIR, exist_ok=True)


def _gen_path(gen_num):
    return os.path.join(READ_DIR, f"pokemon_gen{gen_num}.csv")


def _master_path():
    return os.path.join(READ_DIR, "pokemon_all_gens.csv")


def _poke_team_path():
    return os.path.join(WRITE_DIR, "poke_team.csv")


def _pokemon_team_path():
    return os.path.join(WRITE_DIR, "pokemon_team.csv")


# Function to Join Tables
def join_gens(gen: list) -> pd.DataFrame:
    """Reads and concatenates one or more generation CSVs, then persists the
    result to poke_team.csv (equivalent of saveAsTable)."""
    gen = list(gen)  # don't mutate the caller's list
    joined_tables = pd.read_csv(_gen_path(gen[0]))
    gen.pop(0)
    # if you actually have to join gens
    while len(gen) > 0:
        df = pd.read_csv(_gen_path(gen[0]))
        joined_tables = pd.concat([joined_tables, df], ignore_index=True)
        gen.pop(0)
    joined_tables.to_csv(_poke_team_path(), index=False)
    return joined_tables

# Random Number Generator -- unchanged, no Spark involved
def random_number_generator(minimum, maximum):
    return random.randint(minimum, maximum)

# Fill in Blank Spaces for Types of Pokemon -- unchanged, no Spark involved
def type_checker(poke_type):
    if len(poke_type) < 6:
        while len(poke_type) < 6:
            idx = random_number_generator(0, len(poke_type) - 1)
            poke_type.append(poke_type[idx].lower())
    return poke_type


# Function to Build Team
def build_team(team_source: pd.DataFrame, poke_type):
    # Step 1: Filter by types
    filtered_df = team_source[team_source["type1"].isin(poke_type)]

    # Step 2: Grab the columns we need
    rows = filtered_df[["name", "type1"]]

    if rows.empty:
        return {}

    # Step 3: Build pool of names (no duplicates)
    all_names = list(set(rows["name"]))

    # Step 4: Pick up to 6 random unique names
    chosen_names = random.sample(all_names, min(6, len(all_names)))

    # Step 5: Return as dict
    return {f"slot{i+1}": name for i, name in enumerate(chosen_names)}


# Team_Stats
def team_stats(team):  # team is a list of pokemon names
    df = pd.read_csv(_master_path())
    cols = ["name", "type1", "type2", "attack", "sp_attack", "defense",
            "sp_defense", "hp", "speed", "battle_archetypes"]
    df = df[cols]
    df = df[df["name"].isin(team)]
    return df.reset_index(drop=True)


# Unpack_Dict
def unpack(team):
    """Takes in a list of dicts, and returns a dict of each archetype and its counts"""
    battle_count = {'juggernaut': 0, 'sweeper': 0, 'bulky_attacker': 0, 'glass_cannon': 0,
                     'support': 0, 'tank': 0, 'bulky_speedster': 0, 'attacker': 0,
                     'slow_attacker': 0, 'bulky': 0, 'weak_slow': 0, 'slow_support': 0,
                     'fragile': 0, 'balanced': 0, 'midrange': 0}
    for row in team:
        if row['battle_archetypes'] in battle_count:
            battle_count[row['battle_archetypes']] = row['count']
    return battle_count

# Poketeam_Evaluator
def team_evaluator(team):
    """Takes in a list of 6 pokemon, counts how many of each battle archetype is on
    that team, and returns an evaluation string."""
    result = ''
    full_team = team_stats(team)
    df = full_team.groupby('battle_archetypes').size().reset_index(name='count')
    df = df.sort_values('count', ascending=False)

    list_of_highest = []
    list_of_lowest = []
    battle_list = df.to_dict('records')
    count = unpack(battle_list)

    highest = 0
    lowest = 6
    for key in count:
        if count[key] == 0:
            continue
        if count[key] >= highest:
            highest = count[key]
            list_of_highest.append(key)
        elif count[key] <= lowest:
            lowest = count[key]
            list_of_lowest.append(key)

    god_rank = ['juggernaut', 'sweeper', 'bulky_attacker']
    demigod_rank = ['glass_cannon', 'tank', 'support']
    hero_rank = ['bulky', 'bulky_speedster', 'attacker']
    mortal_rank = ['slow_attacker', 'slow_support', 'weak_slow']
    puny_rank = ['fragile', 'balanced', 'midrange']

    top = full_team[full_team['battle_archetypes'] == list_of_highest[0]]['name'].iloc[0]
    try:
        bottom = full_team[full_team['battle_archetypes'] == list_of_lowest[-1]]['name'].iloc[0]
    except IndexError:
        bottom = full_team[full_team['battle_archetypes'] == list_of_highest[-1]]['name'].iloc[0]

    if set(list_of_highest).issubset(god_rank):
        if set(list_of_lowest).issubset(god_rank):
            result = f'You have a team that is Powerful and Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(demigod_rank):
            result = f'You have a team that is Legendary! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(hero_rank):
            result = f'You have a team that is Epic! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(mortal_rank):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. It is recomended that you switch out {bottom} with a pokemon that is more on par with the rest of your team.'
        elif set(list_of_lowest).issubset(puny_rank):
            result = f'Your team has an Achilles Heel! Team MVP: {top}. Weakest Link: {bottom}. Please change out {bottom}, as they are too far below the level of {top}.'
        else:
            result = f'Your team is majority god tier! Team MVP: {top}. Weakest Link: {bottom}.'
    elif set(list_of_highest).issubset(demigod_rank):
        if set(list_of_lowest).issubset(demigod_rank):
            result = f'You have a team that is Powerful and Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(god_rank):
            result = f'You have a team that is Legendary! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(hero_rank):
            result = f'You have a team that is Powerful! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(mortal_rank):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. It is recomended that you switch out {bottom} with a pokemon that is more on par with the rest of your team.'
        elif set(list_of_lowest).issubset(puny_rank):
            result = f'Your team has an Achilles Heel! Team MVP: {top}. Weakest Link: {bottom}. Please change out {bottom}, as they are too far below the level of {top}.'
        else:
            result = f'Your team sure is really strong! Team MVP: {top}. Weakest Link: {bottom}.'
    elif set(list_of_highest).issubset(hero_rank):
        if set(list_of_lowest).issubset(god_rank):
            result = f'You have a team that is Epic! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(demigod_rank):
            result = f'You have a team that is Powerful! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(hero_rank):
            result = f'You have a team that is Strong and Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(mortal_rank):
            result = f'You have a team that is Good! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(puny_rank):
            result = f'You have a team that is Average! Team MVP: {top}. Weakest Link: {bottom}.'
        else:
            result = f'Your team is pretty strong! Team MVP: {top}. Weakest Link: {bottom}.'
    elif set(list_of_highest).issubset(mortal_rank):
        if set(list_of_lowest).issubset(god_rank):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. Looks like most of your team is lower level than {top}, maybe save them as your Ace!'
        elif set(list_of_lowest).issubset(demigod_rank):
            result = f'You have a team that is Average! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(hero_rank):
            result = f'You have a team that is Good! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(mortal_rank):
            result = f'You have a team that is Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(puny_rank):
            result = f'You have a good starter team going! Team MVP: {top}. Weakest Link: {bottom}.'
        else:
            result = f'Your team sure is something! Team MVP: {top}. Weakest Link: {bottom}.'
    elif set(list_of_highest).issubset(puny_rank):
        if set(list_of_lowest).issubset(god_rank):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. Looks like most of your team is lower level than {top}, maybe save them as your Ace!'
        elif set(list_of_lowest).issubset(demigod_rank):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. Looks like most of your team is lower level than {top}, maybe save them as your Ace!'
        elif set(list_of_lowest).issubset(hero_rank):
            result = f'You have a team that is Average! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(mortal_rank):
            result = f'You have a good starter team going! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(puny_rank):
            result = f'You have a team that is Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        else:
            result = f'Your team is on the weaker side! Team MVP: {top}. Weakest Link: {bottom}.'
    else:
        result = f'Your team sure is a Mixed Bag! Team MVP: {top}. Weakest Link: {bottom}.'
    return result

# Team_Generator
def generate_team():
    team = False
    poke_types = ['ice', 'fire', 'water', 'grass', 'normal', 'electric', 'psychic', 'dark',
                  'fairy', 'fighting', 'rock', 'steel', 'bug', 'poison', 'flying', 'ghost',
                  'dragon', 'ground']
    try:
        while team is False:
            gen = input("Hi! Please which generations you would like to use, seperated by spaces. Such as 1 2 5: ").strip()
            gen = gen.split(" ")
            for i in gen:
                if i.isdigit() is False:
                    raise ValueError("Please enter a NUMBER.")
            i = int(i)
            if i > 9 or i < 1:
                raise ValueError("Please enter a valid generation number between 1 and 9.")
            team_source = join_gens(gen)
            team = True
        team = False
        while team is False:
            poke_type = input("Please enter some types you would like to use, separated by commas: ").strip()
            poke_type = [ptype.strip() for ptype in poke_type.lower().split(",")]
            for poke in poke_type:
                if poke not in poke_types:
                    raise ValueError("Sorry! You must enter valid types.")
            full_team = build_team(team_source, poke_type)
            pokemon_list = [value for value in full_team.values()]
            if len(pokemon_list) != 6:
                print("Sorry! There's been an error")
                break
            else:
                team = True
                print('Your team is ready!')
            pokemon_team = team_stats(pokemon_list)
            pokemon_team.to_csv(_pokemon_team_path(), index=False)
            return team_stats(pokemon_list)
    except ValueError as e:
        print(e)

# Pokemon_Switcher
def poke_switch():
    full_team = pd.read_csv(_pokemon_team_path())
    pokemon_list = full_team["name"].tolist()
    ifThen = 1
    team = False
    try:
        while team is False:
            pokemon_switcher = input("Would you like to switch out a pokemon? (yes/no) ").strip()
            if pokemon_switcher.lower() == 'yes':
                pokemon_to_switch = input("Which pokemon would you like to switch out? ").strip()
            else:
                print("Aight, bye")
                ifThen = 0
                break
            if pokemon_to_switch not in pokemon_list:
                raise ValueError("Sorry! That pokemon isn't on your team.")
            else:
                new_pokemon = input("What pokemon would you like to switch to? ").strip()
                team_source = pd.read_csv(_master_path())
                exists = (team_source["name"] == new_pokemon).any()
                if not exists:
                    raise ValueError("Sorry! That pokemon isn't in the database.")
                else:
                    team = True
                    pokemon_list.remove(pokemon_to_switch)
                    pokemon_list.append(new_pokemon)
        if ifThen == 1:
            pokemon_team = team_stats(pokemon_list)
            pokemon_team.to_csv(_pokemon_team_path(), index=False)
            return team_stats(pokemon_list)
        else:
            pass
    except ValueError as e:
        print(e)

# Build_Team from Nothing
def poketeam_builder():
    """Based on pokemon name, enters pokemon and associated stats into a table, default to base stats"""
    slots = 0
    while slots == 0:
        chosen = input("Please enter 6 pokemon you would like for your team! You can seperate them by spaces, but spaces within names should be divided by (-) ")
        chosen = chosen.split(" ")
        for i in chosen:
            if i.isdigit() is True:
                raise ValueError("Please enter a valid pokemon name.")
            else:
                slots += 1
    team_source = pd.read_csv(_master_path())
    for i in chosen:
        exists = (team_source["name"] == i).any()
        if not exists:
            raise ValueError("Sorry! That pokemon isn't in the database.")
        else:
            print("Your team is ready!")
            break
    pokemon_team = team_stats(chosen)
    pokemon_team.to_csv(_pokemon_team_path(), index=False)
    return team_stats(chosen)


# Calc_Archetype
def calc_arch(pokemon):
    """Calculates a fresh archetype for an individual pokemon based on the name. It takes
    the current stats and compares them to the bottom 33%, middling 67% and the top
    percent of the database's sums for each column."""
    full_list = pd.read_csv(_master_path())

    bottom33_bulk = full_list['bulk'].quantile(0.30)
    mid33_bulk = full_list['bulk'].quantile(0.67)

    bottom33_offense = full_list['offense'].quantile(0.05)
    mid33_offense = full_list['offense'].quantile(0.67)

    bottom33_speed = full_list['speed'].quantile(0.05)
    mid33_speed = full_list['speed'].quantile(0.67)

    team_list = pd.read_csv(_pokemon_team_path())
    row = team_list[team_list["name"] == pokemon].iloc[0]

    current_speed = row["speed"]
    current_attack = row["attack"]
    current_sa = row["sp_attack"]
    current_defense = row["defense"]
    current_spd = row["sp_defense"]
    current_hp = row["hp"]

    current_bulk = current_hp + current_defense + current_spd
    current_offense = current_attack + current_sa

    archType = ""

    if current_offense > mid33_offense:
        if current_bulk > mid33_bulk:
            if current_speed > mid33_speed:
                archType = 'juggernaut'
            elif current_speed < mid33_speed and current_speed > bottom33_speed:
                archType = 'bulky_attacker'
        elif current_bulk < mid33_bulk and current_bulk > bottom33_bulk:
            if current_speed > mid33_speed:
                archType = "sweeper"
            elif current_speed > bottom33_speed and current_speed < mid33_speed:
                archType = "attacker"
        elif current_bulk < bottom33_bulk:
            if current_speed > bottom33_speed:
                archType = "glass_cannon"

    elif current_offense > bottom33_offense:
        if current_bulk > bottom33_bulk and current_speed < bottom33_speed:
            archType = "slow_attacker"
        if current_bulk > mid33_bulk:
            if current_speed > mid33_speed:
                archType = 'bulky_speedster'
            elif current_speed < mid33_speed and current_speed > bottom33_speed:
                archType = "bulky"
        elif current_bulk < mid33_bulk and current_bulk > bottom33_bulk:
            if current_speed < mid33_speed and current_speed > bottom33_speed:
                archType = "balanced"
    elif current_offense < bottom33_offense:
        if current_bulk > mid33_bulk:
            if current_speed > bottom33_speed:
                archType = "support"
            elif current_speed < bottom33_speed:
                archType = "tank"
        elif current_bulk > bottom33_bulk:
            if current_speed < bottom33_speed:
                archType = "slow_support"
        elif current_bulk < bottom33_bulk:
            if current_speed > bottom33_speed:
                archType = "fragile"
            elif current_speed < mid33_speed:
                archType = "weak_slow"
    else:
            archType = "balanced"
    return archType


# Team Editor
def team_edit():
    """This function takes the pokemon_team table and allows the user to edit individual
    stats for a pokemon, altering the battle archetype automatically"""
    source_list = pd.read_csv(_pokemon_team_path())
    pokemon = input("Hello! Please enter the name of the pokemon you wish to edit: ")
    if pokemon not in source_list["name"].tolist():
        raise ValueError("Sorry! That pokemon isn't on your team.")
    else:
        stat = input("Please enter the stat you wish to edit: ")
        if stat not in source_list.columns:
            raise ValueError("Sorry! That stat isn't in the database.")
        else:
            value = input("Please enter the value you wish to change it to: ")
            value = int(value)
            source_list.loc[source_list["name"] == pokemon, stat] = value
            source_list.to_csv(_pokemon_team_path(), index=False)
    new_type = calc_arch(pokemon)
    source_list.loc[source_list["name"] == pokemon, 'battle_archetypes'] = new_type
    source_list.to_csv(_pokemon_team_path(), index=False)
    return source_list
