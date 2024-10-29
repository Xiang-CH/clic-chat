import pandas as pd
import json
import os
import re

interp_key = {
    "en": "Interpretation",
    "sc": "释义",
    "tc": "釋義"
}

and_trans = {
    "en": "and",
    "sc": "和",
    "tc": "和"
}

or_trans = {
    "en": "or",
    "sc": "或",
    "tc": "或"
}

means_trans = {
    "en": "means",
    "sc": "指",
    "tc": "指"
}

for lang in ["en", "sc", "tc"]:
    files = os.listdir(f"ordinances/full_cap/{lang}")
    for file in files:
        with open(f"ordinances/full_cap/{lang}/{file}") as f:
            data = json.load(f)

        interp_data = []

        cap_no = data["cap_no"]
        sections = data["sections"]
        if len(sections) == 0:
            continue
        for sec in sections:
            if not sec["heading"]:
                continue

            if sec["heading"] == interp_key[lang]:
                print(f"Cap: {cap_no}")

                if sec["text"].split("\n", maxsplit=1)[1].startswith("(1)"):
                    terms = re.split(r"\(\d\).*?\n", sec["text"])[1]
                    lines = terms.split("\n")
                else:
                    lines = sec["text"].split("\n")[2:]

                for line in lines:
                    print(line)
                    if line.strip() in ["", "(Not yet in operation)", "Editorial Note:"]:
                        continue
                    if line.startswith("(2)"):
                        break
                    if line.startswith("(1)") or line.startswith("[") or line.startswith("*"):
                        continue
                    if line.startswith("("):
                        interp_data[-1]["definition"] += f"\n{line}"
                        continue

                    phrases = re.split(r"\((?![0-9]).*?\)", line, maxsplit=1)
                    if len(phrases) == 1:
                        if means_trans[lang] not in phrases[0]:
                            interp_data[-1]["definition"] += f"\n{line}"
                            continue
                        else:
                            phrases = line.split(means_trans[lang], maxsplit=1)
                    term = phrases[0].strip().strip('"').strip()
                    definition = phrases[1].strip(",").strip("，").strip()

                    if definition.startswith(and_trans[lang]):
                        phrases2 = re.split(r"\(.*?\)", definition[len(and_trans[lang]) + 1:], maxsplit=1)
                        term2 = phrases2[0].strip().strip('"').strip()
                        definition = phrases2[1].strip(",").strip("，").strip()
                        interp_data.append({
                            "term": term2,
                            "definition": definition
                        })

                    if definition.startswith(or_trans[lang]):
                        phrases2 = re.split(r"\(.*?\)", definition[len(or_trans[lang]) + 1:], maxsplit=1)
                        term2 = phrases2[0].strip().strip('"').strip()
                        definition = phrases2[1].strip(",").strip("，").strip()
                        interp_data.append({
                            "term": term2,
                            "definition": definition
                        })

                    print(
                        f"Term: {term}\nDefinition: {definition}"
                    )
                    interp_data.append({
                        "term": term,
                        "definition": definition
                    })
                break
        
        if not os.path.exists(f"ordinances/interpretations/{lang}"):
            os.mkdir(f"ordinances/interpretations/{lang}")
        if len(interp_data) > 0:
            df = pd.DataFrame(interp_data)
            df.to_csv(f"ordinances/interpretations/{lang}/cap_{cap_no}_{lang}.csv", index=False)
    break