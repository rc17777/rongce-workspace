import pickle
d = pickle.load(open('.rag_vector_index/metadata.pkl', 'rb'))
print(f"Type: {type(d)}")
if isinstance(d, list):
    print(f"Length: {len(d)}")
    if d:
        print(f"First item type: {type(d[0])}")
        print(f"First item: {str(d[0])[:200]}")
        print(f"Last item: {str(d[-1])[:200]}")
elif isinstance(d, dict):
    print(f"Keys: {list(d.keys())}")
