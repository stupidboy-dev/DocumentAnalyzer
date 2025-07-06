import gradio as gr
import os
from model.model import MainModel_MainModule

# Создаем экземпляр процессора (не меняем его методы)
processor = MainModel_MainModule()


# Обработчик загрузки файла
def handle_upload(file_path):
    if file_path is None or not os.path.exists(file_path):
        return "Файл не загружен.", [], []
    # Устанавливаем путь в процессоре
    status = processor.upload(file_path)
    # Получаем первичное содержимое (описание/текст)
    content = processor.content()
    # Формируем первый вопрос и ответ от AI
    user_q = f"Вот считанный документ, что ты можешь про него рассказать? Документ: {content}"
    bot_a = processor.doc_analyze_by_ai(user_q)
    # История чата — список пар [вопрос, ответ]
    history = [[user_q, bot_a]]
    return status, history, history


# Обработчик последующих сообщений
def chat_interface(message, history):
    # history — list of pairs
    if history is None:
        history = []
    # Передаем последний пользовательский запрос
    # Сохраняем новый запрос в историю для контекста
    full_history = "".join([f"User: {h[0]}\nAssistant: {h[1]}\n" for h in history])
    # Запрос к AI с учетом всей истории
    question = message
    answer = processor.doc_analyze_by_ai(f"История:\n{full_history}\nВопрос: {question}")
    history.append([question, answer])
    return history, history, ""


def new_session():
    # Удалим файл, если он существует
    if processor.file_path and os.path.exists(processor.file_path):
        try:
            os.remove(processor.file_path)
            print(f"Удалён файл: {processor.file_path}")
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")
    processor.file_path = None  # Сброс пути к файлу
    return None, [], [],  "", "Ожидается новый файл для анализа"



# Строим Gradio-интерфейс
with gr.Blocks(title="Документы с AI-анализом") as demo:
    gr.Markdown("# Анализатор документов с GPT")

    with gr.Row():
        # Левая колонка — узкая
        with gr.Column(scale=1, min_width=150):
            file_input = gr.File(label="Загрузите файл", type="filepath")
            upload_btn = gr.Button("Загрузить и проанализировать")
            file_status = gr.Textbox(label="Статус", interactive=False, lines=3, max_lines=4)

        # Правая колонка — широкая
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(label="GPT-Ассистент", height=750)
            state = gr.State([])
            msg = gr.Textbox(label="Ваш вопрос", placeholder="Напишите запрос и нажмите Enter или кнопку ниже")
            send_btn = gr.Button("Отправить")
            new_session_btn = gr.Button("Начать новую сессию", variant="secondary")

    # Обработчики
    upload_btn.click(fn=handle_upload,
                     inputs=file_input,
                     outputs=[file_status, chatbot, state])

    send_btn.click(fn=chat_interface,
                   inputs=[msg, state],
                   outputs=[chatbot, state, msg])

    msg.submit(fn=chat_interface,
               inputs=[msg, state],
               outputs=[chatbot, state, msg])

    new_session_btn.click(
        fn=new_session,
        inputs=[],
        outputs=[file_input, chatbot, state, msg, file_status]
    )

if __name__ == "__main__":
    demo.launch(share=True)
