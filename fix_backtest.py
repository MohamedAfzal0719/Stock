def fix():
    with open('d:/Goldbees/src/services/backtest.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    main_idx = -1
    for i, line in enumerate(lines):
        if 'if __name__ == "__main__":' in line:
            main_idx = i
            break

    func_idx = -1
    for i, line in enumerate(lines):
        if 'def evaluate_custom_strategy' in line:
            func_idx = i
            break

    if main_idx != -1 and func_idx != -1 and func_idx > main_idx:
        func_lines = lines[func_idx:]
        new_lines = lines[:main_idx] + func_lines + ['\n'] + lines[main_idx:func_idx]
        with open('d:/Goldbees/src/services/backtest.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print('Fixed backtest.py order!')

if __name__ == '__main__':
    fix()
