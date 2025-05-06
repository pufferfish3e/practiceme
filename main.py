from selenium import webdriver #type: ignore
from selenium.webdriver.common.by import By #type: ignore
from selenium.webdriver.common.keys import Keys #type: ignore
from selenium.webdriver.chrome.service import Service #type: ignore
from selenium.webdriver.chrome.options import Options #type: ignore
from selenium.webdriver.support.ui import WebDriverWait #type: ignore
from selenium.webdriver.support import expected_conditions as EC #type: ignore
import time
from webdriver_manager.chrome import ChromeDriverManager # type: ignore
import google.generativeai as genai # type: ignore
from bs4 import BeautifulSoup # type: ignore
import settings

settings.initialize()

# environment variables
EMAIL = settings.EMAIL
PASSWORD = settings.PASSWORD
GEMINI_API_KEY = settings.GEMINI_API_KEY

# Topic selection: 
# 0 for 'Select All' topics
# OR a list of topic positions (1-15) to select specific topics by their position in the list
# Example: [1, 3, 5] will select the 1st, 3rd, and 5th topics in the list
TOPIC_SELECTION = settings.topic_selection

# Difficulty selection:
# "beginner" or "intermediate"
DIFFICULTY = settings.difficulty

# Map of topic positions (1-15) to their actual checkbox values in the HTML
# This mapping is based on the provided HTML elements
TOPIC_POSITION_TO_VALUE = {
    1: "8",    
    2: "9",    
    3: "10",    
    4: "11",
    5: "5",
    6: "6",
    7: "12",
    8: "13",
    9: "0",
    10: "1",
    11: "14",
    12: "2",
    13: "4",
    14: "7",
    15: "3"
}

# Load environment variables from .env file
print(f"Email: {EMAIL}")
print(f"Password: {"*"*len(PASSWORD)}")
print(f"Gemini API Key: {GEMINI_API_KEY[0:2]}{"*"*(len(GEMINI_API_KEY) - 2)}")
print(f"Topic Selection: {TOPIC_SELECTION}")
print(f"Difficulty Level: {DIFFICULTY}")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Function to extract JavaScript code from a webpage
def extract_javascript(driver):
    # Get all script tags from the page
    script_elements = driver.find_elements(By.TAG_NAME, "script")
    
    # Extract and return the JavaScript code
    javascript_code = []
    for script in script_elements:
        try:
            # Get the source attribute (for external scripts)
            src = script.get_attribute("src")
            if src:
                javascript_code.append(f"// External Script: {src}")
            else:
                # Get inline JavaScript
                content = script.get_attribute("innerHTML")
                if content and content.strip():
                    javascript_code.append(content)
        except:
            pass
    
    return "\n\n".join(javascript_code)

# Function to extract code from a code-snippet element
def extract_code_snippet(driver):
    try:
        # Find the code-snippet element
        code_element = driver.find_element(By.ID, "code-snippet")
        
        # Extract the raw text content
        raw_content = code_element.text
        print("\n=== Raw Code Snippet Content ===")
        print(raw_content)
        print("=== End of Raw Content ===\n")
        
        # Process the text to extract only the JavaScript code
        lines = raw_content.split('\n')
        js_code_lines = []
        
        # Skip the question line and process the actual code
        start_collecting = False
        for line in lines:
            # If we find a line with 'let', 'var', 'const', or 'function', start collecting code
            if any(keyword in line for keyword in ['let ', 'var ', 'const ', 'function ']):
                start_collecting = True
            
            if start_collecting:
                # Remove line numbers if present
                cleaned_line = line
                
                # Better line number removal - check if the line starts with a number followed by space
                if line.strip() and line.strip()[0].isdigit():
                    # Find where the actual code starts after the line number
                    # This regex pattern matches any digits at the start of the line
                    import re
                    match = re.match(r'^\s*\d+\s+(.+)$', line)
                    if match:
                        cleaned_line = match.group(1)
                    else:
                        # Fallback to simpler method
                        parts = line.split(None, 1)
                        if len(parts) > 1 and parts[0].isdigit():
                            cleaned_line = parts[1]
                
                js_code_lines.append(cleaned_line)
        
        processed_js_code = '\n'.join(js_code_lines)
        
        print("\n=== Processed JavaScript Code ===")
        print(processed_js_code)
        print("=== End of Processed Code ===\n")
        
        return processed_js_code
    except Exception as e:
        print(f"Error extracting code snippet: {e}")
        return ""

