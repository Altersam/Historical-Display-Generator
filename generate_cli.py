# Pure command line version - no GUI at all
import requests
from PIL import Image, ImageDraw, ImageFont
import os

HEADERS = {'User-Agent': 'HistoricalDisplay/1.0'}

RUSSIAN_MONTHS = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
}

BG_COLOR = (35, 54, 61)

def load_events(day, month):
    url = f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month:02d}/{day:02d}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    data = resp.json()
    events = [e for e in data.get('events', []) if e.get('year', 0) and e.get('year', 0) < 2000]
    return events[:25]

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        if font.getlength(test) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines

def draw_centered_text(draw, text, y, w, font, fill='white'):
    max_width = w - 40
    lines = wrap_text(text[:200], font, max_width)
    line_height = font.getbbox('A')[3] + 8
    total_height = len(lines) * line_height
    start_y = y - total_height // 2
    for i, line in enumerate(lines):
        draw.text((w//2, start_y + i * line_height), line, fill=fill, font=font, anchor='mm')

def create_side(month, day, year, text, n, font, font_big):
    w, h = 520, 1872
    img = Image.new('RGB', (w, h), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw.line([1, 0, 1, h], fill='white', width=1)
    draw.line([w-2, 0, w-2, h], fill='white', width=1)
    
    draw.text((260, 200), f"{day} {RUSSIAN_MONTHS[month]}", fill='white', font=font_big, anchor='mm')
    draw.text((260, 280), "этот день в истории", fill='white', font=font, anchor='mm')
    draw.line([10, 480, w-10, 480], fill='white', width=2)
    
    if year:
        draw.text((260, 580), f"В {year} году", fill='white', font=font_big, anchor='mm')
    
    draw.line([10, 700, w-10, 700], fill='white', width=2)
    
    if text:
        draw_centered_text(draw, text, 870, w, font)
    
    draw.line([10, 1040, w-10, 1040], fill='white', width=2)
    draw.rectangle([20, 1060, w-20, 1800], outline='white')
    
    return img

def generate(day, month, sides_data, output_folder):
    font_path = "IskraCYR-BoldItalic.otf"
    font = ImageFont.truetype(font_path, 32)
    font_big = ImageFont.truetype(font_path, 48)
    
    combined = Image.new('RGB', (2080, 1872), color=BG_COLOR)
    
    for i in range(4):
        sd = sides_data[i]
        side = create_side(month, day, sd.get('year', ''), sd.get('text', ''), i, font, font_big)
        combined.paste(side, (i * 520, 0))
    
    path = os.path.join(output_folder, f"экран_{month:02d}_{day:02d}.png")
    combined.save(path)
    return path

if __name__ == "__main__":
    print("=== Генератор исторического дисплея ===")
    print()
    
    day = int(input("День (1-31): "))
    month = int(input("Месяц (1-12): "))
    
    print(f"Загружаю события за {day} {RUSSIAN_MONTHS[month]}...")
    events = load_events(day, month)
    print(f"Найдено {len(events)} событий до 2000 года")
    print()
    
    for i, e in enumerate(events[:10]):
        print(f"{i+1}. {e.get('year')} - {e.get('text', '')[:60]}...")
    print()
    
    sides = []
    for i in range(4):
        print(f"Сторона {i+1}:")
        idx = int(input("  Выберите номер события (0=свой текст): "))
        
        if idx > 0 and idx-1 < len(events):
            e = events[idx-1]
            year = str(e.get('year', ''))
            text = e.get('text', '')
        else:
            year = input("  Год: ")
            text = input("  Текст события: ")
        
        sides.append({'year': year, 'text': text})
        print()
    
    folder = input("Папка для сохранения (Enter = текущая): ").strip() or "."
    
    print("Генерация изображения...")
    path = generate(day, month, sides, folder)
    print(f"Сохранено: {path}")
