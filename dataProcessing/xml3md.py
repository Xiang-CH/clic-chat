from bs4 import BeautifulSoup
from markdownify import markdownify as md

# # Parse XML data with BeautifulSoup
# with open("raw_legislations/en/cap_32J_en_c/cap_32J_20210819000000_en_c.xml", "r") as f:
#     soup = BeautifulSoup(f.read(), "xml")

# # Convert the BeautifulSoup object to a string
# for table in soup.find_all("table"):
#     print("========TABLE========")

#     new_table = soup.new_tag("content")
#     new_table.string = md(table.prettify()).strip()
#     # Use markdownify to convert XML/HTML string to Markdown
#     table.replace_with(new_table)


# print(soup.prettify())


# Parse HTML data with BeautifulSoup
with open("raw_judgments/2000/en/HKCA/1.html", "r") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

for table in soup.find_all("table"):
    print("========TABLE========")

    # Use markdownify to convert XML/HTML string to Markdown
    new_table = soup.new_tag("content")
    new_table.string = md(table.prettify()).strip()
    table.replace_with(new_table)

with open("1.txt", "w") as f:
    f.write(soup.get_text(separator=" "))


# import re

# def clean_text(text):
#     """
#     Clean text by removing extra whitespace and trimming.
    
#     Args:
#         text (str): Input text to clean
        
#     Returns:
#         str: Cleaned text with normalized spacing
#     """
#     # Replace multiple whitespace characters with a single space and trim
#     return re.sub(r'\s{2,}', ' ', text).strip()

# print(clean_text("  This is\na test   string  ")) # "This is a test string"

txt = '''<body><a target="_blank" HREF="http://www.austlii.edu.au/cgi-bin/sinodisp/au/other/dfat/treaties/1901/130.html?query=Convention%20for%20the%20Pacific%20Settlement%20of%20International%20Disputes"  >1899年7月29日訂於海牙的《和平解決國際爭端公約》</A> </body>'''

print(len(txt)) # 139
print(md(txt))