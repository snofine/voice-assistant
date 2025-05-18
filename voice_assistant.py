import os
import asyncio
import aiohttp
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
import re

# Загрузка переменных окружения
load_dotenv()

class VoiceAssistant:
    def __init__(self):
        self.api_token = os.getenv('API_TOKEN')
        if not self.api_token:
            raise ValueError("API_TOKEN не найден в .env файле")
            
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        
        # Настройка голоса
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[0].id)  # Используем первый доступный голос
        self.engine.setProperty('rate', 150)  # Скорость речи

    def remove_markdown(self, text):
        # Удаление блоков кода (в т.ч. многострочных)
        text = re.sub(r'`{1,3}.*?`{1,3}', '', text, flags=re.DOTALL)
        # Удаление markdown-ссылок
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Удаление жирного/курсива
        text = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', text)
        # Удаление заголовков (### Текст)
        text = re.sub(r'^\s{0,3}#{1,6}\s*', '', text, flags=re.MULTILINE)
        # Удаление эмодзи
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002700-\U000027BF"  # dingbats
            u"\U0001F900-\U0001F9FF"  # supplemental symbols
            u"\U00002600-\U000026FF"  # misc symbols
            u"\U0001F000-\U0001F02F"  # mahjong tiles
            u"\U0001F0A0-\U0001F0FF"  # playing cards
            u"\U0001F100-\U0001F1FF"  # enclosed alphanumeric supplement
            u"\U0001F200-\U0001F2FF"  # enclosed ideographic supplement
            u"\U0001F300-\U0001F5FF"  # miscellaneous symbols and pictographs
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F680-\U0001F6FF"  # transport and map symbols
            u"\U0001F700-\U0001F77F"  # alchemical symbols
            u"\U0001F780-\U0001F7FF"  # geometric shapes extended
            u"\U0001F800-\U0001F8FF"  # supplemental arrows-c
            u"\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
            u"\U0001FA00-\U0001FA6F"  # chess symbols
            u"\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
            u"\U00002702-\U000027B0"  # dingbats
            u"\U000024C2-\U0001F251"  # enclosed characters
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        # Удаление списков (- пункт)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        # Удаление цитат (> цитата)
        text = re.sub(r'^\s*>+\s?', '', text, flags=re.MULTILINE)
        # Удаление лишних пробелов и переносов строк
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    async def get_ai_response(self, text):
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": "deepseek-ai/DeepSeek-V3-0324",
            "messages": [
                {
                    "role": "user",
                    "content": text
                }
            ],
            "stream": False,
            "max_tokens": 1024,
            "temperature": 0.7
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.chutes.ai/v1/chat/completions",
                headers=headers,
                json=body
            ) as response:
                data = await response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                elif 'error' in data:
                    return f"Ошибка API: {data['error']}"
                else:
                    return "Извините, не удалось получить ответ от API"

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        with sr.Microphone() as source:
            print("Слушаю...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
            
        try:
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            print(f"Вы сказали: {text}")
            return text
        except sr.UnknownValueError:
            print("Не удалось распознать речь")
            return None
        except sr.RequestError:
            print("Ошибка сервиса распознавания речи")
            return None

    async def run(self):
        print("Голосовой помощник запущен. Скажите 'выход' для завершения.")
        self.speak("Голосовой помощник запущен. Чем могу помочь?")

        while True:
            text = self.listen()
            
            if text is None:
                continue
                
            if text.lower() in ['выход', 'пока', 'до свидания']:
                self.speak("До свидания!")
                break

            response = await self.get_ai_response(text)
            clean_response = self.remove_markdown(response)
            print(f"Ответ: {clean_response}")
            self.speak(clean_response)

if __name__ == "__main__":
    assistant = VoiceAssistant()
    asyncio.run(assistant.run()) 