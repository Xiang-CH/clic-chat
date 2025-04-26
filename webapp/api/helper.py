from .utils.prompts import getQueryRewritePrompt, getQueryExpandPrompt, QueryExpandFormat, getTasksPrompt, ConsultTaskFormat
import json

def format_conv_history(history):
    return "\n".join([f"{msg['role']}: {''.join([msg_part['text'] for msg_part in msg['content'] if 'text' in msg_part])}" for msg in history]) if history else "No conversation history."

def get_search_query(llm_client, model, history):
    message = "".join([msg_part['text'] for msg_part in history[-1]["content"] if msg_part["type"] == "text"])
    conversation = format_conv_history(history)

    user_message = "### Conversation History\n" + conversation + "\n\n### New User Message\n" + message

    complete_message = llm_client.chat.completions.create(
        model=model,
        temperature=0.01,
        messages=[{"role": "system", "content": getQueryRewritePrompt()}] + [{"role": "user", "content": user_message}],
    )

    return complete_message.choices[0].message.content

def query_expand(llm_client, model, history):
    conversation = format_conv_history(history)
    user_message = "### Conversation History\n" + conversation

    complete_message = llm_client.beta.chat.completions.parse(
        model=model,
        temperature=0.3,
        messages=[{"role": "system", "content": getQueryExpandPrompt()}] + [{"role": "user", "content": user_message}],
        response_format = QueryExpandFormat
    )

    return complete_message.choices[0].message.parsed.queries

def get_tasks(llm_client, model, history, groundings):
    conversation = format_conv_history(history)
    user_message = "### Conversation History\n" + conversation

    complete_message = llm_client.beta.chat.completions.parse(
        model=model,
        temperature=0.1,
        messages=[{"role": "system", "content": getTasksPrompt(groundings)}] + [{"role": "user", "content": user_message}],
        response_format = ConsultTaskFormat
    )

    return complete_message.choices[0].message.parsed


def process_stream_chunks(stream, available_tools):
    # Track draft tool calls
    draft_tool_calls = []
    draft_tool_calls_index = -1

    for chunk in stream:
        for choice in chunk.choices:
            if choice.delta.content:
                yield f'0:{json.dumps(choice.delta.content)}\n'

            elif choice.finish_reason == "tool_calls":
                for tool_call in draft_tool_calls:
                    yield f'9:{{"toolCallId":"{tool_call["id"]}","toolName":"{tool_call["name"]}","args":{tool_call["arguments"]}}}\n'

                for tool_call in draft_tool_calls:
                    tool_name = tool_call["name"]
                    if tool_name not in available_tools:
                        yield f'9:{{"error":"Tool {tool_name} not found"}}\n'
                        continue
                        
                    tool_result = available_tools[tool_name](**json.loads(tool_call["arguments"]))
                    
                    yield f'a:{{"toolCallId":"{tool_call["id"]}","toolName":"{tool_name}","args":{tool_call["arguments"]},"result":{json.dumps(tool_result)}}}\n'
                    
                # Reset draft tool calls
                draft_tool_calls.clear()
                draft_tool_calls_index = -1
                
            elif choice.delta.tool_calls:
                for tool_call in choice.delta.tool_calls:
                    id = tool_call.id
                    name = tool_call.function.name
                    arguments = tool_call.function.arguments

                    if id is not None:
                        draft_tool_calls_index += 1
                        draft_tool_calls.append(
                            {"id": id, "name": name, "arguments": ""}
                        )
                    else:
                        draft_tool_calls[draft_tool_calls_index]["arguments"] += arguments

            if choice.finish_reason and choice.finish_reason != "tool_calls":
                pass

    if chunk.choices == []:
        if chunk.usage:
            prompt_tokens = chunk.usage.prompt_tokens
            completion_tokens = chunk.usage.completion_tokens
            print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}", flush=True)
            yield f'd:{{"finishReason":"{choice.finish_reason}","usage":{{"promptTokens":{prompt_tokens},"completionTokens":{completion_tokens}}},"isContinued":false}}\n'
        else:
            yield f'd:{{"finishReason":"{choice.finish_reason}"}}\n'