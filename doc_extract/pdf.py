import pdfplumber
from pdf2image import convert_from_path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure, LTRect
from PIL import Image
import pytesseract
import os
from doc_extract.images_descriptions import ImageExtractions

class PdfExtraction:
    def __init__(self):
        """
        Инициализирует класс FeatureExtraction.
        """
        pass  # Пустой конструктор, так как класс не требует инициализации специфичных атрибутов

    def text_extraction(self, element):
        """
        Извлекает текст и форматы текста из элемента LTTextContainer.
        :param element: Элемент страницы (LTTextContainer)
        :return: Кортеж (текст, список уникальных форматов)
        """
        # Извлекаем текст из переданного элемента
        line_text = element.get_text()
        # Создаём список для хранения форматов текста (шрифт и размер)
        line_formats = []
        # Перебираем строки текста в элементе
        for text_line in element:
            # Проверяем, является ли строка текстовым контейнером
            if isinstance(text_line, LTTextContainer):
                # Перебираем символы в строке
                for character in text_line:
                    # Проверяем, является ли объект символом
                    if isinstance(character, LTChar):
                        # Добавляем название шрифта и его размер в список форматов
                        line_formats.append((character.fontname, character.size))
        # Создаём список уникальных форматов, удаляя дубликаты
        format_per_line = list(set(line_formats))
        # Возвращаем кортеж из текста и списка форматов
        return (line_text, format_per_line)

    def convert_to_images(self, input_file, page_num):
        """
        Преобразует указанную страницу PDF в изображение.
        :param input_file: Путь к PDF-файлу
        :param page_num: Номер страницы (начинается с 0)
        :return: Путь к сохранённому изображению или None в случае ошибки
        """
        # Преобразуем указанную страницу PDF в изображение с помощью pdf2image
        images = convert_from_path(input_file, first_page=page_num + 1, last_page=page_num + 1)
        # Проверяем, получены ли изображения
        if images:
            # Формируем имя выходного файла для изображения
            output_file = f"images/PDF_image_page_{page_num}.png"
            # Сохраняем первое изображение в формате PNG
            images[0].save(output_file, "PNG")
            # Возвращаем путь к сохранённому изображению
            return output_file
        # Возвращаем None, если изображение не было создано
        return None

    def image_to_text(self, image_path):
        """
        Извлекает текст из изображения с помощью OCR (pytesseract).
        :param image_path: Путь к файлу изображения
        :return: Извлечённый текст или пустая строка в случае ошибки
        """
        # Проверяем, существует ли файл изображения
        if not os.path.exists(image_path):
            # Возвращаем пустую строку, если файл не найден
            return ""
        # Открываем изображение с помощью PIL
        img = Image.open(image_path)
        # Извлекаем текст из изображения с поддержкой русского и английского языков
        text = pytesseract.image_to_string(img, lang='rus+eng')
        # Возвращаем извлечённый текст
        return text

    def extract_table(self, pdf_path, page_num, table_num):
        """
        Извлекает таблицу с указанной страницы PDF.
        :param pdf_path: Путь к PDF-файлу
        :param page_num: Номер страницы (начинается с 0)
        :param table_num: Номер таблицы на странице
        :return: Данные таблицы или None в случае ошибки
        """
        try:
            # Открываем PDF-файл с помощью pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                # Проверяем, существует ли страница с указанным номером
                if page_num < len(pdf.pages):
                    # Получаем указанную страницу
                    table_page = pdf.pages[page_num]
                    # Извлекаем все таблицы на странице
                    tables = table_page.extract_tables()
                    # Проверяем, существует ли таблица с указанным номером
                    if table_num < len(tables):
                        # Возвращаем данные указанной таблицы
                        return tables[table_num]
                # Возвращаем None, если страница или таблица не найдены
                return None
        except Exception as e:
            # Выводим сообщение об ошибке при извлечении таблицы
            print(f"Ошибка при извлечении таблицы: {e}")
            # Возвращаем None в случае ошибки
            return None

    def table_converter(self, table):
        """
        Преобразует таблицу в текстовый формат с разделителями '|'.
        :param table: Данные таблицы
        :return: Строковое представление таблицы или пустая строка, если таблица пуста
        """
        # Проверяем, передана ли таблица
        if not table:
            return ""
        # Создаём пустую строку для хранения текстового представления таблицы
        table_string = ''
        # Перебираем строки таблицы
        for row_num in range(len(table)):
            # Получаем данные текущей строки
            row = table[row_num]
            # Очищаем данные: заменяем '\n' на пробелы, None на 'None'
            cleaned_row = [item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item in row]
            # Формируем строку таблицы с разделителями '|'
            table_string += '|' + '|'.join(cleaned_row) + '|\n'
        # Удаляем последний перенос строки и возвращаем результат
        return table_string.rstrip('\n')

def extract_pages_pdf(pdf_path):
    """
    Обрабатывает страницы PDF-файла, извлекая текст, таблицы и изображения.
    :param pdf_path: Путь к PDF-файлу
    :return: Строку с извлечёнными данными (текст, форматы, таблицы, текст и описания изображений)
    """
    # Перебираем страницы PDF-файла с помощью pdfminer
    for pagenum, page in enumerate(extract_pages(pdf_path)):
        # Создаём экземпляр класса FeatureExtraction для обработки элементов страницы
        extract = PdfExtraction()
        # Выводим сообщение о начале обработки текущей страницы
        print(f"\nОбработка страницы {pagenum + 1}:")
        # Создаём пустую строку для хранения данных страницы
        features = ''

        # Инициализируем счётчик таблиц на странице
        table_num = 0

        # Итеративно обходим элементы страницы
        for element in page:
            # Извлечение текста и форматов
            if isinstance(element, LTTextContainer):
                # Извлекаем текст и форматы текста из элемента
                (line_text, format_per_line) = extract.text_extraction(element)
                # Добавляем текст в результирующую строку
                features += f"Текст: {line_text.strip()}"
                # Добавляем форматы текста в результирующую строку
                features += f"Форматы: {format_per_line}"

            # Извлечение изображений и их описаний
            if isinstance(element, LTFigure):
                # Конвертируем страницу PDF в изображение
                image_path = extract.convert_to_images(pdf_path, pagenum)
                # Создаём экземпляр ImageExtractions для получения описания изображения
                image_extraction = ImageExtractions(image_path)
                # Проверяем, было ли создано изображение
                if image_path:
                    # Извлекаем текст из изображения с помощью OCR
                    text_from_image = extract.image_to_text(image_path)
                    # Добавляем текст из изображения в результирующую строку
                    features += f"Текст из изображения: {text_from_image.strip()}"
                    # Получаем описание изображения с помощью метода gpt_describe и добавляем его
                    features += f"Описание изображения: {image_extraction.gpt_describe()}"

            # Извлечение таблиц
            if isinstance(element, LTRect):
                # Проверяем, есть ли таблица на этой странице
                table = extract.extract_table(pdf_path, pagenum, table_num)
                # Если таблица найдена
                if table:
                    # Преобразуем таблицу в текстовый формат
                    table_string = extract.table_converter(table)
                    # Выводим таблицу с номером
                    print(f"Таблица {table_num + 1}:\n{table_string}")
                    # Добавляем таблицу в результирующую строку
                    features += f"Таблица {table_num + 1}:\n{table_string}"
                    # Увеличиваем счётчик таблиц
                    table_num += 1

        # Возвращаем строку с извлечёнными данными для текущей страницы
    return features