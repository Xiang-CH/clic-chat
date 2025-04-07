import pandas as pd
from sentence_transformers import SentenceTransformer
import os 

model = SentenceTransformer("BAAI/bge-m3")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

df = pd.read_json("cases_meta.json")
print(df.info())
print(df.head(5))

# Drop rows where case_number is a list
df = df[~df["case_number"].apply(lambda x: isinstance(x, list))]
print(f"DataFrame after dropping rows: {len(df)} rows remaining")

embeddings = model.encode(df["case_summary"].tolist(), show_progress_bar=True)
df["summary_vector"] = embeddings.tolist()


# Create case references dataframe
case_ref_rows = []
for idx, row in df.iterrows():
    # Convert string representation of list to actual list if needed
    citations = row["law_report_citations"]
    
    # Add each citation as a reference
    for citation in citations:
        if citation and citation.strip():  # Skip empty citations
            case_ref_rows.append({
                "source_case_id": row["citation"],
                "referenced_citation": citation.strip()
            })

# Create the case references dataframe
case_ref_df = pd.DataFrame(case_ref_rows)
print(f"Created {len(case_ref_df)} case references")
print(case_ref_df.head(5))

df.drop(columns=["law_report_citations"], inplace=True)
print(df.info())
print(df.head(5))

# Save both dataframes
df.to_parquet("cases_meta_with_embeddings.parquet")
case_ref_df.to_parquet("case_references.parquet")

