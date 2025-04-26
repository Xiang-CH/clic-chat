import gradio as gr
import json
import os
import glob

# Load the JSON data
def load_json_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Save the JSON data
def save_json_data(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, indent=2, ensure_ascii=False, fp=f)
    return f"Saved to {file_path}"

# Get available JSON files
def get_json_files(directory="eval/checked/"):
    return glob.glob(f"{directory}*.json")

# Default file path
default_file_path = "eval/checked/cap_qa_pairs_gpt4o_.json"
data = load_json_data(default_file_path)
current_file_path = default_file_path

def change_file(file_path):
    global data, current_file_path
    current_file_path = file_path
    data = load_json_data(file_path)
    return f"Loaded file: {file_path}", 0

def update_entry(index, question, url, ordinances_json, contains_cap, contains_hallucination, hallucinated_content):
    global data, current_file_path
    
    try:
        idx = int(index)
        if idx < 0 or idx >= len(data):
            return "Invalid index", data[0]["Answer"], data[0]["tool_response"]
        
        # Parse ordinances JSON
        try:
            ordinances = json.loads(ordinances_json)
        except:
            return "Invalid ordinances JSON format", data[idx]["Answer"], data[idx]["tool_response"]
        
        # Update the entry
        data[idx]["index"] = idx
        data[idx]["Question"] = question
        data[idx]["URL"] = url
        data[idx]["ordinances"] = ordinances
        data[idx]["contains_cap"] = contains_cap == "True"
        data[idx]["contains_hallucination"] = contains_hallucination == "True" if contains_hallucination == "True" else False if contains_hallucination == "False" else None
        data[idx]["hallucinated_content"] = hallucinated_content
        
        # Save the updated data
        save_json_data(data, current_file_path)
        
        return f"Updated entry {idx}", data[idx]["Answer"], data[idx]["tool_response"]
    except Exception as e:
        return f"Error: {str(e)}", data[0]["Answer"], data[0]["tool_response"]

def load_entry(index):
    global data
    try:
        idx = int(index)
        if idx < 0 or idx >= len(data):
            return "Invalid index", "", "", "[]", "False", None, "", "", ""
        
        entry = data[idx]
        ordinances_json = json.dumps(entry.get("ordinances", []), indent=2)
        contains_cap = "True" if entry.get("contains_cap", False) else "False"
        contains_hallucination = "True" if entry.get("contains_hallucination", None) is True else "False" if entry.get("contains_hallucination", None) is False else None
        hallucinated_content = entry.get("hallucinated_content", "")
        
        return f"Loaded entry {idx}", entry.get("Question", ""), entry.get("URL", ""), ordinances_json, contains_cap, contains_hallucination, hallucinated_content, entry.get("Answer", ""), entry.get("tool_response", "")
    except Exception as e:
        return f"Error: {str(e)}", "", "", "[]", "False", None, "", "", ""
    
def prev_entry(index, question, url, ordinances_json, contains_cap, contains_hallucination, hallucinated_content):
    # First save current entry
    update_entry(index, question, url, ordinances_json, contains_cap, contains_hallucination, hallucinated_content)
    
    # Then load previous entry
    new_index = max(0, int(index) - 1)
    return new_index, *load_entry(new_index)

def next_entry(index, question, url, ordinances_json, contains_cap, contains_hallucination, hallucinated_content):
    # First save current entry
    update_entry(index, question, url, ordinances_json, contains_cap, contains_hallucination, hallucinated_content)
    
    # Then load next entry
    global data
    new_index = min(len(data) - 1, int(index) + 1)
    return new_index, *load_entry(new_index)

with gr.Blocks() as demo:
    gr.Markdown("# QA Pair Editor")
    
    with gr.Row():
        file_selector = gr.Dropdown(
            choices=get_json_files(),
            value=default_file_path,
            label="Select JSON File"
        )
        load_btn = gr.Button("Load Entry")
    
    with gr.Row():
        prev_btn = gr.Button("← Previous")
        index_input = gr.Number(label="Index", value=0)
        next_btn = gr.Button("Next →")
        status = gr.Textbox(label="Status")
    
    with gr.Row():
        with gr.Column():
            question = gr.Textbox(label="Question", lines=3)
            url = gr.Textbox(label="URL")
            ordinances = gr.Code(label="Ordinances (JSON)", language="json", lines=5)
            contains_cap = gr.Radio(["True", "False"], label="Contains Cap", value="False")
            contains_hallucination = gr.Radio(["True", "False"], label="Contains Hallucination", value=None)
            hallucinated_content = gr.Textbox(label="Hallucinated Content", lines=3)
            update_btn = gr.Button("Update Entry")
        
        with gr.Column(scale=2):
            with gr.Row():
                answer_md = gr.Markdown(label="Answer")
                tool_response_md = gr.Markdown(label="Tool Response")
    
    # Connect the file selector to change_file function
    file_selector.change(
        change_file,
        inputs=[file_selector],
        outputs=[status, index_input]
    )
    
    # Connect the buttons to functions
    load_btn.click(
        load_entry, 
        inputs=[index_input], 
        outputs=[status, question, url, ordinances, contains_cap, contains_hallucination, hallucinated_content, answer_md, tool_response_md]
    )
    
    update_btn.click(
        update_entry,
        inputs=[index_input, question, url, ordinances, contains_cap, contains_hallucination, hallucinated_content],
        outputs=[status, answer_md, tool_response_md]
    )

    prev_btn.click(
        prev_entry,
        inputs=[index_input, question, url, ordinances, contains_cap, contains_hallucination, hallucinated_content],
        outputs=[index_input, status, question, url, ordinances, contains_cap, contains_hallucination, hallucinated_content, answer_md, tool_response_md]
    )
    
    next_btn.click(
        next_entry,
        inputs=[index_input, question, url, ordinances, contains_cap, contains_hallucination, hallucinated_content],
        outputs=[index_input, status, question, url, ordinances, contains_cap, contains_hallucination, hallucinated_content, answer_md, tool_response_md]
    )

if __name__ == "__main__":
    demo.launch()
