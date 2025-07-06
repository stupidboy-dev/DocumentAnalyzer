import os
import base64
from g4f.client import Client
from g4f import Provider
from PIL import Image
import io

class ImageExtractions:
    def __init__(self, image_path):
        self.image_path = image_path
        self.client = Client()
        self.prompt = """
            Опиши изображение подробно.
            """

    def encode_image(self, max_size=(2048, 2048), quality=85):
        """
        Кодирует изображение в формат base64 после сжатия.
        :param max_size: Максимальный размер изображения (ширина, высота)
        :param quality: Качество сжатия JPEG (1-100)
        :return: Строка base64 или None в случае ошибки
        """
        if not os.path.exists(self.image_path):
            print(f"Ошибка: Файл {self.image_path} не найден")
            return None

        try:
            # Открываем изображение
            with Image.open(self.image_path) as image:
                # Конвертируем в RGB если необходимо
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Создаем белый фон для прозрачных изображений
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')

                # Изменяем размер если изображение слишком большое
                if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    print(f"Изображение сжато до размера: {image.size}")

                # Сохраняем в буфер как JPEG
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=quality, optimize=True)
                buffer.seek(0)

                # Кодируем в base64
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return f"data:image/jpeg;base64,{image_base64}"

        except Exception as e:
            print(f"Ошибка при кодировании изображения: {e}")
            return None

    def gpt_describe(self, model="gpt-4.1-nano", detail="low"):
        print(f"Началась обработка: {self.image_path}")
        if not os.path.exists(self.image_path):
            print(f"Ошибка: Файл {self.image_path} не найден")
            return "Изображение не найдено"

        image_url = self.encode_image()
        if not image_url:
            return "Ошибка при кодировании изображения"

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {"type": "image_url", "image_url": {"url": image_url, "detail": detail}}
                    ]
                }],
                web_search=True,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка при запросе к модели GPT: {e}")
            return f"Ошибка при описании изображения: {e}"
