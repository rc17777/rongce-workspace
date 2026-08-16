"""22家投标人全量TF-IDF文本雷同检测 — 并行提取+相似度矩阵"""
import sys, os, fitz, re, json, pickle
sys.stdout.reconfigure(encoding='utf-8')
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import warnings
warnings.filterwarnings('ignore')

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\5号6号学生宿舍建设项目监理\监理投标文件(PDF)"
OUT = r"D:\openclaw-workspace\output\宿舍监理"
CACHE = os.path.join(OUT, 'tfidf_cache.pkl')
os.makedirs(OUT, exist_ok=True)

# ====== Step 1: Extract text from all bidders ======
bidders = []
print("=" * 60)
print("STEP 1: Extract text from 22 bidders (first 300 pages each)")
print("=" * 60)

# Try loading cache
if os.path.exists(CACHE):
    print("Loading cached texts...")
    with open(CACHE, 'rb') as f:
        bidders = pickle.load(f)
    print(f"Loaded {len(bidders)} cached texts")
else:
    for fname in sorted(os.listdir(BASE)):
        if not fname.endswith('.pdf'): continue
        path = os.path.join(BASE, fname)
        name = fname.replace('.pdf', '').strip()
        
        print(f'  Extracting: {name[:30]}...', end=' ', flush=True)
        doc = fitz.open(path)
        text_parts = []
        max_pages = min(300, len(doc))
        
        for pg in range(max_pages):
            t = doc[pg].get_text()
            if t.strip():
                text_parts.append(t.strip())
        
        doc.close()
        full_text = '\n'.join(text_parts)
        bidders.append({'name': name, 'text': full_text, 'chars': len(full_text)})
        print(f'{len(full_text):,} chars')
    
    # Save cache
    with open(CACHE, 'wb') as f:
        pickle.dump(bidders, f)
    print(f'Saved cache: {CACHE}')

# ====== Step 2: Clean and prepare texts ======
print(f"\n{'='*60}")
print("STEP 2: Text cleaning and preparation")
print("=" * 60)

# Remove boilerplate common to all bids
common_patterns = [
    r'四川护理职业学院5号学生宿舍.*?监理',
    r'投标人须知.*?监理',
    r'法定代表人.*?签字',
    r'授权委托书',
]

