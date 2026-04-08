import requests
from PIL import Image, ImageDraw, ImageFont, ImageTk
import io
import datetime
import textwrap
import os
import sys
import re
import base64
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread
import urllib.parse
import traceback

# Global exception handler
def global_except_hook(exc_type, exc_value, exc_tb):
    with open('crash_log.txt', 'w', encoding='utf-8') as f:
        f.write(f"Error: {exc_type}: {exc_value}\n")
        traceback.print_tb(exc_tb, file=f)
    print(f"CRASH: {exc_type}: {exc_value}")

sys.excepthook = global_except_hook

# User-Agent header for API requests
HEADERS = {
    'User-Agent': 'HistoricalDisplayGUI/1.0 (https://example.com; contact@example.com)'
}

# Russian month names
RUSSIAN_MONTHS = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
}

# Color scheme
BG_COLOR_START = (35, 54, 61)    # #23363d
BG_COLOR_END = (32, 178, 170)    # #20B2AA
TEXT_COLOR = 'white'

class HistoricalDisplayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор исторического дисплея")
        self.root.geometry("1100x750")
        
        # Create gradient background canvas
        self.bg_canvas = tk.Canvas(root, width=1100, height=750, highlightthickness=0)
        self.bg_canvas.pack(fill='both')
        self.draw_main_gradient()
        
        # Data storage
        self.events_data = {}
        self.current_date = datetime.datetime.now()
        self.sides_data = [
            {'year': '', 'event': '', 'image_url': '', 'image': None},
            {'year': '', 'event': '', 'image_url': '', 'image': None},
            {'year': '', 'event': '', 'image_url': '', 'image': None},
            {'year': '', 'event': '', 'image_url': '', 'image': None}
        ]
        
        # Load font
        self.load_font()
        
        # Create UI - wrapped in try
        try:
            self.create_ui()
        except Exception as e:
            print(f"Error creating UI: {e}")
            import traceback
            traceback.print_exc()
        
    def load_font(self):
        """Try to load Iskra font."""
        font_candidates = [
            "IskraCYR-BoldItalic.otf",
            "arial.ttf",
            "ARIAL.TTF"
        ]
        for font_name in font_candidates:
            try:
                self.font_title = ImageFont.truetype(font_name, 90)
                self.font_subtitle = ImageFont.truetype(font_name, 60)
                self.font_year = ImageFont.truetype(font_name, 72)
                self.font_small = ImageFont.truetype(font_name, 52)
                return True
            except:
                continue
        # Default fonts
        self.font_title = ImageFont.load_default()
        self.font_subtitle = ImageFont.load_default()
        self.font_year = ImageFont.load_default()
        self.font_small = ImageFont.load_default()
        return False
    
    def draw_main_gradient(self):
        """Draw gradient on main canvas."""
        self.bg_canvas.delete('all')
        for i in range(750):
            t = i / 750
            r = int(35 + (32 - 35) * t)
            g = int(54 + (178 - 54) * t)
            b = int(61 + (170 - 61) * t)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.bg_canvas.create_line(0, i, 1100, i, fill=color)
        
    def create_ui(self):
        # Title
        title_label = tk.Label(self.bg_canvas, text="Генератор исторического дисплея", 
                              font=("Arial", 16, "bold"), fg="white", bg="#23363d")
        title_label.pack(pady=5)
        
        # Main container
        main_frame = tk.Frame(self.bg_canvas, bg="#23363d")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side - controls (wider)
        left_frame = tk.Frame(main_frame, bg="#23363d", width=450)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        left_frame.pack_propagate(False)
        
        # Date selection (compact)
        date_frame = tk.LabelFrame(left_frame, text="Дата", font=("Arial", 10, "bold"),
                                   fg="white", bg="#23363d", bd=1, relief=tk.GROOVE, padx=5, pady=3)
        date_frame.pack(fill=tk.X, pady=2)
        
        date_inner = tk.Frame(date_frame, bg="#23363d")
        date_inner.pack()
        
        tk.Label(date_inner, text="День:", fg="white", bg="#23363d", font=("Arial", 9)).grid(row=0, column=0)
        self.day_var = tk.StringVar(value=str(self.current_date.day))
        tk.Spinbox(date_inner, from_=1, to=31, textvariable=self.day_var, width=3).grid(row=0, column=1, padx=1)
        
        tk.Label(date_inner, text="Месяц:", fg="white", bg="#23363d", font=("Arial", 9)).grid(row=0, column=2, padx=1)
        self.month_var = tk.StringVar(value=str(self.current_date.month))
        ttk.Combobox(date_inner, textvariable=self.month_var, values=[str(i) for i in range(1, 13)], width=3).grid(row=0, column=3, padx=1)
        
        tk.Button(date_inner, text="Загрузить", command=self.load_events, bg="#4a6fa5", fg="white", font=("Arial", 8)).grid(row=0, column=7, padx=2)
        
        self.status_label = tk.Label(date_frame, text="Выберите дату", fg="#aaaaaa", bg="#23363d", font=("Arial", 8))
        self.status_label.pack()
        
        # Side controls (all 4 in compact rows) - wider event dropdown
        for i in range(4):
            side_frame = tk.LabelFrame(left_frame, text=f"Сторона {i+1}", font=("Arial", 9, "bold"),
                                       fg="white", bg="#23363d", bd=1, relief=tk.GROOVE, padx=5, pady=3)
            side_frame.pack(fill=tk.X, pady=2)
            self.create_side_controls_wide(side_frame, i)
        
        # Folder and buttons (compact)
        folder_frame = tk.LabelFrame(left_frame, text="Сохранение", font=("Arial", 9, "bold"),
                                     fg="white", bg="#23363d", bd=1, relief=tk.GROOVE, padx=5, pady=3)
        folder_frame.pack(fill=tk.X, pady=2)
        
        self.save_folder_var = tk.StringVar(value=os.getcwd())
        tk.Entry(folder_frame, textvariable=self.save_folder_var, width=35, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(folder_frame, text="...", command=self.browse_folder, bg="#4a6fa5", fg="white", width=3).pack(side=tk.LEFT, padx=2)
        
        btn_inner = tk.Frame(folder_frame, bg="#23363d")
        btn_inner.pack(pady=3)
        tk.Button(btn_inner, text="Собрать", command=self.generate_image, bg="#2d8f4e", fg="white", font=("Arial", 9, "bold"), width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_inner, text="Сохранить", command=self.save_image, bg="#4a6fa5", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Right side - 4 preview windows
        right_frame = tk.Frame(main_frame, bg="#23363d")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 4 preview canvases in 2x2 grid
        for i in range(4):
            preview_frame = tk.LabelFrame(right_frame, text=f"Сторона {i+1}", font=("Arial", 9),
                                         fg="white", bg="#23363d", bd=1, relief=tk.GROOVE)
            preview_frame.grid(row=i//2, column=i%2, padx=3, pady=3, sticky="nsew")
            
            self.sides_data[i]['mini_canvas'] = tk.Canvas(preview_frame, bg="#23363d", width=260, height=310)
            self.sides_data[i]['mini_canvas'].pack(pady=3)
        
        # Configure grid weights
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_columnconfigure(1, weight=1)
        
    def create_side_controls_wide(self, parent, side_num):
        """Create wider controls for one side."""
        # Year
        year_frame = tk.Frame(parent, bg="#23363d")
        year_frame.pack(fill=tk.X, pady=1)
        tk.Label(year_frame, text="Год:", fg="white", bg="#23363d", font=("Arial", 8), width=4).pack(side=tk.LEFT)
        self.sides_data[side_num]['year_var'] = tk.StringVar()
        tk.Entry(year_frame, textvariable=self.sides_data[side_num]['year_var'], width=5, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        
        # Event - wider dropdown
        event_frame = tk.Frame(parent, bg="#23363d")
        event_frame.pack(fill=tk.X, pady=1)
        tk.Label(event_frame, text="Событие:", fg="white", bg="#23363d", font=("Arial", 8), width=7).pack(side=tk.LEFT)
        self.sides_data[side_num]['event_var'] = tk.StringVar()
        self.sides_data[side_num]['event_combo'] = ttk.Combobox(event_frame, 
                                                                  textvariable=self.sides_data[side_num]['event_var'],
                                                                  state='readonly', width=25, font=("Arial", 8))
        self.sides_data[side_num]['event_combo'].pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.sides_data[side_num]['event_combo'].bind('<<ComboboxSelected>>', lambda e, s=side_num: self.on_event_select(s))

        # Image with progress bar
        img_frame = tk.Frame(parent, bg="#23363d")
        img_frame.pack(fill=tk.X, pady=1)
        tk.Label(img_frame, text="Картинка:", fg="white", bg="#23363d", font=("Arial", 8), width=7).pack(side=tk.LEFT)
        self.sides_data[side_num]['image_var'] = tk.StringVar()
        self.sides_data[side_num]['image_combo'] = ttk.Combobox(img_frame,
                                                                  textvariable=self.sides_data[side_num]['image_var'],
                                                                  state='readonly', width=25, font=("Arial", 8))
        self.sides_data[side_num]['image_combo'].pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.sides_data[side_num]['image_combo'].bind('<<ComboboxSelected>>', lambda e, s=side_num: self.on_image_select(s))
        
        # Progress bar for this side
        self.sides_data[side_num]['progress'] = ttk.Progressbar(img_frame, mode='indeterminate', length=50)
        self.sides_data[side_num]['progress'].pack(side=tk.LEFT, padx=2)
        
        tk.Button(img_frame, text="Загр", command=lambda s=side_num: self.load_images_async(s), bg="#4a6fa5", fg="white", font=("Arial", 7), width=4).pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.sides_data[side_num]['status_label'] = tk.Label(img_frame, text="", fg="#aaaaaa", bg="#23363d", font=("Arial", 7))
        self.sides_data[side_num]['status_label'].pack(side=tk.LEFT, padx=2)

    def on_event_text_edit(self, side_num):
        """Handle manual edit of event text in mini preview."""
        text_widget = self.sides_data[side_num].get('event_text_widget')
        if text_widget:
            edited_text = text_widget.get("1.0", tk.END).strip()
            self.sides_data[side_num]['edited_event_text'] = edited_text
            text_widget.edit_modified(False)
        
    def refresh_mini_preview(self, side_num):
        """Refresh mini preview with current event text (from dropdown or edited)."""
        try:
            idx = self.sides_data[side_num]['event_combo'].current()
            edited_text = self.sides_data[side_num].get('edited_event_text', '')
            
            if edited_text:
                event_text = edited_text
            elif idx == 0:
                event_text = ''
            else:
                date_key = f"{int(self.month_var.get()):02d}_{int(self.day_var.get()):02d}"
                if date_key in self.events_data and idx-1 < len(self.events_data[date_key]):
                    event_text = self.events_data[date_key][idx-1].get('text', '')
                else:
                    event_text = ''
            
            img_obj = self.sides_data[side_num].get('image')
            if img_obj:
                self.update_mini_preview_with_image(side_num, event_text, img_obj)
            else:
                self.update_mini_preview(side_num, event_text)
        except Exception as e:
            print(f"Error in refresh_mini_preview: {e}")
        
    def create_side_controls_compact(self, parent, side_num):
        """Create compact controls for one side."""
        # Year
        year_frame = tk.Frame(parent, bg="#23363d")
        year_frame.pack(fill=tk.X, pady=1)
        tk.Label(year_frame, text="Год:", fg="white", bg="#23363d", font=("Arial", 8), width=4).pack(side=tk.LEFT)
        self.sides_data[side_num]['year_var'] = tk.StringVar()
        tk.Entry(year_frame, textvariable=self.sides_data[side_num]['year_var'], width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        
        # Event
        event_frame = tk.Frame(parent, bg="#23363d")
        event_frame.pack(fill=tk.X, pady=1)
        tk.Label(event_frame, text="Соб:", fg="white", bg="#23363d", font=("Arial", 8), width=4).pack(side=tk.LEFT)
        self.sides_data[side_num]['event_var'] = tk.StringVar()
        self.sides_data[side_num]['event_combo'] = ttk.Combobox(event_frame, 
                                                                  textvariable=self.sides_data[side_num]['event_var'],
                                                                  state='readonly', width=18, font=("Arial", 8))
        self.sides_data[side_num]['event_combo'].pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.sides_data[side_num]['event_combo'].bind('<<ComboboxSelected>>', lambda e, s=side_num: self.on_event_select(s))
        
        # Manual event
        self.sides_data[side_num]['manual_event_var'] = tk.StringVar()
        tk.Entry(event_frame, textvariable=self.sides_data[side_num]['manual_event_var'], width=15, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        
        # Image with progress bar
        img_frame = tk.Frame(parent, bg="#23363d")
        img_frame.pack(fill=tk.X, pady=1)
        tk.Label(img_frame, text="Кар:", fg="white", bg="#23363d", font=("Arial", 8), width=4).pack(side=tk.LEFT)
        self.sides_data[side_num]['image_var'] = tk.StringVar()
        self.sides_data[side_num]['image_combo'] = ttk.Combobox(img_frame,
                                                                  textvariable=self.sides_data[side_num]['image_var'],
                                                                  state='readonly', width=18, font=("Arial", 8))
        self.sides_data[side_num]['image_combo'].pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.sides_data[side_num]['image_combo'].bind('<<ComboboxSelected>>', lambda e, s=side_num: self.on_image_select(s))
        
        # Progress bar for this side
        self.sides_data[side_num]['progress'] = ttk.Progressbar(img_frame, mode='indeterminate', length=60)
        self.sides_data[side_num]['progress'].pack(side=tk.LEFT, padx=2)
        
        tk.Button(img_frame, text="Загр", command=lambda s=side_num: self.load_images_async(s), bg="#4a6fa5", fg="white", font=("Arial", 7), width=5).pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.sides_data[side_num]['status_label'] = tk.Label(img_frame, text="", fg="#aaaaaa", bg="#23363d", font=("Arial", 7))
        self.sides_data[side_num]['status_label'].pack(side=tk.LEFT, padx=2)
        
    def load_events(self):
        """Load events for selected date."""
        try:
            day = int(self.day_var.get())
            month = int(self.month_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты")
            return
        
        self.status_label.config(text="Загрузка событий...")
        
        # Fetch events from Wikipedia
        url = f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month:02d}/{day:02d}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
            events = data.get('events', [])
            
            # Filter for events before current year
            current_year = datetime.datetime.now().year
            filtered_events = []
            for event in events:
                event_year = event.get('year')
                if event_year and isinstance(event_year, int) and event_year <= current_year:
                    filtered_events.append(event)
            
            # Store events (max 100)
            date_key = f"{month:02d}_{day:02d}"
            self.events_data[date_key] = filtered_events[:100]
            
            # Update dropdowns for each side
            for i in range(4):
                event_list = [f"{e.get('year', '???')} - {e.get('text', 'Событие')[:50]}..." 
                             for e in self.events_data[date_key]]
                event_list.insert(0, "Ввести вручную...")
                self.sides_data[i]['event_combo']['values'] = event_list
                if event_list:
                    self.sides_data[i]['event_combo'].current(0)
            
            self.status_label.config(text=f"Загружено {len(filtered_events[:100])} событий")
            
        except Exception as e:
            self.status_label.config(text=f"Ошибка загрузки: {str(e)}")
            
    def on_event_select(self, side_num):
        """Handle event selection - show text in preview."""
        try:
            idx = self.sides_data[side_num]['event_combo'].current()
            if idx == 0:  # Manual / edited input
                self.sides_data[side_num]['year_var'].set('')
                event_text = self.sides_data[side_num].get('edited_event_text', '')
            else:
                date_key = f"{int(self.month_var.get()):02d}_{int(self.day_var.get()):02d}"
                if date_key in self.events_data and idx-1 < len(self.events_data[date_key]):
                    event = self.events_data[date_key][idx-1]
                    year = event.get('year', '')
                    event_text = event.get('text', '')
                    self.sides_data[side_num]['year_var'].set(str(year))
                    
                    # Clear edited text when selecting from dropdown
                    self.sides_data[side_num]['edited_event_text'] = ''
                    
                    # Auto-load images asynchronously
                    self.load_images_async(side_num)
                else:
                    event_text = ''
            
            # Update mini preview with event text
            img_obj = self.sides_data[side_num].get('image')
            if img_obj:
                self.update_mini_preview_with_image(side_num, event_text, img_obj)
            else:
                self.update_mini_preview(side_num, event_text)
        except Exception as e:
            print(f"Error in on_event_select: {e}")
        
    def on_image_select(self, side_num):
        """Handle image selection - show in preview."""
        try:
            idx = self.sides_data[side_num]['image_combo'].current()
            
            if idx > 0:  # Has image selected
                images = self.sides_data[side_num].get('available_images', [])
                if images and idx-1 < len(images):
                    try:
                        img_obj = self.download_image(images[idx-1])
                        if img_obj:
                            self.sides_data[side_num]['image'] = img_obj
                            self.refresh_mini_preview(side_num)
                            return
                    except Exception as e:
                        print(f"Error loading image: {e}")
            
            # No image - clear and show text
            self.sides_data[side_num]['image'] = None
            self.refresh_mini_preview(side_num)
        except Exception as e:
            print(f"Error in on_image_select: {e}")
        
    def update_mini_preview(self, side_num, event_text):
        """Update mini preview canvas with editable event text."""
        canvas = self.sides_data[side_num]['mini_canvas']
        canvas.delete('all')
        
        width = 260
        height = 310
        
        # Draw background with gradient
        self.draw_gradient_bg(canvas, width, height)
        
        # Draw date
        day = int(self.day_var.get())
        month = int(self.month_var.get())
        date_text = f"{day} {RUSSIAN_MONTHS[month][:3]}"
        canvas.create_text(width//2, 15, text=date_text, fill='white', font=('Arial', 13, 'bold'), justify='center')
        
        # Draw subtitle
        canvas.create_text(width//2, 32, text="этот день в истории", fill='white', font=('Arial', 11))
        
        # Separator
        canvas.create_line(5, 48, width-5, 48, fill='white', width=4)
        
        # Draw year
        year = self.sides_data[side_num]['year_var'].get()
        year_text = f"В {year} году" if year else "В ???? году"
        canvas.create_text(width//2, 65, text=year_text, fill='white', font=('Arial', 14, 'bold'), justify='center')
        
        # Separator
        canvas.create_line(5, 82, width-5, 82, fill='white', width=4)
        
        # Event text area (editable) - top part ~80px
        text_area_top = 90
        text_area_height = 80
        canvas.create_rectangle(5, text_area_top, width-5, text_area_top + text_area_height, fill='#1a2a30', outline='white', width=4)
        
        # Store or update editable text widget
        if 'event_text_widget' not in self.sides_data[side_num]:
            text_widget = tk.Text(canvas, width=32, height=3, font=('Arial', 7), bg='#1a2a30', fg='white', bd=0)
            text_widget.place(x=10, y=text_area_top + 5, width=width-20, height=text_area_height-10)
            self.sides_data[side_num]['event_text_widget'] = text_widget
            text_widget.insert("1.0", event_text)
            text_widget.bind('<<Modified>>', lambda e, s=side_num: self.on_event_text_edit(s))
        else:
            text_widget = self.sides_data[side_num]['event_text_widget']
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", event_text)
        
        # Image area (below text)
        canvas.create_text(width//2, 220, text="[Картинка]", fill='#888888', font=('Arial', 8))
        
        # Mascot area
        canvas.create_rectangle(width-45, height-35, width-5, height-5, outline='#666666', width=1)
        canvas.create_text(width-25, height-20, text="Маскот", fill='#666666', font=('Arial', 6))
        
    def update_mini_preview_with_image(self, side_num, event_text, img_obj):
        """Update mini preview with editable event text AND image (text above, image below)."""
        canvas = self.sides_data[side_num]['mini_canvas']
        canvas.delete('all')
        
        width = 260
        height = 310
        
        # Draw background with gradient
        self.draw_gradient_bg(canvas, width, height)
        
        # Draw date
        day = int(self.day_var.get())
        month = int(self.month_var.get())
        date_text = f"{day} {RUSSIAN_MONTHS[month][:3]}"
        canvas.create_text(width//2, 15, text=date_text, fill='white', font=('Arial', 13, 'bold'), justify='center')
        canvas.create_text(width//2, 32, text="Этот день", fill='white', font=('Arial', 11))
        canvas.create_text(width//2, 46, text="в истории", fill='white', font=('Arial', 11))
        
        canvas.create_line(5, 58, width-5, 58, fill='white', width=4)
        
        year = self.sides_data[side_num]['year_var'].get()
        year_text = f"В {year} году" if year else "В ???? году"
        canvas.create_text(width//2, 72, text=year_text, fill='white', font=('Arial', 14, 'bold'), justify='center')
        
        canvas.create_line(5, 88, width-5, 88, fill='white', width=4)
        
        # Event text area (editable) - top part ~80px
        text_area_top = 95
        text_area_height = 80
        canvas.create_rectangle(5, text_area_top, width-5, text_area_top + text_area_height, fill='#1a2a30', outline='white', width=4)
        
        if 'event_text_widget' not in self.sides_data[side_num]:
            text_widget = tk.Text(canvas, width=32, height=3, font=('Arial', 7), bg='#1a2a30', fg='white', bd=0)
            text_widget.place(x=10, y=text_area_top + 5, width=width-20, height=text_area_height-10)
            self.sides_data[side_num]['event_text_widget'] = text_widget
            text_widget.insert("1.0", event_text)
            text_widget.bind('<<Modified>>', lambda e, s=side_num: self.on_event_text_edit(s))
        else:
            text_widget = self.sides_data[side_num]['event_text_widget']
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", event_text)
        
        # Image (in bottom area ~170px)
        if img_obj:
            img_obj_copy = img_obj.copy()
            img_obj_copy.thumbnail((width-20, 170), Image.Resampling.LANCZOS)
            try:
                photo = ImageTk.PhotoImage(img_obj_copy)
                canvas.create_image(width//2, 235, image=photo, anchor=tk.CENTER, tags=('img',))
                canvas.image = photo
                
                # Store original image for zoom (not thumbnail)
                self.sides_data[side_num]['preview_img'] = img_obj
                self.sides_data[side_num]['preview_zoom'] = False
                
                canvas.tag_bind('img', '<Button-1>', lambda e, s=side_num: self.toggle_image_zoom(s))
            except:
                canvas.create_text(width//2, 220, text="[Изображение]", fill='#888888', font=('Arial', 8))
        
        # Mascot
        canvas.create_rectangle(width-45, height-35, width-5, height-5, outline='#666666', width=1)
        canvas.create_text(width-25, height-20, text="Маскот", fill='#666666', font=('Arial', 6))
    
    def draw_gradient_bg(self, canvas, width, height):
        """Draw gradient background on canvas."""
        steps = 50
        for i in range(steps):
            t = i / steps
            r = int(35 + (32 - 35) * t)
            g = int(54 + (178 - 54) * t)
            b = int(61 + (170 - 61) * t)
            color = f'#{r:02x}{g:02x}{b:02x}'
            y = int(i * height / steps)
            next_y = int((i + 1) * height / steps)
            canvas.create_rectangle(0, y, width, next_y, fill=color, outline='')
    
    def toggle_image_zoom(self, side_num):
        """Toggle image zoom - show in popup window centered on screen."""
        try:
            if self.sides_data[side_num].get('preview_zoom', False):
                # Close zoom window
                if 'zoom_window' in self.sides_data[side_num] and self.sides_data[side_num].get('zoom_window'):
                    win = self.sides_data[side_num]['zoom_window']
                    try:
                        win.destroy()
                    except:
                        pass
                    self.sides_data[side_num]['zoom_window'] = None
                self.sides_data[side_num]['preview_zoom'] = False
            else:
                # Open zoom window - full screen
                self.sides_data[side_num]['preview_zoom'] = True
                
                img_obj = self.sides_data[side_num].get('preview_img')
                if not img_obj:
                    self.sides_data[side_num]['preview_zoom'] = False
                    return
                
                # Get screen size
                ws = self.root.winfo_screenwidth()
                hs = self.root.winfo_screenheight()
                
                # Create popup window
                win = tk.Toplevel(self.root)
                win.title(f"Сторона {side_num + 1} - Увеличено")
                win.geometry(f"{ws}x{hs}+0+0")
                win.attributes('-fullscreen', True)
                win.attributes('-topmost', True)
                
                # Create canvas
                canvas = tk.Canvas(win, bg='#23363d', width=ws, height=hs)
                canvas.pack()
                
                # Scale image to fit screen while maintaining aspect ratio
                zoomed = img_obj.copy()
                zoomed.thumbnail((ws-100, hs-100), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(zoomed)
                canvas.create_image(ws//2, hs//2, image=photo, anchor=tk.CENTER, tags=('img',))
                canvas.image = photo
                
                # Bind click anywhere to close
                canvas.tag_bind('img', '<Button-1>', lambda e: self._close_zoom_window(side_num))
                canvas.bind('<Button-1>', lambda e: self._close_zoom_window(side_num))
                
                # Store window reference
                self.sides_data[side_num]['zoom_window'] = win
                
                # Clean up when window is closed
                win.protocol("WM_DELETE_WINDOW", lambda: self._close_zoom_window(side_num))
        except Exception as e:
            print(f"Zoom error: {e}")
            self.sides_data[side_num]['preview_zoom'] = False
    
    def _close_zoom_window(self, side_num):
        """Close zoom window."""
        try:
            if 'zoom_window' in self.sides_data[side_num] and self.sides_data[side_num].get('zoom_window'):
                win = self.sides_data[side_num]['zoom_window']
                try:
                    win.destroy()
                except:
                    pass
                self.sides_data[side_num]['zoom_window'] = None
            self.sides_data[side_num]['preview_zoom'] = False
        except:
            pass
                            
    def load_images_async(self, side_num):
        """Load images asynchronously in a separate thread."""
        try:
            # Check if progress bar exists (might be using compact controls)
            if 'progress' not in self.sides_data[side_num]:
                return
            
            # Read values from widgets in main thread
            event_idx = self.sides_data[side_num]['event_combo'].current()
            date_key = f"{int(self.month_var.get()):02d}_{int(self.day_var.get()):02d}"
            events_data = self.events_data.copy()
            
            if event_idx == 0:  # Manual/edited input
                event_text = self.sides_data[side_num].get('edited_event_text', '')
            else:
                if date_key not in events_data:
                    return
                event_text = events_data[date_key][event_idx-1].get('text', '')
            
            if not event_text:
                return
            
            # Start progress bar
            self.sides_data[side_num]['progress'].start(10)
            self.sides_data[side_num]['status_label'].config(text="Загрузка...")
            
            # Run in separate thread - pass data instead of reading from widgets
            thread = Thread(target=self._load_images_thread, args=(side_num, event_idx, date_key, events_data))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"Error in load_images_async: {e}")
        
    def _load_images_thread(self, side_num, event_idx, date_key, events_data):
        """Background thread for loading images."""
        try:
            images = []
            
            if event_idx > 0 and date_key in events_data:
                event_list = events_data[date_key]
                if event_idx-1 < len(event_list):
                    event = event_list[event_idx-1]
                    pages = event.get('pages', [])
                else:
                    pages = []
            else:
                pages = []
            
            for page_idx in range(min(15, len(pages))):
                        page = pages[page_idx]
                        page_title = page.get('title')
                        if not page_title or '_год' in page_title or page_title.isdigit():
                            continue
                        
                        for lang in ['ru', 'en']:
                            try:
                                search_url = f"https://{lang}.wikipedia.org/w/api.php"
                                params = {
                                    'action': 'query',
                                    'format': 'json',
                                    'titles': page_title,
                                    'prop': 'pageimages',
                                    'pithumbsize': 800
                                }
                                response = requests.get(search_url, params=params, headers=HEADERS, timeout=5)
                                if response.status_code == 200:
                                    data = response.json()
                                    pages_result = data.get('query', {}).get('pages', {})
                                    for page_id, page_info in pages_result.items():
                                        if 'thumbnail' in page_info:
                                            img_url = page_info['thumbnail']['source']
                                            if img_url not in images:
                                                images.append(img_url)
                            except:
                                continue
            
            # Update UI in main thread
            self.root.after(0, lambda: self._update_images_ready(side_num, images))
        except Exception as e:
            print(f"Error loading images: {e}")
            self.root.after(0, lambda: self._update_images_ready(side_num, []))
        
    def _update_images_ready(self, side_num, images):
        """Update UI after images are loaded."""
        try:
            # Stop progress bar
            self.sides_data[side_num]['progress'].stop()
            self.sides_data[side_num]['progress'].pack_forget()
            
            # Update status
            self.sides_data[side_num]['status_label'].config(text=f"Найдено: {len(images)}")
            
            # Store available images
            self.sides_data[side_num]['available_images'] = images
            
            # Update dropdown
            image_list = ["Нет картинки"]
            image_list.extend([f"Картинка {i+1}" for i in range(len(images))])
            self.sides_data[side_num]['image_combo']['values'] = image_list
            self.sides_data[side_num]['image_combo'].current(0)
        except Exception as e:
            print(f"Error updating images: {e}")
        
    def download_image(self, url):
        """Download image from URL."""
        try:
            download_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/png,image/jpeg,*/*'
            }
            response = requests.get(url, headers=download_headers, timeout=15)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        except:
            return None
            
    def generate_image(self):
        """Generate the display image."""
        # Get selected date
        try:
            day = int(self.day_var.get())
            month = int(self.month_var.get())
        except:
            messagebox.showerror("Ошибка", "Неверная дата")
            return
        
        # Collect all event texts and calculate global font size
        all_texts = []
        for side_num in range(4):
            event_idx = self.sides_data[side_num]['event_combo'].current()
            edited_text = self.sides_data[side_num].get('edited_event_text', '')
            if edited_text:
                all_texts.append(edited_text)
            elif event_idx > 0:
                date_key = f"{month:02d}_{day:02d}"
                if date_key in self.events_data and event_idx-1 < len(self.events_data[date_key]):
                    all_texts.append(self.events_data[date_key][event_idx-1].get('text', ''))
        
        # Calculate global font size
        event_font_size = self.calculate_event_font_size(all_texts)
            
        # Create side images with global font size
        side_images = []
        for side_num in range(4):
            img = self.create_side_image(month, day, side_num, event_font_size)
            side_images.append(img)
            
        # Create combined image with gradient
        combined_width = 2080
        combined_height = 1872
        combined_img = Image.new('RGB', (combined_width, combined_height))
        draw = ImageDraw.Draw(combined_img)
        for y in range(combined_height):
            t = y / combined_height
            r = int(35 + (32 - 35) * t)
            g = int(54 + (178 - 54) * t)
            b = int(61 + (170 - 61) * t)
            draw.line([(0, y), (combined_width, y)], fill=(r, g, b))
        
        side_width = 520
        for i, side_img in enumerate(side_images):
            combined_img.paste(side_img, (i * side_width, 0))
            
        # Add vertical dividers
        draw = ImageDraw.Draw(combined_img)
        for i in range(1, 4):
            x = i * side_width
            draw.line([x, 0, x, combined_height], fill='white', width=4)
            
        self.combined_image = combined_img
        # self.display_preview(combined_img)  # Disabled - using 4 mini canvases instead

        self.status_label.config(text="Изображение сгенерировано!")
    
    def calculate_event_font_size(self, all_texts):
        """Calculate maximum font size that fits all texts in the block."""
        if not all_texts:
            return 42
        
        padding = 10  # отступ от рамок
        block_width = 500  # ширина между рамками (520 - 20)
        block_height = 340 - padding * 2  # полезная высота блока
        
        for size in range(80, 8, -1):
            try:
                test_font = ImageFont.truetype("IskraCYR-BoldItalic.otf", size)
            except:
                try:
                    test_font = ImageFont.truetype("arial.ttf", size)
                except:
                    continue
            
            fits_all = True
            for text in all_texts:
                if not text:
                    continue
                text_formatted = text[0].upper() + text[1:]
                
                # Определяем оптимальную ширину переноса
                chars_per_line = max(10, int(block_width / (size * 0.5)))
                wrapped = textwrap.fill(text_formatted, width=chars_per_line)
                
                # Проверяем ширину и высоту
                test_img = Image.new('RGB', (block_width, block_height))
                test_draw = ImageDraw.Draw(test_img)
                text_bbox = test_draw.multiline_textbbox((0, 0), wrapped, font=test_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                # Текст должен вписываться с отступами
                if text_height > block_height or text_width > block_width - padding * 2:
                    fits_all = False
                    break
            
            if fits_all:
                return size
        
        return 20
        
    def create_side_image(self, month, day, side_num, event_font_size=42):
        """Create one side of the display."""
        width = 520
        height = 1872
        
        # Create gradient background
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        for y in range(height):
            t = y / height
            r = int(35 + (32 - 35) * t)
            g = int(54 + (178 - 54) * t)
            b = int(61 + (170 - 61) * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Side borders (4px)
        draw.line([2, 0, 2, height], fill='white', width=4)
        draw.line([width-3, 0, width-3, height], fill='white', width=4)
        
        # Get data for this side
        year = self.sides_data[side_num]['year_var'].get()
        
        event_idx = self.sides_data[side_num]['event_combo'].current()
        # Check for edited text first
        edited_text = self.sides_data[side_num].get('edited_event_text', '')
        if edited_text:
            event_text = edited_text
        elif event_idx == 0:  # Manual input
            event_text = ''
        else:
            date_key = f"{month:02d}_{day:02d}"
            if date_key in self.events_data:
                event_text = self.events_data[date_key][event_idx-1].get('text', '')
            else:
                event_text = ''
                
        img_obj = self.sides_data[side_num].get('image')
        
        # === БЛОК 1: ЗАГОЛОВОК (520px) ===
        header_block_height = 520
        header_top = 10
        header_bottom = header_top + header_block_height - 10
        
        date_text = f"{day} {RUSSIAN_MONTHS[month]}"
        date_bbox = draw.textbbox((0, 0), date_text, font=self.font_title)
        date_height = date_bbox[3] - date_bbox[1]
        
        subtitle_text = "этот день в истории"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=self.font_subtitle)
        subtitle_text = "Этот день"
        subtitle2_text = "в истории"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=self.font_subtitle)
        subtitle2_bbox = draw.textbbox((0, 0), subtitle2_text, font=self.font_subtitle)
        subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
        subtitle2_height = subtitle2_bbox[3] - subtitle2_bbox[1]
        line_spacing = 20
        total_subtitle_height = subtitle_height + line_spacing + subtitle2_height
        
        total_header_height = date_height + 30 + total_subtitle_height
        header_content_top = header_top + (header_block_height - total_header_height) // 2
        
        date_x = (width - date_bbox[2]) // 2
        date_y = header_content_top
        draw.text((date_x, date_y), date_text, fill='white', font=self.font_title)
        
        subtitle_x = (width - subtitle_bbox[2]) // 2
        subtitle_y = date_y + date_height + 30
        draw.text((subtitle_x, subtitle_y), subtitle_text, fill='white', font=self.font_subtitle)
        
        subtitle2_x = (width - subtitle2_bbox[2]) // 2
        subtitle2_y = subtitle_y + subtitle_height + line_spacing
        draw.text((subtitle2_x, subtitle2_y), subtitle2_text, fill='white', font=self.font_subtitle)
        
        draw.rectangle([10, header_top, width-10, header_bottom], outline='white', width=4)
        
        # === БЕЛАЯ ПОЛОСА 4px ===
        line1_y = header_bottom
        draw.line([10, line1_y, width-10, line1_y], fill='white', width=4)
        
        # === БЛОК 2: ГОД (200px) ===
        year_block_top = line1_y + 2
        year_block_height = 200
        year_block_bottom = year_block_top + year_block_height
        
        year_text = f"В {year} году" if year else "В ??? году"
        year_bbox = draw.textbbox((0, 0), year_text, font=self.font_year)
        year_height = year_bbox[3] - year_bbox[1]
        
        year_y = year_block_top + (year_block_height - year_height) // 2
        year_x = (width - year_bbox[2]) // 2
        draw.text((year_x, year_y), year_text, fill='white', font=self.font_year)
        
        draw.rectangle([10, year_block_top, width-10, year_block_bottom-10], outline='white', width=4)
        
        # === БЕЛАЯ ПОЛОСА 4px ===
        line2_y = year_block_bottom
        draw.line([10, line2_y, width-10, line2_y], fill='white', width=4)
        
        # === БЛОК 3: 1146px - делится вертикально: текст сверху, картинка снизу ===
        img_block_top = line2_y + 2
        img_block_height = 1146
        img_block_bottom = img_block_top + img_block_height
        
        # Общая рамка вокруг блока
        draw.rectangle([10, img_block_top, width-10, img_block_bottom-10], outline='white', width=4)
        
        # Горизонтальный разделитель между текстом и картинкой (340px текст, 806px картинка)
        text_block_height = 340
        divider_y = img_block_top + text_block_height
        draw.line([10, divider_y, width-10, divider_y], fill='white', width=4)
        
        # === БЛОК 3а: Текст события ===
        text_block_top = img_block_top
        text_block_height = 340
        padding = 10
        block_width = 500
        
        # Текст события - первая буква большая, отцентрован
        if event_text:
            # Делаем первую букву большой
            event_text_formatted = event_text[0].upper() + event_text[1:] if event_text else ""
            
            # Используем переданный размер шрифта
            try:
                event_font = ImageFont.truetype("IskraCYR-BoldItalic.otf", event_font_size)
            except:
                try:
                    event_font = ImageFont.truetype("arial.ttf", event_font_size)
                except:
                    event_font = ImageFont.load_default()
            
            # Определяем оптимальную ширину переноса
            chars_per_line = max(10, int(block_width / (event_font_size * 0.5)))
            wrapped_text = textwrap.fill(event_text_formatted, width=chars_per_line)
            
            # Центрируем по вертикали и горизонтали в блоке с отступами
            text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=event_font)
            text_height = text_bbox[3] - text_bbox[1]
            text_width = text_bbox[2] - text_bbox[0]
            
            text_y = text_block_top + padding + (text_block_height - padding * 2 - text_height) // 2
            text_x = padding + (block_width - text_width) // 2  # центр с учетом отступа
            
            draw.multiline_text((text_x, text_y), wrapped_text, fill='white', font=event_font, align='center')
        
        # === БЛОК 3б: Картинка (нижняя часть, ~806px) ===
        img_subblock_top = divider_y + 2
        img_subblock_bottom = img_block_bottom - 10
        img_subblock_height = img_subblock_bottom - img_subblock_top
        img_subblock_left = 10
        img_subblock_right = width - 10
        img_subblock_width = img_subblock_right - img_subblock_left
        
        # Рамка вокруг картинки
        draw.rectangle([img_subblock_left, img_subblock_top, img_subblock_right, img_subblock_bottom], outline='white', width=4)
        
        if img_obj:
            max_img_width = img_subblock_width - 20
            max_img_height = img_subblock_height - 20
            
            img_obj.thumbnail((max_img_width, max_img_height), Image.Resampling.LANCZOS)
            
            # Центрируем картинку в блоке
            img_x = img_subblock_left + (img_subblock_width - img_obj.width) // 2
            img_y = img_subblock_top + (img_subblock_height - img_obj.height) // 2
            img.paste(img_obj, (img_x, img_y))
        else:
            no_img_text = "Изображение недоступно"
            no_img_bbox = draw.textbbox((0, 0), no_img_text, font=self.font_small)
            no_img_x = img_subblock_left + (img_subblock_width - no_img_bbox[2]) // 2
            no_img_y = img_subblock_top + (img_subblock_height - no_img_bbox[3]) // 2
            draw.text((no_img_x, no_img_y), no_img_text, fill='white', font=self.font_small)
        
        # === БЕЛАЯ ПОЛОСА 2px ===
        line3_y = img_block_bottom
        draw.line([10, line3_y, width-10, line3_y], fill='white', width=2)
        
        # === МАСКОТ ===
        mascot_img = self.load_mascot(side_num + 1)
        if mascot_img:
            mascot_x = width - 150 - 25
            mascot_y = height - 150 - 25
            if mascot_img.mode == 'RGBA':
                img.paste(mascot_img, (mascot_x, mascot_y), mascot_img)
            else:
                img.paste(mascot_img, (mascot_x, mascot_y))
                
        return img
        
    def load_mascot(self, side_number):
        """Load mascot image."""
        mascot_files = {
            1: "Маскот/tsvet_21.png",
            2: "Маскот/tsvet_23.png",
            3: "Маскот/tsvet_28.png",
            4: "Маскот/tsvet_30.png"
        }
        
        try:
            mascot_img = Image.open(mascot_files[side_number])
            mascot_img = mascot_img.resize((150, 150), Image.Resampling.LANCZOS)
            return mascot_img
        except:
            return None
            
    def display_preview(self, img):
        """Display image on canvas."""
        # Convert toPhotoImage
        img.thumbnail((520, 600), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(260, 300, image=self.preview_photo, anchor=tk.CENTER)
        
    def update_preview(self):
        """Update preview with current settings."""
        pass  # Could implement live preview
        
    def browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(initialdir=self.save_folder_var.get())
        if folder:
            self.save_folder_var.set(folder)
            # Open the folder in Explorer
            os.startfile(folder)
            
    def save_image(self):
        """Save the generated image to selected folder."""
        if not hasattr(self, 'combined_image'):
            messagebox.showwarning("Внимание", "Сначала соберите картинку")
            return
            
        # Get save folder
        save_folder = self.save_folder_var.get()
        if not os.path.isdir(save_folder):
            messagebox.showerror("Ошибка", "Указана несуществующая папка")
            return
            
        # Generate filename
        day = self.day_var.get()
        month = self.month_var.get()
        filename = f"исторический_экран_{month}_{day}.png"
        filepath = os.path.join(save_folder, filename)
        
        # Save image
        self.combined_image.save(filepath)
        messagebox.showinfo("Успех", f"Изображение сохранено:\n{filepath}")
            
def main():
    try:
        root = tk.Tk()
        app = HistoricalDisplayApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        
if __name__ == "__main__":
    main()