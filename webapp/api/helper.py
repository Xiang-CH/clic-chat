from .prompts import getQueryRewritePrompt




def get_search_query(llm_client, model, history):
    message = "".join([msg_part['text'] for msg_part in history[-1]["content"] if msg_part["type"] == "text"])
    conversation = "\n".join([f"{msg['role']}: {''.join([msg_part['text'] for msg_part in msg['content'] if 'text' in msg_part])}" for msg in history]) if history else "No conversation history."

    user_message = "### Conversation History\n" + conversation + "\n\n### New User Message\n" + message

    complete_message = llm_client.chat.completions.create(
        model=model,
        temperature=0.01,
        messages=[{"role": "system", "content": getQueryRewritePrompt()}] + [{"role": "user", "content": user_message}],
    )

    return complete_message.choices[0].message.content


