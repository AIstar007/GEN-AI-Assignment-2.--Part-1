import os, io, time, uuid, time
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
tab_chat, tab_files, tab_logs, tab_tickets, tab_requests = st.tabs(
    ["💬 Chat / Install","📁 Files","📑 Logs","🎫 Tickets","📌 Requests / Approvals"]
)

# --------------------------- CHAT TAB --------------------------- #
with tab_chat:
    st.subheader("💬 Chat with Assistant")

    # --- Model selector only for user role ---
    if user["role"] == "user":
        with st.sidebar:
            st.markdown("### 🤖 Choose Model")
            st.session_state.selected_model = st.selectbox(
                "Assistant Model",
                ["gemma2-9b-it", "gpt-4o", "llama-2-7b-chat", "claude-3-sonnet", "mixtral-8x7b"],
                key="chat_model"
            )

    allowed_apps = ROLE_APPS.get(user["role"], [])

    # Init history + detection state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "detected_app" not in st.session_state:
        st.session_state.detected_app = None
        st.session_state.detected_version = None

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["text"])
        else:
            st.chat_message("assistant").write(msg["text"])

    # ---------------- Chat Input ---------------- #
    user_input = st.chat_input("Type your request (e.g., Install Zoom 5.1)")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})

        # Detect app/version
        app_from_text, ver_from_text = None, None
        m = re.match(r".*?(?P<app>[A-Za-z][\w\s]*)\s*(?P<version>[\w\.]+)?", user_input, re.I)
        if m:
            app_from_text = m.group("app").strip()
            ver_from_text = (m.group("version") or "").strip()

        # Fuzzy match app
        detected_app = None
        if app_from_text:
            for app in allowed_apps:
                if app_from_text.lower() in app.lower():
                    detected_app = app
                    break
            if not detected_app:
                close = difflib.get_close_matches(app_from_text, allowed_apps, n=1, cutoff=0.5)
                if close: detected_app = close[0]

        # Save detection in session state
        st.session_state.detected_app = detected_app
        st.session_state.detected_version = ver_from_text

        st.rerun()

    # ---------------- App Detected ---------------- #
    if st.session_state.detected_app:
        detected_app = st.session_state.detected_app
        ver_from_text = st.session_state.detected_version

        with st.chat_message("assistant"):
            st.write(f"✅ I detected **{detected_app}**. Please confirm the version below.")

            selected_app = st.selectbox("Choose an app", allowed_apps,
                                        index=allowed_apps.index(detected_app),
                                        key="chat_app")

            versions = AVAILABLE_APPS[selected_app]
            default_idx = 0
            if ver_from_text and ver_from_text in versions:
                default_idx = versions.index(ver_from_text)
            elif ver_from_text:
                close_ver = difflib.get_close_matches(ver_from_text, versions, n=1, cutoff=0.3)
                if close_ver: default_idx = versions.index(close_ver[0])

            selected_ver = st.selectbox("Choose version", versions,
                                        index=default_idx,
                                        key="chat_ver")

            # Eligibility
            APP_ELIGIBILITY = {
                "user": {"Zoom": ["latest", "5.0"]},
                "manager": {"Zoom": ["latest", "5.0", "5.1"], "MS Excel": ["2019", "2021"]},
                "admin": {
                    "MS Word": ["2016", "2019", "2021"],
                    "MS Excel": ["2016", "2019", "2021"],
                    "Zoom": ["5.0", "5.1", "latest"],
                    "Slack": ["4.20", "4.21", "latest"]
                }
            }
            allowed_versions = APP_ELIGIBILITY.get(user["role"], {}).get(selected_app, [])
            eligible = selected_ver in allowed_versions

            if eligible:
                with st.expander("✅ Eligible! Click to download installer"):
                    st.download_button(
                        "⬇️ Download Package",
                        data=f"Dummy installer for {selected_app} {selected_ver}".encode(),
                        file_name=f"{selected_app}-{selected_ver}.zip",
                        mime="application/zip",
                        key=f"dl_{selected_app}_{selected_ver}"
                    )
            else:
                st.error(f"⛔ Not eligible for {selected_app} {selected_ver}")

            if st.button("🚀 Confirm & Install"):
                if not eligible:
                    st.error("⛔ Cannot install: Not eligible for your role.")
                else:
                    action = f"install {selected_app} {selected_ver}"
                    ticket_id = create_ticket(user, action)
                    log_action_via_agent(action, user["username"])

                    with st.spinner(f"🚀 Deploying {selected_app} {selected_ver}..."):
                        progress = st.progress(0)
                        for i in range(1, 101, 10):
                            time.sleep(0.15)
                            progress.progress(i)

                    st.success(f"✅ Deployment complete! Ticket {ticket_id}")
                    st.session_state.show_download_modal = {"app": selected_app, "ver": selected_ver}
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "text": f"✅ Installed {selected_app} {selected_ver}. Ticket {ticket_id} created."
                    })

                    # Reset detection so dropdown disappears after install
                    st.session_state.detected_app = None
                    st.session_state.detected_version = None
                    st.rerun()

    # ---------------- Otherwise → Chatbot ---------------- #
    elif st.session_state.chat_history:
        last_msg = st.session_state.chat_history[-1]
        if last_msg["role"] == "user":  # only if last was user input
            chosen_model = st.session_state.get("selected_model", "Default-Agent")
            payload = {"input": last_msg["text"], "user": user["username"], "model": chosen_model}
            try:
                res = api_post("/agent/", payload)
                reply = res.get("output") or res.get("message") or "⚠️ Unexpected backend response."
            except Exception as e:
                reply = f"❌ Backend error: {e}"
            st.session_state.chat_history.append({"role": "assistant", "text": reply})
            st.rerun()

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

