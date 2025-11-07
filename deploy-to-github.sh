#!/bin/bash

# Teltonika Tracker - GitHub Deployment Script
# This script helps you quickly deploy your project to GitHub

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         Teltonika Tracker - GitHub Deployment Helper            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed.${NC}"
    echo "   Please install git first:"
    echo "   - macOS: brew install git"
    echo "   - Ubuntu/Debian: sudo apt-get install git"
    echo "   - Windows: Download from https://git-scm.com"
    exit 1
fi

echo -e "${GREEN}✅ Git is installed${NC}"
echo ""

# Check if this is already a git repository
if [ -d ".git" ]; then
    echo -e "${YELLOW}⚠️  This is already a git repository${NC}"
    echo "   Existing remotes:"
    git remote -v
    echo ""
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
else
    echo -e "${BLUE}📦 Initializing new git repository...${NC}"
    git init
    echo -e "${GREEN}✅ Repository initialized${NC}"
    echo ""
fi

# Check git configuration
if ! git config user.name &> /dev/null || ! git config user.email &> /dev/null; then
    echo -e "${YELLOW}⚠️  Git is not configured yet${NC}"
    echo ""
    read -p "Enter your name: " git_name
    read -p "Enter your email: " git_email
    
    git config --global user.name "$git_name"
    git config --global user.email "$git_email"
    
    echo -e "${GREEN}✅ Git configured${NC}"
    echo ""
fi

echo -e "${BLUE}Current git configuration:${NC}"
echo "  Name:  $(git config user.name)"
echo "  Email: $(git config user.email)"
echo ""

# Get GitHub repository URL
echo -e "${BLUE}🔗 GitHub Repository Setup${NC}"
echo ""
echo "Please create a new repository on GitHub first:"
echo "  1. Go to https://github.com/new"
echo "  2. Create your repository (don't initialize with README)"
echo "  3. Copy the repository URL"
echo ""
read -p "Enter your GitHub repository URL: " repo_url

if [ -z "$repo_url" ]; then
    echo -e "${RED}❌ No repository URL provided${NC}"
    exit 1
fi

# Check if remote already exists
if git remote get-url origin &> /dev/null; then
    echo -e "${YELLOW}⚠️  Remote 'origin' already exists${NC}"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote remove origin
        git remote add origin "$repo_url"
        echo -e "${GREEN}✅ Remote updated${NC}"
    fi
else
    git remote add origin "$repo_url"
    echo -e "${GREEN}✅ Remote added${NC}"
fi

echo ""

# Check for sensitive files
echo -e "${BLUE}🔒 Checking for sensitive files...${NC}"
sensitive_files=(".env" "credentials.json" "config.json" "*.pem")
found_sensitive=false

for pattern in "${sensitive_files[@]}"; do
    if ls $pattern 2>/dev/null | grep -q .; then
        echo -e "${RED}⚠️  Found: $pattern${NC}"
        found_sensitive=true
    fi
done

if [ "$found_sensitive" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Sensitive files detected!${NC}"
    echo "   Make sure these are in .gitignore before proceeding."
    echo ""
    read -p "Do you want to review .gitignore? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat .gitignore
        echo ""
        read -p "Press Enter to continue..."
    fi
fi

echo ""

# Stage files
echo -e "${BLUE}📦 Staging files...${NC}"
git add .

# Show status
echo ""
echo -e "${BLUE}Files to be committed:${NC}"
git status --short
echo ""

# Get commit message
read -p "Enter commit message (or press Enter for default): " commit_msg

if [ -z "$commit_msg" ]; then
    commit_msg="Initial commit: Teltonika vehicle tracker dashboard

- Complete vehicle tracking system
- Real-time GPS tracking dashboard
- Trip analysis with ignition detection
- Flask API backend
- AWS Lambda decoder for Teltonika protocol
- Interactive map visualization
- DynamoDB storage integration"
fi

# Commit
echo ""
echo -e "${BLUE}📝 Creating commit...${NC}"
git commit -m "$commit_msg"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Commit failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Commit created${NC}"
echo ""

# Set main branch
echo -e "${BLUE}🌿 Setting default branch to 'main'...${NC}"
git branch -M main
echo -e "${GREEN}✅ Branch set to main${NC}"
echo ""

# Push to GitHub
echo -e "${BLUE}🚀 Pushing to GitHub...${NC}"
echo ""
echo "You may be prompted for GitHub credentials:"
echo "  Username: Your GitHub username"
echo "  Password: Use a Personal Access Token"
echo ""
echo "Generate token at: https://github.com/settings/tokens"
echo "Required scopes: 'repo'"
echo ""
read -p "Ready to push? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Push cancelled. You can push manually later with:"
    echo "  git push -u origin main"
    exit 0
fi

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          🎉 Successfully deployed to GitHub! 🎉        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Your repository is now live at:"
    echo -e "${BLUE}$repo_url${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Visit your repository on GitHub"
    echo "  2. Add topics/tags for discoverability"
    echo "  3. Add screenshots to README"
    echo "  4. Share your project!"
    echo ""
    echo "To make updates in the future:"
    echo "  git add ."
    echo "  git commit -m 'Description of changes'"
    echo "  git push"
else
    echo ""
    echo -e "${RED}❌ Push failed${NC}"
    echo ""
    echo "Common issues:"
    echo "  1. Wrong credentials - Use Personal Access Token"
    echo "  2. Repository doesn't exist - Create it on GitHub first"
    echo "  3. Branch protection - Check repository settings"
    echo ""
    echo "You can try pushing manually:"
    echo "  git push -u origin main"
    exit 1
fi
