import os
p = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\ocr_log.txt'
if os.path.exists(p):
    with open(p, encoding='utf-8') as f:
        lines = f.readlines()
    for l in lines[-20:]:
        print(l.rstrip())
    done = sum(1 for l in lines if l.startswith('DONE'))
    print(f'\nTotal DONE: {done}')
    errs = sum(1 for l in lines if 'ERR' in l or 'error' in l.lower())
    print(f'Errors: {errs}')
    ok_count = sum(1 for l in lines if 'OK' in l)
    print(f'OK pages: {ok_count}')