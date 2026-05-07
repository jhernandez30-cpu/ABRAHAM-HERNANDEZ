from __future__ import annotations

import streamlit as st

from utils import load_environment


load_environment()

from database import init_db
from ui import init_session_state, render_auth_screen, render_chat_screen


def main() -> None:
    init_db()
    st.set_page_config(page_title="Asistente de Programacion", page_icon="T", layout="wide")
    init_session_state()
    if st.session_state.user:
        render_chat_screen()
    else:
        render_auth_screen()


if __name__ == "__main__":
    main()
