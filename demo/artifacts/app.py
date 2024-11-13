import os
import re
from http import HTTPStatus
from typing import Dict, List, Optional, Tuple
import base64


import dashscope
import gradio as gr
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role

import modelscope_studio.components.base as ms
import modelscope_studio.components.legacy as legacy
import modelscope_studio.components.antd as antd
from config import DEMO_LIST, SystemPrompt

YOUR_API_TOKEN = os.getenv('YOUR_API_TOKEN')
dashscope.api_key = YOUR_API_TOKEN

History = List[Tuple[str, str]]
Messages = List[Dict[str, str]]

def history_to_messages(history: History, system: str) -> Messages:
    messages = [{'role': Role.SYSTEM, 'content': system}]
    for h in history:
        messages.append({'role': Role.USER, 'content': h[0]})
        messages.append({'role': Role.ASSISTANT, 'content': h[1]})
    return messages


def messages_to_history(messages: Messages) -> Tuple[str, History]:
    assert messages[0]['role'] == Role.SYSTEM
    history = []
    for q, r in zip(messages[1::2], messages[2::2]):
        history.append([q['content'], r['content']])
    return history


def remove_code_block(text):
    pattern = r'```html\n(.+?)\n```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return text.strip()

def history_render(history: History):
    return gr.update(open=True), history

def clear_history():
    return []

def send_to_sandbox(code):
    encoded_html = base64.b64encode(code.encode('utf-8')).decode('utf-8')
    data_uri = f"data:text/html;charset=utf-8;base64,{encoded_html}"
    return f"<iframe src=\"{data_uri}\" width=\"100%\" height=\"920px\"></iframe>"
    # return {
    #     '/src/App.jsx': {
    #         'code': code,
    #         'fpath': '/src/App.jsx',
    #     },
    #     # 以路径为 key，必须以绝对路径来描述
    #     '/src/index.js': {
    #         'code':
    #         'import React from "react"; import ReactDOM from "react-dom"; import App from "./App"; const rootElement = document.getElementById("root"); ReactDOM.render(<App />, rootElement);',
    #         'fpath': '/src/index.js',
    #     },
    #     '/package.json': {
    #         'code': '{"name":"demo", "main": "./src/index.js", "dependencies":{ "react": "18.3.1", "react-dom": "18.3.1", "antd": "5.21.6", "styled-components": "6.1.13" }}',
    #         'fpath': '/package.json',
    #     },
    # }

def demo_card_click(e: gr.EventData):
    index = e._data['component']['index']
    return DEMO_LIST[index]['description']