# Function to extract code from language-javascript class element
def extract_from_language_javascript(driver, max_attempts=3, delay=0.5):
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt+1}/{max_attempts} to find language-javascript element...")
            
            # Find elements with the class "language-javascript"
            js_elements = driver.find_elements(By.CSS_SELECTOR, "code.language-javascript")
            
            if not js_elements:
                print("No elements with class 'language-javascript' found.")
                
                # Try to find any code elements as a fallback
                code_elements = driver.find_elements(By.TAG_NAME, "code")
                if (code_elements):
                    print(f"Found {len(code_elements)} generic code elements instead.")
                    js_elements = code_elements
                else:
                    raise Exception("No code elements found")
            
            print(f"Found {len(js_elements)} code elements")
            
            # Get the first element
            code_element = js_elements[0]
            
            # Get all span elements within the code element
            span_elements = code_element.find_elements(By.TAG_NAME, "span")
            print(f"Found {len(span_elements)} span elements within the code element")
            
            # Extract and concatenate text from all span elements
            combined_text = ""
            for span in span_elements:
                # Skip line number spans
                if "linenumber" in span.get_attribute("class") or not span.text.strip():
                    continue
                span_text = span.text
                if span_text:
                    combined_text += span_text + " "
            
            # Clean up the combined text
            raw_content = combined_text.strip()
            print("\n=== Raw Content from Spans ===")
            print(raw_content)
            print("=== End of Raw Content ===\n")
            
            # Process the text to extract only the JavaScript code
            # Check if the text starts with a question
            if "What is the output" in raw_content or "What would be the output" in raw_content:
                # Find where the actual code starts
                code_start_indices = []
                for keyword in ['let ', 'var ', 'const ', 'function ']:
                    if keyword in raw_content:
                        code_start_indices.append(raw_content.find(keyword))
                
                # Get the earliest starting point that's not -1
                valid_indices = [idx for idx in code_start_indices if idx != -1]
                if valid_indices:
                    code_start = min(valid_indices)
                    raw_content = raw_content[code_start:]
            
            # Clean up the code
            processed_js_code = raw_content
            print("\n=== Processed JavaScript Code ===")
            print(processed_js_code)
            print("=== End of Processed Code ===\n")
            
            return processed_js_code
            
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt < max_attempts - 1:
                print(f"Waiting {delay} seconds before trying again...")
                time.sleep(delay)
            else:
                print("All attempts to extract code failed.")
                
                # Fallback: Try to get the innerHTML and parse it manually
                try:
                    print("Trying to extract using innerHTML...")
                    js_elements = driver.find_elements(By.CSS_SELECTOR, "code")
                    if js_elements:
                        html_content = js_elements[0].get_attribute("innerHTML")
                        print("HTML content of the code element:")
                        print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
                        
                        # Extract text from HTML, stripping tags
                        soup = BeautifulSoup(html_content, 'html.parser')
                        text_content = soup.get_text()
                        print("Extracted text content:")
                        print(text_content)
                        return text_content
                except Exception as inner_e:
                    print(f"Fallback extraction also failed: {str(inner_e)}")
                
                return ""

# Function to evaluate JavaScript code using Gemini API
def evaluate_javascript_with_gemini(code):
    try:
        # Create a Gemini model instance
        model = genai.GenerativeModel('gemini-1.5-flash')  # Changed from 'gemini-pro' to 'gemini-1.5-flash'
        
        # Prepare the prompt for Gemini
        prompt = f"""
        Execute this JavaScript code and respond with ONLY the exact console output value.
        
        No explanations, no code, no markdown formatting.
        
        ```javascript
        {code}
        ```
        Return only the raw output value that would appear in the console. Nothing else.
        """
        
        # Debug output to see what's being sent to Gemini
        print("\n=== DEBUG: PROMPT SENT TO GEMINI ===")
        print(prompt)
        print("=== END OF GEMINI PROMPT ===\n")
        
        # Generate a response
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        return f"Error using Gemini API: {str(e)}"

