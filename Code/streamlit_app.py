"""
Streamlit UI for the Pokemon Team Builder

Run locally with:
    streamlit run streamlit_app.py OR py -m streamlit run "streamlit_app.py"

State model: each visitor's "current team" lives only in st.session_state (their own
private browser session). It is never written to a shared file. That's what makes
this safe to deploy for multiple simultaneous users.
"""

import pandas as pd
import streamlit as st

import pokemon_engine as engine

st.set_page_config(page_title="Pokedex // Team Builder", page_icon="🕹️", layout="wide")

PAGES = ["Generate a team", "Build from names", "Your team", "Switch a pokemon", "Edit a stat"]

# Real Pokemon type colors! I'm not inventing a new palette for this.
TYPE_COLORS = {
    "normal": "#A8A878", "fire": "#F08030", "water": "#6890F0", "electric": "#F8D030",
    "grass": "#78C850", "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0",
    "ground": "#E0C068", "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820",
    "rock": "#B8A038", "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848",
    "steel": "#B8B8D0", "fairy": "#EE99AC",
}

# Power-tier colors, reusing the same rank groupings the evaluator already uses
TIER_COLOR = {}
for color in engine.GOD_RANK:
    TIER_COLOR[color] = "#d92b3f"       # S-tier: Pokedex red
for color in engine.DEMIGOD_RANK:
    TIER_COLOR[color] = "#f2b705"       # amber
for color in engine.HERO_RANK:
    TIER_COLOR[color] = "#9bd6a3"       # screen green
for color in engine.MORTAL_RANK:
    TIER_COLOR[color] = "#7a89a3"       # steel gray-blue
for color in engine.PUNY_RANK:
    TIER_COLOR[color] = "#5c6167"       # dim

MAX_STAT_SCALE = 180  # rough visual ceiling for stat bars (most base stats sit 20-160)

