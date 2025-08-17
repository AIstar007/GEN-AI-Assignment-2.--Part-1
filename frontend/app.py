import os, io, time, uuid
import pandas as pd
import streamlit as st
import requests
import difflib
import re


BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000/api")

st.set_page_config(page_title="Mimic – Agentic UI", layout="wide")

# --------------------------- HELPERS --------------------------- #
def clean_path(path: str) -> str:
    # Prevents accidental double `/api/api/`
    if path.startswith("/api/"):
        path = path[4:]   # strip "/api"
    return path if path.startswith("/") else "/" + path

def api_get(path, params=None):
    path = clean_path(path)
    r = requests.get(f"{BACKEND_URL}{path}", params=params)
    r.raise_for_status()
    return r.json()

def api_post(path, data=None):
    path = clean_path(path)
    r = requests.post(f"{BACKEND_URL}{path}", json=data or {})
    r.raise_for_status()
    return r.json()

def log_action_via_agent(text: str, user="system"):
    """Send logs to Django backend via /agent/ endpoint"""
    try:
        api_post("/agent/", {"input": text, "user": user})   # ✅ fixed
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

    # --- Show model selector for USERS only ---
    if user["role"] == "user":
        with st.sidebar:
            st.markdown("### 🤖 Choose Model")
            st.session_state.selected_model = st.selectbox(
                "Assistant Model",
                ["gemma2-9b-it", "gpt-4o", "llama-2-7b-chat", "claude-3-sonnet", "mixtral-8x7b"],
                key="chat_model"
            )

    # ---------------- Role-based App Access ---------------- #
    ROLE_APPS = {
        "user": ["Zoom"],
        "manager": ["Zoom", "MS Excel"],
        "admin": list(AVAILABLE_APPS.keys()),
    }
    allowed_apps = ROLE_APPS.get(user["role"], [])

    # ---------------- Chat History ---------------- #
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

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

        # Detect app/version from text
        app_from_text, ver_from_text = None, None
        m = re.match(r".*?(?P<app>[A-Za-z][\w\s]*)\s*(?P<version>[\w\.]+)?", user_input, re.I)
        if m:
            app_from_text = m.group("app").strip()
            ver_from_text = (m.group("version") or "").strip()

        # Fuzzy match app (only from allowed apps!)
        detected_app = None
        if app_from_text:
            for app in allowed_apps:
                if app_from_text.lower() in app.lower():
                    detected_app = app
                    break
            if not detected_app:
                close = difflib.get_close_matches(app_from_text, allowed_apps, n=1, cutoff=0.5)
                if close:
                    detected_app = close[0]

        # ---------------- App Detected → Confirm Install ---------------- #
        if detected_app:
            st.session_state.chat_history.append({
                "role": "assistant",
                "text": f"✅ I detected **{detected_app}**. Please confirm the version below."
            })

            with st.chat_message("assistant"):
                selected_app = st.selectbox(
                    "Choose an app",
                    allowed_apps,
                    index=allowed_apps.index(detected_app),
                    key=f"chat_app_{len(st.session_state.chat_history)}"
                )

                versions = AVAILABLE_APPS[selected_app]
                default_idx = 0
                if ver_from_text and ver_from_text in versions:
                    default_idx = versions.index(ver_from_text)
                elif ver_from_text:
                    close_ver = difflib.get_close_matches(ver_from_text, versions, n=1, cutoff=0.3)
                    if close_ver:
                        default_idx = versions.index(close_ver[0])

                selected_ver = st.selectbox(
                    "Choose version",
                    versions,
                    index=default_idx,
                    key=f"chat_ver_{len(st.session_state.chat_history)}"
                )

                if st.button("🚀 Confirm & Install", key=f"install_{len(st.session_state.chat_history)}"):
                    action = f"install {selected_app} {selected_ver}"
                    ticket_id = create_ticket(user, action)
                    log_action_via_agent(action, user["username"])

                    with st.spinner(f"🚀 Deploying {selected_app} {selected_ver}..."):
                        progress = st.progress(0)
                        for i in range(1, 101, 10):
                            time.sleep(0.15)
                            progress.progress(i)

                    st.success(f"✅ Deployment complete! Ticket {ticket_id}")
                    st.download_button(
                        "⬇️ Download Package",
                        data=f"Dummy installer for {selected_app} {selected_ver}".encode(),
                        file_name=f"{selected_app}-{selected_ver}.zip",
                        mime="application/zip"
                    )
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "text": f"✅ Installed {selected_app} {selected_ver}. Ticket {ticket_id} created."
                    })

        # ---------------- Otherwise → Fallback Chatbot ---------------- #
        else:
            chosen_model = st.session_state.get("selected_model", "Default-Agent")
            payload = {"input": user_input, "user": user["username"], "model": chosen_model}

            try:
                res = api_post("/agent/", payload)   # ✅ fixed
                if "output" in res:
                    reply = res["output"]
                elif "message" in res:
                    reply = res["message"]
                else:
                    reply = "⚠️ Unexpected backend response."
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
        logs = api_get("/logs/")   # ✅ fixed
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

        # ✅ Managers/Admins can approve/reject requests
        if user["role"] in ["manager", "admin"] and not df_tickets.empty:
            st.markdown("### 📝 Approve / Reject Requests")

            # Filter only Open tickets for approval
            pending_tickets = df_tickets[df_tickets["Status"] == "Open"]

            if not pending_tickets.empty:
                ticket_ids = pending_tickets["TicketID"].tolist()
                chosen_id = st.selectbox("Select Pending Ticket", ticket_ids)

                action_choice = st.radio(
                    "Action",
                    ["Approve ✅", "Reject ❌"],
                    horizontal=True
                )

                if st.button("Submit Decision"):
                    df_full = pd.read_excel(ticket_file)  # reload
                    if action_choice == "Approve ✅":
                        df_full.loc[df_full["TicketID"] == chosen_id, "Status"] = "In Progress"
                        df_full.to_excel(ticket_file, index=False)

                        log_action_via_agent(f"SYSTEM: Ticket {chosen_id} approved and deployment started", user["username"])
                        st.success(f"✅ Ticket {chosen_id} approved! Deployment in progress...")

                        # 🚀 Simulate deployment progress
                        with st.spinner("Deploying..."):
                            progress = st.progress(0)
                            for i in range(1, 101, 20):
                                time.sleep(0.3)
                                progress.progress(i)

                        # Mark as closed
                        df_full.loc[df_full["TicketID"] == chosen_id, "Status"] = "Closed"
                        df_full.to_excel(ticket_file, index=False)
                        log_action_via_agent(f"SYSTEM: Ticket {chosen_id} deployment completed", user["username"])
                        st.success(f"🎉 Deployment finished! Ticket {chosen_id} closed.")

                    elif action_choice == "Reject ❌":
                        df_full.loc[df_full["TicketID"] == chosen_id, "Status"] = "Closed"
                        df_full.to_excel(ticket_file, index=False)

                        log_action_via_agent(f"SYSTEM: Ticket {chosen_id} rejected by {user['username']}", user["username"])
                        st.error(f"❌ Ticket {chosen_id} rejected.")

                    st.rerun()
            else:
                st.info("✅ No pending tickets for approval.")

        # Export tickets
        st.download_button(
            "⬇️ Export tickets",
            data=open(ticket_file, "rb").read(),
            file_name="tickets.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
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

    # ---------------- ROLE-BASED ELIGIBILITY ---------------- #
    APP_ELIGIBILITY = {
        "user": {
            "Zoom": ["latest", "5.0"]
        },
        "manager": {
            "Zoom": ["latest", "5.0", "5.1"],
            "MS Excel": ["2019", "2021"]
        },
        "admin": {
            "MS Word": ["2016", "2019", "2021"],
            "MS Excel": ["2016", "2019", "2021"],
            "Zoom": ["5.0", "5.1", "latest"],
            "Slack": ["4.20", "4.21", "latest"]
        }
    }

    # --- Normal users: submit new requests ---
    if user["role"] == "user":
        st.markdown("### ➕ Submit New Request")
        req_app = st.selectbox("Select App", list(AVAILABLE_APPS.keys()))
        req_ver = st.selectbox("Select Version", AVAILABLE_APPS[req_app])

        if st.button("Submit Request"):
            req_id = str(uuid.uuid4())[:8]
            new_req = {
                "RequestID": req_id,
                "User": user["username"],
                "App": req_app,
                "Version": req_ver,
                "Status": "Pending",
            }
            df_reqs = pd.concat([df_reqs, pd.DataFrame([new_req])], ignore_index=True)
            df_reqs.to_excel(req_file, index=False)
            log_action_via_agent(f"REQUEST: {user['username']} requested {req_app} {req_ver}", user["username"])
            st.success(f"✅ Request {req_id} submitted for {req_app} {req_ver}")
            st.rerun()

    # --- Managers/Admins: see and approve requests ---
    if user["role"] in ["manager","admin"]:
        st.markdown("### 📝 Review Requests")
        if df_reqs.empty:
            st.info("No requests yet.")
        else:
            st.dataframe(df_reqs, use_container_width=True)
            pending = df_reqs[df_reqs["Status"]=="Pending"]
            if not pending.empty:
                chosen_req_id = st.selectbox("Select Request to Approve/Reject", pending["RequestID"])
                chosen_req = pending[pending["RequestID"] == chosen_req_id].iloc[0]

                app_name, version, req_user = chosen_req["App"], chosen_req["Version"], chosen_req["User"]

                # Detect requester's role (based on username convention)
                if req_user == "admin":
                    req_role = "admin"
                elif req_user == "bob":
                    req_role = "manager"
                else:
                    req_role = "user"

                # Eligibility check
                allowed_versions = APP_ELIGIBILITY.get(req_role, {}).get(app_name, [])
                eligible = version in allowed_versions

                if eligible:
                    st.success(f"✅ Eligible: {app_name} {version} allowed for role `{req_role}`")
                else:
                    st.error(f"⛔ Not Eligible: {app_name} {version} is NOT allowed for role `{req_role}`")

                decision = st.selectbox("Decision", ["Approve","Reject"])

                if st.button("Update Request"):
                    if decision == "Approve" and not eligible:
                        st.error("⛔ Cannot approve: This app/version is not allowed for the user's role.")
                    else:
                        df_reqs.loc[df_reqs["RequestID"] == chosen_req_id, "Status"] = decision
                        df_reqs.to_excel(req_file, index=False)
                        log_action_via_agent(f"ADMIN: {user['username']} set request {chosen_req_id} to {decision}", user["username"])
                        st.success(f"✅ Request {chosen_req_id} marked as {decision}")
                        st.rerun()

    # --- Export requests ---
    if not df_reqs.empty:
        st.download_button(
            "⬇️ Export requests",
            data=open(req_file,"rb").read(),
            file_name="requests.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

