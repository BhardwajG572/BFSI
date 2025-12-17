import shutil
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Import your Graph
from app.agents.master import app_graph
# --- NEW IMPORTS FOR PDF & LOGIC ---
from app.services.pdf_generator import generate_sanction_letter
from app.core.logic import calculate_emi

load_dotenv()

app = FastAPI(
    title="Tata Capital Agentic Backend",
    description="API for Chat, File Upload, and Logic testing.",
    version="1.0"
)

# --- 1. THE FAKE DATABASE (Session Storage) ---
MEMORY_DB = {}

# --- 2. DATA MODELS ---
class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    next_stage: str
    user_data: Dict[str, Any] = {}
    sanction_letter: Optional[str] = None # <--- Added this field

# --- 3. ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "active", "message": "System Ready"}

@app.post("/reset/{thread_id}")
def reset_memory(thread_id: str):
    if thread_id in MEMORY_DB:
        del MEMORY_DB[thread_id]
    return {"message": f"Memory cleared for {thread_id}"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    The Main Brain. Sends text to the Agent.
    """
    # 1. Retrieve or Initialize State
    if req.thread_id not in MEMORY_DB:
        MEMORY_DB[req.thread_id] = {
            "messages": [], 
            "current_stage": "SALES",
            "user_data": {},
            "loan_amount": 0,
            "sanction_letter": None
        }
    
    current_state = MEMORY_DB[req.thread_id]

    # 2. Append User Message to State
    inputs = {
        "messages": current_state["messages"] + [req.message],
        "current_stage": current_state["current_stage"],
        "user_data": current_state["user_data"],
        "loan_amount": current_state["loan_amount"],
        "sanction_letter": current_state.get("sanction_letter")
    }
    
    try:
        # 3. Run the LangGraph Agent
        result = app_graph.invoke(inputs)
        
        # 4. Save the NEW state back to our "Fake Database"
        MEMORY_DB[req.thread_id] = {
            "messages": result["messages"],
            "current_stage": result["current_stage"],
            "user_data": result.get("user_data", {}),
            "loan_amount": result.get("loan_amount", 0),
            "sanction_letter": result.get("sanction_letter")
        }
        
        # 5. Extract the Bot's last reply
        bot_msg = result["messages"][-1]
        response_text = bot_msg.content if hasattr(bot_msg, 'content') else str(bot_msg)

        # --- FIX: Pass 'sanction_letter' to the frontend ---
        return {
            "response": response_text,
            "next_stage": result["current_stage"],
            "user_data": result.get("user_data", {}),
            "sanction_letter": result.get("sanction_letter", None) # <--- ADD THIS
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_salary_slip(thread_id: str, file: UploadFile = File(...)):
    """
    The specific endpoint for the '2x Limit' Edge Case.
    """
    # 1. Check if session exists
    if thread_id not in MEMORY_DB:
        raise HTTPException(status_code=404, detail="Session not found. Start a chat first.")
    
    state = MEMORY_DB[thread_id]
    
    # 2. Validation
    if state["current_stage"] != "UPLOAD":
        return {"message": "I am not expecting a file right now. Let's chat first."}

    # 3. Save the file
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 4. Run the "Post-Upload" Logic
    user_salary = state["user_data"].get("salary", 50000)
    loan_ask = state["loan_amount"]
    
    pdf_path = None
    
    # Mock Approval Logic (EMI <= 50% Salary)
    if user_salary * 0.5 > (loan_ask * 0.02): 
        decision = "APPROVED_WITH_DOCS"
        
        # --- GENERATE PDF ON UPLOAD SUCCESS ---
        # Default to 36 months for this edge case if not tracked
        tenure = 36 
        emi = calculate_emi(loan_ask, 12.0, tenure)
        
        pdf_path = generate_sanction_letter(
            user_name=state["user_data"]["name"],
            phone=state["user_data"]["phone"],
            amount=loan_ask,
            tenure=tenure,
            emi=emi
        )
        
        bot_reply = "Received your Salary Slip. Everything looks good! Your loan is APPROVED. ✅"
        next_stage = "END"
    else:
        decision = "REJECTED"
        bot_reply = "I reviewed your slip. Unfortunately, your EMI burden is too high."
        next_stage = "END"

    # 5. Update State
    state["messages"].append(f"User uploaded: {file.filename}")
    state["messages"].append(bot_reply)
    state["current_stage"] = next_stage
    state["sanction_letter"] = pdf_path # Save to memory
    
    # Clean up file
    os.remove(file_location)

    # --- RETURN CORRECT STRUCTURE ---
    return {
        "status": "processed",
        "decision": decision,
        "bot_reply": bot_reply,
        "sanction_letter": pdf_path # Send path to frontend
    }