with gr.Blocks(css_paths="app.css") as demo:
    history = gr.State([])
    setting = gr.State({
        "system": SystemPrompt,
    })

    with ms.Application() as app:
        with antd.ConfigProvider():
            with antd.Row(gutter=[32, 12]) as layout:
                with antd.Col(span=24, md=8):
                    with antd.Flex(vertical=True, gap="middle", wrap=True):
                        header = gr.HTML("""
                                  <div class="left_header">
                                   <img src="//img.alicdn.com/imgextra/i2/O1CN01KDhOma1DUo8oa7OIU_!!6000000000220-1-tps-240-240.gif" width="200px" />
                                   <h1>Qwen2.5-Coder</h2>
                                  </div>
                                   """)
                        input = antd.InputTextarea(
                            size="large", allow_clear=True, placeholder="Please enter what kind of application you want")
                        # input = gr.TextArea(placeholder="请输入您想要一个什么样的应用", show_label=False, container=False)
                        btn = antd.Button("send", type="primary", size="large")
                        clear_btn = antd.Button("clear history", type="default", size="large")

                        antd.Divider("examples")
                        with antd.Flex(gap="small", wrap=True):
                            with ms.Each(DEMO_LIST):
                              with antd.Card(hoverable=True, as_item="card") as demoCard:
                                antd.CardMeta()
                              demoCard.click(demo_card_click, outputs=[input])

                        antd.Divider("setting")

                        with antd.Flex(gap="small", wrap=True):
                            settingPromptBtn = antd.Button(
                                "⚙️ set system Prompt", type="default")
                            codeBtn = antd.Button("🧑‍💻 view code", type="default")
                            historyBtn = antd.Button("📜 history", type="default")

                    with antd.Modal(open=False, title="set system Prompt", width="800px") as system_prompt_modal:
                        systemPromptInput = antd.InputTextarea(
                            SystemPrompt, auto_size=True)

                    settingPromptBtn.click(lambda: gr.update(
                        open=True), inputs=[], outputs=[system_prompt_modal])
                    system_prompt_modal.ok(lambda input: ({"system": input}, gr.update(
                        open=False)), inputs=[systemPromptInput], outputs=[setting, system_prompt_modal])
                    system_prompt_modal.cancel(lambda: gr.update(
                        open=False), outputs=[system_prompt_modal])

                    with antd.Drawer(open=False, title="code", placement="left", width="750px") as code_drawer:
                        code_output = legacy.Markdown()

                    codeBtn.click(lambda: gr.update(open=True),
                                  inputs=[], outputs=[code_drawer])
                    code_drawer.close(lambda: gr.update(
                        open=False), inputs=[], outputs=[code_drawer])

                    with antd.Drawer(open=False, title="history", placement="left", width="900px") as history_drawer:
                        history_output = legacy.Chatbot(show_label=False, flushing=False, height=960, elem_classes="history_chatbot")

                    historyBtn.click(history_render, inputs=[history], outputs=[history_drawer, history_output])
                    history_drawer.close(lambda: gr.update(
                        open=False), inputs=[], outputs=[history_drawer])

                with antd.Col(span=24, md=16):
                    with ms.Div(elem_classes="right_panel"):
                        gr.HTML('<div class="render_header"><span class="header_btn"></span><span class="header_btn"></span><span class="header_btn"></span></div>')
                        with antd.Tabs(active_key="empty", render_tab_bar="() => null") as state_tab:
                            with antd.Tabs.Item(key="empty"):
                                empty = antd.Empty(description="empty input", elem_classes="right_content")
                                with antd.Tabs.Item(key="loading"):
                                    loading = antd.Spin(True, tip="coding...", size="large", elem_classes="right_content")
                                with antd.Tabs.Item(key="render"):
                                    sandbox = gr.HTML(elem_classes="html_content")
                                # sandbox = pro.FrontendCodeSandbox(elem_style={
                                #   'height': '920px',
                                #   'width': '100%'
                                # })

            def generation_code(query: Optional[str], _setting: Dict[str, str], _history: Optional[History]):
              if query is None:
                  query = ''
              if _history is None:
                  _history = []
              messages = history_to_messages(_history, _setting['system'])
              messages.append({'role': Role.USER, 'content': query})

              gen = Generation.call(model="qwen2.5-coder-32b-instruct",
                                    messages=messages,
                                    result_format='message',
                                    stream=True)
              for response in gen:
                  if response.status_code == HTTPStatus.OK:
                      role = response.output.choices[0].message.role
                      content = response.output.choices[0].message.content
                      if response.output.choices[0].finish_reason == 'stop':
                        _history = messages_to_history(messages + [{
                            'role': role,
                            'content': content
                        }])
                        print('history')
                        print(_history)
                        yield {
                            code_output: content,
                            history: _history,
                            sandbox: send_to_sandbox(remove_code_block(content)),
                            state_tab:  gr.update(active_key="render"),
                            code_drawer:  gr.update(open=False),
                        }
                      else:
                        yield {
                            code_output: content,
                            state_tab:  gr.update(active_key="loading"),
                            code_drawer: gr.update(open=True),
                        }                      
                  else:
                      raise ValueError(
                          'Request id: %s, Status code: %s, error code: %s, error message: %s'
                          % (response.request_id, response.status_code, response.code,
                            response.message))

            btn.click(generation_code,
                      inputs=[input, setting, history],
                      outputs=[code_output, history, sandbox, state_tab, code_drawer])
            
            clear_btn.click(clear_history, inputs=[], outputs=[history])

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=20).launch(ssr_mode=False)
