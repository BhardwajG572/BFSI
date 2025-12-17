import os
from dotenv import load_dotenv

# Load keys immediately
load_dotenv()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.tools import tool_lookup_user, tool_check_eligibility
from app.core.logic import calculate_emi, get_emi_options_table
# --- NEW IMPORT ---
from app.services.pdf_generator import generate_sanction_letter

# 1. Setup LLM
llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.1-8b-instant", 
    api_key=os.getenv("GROQ_API_KEY")
)

# 2. Define State
class AgentState(TypedDict):
    messages: List[str]
    current_stage: str
    user_data: dict
    loan_amount: float
    sanction_letter: str # <--- NEW FIELD

# 3. Define Nodes

def entry_node(state: AgentState):
    """
    DUMMY NODE: Just decides where to go based on state.
    """
    return state

def sales_node(state: AgentState):
    messages = state["messages"]
    last_user_msg = messages[-1].strip()

    # --- 1. THE SHORTCUT FIX ---
    if last_user_msg.isdigit() and len(last_user_msg) == 10:
        return {
            "current_stage": "VERIFICATION",
            "messages": messages 
        }

    # --- 2. Standard Sales Logic ---
    sys_msg = """You are a polite Tata Capital Loan Officer. 
    Persuade the user to apply. 
    If the user agrees or says 'yes', reply ONLY with: 'MOVE_TO_VERIFICATION'.
    Do not ask for the phone number yourself, just output the token."""
    
    conversation = [SystemMessage(content=sys_msg)] + [HumanMessage(content=m) for m in messages]
    response = llm.invoke(conversation)
    content = response.content.strip()
    
    if "MOVE_TO_VERIFICATION" in content:
        return {
            "current_stage": "VERIFICATION", 
            "messages": messages + ["Great! Let's get started. Please type your 10-digit phone number."]
        }
    
    return {"messages": messages + [content], "current_stage": "SALES"}

def verification_node(state: AgentState):
    messages = state["messages"]
    last_msg = messages[-1]
    
    phone_input = last_msg.strip()
    
    if phone_input.isdigit() and len(phone_input) == 10:
        result = tool_lookup_user(phone_input)
        if result["found"]:
            user = result["data"]
            msg = f"Thanks {user['name']}. You are eligible! How much loan do you need?"
            return {"user_data": user, "current_stage": "UNDERWRITING", "messages": messages + [msg]}
        else:
            return {"messages": messages + ["Number not found. Try 9999999901."], "current_stage": "VERIFICATION"}
            
    return {"messages": messages + ["Please enter a valid 10-digit phone number."], "current_stage": "VERIFICATION"}

def underwriting_node(state: AgentState):
    messages = state["messages"]
    user_data = state["user_data"]
    last_msg = messages[-1].strip()
    
    # --- STEP 1: If we haven't locked a loan amount yet ---
    if state.get("loan_amount", 0) == 0:
        try:
            clean_amount = last_msg.lower().replace("k", "000").replace(",", "")
            amount = float(clean_amount)
            
            offer_table = get_emi_options_table(amount)
            
            return {
                "messages": messages + [offer_table], 
                "current_stage": "UNDERWRITING", 
                "loan_amount": amount 
            }
        except ValueError:
            return {
                "messages": messages + ["Please enter a valid numeric amount (e.g. 500000)."], 
                "current_stage": "UNDERWRITING"
            }

    # --- STEP 2: User has selected a tenure ---
    else:
        amount = state["loan_amount"]
        
        if last_msg in ["12", "24", "36","48","60"]:
            selected_tenure = int(last_msg)
            
            decision = tool_check_eligibility(amount, user_data)
            
            if decision["status"] == "APPROVED_INSTANT":
                final_emi = calculate_emi(amount, 12.0, selected_tenure)
                
                # --- NEW: GENERATE PDF ---
                pdf_path = generate_sanction_letter(
                    user_name=user_data['name'],
                    phone=user_data['phone'],
                    amount=amount,
                    tenure=selected_tenure,
                    emi=final_emi
                )
                
                res = f"Excellent choice! Your {selected_tenure}-month plan is **INSTANTLY APPROVED**. 🟢\n\nI have generated your Sanction Letter. Please download it below."
                
                return {
                    "messages": messages + [res], 
                    "current_stage": "END", 
                    "sanction_letter": pdf_path # <--- Store path
                }
                
            elif decision["status"] == "REQUIRES_SALARY_SLIP":
                res = f"Great choice. Since ₹{amount:,.0f} is a high amount, I just need your Salary Slip to confirm the EMI. Please upload it."
                return {"messages": messages + [res], "current_stage": "UPLOAD"}
                
            else:
                res = f"I'm sorry. We cannot approve this amount. Reason: {decision['reason']}"
                return {"messages": messages + [res], "current_stage": "END"}
        
        else:
            return {
                "messages": messages + ["Please select a tenure: Type '12', '24', or '36'."], 
                "current_stage": "UNDERWRITING"
            }

# 4. Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("entry", entry_node) 
workflow.add_node("sales", sales_node)
workflow.add_node("verification", verification_node)
workflow.add_node("underwriting", underwriting_node)

workflow.set_entry_point("entry")

def router(state):
    return state["current_stage"].lower()

workflow.add_conditional_edges(
    "entry",
    router,
    {
        "sales": "sales",
        "verification": "verification",
        "underwriting": "underwriting",
        "upload": END,
        "end": END
    }
)

workflow.add_edge("sales", END)
workflow.add_edge("verification", END)
workflow.add_edge("underwriting", END)

app_graph = workflow.compile()