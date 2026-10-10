# PulseTalk Automated Setup Script for Windows
# This script sets up the complete development environment

# Colors for output (PowerShell)
function Write-Info {
    Write-Host "ℹ $args" -ForegroundColor Blue
}

function Write-Success {
    Write-Host "✓ $args" -ForegroundColor Green
}

function Write-Warning {
    Write-Host "⚠ $args" -ForegroundColor Yellow
}

function Write-Error-Custom {
    Write-Host "✗ $args" -ForegroundColor Red
}

function Write-Header {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "  $args" -ForegroundColor Blue
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
}

# Check if command exists
function Test-CommandExists {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Main setup function
function Main {
    Write-Header "🎯 PulseTalk Development Environment Setup"
    
    Write-Info "This script will set up your development environment for PulseTalk"
    Write-Info "It will install dependencies and configure all three services:"
    Write-Info "  • Frontend (React + Vite)"
    Write-Info "  • Backend (Node.js + Express)"
    Write-Info "  • ML Engine (Python + FastAPI)"
    Write-Host ""
    
    $continue = Read-Host "Continue with setup? (y/n)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        Write-Warning "Setup cancelled"
        exit 0
    }
    
    # Step 1: Check prerequisites
    Write-Header "Step 1: Checking Prerequisites"
    Check-Prerequisites
    
    # Step 2: Install backend dependencies
    Write-Header "Step 2: Installing Backend Dependencies"
    Setup-Backend
    
    # Step 3: Install frontend dependencies
    Write-Header "Step 3: Installing Frontend Dependencies"
    Setup-Frontend
    
    # Step 4: Install ML engine dependencies
    Write-Header "Step 4: Installing ML Engine Dependencies"
    Setup-MLEngine
    
    # Step 5: Create environment files
    Write-Header "Step 5: Creating Environment Files"
    Create-EnvFiles
    
    # Step 6: Final instructions
    Write-Header "🎉 Setup Complete!"
    Print-FinalInstructions
}

# Check prerequisites
function Check-Prerequisites {
    $allGood = $true
    
    # Check Node.js
    if (Test-CommandExists node) {
        $nodeVersion = (node -v).Substring(1).Split('.')[0]
        if ([int]$nodeVersion -ge 18) {
            Write-Success "Node.js $(node -v) installed"
        } else {
            Write-Error-Custom "Node.js version must be >= 18.x (current: $(node -v))"
            $allGood = $false
        }
    } else {
        Write-Error-Custom "Node.js is not installed"
        Write-Info "Install from: https://nodejs.org/"
        $allGood = $false
    }
    
    # Check npm
    if (Test-CommandExists npm) {
        Write-Success "npm $(npm -v) installed"
    } else {
        Write-Error-Custom "npm is not installed"
        $allGood = $false
    }
    
    # Check Python
    if (Test-CommandExists python) {
        $pythonVersion = (python --version)
        Write-Success "$pythonVersion installed"
    } else {
        Write-Error-Custom "Python is not installed"
        Write-Info "Install from: https://www.python.org/"
        $allGood = $false
    }
    
    # Check pip
    if (Test-CommandExists pip) {
        Write-Success "pip $(pip --version | Select-String -Pattern '\d+\.\d+\.\d+' | ForEach-Object { $_.Matches.Value }) installed"
    } else {
        Write-Error-Custom "pip is not installed"
        $allGood = $false
    }
    
    # Check Git
    if (Test-CommandExists git) {
        Write-Success "Git $(git --version | Select-String -Pattern '\d+\.\d+\.\d+' | ForEach-Object { $_.Matches.Value }) installed"
    } else {
        Write-Warning "Git is not installed (optional but recommended)"
    }
    
    if (-not $allGood) {
        Write-Error-Custom "Please install missing prerequisites and run this script again"
        exit 1
    }
    
    Write-Host ""
}

# Setup backend
function Setup-Backend {
    Write-Info "Installing backend dependencies..."
    
    Push-Location backend
    
    if (Test-Path "package.json") {
        npm install --legacy-peer-deps
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Backend dependencies installed"
        } else {
            Write-Error-Custom "Failed to install backend dependencies"
            Pop-Location
            exit 1
        }
    } else {
        Write-Error-Custom "package.json not found in backend directory"
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host ""
}

# Setup frontend
function Setup-Frontend {
    Write-Info "Installing frontend dependencies..."
    
    Push-Location frontend
    
    if (Test-Path "package.json") {
        npm install --legacy-peer-deps
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend dependencies installed"
        } else {
            Write-Error-Custom "Failed to install frontend dependencies"
            Pop-Location
            exit 1
        }
    } else {
        Write-Error-Custom "package.json not found in frontend directory"
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host ""
}

