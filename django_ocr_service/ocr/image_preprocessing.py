"""
Utilities to enable image preprocessing before OCR
"""
import logging
import tempfile

import cv2
from django.conf import settings
import numpy as np
from PIL import Image
from PIL import ImageFile

logger = logging.getLogger(__name__)

# Below line is to ensure PIL does not throw error if it feels image is truncated
ImageFile.LOAD_TRUNCATED_IMAGES = True


def get_size_of_scaled_image(im):
    """
    Return resize scale

    :param im:
    :return:
    """
    length_x, width_y = im.size
    factor = max(1, int(settings.IMAGE_SIZE / length_x))
    size = factor * length_x, factor * width_y
    return size


def set_image_dpi(file_path):
    """
    Sets image dpi

    :param file_path:
    :return:
    """
    im = Image.open(file_path)
    size = get_size_of_scaled_image(im)
    im_resized = im.resize(size, Image.ANTIALIAS)
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, dir=settings.LOCAL_FILES_SAVE_DIR, suffix=".png"
    )
    temp_filename = temp_file.name
    im_resized.save(temp_filename, dpi=(300, 300))
    return temp_filename


def image_smoothening(img):
    """
    Smoothens image

    :param img:
    :return:
    """
    ret1, th1 = cv2.threshold(img, settings.BINARY_THRESHOLD, 255, cv2.THRESH_BINARY)
    ret2, th2 = cv2.threshold(th1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    blur = cv2.GaussianBlur(th2, (1, 1), 0)
    ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th3


def remove_noise_and_smooth(file_name):
    """
    Removes additional noise in image

    :param file_name:
    :return:
    """
    logging.info("Removing noise and smoothening image")
    img = cv2.imread(file_name, 0)
    filtered = cv2.adaptiveThreshold(
        img.astype(np.uint8), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 41, 3
    )
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    img = image_smoothening(img)
    or_image = cv2.bitwise_or(img, closing)
    return or_image


def preprocess_image_for_ocr(file_path):
    logging.info("Processing image for OCR")
    temp_filename = set_image_dpi(file_path)
    im_new = remove_noise_and_smooth(temp_filename)
    return im_new
