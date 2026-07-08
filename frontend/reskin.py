import re

with open('d:/Goldbees/frontend/src/app/page.js', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'bg-stone-50': 'bg-[#0B0E14]',
    'text-stone-850': 'text-gray-200',
    'text-stone-800': 'text-gray-200',
    'bg-white': 'bg-[#181A20]',
    'bg-[#FAF9F5]': 'bg-[#181A20]',
    'border-stone-200': 'border-[#2B3139]',
    'border-stone-300': 'border-[#2B3139]',
    'text-stone-500': 'text-gray-400',
    'text-stone-600': 'text-gray-400',
    'text-stone-700': 'text-gray-300',
    'text-stone-950': 'text-white',
    'text-stone-900': 'text-white',
    'bg-stone-100': 'bg-[#2B3139]',
    'bg-stone-200/60': 'bg-[#181A20]',
    'from-amber-600 to-amber-700': 'from-emerald-400 to-emerald-600',
    'bg-amber-50': 'bg-emerald-900/30',
    'text-amber-700': 'text-emerald-400',
    'border-yellow-500/50': 'border-emerald-500/30',
    'bg-amber-500': 'bg-emerald-600',
    'hover:bg-amber-600': 'hover:bg-emerald-500',
    'ring-amber-500': 'ring-emerald-500',
    'border-amber-500': 'border-emerald-500',
    'text-amber-600': 'text-emerald-500',
    'text-amber-500': 'text-emerald-500'
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Update chart styles for dark mode
content = content.replace("theme: { mode: 'light' }", "theme: { mode: 'dark' }")
content = content.replace("colors: ['#D97706']", "colors: ['#10B981']") # Emerald color
content = content.replace("background: '#fff'", "background: '#181A20'")
content = content.replace("color: '#1c1917'", "color: '#EDEDED'")
content = content.replace("border: '1px solid #e7e5e4'", "border: '1px solid #2B3139'")
content = content.replace("grid: { borderColor: '#e2e8f0', strokeDashArray: 4 }", "grid: { borderColor: '#2B3139', strokeDashArray: 4 }")
content = content.replace("grid: { borderColor: '#E2E8F0' }", "grid: { borderColor: '#2B3139' }")
content = content.replace("style: { colors: '#78716c' }", "style: { colors: '#9CA3AF' }")

with open('d:/Goldbees/frontend/src/app/page.js', 'w', encoding='utf-8') as f:
    f.write(content)
