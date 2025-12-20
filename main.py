from converter import ConverterToMd

def main():
    file_to_convert = "lec.pdf"
    
    converter = ConverterToMd()

    try:
        markdown_text = converter.convert(file_to_convert)
        
        with open("result.md", "w", encoding="utf-8") as f:
            f.write(markdown_text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()