# 🔑 Setting Up Your Groq API Key

**Note**: NLytics is a proof-of-concept demonstrating AI-powered natural language to code generation.

NLytics uses **AI-powered query understanding** via Groq's Llama model. The system intelligently understands your questions by analyzing your actual dataset - no clarifications needed for most queries.

## Quick Setup (2 minutes)

### 1. Get Your Free Groq API Key

1. Go to https://console.groq.com/keys
2. Sign up for a free account (no credit card required)
3. Click "Create API Key"
4. Copy your key (starts with `gsk_...`)

### 2. Set the Environment Variable

**Option A: Using .env file (Recommended)**
```bash
# Create .env file in the NLytics folder
echo GROQ_API_KEY=your_actual_key_here > .env
```

**Option B: PowerShell (Current Session)**
```powershell
$env:GROQ_API_KEY = "your_actual_key_here"
python start.py
```

**Option C: PowerShell (Permanent)**
```powershell
[Environment]::SetEnvironmentVariable("GROQ_API_KEY", "your_actual_key_here", "User")
```

### 3. Restart the Server

```bash
python start.py
```

## What Changed?

### Before (Pattern Matching):
```
You: highest valued stock
Bot: Please specify which column to rank by.
You: price
Bot: Error... 🤦
```

### Now (AI-Powered):
```
You: highest valued stock
Bot: Top 10 rows by highest close_price:
     1. close_price: $523.45 (symbol: NVDA, date: 2025-07-15)
     2. close_price: $498.32 (symbol: TSLA, date: 2025-07-22)
     ... ✨
```

## How It Works

The AI now receives:
- **Your query**: "highest valued stock"
- **Dataset schema**: All column names and types
- **Sample data**: A few values from each column
- **Statistics**: Min/max/mean for numeric columns
- **Conversation history**: Previous messages for context

The AI intelligently:
- Figures out you want `close_price` (the value column)
- Understands "highest" means descending sort
- Defaults to top 10 results
- Includes context columns (symbol, date, etc.)

## Free Tier Limits

Groq's free tier is **very generous**:
- **6,000 requests per minute**
- **30 requests per minute** per model
- More than enough for personal use!

## Troubleshooting

**Error: "GROQ_API_KEY not found"**
- Make sure you've set the environment variable
- Restart your terminal/PowerShell after setting it
- Check `.env` file is in the NLytics root folder

**Error: "Invalid API key"**
- Double-check your key from https://console.groq.com/keys
- Make sure there are no extra spaces or quotes

**Need Help?**
- Check your API usage: https://console.groq.com/settings/usage
- Groq Discord: https://discord.gg/groq
