# Promotion Coach Multi-AI Agent

<img width="1283" height="719" alt="Screenshot 2025-11-02 at 11 38 13 AM" src="https://github.com/user-attachments/assets/de156b8a-4485-43fc-9885-d34b06f0e031" />

## Quick Setup & Running

### Automated Setup (Recommended)

The easiest way to get started is using the provided setup script:

```bash
# Make the script executable (first time only)
chmod +x setup.sh

# Run the setup script
./setup.sh
```

**What `setup.sh` does:**

✅ Creates a Python virtual environment (`venv`)  
✅ Activates the virtual environment  
✅ Upgrades pip to the latest version  
✅ Installs all required dependencies from `requirements.txt`  
✅ Creates a `.env` file template for your API keys  

**After running setup.sh:**

1. **Add your API keys to `.env`**:
   ```bash
   # Edit .env file and replace with your actual keys
   GEMINI_API_KEY=your_gemini_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   ```

2. **Get your API keys:**
   - **Gemini API Key**: https://makersuite.google.com/app/apikey
   - **Serper API Key**: https://serper.dev (free tier available)

### Running the Application

Once setup is complete:

```bash
# 1. Activate the virtual environment (if not already active)
source venv/bin/activate

# On Windows, use:
# venv\Scripts\activate

# 2. Run the application
python main.py
```

### First Run

When you run `python main.py`, you'll be prompted to enter:

- **Engineer Name**: The name of the engineer being analyzed
- **Current Level**: Current job level (e.g., "L4", "Senior Engineer")
- **Target Level**: Target promotion level (e.g., "L5", "Staff Engineer")
- **Discipline**: Engineering discipline (default: "Software Engineering")

The system will then:
1. Load data from the `data/` folder
2. Run the multi-agent workflow
3. Generate comprehensive analysis reports
4. Save outputs to the `outputs/` folder

### Viewing Results

After the workflow completes, find your results in the `outputs/` folder:

```bash
# List all outputs
ls outputs/

# Open HTML reports in your browser
# macOS:
open outputs/your_name_full_report.html

# Linux:
xdg-open outputs/your_name_full_report.html

# Windows:
start outputs/your_name_full_report.html
```

### Troubleshooting

**If setup.sh fails:**
```bash
# Check Python version (need 3.9+)
python3 --version

# Make script executable
chmod +x setup.sh

# Run with bash explicitly
bash setup.sh
```

**If application won't run:**
```bash
# Ensure venv is activated (you should see (venv) in your prompt)
source venv/bin/activate

# Verify dependencies are installed
pip list | grep langchain

# Reinstall if needed
pip install -r requirements.txt
```

**If you see API key errors:**
- Verify `.env` file exists in project root
- Check that keys are set without quotes: `GEMINI_API_KEY=actual_key_here`
- Ensure no extra spaces or line breaks in `.env` file

## Additional Resources

- See `handbook.md` for detailed technical documentation
- Check `SETUP.md` for manual setup instructions
- Review `data/` folder to customize input data