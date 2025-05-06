# PracticeMe Automation Tool

## Project Info

This project automates answering single-player practice questions on [PracticeMe](https://practiceme.vercel.app/).

It uses [Selenium](https://pypi.org/project/selenium/) with [Python](https://www.python.org/) for web automation, allowing it to interact with the browser like a human user.

Additionally, the project integrates the [Gemini API](https://ai.google.dev/) to evaluate and interpret simple [JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript) code dynamically.

> ⚠️ **Disclaimer:**  
This tool is intended for **educational purposes only**. Use it at your own risk.  
AI-generated results may contain errors—always verify important outputs manually.

Gemini is not good at solving the following problem types:
- Index Operations
- For Loops
- While Loops
- Function Parameters
- Arithmetic Precedence
- Post/Pre In/Decrement
- Switch
- Do...While

## 📦 Requirements

- Python 3
- Google Chrome
- Visual Studio Code (or any text/code editor)

## ⚙️ Installation

> 💡 It's recommended to use a [Python virtual environment](https://docs.python.org/3/library/venv.html) for managing dependencies.

### 1. Clone the repository

```bash
git clone https://github.com/pufferfish3e/practiceme.git
cd practiceme
```

## 2. Install Dependencies:

```bash
pip install -r requirements.txt
```

## 3. Get a Gemini API Key

Visit [Google's Gemini API page](https://ai.google.dev/gemini-api/docs/api-key) and generate a key.

## 4. Update your settings.py file

Replace placeholder values with your actual iChat email, password, and Gemini API key.

```python
EMAIL = "YOUR_EMAIL"
PASSWORD = "YOUR_PASSWORD"
GEMINI_API_KEY = "YOUR_API_KEY"
```

There are additional settings that can be configured within the ```bash settings.py``` file.

## 5. Run the Script

```python
python main.py
```

## Known Issues
- When entering "0", the website might crash midway whilst completing the problems.
- Logs may appear within your working directory even if the script runs without any problem, just delete them
- 

## Changelog

### Version 1.2
- attempted to fix crash while doing questions when the "select all topics" button is pressed
- added functionality to select different topics within the selector
- found some flagged topics (that the AI is not really good at solving)

### Version 1.1
- added functionality to customise different difficulty settings

Made with ❤️ by Kendrick