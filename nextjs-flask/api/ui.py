import gradio as gr
from index import search_ord, search_judg

with gr.Blocks() as search:
    with gr.Row():
        top_k = gr.Number(value=10, label="Top K")
        query_type = gr.Radio(["vector", "fts", "hybrid"], value="hybrid", label="Query Type")
    query = gr.Textbox(label="Query Input")
    search_btn = gr.Button("Search")
    with gr.Row():
        with gr.Column():
            ord_output = gr.Textbox(label="Ordinances Output")
        with gr.Column():
            judg_output = gr.Textbox(label="Judgements Output")

    @search_btn.click(inputs=[query, top_k, query_type], outputs=[ord_output, judg_output])
    def search(query, top_k, query_type):
        ord_output = search_ord(query, top_k, query_type)
        judg_output = search_judg(query, top_k, query_type)
        return ord_output, judg_output

with gr.Blocks() as chat:
    name = gr.Textbox(label="Name")
    output = gr.Textbox(label="Output Box")
    greet_btn = gr.Button("Greet")

    @greet_btn.click(inputs=name, outputs=output)
    def greet(name):
        return "Hello " + name + "!"


demo = gr.TabbedInterface(interface_list=[search, chat], tab_names=["Search", "Chat"], title="CLIC-Chat Demo")

if __name__ == "__main__":
    demo.launch()