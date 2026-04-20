import requests
from PIL import Image, ImageDraw, ImageFont
import io
import datetime
import textwrap
import os
import sys
import re
import base64
import json

# User-Agent header for API requests
HEADERS = {
    'User-Agent': 'FourSidedHistoricalDisplay/1.0 (https://example.com; contact@example.com)'
}

# Russian month names
RUSSIAN_MONTHS = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
}

def wrap_text(text, font, max_width):
    """Разбить текст на строки с учетом максимальной ширины."""
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

def find_optimal_font_size(texts, max_width, max_height, font_path):
    """Найти максимальный размер шрифта, которым все тексты влезают в блок."""
    if not texts:
        return 40
    
    best_size = 20
    for size in range(80, 19, -1):
        try:
            font = ImageFont.truetype(font_path, size)
            all_fit = True
            for text in texts:
                lines = wrap_text(text[:250], font, max_width)
                line_height = font.getbbox('A')[3] + 8
                total_height = len(lines) * line_height
                if total_height > max_height:
                    all_fit = False
                    break
            if all_fit:
                best_size = size
                break
        except:
            continue
    return best_size

def draw_centered_text(draw, text, y, w, font, fill='white'):
    """Нарисовать текст, отцентрованный по горизонтали и вертикали."""
    max_width = w - 20
    lines = wrap_text(text[:250], font, max_width)
    line_height = font.getbbox('A')[3] + 8
    total_height = len(lines) * line_height
    start_y = y - total_height // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (w - line_width) // 2
        draw.text((x, start_y + i * line_height), line, fill=fill, font=font)
        x = (w - line_width) // 2
        draw.text((x, start_y + i * line_height), line, fill=fill, font=font)

