from converter import ConverterToMd
from testmaker import TestMaker

def main():
    file_to_convert = "Лекция1.pdf"
    
    converter = ConverterToMd()
    testmaker = TestMaker()

    try:
        markdown_text: str = converter.convert(file_to_convert)
        
        with open("lecture.md", "w", encoding="utf-8") as f:
            f.write(markdown_text)

    except Exception as e:
        print(f"Error: {e}")

    try:
        markdown_text: str = converter.convert(file_to_convert)
        
        test_json = testmaker.make_test(markdown_text, level="medium", count=10, test_name="Тест по первой лекции.")

        with open("test.json", "w", encoding="utf-8") as f:
            f.write(test_json)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()