import re

def rebuild():
    with open(r'd:\Goldbees\frontend\src\app\page.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # The issue: max-w-7xl was opened at 420.
    # It was closed at 904. But wait, at 904 there is `</div>\n</div>`. Let's see what they actually closed.
    
    # Rather than trying to manually guess, let's just make sure the `simulation` tab conditional is well-formed.
    # Right now, `page.js` has:
    # 706: </div> {/* End Right Column */}
    # 707: </div> {/* End Main Content Grid */}
    # 708: </>
    # 709: )}
    
    # 852: </div>
    # 853: )}
    
    # 1041: </div>
    # 1042: )}
    
    # What if we just fix the syntax of `{activeTab === 'simulation' && (<div className="space-y-8">`
    # Instead of doing that, I'll strip all Tab logic from the file, effectively restoring it to a single page view.
    # Then I'll cleanly inject the tabs at the top level!
    
    # Strip opening tags
    content = content.replace("{activeTab === 'overview' && (", "")
    content = content.replace("{activeTab === 'ailab' && (", "")
    content = content.replace("{activeTab === 'simulation' && (", "")
    
    # Strip fragments
    content = content.replace("<>\n", "")
    content = content.replace("</>\n", "")
    
    # Strip all closing tags of the conditionals (we'll just search for `)}` on a line by itself)
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        # Remove empty `)}` lines
        if line.strip() == ')}':
            continue
        # Remove `<>` and `</>`
        if line.strip() in ['<>', '</>']:
            continue
        # Remove `<div className="space-y-8">` right after the simulation or ailab tabs were opened
        if line.strip() == '<div className="space-y-8">' and ("ailab" in lines[i-1] or "simulation" in lines[i-1]):
            continue
        new_lines.append(line)
        
    content = '\n'.join(new_lines)
    
    # Also I need to remove the closing `</div>` that corresponded to `<div className="space-y-8">` for ailab and simulation.
    # This is tricky. Let's just fix the syntax of the current file instead.
    
    pass

if __name__ == "__main__":
    rebuild()
