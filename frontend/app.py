import os, io, time, uuid
import pandas as pd
import streamlit as st
import requests
import difflib
import re


BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000/api")

st.set_page_config(page_title="Mimic – Agentic UI", layout="wide")

# --------------------------- HELPERS --------------------------- #
def api_get(path, params=None):
    r = requests.get(f"{BACKEND_URL}{path}", params=params)
    r.raise_for_status()
    return r.json()

def api_post(path, data=None):
    r = requests.post(f"{BACKEND_URL}{path}", json=data or {})
    r.raise_for_status()
    return r.json()

def log_action_via_agent(text: str, user="system"):
    """Send logs to Django backend via /agent/ endpoint"""
    try:
        api_post("/agent/", {"input": text, "user": user})
    except Exception as e:
        st.warning(f"Could not log action: {e}")

def create_ticket(user, action, status="Open"):
    """Creates ticket locally and logs SYSTEM event in backend"""
    ticket_id = str(uuid.uuid4())[:8]
    ticket_file = "tickets.xlsx"
    new_ticket = {
        "TicketID": ticket_id,
        "User": user["username"],
        "Role": user["role"],
        "Action": action,
        "Status": status,
    }
    if os.path.exists(ticket_file):
        df = pd.read_excel(ticket_file)
        df = pd.concat([df, pd.DataFrame([new_ticket])], ignore_index=True)
    else:
        df = pd.DataFrame([new_ticket])
    df.to_excel(ticket_file, index=False)

    # Log SYSTEM event
    log_action_via_agent(f"SYSTEM: Ticket {ticket_id} created for {action}", user["username"])
    return ticket_id

# --------------------------- LOGIN --------------------------- #
def login_box():
    with st.sidebar:
        st.header("🔐 Login")
        u = st.text_input("Username", value="alice")
        p = st.text_input("Password", value="pass", type="password")
        if st.button("Sign In", use_container_width=True):
            if u=="admin" and p=="admin":
                st.session_state.user={"username":"admin","role":"admin"}
            elif u=="bob" and p=="pass":
                st.session_state.user={"username":"bob","role":"manager"}
            elif u=="alice" and p=="pass":
                st.session_state.user={"username":"alice","role":"user"}
            else:
                st.error("Invalid credentials")
                return
            st.rerun()

if "user" not in st.session_state:
    login_box(); st.stop()

user = st.session_state.user
st.sidebar.success(f"👤 {user['username']} ({user['role']})")
if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()

st.title("🤖 Mimic – Agentic UI")
st.caption("Role-based downloads, chatbot assistant, file access, and tickets")

# --------------------------- APP LIST --------------------------- #
AVAILABLE_APPS = {
    "MS Word": ["2016", "2019", "2021"],
    "MS Excel": ["2016", "2019", "2021"],
    "Zoom": ["5.0", "5.1", "latest"],
    "Slack": ["4.20", "4.21", "latest"],
}
ROLE_APPS = {
    "user": ["Zoom"],
    "manager": ["Zoom", "MS Excel"],
    "admin": list(AVAILABLE_APPS.keys()),
}

# --------------------------- FILES --------------------------- #
FILES_DB = [
    {"filename":"Employee_Handbook.pdf","category":"general","is_public":1},
    {"filename":"VPN_Guide.pdf","category":"general","is_public":1},
    {"filename":"Finance_Q3.xlsx","category":"finance","is_public":0},
    {"filename":"Prod_DB_Creds.txt","category":"sensitive","is_public":0},
]
FILES_PERMISSIONS = {
    "user": ["general"],
    "manager": ["general", "finance"],
    "admin": ["general", "finance", "sensitive"],
}

# --------------------------- TABS --------------------------- #
tab_chat, tab_files, tab_logs, tab_tickets = st.tabs(
    ["💬 Chat / Install","📁 Files","📑 Logs","🎫 Tickets"]
)

