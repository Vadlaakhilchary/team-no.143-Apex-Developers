# helpers.py
import re
import os
import requests
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env (if present)
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "google/flan-t5-small")
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# ----------------- Hugging Face helper -----------------
def call_hf_polish(core_reply, user_question, profile):
    """
    Call Hugging Face Inference API to polish a rule-based reply.
    Returns polished text, or None on failure.
    """
    if not HF_TOKEN:
        return None

    # Construct a concise prompt to instruct the model to polish
    prompt = (
        "You are an expert but friendly personal finance assistant. "
        "Polish and simplify the following reply so it is clear, concise, "
        "and easy to understand. Keep any numerical values or currencies unchanged.\n\n"
        f"User question: {user_question}\n\n"
        f"Reply: {core_reply}\n\n"
        "Polished reply:"
    )

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 200, "temperature": 0.2},
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            # If the API returns a non-200, return None to fallback cleanly
            return None
        data = resp.json()
        # Parse possible response formats
        # Common responses: [{"generated_text": "..."}] or {"generated_text": "..."}
        if isinstance(data, list) and data and "generated_text" in data[0]:
            out = data[0]["generated_text"]
        elif isinstance(data, dict) and "generated_text" in data:
            out = data["generated_text"]
        elif isinstance(data, str):
            out = data
        else:
            # Some models return other nested formats; try a best-effort
            out = None
            try:
                # If it's a list of dicts with 'generated_text' deeper
                out = data[0].get("generated_text")
            except Exception:
                out = None

        if out:
            return out.strip()
    except Exception:
        # Network error, timeout, auth failure, etc. — just return None to fallback
        return None

    return None

def maybe_polish_and_return(core_reply, user_question, profile):
    """Try to polish using HF; fallback to core_reply."""
    polished = call_hf_polish(core_reply, user_question, profile)
    return polished if polished else core_reply

# ----------------- Profile & parsing -----------------
def init_profile():
    """Initialize a default user profile with more fields."""
    return {
        "income": 0,
        "expenses": 0,
        "risk_tolerance": "medium",
        # This key tracks multi-step conversation state
        "conversation_state": None
    }

def parse_number(text):
    """Extracts the first numerical value from a string."""
    match = re.search(r'[\d,]+(?:\.\d+)?', text)
    if match:
        return float(match.group(0).replace(',', ''))
    return None

