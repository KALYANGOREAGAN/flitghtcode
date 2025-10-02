#!/bin/bash

echo "Installing GreenFlight Optimizer dependencies..."
echo "-----------------------------------------------"

# Activate virtual environment
source venv/bin/activate

# Install base dependencies
pip install django djangorestframework

# Install dependencies for PDF generation
pip install reportlab

# Install AI prediction dependencies
pip install numpy scikit-learn

echo "-----------------------------------------------"
echo "All dependencies installed successfully!"
echo "You can now restart your server."