def load_mascot_image(side_number):
    """Загрузить изображение маскота для указанной стороны."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    mascot_files = {
        1: os.path.join(base_path, "Маскот", "tsvet_21.png"),
        2: os.path.join(base_path, "Маскот", "tsvet_23.png"),
        3: os.path.join(base_path, "Маскот", "tsvet_28.png"),
        4: os.path.join(base_path, "Маскот", "tsvet_30.png")
    }
    
    if side_number not in mascot_files:
        return None
    
    try:
        mascot_path = mascot_files[side_number]
        mascot_img = Image.open(mascot_path)
        mascot_img = mascot_img.resize((150, 150), Image.Resampling.LANCZOS)
        return mascot_img
    except Exception as e:
        print(f"  [WARNING] Не удалось загрузить маскот: {e}")
        return None

def image_to_base64(img, format='PNG'):
    """Конвертировать изображение в строку base64."""
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def fetch_russian_wikipedia_events(month, day):
    """Получить исторические события для заданного месяца и дня из русской Википедии, только до 2000 года."""
    url = f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month:02d}/{day:02d}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        events = data.get('events', [])
        # Filter events to only those before year 2000
        filtered_events = []
        for event in events:
            year = event.get('year')
            # Handle different year formats
            if year is not None:
                if isinstance(year, int) and year < 2000:
                    filtered_events.append(event)
                elif isinstance(year, str):
                    if year.isdigit() and int(year) < 2000:
                        filtered_events.append(event)
                    # Try to extract year from text if year field is not numeric
                    elif not year.isdigit():
                        year_match = re.search(r'\b(\d{4})\b', year)
                        if year_match and int(year_match.group(1)) < 2000:
                            filtered_events.append(event)
            # If year is in text field, try to extract it
            elif 'text' in event:
                year_match = re.search(r'\b(\d{4})\b', event['text'])
                if year_match:
                    year_int = int(year_match.group(1))
                    if year_int < 2000:
                        filtered_events.append(event)
        return filtered_events
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении событий для {month:02d}/{day:02d}: {e}")
        return []
    except Exception as e:
        print(f"Неожиданная ошибка при обработке событий: {e}")
        return []

def search_image_from_duckduckgo(query):
    """Попробовать найти изображение через DuckDuckGo."""
    try:
        # Используем DuckDuckGo API для поиска изображений
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'ia': 'images',
            'image_index': 0
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('Image'):
                return data['Image'][0].get('URL')
    except:
        pass
    return None

def search_image_from_bing_fallback(query):
    """Резервный поиск изображений (использует открытые источники)."""
    # Пробуем найти изображение через Wikipedia Commons напрямую
    try:
        # Ищем на Wikimedia Commons
        search_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query + ' site:commons.wikimedia.org',
            'srlimit': 5
        }
        response = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('query', {}).get('search', [])
            if results:
                # Пробуем получить изображение для первого результата
                page_title = results[0]['title']
                img_params = {
                    'action': 'query',
                    'format': 'json',
                    'titles': page_title,
                    'prop': 'pageimages',
                    'pithumbsize': 1024
                }
                img_response = requests.get(search_url, params=img_params, headers=HEADERS, timeout=10)
                if img_response.status_code == 200:
                    img_data = img_response.json()
                    pages = img_data.get('query', {}).get('pages', {})
                    for page_id, page_info in pages.items():
                        if 'thumbnail' in page_info:
                            return page_info['thumbnail']['source']
    except:
        pass
    return None

def fetch_image_with_fallback(event_data, event_text):
    """Получить изображение с несколькими попытками из разных источников."""
    img_obj = None
    
    # 1. Пробуем страницы из события Wikipedia (до 10 страниц)
    pages = event_data.get('pages', [])
    if pages:
        for page_idx in range(min(10, len(pages))):
            page = pages[page_idx]
            page_title = page.get('title')
            if not page_title:
                continue
            if '_год' in page_title or page_title.isdigit() or (len(page_title) == 4 and page_title.isdigit()):
                continue
            
            for lang in ['ru', 'en']:
                try:
                    search_url = f"https://{lang}.wikipedia.org/w/api.php"
                    params = {
                        'action': 'query',
                        'format': 'json',
                        'titles': page_title,
                        'prop': 'pageimages',
                        'pithumbsize': 1024,
                        'pilimit': 1
                    }
                    response = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        image_data = response.json()
                        pages_result = image_data.get('query', {}).get('pages', {})
                        for page_id, page_info in pages_result.items():
                            if 'thumbnail' in page_info:
                                img_url = page_info['thumbnail']['source']
                                downloaded = download_image(img_url)
                                if downloaded:
                                    return downloaded
                except:
                    continue
    
    # 2. Пробуем резервный метод через Wikipedia Commons
    if not img_obj and event_text:
        # Извлекаем ключевые слова из текста события
        keywords = event_text.split()[:5]  # Первые 5 слов
        query = ' '.join(keywords)
        img_url = search_image_from_bing_fallback(query)
        if img_url:
            img_obj = download_image(img_url)
            if img_obj:
                return img_obj
    
    # 3. Пробуем DuckDuckGo
    if not img_obj and event_text:
        keywords = event_text.split()[:5]
        query = ' '.join(keywords)
        img_url = search_image_from_duckduckgo(query)
        if img_url:
            img_obj = download_image(img_url)
            if img_obj:
                return img_obj
    
    return None

def fetch_wikipedia_image(event_title):
    """Получить изображение со страницы Википедии (любой языковой версии) - резервный метод."""
    # Попытка получить изображение сначала из русской, потом из английской Википедии
    for lang in ['ru', 'en']:
        try:
            # Поиск страницы
            search_url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': event_title,
                'srlimit': 1
            }
            response = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            search_data = response.json()
            
            if not search_data.get('query', {}).get('search'):
                continue
                
            page_id = search_data['query']['search'][0]['pageid']
            
            # Получение URL изображений для страницы
            params = {
                'action': 'query',
                'format': 'json',
                'pageids': page_id,
                'prop': 'pageimages',
                'pithumbsize': 1024,  # Больше размер для лучшего качества
                'pilimit': 1
            }
            response = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            image_data = response.json()
            
            page_info = image_data.get('query', {}).get('pages', {}).get(str(page_id))
            if page_info and 'thumbnail' in page_info:
                return page_info['thumbnail']['source']
        except:
            continue  # Попробовать другой язык если текущий не сработал
    return None

def download_image(url):
    """Скачать изображение по URL."""
    try:
        # Для Wikimedia изображений используем более мягкие заголовки
        download_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/png,image/jpeg,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://wikipedia.org/'
        }
        response = requests.get(url, headers=download_headers, timeout=15)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"  [ERROR] Ошибка 403 при скачивании - пробуем альтернативный URL")
            # Пробуем получить более маленькое изображение
            if '/thumb/' in url:
                # Попробуем уменьшить размер
                base_url = url.split('/thumb/')[0]
                small_url = base_url.replace('/commons/', '/commons/thumb/').replace('/ru/', '/ru/thumb/')
                # Просто возвращаем None - это изображение недоступно
                return None
        print(f"  [ERROR] Ошибка при скачивании изображения HTTP: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Ошибка при скачивании изображения: {e}")
        return None
    except Exception as e:
        print(f"  [ERROR] Неожиданная ошибка при обработке скачанного изображения: {e}")
        return None

def create_side_display(month, day, event_data, side_number, event_text_font_size=40):
    """Создать одну сторону дисплея 520x1872px."""
    width = 520
    height = 1872
    
    # Цвет фона rgb(35, 54, 61)
    bg_color = (35, 54, 61)
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Белые полосы слева и справа по 1px
    draw.line([1, 0, 1, height], fill='white', width=1)
    draw.line([width-2, 0, width-2, height], fill='white', width=1)
    
    # Загружаем шрифты (попробуем Iskra Cyrillic Bold Italic)
    font_candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "IskraCYR-BoldItalic.otf"),
        "IskraCYR-BoldItalic.otf",
        "IskraCyrillic.ttf",
        "iskracyrillic.ttf",
        "arial.ttf",
        "ARIAL.TTF"
    ]
    
    font_name = None
    font_loaded = False
    for font_name in font_candidates:
        try:
            font_title = ImageFont.truetype(font_name, 72)
            font_subtitle = ImageFont.truetype(font_name, 48)
            font_year = ImageFont.truetype(font_name, 60)
            font_small = ImageFont.truetype(font_name, 40)
            font_event_text = ImageFont.truetype(font_name, event_text_font_size)
            print(f"  Загружен шрифт: {font_name}")
            font_loaded = True
            break
        except:
            continue
    
    if not font_loaded:
        print("  Используем шрифт по умолчанию")
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_year = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_event_text = font_small
    
    # Данные события
    if event_data:
        year = event_data.get('year', 'Неизвестно')
        title = event_data.get('text', 'Описание недоступно')
        if year == 'Неизвестно':
            year_match = re.search(r'\b(\d{4})\b', title)
            if year_match:
                year = year_match.group(1)
    else:
        year = '2023'
        title = 'Для этой стороны не выбрано событие.'
    
    current_day = day
    current_month_name = RUSSIAN_MONTHS[month]
    
    # === БЛОК 1: ЗАГОЛОВОК (высота 520px) ===
    header_block_height = 520
    header_top = 10
    header_bottom = header_top + header_block_height - 10
    
    # Дата по центру
    date_text = f"{current_day} {current_month_name}"
    date_bbox = draw.textbbox((0, 0), date_text, font=font_title)
    date_height = date_bbox[3] - date_bbox[1]
    
    # Подзаголовок
    subtitle_text = "этот день в истории"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_subtitle)
    subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
    
    # Центрируем по вертикале в блоке 520px
    total_header_height = date_height + 20 + subtitle_height
    header_content_top = header_top + (header_block_height - total_header_height) // 2
    
    # Дата
    date_x = (width - date_bbox[2]) // 2
    date_y = header_content_top
    draw.text((date_x, date_y), date_text, fill='white', font=font_title)
    
    # Подзаголовок
    subtitle_x = (width - subtitle_bbox[2]) // 2
    subtitle_y = date_y + date_height + 20
    draw.text((subtitle_x, subtitle_y), subtitle_text, fill='white', font=font_subtitle)
    
    # Рамка вокруг заголовка
    draw.rectangle([10, header_top, width-10, header_bottom], outline='white', width=2)
    
    # === БЕЛАЯ ПОЛОСА 2px ===
    line1_y = header_bottom
    draw.line([10, line1_y, width-10, line1_y], fill='white', width=2)
    
    # === БЛОК 2: ГОД (высота 200px) ===
    year_block_top = line1_y + 2
    year_block_height = 200
    year_block_bottom = year_block_top + year_block_height
    
    # "В {год} году" по центру
    year_text = f"В {year} году"
    year_bbox = draw.textbbox((0, 0), year_text, font=font_year)
    year_height = year_bbox[3] - year_bbox[1]
    
    # Центрируем по вертикале в блоке 200px
    year_y = year_block_top + (year_block_height - year_height) // 2
    year_x = (width - year_bbox[2]) // 2
    draw.text((year_x, year_y), year_text, fill='white', font=font_year)
    
    # Рамка вокруг года
    draw.rectangle([10, year_block_top, width-10, year_block_bottom-10], outline='white', width=2)
    
    # === БЕЛАЯ ПОЛОСА 2px ===
    line2_y = year_block_bottom
    draw.line([10, line2_y, width-10, line2_y], fill='white', width=2)
    
    # === БЛОК 3: ТЕКСТ СОБЫТИЯ ===
    text_block_top = line2_y + 2
    text_block_height = 300
    text_block_bottom = text_block_top + text_block_height
    
    if event_data:
        event_text = event_data.get('text', 'Описание недоступно')
    else:
        event_text = 'Для этой стороны не выбрано событие.'
    
    draw_centered_text(draw, event_text, text_block_top + text_block_height//2, width, font_event_text)
    
    # Рамка вокруг текста
    draw.rectangle([10, text_block_top, width-10, text_block_bottom-10], outline='white', width=2)
    
    # === БЕЛАЯ ПОЛОСА 2px ===
    line3_y = text_block_bottom
    draw.line([10, line3_y, width-10, line3_y], fill='white', width=2)
    
    # === БЛОК 4: КАРТИНКА (высота ~846px) ===
    img_block_top = line3_y + 2
    img_block_height = 846
    img_block_bottom = img_block_top + img_block_height
    
    # Получаем изображение (пробуем несколько источников)
    img_obj = None
    if event_data:
        event_text = event_data.get('text', '')
        img_obj = fetch_image_with_fallback(event_data, event_text)
    
    # Рамка вокруг изображения
    draw.rectangle([10, img_block_top, width-10, img_block_bottom-10], outline='white', width=2)
    
    if img_obj:
        # Максимальные размеры для изображения с отступом 5px
        max_img_width = width - 20 - 10  # 520 - 20 (рамка) - 10 (отступы)
        max_img_height = img_block_height - 20 - 10  # 1146 - 20 (рамка) - 10 (отступы)
        
        # Изменяем размер с сохранением пропорций
        img_obj.thumbnail((max_img_width, max_img_height), Image.Resampling.LANCZOS)
        
        # Центрируем изображение в блоке
        img_x = (width - img_obj.width) // 2
        img_y = img_block_top + (img_block_height - img_obj.height) // 2
        img.paste(img_obj, (img_x, img_y))
    else:
        # Текст "Изображение недоступно"
        no_img_text = "Изображение недоступно"
        no_img_bbox = draw.textbbox((0, 0), no_img_text, font=font_small)
        no_img_x = (width - no_img_bbox[2]) // 2
        no_img_y = img_block_top + (img_block_height - no_img_bbox[3]) // 2
        draw.text((no_img_x, no_img_y), no_img_text, fill='white', font=font_small)
    
    # === БЕЛАЯ ПОЛОСА 2px (нижняя) ===
    line3_y = img_block_bottom
    draw.line([10, line3_y, width-10, line3_y], fill='white', width=2)
    
    # Добавляем маскот в правый нижний угол (150x150px, без рамки)
    mascot_img = load_mascot_image(side_number)
    if mascot_img:
        # Позиция: выше на 25px и левее на 25px от правого нижнего угла
        mascot_x = width - 150 - 25  # 25px левее
        mascot_y = height - 150 - 25  # 25px выше
        # Используем alpha_composite для поддержки прозрачности
        if mascot_img.mode == 'RGBA':
            img.paste(mascot_img, (mascot_x, mascot_y), mascot_img)
        else:
            img.paste(mascot_img, (mascot_x, mascot_y))
    
    return img

def select_four_different_events(events):
    """Выбрать четыре разных события для четырех сторон."""
    if not events:
        return [None, None, None, None]
    
    # Если событий меньше 4, дублируем их
    if len(events) < 4:
        # Повторяем события пока не получим 4 стороны
        selected = []
        for i in range(4):
            selected.append(events[i % len(events)])
        return selected
    
    # Если событий 4 или больше, выбираем первые 4 разных
    return events[:4]

def main():
    """Главная функция программы."""
    # Проверка, предоставлены ли аргументы даты
    if len(sys.argv) == 3:
        try:
            month = int(sys.argv[1])
            day = int(sys.argv[2])
            # Валидация даты
            datetime.datetime(2000, month, day)  # Вызовет ValueError если дата неверна
            generate_for_date(month, day)
        except ValueError as e:
            print(f"Ошибка: Неверная дата: {e}")
            print("Использование: python four_sided_display.py <месяц> <день>")
            print("Пример: python four_sided_display.py 4 15")
            sys.exit(1)
    elif len(sys.argv) == 1:
        # Нет аргументов - используем текущую дату
        today = datetime.datetime.now()
        month = today.month
        day = today.day
        print(f"Дата не указана, используется текущая дата: {month:02d}/{day:02d}")
        generate_for_date(month, day)
    else:
        print("Использование: python four_sided_display.py [<месяц> <день>]")
        print("Если аргументы не предоставлены, используется текущая дата")
        print("Пример: python four_sided_display.py 4 15")
        sys.exit(1)

def generate_for_date(month, day):
    """Сгенерировать четыре стороны для конкретной даты."""
    print(f"Генерация четырех сторон для {month:02d}/{day:02d}")
    
    # Получение событий из русской Википедии (отфильтрованных до 2000 года)
    events = fetch_russian_wikipedia_events(month, day)
    print(f"Найдено {len(events)} событий до 2000 года")
    
    # Выбор четырех событий для четырех сторон
    selected_events = select_four_different_events(events)
    print(f"Выбрано {len([e for e in selected_events if e is not None])} событий для сторон")
    
    # Находим оптимальный размер шрифта для текста событий
    font_path = None
    for fn in ["IskraCYR-BoldItalic.otf", "IskraCyrillic.ttf", "arial.ttf"]:
        if os.path.exists(fn):
            font_path = fn
            break
    
    if font_path:
        event_texts = [e.get('text', '') if e else '' for e in selected_events]
        text_block_width = 520 - 20  # 10px отступы слева и справа
        text_block_height = 300 - 4   # минус рамка
        optimal_font_size = find_optimal_font_size(event_texts, text_block_width, text_block_height, font_path)
        print(f"  Оптимальный размер шрифта для текста событий: {optimal_font_size}")
    else:
        optimal_font_size = 40
    
    # Список для хранения base64 изображений
    base64_images = []
    
    # Генерация каждой стороны
    side_images = []
    for i, event in enumerate(selected_events):
        side_num = i + 1
        print(f"Создание стороны {side_num}...")
        
        # Создание дисплея для этой стороны
        img = create_side_display(month, day, event, side_num, optimal_font_size)
        side_images.append(img)
        
        # Сохранение изображения
        filename = f"сторона_{side_num}_{month:02d}_{day:02d}.png"
        img.save(filename)
        print(f"Изображение стороны {side_num} сохранено как {filename}")
        print(f"  Размеры: {img.size}")
        
        # Конвертирование в base64 и сохранение
        base64_str = image_to_base64(img, 'PNG')
        base64_images.append({
            'side': side_num,
            'filename': filename,
            'base64': base64_str,
            'year': event.get('year', 'Неизвестно') if event else 'Нет события',
            'title': event.get('text', 'Нет описания')[:100] if event else 'Нет события'
        })
    
    # Создание объединенного изображения 2080x1872 (4 стороны по 520px)
    print("Создание объединенного изображения...")
    combined_width = 2080
    combined_height = 1872
    bg_color = (35, 54, 61)
    combined_img = Image.new('RGB', (combined_width, combined_height), color=bg_color)
    
    # Вставляем каждую сторону в нужное место
    side_width = 520
    for i, side_img in enumerate(side_images):
        x_offset = i * side_width
        combined_img.paste(side_img, (x_offset, 0))
    
    # Рисуем вертикальные разделители между сторонами (белые линии 2px)
    draw_combined = ImageDraw.Draw(combined_img)
    for i in range(1, 4):
        x = i * side_width
        draw_combined.line([x, 0, x, combined_height], fill='white', width=2)
    
    # Сохранение объединенного изображения
    combined_filename = f"исторический_экран_{month:02d}_{day:02d}.png"
    combined_img.save(combined_filename)
    print(f"Объединенное изображение сохранено как {combined_filename}")
    print(f"  Размеры: {combined_img.size}")
    
    # Сохранение base64 данных в JSON файл
    log_data = {
        'date': f"{month:02d}/{day:02d}",
        'generated_at': datetime.datetime.now().isoformat(),
        'total_events_found': len(events),
        'sides': base64_images,
        'combined_image': {
            'filename': combined_filename,
            'base64': image_to_base64(combined_img, 'PNG'),
            'size': f"{combined_width}x{combined_height}"
        }
    }
    
    log_filename = f"log_base64_{month:02d}_{day:02d}.json"
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"Base64 данные сохранены в файл: {log_filename}")
    print(f"Генерация завершена. Создано 4 файла + 1 объединенный для {month:02d}/{day:02d}.")

if __name__ == "__main__":
    main()