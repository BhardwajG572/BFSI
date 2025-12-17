import streamlit as st
import requests
import os

# Backend URL
API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Tata Capital GenAI Agent", page_icon="🏦")

st.title("🏦 Tata Capital Loan Assistant")

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "SALES"
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "User_Web_1" 

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("🧠 Agent Brain State")
    st.metric("Current Stage", st.session_state.current_stage)
    
    if st.session_state.user_data:
        st.success(f"✅ Verified: {st.session_state.user_data.get('name')}")
        with st.expander("View User Details"):
            st.json(st.session_state.user_data)
    else:
        st.info("Waiting for Verification...")

    # --- FILE UPLOAD LOGIC ---
    if st.session_state.current_stage == "UPLOAD":
        st.warning("⚠️ High Risk Request: Salary Slip Required")
        uploaded_file = st.file_uploader("Upload Salary Slip (PDF)", type=["pdf", "txt", "png"])
        
        if uploaded_file:
            with st.spinner("Analyzing Document..."):
                files = {"file": uploaded_file}
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/upload?thread_id={st.session_state.thread_id}", 
                        files=files
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.current_stage = "END"
                        
                        # SAVE PDF PATH TO HISTORY
                        msg_data = {
                            "role": "assistant", 
                            "content": data["bot_reply"],
                            "sanction_letter": data.get("sanction_letter") # <--- SAVE THIS
                        }
                        st.session_state.messages.append(msg_data)
                        st.rerun()
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    # Reset Button
    if st.button("Reset Conversation"):
        requests.post(f"{API_BASE_URL}/reset/{st.session_state.thread_id}")
        st.session_state.messages = []
        st.session_state.current_stage = "SALES"
        st.session_state.user_data = {}
        st.rerun()

# --- 3. MAIN CHAT INTERFACE ---

# --- FIX: RENDER HISTORY WITH BUTTONS ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # CHECK IF THIS MESSAGE HAS A PDF ATTACHED
        pdf_path = msg.get("sanction_letter")
        if pdf_path and os.path.exists(pdf_path):
            try:
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Download Sanction Letter",
                        data=pdf_file.read(),
                        file_name="Sanction_Letter.pdf",
                        mime='application/pdf',
                        key=f"download_btn_{i}" # Unique key for every button
                    )
            except Exception as e:
                st.error(f"Error loading PDF: {e}")

# --- 4. HANDLE USER INPUT ---
if prompt := st.chat_input("Type your message here..."):
    # Display User Message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Send to Backend
    payload = {
        "message": prompt,
        "thread_id": st.session_state.thread_id
    }
    
    try:
        with st.spinner("Agent is thinking..."):
            response = requests.post(f"{API_BASE_URL}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                bot_text = data.get("response", "Error: No response")
                next_stage = data.get("next_stage", "SALES")
                user_data = data.get("user_data", {})
                sanction_path = data.get("sanction_letter") # Capture the path
                
                # Update State
                st.session_state.current_stage = next_stage
                if user_data:
                    st.session_state.user_data = user_data
                
                # --- SAVE MESSAGE WITH PDF PATH ---
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": bot_text,
                    "sanction_letter": sanction_path # <--- CRITICAL: Save it here
                })
                
                # Refresh to update the Sidebar and History Loop
                st.rerun()
            else:
                st.error(f"Backend Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error connecting to brain: {e}")