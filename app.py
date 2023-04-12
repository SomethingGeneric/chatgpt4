import os
import random
import markdown
import nltk
import json
import toml
from flask import Flask, request, render_template
import openai

app = Flask(__name__)

# Download the words corpus if necessary
nltk.download("words")

if not os.path.exists("history"):
    os.makedirs("history")

openai.api_key = open(".key").read().strip()


# Generate random conversation ID for each new conversation
def generate_conversation_id():
    # Choose three random words from the corpus
    words = random.choices(nltk.corpus.words.words(), k=3)
    # Join the words with hyphens
    conversation_id = "-".join(words)
    return conversation_id


# Load conversation history from disk if there is any
def load_conversation_history(conversation_id, format="json"):
    history_path = f"history/{conversation_id}.{format}"
    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            if format == "json":
                return json.load(f)
            elif format == "toml":
                return toml.load(f)
    else:
        return []


# Save conversation history to disk
def save_conversation_history(conversation_id, history, format="json"):
    history_path = f"history/{conversation_id}.{format}"
    with open(history_path, "w") as f:
        if format == "json":
            json.dump(history, f)
        elif format == "toml":
            toml.dump(history, f)


@app.route("/", methods=["GET", "POST"])
def nconvo():
    if request.method == "POST":
        # Load conversation history from disk if there is any
        conversation_id = request.form["conversation_id"]
        history = load_conversation_history(conversation_id)
        input_string = request.form["input_string"]
        oaih = [
            {
                "role": "system",
                "content": "You're answering questions from unknown users. Feel free to use formatting, and follow their instructions to the best of your ability.",
            }
        ]
        if history != []:
            for message in history:
                if message["role"] == "user":
                    oaih.append({"role": "user", "content": message["content"]})
                elif message["role"] == "assistant":
                    oaih.append(
                        {"role": "assistant", "content": message["content"]}
                    )
        oaih.append({"role": "user", "content": input_string})
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=oaih,
        )
        bot_output = response["choices"][0]["message"]["content"]
        # Convert markdown to HTML
        output_html = markdown.markdown(bot_output)
        # Append input and output to conversation history
        history.append({"role": "user", "content": input_string})
        history.append({"role": "assistant", "content": output_html})
        # Save conversation history to disk
        save_conversation_history(conversation_id, history)
    else:
        # Generate a new conversation ID for each new conversation
        history = []
        conversation_id = generate_conversation_id()
        output_html = ""

    # Render template with conversation ID and history
    return render_template(
        "index.html",
        conversation_id=conversation_id,
        history=history,
        output_html=output_html,
    )

if __name__ == "__main__":
    app.run(debug=True)
