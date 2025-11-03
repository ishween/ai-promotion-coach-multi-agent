# Setup Instructions

## Quick Setup

Run the setup script:

```bash
./setup.sh
```

This will:
1. Create a virtual environment (`venv`)
2. Install all dependencies
3. Create a `.env` file template

## Manual Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

On Windows:
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys:

```
GEMINI_API_KEY=your_actual_gemini_api_key
SERPER_API_KEY=your_actual_serper_api_key
```

#### Getting API Keys:

1. **Gemini API Key**: 
   - Go to https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the key

2. **Serper API Key**:
   - Go to https://serper.dev
   - Sign up for a free account
   - Navigate to API keys section
   - Copy your API key

## Running the Application

```bash
source venv/bin/activate  # Activate venv if not already active
python main.py
```

## Model Information

The system uses:
- **Gemini 2.5 Flash** model for all LLM operations
- **Serper API** for course search with web scraping


<img width="1257" height="400" alt="Screenshot 2025-11-02 at 12 58 23 PM" src="https://github.com/user-attachments/assets/0e07fe0b-ff0d-4173-9de7-8f1d7bf18203" />
<img width="1260" height="485" alt="Screenshot 2025-11-02 at 1 02 51 PM" src="https://github.com/user-attachments/assets/13e90295-a7b6-4468-869d-d3da443ea95a" />
