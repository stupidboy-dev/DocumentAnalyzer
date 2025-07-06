import pdfplumber
from pdf2image import convert_from_path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure
from PIL import Image
import pytesseract
import os
from doc_extract.images_descriptions import ImageExtractions


class PdfExtraction:
    def __init__(self):
        """Инициализирует класс PdfExtraction."""
        if not os.path.exists('images'):
            os.makedirs('images')

    def text_extraction(self, element):
        """
        Извлекает текст и форматы текста из элемента LTTextContainer.
        """
        line_text = element.get_text()
        line_formats = []

        for text_line in element:
            if isinstance(text_line, LTTextContainer):
                for character in text_line:
                    if isinstance(character, LTChar):
                        line_formats.append((character.fontname, character.size))

        format_per_line = list(set(line_formats))
        return (line_text, format_per_line)

    def convert_page_to_image(self, pdf_path, page_num):
        """
        Конвертирует страницу PDF в изображение.
        ПРОСТОЙ И НАДЕЖНЫЙ МЕТОД.
        """
        try:
            print(f"Конвертирую страницу {page_num + 1} в изображение...")
            images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)

            if images:
                image_path = f"images/page_{page_num + 1}.png"
                images[0].save(image_path, "PNG")
                print(f"Изображение сохранено: {image_path}")
                return image_path
            else:
                print(f"Не удалось конвертировать страницу {page_num + 1}")
                return None

        except Exception as e:
            print(f"Ошибка при конвертации страницы {page_num + 1}: {e}")
            return None

    def image_to_text(self, image_path):
        """Извлекает текст из изображения с помощью OCR."""
        if not os.path.exists(image_path):
            print(f"Файл {image_path} не найден")
            return ""

        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang='rus+eng')
            return text.strip()
        except Exception as e:
            print(f"Ошибка OCR для {image_path}: {e}")
            return ""

    def extract_tables_from_page(self, pdf_path, page_num):
        """Извлекает все таблицы с указанной страницы."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()
                    return tables if tables else []
                return []
        except Exception as e:
            print(f"Ошибка при извлечении таблиц: {e}")
            return []

    def table_to_string(self, table):
        """Преобразует таблицу в текстовый формат."""
        if not table:
            return ""

        table_string = ''
        for row in table:
            cleaned_row = [
                str(item).replace('\n', ' ') if item is not None else 'None'
                for item in row
            ]
            table_string += '|' + '|'.join(cleaned_row) + '|\n'

        return table_string.rstrip('\n')


def extract_pages_pdf(pdf_path):
    """
    ПРОСТАЯ И НАДЕЖНАЯ обработка PDF.
    Для каждой страницы:
    1. Извлекает текст
    2. Если есть изображения (LTFigure) - конвертирует всю страницу
    3. Извлекает таблицы
    """
    extract = PdfExtraction()
    all_pages_data = {}

    for page_num, page in enumerate(extract_pages(pdf_path)):
        print(f"\n=== Обработка страницы {page_num + 1} ===")

        page_data = {
            'text': '',
            'images': [],
            'tables': [],
            'formats': []
        }

        # Флаг для отслеживания наличия изображений
        has_images = False

        # Обрабатываем элементы страницы
        for element in page:
            # Извлекаем текст
            if isinstance(element, LTTextContainer):
                line_text, formats = extract.text_extraction(element)
                page_data['text'] += line_text
                page_data['formats'].extend(formats)

            # Проверяем наличие изображений
            if isinstance(element, LTFigure):
                has_images = True

        # Если есть изображения - конвертируем всю страницу
        if has_images:
            print(f"Обнаружены изображения на странице {page_num + 1}")
            image_path = extract.convert_page_to_image(pdf_path, page_num)

            if image_path and os.path.exists(image_path):
                print(f"Успешно создано изображение: {image_path}")

                # OCR
                ocr_text = extract.image_to_text(image_path)

                # Описание изображения
                try:
                    image_extraction = ImageExtractions(image_path)
                    description = image_extraction.gpt_describe()
                except Exception as e:
                    print(f"Ошибка при получении описания: {e}")
                    description = "Описание недоступно"

                page_data['images'].append({
                    'path': image_path,
                    'ocr_text': ocr_text,
                    'description': description
                })
            else:
                print(f"Не удалось создать изображение для страницы {page_num + 1}")

        # Извлекаем таблицы
        tables = extract.extract_tables_from_page(pdf_path, page_num)
        for i, table in enumerate(tables):
            table_string = extract.table_to_string(table)
            if table_string:
                print(f"Найдена таблица {i + 1}:")
                print(table_string)
                page_data['tables'].append({
                    'number': i + 1,
                    'data': table_string
                })

        # Убираем дубликаты форматов
        page_data['formats'] = list(set(page_data['formats']))

        all_pages_data[page_num + 1] = page_data
        print(f"Страница {page_num + 1} обработана")

    return all_pages_data