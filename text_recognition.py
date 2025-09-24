import pytesseract
from PIL import Image
import os


def extract_text_from_image(image_path):
    """
    Извлекает текст с изображения используя pytesseract.

    Args:
        image_path (str): Путь к изображению

    Returns:
        str: Распознанный текст или сообщение об ошибке
    """
    try:
        if not os.path.exists(image_path):
            return f"Файл {image_path} не найден"

        image = Image.open(image_path)
        custom_config = r"--oem 3 --psm 6 -l rus"
        text = pytesseract.image_to_string(image, config=custom_config, lang="rus")

        return text.strip() if text.strip() else "Текст не распознан"

    except Exception as e:
        return f"Ошибка при обработке изображения: {e}"


def process_all_images_to_md():
    """
    Обрабатывает все изображения в папке pics и сохраняет результаты в lectures.md.
    """
    folder_path = "pics"
    output_file = "lectures.md"

    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не существует!")
        return

    # Получаем список изображений (сортировка для порядка обработки)
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"}
    images = sorted(
        [
            f
            for f in os.listdir(folder_path)
            if os.path.splitext(f)[1].lower() in image_extensions
        ]
    )

    if not images:
        print("В папке pics нет изображений!")
        return

    print(f"Найдено {len(images)} изображений для обработки")
    print(f"Результат будет сохранен в: {output_file}")
    print("=" * 60)

    with open(output_file, "w", encoding="utf-8") as md_file:
        for i, image_name in enumerate(images, 1):
            image_path = os.path.join(folder_path, image_name)
            print(f"[{i}/{len(images)}] Обрабатываем: {image_name}")

            # Извлекаем текст
            text = extract_text_from_image(image_path)

            # Записываем в markdown файл
            md_file.write(f"# {image_name}\n\n")  # Заголовок с именем файла
            md_file.write(f"{text}\n\n")  # Текст изображения
            md_file.write("---\n\n")  # Разделитель между изображениями

            print(f"    ✓ Текст сохранен ({len(text)} символов)")

    print("=" * 60)
    print(f"✅ Готово! Результаты сохранены в {output_file}")


def main():
    """
    Основная функция для обработки изображений.
    """
    # Проверяем наличие Tesseract
    try:
        pytesseract.get_tesseract_version()
    except:
        print("❌ Tesseract не установлен или не найден!")
        print("Установите Tesseract OCR и добавьте путь в переменные среды")
        return

    print("🚀 Запуск обработки изображений...")
    print()

    # запускаем обработку
    process_all_images_to_md()


if __name__ == "__main__":
    main()
