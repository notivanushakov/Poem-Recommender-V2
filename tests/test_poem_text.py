import json
import pandas as pd

# Load data
df = pd.read_parquet('data/processed/poems.parquet')
with open('models/id_map.json', 'r', encoding='utf-8') as f:
    idmap = json.load(f)

print(f"Total poems in parquet: {len(df)}")
print(f"Total poems in id_map: {len(idmap)}")
print(f"\nFirst id_map entry poem_id: {idmap[0]['poem_id']} (type: {type(idmap[0]['poem_id'])})")
print(f"First parquet poem_id: {df.iloc[0]['poem_id']} (type: {type(df.iloc[0]['poem_id'])})")

# Try to match
test_id = idmap[0]['poem_id']
matches = df[df['poem_id'] == test_id]
print(f"\nMatches for poem_id {test_id}: {len(matches)}")
if not matches.empty:
    print(f"Text found: {matches.iloc[0]['text'][:100]}...")
else:
    print("No match found!")
    print(f"Sample parquet IDs: {df['poem_id'].head().tolist()}")
