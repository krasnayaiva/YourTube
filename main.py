#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YourTube - приложение для скачивания видео с YouTube, RuTube и других платформ
Version: 1.0
"""

import sys
import os
from ui import YourTubeApp


def main():
    """Главная функция"""
    try:
        # Создание папки для загрузок, если её нет
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
            print("📁 Создана папка для загрузок: downloads")

        # Создание папки для логов (опционально)
        if not os.path.exists("logs"):
            os.makedirs("logs")

        print("🎬 YourTube v1.0")
        print("=" * 50)
        print("✅ Запуск приложения...")

        # Запуск приложения
        app = YourTubeApp()
        app.run()

    except KeyboardInterrupt:
        print("\n👋 Программа остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()