# Setup ML engine
function Setup-MLEngine {
    Write-Info "Installing ML engine dependencies..."
    Write-Warning "This may take 5-10 minutes (downloading ML models)..."
    
    Push-Location ml-engine
    
    if (Test-Path "requirements.txt") {
        # Create virtual environment (optional but recommended)
        if (Test-CommandExists python) {
            Write-Info "Creating Python virtual environment..."
            python -m venv venv
            
            if (Test-Path "venv\Scripts\Activate.ps1") {
                Write-Success "Virtual environment created"
                
                # Install using venv pip directly (avoids PowerShell ExecutionPolicy restrictions)
                & "venv\Scripts\pip.exe" install -r requirements.txt
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "ML engine dependencies installed"
                } else {
                    Write-Error-Custom "Failed to install ML engine dependencies"
                    Pop-Location
                    exit 1
                }
            }
        }
    } else {
        Write-Error-Custom "requirements.txt not found in ml-engine directory"
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host ""
}

# Create environment files
function Create-EnvFiles {
    # Backend .env
    if (-not (Test-Path "backend\.env")) {
        Write-Info "Creating backend\.env file..."
        
        $backendEnv = @"
# Server Configuration
PORT=5000
NODE_ENV=development

# Database
MONGODB_URI=mongodb://localhost:27017/pulsetalk
# For MongoDB Atlas, use:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/pulsetalk

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_REFRESH_SECRET=your-super-secret-refresh-key-change-this-in-production
JWT_EXPIRE=15m
JWT_REFRESH_EXPIRE=7d

# ML Engine
ML_ENGINE_URL=http://localhost:8000

# CORS
FRONTEND_URL=http://localhost:5173
"@
        
        $backendEnv | Out-File -FilePath "backend\.env" -Encoding UTF8
        Write-Success "Created backend\.env"
    } else {
        Write-Warning "backend\.env already exists, skipping"
    }
    
    # Frontend .env
    if (-not (Test-Path "frontend\.env")) {
        Write-Info "Creating frontend\.env file..."
        
        $frontendEnv = @"
# API Configuration
VITE_API_URL=http://localhost:5000/api
"@
        
        $frontendEnv | Out-File -FilePath "frontend\.env" -Encoding UTF8
        Write-Success "Created frontend\.env"
    } else {
        Write-Warning "frontend\.env already exists, skipping"
    }
    
    # ML Engine .env
    if (-not (Test-Path "ml-engine\.env")) {
        Write-Info "Creating ml-engine\.env file..."
        
        $mlEngineEnv = @"
# Server Configuration
PORT=8000
ENVIRONMENT=development

# Model Configuration
MODEL_NAME=cardiffnlp/twitter-roberta-base-sentiment-latest
MAX_LENGTH=512
BATCH_SIZE=8
"@
        
        $mlEngineEnv | Out-File -FilePath "ml-engine\.env" -Encoding UTF8
        Write-Success "Created ml-engine\.env"
    } else {
        Write-Warning "ml-engine\.env already exists, skipping"
    }
    
    Write-Host ""
}

# Print final instructions
function Print-FinalInstructions {
    Write-Host ""
    Write-Success "All dependencies installed successfully!"
    Write-Host ""
    Write-Info "Next steps:"
    Write-Host ""
    Write-Host "  1. Configure your environment variables:"
    Write-Host "     • backend\.env  - Update MONGODB_URI with your database"
    Write-Host "     • frontend\.env - Already configured for local development"
    Write-Host "     • ml-engine\.env - Already configured for local development"
    Write-Host ""
    Write-Host "  2. Start the development servers (in 3 separate terminals):"
    Write-Host ""
    Write-Host "     Terminal 1 - ML Engine:" -ForegroundColor Cyan
    Write-Host "     cd ml-engine" -ForegroundColor Green
    Write-Host "     .\venv\Scripts\Activate.ps1  # If using virtual environment" -ForegroundColor Green
    Write-Host "     uvicorn app.main:app --reload --port 8000" -ForegroundColor Green
    Write-Host ""
    Write-Host "     Terminal 2 - Backend:" -ForegroundColor Cyan
    Write-Host "     cd backend" -ForegroundColor Green
    Write-Host "     npm run dev" -ForegroundColor Green
    Write-Host ""
    Write-Host "     Terminal 3 - Frontend:" -ForegroundColor Cyan
    Write-Host "     cd frontend" -ForegroundColor Green
    Write-Host "     npm run dev" -ForegroundColor Green
    Write-Host ""
    Write-Host "  3. Access the application:"
    Write-Host "     • Frontend:  " -NoNewline
    Write-Host "http://localhost:5173" -ForegroundColor Blue
    Write-Host "     • Backend:   " -NoNewline
    Write-Host "http://localhost:5000" -ForegroundColor Blue
    Write-Host "     • ML Engine: " -NoNewline
    Write-Host "http://localhost:8000" -ForegroundColor Blue
    Write-Host "     • ML Docs:   " -NoNewline
    Write-Host "http://localhost:8000/docs" -ForegroundColor Blue
    Write-Host ""
    Write-Info "For more information, see README.md and SETUP.md"
    Write-Host ""
}

# Run main function
Main
