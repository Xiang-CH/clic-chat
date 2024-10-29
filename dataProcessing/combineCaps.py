import pandas as pd
import os 
from tqdm import tqdm

os.chdir(os.path.dirname(os.path.abspath(__file__)))

for lang in ["en", "sc", "tc"]:
    df = None

    files = os.listdir(f"ordinances/embeddedChunks/{lang}")
    for file in tqdm(files, leave=True, desc=f"Combining ({lang})"):
        if df is None:
            df = pd.read_csv(f"ordinances/embeddedChunks/{lang}/{file}")
        else:
            concat_df = pd.read_csv(f"ordinances/embeddedChunks/{lang}/{file}")
            df = pd.concat([df, concat_df], ignore_index=True)
       
    df.to_csv(f"vectorData/ordinances_{lang}.csv", index=False)
    df.to_excel(f"vectorData/ordinances_{lang}.xlsx", index=False)
    