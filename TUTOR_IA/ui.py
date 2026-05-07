from __future__ import annotations

import secrets

import streamlit as st

import auth
import chat


def init_session_state() -> None:
    st.session_state.setdefault("auth_view", "login")
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("active_session_id", None)
    st.session_state.setdefault("oauth_state", None)


def set_active_user(user: dict) -> None:
    st.session_state.user = user
    selected = chat.ensure_user_session(user["id"])
    st.session_state.active_session_id = selected["id"]


def clear_active_user() -> None:
    st.session_state.user = None
    st.session_state.active_session_id = None
    st.session_state.oauth_state = None


def render_auth_screen() -> None:
    st.title("Asistente de Programacion")
    st.caption("Inicia sesion para guardar tu historial y cargar tus conversaciones tecnicas.")

    _handle_google_callback()

    login_tab, register_tab = st.tabs(["Login", "Registro"])
    with login_tab:
        _render_login_form()
    with register_tab:
        _render_register_form()


def render_sidebar() -> None:
    user = st.session_state.user
    if not user:
        return

    with st.sidebar:
        st.subheader("Usuario activo")
        if user.get("profile_picture"):
            st.image(user["profile_picture"], width=64)
        st.write(user.get("name", "Usuario"))
        st.caption(user.get("email", ""))

        if st.button("Nuevo chat", use_container_width=True):
            new_session = chat.create_chat_session(user["id"])
            st.session_state.active_session_id = new_session["id"]
            st.rerun()

        st.divider()
        st.subheader("Conversaciones")
        sessions = chat.list_chat_sessions(user["id"])
        for session in sessions:
            label = session["title"] or "Nuevo chat"
            if session.get("message_count", 0):
                label = f"{label} ({session['message_count']})"
            if st.button(
                label,
                key=f"session-{session['id']}",
                use_container_width=True,
                disabled=session["id"] == st.session_state.active_session_id,
            ):
                st.session_state.active_session_id = session["id"]
                st.rerun()

        st.divider()
        if st.button("Cerrar sesion", use_container_width=True):
            clear_active_user()
            st.rerun()


def render_chat_screen() -> None:
    user = st.session_state.user
    if not user:
        render_auth_screen()
        return

    if st.session_state.active_session_id is None:
        selected = chat.ensure_user_session(user["id"])
        st.session_state.active_session_id = selected["id"]

    render_sidebar()
    session = chat.get_chat_session(user["id"], st.session_state.active_session_id)
    if session is None:
        session = chat.ensure_user_session(user["id"])
        st.session_state.active_session_id = session["id"]

    st.title("Asistente de Programacion")
    st.caption(session.get("title") or "Nuevo chat")

    messages = chat.list_messages(st.session_state.active_session_id, user["id"])
    for message in messages:
        with st.chat_message("assistant" if message["role"] == "assistant" else "user"):
            st.markdown(message["content"])

    prompt = st.chat_input("Pregunta algo sobre codigo, bugs, arquitectura o el proyecto")
    if not prompt:
        return

    chat.update_session_title_from_message(st.session_state.active_session_id, user["id"], prompt)
    chat.add_message(st.session_state.active_session_id, user["id"], "user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando con tu historial reciente de programacion..."):
            try:
                result = chat.call_assistant(prompt, st.session_state.active_session_id, user["id"])
                answer = result.get("answer") or result.get("error") or "No pude generar una respuesta."
            except Exception as exc:
                answer = f"No pude consultar el asistente: {exc}"
            st.markdown(answer)

    chat.add_message(st.session_state.active_session_id, user["id"], "assistant", answer)
    st.rerun()


def _render_login_form() -> None:
    with st.form("login-form"):
        email = st.text_input("Correo")
        password = st.text_input("Contrasena", type="password")
        submitted = st.form_submit_button("Iniciar sesion", use_container_width=True)
    if submitted:
        ok, message, user = auth.authenticate_user(email, password)
        if ok and user:
            set_active_user(user)
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    _render_google_button()


def _render_register_form() -> None:
    with st.form("register-form"):
        name = st.text_input("Nombre")
        email = st.text_input("Correo", key="register-email")
        password = st.text_input("Contrasena", type="password", key="register-password")
        submitted = st.form_submit_button("Crear cuenta", use_container_width=True)
    if submitted:
        ok, message, user = auth.create_user(name, email, password)
        if ok and user:
            set_active_user(user)
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def _render_google_button() -> None:
    if not auth.google_oauth_configured():
        st.info("Configura GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET y GOOGLE_REDIRECT_URI para activar Google OAuth.")
        return
    state = st.session_state.oauth_state or secrets.token_urlsafe(24)
    st.session_state.oauth_state = state
    st.link_button("Continuar con Google", auth.build_google_auth_url(state), use_container_width=True)


def _handle_google_callback() -> None:
    params = st.query_params
    code = params.get("code")
    state = params.get("state")
    if not code:
        return
    if not state or state != st.session_state.oauth_state:
        st.error("La validacion OAuth fallo. Intenta iniciar sesion con Google otra vez.")
        st.query_params.clear()
        return

    ok, message, user = auth.exchange_google_code(code)
    st.query_params.clear()
    if ok and user:
        set_active_user(user)
        st.success(message)
        st.rerun()
    else:
        st.error(message)
