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
            Опиши изображение.
            """

    def compress_image(self, max_size=(512, 512)):
        """
        Сжимает изображение до указанного размера.
        :param max_size: Кортеж (ширина, высота) для максимального размера
        :return: Сжатое изображение в формате bytes
        """
        try:
            with Image.open(self.image_path) as img:
                img = img.convert("RGB")
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG", quality=85)
                return img_byte_arr.getvalue()
        except Exception as e:
            print(f"Ошибка при сжатии изображения: {e}")
            return None

    def encode_image(self):
        """
        Кодирует изображение в формат base64 после сжатия.
        :return: Строка base64 или None в случае ошибки
        """
        if not os.path.exists(self.image_path):
            print(f"Ошибка: Файл {self.image_path} не найден")
            return None
        try:
            image_data = self.compress_image()
            if not image_data:
                return None
            image_base64 = base64.b64encode(image_data).decode('utf-8')
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
                web_search=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка при запросе к модели GPT: {e}")
            return f"Ошибка при описании изображения: {e}"