# Theme CSS
def inject_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Space+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] { font-family: 'Space Mono', monospace; }

    /* App background: console shell with a faint scanline texture */
    [data-testid="stAppViewContainer"] {
        background:
            repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 3px),
            #14171c;
    }
    [data-testid="stHeader"] { background: transparent; }

    /* Sidebar: red-trimmed console panel  */
    section[data-testid="stSidebar"] {
        background: #1a1d23;
        border-right: 3px solid #d92b3f;
    }
    section[data-testid="stSidebar"] > div { padding-top: 0; }

    /* Headline*/
    .console-title {
        font-family: 'Press Start 2P', monospace;
        font-size: 1.4rem;
        color: #eef1f4;
        letter-spacing: 1px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .console-led { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
    .led-red { background: #d92b3f; box-shadow: 0 0 8px #d92b3f; }
    .led-green { background: #9bd6a3; box-shadow: 0 0 8px #9bd6a3; }
    .console-subtitle { color: #8b93a1; font-size: 0.85rem; margin-bottom: 1.2rem; }
    .console-disclaimer { color: #5c6167; font-size: 0.68rem; line-height: 1.3; margin: 2px 0 10px 0; }

    /* Radio nav styled as console buttons */
    div[data-testid="stRadio"] label {
        background: #22262e;
        border: 1px solid #3a4048;
        border-radius: 4px;
        padding: 8px 12px !important;
        margin-bottom: 6px;
        width: 100%;
        transition: all 0.15s ease;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: #d92b3f;
        border-color: #d92b3f;
        color: #14171c !important;
        font-weight: bold;
    }
    div[data-testid="stRadio"] label:has(input:checked) p { color: #14171c !important; }

    /* Buttons  */
    .stButton button {
        background: #d92b3f;
        color: #eef1f4;
        border: none;
        border-radius: 4px;
        font-family: 'Space Mono', monospace;
        font-weight: bold;
        letter-spacing: 0.5px;
        padding: 0.5rem 1rem;
    }
    .stButton button:hover { background: #b8222f; color: #eef1f4; }
    .stButton button:disabled { background: #3a4048; color: #6b7078; }

    /*Section header (LCD-style) */
    .screen-header {
        border: 1px solid #3a4048;
        border-left: 4px solid #9bd6a3;
        background: #1a1e15;
        color: #9bd6a3;
        font-family: 'Space Mono', monospace;
        padding: 10px 14px;
        margin-bottom: 1rem;
        border-radius: 2px;
    }

    /* Pokemon card */
    .poke-card {
        background: #1e222a;
        border: 1px solid #3a4048;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 14px;
    }
    .poke-card-name {
        font-weight: bold;
        font-size: 1.05rem;
        color: #eef1f4;
        text-transform: capitalize;
        margin-bottom: 6px;
    }
    .type-pill {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: bold;
        color: #14171c;
        padding: 2px 9px;
        border-radius: 10px;
        margin-right: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .arch-pill {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: bold;
        padding: 2px 9px;
        border-radius: 10px;
        margin-left: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid currentColor;
    }
    .class-pill {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 10px;
        margin-left: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .class-legendary { background: #7a5c14; color: #f2d98a; }
    .class-mythical { background: #4a2a5e; color: #dcb3f0; }
    .stat-row { display: flex; align-items: center; gap: 8px; margin-top: 5px; font-size: 0.72rem; color: #8b93a1; }
    .stat-label { width: 68px; flex-shrink: 0; text-transform: uppercase; }
    .stat-bar-bg { flex-grow: 1; background: #14171c; border-radius: 3px; height: 8px; overflow: hidden; border: 1px solid #3a4048; }
    .stat-bar-fill { height: 100%; background: #9bd6a3; }
    .stat-value { width: 28px; text-align: right; color: #eef1f4; }

    /* Empty slot placeholder card */
    .empty-card {
        border: 1px dashed #3a4048;
        border-radius: 8px;
        padding: 28px 16px;
        margin-bottom: 14px;
        text-align: center;
        color: #5c6167;
        font-size: 0.85rem;
    }
    .empty-card .icon { font-size: 1.6rem; display: block; margin-bottom: 6px; opacity: 0.6; }

    /* Sidebar team preview */
    .roster-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 0.82rem; }
    .tier-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
    .roster-name { text-transform: capitalize; color: #eef1f4; }
    </style>
    """, unsafe_allow_html=True)


def type_pill(t):
    if pd.isna(t):
        return ""
    color = TYPE_COLORS.get(str(t).lower(), "#8b93a1")
    return f'<span class="type-pill" style="background:{color}">{t}</span>'


def class_pill(pokemon_class):
    if pokemon_class not in ("legendary", "mythical"):
        return ""
    return f'<span class="class-pill class-{pokemon_class}">{pokemon_class}</span>'


def arch_pill(archetype):
    if not archetype:
        return ""
    color = TIER_COLOR.get(archetype, "#8b93a1")
    return f'<span class="arch-pill" style="color:{color}">{archetype}</span>'


def stat_bar(label, value):
    pct = max(4, min(100, round(100 * value / MAX_STAT_SCALE)))
    return (
        f'<div class="stat-row"><div class="stat-label">{label}</div>'
        f'<div class="stat-bar-bg"><div class="stat-bar-fill" style="width:{pct}%"></div></div>'
        f'<div class="stat-value">{value}</div></div>'
    )


def empty_card_html():
    return (
        '<div class="empty-card"><span class="icon">⚪</span>'
        f'{engine.EMPTY_SLOT}<br><span style="font-size:0.72rem">'
        'No pokemon matched this type + class combo</span></div>'
    )


def poke_card_html(row):
    if row["name"] == engine.EMPTY_SLOT:
        return empty_card_html()
    stats = "".join([
        stat_bar("HP", row["hp"]),
        stat_bar("ATK", row["attack"]),
        stat_bar("DEF", row["defense"]),
        stat_bar("SP.ATK", row["sp_attack"]),
        stat_bar("SP.DEF", row["sp_defense"]),
        stat_bar("SPD", row["speed"]),
    ])
    types = type_pill(row["type1"]) + type_pill(row["type2"])
    return (
        f'<div class="poke-card">'
        f'<div class="poke-card-name">{row["name"]} {arch_pill(row["battle_archetypes"])}{class_pill(row.get("pokemon_class"))}</div>'
        f'<div>{types}</div>{stats}</div>'
    )


def render_team_cards(team_df, columns=2):
    cols = st.columns(columns)
    for i, (_, row) in enumerate(team_df.iterrows()):
        with cols[i % columns]:
            st.markdown(poke_card_html(row), unsafe_allow_html=True)


# Cached, shared, read-only data
@st.cache_data
def get_master():
    return engine.load_master()

@st.cache_data
def get_quantiles():
    return engine.compute_quantiles(master_df=get_master())

@st.cache_data
def get_all_names():
    return sorted(get_master()["name"].unique().tolist())

def get_team_df():
    return st.session_state.get("team_df")

def set_team_df(df):
    st.session_state["team_df"] = df

def refresh_archetype(pokemon_name):
    """Recalculates and writes back the archetype for one pokemon in the session team."""
    team_df = get_team_df()
    new_type = engine.calc_arch(pokemon_name, team_df, quantiles=get_quantiles())
    team_df.loc[team_df["name"] == pokemon_name, "battle_archetypes"] = new_type
    set_team_df(team_df)

# Layout
inject_theme()

st.sidebar.markdown(
    '<div class="console-title"><span class="console-led led-red"></span>'
    '<span class="console-led led-green"></span>POKEDEX</div>'
    '<div class="console-disclaimer">This is a fan made product, I have no association '
    'with Nintendo whatsoever. I do not reflect the opinions of the brand or company.</div>'
    '<div class="console-subtitle">// Team Builder Unit</div>',
    unsafe_allow_html=True,
)
page = st.sidebar.radio("Go to", PAGES, label_visibility="collapsed")

def render_sidebar_roster():
    """Called at the very end of the script (see bottom of file) so it reflects any
    team changes made by button clicks earlier in this same run -- rendering it here
    at the top would show last run's (stale) team state instead."""
    team_df = get_team_df()
    if team_df is not None:
        st.sidebar.markdown("---")
        st.sidebar.caption("CURRENT ROSTER")
        rows_html = ""
        for _, row in team_df.iterrows():
            dot = TIER_COLOR.get(row["battle_archetypes"], "#8b93a1")
            rows_html += (
                f'<div class="roster-row"><span class="tier-dot" style="background:{dot}"></span>'
                f'<span class="roster-name">{row["name"]}</span></div>'
            )
        st.sidebar.markdown(rows_html, unsafe_allow_html=True)
        st.sidebar.download_button(
            "⬇ Download team as CSV",
            team_df.to_csv(index=False).encode("utf-8"),
            file_name="pokemon_team.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.sidebar.markdown("---")
        st.sidebar.caption("No team yet — generate or build one to get started.")


# Page: Generate a team (by generation + type)
if page == "Generate a team":
    st.markdown('<div class="console-title"><span class="console-led led-red"></span>GENERATE A TEAM</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-header">Pick generations and types, and we\'ll assemble a random 6-pokemon team that fits.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        gens = st.multiselect("Generations", options=list(range(1, 10)), default=[1])
    with col2:
        types = st.multiselect("Types", options=engine.ALL_TYPES, default=["fire", "water"])

    st.caption("INCLUDE CLASSES")
    tcol1, tcol2, tcol3 = st.columns(3)
    with tcol1:
        allow_normal = st.toggle("Normal", value=True)
    with tcol2:
        allow_legendary = st.toggle("Legendary", value=True)
    with tcol3:
        allow_mythical = st.toggle("Mythical", value=True)

    allowed_classes = {c for c, on in [("normal", allow_normal), ("legendary", allow_legendary), ("mythical", allow_mythical)] if on}
    if not allowed_classes:
        st.warning("Turn at least one class on — otherwise no pokemon can ever qualify.")

    st.caption("INCLUDE EVOLUTION STAGES")
    ecol1, ecol2, ecol3 = st.columns(3)
    with ecol1:
        allow_starter = st.toggle("Starter", value=True, help="The base/first form of a multi-stage evolution line.")
    with ecol2:
        allow_middle = st.toggle("Middle", value=True, help="An in-between evolution stage (only applies to 3+ stage evolution lines).")
    with ecol3:
        allow_final = st.toggle("Final", value=True, help="The last form of an evolution line, or a pokemon that doesn't evolve at all (e.g. Mewtwo, Tauros).")

    allowed_evolution_stages = {s for s, on in [("starter", allow_starter), ("middle", allow_middle), ("final", allow_final)] if on}
    if not allowed_evolution_stages:
        st.warning("Turn at least one evolution stage on — otherwise no pokemon can ever qualify.")

    if st.button("Generate team", type="primary", disabled=not gens or not types or not allowed_classes or not allowed_evolution_stages):
        team_source = engine.join_gens(gens)
        full_team = engine.build_team(
            team_source, types,
            allowed_classes=allowed_classes,
            allowed_evolution_stages=allowed_evolution_stages,
        )
        pokemon_list = list(full_team.values())

        if len(pokemon_list) != 6:
            st.warning(
                f"Only found {len(pokemon_list)} matching pokemon across generation(s) "
                f"{gens}, type(s) {types}, class(es) {sorted(allowed_classes)}, and "
                f"evolution stage(s) {sorted(allowed_evolution_stages)} — need at least "
                "6. Try adding more generations, types, classes, or evolution stages."
            )
        else:
            set_team_df(engine.team_stats(pokemon_list, master_df=get_master()))
            n_empty = sum(1 for n in pokemon_list if n == engine.EMPTY_SLOT)
            if n_empty:
                st.warning(
                    f"Filled the team, but {n_empty} slot(s) had no pokemon matching your "
                    f"type, class, and evolution stage filters and became {engine.EMPTY_SLOT}. "
                    "Try widening your type, class, or evolution stage selection, or swap "
                    "them out on the Switch page."
                )
            else:
                st.success("Your team is ready!")
            render_team_cards(get_team_df())

# Page: Build from names
elif page == "Build from names":
    st.markdown('<div class="console-title"><span class="console-led led-red"></span>BUILD FROM NAMES</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-header">Pick exactly 6 pokemon by name.</div>', unsafe_allow_html=True)

    all_names = get_all_names()
    chosen = st.multiselect("Pokemon (pick 6)", options=all_names)

    n_chosen = len(chosen)
    if n_chosen == 6:
        st.caption(f"✅ {n_chosen}/6 selected")
    elif n_chosen > 6:
        st.error(f"Too many selected ({n_chosen}/6) — remove {n_chosen - 6} pokemon.")
    else:
        st.caption(f"{n_chosen}/6 selected — pick {6 - n_chosen} more.")

    if st.button("Build team", type="primary", disabled=n_chosen != 6):
        missing = engine.validate_names_exist(chosen, master_df=get_master())
        if missing:
            st.error(f"Not found in the database: {', '.join(missing)}")
        else:
            set_team_df(engine.team_stats(chosen, master_df=get_master()))
            st.success("Your team is ready!")
            render_team_cards(get_team_df())

# Page: Your team (view + evaluate)
elif page == "Your team":
    st.markdown('<div class="console-title"><span class="console-led led-green"></span>YOUR TEAM</div>', unsafe_allow_html=True)
    team_df = get_team_df()
    if team_df is None:
        st.info("No team yet. Head to **Generate a team** or **Build from names** first.")
    else:
        render_team_cards(team_df)
        n_empty = int((team_df["name"] == engine.EMPTY_SLOT).sum())
        if n_empty:
            st.info(f"Fill the {n_empty} {engine.EMPTY_SLOT} slot(s) on the Switch page before evaluating your team.")
        elif st.button("Evaluate team", type="primary"):
            result = engine.team_evaluator(team_df["name"].tolist(), master_df=get_master())
            st.markdown(f'<div class="screen-header">{result}</div>', unsafe_allow_html=True)

# Page: Switch a pokemon
elif page == "Switch a pokemon":
    st.markdown('<div class="console-title"><span class="console-led led-red"></span>SWITCH A POKEMON</div>', unsafe_allow_html=True)
    team_df = get_team_df()
    if team_df is None:
        st.info("No team yet. Head to **Generate a team** or **Build from names** first.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            outgoing = st.selectbox("Switch out", options=team_df["name"].tolist())
        with col2:
            incoming = st.selectbox("Switch in", options=[n for n in get_all_names() if n not in team_df["name"].tolist()])

        if st.button("Switch", type="primary"):
            new_list = team_df["name"].tolist()
            new_list.remove(outgoing)  # removes only the first/selected occurrence --
            # important now that Empty Pokeball can appear more than once in a team;
            # filtering with `!= outgoing` would have removed every empty slot at once.
            new_list.append(incoming)
            set_team_df(engine.team_stats(new_list, master_df=get_master()))
            st.success(f"Swapped {outgoing} for {incoming}!")
            render_team_cards(get_team_df())

# Page: Edit a stat
elif page == "Edit a stat":
    st.markdown('<div class="console-title"><span class="console-led led-red"></span>EDIT A STAT</div>', unsafe_allow_html=True)
    team_df = get_team_df()
    editable_names = [] if team_df is None else [n for n in team_df["name"].tolist() if n != engine.EMPTY_SLOT]
    if team_df is None:
        st.info("No team yet. Head to **Generate a team** or **Build from names** first.")
    elif not editable_names:
        st.info(f"Your whole team is {engine.EMPTY_SLOT} slots — nothing to edit yet. Try Switch a pokemon to fill them in.")
    else:
        editable_stats = ["attack", "sp_attack", "defense", "sp_defense", "hp", "speed"]
        col1, col2, col3 = st.columns(3)
        with col1:
            pokemon = st.selectbox("Pokemon", options=editable_names)
        with col2:
            stat = st.selectbox("Stat", options=editable_stats)
        with col3:
            current_val = int(team_df.loc[team_df["name"] == pokemon, stat].iloc[0])
            value = st.number_input("New value", min_value=1, max_value=999, value=current_val, step=1)

        if st.button("Apply change", type="primary"):
            team_df.loc[team_df["name"] == pokemon, stat] = value
            set_team_df(team_df)
            refresh_archetype(pokemon)
            st.success(f"Updated {pokemon}'s {stat} to {value} — archetype recalculated.")
            render_team_cards(get_team_df())

render_sidebar_roster()