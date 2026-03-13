import customtkinter as ctk
from tkinter import filedialog, messagebox
from downloader import YourTubeDownloader
import threading
from pathlib import Path
import webbrowser
import pyperclip
import os
import datetime
import io
import sys


class TextRedirector(io.StringIO):
    """Перенаправление stdout/stderr в виджет логов"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, string):
        if string.strip():
            self.text_widget.insert("end", string)
            self.text_widget.see("end")

    def flush(self):
        pass


class YourTubeApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YourTube - Скачивай видео легко")

        self.window.geometry("780x650")
        self.window.minsize(780, 650)
        self.window.maxsize(780, 650)
        self.window.resizable(False, False)

        # Настройка темы
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Инициализация загрузчика
        self.downloader = YourTubeDownloader()
        self.downloader.set_progress_callback(self.update_progress)

        # Переменные
        self.current_url = ""
        self.video_info = None
        self.current_platform = None
        self.download_path = Path("downloads").absolute()
        self.log_file = Path("logs") / f"yourtube_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        Path("logs").mkdir(exist_ok=True)

        self.setup_ui()
        self.setup_hotkeys()
        self.redirect_output()

        self.log("=" * 60)
        self.log(f"🚀 YourTube запущен {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 60)

    def redirect_output(self):
        """Перенаправление stdout и stderr в лог"""
        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)

    def log(self, message):
        """Запись сообщения в лог"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass

    def setup_hotkeys(self):
        """Настройка горячих клавиш"""
        self.window.bind('<Control-v>', self.paste_url)
        self.window.bind('<Command-v>', self.paste_url)
        self.window.bind('<Control-V>', self.paste_url)
        self.window.bind('<Return>', lambda e: self.get_video_info_thread())

        self.window.bind('<Control-c>', self.copy_logs)
        self.window.bind('<Command-c>', self.copy_logs)
        self.window.bind('<Control-l>', self.clear_logs)
        self.window.bind('<Command-l>', self.clear_logs)

    def copy_logs(self, event=None):
        """Копирование логов в буфер обмена"""
        logs = self.log_text.get("1.0", "end-1c")
        if logs:
            try:
                pyperclip.copy(logs)
                self.status_label.configure(text="✅ Логи скопированы")
                self.window.after(2000, lambda: self.status_label.configure(text="✅ Готов к работе"))
            except:
                self.window.clipboard_clear()
                self.window.clipboard_append(logs)
                self.status_label.configure(text="✅ Логи скопированы")
        return "break"

    def clear_logs(self, event=None):
        """Очистка логов"""
        self.log_text.delete("1.0", "end")
        self.log("🧹 Логи очищены")
        return "break"

    def paste_url(self, event=None):
        """Вставка URL из буфера обмена"""
        try:
            try:
                clipboard_text = pyperclip.paste()
            except:
                clipboard_text = self.window.clipboard_get()
        except:
            clipboard_text = ""

        if clipboard_text:
            clipboard_text = clipboard_text.strip()
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, clipboard_text)
            self.log(f"📋 URL вставлен: {clipboard_text[:50]}...")
            self.status_label.configure(text="✅ URL вставлен")

            self.get_video_info_thread()

        return "break"

    def setup_ui(self):
        """Создание интерфейса"""
        # Основной горизонтальный контейнер
        main_container = ctk.CTkFrame(self.window)
        main_container.pack(fill="both", expand=True, padx=8, pady=8)

        # Левая панель (основной интерфейс)
        left_panel = ctk.CTkFrame(main_container, width=420, corner_radius=12)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        left_panel.pack_propagate(False)

        # Правая панель (логи)
        right_panel = ctk.CTkFrame(main_container, width=340, corner_radius=12)
        right_panel.pack(side="right", fill="both", expand=True, padx=(8, 0))
        right_panel.pack_propagate(False)

        # === ЛЕВАЯ ПАНЕЛЬ ===
        # Заголовок
        header_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 8))

        title_label = ctk.CTkLabel(
            header_frame,
            text="YourTube",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#1E88E5", "#64B5F6")
        )
        title_label.pack(side="left")

        # Фрейм для ввода URL
        url_frame = ctk.CTkFrame(left_panel, fg_color=("gray90", "gray20"), corner_radius=10)
        url_frame.pack(fill="x", padx=15, pady=8)

        url_icon = ctk.CTkLabel(url_frame, text="🔗", font=ctk.CTkFont(size=18))
        url_icon.pack(side="left", padx=(8, 5))

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="Вставьте ссылку на видео",
            height=38,
            font=ctk.CTkFont(size=13),
            border_width=0,
            fg_color="transparent"
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # Кнопки в одной строке
        button_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_row.pack(fill="x", padx=15, pady=5)

        self.paste_button = ctk.CTkButton(
            button_row,
            text="📋 Вставить",
            command=self.paste_url,
            height=36,
            width=90,
            font=ctk.CTkFont(size=12)
        )
        self.paste_button.pack(side="left", padx=(0, 5))

        self.info_button = ctk.CTkButton(
            button_row,
            text="🔍 Получить информацию",
            command=self.get_video_info_thread,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        self.info_button.pack(side="left", fill="x", expand=True, padx=5)

        # Подсказка
        hint_label = ctk.CTkLabel(
            left_panel,
            text="💡 Ctrl+V для вставки, Enter для поиска",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        hint_label.pack(anchor="w", padx=18, pady=(0, 8))

        # Фрейм для пути сохранения
        path_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        path_frame.pack(fill="x", padx=15, pady=5)

        path_label = ctk.CTkLabel(path_frame, text="💾", font=ctk.CTkFont(size=14))
        path_label.pack(side="left", padx=(0, 5))

        self.path_entry = ctk.CTkEntry(
            path_frame,
            height=36,
            font=ctk.CTkFont(size=12)
        )
        self.path_entry.insert(0, str(self.download_path))
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.browse_button = ctk.CTkButton(
            path_frame,
            text="📁 Обзор",
            command=self.browse_folder,
            width=80,
            height=36,
            font=ctk.CTkFont(size=11)
        )
        self.browse_button.pack(side="right")

        # Фрейм с информацией о видео
        self.info_frame = ctk.CTkFrame(left_panel, corner_radius=10)
        self.info_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Заголовок информации
        info_header = ctk.CTkFrame(self.info_frame, fg_color="transparent", height=28)
        info_header.pack(fill="x", padx=12, pady=(10, 5))

        ctk.CTkLabel(
            info_header,
            text="📊 Информация о видео",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        self.platform_badge = ctk.CTkLabel(
            info_header,
            text="",
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            padx=10,
            height=24
        )
        self.platform_badge.pack(side="right")

        # Контент информации
        info_content = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        info_content.pack(fill="both", expand=True, padx=12, pady=5)

        # Название
        self.title_label = ctk.CTkLabel(
            info_content,
            text="🎬 Название: -",
            font=ctk.CTkFont(size=13),
            wraplength=380,
            justify="left",
            anchor="w"
        )
        self.title_label.pack(anchor="w", pady=5)

        # Детали
        details_frame = ctk.CTkFrame(info_content, fg_color="transparent")
        details_frame.pack(fill="x", pady=5)

        self.duration_label = ctk.CTkLabel(
            details_frame,
            text="⏱ Длительность: -",
            font=ctk.CTkFont(size=12)
        )
        self.duration_label.pack(side="left", padx=(0, 15))

        self.author_label = ctk.CTkLabel(
            details_frame,
            text="👤 Автор: -",
            font=ctk.CTkFont(size=12)
        )
        self.author_label.pack(side="left", padx=(0, 15))

        self.views_label = ctk.CTkLabel(
            details_frame,
            text="👁 Просмотры: -",
            font=ctk.CTkFont(size=12)
        )
        self.views_label.pack(side="left")

        # Фрейм для выбора качества
        quality_frame = ctk.CTkFrame(left_panel, fg_color=("gray90", "gray20"), corner_radius=10)
        quality_frame.pack(fill="x", padx=15, pady=8)

        quality_icon = ctk.CTkLabel(quality_frame, text="⚙️", font=ctk.CTkFont(size=16))
        quality_icon.pack(side="left", padx=(10, 5))

        quality_label = ctk.CTkLabel(quality_frame, text="Качество:", font=ctk.CTkFont(size=13, weight="bold"))
        quality_label.pack(side="left", padx=(0, 5))

        self.quality_var = ctk.StringVar()
        self.quality_combo = ctk.CTkComboBox(
            quality_frame,
            values=["Получите информацию"],
            variable=self.quality_var,
            width=220,
            height=34,
            state="readonly",
            font=ctk.CTkFont(size=12),
            dropdown_font=ctk.CTkFont(size=12)
        )
        self.quality_combo.pack(side="left", padx=5, pady=6)

        # Прогресс бар
        self.progress_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=15, pady=8)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=14, corner_radius=5)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="💤 Готов к загрузке",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.progress_label.pack()

        # Кнопки управления
        button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(5, 15))

        self.download_button = ctk.CTkButton(
            button_frame,
            text="⬇️ Скачать видео",
            command=self.start_download,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#43A047",
            hover_color="#2E7D32",
            state="disabled"
        )
        self.download_button.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Отмена",
            command=self.cancel_download,
            height=40,
            width=100,
            font=ctk.CTkFont(size=13),
            fg_color="#E53935",
            hover_color="#B71C1C",
            state="disabled"
        )
        self.cancel_button.pack(side="right")

        # Статус бар
        status_frame = ctk.CTkFrame(left_panel, fg_color="transparent", height=22)
        status_frame.pack(fill="x", side="bottom", pady=(0, 8))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✅ Готов к работе",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=15)

        version_label = ctk.CTkLabel(
            status_frame,
            text="v1.0",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack(side="right", padx=15)

        # === ПРАВАЯ ПАНЕЛЬ (ЛОГИ) ===
        log_header = ctk.CTkFrame(right_panel, fg_color="transparent", height=32)
        log_header.pack(fill="x", padx=12, pady=(12, 5))

        ctk.CTkLabel(
            log_header,
            text="📋 Журнал событий",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        # Кнопки управления логами
        log_buttons = ctk.CTkFrame(log_header, fg_color="transparent")
        log_buttons.pack(side="right")

        self.copy_logs_button = ctk.CTkButton(
            log_buttons,
            text="📋",
            command=self.copy_logs,
            width=90,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        self.copy_logs_button.pack(side="left", padx=2)

        self.clear_logs_button = ctk.CTkButton(
            log_buttons,
            text="🧹",
            command=self.clear_logs,
            width=80,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        self.clear_logs_button.pack(side="left", padx=2)

        # Текстовое поле для логов
        log_frame = ctk.CTkFrame(right_panel)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=11, family="Consolas"),  # Увеличен шрифт
            wrap="word",
            activate_scrollbars=True
        )
        self.log_text.pack(fill="both", expand=True)

        # Настройка цветов для логов
        self.log_text.tag_config("error", foreground="#FF5555")
        self.log_text.tag_config("success", foreground="#55FF55")
        self.log_text.tag_config("info", foreground="#5555FF")
        self.log_text.tag_config("warning", foreground="#FFFF55")

        # Приветственное сообщение в логах
        self.log("👋 Добро пожаловать в YourTube!")
        self.log("")
        self.log("💡 Горячие клавиши:")
        self.log("   • Ctrl+V - вставить URL")
        self.log("   • Ctrl+C - скопировать логи")
        self.log("   • Ctrl+L - очистить логи")
        self.log("   • Enter  - получить информацию")
        self.log("")
        self.log("📁 Логи сохраняются в папке 'logs'")
        self.log("=" * 50)

    def log_message(self, message, tag=None):
        """Запись сообщения с тегом"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.insert("end", f"[{timestamp}] {message}\n", tag)
        self.log_text.see("end")

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass

    def browse_folder(self):
        """Выбор папки для сохранения"""
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = Path(folder)
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, str(folder))
            self.downloader.download_path = folder
            self.log(f"📁 Папка сохранения изменена: {folder}")

    def get_video_info_thread(self):
        """Запуск получения информации в отдельном потоке"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("YourTube", "⚠️ Введите URL видео")
            return

        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)

        self.current_url = url
        self.current_platform = self.downloader.detect_platform(url)

        self.log(f"🔍 Получение информации: {url}")
        self.log(f"📱 Платформа: {self.current_platform}")

        self.info_button.configure(state="disabled", text="⏳ Загрузка...")
        self.status_label.configure(text="🔄 Получение информации...")

        thread = threading.Thread(target=self.get_video_info)
        thread.daemon = True
        thread.start()

    def get_video_info(self):
        """Получение информации о видео"""
        try:
            self.video_info = self.downloader.get_video_info(self.current_url)
            self.window.after(0, self.update_video_info)
            self.log(f"✅ Информация получена: {self.video_info['title'][:50]}...")
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ Ошибка: {error_msg}", "error")
            self.window.after(0, lambda: self.show_error(error_msg))
        finally:
            self.window.after(0, lambda: self.info_button.configure(
                state="normal", text="🔍 Получить информацию"
            ))

    def show_error(self, error_msg):
        """Показ ошибки с расширенными рекомендациями"""
        self.log(f"❌ Ошибка: {error_msg}", "error")
        messagebox.showerror("YourTube", f"❌ {error_msg}")

    def update_video_info(self):
        """Обновление информации о видео"""
        if self.video_info:
            platform = self.video_info.get('platform', 'Неизвестно')
            self.current_platform = platform

            colors = {
                'YouTube': ('#FF0000', '#FF4444'),
                'RuTube': ('#00AAE4', '#33CCFF'),
                'Другое': ('gray', 'darkgray')
            }
            color = colors.get(platform, ('gray', 'darkgray'))

            self.platform_badge.configure(
                text=f"  {platform}  ",
                fg_color=color
            )

            title = self.video_info['title']
            if len(title) > 60:
                title = title[:57] + "..."
            self.title_label.configure(text=f"🎬 {title}")

            self.duration_label.configure(text=f"⏱ Длительность: {self.video_info.get('duration_str', '-')}")
            self.author_label.configure(text=f"👤 Автор: {self.video_info.get('uploader', '-')[:20]}")
            self.views_label.configure(text=f"👁 Просмотры: {self.video_info.get('views_str', '0')}")

            if 'formats' in self.video_info:
                quality_names = [f['name'] for f in self.video_info['formats']]
                self.quality_combo.configure(values=quality_names)
                if quality_names:
                    self.quality_var.set(quality_names[0])
                self.log(f"📊 Доступно форматов: {len(quality_names)}")

            self.download_button.configure(state="normal")
            self.status_label.configure(text="✅ Информация получена")

    def start_download(self):
        """Начало загрузки"""
        if not self.current_url or not self.video_info:
            return

        selected_name = self.quality_var.get()
        selected_format = None

        for f in self.video_info['formats']:
            if f['name'] == selected_name:
                selected_format = f
                break

        if not selected_format:
            selected_format = self.video_info['formats'][0]

        format_id = selected_format['id']

        self.log(f"⬇️ Начало загрузки: {selected_name}")
        self.log(f"📁 Путь: {self.download_path}")

        # Путь для сохранения
        output_template = str(self.download_path / '%(title)s.%(ext)s')

        # Блокировка
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.info_button.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        self.quality_combo.configure(state="disabled")
        self.paste_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")

        # Запуск загрузки
        self.downloader.download_video(
            self.current_url,
            format_id,
            output_template,
            self.current_platform
        )

        self.status_label.configure(text="🔄 Загрузка...")

    def update_progress(self, percent, speed, eta):
        """Обновление прогресса"""

        def update():
            self.progress_bar.set(percent / 100)

            if percent < 100:
                filled = int(percent / 10)
                progress_visual = "█" * filled + "▒" * (10 - filled)

                self.progress_label.configure(
                    text=f"{progress_visual}  {percent:.1f}%  |  ⚡ {speed}"
                )

                if int(percent) % 10 == 0:  # Логируем каждые 10%
                    self.log(f"📊 Прогресс: {percent:.1f}% | Скорость: {speed}")
            else:
                self.progress_label.configure(text="✅ Загрузка завершена!")
                self.log("✅ Загрузка успешно завершена!", "success")

                # Восстановление
                self.download_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
                self.info_button.configure(state="normal")
                self.url_entry.configure(state="normal")
                self.quality_combo.configure(state="readonly")
                self.paste_button.configure(state="normal")
                self.browse_button.configure(state="normal")
                self.status_label.configure(text="✅ Готово")

        self.window.after(0, update)

    def cancel_download(self):
        """Отмена загрузки"""
        self.downloader.cancel_download()
        self.progress_label.configure(text="❌ Загрузка отменена")
        self.status_label.configure(text="❌ Отменено")
        self.progress_bar.set(0)
        self.log("❌ Загрузка отменена пользователем", "warning")

        # Восстановление
        self.download_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.info_button.configure(state="normal")
        self.url_entry.configure(state="normal")
        self.quality_combo.configure(state="readonly")
        self.paste_button.configure(state="normal")
        self.browse_button.configure(state="normal")

    def run(self):
        """Запуск приложения"""
        self.window.mainloop()