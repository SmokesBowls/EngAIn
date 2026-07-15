#!/bin/bash
# OKArchitect Setup Script
# Pulls required models and sets up the council

echo "🏗️  Setting up OKArchitect - Specialized AI Council"
echo "=================================================="
echo ""

# Check if ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama doesn't appear to be running."
    echo "   Please start ollama first: ollama serve"
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Function to check if model exists
model_exists() {
    ollama list | grep -q "$1"
}

# Function to pull model with status
pull_model() {
    local model=$1
    local purpose=$2
    
    echo "📦 Pulling $model ($purpose)..."
    
    if model_exists "$model"; then
        echo "   ✅ Already installed"
    else
        echo "   ⏳ Downloading..."
        if ollama pull "$model"; then
            echo "   ✅ Successfully installed"
        else
            echo "   ❌ Failed to install $model"
            return 1
        fi
    fi
    echo ""
}

echo "🎯 Installing Council Members..."
echo "================================"
echo ""

# Pull all required models
pull_model "dolphin-llama3:latest" "Reasoner - Strategic Architecture"
pull_model "phi3:mini-128k" "Validator - Fast Validation"
pull_model "deepseek-coder:6.7b" "EngineerA - Systems Engineering"
pull_model "qwen2.5-coder:7b" "EngineerB - Formal Patterns"
pull_model "joreilly86/structural_llama_3.0" "StructuralLogic - Mathematical Logic"

# Pull backup model
echo "📦 Installing backup model..."
pull_model "phi3:latest" "Backup model for timeouts"

echo "✨ Installation Complete!"
echo "======================="
echo ""
echo "Your OKArchitect council is ready:"
echo "  • Reasoner (dolphin-llama3)"
echo "  • Validator (phi3 mini)"
echo "  • EngineerA (deepseek-coder)"
echo "  • EngineerB (qwen2.5-coder)"
echo "  • StructuralLogic (structural_llama)"
echo ""
echo "🚀 To start the council:"
echo "   ./okarchitect.py"
echo ""
echo "📖 For quick help:"
echo "   ./okarchitect.py --help"
echo ""
echo "🎯 Quick consultation:"
echo "   ./okarchitect.py --quick \"Your question here\""
echo ""
echo "Happy architecting! 🏗️✨"
