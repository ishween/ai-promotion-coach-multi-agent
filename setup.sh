#!/bin/bash

# Setup script for Promotion Coach System
echo "Setting up Promotion Coach System..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here
EOF
    echo ""
    echo "⚠️  Please update .env file with your API keys:"
    echo "   - GEMINI_API_KEY: Get from https://makersuite.google.com/app/apikey"
    echo "   - SERPER_API_KEY: Get from https://serper.dev"
    echo ""
else
    echo ".env file already exists. Skipping creation."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the application:"
echo "  python main.py"
echo ""

