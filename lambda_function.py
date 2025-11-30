"""
Alexa → AWS Lambda → Perplexity Chat Completions

This Lambda is used as the backend for an Alexa skill that answers
general questions using Perplexity's /chat/completions API.

- No external libraries required (uses urllib from the standard library)
- Cleans markdown and line breaks for Alexa-friendly speech
- Handles LaunchRequest + IntentRequest
- Robust slot extraction with fallback
"""

import json
import os
import re
import urllib.request
import urllib.error

# Set this environment variable in Lambda configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Perplexity model you want to use
PERPLEXITY_MODEL = "sonar-pro"


def clean_text(text: str) -> str:
    """
    Clean AI output to make it Alexa-friendly:
    - strip markdown (*, _, `, #, [ ], ( ))
    - remove line breaks
    - collapse extra spaces
    - optionally limit length
    """
    if not text:
        return text

    # Remove common markdown formatting characters
    text = re.sub(r"\*", "", text)            # bold / list bullets
    text = re.sub(r"_", "", text)             # italics
    text = re.sub(r"`+", "", text)            # code backticks
    text = re.sub(r"#+", "", text)            # headers like ### Title
    text = re.sub(r"\[|\]", "", text)         # [link text]
    text = re.sub(r"\(|\)", "", text)         # (urls) or (extra info)

    # If Perplexity returns bullets with "- something"
    # remove leading dash + space at line starts
    text = re.sub(r"^\s*-\s*", "", text, flags=re.MULTILINE)

    # Replace newlines with space
    text = text.replace("\n", " ")

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Limit text length so Alexa doesn't drone on forever
    max_len = 700
    if len(text) > max_len:
        text = text[:max_len].rstrip() + "... Let me know if you want more."

    return text


def extract_query(event):
    """
    Try to extract the 'query' text from an Alexa IntentRequest.
    - Primary: slot named 'query' / 'Query'
    - Fallback: first slot that has a value
    Returns:
        query_text (str) or None
    """
    request = event.get("request", {})
    if request.get("type") != "IntentRequest":
        return None

    intent = request.get("intent", {})
    slots = intent.get("slots", {}) or {}

    # 1) Try explicit 'query' slot first
    for key in ("query", "Query"):
        slot = slots.get(key)
        if slot and slot.get("value"):
            return slot["value"]

    # 2) Fallback: first slot with a value
    for slot_name, slot in slots.items():
        value = slot.get("value")
        if value:
            return value

    return None


def call_perplexity(query: str) -> str:
    """
    Call Perplexity's /chat/completions endpoint with the given query.
    Returns cleaned text suitable for Alexa to speak.
    """
    if not PERPLEXITY_API_KEY:
        # Fail fast if API key is missing
        return (
            "Perplexity API key is not configured. "
            "Please set the PERPLEXITY_API_KEY environment variable in Lambda."
        )

    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "user",
                "content": query,
            }
        ],
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            raw = res.read().decode("utf-8")
            response_json = json.loads(raw)

        # Perplexity-style response:
        # {
        #   "choices": [
        #       {
        #           "message": { "content": "..." },
        #           ...
        #       }
        #   ]
        # }
        choices = response_json.get("choices") or []
        if not choices:
            return "I couldn't get a useful response from Perplexity."

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            return "Perplexity didn't return any content for this question."

        return clean_text(content)

    except urllib.error.HTTPError as e:
        # Log details for debugging
        print("HTTPError calling Perplexity:", e.code, e.reason)
        try:
            body = e.read().decode("utf-8")
            print("Error body:", body)
        except Exception:
            pass
        if e.code == 401:
            return "Authentication with Perplexity failed. Please check your API key."
        return "I had a problem contacting Perplexity."

    except urllib.error.URLError as e:
        print("URLError calling Perplexity:", str(e))
        return "I couldn't reach Perplexity right now. Please try again."

    except Exception as e:
        print("Unexpected error calling Perplexity:", str(e))
        return "Something went wrong while processing your request."


def handler(event, context):
    """
    Main Lambda entrypoint for Alexa Skills Kit.
    Handles:
    - LaunchRequest: "Alexa, open <invocation name>"
    - IntentRequest: "Alexa, ask <invocation name> ..."

    Returns Alexa-compatible JSON response.
    """
    # Log the full event for debugging in CloudWatch (helpful for readers)
    print("Incoming event:", json.dumps(event))

    request = event.get("request", {})
    request_type = request.get("type")

    # 1) LaunchRequest: user just opens the skill
    if request_type == "LaunchRequest":
        return speak(
            "Hi, I'm your Perplexity news agent. "
            "Ask me something like: what's the latest about OpenAI today?"
        )

    # 2) IntentRequest: user asked something specific
    if request_type == "IntentRequest":
        intent = request.get("intent", {})
        intent_name = intent.get("name", "")

        # If Alexa couldn't match our custom intent, it may send AMAZON.FallbackIntent
        if intent_name == "AMAZON.FallbackIntent":
            return speak(
                "I didn't quite catch that. "
                "Try saying something like: tell me the latest about OpenAI."
            )

        query = extract_query(event)
        if not query:
            # No slot or empty slot (common modeling mistake)
            return speak(
                "I didn't get the topic. "
                "Try saying: tell me the latest about OpenAI."
            )

        reply = call_perplexity(query)
        return speak(reply)

    # 3) Any other request types (SessionEndedRequest, etc.)
    return speak("Goodbye.")


def speak(text: str):
    """
    Helper to build an Alexa Skill Kit v1 response.
    """
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text,
            },
            # Keep session open so user can follow up if they want
            "shouldEndSession": False,
        },
    }
