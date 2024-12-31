import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding']

file = "raw_judgments/eng/hkfc_2021/47.docx"

print(detect_encoding(file))