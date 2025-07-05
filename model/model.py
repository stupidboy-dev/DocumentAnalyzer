import os.path

from g4f.client import Client
import g4f
from collections import deque
from doc_extract.pdf import extract_pages_pdf
from doc_extract.docx import DocxExtracting

class MainModel_MainModuel:
    def __init__(self, file_path):
        self.file_path = file_path

    def content(self):
        if os.path.splitext(self.file_path)[1].lower() == '.pdf':
            return extract_pages_pdf(self.file_path)
        elif os.path.splitext(self.file_path)[1].lower() == '.docx':
            docx = DocxExtracting(self.file_path)
            return docx.make_description()


    def doc_analyze_by_ai(self, qwestion, search=False):
        client = Client()
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": qwestion}],
                web_search=search,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при обращении к API: {str(e)}"

    def interface(self):
        content = self.content()
        session = True
        history_dialog = deque(maxlen=4)  # Limit to 4 interactions
        cont = 0

        while session:
            if cont == 0:
                qwestion = f"Вот считанный для тебя документ, что ты можешь про него рассказать? Документ: {content}"
            else:
                print('Что хотите спросить?')
                qwestion = str(input('Вводите:...')).strip()
                if not qwestion:
                    print("Пожалуйста, введите вопрос.")
                    continue
                if qwestion.lower() in ["exit", "quit", "выйти"]:
                    session = False
                    lst = os.listdir('images')
                    for i in lst:
                        del_path = os.path.join('images/', i)
                        os.remove(del_path)
                    break

            # Append only the current question to history
            history_dialog.append({"question": qwestion})

            # Call AI with question and limited history
            history_str = "\n".join([f"Вопрос {i+1}: {item['question']}" for i, item in enumerate(history_dialog)])
            full_qwestion = f"{qwestion}\nИстория чата:\n{history_str}"
            answer = self.doc_analyze_by_ai(full_qwestion)

            # Store answer in history
            history_dialog[-1]["answer"] = answer

            print(f"Ответ {cont + 1}: {answer}")
            print('*' * 200)
            print('-' * 200)
            print('*' * 200)

            cont += 1