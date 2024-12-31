import os

def create_directory(year, lang, court):
    if not os.path.exists(f"raw_judgments/{year}"):
        os.makedirs(f"raw_judgments/{year}")
    if not os.path.exists(f"raw_judgments/{year}/{lang}"):
        os.makedirs(f"raw_judgments/{year}/{lang}")
    if not os.path.exists(f"raw_judgments/{year}/{lang}/{court}"):
        os.makedirs(f"raw_judgments/{year}/{lang}/{court}")

def data_2023():
    base = "raw_judgments/legalData_2023_2024"
    for directory in os.listdir(f"{base}/en"):
        # Skip hidden files and documents
        if directory.startswith(".") or os.path.isfile(f"{base}/en/{directory}"):
            continue

        court, year = directory.split("_")
        # Move files to the correct directory
        for file in os.listdir(f"{base}/en/{directory}"):
            if file.startswith("."):
                continue

            create_directory(year, "en", court)
            # os.system(f"cp {base}/en/{directory}/{file} raw_judgments/{year}/en/{court}")
            os.rename(f"{base}/en/{directory}/{file}", f"raw_judgments/{year}/en/{court}/{file}")

def data_2021():
    base = "raw_judgments/legalData_2021_2022"
    for lang in ['en', 'ch']:
        for directory in os.listdir(f"{base}/{lang}"):
            # Skip hidden files and documents
            if directory.startswith(".") or os.path.isfile(f"{base}/{lang}/{directory}"):
                continue

            court, year = directory.split("_")
            # Move files to the correct directory
            for file in os.listdir(f"{base}/{lang}/{directory}"):
                if file.startswith("."):
                    continue

                create_directory(year, lang, court)
                os.rename(f"{base}/{lang}/{directory}/{file}", f"raw_judgments/{year}/{lang}/{court}/{file}")

def data_2019():
    base = "raw_judgments/legalData_2019_2020"
    for lang in ['en', 'ch']:
        for directory in os.listdir(f"{base}/{lang}"):
            # Skip hidden files and documents
            if directory.startswith(".") or os.path.isfile(f"{base}/{lang}/{directory}"):
                continue

            court, year = directory.split("_")
            # Move files to the correct directory
            for file in os.listdir(f"{base}/{lang}/{directory}"):
                if file.startswith("."):
                    continue

                create_directory(year, lang, court)
                os.rename(f"{base}/{lang}/{directory}/{file}", f"raw_judgments/{year}/{lang}/{court}/{file}")

def data_pre_2019():
    base = "raw_judgments/legalData"
    for lang in ['en', 'ch']:
        for directory in os.listdir(f"{base}/{lang}"):
            # Skip hidden files and documents
            if directory.startswith(".") or os.path.isfile(f"{base}/{lang}/{directory}"):
                continue

            court = directory

            if not "data" in os.listdir(f"{base}/{lang}/{directory}"):
                continue

            # Move files to the correct directory
            for file in os.listdir(f"{base}/{lang}/{directory}/data"):
                if file.startswith("."):
                    continue
                    
                try:
                    year, new_file = file.split("_")
                except Exception as e:
                    year = "ND"
                    new_file = file

                if year is None:
                    continue

                create_directory(year, lang, court)

                os.rename(f"{base}/{lang}/{directory}/data/{file}", f"raw_judgments/{year}/{lang}/{court}/{new_file}")

data_pre_2019()