# --------------------------- LOGS TAB --------------------------- #
with tab_logs:
    try:
        logs = api_get("/logs/")
    except Exception as e:
        st.error(f"Error fetching logs: {e}")
        logs = []

    df = pd.DataFrame(logs or [])
    if user["role"] == "user" and not df.empty and "user" in df.columns:
        df = df[df["user"] == user["username"]]

    if not df.empty:
        st.dataframe(df, use_container_width=True, height=360)
    else:
        st.info("No logs available.")

# --------------------------- TICKETS TAB --------------------------- #
with tab_tickets:
    st.subheader("🎫 Ticket Tracking")
    ticket_file = "tickets.xlsx"

    if os.path.exists(ticket_file):
        df_tickets = pd.read_excel(ticket_file)
        if user["role"] == "user":
            df_tickets = df_tickets[df_tickets["User"] == user["username"]]

        st.dataframe(df_tickets, use_container_width=True)

        if user["role"] in ["manager", "admin"] and not df_tickets.empty:
            pending_tickets = df_tickets[df_tickets["Status"] == "Open"]
            if not pending_tickets.empty:
                chosen_id = st.selectbox("Select Pending Ticket", pending_tickets["TicketID"])
                action_choice = st.radio("Action", ["Approve ✅", "Reject ❌"], horizontal=True)

                if st.button("Submit Decision"):
                    df_full = pd.read_excel(ticket_file)
                    if action_choice == "Approve ✅":
                        df_full.loc[df_full["TicketID"] == chosen_id, "Status"] = "Closed"
                        df_full.to_excel(ticket_file, index=False)
                        log_action_via_agent(f"SYSTEM: Ticket {chosen_id} deployment completed", user["username"])
                        st.success(f"🎉 Deployment finished! Ticket {chosen_id} closed.")
                        st.session_state.show_download_modal = {"app": "Approved-App", "ver": "latest"}

                    elif action_choice == "Reject ❌":
                        df_full.loc[df_full["TicketID"] == chosen_id, "Status"] = "Closed"
                        df_full.to_excel(ticket_file, index=False)
                        st.error(f"❌ Ticket {chosen_id} rejected.")

                    st.rerun()
    else:
        st.info("No tickets logged yet.")

# --------------------------- REQUESTS TAB --------------------------- #
with tab_requests:
    st.subheader("📌 App Requests & Admin Approval")
    req_file = "requests.xlsx"
    if os.path.exists(req_file):
        df_reqs = pd.read_excel(req_file)
    else:
        df_reqs = pd.DataFrame(columns=["RequestID","User","App","Version","Status"])

    APP_ELIGIBILITY = {
        "user": {"Zoom": ["latest", "5.0"]},
        "manager": {"Zoom": ["latest", "5.0", "5.1"], "MS Excel": ["2019", "2021"]},
        "admin": {
            "MS Word": ["2016", "2019", "2021"],
            "MS Excel": ["2016", "2019", "2021"],
            "Zoom": ["5.0", "5.1", "latest"],
            "Slack": ["4.20", "4.21", "latest"]
        }
    }

    if user["role"] == "user":
        req_app = st.selectbox("Select App", list(AVAILABLE_APPS.keys()))
        req_ver = st.selectbox("Select Version", AVAILABLE_APPS[req_app])
        if st.button("Submit Request"):
            req_id = str(uuid.uuid4())[:8]
            df_reqs = pd.concat([df_reqs, pd.DataFrame([{
                "RequestID": req_id,
                "User": user["username"],
                "App": req_app,
                "Version": req_ver,
                "Status": "Pending",
            }])], ignore_index=True)
            df_reqs.to_excel(req_file, index=False)
            st.success(f"✅ Request {req_id} submitted for {req_app} {req_ver}")
            st.rerun()

    if user["role"] in ["manager","admin"]:
        st.dataframe(df_reqs, use_container_width=True)
        pending = df_reqs[df_reqs["Status"]=="Pending"]
        if not pending.empty:
            chosen_req_id = st.selectbox("Select Request", pending["RequestID"])
            chosen_req = pending[pending["RequestID"] == chosen_req_id].iloc[0]
            app_name, version, req_user = chosen_req["App"], chosen_req["Version"], chosen_req["User"]
            req_role = "admin" if req_user=="admin" else ("manager" if req_user=="bob" else "user")
            eligible = version in APP_ELIGIBILITY.get(req_role, {}).get(app_name, [])

            if eligible: st.success("✅ Eligible")
            else: st.error("⛔ Not Eligible")

            decision = st.selectbox("Decision", ["Approve","Reject"])
            if st.button("Update Request"):
                df_reqs.loc[df_reqs["RequestID"] == chosen_req_id, "Status"] = decision
                df_reqs.to_excel(req_file, index=False)
                if decision == "Approve" and eligible:
                    st.session_state.show_download_modal = {"app": app_name, "ver": version}
                st.rerun()

# --------------------------- Modal Popup --------------------------- #
if "show_download_modal" in st.session_state and st.session_state.show_download_modal:
    app_info = st.session_state.show_download_modal
    with st.modal("⬇️ Download Package"):
        st.write(f"Here is your installer for **{app_info['app']} {app_info['ver']}**")
        st.download_button(
            "Download Now",
            data=f"Dummy installer for {app_info['app']} {app_info['ver']}".encode(),
            file_name=f"{app_info['app']}-{app_info['ver']}.zip",
            mime="application/zip"
        )
        if st.button("Close"):
            st.session_state.show_download_modal = None
            st.rerun()
