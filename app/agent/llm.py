"""
LLM 交互模块
使用 OpenAI SDK 调用大模型，支持 Tool Calling
"""
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.config import get_settings
from app.utils.logging import log
from app.agent.tools import TOOLS_DEFINITIONS, TOOLS_MAP

settings = get_settings()

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base
        )
        self.model = settings.openai_model
        
    def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
        """
        发送聊天请求，支持工具调用
        """
        try:
            log.info(f"发送 LLM 请求 (Model: {self.model})...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto" if tools else None,
                temperature=0.7
            )
            return response.choices[0].message
        except Exception as e:
            log.error(f"LLM 请求失败: {e}")
            raise e

    def process_tool_calls(self, tool_calls: List[Any]) -> List[Dict]:
        """
        处理工具调用请求，执行对应的函数并返回结果消息列表
        """
        messages = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_call_id = tool_call.id
            
            log.info(f"🛠️ LLM 调用工具: {function_name} 参数: {function_args}")
            
            content = ""
            if function_name in TOOLS_MAP:
                try:
                    function_to_call = TOOLS_MAP[function_name]
                    function_response = function_to_call(**function_args)
                    
                    # 将结果转换为 JSON 字符串
                    content = json.dumps(function_response, ensure_ascii=False, default=str)
                except Exception as e:
                    log.error(f"工具执行失败: {e}")
                    content = json.dumps({"error": str(e)}, ensure_ascii=False)
            else:
                content = json.dumps({"error": f"未知工具: {function_name}"}, ensure_ascii=False)
            
            # OpenAI Tool Message 格式
            messages.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": function_name,
                "content": content
            })
            
        return messages

# 全局单例
llm_client = LLMClient()
