import os
import yt_dlp
import threading
import time
import random
import subprocess
import sys
from pathlib import Path
from tkinter import messagebox


class YourTubeDownloader:
    def __init__(self, download_path="downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        self.current_download = None
        self.is_downloading = False
        self.progress_callback = None

        # Расширенный список User-Agent
        self.user_agents = [
            # Chrome на Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            # Firefox на Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            # Chrome на macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            # Safari на macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            # Chrome на Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Мобильные User-Agent
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
        ]

        # Список стран для гео-обхода
        self.countries = ['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'KR', 'BR', 'IN']

    def set_progress_callback(self, callback):
        """Установка функции обратного вызова для прогресса"""
        self.progress_callback = callback

    def get_random_user_agent(self):
        """Получение случайного User-Agent"""
        return random.choice(self.user_agents)

    def get_random_country(self):
        """Получение случайной страны для гео-обхода"""
        return random.choice(self.countries)

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
        """Хук для отслеживания прогресса загрузки"""
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

    def check_yt_dlp_version(self):
        """Проверка версии yt-dlp и обновление при необходимости"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'yt-dlp'],
                                    capture_output=True, text=True)
            if 'Version:' in result.stdout:
                version = result.stdout.split('Version:')[1].split('\n')[0].strip()
                print(f"yt-dlp версия: {version}")

                # Проверяем, не устарела ли версия
                major_version = int(version.split('.')[0]) if version.split('.')[0].isdigit() else 0
                if major_version < 2024:
                    print("yt-dlp устарел, рекомендуется обновить")
                    return False
            return True
        except:
            return False

    def update_yt_dlp(self):
        """Обновление yt-dlp до последней версии"""
        try:
            print("Обновление yt-dlp...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
                           check=True, capture_output=True)
            print("yt-dlp успешно обновлен")
            return True
        except Exception as e:
            print(f"Ошибка обновления yt-dlp: {e}")
            return False

    def get_youtube_options(self, attempt=0):
        """Получение опций для YouTube с расширенным обходом защиты"""
        country = self.get_random_country()
        user_agent = self.get_random_user_agent()

        # Базовые опции
        options = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': user_agent,
            'geo_bypass': True,
            'geo_bypass_country': country,
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Charset': 'utf-8,ISO-8859-1;q=0.7,*;q=0.3',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
            # Различные клиенты для обхода
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],  # Пропускаем проблемные форматы
                    'player_client': ['android', 'web', 'ios'],  # Несколько клиентов
                }
            },
            # Задержки для имитации человека
            'sleep_interval': random.randint(2, 5),
            'max_sleep_interval': random.randint(5, 10),
            'sleep_interval_requests': random.randint(1, 3),
        }

        # Для повторных попыток более агрессивные настройки
        if attempt >= 2:
            options['extractor_args']['youtube']['player_client'] = ['android', 'ios']
            options['extractor_args']['youtube']['skip'] = ['webpage', 'dash', 'hls']

        if attempt >= 3:
            # Мобильные клиенты
            options['extractor_args']['youtube']['player_client'] = ['android']
            options['user_agent'] = random.choice([ua for ua in self.user_agents if 'Mobile' in ua])

        return options

    def get_rutube_options(self):
        """Получение опций для RuTube"""
        return {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': self.get_random_user_agent(),
        }

    def extract_video_id(self, url):
        """Извлечение ID видео из URL YouTube"""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([\w-]+)',
            r'(?:youtu\.be\/)([\w-]+)',
            r'(?:youtube\.com\/embed\/)([\w-]+)',
            r'(?:youtube\.com\/v\/)([\w-]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_video_info(self, url):
        """Получение информации о видео с расширенными попытками"""
        try:
            platform = self.detect_platform(url)

            # Проверяем версию yt-dlp
            self.check_yt_dlp_version()

            if platform == 'YouTube':
                return self.get_youtube_info_with_retries(url)
            elif platform == 'RuTube':
                return self.get_rutube_info(url)
            else:
                return self.get_other_info(url)

        except Exception as e:
            error_msg = str(e)
            if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
                raise Exception("YouTube заблокировал запрос.\n\n"
                                "Рекомендации:\n"
                                "1. Включите VPN и попробуйте снова\n"
                                "2. Подождите 10-15 минут\n"
                                "3. Попробуйте скачать видео через прокси\n"
                                "4. Обновите yt-dlp: pip install --upgrade yt-dlp")
            raise Exception(f"Ошибка получения информации: {error_msg}")

    def get_youtube_info_with_retries(self, url):
        """Получение информации с YouTube с множественными попытками"""
        max_retries = 5
        last_error = None

        for attempt in range(max_retries):
            try:
                print(f"Попытка {attempt + 1} из {max_retries}")

                # Случайная задержка перед запросом
                if attempt > 0:
                    wait_time = random.randint(10, 20)  # Увеличиваем задержку
                    print(f"Ожидание {wait_time} секунд...")
                    time.sleep(wait_time)

                ydl_opts = self.get_youtube_options(attempt)

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
                            'platform': 'YouTube',
                            'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                            'formats': self.get_youtube_formats_with_retries(url)
                        }

            except Exception as e:
                last_error = e
                error_str = str(e)
                print(f"Попытка {attempt + 1} не удалась: {error_str[:100]}")

                if 'Video unavailable' in error_str:
                    raise Exception("Видео недоступно или удалено")

                if attempt == max_retries - 1:
                    break

                continue

        # Если все попытки не удались
        if last_error:
            error_msg = str(last_error)
            if 'Sign in to confirm' in error_msg:
                raise Exception("YouTube заблокировал все запросы.\n"
                                "Попробуйте позже или используйте другой URL")
            raise last_error

    def get_youtube_formats_with_retries(self, url):
        """Получение форматов с YouTube с повторными попытками"""
        try:
            ydl_opts = self.get_youtube_options(0)

            formats_list = [
                {
                    'id': 'bestvideo+bestaudio/best',
                    'name': '🎥 Наилучшее качество',
                    'ext': 'mp4',
                    'quality': 'Лучшее',
                    'note': 'Видео + аудио',
                    'resolution': 'Максимальная'
                },
                {
                    'id': 'bestaudio',
                    'name': '🎵 Только аудио (MP3)',
                    'ext': 'mp3',
                    'quality': '320kbps',
                    'note': 'MP3',
                    'resolution': 'Аудио'
                }
            ]

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

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
                                    'note': f"{height}p",
                                    'resolution': f"{height}p"
                                })
            except:
                for res in [2160, 1440, 1080, 720, 480, 360]:
                    formats_list.append({
                        'id': f'best[height<={res}]',
                        'name': f'📹 {res}p',
                        'ext': 'mp4',
                        'quality': f"{res}p",
                        'note': f"{res}p",
                        'resolution': f"{res}p"
                    })

            unique_formats = []
            seen = set()
            for f in formats_list:
                if f['resolution'] not in seen:
                    seen.add(f['resolution'])
                    unique_formats.append(f)

            def sort_key(x):
                if x['resolution'] == 'Максимальная':
                    return -1000
                elif x['resolution'] == 'Аудио':
                    return 1000
                elif x['resolution'].replace('p', '').isdigit():
                    return -int(x['resolution'].replace('p', ''))
                return 0

            unique_formats.sort(key=sort_key)
            return unique_formats

        except Exception as e:
            print(f"Ошибка получения форматов: {e}")
            return [
                {'id': 'bestvideo+bestaudio/best', 'name': '🎥 Наилучшее качество', 'ext': 'mp4', 'quality': 'Лучшее',
                 'resolution': 'Максимальная'},
                {'id': 'best[height<=1080]', 'name': '📹 1080p', 'ext': 'mp4', 'quality': '1080p',
                 'resolution': '1080p'},
                {'id': 'best[height<=720]', 'name': '📹 720p', 'ext': 'mp4', 'quality': '720p', 'resolution': '720p'},
                {'id': 'best[height<=480]', 'name': '📹 480p', 'ext': 'mp4', 'quality': '480p', 'resolution': '480p'},
                {'id': 'bestaudio', 'name': '🎵 Только аудио (MP3)', 'ext': 'mp3', 'quality': '320kbps',
                 'resolution': 'Аудио'}
            ]

    def get_rutube_info(self, url):
        """Получение информации с RuTube"""
        ydl_opts = self.get_rutube_options()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            duration = info.get('duration', 0)
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes}:{seconds:02d}"

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
                'platform': 'RuTube',
                'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                'formats': self.get_rutube_formats(url)
            }

    def get_rutube_formats(self, url):
        """Получение форматов для RuTube"""
        formats_list = [
            {
                'id': 'bestvideo+bestaudio/best',
                'name': '🎥 Наилучшее качество',
                'ext': 'mp4',
                'quality': 'Лучшее',
                'resolution': 'Максимальная'
            },
            {
                'id': 'bestaudio/best',
                'name': '🎵 Только аудио (MP3)',
                'ext': 'mp3',
                'quality': '320kbps',
                'resolution': 'Аудио'
            }
        ]

        try:
            ydl_opts = self.get_rutube_options()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

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
        except:
            for res in [1080, 720, 480, 360]:
                formats_list.append({
                    'id': f'best[height<={res}]',
                    'name': f'📹 {res}p',
                    'ext': 'mp4',
                    'quality': f"{res}p",
                    'resolution': f"{res}p"
                })

        return formats_list

    def get_other_info(self, url):
        """Получение информации с других платформ"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            duration = info.get('duration', 0)
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes}:{seconds:02d}"

            return {
                'title': info.get('title', 'Без названия'),
                'duration': duration,
                'duration_str': duration_str,
                'uploader': info.get('uploader', 'Неизвестно'),
                'views': info.get('view_count', 0),
                'views_str': str(info.get('view_count', 0)),
                'platform': 'Другое',
                'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                'formats': self.get_other_formats(url)
            }

    def get_other_formats(self, url):
        """Получение форматов для других платформ"""
        return [
            {'id': 'best', 'name': '🎥 Лучшее качество', 'ext': 'mp4', 'quality': 'Лучшее',
             'resolution': 'Максимальная'},
            {'id': 'bestaudio', 'name': '🎵 Только аудио', 'ext': 'mp3', 'quality': 'Аудио', 'resolution': 'Аудио'}
        ]

    def download_video(self, url, format_id='best', output_template=None, platform=None):
        """Загрузка видео с расширенными попытками"""
        if self.is_downloading:
            return False

        self.is_downloading = True

        if output_template is None:
            output_template = str(self.download_path / '%(title)s.%(ext)s')

        if platform is None:
            platform = self.detect_platform(url)

        def download_thread():
            try:
                max_retries = 3 if platform == 'YouTube' else 1

                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            print(f"Попытка загрузки {attempt + 1}")
                            time.sleep(random.randint(10, 15))

                        if platform == 'YouTube':
                            ydl_opts = self.get_youtube_options(attempt)
                        elif platform == 'RuTube':
                            ydl_opts = self.get_rutube_options()
                        else:
                            ydl_opts = {'quiet': True, 'no_warnings': True}

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
                        return

                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        print(f"Ошибка загрузки, пробуем снова: {e}")
                        continue

            except Exception as e:
                if self.progress_callback:
                    self.progress_callback(0, "Ошибка", str(e))

                error_msg = str(e)
                if 'Sign in to confirm' in error_msg:
                    error_msg = ("YouTube заблокировал загрузку.\n\n"
                                 "Что делать:\n"
                                 "1. Включите VPN и повторите попытку\n"
                                 "2. Подождите 15-20 минут\n"
                                 "3. Попробуйте скачать позже\n"
                                 "4. Используйте другой видео-хостинг")

                messagebox.showerror("YourTube", f"❌ Ошибка загрузки:\n{error_msg}")
            finally:
                self.is_downloading = False

        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

        return True

    def cancel_download(self):
        """Отмена загрузки"""
        self.is_downloading = False