# app.py

import os
from http.client import HTTPMessage

os.system('pip install dashscope')

import gradio as gr
from http import HTTPStatus
import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role
from typing import List, Optional, Tuple, Dict
from urllib.error import HTTPError

default_system = 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'

YOUR_API_TOKEN = os.getenv('YOUR_API_TOKEN')
dashscope.api_key = YOUR_API_TOKEN

History = List[Tuple[str, str]]
Messages = List[Dict[str, str]]

def clear_session() -> History:
    return '', []

def modify_system_session(system: str) -> str:
    if system is None or len(system) == 0:
        system = default_system
    return system, system, []

def history_to_messages(history: History, system: str) -> Messages:
    messages = [{'role': Role.SYSTEM, 'content': system}]
    for h in history:
        messages.append({'role': Role.USER, 'content': h[0]})
        messages.append({'role': Role.ASSISTANT, 'content': h[1]})
    return messages


def messages_to_history(messages: Messages) -> Tuple[str, History]:
    assert messages[0]['role'] == Role.SYSTEM
    system = messages[0]['content']
    history = []
    for q, r in zip(messages[1::2], messages[2::2]):
        history.append([q['content'], r['content']])
    return system, history


def model_chat(query: Optional[str], history: Optional[History], system: str,
               temperature: float, top_p: float, max_length: int) -> Tuple[str, str, History]:
    if query is None:
        query = ''
    if history is None:
        history = []
    messages = history_to_messages(history, system)
    messages.append({'role': Role.USER, 'content': query})
    gen = Generation.call(
        model="qwen2.5-coder-32b-instruct",
        messages=messages,
        result_format='message',
        stream=True,
        temperature=temperature,
        top_p=top_p,
        max_length=max_length
    )
    for response in gen:
        if response.status_code == HTTPStatus.OK:
            role = response.output.choices[0].message.role
            response = response.output.choices[0].message.content
            system, history = messages_to_history(messages + [{'role': role, 'content': response}])
            yield '', history, system
        else:
            raise HTTPError( code=404, msg='Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                response.request_id, response.status_code,
                response.code, response.message), hdrs=HTTPMessage(), url='http://example.com', fp=None)




def chiose_radio(radio, system):
    mark_ = gr.Markdown(value=f"<center><font size=8>Qwen2.5-Coder-{radio}-instruct👾</center>")
    chatbot = gr.Chatbot(label=f'Qwen2.5-Coder-{radio.lower()}-instruct')
    
    if system is None or len(system) == 0:
        system = default_system
    
    return mark_, chatbot, system, system, ""


def update_other_radios(value, other_radio1, other_radio2):
    if value == "":
        if other_radio1 != "":
            selected = other_radio1
        else:
            selected = other_radio2
        return selected, other_radio1, other_radio2
    return value, "", ""


def main():
    # 创建两个标签
    with gr.Blocks() as demo:
        with gr.Row():
            options_coder = ["0.5B", "1.5B", "3B", "7B", "14B", "32B",]
            with gr.Row():
                radio = gr.Radio(choices=options_coder, label="Qwen2.5-Coder：", value="32B")
                
        with gr.Row():
            with gr.Accordion():
                mark_ = gr.Markdown("""<center><font size=8>Qwen2.5-Coder-32B-Instruct Bot👾</center>""")
                with gr.Row():
                    with gr.Column(scale=3):
                        system_input = gr.Textbox(value=default_system, lines=1, label='System')
                    with gr.Column(scale=1):
                        modify_system = gr.Button("🛠️ Set system prompt and clear history", scale=2)
                    system_state = gr.Textbox(value=default_system, visible=False)
                chatbot = gr.Chatbot(label='Qwen2.5-Coder-32B-Instruct')
                textbox = gr.Textbox(lines=1, label='Input')
                
                with gr.Row():
                    clear_history = gr.Button("🧹 Clear History")
                    sumbit = gr.Button("🚀 Send")
                
                with gr.Accordion("Parameters", open=False):
                    temperature = gr.Slider(minimum=0.0, maximum=1.0, value=0.5, step=0.1, label="Temperature")
                    top_p = gr.Slider(minimum=0.6, maximum=1.0, value=0.9, step=0.05, label="Top P")
                    max_length = gr.Slider(minimum=512, maximum=8192, value=2048, step=128, label="Max Length")

                textbox.submit(model_chat,
                            inputs=[textbox, chatbot, system_state, temperature, top_p, max_length],
                            outputs=[textbox, chatbot, system_input])
                sumbit.click(model_chat,
                             inputs=[textbox, chatbot, system_state, temperature, top_p, max_length],
                             outputs=[textbox, chatbot, system_input],
                             concurrency_limit=100)
                clear_history.click(fn=clear_session,
                                    inputs=[],
                                    outputs=[textbox, chatbot])
                modify_system.click(fn=modify_system_session,
                                    inputs=[system_input],
                                    outputs=[system_state, system_input, chatbot])
        
        radio.change(chiose_radio,
                     inputs=[radio, system_input],
                     outputs=[mark_, chatbot, system_state, system_input, textbox])
    
    demo.queue(api_open=False, default_concurrency_limit=40)
    demo.launch(max_threads=5)


if __name__ == "__main__":
    main()
