# Pokémon Complete Dataset (Generations 1-9)

## Overview
This project builds a comprehensive Pokémon dataset covering **Generations 1 through 9** using data collected from the **PokéAPI** and enhanced with extensive **feature engineering** designed for machine learning and data analysis. 

The dataset combines:
- Base Pokémon attributes
- Battle stats
- Type matchup multipliers
- Species metadata
- Evolution data
- Engineered combat metrics
- Archetype classifications

---

## Dataset Summary

| Attribute | Value |
|------------|-------|
| Generations | 1-9 |
| Pokémon covered | 1025 |
| Rows | ~1500+ |
| Columns | ~80 |
| Forms Included | Yes |
| Data Source | PokéAPI |

---

## Data Source
Primary data source:

**PokéAPI**
https://pokeapi.co/

Pokémon intellectual property belongs to 
- **Nintendo**
- **Game Freak**
- **The Pokémon Company**

This dataset is intended for **educational and research purposes**.

---

## Dataset Files
This project produces two dataset types.

### Generation-Relative Datasets

| File | Description |
|-------|-------------|
| pokemon_gen1.csv | Generation 1 Pokémon |
| pokemon_gen2.csv | Generation 2 Pokémon |
| pokemon_gen3.csv | Generation 3 Pokémon |
| pokemon_gen4.csv | Generation 4 Pokémon |
| pokemon_gen5.csv | Generation 5 Pokémon |
| pokemon_gen6.csv | Generation 6 Pokémon |
| pokemon_gen7.csv | Generation 7 Pokémon |
| pokemon_gen8.csv | Generation 8 Pokémon |
| pokemon_gen9.csv | Generation 9 Pokémon |
| pokemon_all_gens_gen_relatives.csv | Combined dataset, where archetypes and stats are generation-related|

In these datasets, archetypes and percentile features are calculated **within each generation**.

---

### Overall Comparison Dataset
| File | Description |
|------|-------------|
| pokemon_all_gens.csv | Dataset where Pokémon are compared across all generations |

In this dataset:
- archetypes
- defensive typing classes
- stat distribution classes

are calculated **across the entire Pokédex**.

This allows direct comparison of Pokémon across generations.

---

## Row Definition
Each row represents **one Pokémon record** at the form/variety level. Since Pokémon may have multiple forms, the **Pokédex IDs are not unique**. Three columns identify a record, with **name** being the identifier.

**Example**:
| pokedex_id | species_name | name |
|-------------|--------------|-------|
| 25 | pikachu | pikachu |
| 25 | pikachu | pikachu-cosplay |
| 479 | rotom | rotom-heat |
| 1024 | terapagos | terapagos-stellar |

---

## Full Column Dictionary

### Identification
| Column | Description|
|---------|------------|
|`pokedex_id` | National Pokédex number |
| `species_name` | Species-level Pokémon name |
| `name` | Row-level identifier, including form/variety distinction where applicable |
| `generation` | Generation number |

---

### Typing
| Column | Description |
|---------|-------------|
| `type1` | Primary type |
| `type2` | Secondary type, if applicable |
| `type_count` | Number of types |

---

### Abilities
| Column | Description |
|---------|-------------|
| `abilities` | Standard abilities |
| `hidden_abilities` | Hidden abilities |

---

### Base Stats
| Column | Description |
|--------|--------------|
| `hp` | Base HP |
| `attack` | Base Attack |
| `defense` | Base Defense |
| `sp_attack` | Base Special Attack |
| `sp_defense` | Base Special Defense |
| `speed` | Base Speed |
| `base_stat_total` | Sum of all base stats |

---

### Normalized Stat Ratios
These columns represent the proportion of each stat in relation to the base stat.
| Column | Description |
|--------|-------------|
| `hp_ratio` | hp / base_stat_total |
| `attack_ratio` | attack / base_stat_total |
| `defense_ratio` | defense / base_stat_total |
| `sp_attack_ratio` | sp_attack / base_stat_total |
| `sp_defense_ratio` | sp_defense / base_stat_total |
| `speed_ratio` | speed / base_stat_total |

---

