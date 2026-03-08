import sys
import os
import readline # 启用历史记录和行编辑

# 确保项目根目录在 path 中，以便能正确导入 app 模块
# 获取当前脚本所在目录的上一级目录 (即项目根目录)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.agent.workflow import create_agent_graph
from app.utils.logging import log

def main():
    print("="*50)
    print("🤖 股票分析 AI 助手 (CLI)")
    print("输入您的问题，例如：'推荐几只热门股票' 或 '分析贵州茅台'")
    print("输入 'exit' 或 'quit' 退出")
    print("="*50)
    
    # 初始化 Graph
    app = create_agent_graph()
    
    # 维护对话历史
    history = []
    
    while True:
        try:
            user_input = input("\n👤 您: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                print("👋 再见！")
                break
            
            # 构造输入
            if not history:
                inputs = {"query": user_input, "messages": []}
            else:
                history.append({"role": "user", "content": user_input})
                inputs = {"query": user_input, "messages": history}
            
            print("🤖 思考中...", end="", flush=True)
            
            # 运行 graph
            result = app.invoke(inputs)
            
            # 更新 history (result["messages"] 是完整的历史记录)
            history = result["messages"]
            
            # 清除 "思考中..."
            print("\r" + " "*10 + "\r", end="")
            
            last_msg = history[-1]
            
            # 兼容处理：history 中的消息可能是 dict 也可能是 object (ChatCompletionMessage)
            role = ""
            content = ""
            
            if isinstance(last_msg, dict):
                role = last_msg.get("role")
                content = last_msg.get("content")
            else:
                # 假设是对象，尝试属性访问
                role = getattr(last_msg, "role", "")
                content = getattr(last_msg, "content", "")
            
            if role == "assistant":
                 print(f"🤖 AI: {content}")
            else:
                 print(f"🤖 AI (Raw): {last_msg}")
                 
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            log.error(f"CLI Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
