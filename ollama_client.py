import subprocess

# Moved from museum_assistant.py
SYSTEM_PROMPT = (
    "You are the Grand Museum Assistant. You have encyclopedic knowledge of the following ten artifacts:\n\n"
    "1. **The Solstice Sundial** (c. 1500 BCE, Egypt) – Bronze and granite dial used to mark solstices; inscribed with hieroglyphs of Ra; diameter ~50 cm; weight ~15 kg; original red ochre pigments visible; oriented to true north; housed in Solar Hall, Gallery 1.\n"
    "2. **Empress Mei’s Silk Fan** (c. 1392, Ming Dynasty) – Hand‑painted with phoenix motifs and inlaid jade handle; silk panels 30×45 cm; gold‑leaf accents; carved from imperial jade; used in court ceremonies; donated by the Liu family.\n"
    "When you see a user question, answer using only this information (you may infer logically but do not invent new artifacts). Answer concisely and shortly. User question: "
)

def query_ollama(user_text: str, conversation_history: list, model_name: str) -> str:
    """
    Send system prompt, history, and user prompt to Ollama and return the raw assistant output.
    """
    # Build the history string
    history_string = "\n".join(conversation_history)

    # Build a single prompt with system instruction, history, and current user text
    full_prompt = (
        f"SYSTEM: {SYSTEM_PROMPT}\n\n"
        f"CONVERSATION HISTORY:\n{history_string}\n\n" # Include history
        f"USER: {user_text}\n\n"
        f"ASSISTANT:"
    )
    # Consider making the model name ('llama2') a parameter or config value
    result = subprocess.run(
        ["ollama", "run", model_name],
        input=full_prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE # Capture stderr for potential errors
    )
    if result.returncode != 0:
        print(f"Error running Ollama: {result.stderr.decode()}")
        return "Sorry, I encountered an error trying to think."
    return result.stdout.decode().strip()