def select_topics(driver, topic_selection):
    # Wait for the topic selection page to load
    print("Waiting for topic selection page to load...")
    time.sleep(1)  # Increased wait time for page to fully load
    
    if topic_selection == 0:
        # Use the 'Select All Topics' button
        print("Using 'Select All Topics' button as configured...")
        select_all_topics_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, 
                "//button[contains(@class, 'MuiButton-containedPrimary') and contains(text(), 'Select All Topics')]"))
        )
        print("Clicking on Select All Topics button...")
        select_all_topics_button.click()
    else:
        # Select individual topics via checkboxes
        print(f"Selecting topics by position: {topic_selection}")
        
        # Make sure topic_selection is always a list
        if not isinstance(topic_selection, list):
            topic_selection = [topic_selection]
        
        # Click each checkbox according to the selected topic positions
        for topic_position in topic_selection:
            try:
                # Convert position to the corresponding value using our mapping
                if topic_position in TOPIC_POSITION_TO_VALUE:
                    topic_value = TOPIC_POSITION_TO_VALUE[topic_position]
                    print(f"Looking for checkbox at position {topic_position} (value={topic_value})...")
                    
                    # Try multiple strategies to click the checkbox
                    
                    # Strategy 1: Try clicking the label/span wrapping the checkbox first (most reliable)
                    try:
                        # Find the parent element that contains the checkbox
                        # This targets the span or label wrapping the checkbox (common pattern in Material-UI)
                        checkbox_wrapper = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, 
                                f"//input[@type='checkbox' and @value='{topic_value}']/parent::span"))
                        )
                        print(f"Found checkbox wrapper for position {topic_position}. Clicking...")
                        checkbox_wrapper.click()
                        print(f"Clicked on wrapper for checkbox at position {topic_position}")
                        time.sleep(0.1)  # Increased delay between clicks
                        continue  # Go to next checkbox if successful
                    except Exception as e1:
                        print(f"Couldn't click checkbox wrapper: {e1}")
                    
                    # Strategy 2: Try finding the parent label if the span didn't work
                    try:
                        # Find a wrapping label that might handle the click
                        checkbox_label = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, 
                                f"//input[@type='checkbox' and @value='{topic_value}']/ancestor::label"))
                        )
                        print(f"Found checkbox label for position {topic_position}. Clicking...")
                        checkbox_label.click()
                        print(f"Clicked on label for checkbox at position {topic_position}")
                        time.sleep(0.1)  # Increased delay between clicks
                        continue  # Go to next checkbox if successful
                    except Exception as e2:
                        print(f"Couldn't click checkbox label: {e2}")
                    
                    # Strategy 3: Use JavaScript to execute the click (bypass normal click handling)
                    try:
                        checkbox = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, 
                                f"//input[@type='checkbox' and @value='{topic_value}']"))
                        )
                        print(f"Using JavaScript to click checkbox at position {topic_position}")
                        driver.execute_script("arguments[0].click();", checkbox)
                        print(f"JavaScript clicked checkbox at position {topic_position}")
                        time.sleep(0.1)  # Increased delay between clicks
                    except Exception as e3:
                        print(f"JavaScript click failed: {e3}")
                        
                        # Strategy 4: Final fallback - try to find any clickable element near the checkbox
                        try:
                            # Look for any clickable element near the checkbox
                            outer_container = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, 
                                    f"//input[@type='checkbox' and @value='{topic_value}']/ancestor::div[contains(@class, 'MuiFormControl') or contains(@class, 'MuiCheckbox')]"))
                            )
                            print(f"Found outer container for position {topic_position}. Clicking...")
                            outer_container.click()
                            print(f"Clicked on container for checkbox at position {topic_position}")
                            time.sleep(0.1)  # Increased delay between clicks
                        except Exception as e4:
                            print(f"All strategies failed for checkbox at position {topic_position}")
                            raise Exception(f"Could not click checkbox at position {topic_position}")
                else:
                    print(f"Warning: Topic position {topic_position} is not valid. Valid positions are 1-15.")
            except Exception as e:
                print(f"Error selecting topic at position {topic_position}: {e}")
    
    # Wait for the selection to register
    time.sleep(0.5)  # Increased wait time after selection