### Engineered Combat Metrics
| Column | Description |
|--------|-------------|
| `dominant_stat` | Highest base stat |
| `offense` | attack + sp_attack |
| `bulk` | hp + defense + sp_defense |
| `speed_tier` | Speed category (slow, average, fast) |
| `stat_variance` | Variance across the six base stats |
| `stat_variance_quantile` | Quantile group of stat variance |
| `stat_specialization` | Interpretable stat distribution class (not based on stat_variance_quantile due to pokemon having skewed variances)|

For speed_tier, any Pokémon with a base speed score under 60 is considered slow, under 100 is average, and 100+ is fast.

For stat_variance, anything under 200 is considered balanced, under 500 is slightly specialized, under 900 is specialized, under 1400 is highly specialized, and 1400+ is extreme

---

### Generation-Relative Strength
| Column | Description |
|--------|-------------|
| `bst_percentile_gen` | Base stat total percentile within generation |
| `bst_gen_class` | Tier label derived from generation-relative BST |

---

### Overall Strength Metrics
| Column | Description |
|--------|-------------|
| `bst_percentile_all` | Percentile rank across all Pokémon |
| `bst_all_class` | Overall strength tier classification |

In the generation-relative datasets, these columns reflect the same values as the generation-relative strength columns.

---

### Defensive Typing Metrics
| Column | Description |
|--------|-------------|
| `weakness_count` | Number of type weaknesses |
| `resistance_count` | Number of type resistances |
| `immunity_count` | Number of type immunities |
| `typing_defense_score` | Engineered defensive typing score |
| `typing_defense_class` | Defensive typing classification |

Typing_defense_score is derived from the defensive type matchup matrix (`against_*`, which is explained further down), and counts the number of type weaknesses, type immunities, and type resistances. The score is calculated as typing_defense_score = (df[resistance_count] * 0.5) + (df[immunity_count] * 1.5) - df[weakness_count]. Immunities are weighed heavier than resistance because they completely negate damage, whereas resistance reduces damage but still allows it to occur, thus resistance contributes less to the defense score.

Typing_defense_class is a categorical version of `typing_defense_score`. For the generation-relative datasets, the scores are divided into **quantiles across each generation**, which creates balanced groups representing relative defensive strength in each generation. For the overall dataset, the scores are divided into **quantiles across the entire Pokédex**, forming balanced groups representing relative defensive strength across generations.

The resulting classes describe **how strong a Pokémon's defensive typing is compared to others**.
| Class | Interpretation |
|-------|----------------|
| frail | Weak defensive typing |
| exposed | Below-average defensive typing |
| neutral | Average defensive typing |
| solid | Above-average defensive typing |
| iron | Strong defensive typing |

---

### Battle Archetypes
| Column | Description |
|--------|-------------|
| `battle_archetypes` | Battle role classification |
| `combat_profile` | Combined typing_defense_class with battle_archetypes |

The `battle_archetypes` column classifies Pokémon into combat roles based on three combat metrics:
- **offense**
- **bulk**
- **speed**

Each metric is divided into three tiers using generation quantiles:

- 33rd percentile --> low
- 33rd-67th percentile --> mid
- 67th percentile --> high

Each Pokémon in a generation is then assigned: low, mid, or high.

The final archetype is determined by combinations of the three tiers.

---

#### Offensive Roles
|Offense | Bulk | Speed | Archetype |
|--------|------|-------|-----------|
| high | high | high | juggernaut |
| high | mid | high | sweeper |
| high | high | mid | bulky_attacker |
| high | low | mid/high | glass_cannon |
| high | mid | mid | attacker |

--- 

#### Defensive Roles
|Offense | Bulk | Speed | Archetype |
|--------|------|-------|-----------|
| low | high | low | tank |
| low | high | mid/high | support |
| mid | high | high | bulky_speedster |
| mid | high | mid | bulky |

--- 

#### Low Speed Roles
|Offense | Bulk | Speed | Archetype |
|--------|------|-------|-----------|
| low | low | low | weak_slow |
| low | mid/high | low | slow_support |
| mid/high | mid/high | low | slow_attacker |

---

#### Fragile Build
|Offense | Bulk | Speed | Archetype |
|--------|------|-------|-----------|
| low | low | mid/high | fragile |

---

#### Balanced Build
|Offense | Bulk | Speed | Archetype |
|--------|------|-------|-----------|
| mid | mid | mid | balanced |

