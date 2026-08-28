"""
Framework-agnostic core logic for the Pokemon Team Builder.

This module has ZERO input() calls and ZERO Streamlit/CLI-specific code. It's pure
data logic that both Main(python).py (terminal) and streamlit_app.py (web UI) can
import and call. This split exists so the same battle-tested logic backs both
interfaces instead of being duplicated.

IMPORTANT DESIGN NOTE FOR THE WEB UI
-------------------------------------
The original pokemon_team.csv approach (write the "current team" to a shared file,
read it back) works fine for a single person in a terminal, but breaks down the
moment this becomes a deployed web app: every visitor would share and overwrite the
same file. So in this module, the "current team" is never written to disk. It's
just a pandas DataFrame that the caller (streamlit_app.py) holds in per-visitor
session state. Only the read-only source data (gen CSVs, pokemon_all_gens.csv) is
ever read from disk here.
"""

import csv
import os
import random
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

READ_DIR = os.path.join(SCRIPT_DIR, "..", "Data", "pokemon_datasets")

TEAM_STAT_COLUMNS = ["name", "type1", "type2", "pokemon_class", "attack", "sp_attack",
                     "defense", "sp_defense", "hp", "speed", "battle_archetypes"]

# All valid Pokemon types a user can filter/build a team by.
ALL_TYPES = ['ice', 'fire', 'water', 'grass', 'normal', 'electric', 'psychic', 'dark',
             'fairy', 'fighting', 'rock', 'steel', 'bug', 'poison', 'flying', 'ghost',
             'dragon', 'ground']

# The three pokemon "classes" a user can toggle on/off for team generation.
POKEMON_CLASSES = ['normal', 'legendary', 'mythical']

# The three evolution-stage buckets a user can toggle on/off for team generation. Note
# these are DERIVED buckets, not a literal read of evolution_stage -- see
# _evolution_bucket() for why (short version: evolution_stage==0 means "never evolves"
# and is bucketed as 'final', not 'starter'; and a 2-stage chain's final form sits at
# evolution_stage==2, not 3).
EVOLUTION_STAGES = ['starter', 'middle', 'final']

# Placeholder used when a team slot can't find any pokemon that satisfies the chosen
# type(s), allowed class(es), and allowed evolution stage(s).
EMPTY_SLOT = "Empty Pokeball"

BATTLE_ARCHETYPES = ['juggernaut', 'sweeper', 'bulky_attacker', 'glass_cannon', 'support',
                      'tank', 'bulky_speedster', 'attacker', 'slow_attacker', 'bulky',
                      'weak_slow', 'slow_support', 'fragile', 'balanced', 'midrange']

GOD_RANK = ['juggernaut', 'sweeper', 'bulky_attacker']
DEMIGOD_RANK = ['glass_cannon', 'tank', 'support']
HERO_RANK = ['bulky', 'bulky_speedster', 'attacker']
MORTAL_RANK = ['slow_attacker', 'slow_support', 'weak_slow']
PUNY_RANK = ['fragile', 'balanced', 'midrange']


def _evolution_bucket(evolution_stage, is_final_evolution) -> str:
    """Classifies a pokemon into 'starter' / 'middle' / 'final' from the raw
    evolution_stage + is_final_evolution columns.

    evolution_stage is a *positional* value (1st form, 2nd form, 3rd form) and
    is_final_evolution tells you whether that position happens to be the end of the
    line -- which depends on how long the line is. So evolution_stage alone isn't
    enough: for a 2-stage line (e.g. Eevee -> Vaporeon) the final form sits at
    evolution_stage==2, the same value a 3-stage line's true *middle* form uses (e.g.
    Ivysaur). is_final_evolution disambiguates the two.

    evolution_stage==0 is used for pokemon with no evolution line at all (Tauros,
    Mewtwo, Ditto, ...). These are bucketed as 'final' rather than 'starter': a
    pokemon that never evolves is already at the end of its (nonexistent) line, and
    lumping standalone legendaries/pseudo-legendaries like Mewtwo in with true
    first-stage starters like Bulbasaur would be misleading for anyone filtering for
    "early game" picks specifically.
    """
    if is_final_evolution == 1 or evolution_stage == 0:
        return 'final'
    if evolution_stage == 1:
        return 'starter'
    return 'middle'



def _gen_path(gen_num):
    return os.path.join(READ_DIR, f"pokemon_gen{gen_num}.csv")


def _master_path():
    return os.path.join(READ_DIR, "pokemon_all_gens.csv")


# Data loading (read-only, shared, safe to cache)