def select_difficulty(driver, difficulty):
    """
    Selects the difficulty level based on user configuration.
    
    Args:
        driver: The Selenium WebDriver instance
        difficulty: String value, either "beginner" or "intermediate"
    """
    print(f"Setting difficulty level to: {difficulty}")
    
    # Make sure the difficulty value is valid
    if difficulty not in ["beginner", "intermediate"]:
        print(f"Warning: Invalid difficulty '{difficulty}'. Using 'beginner' as default.")
        difficulty = "beginner"
    
    # Wait for difficulty selection radio buttons to be present
    time.sleep(0.5)
    
    try:
        # Try multiple strategies to click the radio button
        
        # Strategy 1: Try clicking the radio input directly using JavaScript
        try:
            radio_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, 
                    f"//input[@type='radio' and @value='{difficulty}']"))
            )
            print(f"Found {difficulty} radio button. Using JavaScript to click...")
            driver.execute_script("arguments[0].click();", radio_button)
            print(f"Selected {difficulty} difficulty using JavaScript")
            return
        except Exception as e1:
            print(f"JavaScript click on radio button failed: {e1}")
        
        # Strategy 2: Try clicking the parent span
        try:
            radio_wrapper = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    f"//input[@type='radio' and @value='{difficulty}']/parent::span"))
            )
            print(f"Found radio button wrapper. Clicking...")
            radio_wrapper.click()
            print(f"Selected {difficulty} difficulty by clicking wrapper")
            return
        except Exception as e2:
            print(f"Clicking radio button wrapper failed: {e2}")
            
        # Strategy 3: Try clicking the parent label
        try:
            radio_label = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    f"//input[@type='radio' and @value='{difficulty}']/ancestor::label"))
            )
            print(f"Found radio button label. Clicking...")
            radio_label.click()
            print(f"Selected {difficulty} difficulty by clicking label")
            return
        except Exception as e3:
            print(f"Clicking radio button label failed: {e3}")
            
        # Strategy 4: Try finding any clickable element near the radio button
        try:
            container = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    f"//input[@type='radio' and @value='{difficulty}']/ancestor::div[contains(@class, 'MuiFormControl') or contains(@class, 'MuiRadio')]"))
            )
            print(f"Found outer container for radio button. Clicking...")
            container.click()
            print(f"Selected {difficulty} difficulty by clicking container")
            return
        except Exception as e4:
            print(f"All strategies failed for selecting {difficulty} difficulty")
            raise Exception(f"Could not select {difficulty} difficulty")
    
    except Exception as e:
        print(f"Error selecting difficulty {difficulty}: {e}")
    
    # Wait for the selection to register
    time.sleep(0.5)

