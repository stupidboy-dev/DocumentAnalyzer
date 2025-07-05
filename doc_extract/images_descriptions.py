import os
import base64
from g4f.client import Client

class ImageExtractions:
    def __init__(self, image_path):
        """
        Инициализирует класс с путём к изображению.
        :param image_path: Путь к файлу изображения
        """
        self.image_path = image_path  # Сохраняем путь к изображению
        self.client = Client()  # Инициализируем клиент g4f для взаимодействия с AI
        self.prompt = """
            Опиши изображение из документа максимально подробно, чтобы другая модель могла использовать описание для анализа. Включи следующие аспекты:
            1. Основные объекты: перечисли все видимые объекты, их форму, размер и расположение.
            2. Текст: извлеки весь текст на изображении, включая шрифт, размер и расположение.
            3. Цвета: опиши основные цвета объектов, фона и других элементов.
            4. Композиция: опиши расположение элементов относительно друг друга (например, центр, края, перекрытия).
            5. Фон: опиши фон изображения (однотонный, пейзаж, текстура и т.д.).
            6. Контекст: предположи назначение изображения (например, диаграмма, фотография, таблица).
            7. Дополнительные детали: любые уникальные элементы, такие как символы, логотипы, узоры.
            Организуй ответ по этим пунктам в виде структурированного текста. Укажи, если какие-то элементы отсутствуют. Изображение находится в документе (PDF или .docx), и твоё описание критически важно для успеха последующего анализа.
            """

    def encode_image(self):
        """
        Кодирует изображение в формат base64.
        :return: Строка base64 или None в случае ошибки
        """
        if not os.path.exists(self.image_path):
            print(f"Ошибка: Файл {self.image_path} не найден")
            return None
        try:
            with open(self.image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{image_base64}"
        except Exception as e:
            print(f"Ошибка при кодировании изображения: {e}")
            return None

    def gpt_describe(self, model="gpt-4o-mini", detail="high"):
        """
        Получает подробное описание изображения с помощью модели GPT.
        :param model: Название модели (по умолчанию gpt-4o-mini)
        :param detail: Уровень детализации (low, high, auto)
        :return: Описание изображения или строка с ошибкой
        """
        if not os.path.exists(self.image_path):
            print(f"Ошибка: Файл {self.image_path} не найден")
            return "Изображение не найдено"

        # Кодируем изображение
        image_url = self.encode_image()
        if not image_url:
            return "Ошибка при кодировании изображения"

        try:
            # Отправляем запрос к модели
            response = self.client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": detail
                            }
                        }
                    ]
                }],
                web_search=True
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка при запросе к модели GPT: {e}")
            return f"Ошибка при описании изображения: {e}"