---

#### Default Case

If no specific condition is met, the Archtype is **midrange**.

---

#### Archetype Descriptions

| Archetype | Description |
|-----------|-------------|
| juggernaut | Extremely powerful in offense, bulk, and speed |
| sweeper | Fast offensive Pokémon designed to KO quickly |
| bulky_attacker | Strong offense combined with durability |
| glass_cannon | Very strong offense but fragile defenses |
| tank | Extremely durable but slow |
| support | Defensive Pokémon with limited offensive power |
| bulky_speedster | Durable Pokémon that still maintain speed |
| attacker | Offensive Pokémon without extreme specialization |
| slow_attacker | Strong Pokémon but low speed |
| slow_support | Defensive Pokémon with limited offensive presence |
| weak_slow | Low power and slow |
| fragile | Poor defenses and limited survivability |
| balanced | Even distribution of stats |
| midrange | Mixed stat profile without clear specialization |

---

#### Generation-Relative vs All Archetypes

Within Generation-Relative datasets, the archetype columns are calculated **within each generation**. This prevents early-gen Pokémon from being unfairly classified due to stat power creep in newer generations.

Within the Overall dataset, the archetype columns are calculated **across all Pokémon**. This allows direct comparisons between Pokémon from different generations.

---

#### Purpose of this Feature

The archetype system provides an interpretable way to classify Pokémon battle roles and it supports:
- machine learning classification tasks
- clustering analyses
- team composition analysis
- combat role comparisons

--- 

### Physical Attributes
| Column | Description |
|--------|-------------|
| `height_m` | Approximate height in meters |
| `weight_kg` | Approximate weight in kilograms |
| `mass_index` | Engineered size index |
| `mass_index_class` | Physical build classification |

In the PokéAPI, height and weight were done in rounded decimeters and hexagrams, so the engineered height and weight columns are only approximate to the true height and weight of each Pokémon.

Mass_index_class was created through quantiles. These classes can potentially shift between the Generation-Relative datasets and the Overall Dataset. The five classes a Pokémon can belong to are:
- very_light
- light
- average
- heavy
- very_heavy

---

### Gender
| Column | Description |
|--------|-------------|
| `is_genderless` | Genderless indicator (0 is no, 1 is yes) |
| `female_ratio` | Female proportion |

Both columns were created from PokéAPI's gender_rate column, which had -1 represent genderless Pokémon and 0-8 represent the female rate.

---

### Species Metadata
| Column | Description |
|--------|-------------|
| `pokemon_class` | Pokémon classification (normal, legendary, mythical) |
| `base_experience` | Base experience yield |
| `moves_count` | Number of moves available |
| `capture_rate` | Capture rate |
| `base_happiness` | Base friendship value |
| `hatch_counter` | Egg hatch cycles |
| `egg_groups` | Breeding groups |
| `growth_rate` | Experience growth rate |
| `shape` | Body shape classification |
| `color` | Pokédex color |
| `genus` | Pokédex genus classification in English |
| `flavor_text` | Pokédex flavor text in English |

---

### Evolution Data
| Column | Description |
|--------|-------------|
| `evolution_line` | Evolution chain string |
| `evolution_chain_length` | Number of species in chain |
| `evolution_stage` | Stage within chain |
| `is_final_evolution` | Final evolution indicator (0 is no, 1 is yes)

---

### Type Matchup Matrix

The dataset includes a full defensive type matchup matrix made up of the following columns:

- `against_normal`
- `against_fire`
- `against_water`
- `against_electric`
- `against_grass`
- `against_ice`
- `against_fighting`
- `against_poison`
- `against_ground`
- `against_flying`
- `against_psychic`
- `against_bug`
- `against_rock`
- `against_ghost`
- `against_dragon`
- `against_dark`
- `against_steel`
- `against_fairy`

These columns represent **damage multipliers received from each attacking types**.
| Value | Meaning |
|-------|---------|
| 0 | immunity |
| 0.5 or 0.25 | resistance |
| 1 | neutral |
| 2 or 4 | weakness

---

## Example Use Cases

This dataset can be used for:

- Pokémon clustering
- Battle role classification
- Type interaction analysis
- Generational balance studies
- Machine learning experiments 
- Data visualization