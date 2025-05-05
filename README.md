# PracticeMe Automation (Currently Broken)

This project automates answering singleplayer practice questions on [PracticeMe](https://practiceme.vercel.app/).

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

## 2. Set up your environment variables

Create a .env file with your credentials and Gemini API key:

```bash
touch .env
echo EMAIL=your_email@example.com >> .env
echo PASSWORD=your_password >> .env
echo GEMINI_API_KEY=your_api_key >> .env
```

## 3. Install Dependencies:

```bash
pip install -r requirements.txt
```

## 4. Get a Gemini API Key

Visit [Google's Gemini API page](https://ai.google.dev/gemini-api/docs/api-key) and generate a key.

## 5. Update your .env file

Replace placeholder values with your actual iChat email, password, and Gemini API key.

## 6. Run the Script

```python
python main.py
```
