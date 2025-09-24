import os
import re
import requests
from urllib.parse import urlparse
import time

folder_path = "links"
download_folder = "pics"


def create_download_folder():
    """
    Создает папку для загрузки изображений, если она не существует.

    Returns:
        bool: True если папка существует или была создана, False в случае ошибки.
    """
    try:
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
            print(f"Создана папка для загрузок: {download_folder}")
        return True
    except Exception as e:
        print(f"Ошибка создания папки {download_folder}: {e}")
        return False


def download_image(url, filename, max_retries=3):
    """
    Скачивает изображение по URL и сохраняет его в папку pics.

    Args:
        url (str): URL-адрес изображения для скачивания
        filename (str): Имя файла для сохранения
        max_retries (int): Максимальное количество попыток при ошибках

    Returns:
        bool: True если скачивание успешно, False в случае ошибки

    Examples:
        >>> download_image("http://example.com/image.jpg", "photo.jpg")
        True  # если скачивание успешно
    """
    for attempt in range(max_retries):
        try:
            # Добавляем задержку между запросами чтобы не перегружать сервер
            if attempt > 0:
                time.sleep(1)

            print(f"Попытка {attempt + 1}: Скачиваем {filename}...")

            # Отправляем GET-запрос с таймаутом
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()  # Проверяем статус код

            # Определяем расширение файла из URL или Content-Type
            file_extension = get_file_extension(
                url, response.headers.get("content-type", "")
            )
            full_filename = add_extension(filename, file_extension)
            file_path = os.path.join(download_folder, full_filename)

            # Проверяем, не существует ли уже файл
            if os.path.exists(file_path):
                print(f"Файл {full_filename} уже существует, пропускаем")
                return True

            # Сохраняем изображение
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

            file_size = os.path.getsize(file_path) / 1024  # Размер в KB
            print(f"✓ Успешно скачан: {full_filename} ({file_size:.1f} KB)")
            return True

        except requests.exceptions.Timeout:
            print(f"× Таймаут при скачивании {filename} (попытка {attempt + 1})")
        except requests.exceptions.HTTPError as e:
            print(f"× HTTP ошибка при скачивании {filename}: {e}")
            if e.response.status_code == 404:
                return False  # Не пытаемся повторно для 404 ошибок
        except requests.exceptions.RequestException as e:
            print(f"× Ошибка сети при скачивании {filename}: {e}")
        except IOError as e:
            print(f"× Ошибка записи файла {filename}: {e}")
            return False
        except Exception as e:
            print(f"× Неожиданная ошибка при скачивании {filename}: {e}")

    print(f"× Не удалось скачать {filename} после {max_retries} попыток")
    return False


def get_file_extension(url, content_type):
    """
    Определяет расширение файла на основе URL и Content-Type.

    Args:
        url (str): URL изображения
        content_type (str): Заголовок Content-Type из ответа сервера

    Returns:
        str: Расширение файла (например: ".jpg", ".png")
    """
    # Пытаемся получить расширение из URL
    parsed_url = urlparse(url)
    url_path = parsed_url.path.lower()

    # Распространенные расширения изображений
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}

    for ext in image_extensions:
        if url_path.endswith(ext):
            return ext

    # Если не нашли в URL, проверяем Content-Type
    content_type = content_type.lower()
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    elif "png" in content_type:
        return ".png"
    elif "gif" in content_type:
        return ".gif"
    elif "webp" in content_type:
        return ".webp"
    elif "svg" in content_type:
        return ".svg"
    elif "bmp" in content_type:
        return ".bmp"

    # По умолчанию используем .jpg
    return ".jpg"


def add_extension(filename, extension):
    """
    Добавляет расширение к имени файла, если его нет.

    Args:
        filename (str): Имя файла
        extension (str): Расширение файла

    Returns:
        str: Имя файла с расширением
    """
    if not filename.lower().endswith(
        (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg")
    ):
        return filename + extension
    return filename


def parse_img_tag(html_line):
    """
    Парсит HTML-строку с тегом img и извлекает значения атрибутов name и src.
    """
    try:
        cleaned_line = html_line.strip()
        if not cleaned_line or "<img" not in cleaned_line.lower():
            return None, None

        name_pattern = r'name\s*=\s*"([^"]*)"'
        src_pattern = r'src\s*=\s*"([^"]*)"'

        name_match = re.search(name_pattern, cleaned_line, re.IGNORECASE)
        src_match = re.search(src_pattern, cleaned_line, re.IGNORECASE)

        return (
            (name_match.group(1), src_match.group(1))
            if name_match and src_match
            else (None, None)
        )

    except Exception as e:
        print(f"Ошибка при парсинге строки: {e}")
        return None, None


def read_and_parse_file(file_path):
    """
    Читает файл построчно и извлекает данные изображений из HTML-тегов <img>.
    """
    results = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, 1):
                name, src = parse_img_tag(line)
                if name and src:
                    results.append((name, src))
                    print(
                        f"Файл {os.path.basename(file_path)}, строка {line_number}: {name} -> {src}"
                    )

    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="cp1251") as file:
                for line_number, line in enumerate(file, 1):
                    name, src = parse_img_tag(line)
                    if name and src:
                        results.append((name, src))
                        print(
                            f"Файл {os.path.basename(file_path)}, строка {line_number}: {name} -> {src}"
                        )
        except Exception as e:
            print(f"Ошибка чтения файла {file_path}: {e}")
            return []
    except Exception as e:
        print(f"Ошибка обработки файла {file_path}: {e}")
        return []

    return results


def download_all_images(image_list):
    """
    Скачивает все изображения из списка.

    Args:
        image_list (list): Список кортежей (name, src)

    Returns:
        tuple: (success_count, total_count) - количество успешных загрузок и общее количество
    """
    if not image_list:
        print("Нет изображений для скачивания")
        return 0, 0

    success_count = 0
    total_count = len(image_list)

    print(f"\nНачинаем скачивание {total_count} изображений...")
    print("=" * 60)

    for i, (name, src) in enumerate(image_list, 1):
        print(f"[{i}/{total_count}] ", end="")
        if download_image(src, name):
            success_count += 1

    return success_count, total_count


def main():
    """
    Основная функция скрипта для обработки и скачивания изображений.
    """
    # Создаем папку для загрузок
    if not create_download_folder():
        return

    # Проверяем папку с исходными файлами
    if not os.path.exists(folder_path):
        print(f"Папка '{folder_path}' не существует!")
        return

    all_results = []

    # Парсим все файлы
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            print(f"\n--- Обрабатываем файл: {file} ---")
            file_results = read_and_parse_file(file_path)
            all_results.extend(file_results)

    # Скачиваем изображения
    if all_results:
        success_count, total_count = download_all_images(all_results)
        print("\n" + "=" * 60)
        print(f"=== РЕЗУЛЬТАТ ===")
        print(f"Успешно скачано: {success_count}/{total_count} изображений")
        print(f"Папка с изображениями: {download_folder}")
    else:
        print("Не найдено изображений для скачивания")


if __name__ == "__main__":
    main()
