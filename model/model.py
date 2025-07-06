import sys
sys.stdin.reconfigure(encoding='utf-8')

import gradio as gr
import os
from g4f.client import Client
from g4f import Provider
import g4f
from collections import deque
import tkinter as tk
from tkinter import filedialog
from doc_extract.images_descriptions import ImageExtractions
# Импорты для обработки документов
try:
    from doc_extract.pdf import extract_pages_pdf

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Модуль для обработки PDF недоступен")

try:
    from doc_extract.docx import DocxExtracting

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Модуль для обработки DOCX недоступен")


class MainModel_MainModule:
    def __init__(self):
        self.file_path = None
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
        self.supported_document_formats = ['.pdf', '.docx']

    def is_image_file(self, file_path):
        """Проверяет, является ли файл изображением"""
        return os.path.splitext(file_path)[1].lower() in self.supported_image_formats

    def is_document_file(self, file_path):
        """Проверяет, является ли файл документом"""
        return os.path.splitext(file_path)[1].lower() in self.supported_document_formats

    def content(self):
        """Обрабатывает содержимое файла в зависимости от его типа"""
        if not self.file_path:
            return "Файл не выбран"

        file_ext = os.path.splitext(self.file_path)[1].lower()

        # Обработка изображений
        if self.is_image_file(self.file_path):
            print("Обнаружено изображение, начинаю обработку...")
            image_processor = ImageExtractions(self.file_path)
            return image_processor.gpt_describe()

        # Обработка документов
        elif file_ext == '.pdf':
            print("Обнаружен PDF документ, начинаю обработку...")
            if PDF_AVAILABLE:
                try:
                    return extract_pages_pdf(self.file_path)
                except Exception as e:
                    return f"Ошибка при обработке PDF: {str(e)}"
            else:
                return "Обработка PDF недоступна (модуль doc_extract.pdf не найден)"

        elif file_ext == '.docx':
            print("Обнаружен DOCX документ, начинаю обработку...")
            if DOCX_AVAILABLE:
                try:
                    docx = DocxExtracting(self.file_path)
                    return docx.make_description()
                except Exception as e:
                    return f"Ошибка при обработке DOCX: {str(e)}"
            else:
                return "Обработка DOCX недоступна (модуль doc_extract.docx не найден)"

        else:
            return f"Неподдерживаемый формат файла: {file_ext}"

    file_input = gr.File(type="filepath")

    def upload(self, path: str):
        self.file_path = path
        return os.path.basename(path)

    def choose_file(self):
        """Открывает диалоговое окно для выбора файла"""
        root = tk.Tk()
        root.withdraw()  # Скрываем главное окно Tkinter

        # Создаем фильтры для типов файлов
        filetypes = [
            ('Все поддерживаемые', '*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.tiff;*.webp;*.pdf;*.docx'),
            ('Изображения', '*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.tiff;*.webp'),
            ('Документы', '*.pdf;*.docx'),
            ('Все файлы', '*.*')
        ]

        self.file_path = filedialog.askopenfilename(
            title="Выберите файл для обработки"
        )

        if self.file_path:
            print(f"Выбран файл: {self.file_path}")
            file_ext = os.path.splitext(self.file_path)[1].lower()
            if self.is_image_file(self.file_path):
                print("Тип файла: Изображение")
            elif self.is_document_file(self.file_path):
                print("Тип файла: Документ")
            else:
                print(f"Внимание: Неподдерживаемый тип файла ({file_ext})")
        else:
            print("Файл не выбран.")

        root.destroy()

    def doc_analyze_by_ai(self, question, search=False):
        """Анализирует документ с помощью AI"""
        client = Client()
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-nano",  # Изменена модель для лучшей поддержки
                messages=[{"role": "user", "content": question}],
                web_search=search,

            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при обращении к API: {str(e)}"

    def interface(self):
        """Основной интерфейс программы"""
        print("=== Анализатор документов и изображений ===")
        print("Поддерживаемые форматы:")
        print("- Изображения: JPG, PNG, BMP, GIF, TIFF, WebP")
        print("- Документы: PDF, DOCX")
        print("=" * 50)

        self.choose_file()

        if not self.file_path:
            print("Программа завершена: файл не выбран")
            return

        # Получаем содержимое файла
        content = self.content()

        if "Ошибка" in content or "недоступна" in content:
            print(f"Проблема с обработкой файла: {content}")
            return

        session = True
        history_dialog = ""
        cont = 0

        while session:
            if cont == 0:
                if self.is_image_file(self.file_path):
                    question = f"Вот описание изображения, проанализируй его: {content}"
                else:
                    question = f"Вот считанный для тебя документ, что ты можешь про него рассказать? Документ: {content}"
            else:
                print('\nЧто хотите спросить? (введите "exit" для выхода)')
                question = str(input('Вводите: ')).encode('utf-8').decode('utf-8', errors='ignore')

                if not question:
                    print("Пожалуйста, введите вопрос.")
                    continue

                if question.lower() in ["exit", "quit", "выйти"]:
                    session = False
                    # Очистка папки images если она существует
                    if os.path.exists('images'):
                        try:
                            for filename in os.listdir('images'):
                                file_path = os.path.join('images', filename)
                                if os.path.isfile(file_path):
                                    os.remove(file_path)
                            print("Временные файлы очищены.")
                        except Exception as e:
                            print(f"Ошибка при очистке временных файлов: {e}")
                    break


            # Формируем полный вопрос с историей
            if len(history_dialog) > 1:
                full_question = f"История вашей переписки: {history_dialog}, Вопрос пользователя: {question}"
            else:
                full_question = question

            # Получаем ответ от AI
            answer = self.doc_analyze_by_ai(full_question)

            # Сохраняем ответ в историю
            history_dialog += f"User question{cont+1}: {question}\nYour answer{cont+1}: {answer}"
            if cont > 4:
                history_dialog.pop(0)

            print(f"\nОтвет {cont + 1}: {answer}")
            print('*' * 80)
            print('-' * 80)
            print('*' * 80)

            cont += 1
