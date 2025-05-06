# Enter your email, password and gemini api key here.
def initialize():
    global EMAIL,PASSWORD,GEMINI_API_KEY,topic_selection,difficulty

    EMAIL="YOUR_EMAIL"
    PASSWORD="YOUR_PASSWORD"
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
    
    # Optional Settings.

    # Topic selection: 
    # 0 for 'Select All' topics
    # OR a list of topic positions (1-15) to select specific topics by their position in the list
    # Example: [1, 3, 5] will select the 1st, 3rd, and 5th topics in the list

    # Topic List:
    """
    1. Length
    2. Index
    3. Index Operations (Sometimes Wrong)
    4. Methods
    5. For Loops (Sometimes Wrong)
    6. While Loops (Broken for now, don't touch)
    7. Function Scopes
    8. Function Parameters (Sometimes Wrong)
    9. Boolean
    10. Shorthand
    11. Arithmetic Precedence (Terribly Wrong)
    12. Post/Pre In/Decrement (Gets kicked out)
    13. Switch (Broken for now, don't touch)
    14. Do...While (Broken for now, don't touch)
    15. If/Else
    """

    topic_selection = [0]

    # Difficulty selection:
    # "beginner" or "intermediate"
    difficulty = "beginner"