import os
import yt_dlp
import threading
import time
import random
from pathlib import Path
from tkinter import messagebox


class YourTubeDownloader:
    def __init__(self, download_path="downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        self.current_download = None
        self.is_downloading = False
        self.progress_callback = None

        # User-Agent для разных платформ
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        ]

    def set_progress_callback(self, callback):
        self.progress_callback = callback

    def get_random_user_agent(self):
        return random.choice(self.user_agents)

    def detect_platform(self, url):
        """Определение платформы по URL"""
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'YouTube'
        elif 'rutube.ru' in url_lower:
            return 'RuTube'
        else:
            return 'Другое'

    def progress_hook(self, d):
        """Хук для отслеживания прогресса"""
        if d['status'] == 'downloading':
            if self.progress_callback:
                try:
                    percent = d.get('_percent_str', '0%').strip('%')
                    speed = d.get('_speed_str', 'N/A')
                    eta = d.get('_eta_str', 'N/A')

                    try:
                        percent_float = float(percent)
                    except (ValueError, TypeError):
                        percent_float = 0

                    self.progress_callback(percent_float, speed, eta)
                except Exception as e:
                    print(f"Error in progress hook: {e}")

        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback(100, "Завершено", "Конвертация...")

    def get_platform_options(self, platform, attempt=0):
        """Получение опций для конкретной платформы"""
        base_options = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': self.get_random_user_agent(),
        }

        if platform == 'YouTube':
            base_options.update({
                'extract_flat': False,
                'geo_bypass': True,
                'geo_bypass_country': random.choice(['US', 'GB', 'CA', 'DE']),
                'http_headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'] if attempt < 2 else ['android'],
                    }
                },
            })

        elif platform == 'RuTube':
            base_options.update({
                'extract_flat': False,
            })

        return base_options

    def get_video_info(self, url):
        """Получение информации о видео"""
        try:
            platform = self.detect_platform(url)

            max_retries = 3 if platform == 'YouTube' else 2

            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(random.randint(3, 6))

                    ydl_opts = self.get_platform_options(platform, attempt)

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)

                        if info:
                            # Форматирование длительности
                            duration = info.get('duration', 0)
                            minutes = duration // 60
                            seconds = duration % 60
                            duration_str = f"{minutes}:{seconds:02d}"

                            # Форматирование просмотров
                            views = info.get('view_count', 0)
                            if views > 1000000:
                                views_str = f"{views / 1000000:.1f}M"
                            elif views > 1000:
                                views_str = f"{views / 1000:.1f}K"
                            else:
                                views_str = str(views)

                            return {
                                'title': info.get('title', 'Без названия'),
                                'duration': duration,
                                'duration_str': duration_str,
                                'uploader': info.get('uploader', 'Неизвестно'),
                                'views': views,
                                'views_str': views_str,
                                'platform': platform,
                                'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                                'formats': self.get_available_formats(info, platform)
                            }

                except Exception as e:
                    print(f"Попытка {attempt + 1} не удалась: {str(e)[:100]}")
                    if attempt == max_retries - 1:
                        raise
                    continue

        except Exception as e:
            error_msg = str(e)
            if 'Failed to extract' in error_msg:
                raise Exception("YouTube изменил API. Обновите yt-dlp:\npip install --upgrade yt-dlp")
            raise Exception(f"Ошибка получения информации: {error_msg}")

    def get_available_formats(self, info, platform):
        """Получение доступных форматов"""
        formats_list = []

        # Аудио формат (всегда доступен)
        if platform == 'RuTube':
            audio_id = 'bestaudio/best'
        else:
            audio_id = 'bestaudio'

        formats_list.append({
            'id': audio_id,
            'name': '🎵 Только аудио (MP3)',
            'ext': 'mp3',
            'quality': '320kbps',
            'resolution': 'Аудио'
        })

        # Доступные видео форматы
        resolutions_seen = set()
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                height = f.get('height', 0)
                if height and height not in resolutions_seen:
                    resolutions_seen.add(height)
                    formats_list.append({
                        'id': f['format_id'],
                        'name': f'📹 {height}p',
                        'ext': f.get('ext', 'mp4'),
                        'quality': f"{height}p",
                        'resolution': f"{height}p"
                    })

        # Если нет форматов, добавляем стандартные
        if len(formats_list) <= 1:  # Только аудио формат
            for res in [2160, 1440, 1080, 720, 480, 360]:
                if res not in resolutions_seen:
                    formats_list.append({
                        'id': f'best[height<={res}]',
                        'name': f'📹 {res}p',
                        'ext': 'mp4',
                        'quality': f"{res}p",
                        'resolution': f"{res}p"
                    })

        # Сортировка (от большего к меньшему)
        def sort_key(x):
            if x['resolution'] == 'Аудио':
                return 1000
            elif x['resolution'].replace('p', '').isdigit():
                return -int(x['resolution'].replace('p', ''))
            return 0

        formats_list.sort(key=sort_key)
        return formats_list

    def download_video(self, url, format_id='best', output_template=None, platform=None):
        """Загрузка видео"""
        if self.is_downloading:
            return False

        self.is_downloading = True

        if output_template is None:
            output_template = str(self.download_path / '%(title)s.%(ext)s')

        if platform is None:
            platform = self.detect_platform(url)

        def download_thread():
            try:
                ydl_opts = self.get_platform_options(platform, 0)

                ydl_opts.update({
                    'format': format_id,
                    'outtmpl': output_template,
                    'progress_hooks': [self.progress_hook],
                })

                # Добавляем постпроцессор для аудио
                if 'audio' in format_id.lower() or format_id in ['bestaudio', 'bestaudio/best']:
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    }]

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                if self.progress_callback:
                    self.progress_callback(100, "Завершено", "Готово")

                messagebox.showinfo("YourTube", "✅ Видео успешно скачано!")

            except Exception as e:
                if self.progress_callback:
                    self.progress_callback(0, "Ошибка", str(e))

                error_msg = str(e)
                if 'Failed to extract' in error_msg:
                    error_msg = ("❌ Ошибка извлечения данных.\n\n"
                                 "Попробуйте обновить yt-dlp:\n"
                                 "pip install --upgrade yt-dlp")

                messagebox.showerror("YourTube", f"❌ Ошибка загрузки:\n{error_msg}")
            finally:
                self.is_downloading = False

        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

        return True

    def cancel_download(self):
        self.is_downloading = False