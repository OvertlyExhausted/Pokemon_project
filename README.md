# Pokemon Team Builder

# DISCLAIMER : This program is created as a **fan work** of Nintendo's Pokemon games. I am not affilliated with the IP or company, nor am I trying to claim their work as my own. Please support the official releases of the games/tv shows/movies

## Overview 
This project works off of **Michaela Gruber's** work with the **PokéAPI**, collecting and cleaning data on the pokemon of generations 1-9 and associated statistics for the use in machine learning and data analysis. Useing **Streamlit** as a host, this project allows for users to randomly generate pokemon teams within specific parameters such as **generation, type, and class**, then listing options to evaluate the strength of the team, change out pokemon, or edit individual stats.

This Streamlit app allows you to:
- generate team of 6 based on class, type, and generation
- generate team based on pokemon names
- alter team makeup
- alter individual pokemon stats
- download results as a csv 

## Project Contents
- Original code in pyspark (Databricks) format
- Altered pure Python code
- pokemon_engine code (loads in Streamlit app)
- streamlit_app.py for designing UI and editing css

## Base Evaluation Calculations
To evaluate a pokemon team, battle archetypes (calculated by Michaela Gruber in her database) are sorted into categories , **GOD_RANK**, **DEMIGOD_RANK**, **HERO_RANK**, **MORTAL_RANK**, and **PUNY_RANK** which are then compared to rank in a variety of classifications. If a team is mostly one rank, but with a clear outlier, the system will label the team as Uneven, whereas if a team has a mix of two or more classifications, the system will label it as Balanced, whereas a team with a mix of three or more rankings will be a Mixed Bag etc. The program also highlights the strongest and weakest within a team. If multiple pokemon of the same battle archetype are found, the first one will be labeled as the strongest/weakest of the team. 

## Generative Methodology

pokemon_engine.py is an almost exact clone of the altered python code labeled main(python).py. The function of this code is to work identically as main(python).py but for use in the Streamlit app, so lacks the user input calls and does not write the generated team to a new csv file in the same way, as in order to keep the app running smoothly for use by multiple users. 

The style of team generation remains the same between both files. A user chooses the generations and types (up to 6, one per pokemon) and the program combines the select generations to pull from. The resulting database is then run through a random number generator to grab six random pokemon with the aligning types. The resulting team can then be edited by hand for stats or the pokemon itself and evaluated. 

## Streamlit Methodology

The streamlit_app.py functions as the UI layer of the code, handling navigation, layouts, styling, and rendering the pokemon_engine code, which in turn handles the actual team building and evaluation. 

### Navigation

On the left sidebar of this application is the navigation bottons, styled to look like old-school gaming console selection options:
- Generate a team
- Build from names
- Your team
- Switch a pokemon
- Edit a stat

### State Model

Each visitor's team is kept to team_df and never writen to a shared file or database. That way the app is safe for multiple users at once, living on the tab alone, so that no one's team overwrites another. Helper functions get_team_df and set_team_df wrap session states access so the app doesn't touch st_session_state directly. 

### Sidebar roster and Export
A live-updating roster summary renders in the sidebar on every page, listing each teammate with a tier-colored dot, plus a download button that exports the current team as a CSV. This is rendered as the very last step of each script run (after any button-triggered team changes), so it always reflects the latest state instead of the previous run's.



