import re

with open('d:/Goldbees/frontend/src/app/page.js', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    "bg-emerald-50 text-emerald-700 border-emerald-500/50": "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    "bg-rose-50 text-rose-700 border-red-500/50": "bg-red-500/10 text-red-400 border-red-500/30",
    "bg-indigo-500/10 border border-emerald-500/20 text-indigo-300": "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400",
    "bg-gradient-to-r from-indigo-900/50 to-blue-900/50": "bg-[#15171C] border border-[#1A1D24]",
    "text-indigo-300": "text-emerald-400",
    "bg-emerald-50 p-3": "bg-emerald-500/10 p-3",
    "text-emerald-600 font-bold": "text-emerald-400 font-bold",
    "text-emerald-600": "text-emerald-500",
    "text-red-600": "text-red-500",
    "bg-stone-850 hover:bg-stone-950": "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30",
    "bg-stone-800 hover:bg-stone-900": "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30",
    "text-pink-400": "text-emerald-400",
    "bg-slate-800": "bg-[#1A1D24] border border-[#2B3139]",
    "bg-gradient-to-r from-stone-800 to-stone-900": "bg-[#15171C] border-b border-[#1A1D24]",
    "bg-[#181A20] border border-[#2B3139] rounded-2xl shadow-sm p-6": "bg-[#15171C] border border-[#1A1D24] rounded-2xl p-6 shadow-sm",
    "bg-[#181A20] border border-[#2B3139] rounded-2xl shadow-sm p-6 col-span-1 lg:col-span-2": "bg-[#15171C] border border-[#1A1D24] rounded-2xl p-6 shadow-sm col-span-1 lg:col-span-2"
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Let's fix the button colors specifically for the strategy builder
content = content.replace("bg-stone-850 hover:bg-stone-950 text-white px-6 py-2.5 rounded-xl font-bold transition-all shadow-sm disabled:opacity-50", "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 px-6 py-2.5 rounded-xl font-bold transition-all border border-emerald-500/30 disabled:opacity-50")
content = content.replace("bg-stone-850 hover:bg-stone-950 text-white font-bold rounded-xl px-4 w-1/4 transition-all shadow-sm", "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 font-bold rounded-xl px-4 w-1/4 transition-all border border-emerald-500/30")

with open('d:/Goldbees/frontend/src/app/page.js', 'w', encoding='utf-8') as f:
    f.write(content)
