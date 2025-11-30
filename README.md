# Perplexity AI Alexa Skill

Query Perplexity AI hands-free using your Alexa device.

## What You Can Do

Ask Alexa natural questions and get instant answers powered by Perplexity:

- "Alexa, ask Perplexity News Agent what's new in OpenAI today"
- "Alexa, ask Perplexity News Agent for the latest about Airbus"
- "Alexa, ask Perplexity News Agent to summarize today's AI developments"
- "Alexa, ask Perplexity News Agent to get me top restaurants in Toronto"

## How It Works

The architecture is straightforward: your voice → Alexa → AWS Lambda → Perplexity API → cleaned response → Alexa speaks back.

The Lambda function handles API calls, cleans markdown formatting, removes unnecessary line breaks, and returns voice-friendly text optimized for Alexa's speech synthesis.

## Key Features

- **Voice-driven queries** – hands-free interaction with no typing required
- **Perplexity sonar-pro model** – reliable, up-to-date AI responses
- **Smart formatting** – removes markdown clutter for natural-sounding speech
- **Graceful fallbacks** – helpful prompts when Alexa doesn't understand
- **No external dependencies** – uses only Python's built-in urllib library

## Prerequisites

- AWS account (for Lambda)
- Amazon Developer account (for Alexa Skill)
- Perplexity API key from [perplexity.ai](https://www.perplexity.ai)

---

# Setup Guide

## 1. Configure AWS Lambda

### Create the Function

1. Go to **AWS Console → Lambda → Create function**
2. Choose these settings:
   - **Author from scratch**
   - **Name:** perplexity-news-agent
   - **Runtime:** Python 3.11 (or 3.10+)
   - **Architecture:** x86_64
3. Click **Create function**

### Deploy the Code

1. Open your Lambda function in the AWS Console
2. Navigate to **Code → lambda_function.py**
3. Replace the default code with `lambda_function.py` from this repository
4. Click **Deploy**

Since this project uses only the standard library, no layers or zip packaging is needed.

### Add Your API Key

1. Go to **Lambda → Configuration → Environment variables**
2. Click **Edit** and add:
   - **Key:** `PERPLEXITY_API_KEY`
   - **Value:** Your Perplexity API key
3. Click **Save**

### Verify Permissions

The default `AWSLambdaBasicExecutionRole` is sufficient—it enables CloudWatch Logs and has no network restrictions (ensure your function isn't in a private subnet without internet access).

---

## 2. Create and Configure the Alexa Skill

### Create the Skill

1. Go to [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Click **Create Skill**
3. Fill in the details:
   - **Skill name:** Perplexity News Agent
   - **Default language:** English (US)
   - **Model:** Custom
   - **Backend:** Provision your own / AWS Lambda ARN
4. Click **Create skill**

### Set the Invocation Name

1. Go to **Build → Invocation**
2. Set **Invocation name** to: `perplexity news agent` (lowercase, no special characters)

Users will invoke your skill like this:
- "Alexa, open perplexity news agent"
- "Alexa, ask perplexity news agent what's new in OpenAI today"

### Create the Intent and Slot

1. Go to **Build → Interaction Model → Intents**
2. Click **Add Intent → Create custom intent**
3. Name it: `GeneralSearchIntent`

**Add the Slot:**
- Click **Add Slot**
- **Slot name:** `query`
- **Slot type:** `AMAZON.SearchQuery`

**Add Sample Utterances:**

Include at least these phrases (add more for better recognition):

```
get me {query}
what is {query}
to get me {query}
tell me what's latest on {query}
what is latest about {query}
tell me news on {query}
find details about {query}
search about {query}
search for {query}
tell me the latest about {query}
what is the news about {query}
give me updates on {query}
what's happening with {query}
what is new in {query} today
what is new in {query}
tell me what is new in {query}
give me news on {query}
what's new with {query}
what is the latest news on {query}
updates about {query}
latest updates about {query}
news about {query}
```

**Pro tip:** Make sure your utterances match the phrases you actually speak. If you say "what is new in openai today," you need an utterance like `what is new in {query} today`.

### Configure Dialog and Built-in Intents

1. For **GeneralSearchIntent**, set **Dialog delegation** to **Skill handles dialog**
2. Keep these built-in intents (no changes needed):
   - AMAZON.HelpIntent
   - AMAZON.CancelIntent
   - AMAZON.StopIntent
   - AMAZON.FallbackIntent

### Connect Lambda to Alexa

1. Go to **Build → Endpoint**
2. Select **AWS Lambda ARN**
3. Paste your Lambda function's ARN in the **Default Region** field:
   ```
   arn:aws:lambda:us-east-1:123456789012:function:perplexity-news-agent
   ```
   (Replace the account ID and region with your own)
4. Click **Save**

### Build the Skill

1. Click **Save Model** (top bar)
2. Click **Build Model**
3. Wait for the build to complete

---

## 3. Support Multiple Locales (Important!)

A common issue: your device uses English (India) but the skill only has English (US). It works in the simulator but not on your device.

### Add English (India) to Your Skill

1. In the **Alexa Developer Console**, open your skill
2. Use the **language dropdown** (top-left) → **Add new language**
3. Select **English (IN)**
4. Choose **Copy from English (US)**
5. With English (IN) selected, click **Build Model** again

### Set Your Device to English (India)

1. Open the **Alexa App** on your phone or Echo
2. Go to **Devices → [Your device] → Settings → Language**
3. Select **English (India)**
4. If it was already set to English (India), toggle it to English (US) then back to force a refresh

---

## 4. Test Your Skill

### In the Developer Console

1. Go to the **Test** tab
2. Set **Test is enabled for this skill** to **Development**
3. Try these phrases:
   - "open perplexity news agent"
   - "ask perplexity news agent what's new in OpenAI today"
   - "ask perplexity news agent give me updates on Airbus"

You should see the request JSON (with your intent and query slot) and response JSON (with Perplexity's answer).

### On Your Device

1. Ensure the skill is enabled:
   - Open **Alexa App → More → Skills & Games → Your Skills → Dev Skills**
   - Find your skill and verify it's enabled
2. Say: "Alexa, open perplexity news agent"
3. Alexa should respond with a greeting
4. Ask: "What's new in OpenAI today"

---

## 5. Troubleshooting

### Alexa says "I'm not quite sure how to help with that"

**Likely cause:** The skill isn't being invoked.

**Checklist:**
- ✅ Is the skill enabled in your Alexa App (Skills & Games → Dev Skills)?
- ✅ Are you using the exact invocation name? Check **Build → Invocation Name** and use that exact phrase.
- ✅ Is there a locale mismatch? Add English (India) to your skill and rebuild if your device uses that locale.

### Lambda shows AMAZON.FallbackIntent instead of GeneralSearchIntent

**Cause:** Alexa didn't match your spoken phrase to your intent.

**Solution:**
- Review your sample utterances—do they match what you actually say?
- If you say "what is new in openai today," make sure you have an utterance like `what is new in {query} today`
- Rebuild the model after making changes

### Lambda response says "I didn't get the topic"

**Cause:** The `query` slot wasn't extracted.

**Solution:**
- Verify the slot is named `query` and type is `AMAZON.SearchQuery`
- Ensure utterances include `{query}`
- Rebuild the model

### "No module named 'requests'" Error

This project uses only `urllib` to avoid packaging issues. If you see this error, either switch to `urllib` or package `requests` in a deployment zip or Lambda layer.

### "Authentication with Perplexity failed" or 401 Errors

**Solution:**
- Check your `PERPLEXITY_API_KEY` in Lambda environment variables
- Confirm the key is valid and hasn't expired
- Ensure there's no extra whitespace in the key value

---

## 6. Response Formatting

Perplexity often returns markdown-formatted responses with bullets, bold text, and headers. The Lambda function's `clean_text()` function automatically:

- Strips markdown characters: `*`, `_`, `#`, backticks, `[]`, `()`
- Removes line breaks and collapses multiple spaces
- Truncates very long responses (~700 characters) to keep Alexa responses concise
- Produces natural, spoken-word output

### Customizing Output

You can modify the `clean_text()` function to:
- Add prefixes like "Here's what I found…"
- Convert bullet points to spoken lists ("First…, Second…")
- Add SSML for advanced speech formatting
- Adjust the character limit based on your preference

---

## Architecture Overview

```
┌─────────────────┐
│ Alexa Device    │
│ (Echo / App)    │
└────────┬────────┘
         │
┌────────▼────────────────────┐
│ Alexa Skill                 │
│ (Custom Intent + Slots)     │
└────────┬────────────────────┘
         │
┌────────▼────────────────────┐
│ AWS Lambda (Python)         │
│ - Extracts query            │
│ - Calls Perplexity API      │
│ - Cleans response           │
└────────┬────────────────────┘
         │
┌────────▼────────────────────┐
│ Perplexity AI               │
│ (/chat/completions)         │
│ sonar-pro model             │
└─────────────────────────────┘
```
