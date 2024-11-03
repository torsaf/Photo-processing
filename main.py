import os
import cv2
import numpy as np
from PIL import Image

def convert_image_to_jpg(image_path):
    """Конвертирует изображение в формат JPG, если оно не в этом формате."""
    _, ext = os.path.splitext(image_path)
    ext = ext.lower()

    if ext in ['.png', '.webp', '.jfif']:
        with Image.open(image_path) as img:
            rgb_image = img.convert('RGB')
            new_image_path = image_path.replace(ext, '.jpg')
            rgb_image.save(new_image_path, 'JPEG')

            # Получаем имя папки и файла для вывода
            folder_name = os.path.basename(os.path.dirname(image_path))
            file_name = os.path.basename(image_path)
            new_file_name = os.path.basename(new_image_path)

            print(f"Конвертировано: {folder_name}/{file_name} -> {folder_name}/{new_file_name}")

        # Удаляем исходный файл после успешной конвертации
        os.remove(image_path)
        print(f"Удалён исходный файл: {folder_name}/{file_name}")
        return True  # Успешно конвертировано

    elif ext in ['.jpg', '.jpeg']:
        return False  # Уже в формате JPG, ничего не делаем

    else:
        # Сообщение об ошибке с упрощенным выводом
        folder_name = os.path.basename(os.path.dirname(image_path))
        file_name = os.path.basename(image_path)
        print(f"Ошибка: Неподдерживаемый формат '{ext}' для изображения '{folder_name}/{file_name}'.")
        os.remove(image_path)  # Удаляем файл с неподдерживаемым форматом
        print(f"Удалён неподдерживаемый файл: {folder_name}/{file_name}")
        return False  # Ошибка формата

def resize_and_crop(image_path):
    """Изменяет размер и обрезает изображение до соотношения 4:3."""
    image = cv2.imread(image_path)
    if image is None:
        print(f"Ошибка: Не удалось загрузить изображение '{image_path}'.")
        return False  # Не удалось обработать

    img_height, img_width = image.shape[:2]

    if img_width / img_height == 4 / 3:
        return False  # Не нужно сохранять и не удаляем

    # Конвертация в градации серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Пороговое выделение объекта на белом фоне
    _, threshold = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # Нахождение контуров и выбор основного контура
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        cropped_image = image[y:y + h, x:x + w]

        img_height, img_width = cropped_image.shape[:2]
        add_top_bottom = int(img_height * 0.1)  # 10% сверху и снизу
        add_left_right = int(img_width * 0.1)  # 10% справа и слева

        new_height = img_height + 2 * add_top_bottom
        new_width = img_width + 2 * add_left_right

        target_ratio = 4 / 3
        current_ratio = img_width / img_height

        if current_ratio < target_ratio:
            new_width = int(new_height * target_ratio)
        else:
            new_height = int(new_width / target_ratio)

        background = np.ones((new_height, new_width, 3), dtype=np.uint8) * 255
        offset_y = (background.shape[0] - cropped_image.shape[0]) // 2
        offset_x = (background.shape[1] - cropped_image.shape[1]) // 2
        background[offset_y:offset_y + cropped_image.shape[0],
        offset_x:offset_x + cropped_image.shape[1]] = cropped_image

        final_height, final_width = background.shape[:2]

        if final_width > 2000 or final_height > 1500:
            background = cv2.resize(background, (2000, 1500), interpolation=cv2.INTER_AREA)
            print(f"Уменьшено до 2000x1500")
        elif final_width < 800 or final_height < 600:
            background = cv2.resize(background, (800, 600), interpolation=cv2.INTER_LINEAR)
            print(f"Увеличено до 800x600")

        # Получаем имя папки для корректного вывода
        folder_name = os.path.basename(os.path.dirname(image_path))
        file_name = os.path.basename(image_path)

        cv2.imwrite(image_path, background)
        print(f"Обработано и сохранено: {folder_name}/{file_name}")
        return True  # Успешно обработано
    else:
        print(f"Ошибка: Объекты не найдены на изображении '{image_path}'.")
        return False  # Не удалось обработать


def process_all_images_in_folders(root_folder):
    """Обрабатывает все изображения в указанной папке и её подкаталогах."""
    for subdir, _, files in os.walk(root_folder):
        for filename in files:
            input_path = os.path.join(subdir, filename)
            # Конвертируем изображение в JPG, если это необходимо
            if convert_image_to_jpg(input_path):  # Если конвертация произошла
                # Заменяем расширение на .jpg
                input_path = input_path.rsplit('.', 1)[0] + '.jpg'
            # Изменяем размер и обрезаем изображение
            resize_and_crop(input_path)


def check_images_in_folders(root_folder):
    """Проверяет все подпапки в указанной директории на наличие jpg файлов и уведомляет о пропущенных."""
    for subdir, _, files in os.walk(root_folder):
        # Игнорируем корневую папку
        if subdir == root_folder:
            continue

        jpg_files = [f for f in files if f.lower().endswith('.jpg')]
        jpg_files.sort()  # Сортируем файлы для корректной проверки

        if not jpg_files:
            print(f"В папке '{os.path.basename(subdir)}' нет файлов .jpg.")
            continue  # Переходим к следующей папке

        if len(jpg_files) > 10:
            print(f"В папке '{os.path.basename(subdir)}' больше 10 файлов .jpg: найдено {len(jpg_files)}.")
            continue  # Переходим к следующей папке

        # Собираем существующие номера
        existing_numbers = sorted(int(f.split('.')[0]) for f in jpg_files)

        # Находим максимальный номер для проверки пропусков
        max_number = existing_numbers[-1]
        missing_numbers = []

        for expected_number in range(1, max_number + 1):
            if expected_number not in existing_numbers:
                missing_numbers.append(expected_number)

        # Уведомляем о пропущенных номерах
        if missing_numbers:
            print(f"В папке '{os.path.basename(subdir)}' отсутствуют следующие файлы: {', '.join(map(str, missing_numbers))}.")

# Запрашиваем путь к папке с фото у пользователя
root_folder = input("Введите путь к папке с фото: ").strip()

# Запускаем обработку и проверку изображений по указанному пути
process_all_images_in_folders(root_folder)  # Обработка изображений
check_images_in_folders(root_folder)  # Проверка наличия изображений
input("Нажмите Enter, чтобы завершить программу...")
