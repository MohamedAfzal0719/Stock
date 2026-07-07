import re
import os

filepath = r"d:\Goldbees\frontend\src\app\page.js"

with open(filepath, "r", encoding="utf-8") as f:
    code = f.read()

# I will write a simple string replacement script to clean up the tabs.
# But actually, I can just use regex to remove the existing tab wrappers first.

code = code.replace("{activeTab === 'overview' && (", "")
code = code.replace("{activeTab === 'ailab' && (", "")
code = code.replace("{activeTab === 'simulation' && (", "")
code = code.replace("<>","")
code = code.replace("</>","")

# Wait, if I just do this I might break it more.
# It's easier if I just fetch the original file from github/backup, or I'll just write a script that does precise replacements.

# Let's target the exact lines that are broken.
# 1. Remove the stray `</div></div>` around line 903
lines = code.split('\n')
for i, line in enumerate(lines):
    if "</div>" in line and "</div>" in lines[i-1] and "Leaderboard Table" in lines[i+2]:
        print(f"Found rogue divs at {i}")