# Function to check if we are still on the question page and recover if needed
def check_and_recover_page(driver, question_number):
    """
    Checks if we're still on the question page and attempts to recover if we've been
    redirected back to the dashboard unexpectedly.
    
    Returns:
        bool: True if we're on the correct page or recovery was successful, False otherwise
    """
    current_url = driver.current_url
    print(f"Current URL: {current_url}")
    
    # Check if we're on the dashboard page instead of a question page
    if "dashboard" in current_url:
        print(f"WARNING: Detected unexpected return to dashboard during question {question_number}")
        try:
            print("Attempting to recover...")
            
            # 1. Click on "Single Player" button again
            print("Looking for Single Player button...")
            single_player_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'MuiListItemButton-root')]//span[text()='Single Player']//ancestor::div[contains(@class, 'MuiButtonBase-root')]"))
            )
            print("Clicking on Single Player button...")
            single_player_button.click()
            time.sleep(0.5)
            
            # 2. Select topics again
            select_topics(driver, TOPIC_SELECTION)
            
            # 3. Select difficulty again
            select_difficulty(driver, DIFFICULTY)
            
            # 4. Click "Start" again
            print("Looking for Start button...")
            start_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'MuiButton-containedPrimary') and contains(text(), 'Start')]"))
            )
            print("Clicking on Start button...")
            start_button.click()
            
            print("Recovery attempt completed. Now we need to skip to the appropriate question...")
            
            # We need to skip to the current question
            # Wait a moment for the first question to load
            time.sleep(2)
            
            # Skip to the current question by clicking "Next" for (question_number-1) times
            # But only if we're not already on question 1
            if question_number > 1:
                print(f"Skipping ahead to question {question_number}...")
                for i in range(1, question_number):
                    try:
                        # Find and click any Next button to continue
                        skip_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
                        )
                        skip_button.click()
                        print(f"Skipped question {i}")
                        time.sleep(1.5)  # Wait for next question to load
                    except Exception as e:
                        print(f"Error while skipping to question {i+1}: {e}")
                        return False
            
            print(f"Recovery successful! Now processing question {question_number}")
            return True
            
        except Exception as e:
            print(f"Recovery attempt failed: {e}")
            return False
    
    # Check if we're on the authentication page
    elif "authenticate" in current_url:
        print(f"WARNING: Session expired, returned to login page during question {question_number}")
        try:
            print("Attempting to log back in...")
            
            # Find and fill the login fields
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "«r1»"))
            )
            password_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "«r2»"))
            )
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.MuiButtonBase-root.MuiButton-containedPrimary[type='submit']"))
            )
            
            email_field.send_keys(EMAIL)
            password_field.send_keys(PASSWORD)
            login_button.click()
            
            # Wait for successful login and redirect to dashboard
            WebDriverWait(driver, 10).until(
                EC.url_contains("dashboard")
            )
            
            # Now follow the same recovery steps as above
            # 1. Click on "Single Player" button again
            single_player_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'MuiListItemButton-root')]//span[text()='Single Player']//ancestor::div[contains(@class, 'MuiButtonBase-root')]"))
            )
            single_player_button.click()
            time.sleep(0.5)
            
            # 2. Select topics again
            select_topics(driver, TOPIC_SELECTION)
            
            # 3. Select difficulty again
            select_difficulty(driver, DIFFICULTY)
            
            # 4. Click "Start" again
            start_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'MuiButton-containedPrimary') and contains(text(), 'Start')]"))
            )
            start_button.click()
            
            # Skip to the current question as above
            time.sleep(2)
            if question_number > 1:
                print(f"Skipping ahead to question {question_number}...")
                for i in range(1, question_number):
                    try:
                        skip_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
                        )
                        skip_button.click()
                        print(f"Skipped question {i}")
                        time.sleep(1.5)
                    except Exception as e:
                        print(f"Error while skipping to question {i+1}: {e}")
                        return False
            
            print(f"Login recovery successful! Now processing question {question_number}")
            return True
            
        except Exception as e:
            print(f"Login recovery attempt failed: {e}")
            return False
    
    # We're on the expected page
    return True

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Initialize the WebDriver with the correct ChromeDriver version
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Navigate to the login page (changing to the login page instead of dashboard)
    driver.get("https://practiceme.vercel.app/authenticate")
    
    # Wait for the page to load
    time.sleep(2)
    
    # Print page title for debugging
    print(f"Page title: {driver.title}")
    
    # Try to find elements using the IDs from the HTML
    try:
        # Find the email input field using the ID from the HTML
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "«r1»"))
        )
        
        # Find the password field using the ID from the HTML
        password_field = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "«r2»"))
        )
        
        # Find the login button using the CSS class from the HTML
        login_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.MuiButtonBase-root.MuiButton-containedPrimary[type='submit']"))
        )
        
        # Fill in the form using credentials from .env
        email_field.send_keys(EMAIL)
        password_field.send_keys(PASSWORD)
        
        # Optional: Add a pause before clicking login
        print("About to click login button...")
        time.sleep(0.5)
        
        # Click the login button
        login_button.click()
        
        # Wait for successful login and redirect to dashboard
        print("Waiting for dashboard to load...")
        WebDriverWait(driver, 10).until(
            EC.url_contains("dashboard")
        )
        
        print("Successfully logged in!")
        
        # Now perform the requested clicks
        
        # 1. Click on "Single Player" button
        print("Looking for Single Player button...")
        single_player_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'MuiListItemButton-root')]//span[text()='Single Player']//ancestor::div[contains(@class, 'MuiButtonBase-root')]"))
        )
        print("Clicking on Single Player button...")
        single_player_button.click()
        time.sleep(1)
        
        # 2. Select topics based on user configuration
        select_topics(driver, TOPIC_SELECTION)
        
        # 3. Select difficulty based on user configuration
        select_difficulty(driver, DIFFICULTY)
        
        # 4. Click on "Start" button
        print("Looking for Start button...")
        start_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'MuiButton-containedPrimary') and contains(text(), 'Start')]"))
        )
        print("Clicking on Start button...")
        start_button.click()
        
        print("All buttons clicked successfully!")
        time.sleep(3)  # Wait to see the results
        
        # Set up a loop to handle 10 questions
        for question_number in range(1, 11):
            print(f"\n=== Processing Question {question_number}/10 ===\n")
            
            # Wait for the page to load the question
            time.sleep(1.5)
            
            # Check if we are still on the question page and recover if needed
            if not check_and_recover_page(driver, question_number):
                print(f"Failed to recover page for question {question_number}. Exiting loop.")
                break
            
            # Try to find and extract code from code-snippet element
            code_snippet = extract_code_snippet(driver)
            
            # If code-snippet element extraction failed, try the language-javascript extraction
            if not code_snippet:
                print("Code snippet element not found. Trying language-javascript extraction...")
                code_snippet = extract_from_language_javascript(driver)
            
            if code_snippet:
                print("\n=== Code Snippet Found ===")
                print(code_snippet)
                print("=== End of Code Snippet ===\n")
                
                # Evaluate the code snippet with Gemini
                print("Evaluating code snippet with Gemini API...")
                snippet_evaluation = evaluate_javascript_with_gemini(code_snippet)
                print("\n=== Gemini Evaluation of Code Snippet ===")
                print(snippet_evaluation)
                print("=== End of Evaluation ===\n")
                
                # Input the answer from Gemini into the text field
                try:
                    print("Entering the answer in the input field...")
                    input_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input.MuiInputBase-input.MuiOutlinedInput-input"))
                    )
                    
                    # Clear any existing text and enter the evaluation result
                    input_field.clear()
                    input_field.send_keys(snippet_evaluation)
                    print(f"Entered answer: {snippet_evaluation}")
                    
                    # Add a 1-second delay before clicking the Next button
                    print("Waiting 1 second before clicking Next button...")
                    time.sleep(1)
                    
                    # Click the "Next" button using the exact class structure you provided
                    print("Looking for Next button...")
                    next_button_xpath = "//button[contains(@class, 'MuiButton-containedPrimary') and contains(@class, 'MuiButton-colorPrimary') and contains(text(), 'Next')]"
                    next_button_css = "button.MuiButtonBase-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-colorPrimary[type='submit']"
                    
                    # Try XPath first
                    try:
                        next_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, next_button_xpath))
                        )
                        print("Found Next button using XPath selector")
                    except:
                        # Fall back to CSS selector if XPath fails
                        next_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_css))
                        )
                        print("Found Next button using CSS selector")
                    
                    print("Clicking Next button...")
                    next_button.click()
                    print(f"Completed question {question_number}/10")
                    
                    # Wait a moment and check if we're still on the right page
                    time.sleep(1)
                    if not check_and_recover_page(driver, question_number + 1):
                        print(f"Failed to stay on question page after submitting answer for question {question_number}.")
                        # If recovery failed, try once more before giving up
                        time.sleep(1)
                        if not check_and_recover_page(driver, question_number + 1):
                            print("Second recovery attempt failed. Exiting loop.")
                            break
                    
                    # Additional wait for next question to load
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error entering answer or clicking Next: {e}")
                    
                    # Check if we're on the right page before continuing
                    if not check_and_recover_page(driver, question_number):
                        print("Could not recover after error. Exiting loop.")
                        break
                    
                    # Try to continue with the next question if possible
                    try:
                        # Find and click the Next button using a more generic selector
                        fallback_next = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
                        fallback_next.click()
                        print("Used fallback method to proceed to next question")
                        time.sleep(1)
                        
                        # Check again if we're on the right page
                        if not check_and_recover_page(driver, question_number + 1):
                            print("Could not recover after fallback next button. Exiting loop.")
                            break
                    except:
                        print(f"Could not proceed to next question. Breaking loop.")
                        break
            else:
                
                # Check if we're on the right page before continuing
                if not check_and_recover_page(driver, question_number):
                    print("Could not recover after failing to find code. Exiting loop.")
                    break
                
                # Try to continue with the next question anyway
                try:
                    # Just try to find and click any Next button to continue
                    next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
                    next_button.click()
                    print("Skipped to next question")
                    time.sleep(1)
                    
                    # Check again if we're on the right page
                    if not check_and_recover_page(driver, question_number + 1):
                        print("Could not recover after skipping question. Exiting loop.")
                        break
                except Exception as e:
                    print(f"Could not proceed to next question: {e}")
                    break
        
        print("\n=== Completed all 10 questions! ===\n")
        
    except Exception as e:
        print(f"Error interacting with elements: {e}")
        
        # Alternative approach: try using name attribute instead of ID
        print("Trying alternative selectors...")
        try:
            email_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            password_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            
            # Find the button using the exact CSS selector
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary[type='submit']"))
            )
            
            login_button.click()
            print("Login attempted using alternative selectors")
            
            # Wait for redirect
            time.sleep(2)
            
        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")
        

finally:
    # Optional: Add a pause to see the final state
    print("Script completed. Browser will close in 3 seconds...")
    time.sleep(3)
    
    # Close the browser
    driver.quit()