# ----------------- Core rule-based logic (unchanged flows) -----------------
def get_response(user_input, profile):
    """
    Generates a response based on user input and conversation state.
    Uses rule-based logic for finance features and polishes replies with HF if available.
    """
    raw_text = user_input.lower()
    state = profile.get("conversation_state")

    # --- State machine: multi-step conversations ---
    if raw_text.strip() == "back":
        profile["conversation_state"] = None
        core = "I've reset the conversation. How can I help you next?"
        return maybe_polish_and_return(core, user_input, profile)

    if state == "getting_income_for_budget":
        income = parse_number(user_input)
        if income:
            profile["income"] = income
            profile["conversation_state"] = "getting_expenses_for_budget"
            core = f"Great! Your monthly income is ₹{income:,.0f}. Now, what are your total monthly expenses (rent, bills, food, etc.)? You can also type 'back' to return to the main menu."
            return maybe_polish_and_return(core, user_input, profile)
        else:
            core = "I couldn't understand that number. Please provide your total monthly income. You can also type 'back' to return to the main menu."
            return maybe_polish_and_return(core, user_input, profile)

    elif state == "getting_expenses_for_budget":
        expenses = parse_number(user_input)
        if expenses:
            profile["expenses"] = expenses
            profile["conversation_state"] = None
            savings = profile["income"] - profile["expenses"]
            needs = profile["income"] * 0.5
            wants = profile["income"] * 0.3
            saves_target = profile["income"] * 0.2

            core = (
                f"Thanks! Based on your numbers:\n\n"
                f"- Income: ₹{profile['income']:,.0f}\n"
                f"- Expenses: ₹{profile['expenses']:,.0f}\n"
                f"- Potential Savings: ₹{savings:,.0f} per month\n\n"
                f"Sample budget (50/30/20):\n"
                f"- Needs (50%): ₹{needs:,.0f}\n"
                f"- Wants (30%): ₹{wants:,.0f}\n"
                f"- Savings (20%): ₹{saves_target:,.0f}\n\n"
            )
            if savings >= saves_target:
                core += "You're doing a great job with your savings! Keep it up."
            else:
                core += "You're a bit below the 20% savings target. Consider trimming wants."
            return maybe_polish_and_return(core, user_input, profile)
        else:
            core = "I couldn't understand that number. Please provide your total monthly expenses. You can also type 'back' to return to the main menu."
            return maybe_polish_and_return(core, user_input, profile)

    elif state == "getting_goal_amount":
        amount = parse_number(user_input)
        if amount:
            st.session_state.temp_goal_amount = amount
            profile["conversation_state"] = "getting_goal_time"
            core = f"Goal amount set to ₹{amount:,.0f}. In how many months do you want to achieve this goal? You can also type 'back' to return to the main menu."
            return maybe_polish_and_return(core, user_input, profile)
        else:
            core = "Please enter a valid target amount for your goal. You can also type 'back' to return to the main menu."
            return maybe_polish_and_return(core, user_input, profile)

    elif state == "getting_goal_time":
        months = parse_number(user_input)
        if months and months > 0:
            amount = st.session_state.temp_goal_amount
            monthly_savings = amount / months
            profile["conversation_state"] = None
            try:
                del st.session_state.temp_goal_amount
            except Exception:
                pass
            core = f"To reach your goal of ₹{amount:,.0f} in {int(months)} months, save ₹{monthly_savings:,.2f} every month."
            return maybe_polish_and_return(core, user_input, profile)
        else:
            core = "Please enter a valid number of months. You can also type 'back' to return to the main menu."
            return maybe_polish_and_return(core, user_input, profile)

    elif state == "getting_emergency_expenses":
        expenses = parse_number(user_input)
        if expenses:
            fund_3_months = expenses * 3
            fund_6_months = expenses * 6
            profile["conversation_state"] = None
            core = (
                f"For an emergency fund based on ₹{expenses:,.0f} monthly expenses, aim for:\n\n"
                f"- 3-month fund: ₹{fund_3_months:,.0f}\n"
                f"- 6-month fund: ₹{fund_6_months:,.0f}\n\n"
                "Keep this in a liquid/higher-yield savings option."
            )
            return maybe_polish_and_return(core, user_input, profile)
        else:
            core = "I didn't catch that. Please tell me your essential monthly expenses. You can also type 'back' to return to the main menu."
            return maybe_polish_and_return(core, user_input, profile)

    # --- Keyword-based intents (start conversations) ---
    if "budget" in raw_text or "plan" in raw_text:
        profile["conversation_state"] = "getting_income_for_budget"
        core = "Let's create a budget. What is your total monthly income after tax? You can also type 'back' to return to the main menu."
        return maybe_polish_and_return(core, user_input, profile)

    elif "emergency fund" in raw_text or "emergency" in raw_text:
        profile["conversation_state"] = "getting_emergency_expenses"
        core = "What are your essential monthly expenses (rent, food, utilities, EMIs)? You can also type 'back' to return to the main menu."
        return maybe_polish_and_return(core, user_input, profile)

    elif "goal" in raw_text:
        profile["conversation_state"] = "getting_goal_amount"
        core = "What is the target amount you want to save? You can also type 'back' to return to the main menu."
        return maybe_polish_and_return(core, user_input, profile)

    elif "tax" in raw_text:
        core = (
            "In India, you can save taxes using several sections:\n\n"
            "1. Section 80C (up to ₹1.5 lakh): PPF, ELSS, Life Insurance, principal repayment of home loan.\n"
            "2. Section 80D: Health insurance premium deduction.\n"
            "3. NPS (Section 80CCD(1B)): extra deduction of ₹50,000.\n\n"
            "The best option depends on your goals and risk appetite."
        )
        return maybe_polish_and_return(core, user_input, profile)

    elif "invest" in raw_text:
        core = (
            "Investment options by risk:\n\n"
            "- Low risk: FDs, PPF, Debt funds.\n"
            "- Medium risk: Index funds, Balanced mutual funds.\n"
            "- High risk: Direct equity, mid/small-cap funds, crypto (small allocation).\n\n"
            "What is your risk tolerance (low, medium, high)?"
        )
        return maybe_polish_and_return(core, user_input, profile)

    elif "hello" in raw_text or "hi" in raw_text:
        core = "Hello! 👋 How can I help you with your finances today? Try: 'create a budget', 'set a goal', or 'tax'."
        return maybe_polish_and_return(core, user_input, profile)

    # Default fallback
    core = "I’m not sure about that. Try asking me to 'create a budget', set a 'savings goal', or ask about 'tax' or 'investments'."
    return maybe_polish_and_return(core, user_input, profile)