def clean_text(text):
    """Remove excessive whitespace and normalize"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'_+', ' ', text)
    # Remove common header/footer patterns
    text = re.sub(r'第\s*\d+\s*页\s*共\s*\d+\s*页', ' ', text)
    return text.strip()

names = [b['name'][:30] for b in bidders]
texts = [clean_text(b['text']) for b in bidders]
char_counts = [b['chars'] for b in bidders]

print(f'Total bidders: {len(bidders)}')
print(f'Total chars: {sum(char_counts):,}')
print(f'Min chars: {min(char_counts):,} ({names[char_counts.index(min(char_counts))].strip()})')
print(f'Max chars: {max(char_counts):,} ({names[char_counts.index(max(char_counts))].strip()})')

# ====== Step 3: TF-IDF with char_wb (fast, catches template overlap) ======
print(f"\n{'='*60}")
print("STEP 3: TF-IDF char_wb analysis")
print("=" * 60)

vectorizer_cw = TfidfVectorizer(
    analyzer='char_wb',
    ngram_range=(3, 5),
    max_features=5000,
    min_df=2,
    max_df=0.8,
)

try:
    tfidf_cw = vectorizer_cw.fit_transform(texts)
    sim_matrix_cw = cosine_similarity(tfidf_cw)
    
    # Find top similar pairs
    n = len(bidders)
    pairs_cw = []
    for i in range(n):
        for j in range(i+1, n):
            sim = sim_matrix_cw[i][j]
            pairs_cw.append((sim, names[i], names[j], char_counts[i], char_counts[j]))
    
    pairs_cw.sort(reverse=True)
    
    print(f'\nTop 15 most similar pairs (char_wb 3-5):')
    print(f'{"Rank":4s} {"Sim":>6s}  {"Bidder A":25s} {"Bidder B":25s} {"Chars A":>10s} {"Chars B":>10s}')
    print('-' * 95)
    for rank, (sim, a, b, ca, cb) in enumerate(pairs_cw[:15]):
        flag = ' *** HIGH' if sim > 0.95 else (' ** ELEV' if sim > 0.90 else '')
        print(f'{rank+1:4d} {sim:.4f}{flag:>10s}  {a:25s} {b:25s} {ca:>10,} {cb:>10,}')
    
    # Statistics
    sims = [p[0] for p in pairs_cw]
    print(f'\nchar_wb stats: mean={np.mean(sims):.4f} median={np.median(sims):.4f} '
          f'min={np.min(sims):.4f} max={np.max(sims):.4f} std={np.std(sims):.4f}')
    print(f'High (>0.95): {sum(1 for s in sims if s>0.95)} pairs')
    print(f'Elevated (0.90-0.95): {sum(1 for s in sims if 0.90<s<=0.95)} pairs')
    print(f'Normal (<0.90): {sum(1 for s in sims if s<=0.90)} pairs')
    
except Exception as e:
    print(f'char_wb error: {e}')

# ====== Step 4: TF-IDF with word analyzer (more meaningful) ======
print(f"\n{'='*60}")
print("STEP 4: TF-IDF word-level analysis (jieba)")
print("=" * 60)

try:
    import jieba
    jieba.setLogLevel(20)
    
    # Tokenize with jieba
    texts_cut = [' '.join(jieba.cut(t)) for t in texts]
    
    vectorizer_w = TfidfVectorizer(
        analyzer='word',
        token_pattern=r'(?u)\b\w+\b',
        max_features=8000,
        min_df=3,
        max_df=0.7,
        ngram_range=(1, 2),
    )
    
    tfidf_w = vectorizer_w.fit_transform(texts_cut)
    sim_matrix_w = cosine_similarity(tfidf_w)
    
    pairs_w = []
    for i in range(n):
        for j in range(i+1, n):
            sim = sim_matrix_w[i][j]
            pairs_w.append((sim, names[i], names[j], char_counts[i], char_counts[j]))
    
    pairs_w.sort(reverse=True)
    
    print(f'\nTop 15 most similar pairs (word-level, jieba):')
    print(f'{"Rank":4s} {"Sim":>6s}  {"Bidder A":25s} {"Bidder B":25s} {"Chars A":>10s} {"Chars B":>10s}')
    print('-' * 95)
    for rank, (sim, a, b, ca, cb) in enumerate(pairs_w[:15]):
        flag = ' *** HIGH' if sim > 0.70 else (' ** ELEV' if sim > 0.50 else '')
        print(f'{rank+1:4d} {sim:.4f}{flag:>10s}  {a:25s} {b:25s} {ca:>10,} {cb:>10,}')
    
    sims_w = [p[0] for p in pairs_w]
    print(f'\nword stats: mean={np.mean(sims_w):.4f} median={np.median(sims_w):.4f} '
          f'min={np.min(sims_w):.4f} max={np.max(sims_w):.4f} std={np.std(sims_w):.4f}')
    print(f'High (>0.70): {sum(1 for s in sims_w if s>0.70)} pairs')
    print(f'Elevated (0.50-0.70): {sum(1 for s in sims_w if 0.50<s<=0.70)} pairs')
    print(f'Normal (<0.50): {sum(1 for s in sims_w if s<=0.50)} pairs')
    
except ImportError:
    print('jieba not installed, skipping word-level analysis')

# ====== Step 5: Save full similarity matrix ======
print(f"\n{'='*60}")
print("STEP 5: Save results")
print("=" * 60)

try:
    # Save char_wb matrix as npz
    np.savez(os.path.join(OUT, 'tfidf_charwb_matrix.npz'), matrix=sim_matrix_cw, names=np.array(names))
    print(f'Saved char_wb matrix')
except:
    pass

try:
    np.savez(os.path.join(OUT, 'tfidf_word_matrix.npz'), matrix=sim_matrix_w, names=np.array(names))
    print(f'Saved word matrix')
except:
    pass

print('\nDONE!')
