"""
YourTube v1.1 - приложение для скачивания видео
Поддерживает: YouTube, RuTube, VK Видео и другие платформы
"""

import sys
import os
from ui import YourTubeApp


def main():
    """Главная функция"""
    try:
        print("🎬 YourTube v1.1")
        print("=" * 50)
        print("📱 Поддержка: YouTube, RuTube, VK Видео")
        print("=" * 50)

        # Создание папки для загрузок
        os.makedirs("downloads", exist_ok=True)

        print("✅ Запуск приложения...")

        app = YourTubeApp()
        app.run()

    except KeyboardInterrupt:
        print("\n👋 Программа остановлена")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()