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
import os
from logo import logo
import base64
import tempfile

theme_changer = "dark"

class TextRedirector(io.StringIO):
    """Перенаправление stdout/stderr в виджет логов"""

    def __init__(self, text_widget, save_to_file=False, log_file=None):
        super().__init__()
        self.text_widget = text_widget
        self.save_to_file = save_to_file
        self.log_file = log_file

    def write(self, string):
        if string.strip():
            self.text_widget.insert("end", string)
            self.text_widget.see("end")

            if self.save_to_file and self.log_file:
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(string)
                except:
                    pass

    def flush(self):
        pass

    def update_save_setting(self, save_to_file, log_file):
        """Обновление настроек сохранения"""
        self.save_to_file = save_to_file
        self.log_file = log_file


class YourTubeApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YourTube v1.1 - Скачивай видео легко")

        # Размер окна
        self.window.geometry("780x650")
        self.window.minsize(780, 650)
        self.window.maxsize(780, 650)
        self.window.resizable(False, False)

        self.set_icon()

        # Настройка темы
        ctk.set_appearance_mode(theme_changer)
        ctk.set_default_color_theme("blue")

        # Инициализация загрузчика
        self.downloader = YourTubeDownloader()
        self.downloader.set_progress_callback(self.update_progress)

        # Переменные
        self.current_url = ""
        self.video_info = None
        self.current_platform = None
        self.download_path = Path("downloads").absolute()
        self.save_logs = False  # По умолчанию не сохраняем логи
        self.log_file = None
        self.current_session_log = []

        # Создание папок
        Path("downloads").mkdir(exist_ok=True)

        # Создание интерфейса
        self.setup_ui()

        # Привязка горячих клавиш
        self.setup_hotkeys()

        # Настройка перенаправления вывода
        self.redirect_output()

        # Приветственное сообщение
        self.log("=" * 60)
        self.log(f"🚀 YourTube v1.1 запущен {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 60)
        self.log("")
        self.log("📱 Поддерживаемые платформы:")
        self.log("   • YouTube")
        self.log("   • RuTube")
        self.log("   • VK Видео")
        self.log("   • Другие (через yt-dlp)")
        self.log("")
        self.log("💡 Горячие клавиши:")
        self.log("   • Ctrl+V - вставить URL")
        self.log("   • Ctrl+C - скопировать логи")
        self.log("   • Ctrl+L - очистить логи")
        self.log("   • Enter  - получить информацию")
        self.log("")
        self.log("📁 Логи сохраняются только при включенном чекбоксе")
        self.log("=" * 60)

    def set_icon(self):
        """Устанавливает иконку приложения"""
        try:
            icon_data = logo.icon_data
            icon_bytes = base64.b64decode(icon_data)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.ico') as tmp_file:
                tmp_file.write(icon_bytes)
                self.temp_icon_path = tmp_file.name

            self.window.iconbitmap(default=self.temp_icon_path)
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

            print("✅ Иконка успешно загружена")

        except Exception as e:
            print(f"⚠️ Не удалось загрузить иконку: {e}")

    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.temp_icon_path and os.path.exists(self.temp_icon_path):
            try:
                os.remove(self.temp_icon_path)
            except:
                pass
        self.window.destroy()

    def redirect_output(self):
        """Перенаправление stdout и stderr"""
        self.redirector = TextRedirector(self.log_text, self.save_logs, self.log_file)
        sys.stdout = self.redirector
        sys.stderr = self.redirector

    def update_log_settings(self):
        """Обновление настроек сохранения логов"""
        self.save_logs = self.save_logs_var.get()

        if self.save_logs:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_file = log_dir / f"yourtube_{timestamp}.log"

            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get("1.0", "end-1c"))
                self.log(f"📁 Логи сохраняются в: {self.log_file}")
            except Exception as e:
                self.log(f"❌ Ошибка сохранения логов: {e}")
        else:
            if self.log_file:
                self.log(f"📁 Сохранение логов отключено")
                self.log_file = None

        self.redirector.update_save_setting(self.save_logs, self.log_file)

    def log(self, message):
        """Запись сообщения в лог"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        formatted_msg = f"[{timestamp}] {message}\n"

        self.log_text.insert("end", formatted_msg)
        self.log_text.see("end")

        if self.save_logs and self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(formatted_msg)
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
        """Копирование логов"""
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
        """Вставка URL"""
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
        # Основной контейнер
        main_container = ctk.CTkFrame(self.window)
        main_container.pack(fill="both", expand=True, padx=8, pady=8)

        # Левая панель (420px)
        left_panel = ctk.CTkFrame(main_container, width=420, corner_radius=12)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        left_panel.pack_propagate(False)

        # Правая панель (340px)
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

        version_label = ctk.CTkLabel(
            header_frame,
            text="v1.1",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version_label.pack(side="left", padx=(5, 0))

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

        # Кнопки
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

        # Путь сохранения
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

        # Информация о видео
        self.info_frame = ctk.CTkFrame(left_panel, corner_radius=10)
        self.info_frame.pack(fill="both", expand=True, padx=15, pady=10)

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

        info_content = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        info_content.pack(fill="both", expand=True, padx=12, pady=5)

        self.title_label = ctk.CTkLabel(
            info_content,
            text="🎬 Название: -",
            font=ctk.CTkFont(size=13),
            wraplength=380,
            justify="left",
            anchor="w"
        )
        self.title_label.pack(anchor="w", pady=5)

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

        # Качество
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
            font=ctk.CTkFont(size=12)
        )
        self.quality_combo.pack(side="left", padx=5, pady=6)

        # Прогресс
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

        # Кнопки
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

        # Статус
        status_frame = ctk.CTkFrame(left_panel, fg_color="transparent", height=22)
        status_frame.pack(fill="x", side="bottom", pady=(0, 8))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✅ Готов к работе",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=15)

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
            width=28,
            height=28,
            font=ctk.CTkFont(size=16)
        )
        self.copy_logs_button.pack(side="left", padx=2)

        self.clear_logs_button = ctk.CTkButton(
            log_buttons,
            text="🧹",
            command=self.clear_logs,
            width=28,
            height=28,
            font=ctk.CTkFont(size=16)
        )
        self.clear_logs_button.pack(side="left", padx=2)

        # Чекбокс сохранения логов
        log_options = ctk.CTkFrame(right_panel, fg_color="transparent")
        log_options.pack(fill="x", padx=12, pady=(0, 5))

        self.save_logs_var = ctk.BooleanVar(value=False)
        self.save_logs_checkbox = ctk.CTkCheckBox(
            log_options,
            text="💾 Сохранить журнал в файл",
            variable=self.save_logs_var,
            command=self.update_log_settings,
            font=ctk.CTkFont(size=11),
            width=17,
            height=17,
            checkbox_width=17,
            checkbox_height=17
        )
        self.save_logs_checkbox.pack(side="left")

        # Текстовое поле для логов
        log_frame = ctk.CTkFrame(right_panel)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=11, family="Consolas"),
            wrap="word",
            activate_scrollbars=True
        )
        self.log_text.pack(fill="both", expand=True)

        # Цвета для логов
        self.log_text.tag_config("error", foreground="#FF5555")
        self.log_text.tag_config("success", foreground="#55FF55")
        self.log_text.tag_config("info", foreground="#5555FF")
        self.log_text.tag_config("warning", foreground="#FFFF55")

    def browse_folder(self):
        """Выбор папки"""
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = Path(folder)
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, str(folder))
            self.downloader.download_path = folder
            self.log(f"📁 Папка сохранения: {folder}")

    def get_video_info_thread(self):
        """Получение информации"""
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
        """Получение информации"""
        try:
            self.video_info = self.downloader.get_video_info(self.current_url)
            self.window.after(0, self.update_video_info)
            self.log(f"✅ Информация получена: {self.video_info['title'][:50]}...")
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ Ошибка: {error_msg}")
            self.window.after(0, lambda: messagebox.showerror("YourTube", f"❌ {error_msg}"))
        finally:
            self.window.after(0, lambda: self.info_button.configure(
                state="normal", text="🔍 Получить информацию"
            ))

    def update_video_info(self):
        """Обновление информации"""
        if self.video_info:
            platform = self.video_info.get('platform', 'Неизвестно')
            self.current_platform = platform

            # Цвет для платформы
            colors = {
                'YouTube': ('#FF0000', '#FF4444'),
                'RuTube': ('#00AAE4', '#33CCFF'),
                'VK': ('#0077FF', '#4A90E2'),
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

        output_template = str(self.download_path / '%(title)s.%(ext)s')

        # Блокировка
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.info_button.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        self.quality_combo.configure(state="disabled")
        self.paste_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.save_logs_checkbox.configure(state="disabled")

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

                if int(percent) % 10 == 0:
                    self.log(f"📊 Прогресс: {percent:.1f}% | Скорость: {speed}")
            else:
                self.progress_label.configure(text="✅ Загрузка завершена!")
                self.log("✅ Загрузка успешно завершена!")

                # Восстановление
                self.download_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
                self.info_button.configure(state="normal")
                self.url_entry.configure(state="normal")
                self.quality_combo.configure(state="readonly")
                self.paste_button.configure(state="normal")
                self.browse_button.configure(state="normal")
                self.save_logs_checkbox.configure(state="normal")
                self.status_label.configure(text="✅ Готово")

        self.window.after(0, update)

    def cancel_download(self):
        """Отмена загрузки"""
        self.downloader.cancel_download()
        self.progress_label.configure(text="❌ Загрузка отменена")
        self.status_label.configure(text="❌ Отменено")
        self.progress_bar.set(0)
        self.log("❌ Загрузка отменена пользователем")

        # Восстановление
        self.download_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.info_button.configure(state="normal")
        self.url_entry.configure(state="normal")
        self.quality_combo.configure(state="readonly")
        self.paste_button.configure(state="normal")
        self.browse_button.configure(state="normal")
        self.save_logs_checkbox.configure(state="normal")

    def run(self):
        """Запуск"""
        self.window.mainloop()