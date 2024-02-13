import json

import pandas as pd


# Load the json file
with open("final_scrape_no_capital.json") as f:
    data = json.load(f)

df = pd.json_normalize(data)


def clean_list(l):
    l = list(set(l))
    return list(sorted(l))[:5]


# Function to extract data from word info
def extract_info(word_info_list):
    # Initialize empty dict for output info
    output_info = {
        "definition": None,
        "wordType": None,
        "phonetic": None,
        "audioUrl": None,
        "synonyms": [],
        "antonyms": [],
        "examples": [],
    }

    for word_info in word_info_list:
        # Extract phonetic
        if "phonetics" in word_info and word_info["phonetics"]:
            for phonetic in word_info["phonetics"]:
                if output_info["audioUrl"] is None and phonetic.get("audio", "") != "":
                    output_info["audioUrl"] = phonetic.get("audio", None)
                if output_info["phonetic"] is None:
                    output_info["phonetic"] = phonetic.get("text", None)

        # Extract meaning
        if "meanings" in word_info and word_info["meanings"]:
            for meaning in word_info["meanings"]:
                output_info["wordType"] = meaning.get("partOfSpeech")

                for definition in meaning.get("definitions"):
                    output_info["synonyms"].extend(meaning.get("synonyms", []))
                    output_info["antonyms"].extend(meaning.get("antonyms", []))
                    if "example" in definition:
                        output_info["examples"].append(definition["example"])
                    if output_info["definition"] is None:
                        output_info["definition"] = definition["definition"]
                    if output_info["wordType"] is None:
                        output_info["wordType"] = meaning.get("partOfSpeech")
                    if output_info["synonyms"] is None:
                        output_info["synonyms"] = definition["synonyms"]
                    if output_info["antonyms"] is None:
                        output_info["antonyms"] = definition["antonyms"]

    # Clean up lists
    output_info["synonyms"] = clean_list(output_info["synonyms"])
    output_info["antonyms"] = clean_list(output_info["antonyms"])
    output_info["examples"] = clean_list(output_info["examples"])
    if output_info["phonetic"] == "":
        output_info["phonetic"] = None
    if output_info["audioUrl"] == "":
        output_info["audioUrl"] = None

    return output_info


# Apply the function to each row
df_info = df["WordInfo"].apply(extract_info)

# Convert the Series of dicts to a DataFrame and concatenate with original data
df_info = pd.DataFrame(df_info.tolist())
df_final = pd.concat([df["Word"], df_info], axis=1)

# Write the new data to a json file
df_final.to_json("word_data_processed.json", orient="records")
