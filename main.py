from model.model import MainModel_MainModuel

def main():
    path = str(input("Введите путь к файлу:"))
    processor = MainModel_MainModuel(path)
    processor.interface()

if __name__ == "__main__":
    main()