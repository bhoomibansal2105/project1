import pandas as pd
import json

df = pd.read_csv("cleaned_instruments.csv")

df = df.drop_duplicates(subset=["exchange_instrument_id"])

instrument_dict = (
    df.set_index("exchange_instrument_id")["instrument_name"]
      .to_dict()
)

with open("instrument_mapping.json", "w") as f:
    json.dump(instrument_dict, f, indent=4)

print("JSON saved successfully.")
