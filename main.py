from selenium import webdriver #type: ignore
from selenium.webdriver.common.by import By #type: ignore
from selenium.webdriver.common.keys import Keys #type: ignore
from selenium.webdriver.chrome.service import Service #type: ignore
from selenium.webdriver.chrome.options import Options #type: ignore
from selenium.webdriver.support.ui import WebDriverWait #type: ignore
from selenium.webdriver.support import expected_conditions as EC #type: ignore
import time
from webdriver_manager.chrome import ChromeDriverManager # type: ignore
from dotenv import load_dotenv # type: ignore
import os
import google.generativeai as genai  
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Get Gemini API key from .env

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
                # Remove line numbers that appear at the beginning of lines
                if line.strip() and line.strip()[0].isdigit():
                    parts = line.split(None, 1)
                    if len(parts) > 1:
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
def extract_from_language_javascript(driver, max_attempts=5, delay=2):
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt+1}/{max_attempts} to find language-javascript element...")
            
            # Find elements with the class "language-javascript"
            js_elements = driver.find_elements(By.CSS_SELECTOR, "code.language-javascript")
            
            if not js_elements:
                print("No elements with class 'language-javascript' found.")
                
                # Try to find any code elements as a fallback
                code_elements = driver.find_elements(By.TAG_NAME, "code")
                if code_elements:
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
                
                # Take a screenshot to see what's on the page
                screenshot_path = f"code_extraction_failed_{time.time()}.png"
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
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
        
        # Generate a response
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        return f"Error using Gemini API: {str(e)}"

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
        time.sleep(0.5)
        
        # 2. Click on "Select All Topics" button
        print("Looking for Select All Topics button...")
        select_all_topics_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'MuiButton-containedPrimary') and contains(text(), 'Select All Topics')]"))
        )
        print("Clicking on Select All Topics button...")
        select_all_topics_button.click()
        time.sleep(0.5)
        
        # 3. Click on "Start" button
        print("Looking for Start button...")
        start_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'MuiButton-containedPrimary') and contains(text(), 'Start')]"))
        )
        print("Clicking on Start button...")
        start_button.click()
        
        print("All buttons clicked successfully!")
        time.sleep(1)  # Wait to see the results
        
        # Set up a loop to handle 10 questions
        for question_number in range(1, 11):
            print(f"\n=== Processing Question {question_number}/10 ===\n")
            
            # Wait for the page to load the question
            time.sleep(1.5)
            
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
                    
                    # Wait a moment for the next question to load
                    time.sleep(1.5)
                    
                except Exception as e:
                    print(f"Error entering answer or clicking Next: {e}")
                    screenshot_path = f"answer_input_failed_q{question_number}_{time.time()}.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"Screenshot saved to {screenshot_path}")
                    
                    # Try to continue with the next question if possible
                    try:
                        # Find and click the Next button using a more generic selector
                        fallback_next = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
                        fallback_next.click()
                        print("Used fallback method to proceed to next question")
                        time.sleep(1.5)
                    except:
                        print(f"Could not proceed to next question. Breaking loop.")
                        break
            else:
                print(f"No code snippet could be extracted for question {question_number}. Taking screenshot.")
                screenshot_path = f"no_code_found_q{question_number}_{time.time()}.png"
                driver.save_screenshot(screenshot_path)
                
                # Try to continue with the next question anyway
                try:
                    # Just try to find and click any Next button to continue
                    next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
                    next_button.click()
                    print("Skipped to next question")
                    time.sleep(1.5)
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
            
            # Fill in the form
            email_field.send_keys("your_email@example.com")
            password_field.send_keys("your_password")
            
            # Find the button using the exact CSS selector
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary[type='submit']"))
            )
            
            login_button.click()
            print("Login attempted using alternative selectors")
            
            # Wait for redirect
            time.sleep(5)
            
        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")
        
        # Take a screenshot for debugging
        screenshot_path = "error_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

finally:
    # Optional: Add a pause to see the final state
    print("Script completed. Browser will close in 5 seconds...")
    time.sleep(5)
    
    # Close the browser
    driver.quit()