# --------------------------- CHAT TAB --------------------------- #
with tab_chat:
    st.subheader("💬 Chat with Assistant")

    # --- free text input ---
    typed_query = st.text_input("Type app name (optionally with version)", placeholder="e.g., Zoom OR MS Word 2019")

    app_from_text, ver_from_text = None, None
    if typed_query.strip():
        m = re.match(r".*?(?P<app>[A-Za-z][\w\s]*)\s*(?P<version>[\w\.]+)?", typed_query, re.I)
        if m:
            app_from_text = m.group("app").strip()
            ver_from_text = (m.group("version") or "").strip()

    all_apps = list(AVAILABLE_APPS.keys())

    # fuzzy match app
    detected_app = None
    if app_from_text:
        for app in all_apps:
            if app_from_text.lower() in app.lower():
                detected_app = app
                break
        if not detected_app:
            close = difflib.get_close_matches(app_from_text, all_apps, n=1, cutoff=0.5)
            if close:
                detected_app = close[0]

    # --- dropdown for app ---
    selected_app = st.selectbox(
        "Choose an app",
        [""] + all_apps,
        index=(all_apps.index(detected_app) + 1 if detected_app else 0),
        key="app_select"
    )

    # --- dropdown for version ---
    selected_ver = None
    if selected_app:
        versions = AVAILABLE_APPS[selected_app]
        default_idx = 0
        if ver_from_text:
            if ver_from_text in versions:
                default_idx = versions.index(ver_from_text)
            else:
                close_ver = difflib.get_close_matches(ver_from_text, versions, n=1, cutoff=0.3)
                if close_ver:
                    default_idx = versions.index(close_ver[0])

        selected_ver = st.selectbox(
            "Choose version",
            versions,
            index=default_idx,
            key="ver_select"
        )

    # --- extra generic chat box ---
    q = st.text_area("Or type your message", placeholder="e.g., Having issues installing Zoom")

    # --- action button ---
    if st.button("Send to Assistant"):
        if selected_app and selected_ver:
            action = f"install {selected_app} {selected_ver}"
            ticket_id = create_ticket(user, action)
            with st.spinner(f"🚀 Deploying {selected_app} {selected_ver}..."):
                progress = st.progress(0)
                for i in range(1, 101, 10):
                    time.sleep(0.15)
                    progress.progress(i)
            st.success(f"✅ Deployment complete! Ticket {ticket_id}")
            log_action_via_agent(action, user["username"])
            st.download_button(
                "⬇️ Download Package",
                data=f"Dummy installer for {selected_app} {selected_ver}".encode(),
                file_name=f"{selected_app}-{selected_ver}.zip",
                mime="application/zip"
            )
        elif q.strip():
            try:
                res = api_post("/agent/", {"input": q, "user": user["username"]})
                if "output" in res: st.info(res["output"])
                elif "message" in res: st.success(res["message"])
                else: st.warning("Unexpected backend response.")
            except Exception as e:
                st.error(f"Backend error: {e}")
        else:
            st.warning("Select an app/version or type a query.")

# --------------------------- FILES TAB --------------------------- #
with tab_files:
    st.subheader("📁 Files (role-based access)")
    allowed_categories = FILES_PERMISSIONS.get(user["role"], [])
    visible = [f for f in FILES_DB if f["category"] in allowed_categories]

    search = st.text_input("🔎 Search files")
    if search.strip():
        visible = [f for f in visible if search.lower() in f["filename"].lower()]

    if not visible:
        st.info("No files available.")
    else:
        st.dataframe(pd.DataFrame(visible), use_container_width=True)
        for f in visible:
            st.download_button(
                f"📄 Download {f['filename']}",
                data=f"Dummy data for {f['filename']}".encode(),
                file_name=f['filename'],
                key=f"dl_{f['filename']}"
            )

        # Export visible files
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="xlsxwriter") as xw:
            pd.DataFrame(visible).to_excel(xw, index=False)
        out.seek(0)
        st.download_button(
            "⬇️ Export visible files",
            data=out,
            file_name="files.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --------------------------- LOGS TAB --------------------------- #
with tab_logs:
    try:
        logs = api_get("/logs/")
    except Exception as e:
        st.error(f"Error fetching logs: {e}")
        logs = []

    df = pd.DataFrame(logs or [])

    # Users only see their own logs
    if user["role"] == "user" and not df.empty and "user" in df.columns:
        df = df[df["user"] == user["username"]]

    if not df.empty:
        st.dataframe(df, use_container_width=True, height=360)

        # Export logs
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="xlsxwriter") as xw:
            df.to_excel(xw, index=False)
        out.seek(0)
        st.download_button(
            "⬇️ Export logs",
            data=out,
            file_name="logs.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No logs available.")

# --------------------------- TICKETS TAB --------------------------- #
with tab_tickets:
    st.subheader("🎫 Ticket Tracking")
    ticket_file = "tickets.xlsx"

    if os.path.exists(ticket_file):
        df_tickets = pd.read_excel(ticket_file)

        # Users see only their own tickets
        if user["role"] == "user":
            df_tickets = df_tickets[df_tickets["User"] == user["username"]]

        # 🔍 Status filter
        status_options = ["All", "Open", "In Progress", "Closed"]
        chosen_status = st.selectbox("Filter by Status", status_options)
        if chosen_status != "All":
            df_tickets = df_tickets[df_tickets["Status"] == chosen_status]

        st.dataframe(df_tickets, use_container_width=True)

        # ✏️ Managers/Admins can update ticket status
        if user["role"] in ["manager", "admin"] and not df_tickets.empty:
            st.markdown("### ✏️ Update Ticket Status")
            ticket_ids = df_tickets["TicketID"].tolist()
            chosen_id = st.selectbox("Select Ticket", ticket_ids)
            new_status = st.selectbox("New Status", ["Open", "In Progress", "Closed"])

            if st.button("Update Ticket"):
                df_full = pd.read_excel(ticket_file)  # reload
                df_full.loc[df_full["TicketID"] == chosen_id, "Status"] = new_status
                df_full.to_excel(ticket_file, index=False)
                log_action_via_agent(f"SYSTEM: Ticket {chosen_id} updated to {new_status}", user["username"])
                st.success(f"✅ Ticket {chosen_id} updated to {new_status}")
                st.rerun()

        # Export tickets
        st.download_button(
            "⬇️ Export tickets",
            data=open(ticket_file, "rb").read(),
            file_name="tickets.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No tickets logged yet.")