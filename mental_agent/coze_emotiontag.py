# emotion_analysis.py
"""
情绪分析功能：调用Coze的API接口为输入文本打上情绪标签
"""

import os
import time
import re
from cozepy import Coze, TokenAuth, Message, ChatStatus, COZE_CN_BASE_URL


class EmotionAnalyzer:
    """情绪分析器类"""
    
    def __init__(self, api_token=None, base_url=COZE_CN_BASE_URL):
        """
        初始化情绪分析器
        
        Args:
            api_token: Coze API token，如果为None则使用默认token
            base_url: API基础URL，默认为中国区
        """
        self.api_token = api_token or 'pat_RnKOjeBiPaCgKquixpH5GjEi4Tof8FBpYZV0A1xcXfMDcCv4yTA8rIOPaLXCBh8r'
        self.base_url = base_url
        self.bot_id = '7572844190603395112'
        
        # 初始化Coze客户端
        self.coze = Coze(
            auth=TokenAuth(token=self.api_token),
            base_url=self.base_url
        )
    
    def extract_emotion_tag(self, response_text):
        """
        从响应文本中提取情绪标签
        
        Args:
            response_text: API返回的完整响应文本
            
        Returns:
            str: 提取的情绪标签
        """
        # 查找第一个 { 符号的位置
        json_start_pos = response_text.find('{')
        
        if json_start_pos > 0:
            # 提取 { 符号之前的内容作为情绪标签
            emotion_tag = response_text[:json_start_pos].strip()
            return emotion_tag
        else:
            # 如果没有找到 { 符号，返回整个响应文本
            return response_text.strip()
    
    def analyze_emotion(self, text, user_id='123456789'):
        """
        分析文本情绪
        
        Args:
            text: 要分析的文本
            user_id: 用户ID，默认为'123456789'
            
        Returns:
            dict: 包含分析结果和详细信息的字典
        """
        try:
            print(f"正在分析文本情绪: {text}")
            
            # 调用Coze API
            chat_poll = self.coze.chat.create_and_poll(
                bot_id=self.bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(text),
                ],
            )
            
            # 提取回复内容
            response_text = ""
            for message in chat_poll.messages:
                response_text += str(message.content)
            
            # 提取情绪标签
            emotion_tag = self.extract_emotion_tag(response_text)
            
            # 构建返回结果
            result = {
                'success': True,
                'input_text': text,
                'emotion_analysis': emotion_tag,
                'full_response': response_text,  # 保留完整响应供调试
                'status': chat_poll.chat.status,
                'token_usage': getattr(chat_poll.chat.usage, 'token_count', None) if chat_poll.chat.status == ChatStatus.COMPLETED else None
            }
            
            print("情绪分析完成!")
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'input_text': text,
                'error': str(e),
                'emotion_analysis': None,
                'full_response': None,
                'status': None,
                'token_usage': None
            }
            print(f"情绪分析失败: {e}")
            return error_result


def main():
    """主函数 - 演示使用方法"""
    # 创建情绪分析器实例
    analyzer = EmotionAnalyzer()
    
    # 测试文本列表
    test_texts = [
        "I am going to the park with my friends long time no meet",
        "I feel so sad and lonely today",
        "This is the best day of my life!",
        "I'm really angry about what happened",
        "I don't know how to feel about this situation"
    ]
    
    print("=" * 50)
    print("Coze API 情绪分析演示")
    print("=" * 50)
    
    # 分析每个测试文本
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- 测试案例 {i} ---")
        result = analyzer.analyze_emotion(text)
        
        if result['success']:
            print(f"输入文本: {result['input_text']}")
            print(f"情绪标签: {result['emotion_analysis']}")
            if result['token_usage']:
                print(f"Token使用量: {result['token_usage']}")
        else:
            print(f"分析失败: {result['error']}")
        
        print("-" * 30)
    
    # 用户交互模式
    print("\n" + "=" * 50)
    print("用户交互模式")
    print("输入 'quit' 或 '退出' 结束程序")
    print("=" * 50)
    
    while True:
        user_input = input("\n请输入要分析情绪的文本: ").strip()
        
        if user_input.lower() in ['quit', '退出', 'exit']:
            print("感谢使用情绪分析功能!")
            break
        
        if not user_input:
            print("输入不能为空，请重新输入。")
            continue
        
        # 分析用户输入
        result = analyzer.analyze_emotion(user_input)
        
        if result['success']:
            print(f"\n✅ 情绪标签: {result['emotion_analysis']}")
            if result['token_usage']:
                print(f"📊 Token使用量: {result['token_usage']}")
        else:
            print(f"\n❌ 分析失败: {result['error']}")


if __name__ == "__main__":
    main()