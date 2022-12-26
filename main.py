import streamlit as st
import pandas as pd
from ast import literal_eval
from datetime import datetime, timedelta

TRANSLATIONS = {
    "en": {
        "lang_opt": "Language Options",
        "lang_disp_name": "English",
        "title": "Bottle Post",
        "subtitle": "Bottle post for everyone",
        "post": "Post a bottle",
        "fetch": "Fetch a bottle",
        "say_something": "Say something to random people",
        "send": "Seal and send!",
        "not_found": "Oops! No bottle found. Maybe post a new one?",
        "try_later": "Let's try again later",
        "someone_wrote": "Someone wrote:",
        "leave_comment": "Leave a comment",
        "leave_blank": "Leave blank if you don't want to",
        "upvote": "Is this bottle good?",
        "throw_back": "Throw it back",
        "refresh": "Try another one",
    },
    "zh": {
        "lang_opt": "语言选项",
        "lang_disp_name": "中文",
        "title": "漂流瓶",
        "subtitle": "每个人都能用的漂流瓶",
        "post": "投递漂流瓶",
        "fetch": "捞一个漂流瓶",
        "say_something": "向陌生人说点什么",
        "send": "封口，起航!",
        "not_found": "哎呀！没有找到漂流瓶。要不投一个新的？",
        "try_later": "稍后再试试",
        "someone_wrote": "有人写道：",
        "leave_comment": "留下评论",
        "leave_blank": "不想留的话就留空",
        "upvote": "这个漂流瓶如何？",
        "throw_back": "扔回海里",
        "refresh": "换一个",
    },
}
DATA_FILE = "data/bottles.csv"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
VOTE_DICT = {True: "👍", False: "👎"}

st.set_page_config(
    page_title="漂流瓶 Bottle Post", page_icon="📜", initial_sidebar_state="collapsed"
)

# Language options

if "lang" not in st.session_state:
    st.session_state["lang"] = "zh"

# Header

st.title("📜 " + TRANSLATIONS[st.session_state["lang"]]["title"])
st.write("##### " + TRANSLATIONS[st.session_state["lang"]]["subtitle"])

with st.expander("🔧 " + TRANSLATIONS[st.session_state["lang"]]["lang_opt"]):
    st.radio(
        "🔧 " + TRANSLATIONS[st.session_state["lang"]]["lang_opt"],
        TRANSLATIONS.keys(),
        index=list(TRANSLATIONS.keys()).index(st.session_state["lang"]),
        format_func=lambda x: TRANSLATIONS[x]["lang_disp_name"],
        key="lang_opt",
        on_change=lambda: st.session_state.__setattr__(
            "lang", st.session_state["lang_opt"]
        ),
        label_visibility="collapsed",
        horizontal=True,
    )

# Load data
def load_data_no_cache():
    df = pd.read_csv(DATA_FILE)
    # Drop the dead entries
    df = df[df["ddl"] > datetime.now().strftime(TIME_FORMAT)]
    df["comments"] = df["comments"].apply(literal_eval)
    return df


@st.cache(ttl=60)
def load_data():
    return load_data_no_cache()


def add_post(text: str):
    old_df = load_data_no_cache()
    new_df = pd.DataFrame(
        {
            "text": [text],
            "ddl": [
                (
                    datetime.now()
                    + timedelta(days=st.secrets["options"]["default_ttl"])
                ).strftime(TIME_FORMAT)
            ],
            "up": [0],
            "down": [0],
            "comments": [[]],
        },
    )
    df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset="text")
    df.sort_values(by="ddl", ascending=True, inplace=True)
    # Drop the oldest data if there are more than 10000 rows
    if len(df) > st.secrets["options"]["size_limit"]:
        df = df.iloc[-st.secrets["options"]["size_limit"] :]
    df.to_csv(DATA_FILE, index=False)


def vote_post(text: str, comment: str, up: bool):
    df = load_data_no_cache()
    if not len(df[df["text"] == text]):
        # no match
        return
    if up:
        df.loc[df["text"] == text, "up"] += 1
        # Enlarge the time to live
        df.loc[df["text"] == text, "ddl"] = (
            datetime.now() + timedelta(days=st.secrets["options"]["default_ttl"])
        ).strftime(TIME_FORMAT)
    else:
        df.loc[df["text"] == text, "down"] += 1
    if comment:
        df.loc[df["text"] == text, "comments"] += [[comment]]
    # Only calculate scores when votes change
    filter_post(df).to_csv(DATA_FILE, index=False)


def filter_post(df: pd.DataFrame) -> pd.DataFrame:
    if not len(df):
        return df
    scores = (df["up"] + 1) / (df["up"] + df["down"] + 2)
    return df.loc[scores > st.secrets["options"]["min_score"]]


def sample_post(ori: pd.DataFrame) -> tuple[str, bool]:
    df = ori.copy()
    if not len(df):
        return TRANSLATIONS[st.session_state["lang"]]["not_found"], False
    scores = (df["up"] + 1) / (df["up"] + df["down"] + 2)
    text = df.sample(1, weights=scores)["text"].values[0]
    try:
        assert text is not None
    except AssertionError:
        return TRANSLATIONS[st.session_state["lang"]]["not_found"], False
    return text, True


post_page, fetch_page = st.tabs(
    [
        "📝 " + TRANSLATIONS[st.session_state["lang"]]["post"],
        "🔍 " + TRANSLATIONS[st.session_state["lang"]]["fetch"],
    ]
)

with post_page:
    with st.form("post", clear_on_submit=True):
        text = st.text_area(
            TRANSLATIONS[st.session_state["lang"]]["say_something"],
            max_chars=st.secrets["options"]["max_chars"],
            placeholder=TRANSLATIONS[st.session_state["lang"]]["say_something"],
            label_visibility="collapsed",
        )
        if (
            st.form_submit_button(TRANSLATIONS[st.session_state["lang"]]["send"])
            and text
        ):
            add_post(text)

with fetch_page:
    with st.form("vote", clear_on_submit=True):
        df = load_data()
        text, found = sample_post(df)
        if not found:
            st.write(TRANSLATIONS[st.session_state["lang"]]["not_found"])
            st.form_submit_button(TRANSLATIONS[st.session_state["lang"]]["try_later"])
            st.stop()
        else:
            st.write("##### " + TRANSLATIONS[st.session_state["lang"]]["someone_wrote"])
            st.write("---")
            st.write(text)
            st.write("---")
            comment = st.text_area(
                TRANSLATIONS[st.session_state["lang"]]["leave_comment"],
                max_chars=st.secrets["options"]["max_comment_chars"],
                placeholder=TRANSLATIONS[st.session_state["lang"]]["leave_blank"],
            )
            is_up = st.radio(
                TRANSLATIONS[st.session_state["lang"]]["upvote"],
                [True, False],
                horizontal=True,
                format_func=lambda up: VOTE_DICT[up],
            )
            assert is_up in [True, False]
            if st.form_submit_button(
                TRANSLATIONS[st.session_state["lang"]]["throw_back"]
            ):
                vote_post(text, comment, is_up)
    st.button(TRANSLATIONS[st.session_state["lang"]]["refresh"])

st.dataframe(load_data_no_cache(), use_container_width=True)