def _diagnose_csv_parse_error(path: str, label: str, original_error: Exception) -> str:
    """Builds an actionable error message for a malformed CSV.

    pandas' C parser raises pandas.errors.ParserError with only a line number and a
    "expected N fields, saw M" count -- it doesn't say which file, or what the
    offending row actually contains, which makes tracking down the bad row tedious
    (especially with several similarly-named gen CSVs). This re-reads the file with
    Python's csv module (which respects quoting the same way pandas does, so it will
    land on the same bad row) and lists every field on that row, numbered, so the
    stray comma is easy to spot by eye instead of being buried in a truncated preview.
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            expected = len(header)
            for line_num, row in enumerate(reader, start=2):
                if len(row) != expected:
                    numbered_fields = "\n".join(
                        f"  field {i + 1}: {value!r}" for i, value in enumerate(row)
                    )
                    return (
                        f"{label} ({path}) has a malformed row at line {line_num}: "
                        f"expected {expected} fields (from the header) but found "
                        f"{len(row)}.\n\n"
                        f"Every field on that line, in order:\n{numbered_fields}\n\n"
                        "Look for one field that looks like it contains two values "
                        "separated by a comma that shouldn't be there. Common causes: "
                        "a decimal number saved with a comma instead of a period (e.g. "
                        "'3,5' instead of '3.5'), or a stray comma accidentally typed "
                        "while manually aligning/padding a column (this file's values "
                        "have hand-formatted-looking whitespace padding around them, "
                        "which makes that easy to do by accident). Once you find it, "
                        "either remove the extra comma or wrap that value in double "
                        "quotes, then re-save."
                    )
    except OSError:
        pass
    return f"{label} ({path}) couldn't be parsed as CSV: {original_error}"


def _read_csv_safely(path: str, label: str) -> pd.DataFrame:
    """pd.read_csv wrapped to give a much more actionable error when the CSV is
    malformed, instead of surfacing pandas' bare C-parser error.
    """
    try:
        return pd.read_csv(path)
    except pd.errors.ParserError as e:
        raise pd.errors.ParserError(_diagnose_csv_parse_error(path, label, e)) from e


def load_master() -> pd.DataFrame:
    return _read_csv_safely(_master_path(), "pokemon_all_gens.csv")

def load_gen(gen_num) -> pd.DataFrame:
    return _read_csv_safely(_gen_path(gen_num), f"pokemon_gen{gen_num}.csv")


def join_gens(gens: list) -> pd.DataFrame:
    """Reads and concatenates one or more generation CSVs."""
    dfs = [load_gen(g) for g in gens]
    return pd.concat(dfs, ignore_index=True)

def random_number_generator(minimum, maximum):
    return random.randint(minimum, maximum)

def type_checker(poke_type):
    if len(poke_type) < 6:
        while len(poke_type) < 6:
            idx = random_number_generator(0, len(poke_type) - 1)
            poke_type.append(poke_type[idx].lower())
    return poke_type


# Team building
def build_team(team_source: pd.DataFrame, poke_type, allowed_classes=None, allowed_evolution_stages=None) -> dict:
    """Builds a random 6-slot team from `team_source`, matched against `poke_type`.

    Each selected type is given its own team slot where possible, matched against a
    pokemon's primary type (type1) first, and picks are made in the order the types
    were selected -- this guarantees every selected type shows up in the result
    (instead of the old approach, which pooled all type1 matches together and took a
    flat random sample, so a type with a small type1 pool -- or one that mostly shows
    up as a *secondary* type, like flying or poison -- could easily be left out
    entirely, which is why the 3rd/4th selected type sometimes went missing).

    If more than 6 types are selected there aren't enough slots for one type per slot,
    so types beyond the 6th (in selection order) are matched against a pokemon's
    secondary type (type2) instead of getting a dedicated slot -- folding the extra
    type coverage into the six slots that actually exist rather than requiring a slot
    that isn't there.

    allowed_classes restricts which pokemon "classes" (normal/legendary/mythical) are
    allowed on the team -- defaults to allowing all three, matching old behavior.

    allowed_evolution_stages restricts candidates to given 'starter'/'middle'/'final'
    buckets (see _evolution_bucket for exactly what each bucket means) -- defaults to
    allowing all three.

    Any slot that can't be filled (no eligible pokemon of an allowed class and
    evolution stage matches its type) becomes EMPTY_SLOT rather than leaving the team
    short a member.
    """
    if allowed_classes is None:
        allowed_classes = set(POKEMON_CLASSES)
    else:
        allowed_classes = set(allowed_classes)

    if allowed_evolution_stages is None:
        allowed_evolution_stages = set(EVOLUTION_STAGES)
    else:
        allowed_evolution_stages = set(allowed_evolution_stages)

    # De-duplicate while preserving selection order -- order matters once there are
    # more types selected than team slots (see docstring above).
    seen = set()
    ordered_types = []
    for t in poke_type:
        if t not in seen:
            seen.add(t)
            ordered_types.append(t)

    # A pokemon is a legal candidate if EITHER its type1 or type2 is one of the
    # selected types -- not type1 alone, so dual-typed pokemon whose selected type is
    # their secondary one are still in the pool.
    candidates = team_source[
        team_source["type1"].isin(ordered_types) | team_source["type2"].isin(ordered_types)
    ].copy()
    candidates["evolution_bucket"] = [
        _evolution_bucket(stage, is_final)
        for stage, is_final in zip(candidates["evolution_stage"], candidates["is_final_evolution"])
    ]
    candidates = candidates[candidates["evolution_bucket"].isin(allowed_evolution_stages)]

    rows = candidates[["name", "type1", "type2", "pokemon_class"]].drop_duplicates("name")
    if rows.empty:
        return {}

    class_lookup = rows.set_index("name")["pokemon_class"].to_dict()
    type1_lookup = rows.set_index("name")["type1"].to_dict()
    type2_lookup = rows.set_index("name")["type2"].to_dict()
    all_names = list(class_lookup.keys())

    def eligible(name):
        return class_lookup.get(name) in allowed_classes

    used = set()
    chosen_names = []

    def pool_for_type(t, include_type2):
        pool = [
            n for n in all_names
            if n not in used and eligible(n)
            and (type1_lookup.get(n) == t or (include_type2 and type2_lookup.get(n) == t))
        ]
        random.shuffle(pool)
        return pool

    # Pass 1: reserve one slot per selected type, up to 6 slots, in selection order.
    # The first 6 selected types get matched on type1 (their "own" slot); any type
    # past the 6th only has type2 to ride along on, since there's no slot left to
    # dedicate to it.
    for i, t in enumerate(ordered_types):
        if len(chosen_names) >= 6:
            break
        pick_pool = pool_for_type(t, include_type2=(i >= 6))
        if pick_pool:
            pick = pick_pool[0]
            chosen_names.append(pick)
            used.add(pick)

    # Pass 2: fill any slots still open randomly from the full eligible pool -- covers
    # teams with fewer than 6 usable types, or a selected type with no eligible
    # candidates at all. Unchanged in spirit from the old fallback behavior.
    if len(chosen_names) < 6:
        remaining_pool = [n for n in all_names if n not in used and eligible(n)]
        random.shuffle(remaining_pool)
        needed = 6 - len(chosen_names)
        take = remaining_pool[:needed]
        chosen_names.extend(take)
        used.update(take)

    result = {}
    for i in range(6):
        result[f"slot{i+1}"] = chosen_names[i] if i < len(chosen_names) else EMPTY_SLOT
    return result


def team_stats(team, master_df: pd.DataFrame = None) -> pd.DataFrame:
    """team is a list of pokemon names (which may include EMPTY_SLOT placeholders from
    build_team). Pass master_df to avoid re-reading the CSV -- otherwise it reads it fresh."""
    df = master_df if master_df is not None else load_master()
    df = df[TEAM_STAT_COLUMNS]

    real_names = [n for n in team if n != EMPTY_SLOT]
    result_df = df[df["name"].isin(real_names)].copy()

    n_empty = sum(1 for n in team if n == EMPTY_SLOT)
    if n_empty:
        placeholder = {col: (0 if col in ("attack", "sp_attack", "defense", "sp_defense", "hp", "speed") else None)
                       for col in TEAM_STAT_COLUMNS}
        placeholder["name"] = EMPTY_SLOT
        placeholder["battle_archetypes"] = ""
        placeholders_df = pd.DataFrame([placeholder] * n_empty)
        result_df = pd.concat([result_df, placeholders_df], ignore_index=True)

    return result_df.reset_index(drop=True)


def validate_names_exist(names, master_df: pd.DataFrame = None):
    """Returns the list of names in `names` that are NOT found in the database."""
    df = master_df if master_df is not None else load_master()
    known = set(df["name"])
    return [n for n in names if n not in known]



# Team evaluation
def unpack(team):
    """Takes in a list of dicts, and returns a dict of each archetype and its counts"""
    battle_count = {k: 0 for k in BATTLE_ARCHETYPES}
    for row in team:
        if row['battle_archetypes'] in battle_count:
            battle_count[row['battle_archetypes']] = row['count']
    return battle_count


def team_evaluator(team, master_df: pd.DataFrame = None):
    """Takes in a list of 6 pokemon names, counts how many of each battle archetype is
    on that team, and returns an evaluation string."""
    full_team = team_stats(team, master_df=master_df)
    df = full_team.groupby('battle_archetypes').size().reset_index(name='count')
    df = df.sort_values('count', ascending=False)

    battle_list = df.to_dict('records')
    count = unpack(battle_list)

    # Only consider archetypes actually present on the team (count > 0), then find the
    # true max and min counts among them. Collecting all archetypes that match those
    # counts (rather than accumulating every key that beat a running threshold, as the
    # old loop did) guarantees "highest"/"lowest" reflect the real max/min, regardless
    # of dict iteration order.
    present = {key: c for key, c in count.items() if c > 0}

    highest = max(present.values())
    lowest = min(present.values())
    list_of_highest = [key for key, c in present.items() if c == highest]
    list_of_lowest = [key for key, c in present.items() if c == lowest]

    top = full_team[full_team['battle_archetypes'] == list_of_highest[0]]['name'].iloc[0]
    if list_of_lowest:
        bottom = full_team[full_team['battle_archetypes'] == list_of_lowest[-1]]['name'].iloc[0]
    else:
        bottom = full_team[full_team['battle_archetypes'] == list_of_highest[-1]]['name'].iloc[0]

    if set(list_of_highest).issubset(GOD_RANK):
        if set(list_of_lowest).issubset(GOD_RANK):
            result = f'You have a team that is Powerful and Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(DEMIGOD_RANK):
            result = f'You have a team that is Legendary! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(HERO_RANK):
            result = f'You have a team that is Epic! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(MORTAL_RANK):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. It is recomended that you switch out {bottom} with a pokemon that is more on par with the rest of your team.'
        elif set(list_of_lowest).issubset(PUNY_RANK):
            result = f'Your team has an Achilles Heel! Team MVP: {top}. Weakest Link: {bottom}. Please change out {bottom}, as they are too far below the level of {top}.'
        else:
            result = f'Your team is majority god tier! Team MVP: {top}. Weakest Link: {bottom}.'
    elif set(list_of_highest).issubset(DEMIGOD_RANK):
        if set(list_of_lowest).issubset(DEMIGOD_RANK):
            result = f'You have a team that is Powerful and Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(GOD_RANK):
            result = f'You have a team that is Legendary! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(HERO_RANK):
            result = f'You have a team that is Powerful! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(MORTAL_RANK):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. It is recomended that you switch out {bottom} with a pokemon that is more on par with the rest of your team.'
        elif set(list_of_lowest).issubset(PUNY_RANK):
            result = f'Your team has an Achilles Heel! Team MVP: {top}. Weakest Link: {bottom}. Please change out {bottom}, as they are too far below the level of {top}.'
        else:
            result = f'Your team sure is really strong! Team MVP: {top}. Weakest Link: {bottom}.'
    elif set(list_of_highest).issubset(HERO_RANK):
        if set(list_of_lowest).issubset(GOD_RANK):
            result = f'You have a team that is Epic! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(DEMIGOD_RANK):
            result = f'You have a team that is Powerful! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(HERO_RANK):
            result = f'You have a team that is Strong and Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(MORTAL_RANK):
            result = f'You have a team that is Good! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(PUNY_RANK):
            result = f'You have a team that is Average! Team MVP: {top}. Weakest Link: {bottom}.'
        else:
            result = f'Your team is pretty strong! Team MVP: {top}. Weakest Link: {bottom}.'
    elif set(list_of_highest).issubset(MORTAL_RANK):
        if set(list_of_lowest).issubset(GOD_RANK):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. Looks like most of your team is lower level than {top}, maybe save them as your Ace!'
        elif set(list_of_lowest).issubset(DEMIGOD_RANK):
            result = f'You have a team that is Average! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(HERO_RANK):
            result = f'You have a team that is Good! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(MORTAL_RANK):
            result = f'You have a team that is Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(PUNY_RANK):
            result = f'You have a good starter team going! Team MVP: {top}. Weakest Link: {bottom}.'
        else:
            result = f'Your team sure is something! Team MVP: {top}. Weakest Link: {bottom}.'
    elif set(list_of_highest).issubset(PUNY_RANK):
        if set(list_of_lowest).issubset(GOD_RANK):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. Looks like most of your team is lower level than {top}, maybe save them as your Ace!'
        elif set(list_of_lowest).issubset(DEMIGOD_RANK):
            result = f'You have a team that is Uneven! Team MVP: {top}. Weakest Link: {bottom}. Looks like most of your team is lower level than {top}, maybe save them as your Ace!'
        elif set(list_of_lowest).issubset(HERO_RANK):
            result = f'You have a team that is Average! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(MORTAL_RANK):
            result = f'You have a good starter team going! Team MVP: {top}. Weakest Link: {bottom}.'
        elif set(list_of_lowest).issubset(PUNY_RANK):
            result = f'You have a team that is Balanced! Team MVP: {top}. Weakest Link: {bottom}.'
        else:
            result = f'Your team is on the weaker side! Team MVP: {top}. Weakest Link: {bottom}.'
    else:
        result = f'Your team sure is a Mixed Bag! Team MVP: {top}. Weakest Link: {bottom}.'
    return result

# Archetype calculation
def compute_quantiles(master_df: pd.DataFrame = None) -> dict:
    """Computes the bottom/mid quantile thresholds used to classify a pokemon's
    archetype. Do this once (e.g. cached) rather than per-pokemon."""
    df = master_df if master_df is not None else load_master()
    return {
        "bottom33_bulk": df['bulk'].quantile(0.30),
        "mid33_bulk": df['bulk'].quantile(0.67),
        "bottom33_offense": df['offense'].quantile(0.05),
        "mid33_offense": df['offense'].quantile(0.67),
        "bottom33_speed": df['speed'].quantile(0.05),
        "mid33_speed": df['speed'].quantile(0.67),
    }


def _tier(value, low_thresh, high_thresh) -> str:
    """Classifies a value as 'high' (above the mid-33 threshold), 'mid' (between the
    bottom-33 and mid-33 thresholds), or 'low' (at/below the bottom-33 threshold)."""
    if value > high_thresh:
        return "high"
    elif value > low_thresh:
        return "mid"
    else:
        return "low"


_ARCHETYPE_TABLE = {
    ("high", "high", "high"): "juggernaut",
    ("high", "high", "mid"): "bulky_attacker",
    ("high", "high", "low"): "bulky_attacker",    
    ("high", "mid", "high"): "sweeper",
    ("high", "mid", "mid"): "attacker",
    ("high", "mid", "low"): "slow_attacker",        
    ("high", "low", "high"): "glass_cannon",
    ("high", "low", "mid"): "glass_cannon",
    ("high", "low", "low"): "glass_cannon",
    ("mid", "high", "high"): "bulky_speedster",
    ("mid", "high", "mid"): "bulky",
    ("mid", "high", "low"): "slow_attacker",
    ("mid", "mid", "high"): "midrange",
    ("mid", "mid", "mid"): "balanced",
    ("mid", "mid", "low"): "slow_attacker",
    ("mid", "low", "high"): "midrange",             
    ("mid", "low", "mid"): "midrange",
    ("mid", "low", "low"): "weak_slow",             
    ("low", "high", "high"): "support",
    ("low", "high", "mid"): "support",
    ("low", "high", "low"): "tank",
    ("low", "mid", "high"): "midrange",            
    ("low", "mid", "mid"): "midrange",              
    ("low", "mid", "low"): "slow_support",
    ("low", "low", "high"): "fragile",
    ("low", "low", "mid"): "fragile",
    ("low", "low", "low"): "weak_slow",
}


def calc_arch_from_stats(hp, attack, defense, sp_attack, sp_defense, speed, quantiles: dict) -> str:
    """Pure archetype calculation given a pokemon's raw stats and precomputed quantiles.
    Guaranteed to return one of the 15 known archetypes for any stat input -- never blank."""
    current_bulk = hp + defense + sp_defense
    current_offense = attack + sp_attack
    current_speed = speed

    off_tier = _tier(current_offense, quantiles["bottom33_offense"], quantiles["mid33_offense"])
    bulk_tier = _tier(current_bulk, quantiles["bottom33_bulk"], quantiles["mid33_bulk"])
    speed_tier = _tier(current_speed, quantiles["bottom33_speed"], quantiles["mid33_speed"])

    return _ARCHETYPE_TABLE[(off_tier, bulk_tier, speed_tier)]


def calc_arch(pokemon_name: str, team_df: pd.DataFrame, quantiles: dict = None, master_df: pd.DataFrame = None) -> str:
    """Looks up `pokemon_name` in the in-memory team_df and recalculates its archetype."""
    if quantiles is None:
        quantiles = compute_quantiles(master_df=master_df)
    row = team_df[team_df["name"] == pokemon_name].iloc[0]
    return calc_arch_from_stats(
        hp=row["hp"], attack=row["attack"], defense=row["defense"],
        sp_attack=row["sp_attack"], sp_defense=row["sp_defense"], speed=row["speed"],
        quantiles=quantiles,
    )