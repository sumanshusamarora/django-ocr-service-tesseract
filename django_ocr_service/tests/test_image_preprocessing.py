"""
Tests for image preprocessing
"""
import cv2
from django.conf import settings
import math
import numpy as np
from PIL import Image
import pytest

from ocr.image_preprocessing import (
    get_size_of_scaled_image,
    set_image_dpi,
    image_smoothening,
    remove_noise_and_smooth,
    preprocess_image_for_ocr,
)

from .help_testutils import TESTFILE_IMAGE_PATH

pytestmark = pytest.mark.django_db()

class TestImagePreprocessing:
    """ """

    def setup_method(self):
        """

        :return:
        """
        self.image = Image.open(TESTFILE_IMAGE_PATH)

    def test_get_size_of_scaled_image(self):
        """

        :return:
        """
        orig_size = self.image.size
        scale_size = get_size_of_scaled_image(self.image)
        assert scale_size[0] > orig_size[0] and scale_size == (
            settings.IMAGE_SIZE,
            orig_size[1] * (scale_size[0] / orig_size[0]),
        )

    def test_set_image_dpi(self):
        """

        :return:
        """
        filepath = set_image_dpi(TESTFILE_IMAGE_PATH)
        temp_image = Image.open(filepath)
        assert (math.ceil(temp_image.info["dpi"][0]), math.ceil(temp_image.info["dpi"][1])) == (300, 300)

    def test_image_smoothening(self):
        """

        :return:
        """
        img = cv2.imread(TESTFILE_IMAGE_PATH, 0)
        filtered = cv2.adaptiveThreshold(
            img.astype(np.uint8),
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            41,
            3,
        )
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
        smooth_image = image_smoothening(closing)
        assert smooth_image.shape == (200, 600) and smooth_image.mean() == 215.6025

    def test_remove_noise_and_smooth(self):
        """

        :return:
        """
        return_image = remove_noise_and_smooth(TESTFILE_IMAGE_PATH)
        assert return_image.shape == (200, 600) and return_image.mean() == 216.10825

    def test_preprocess_image_for_ocr(self):
        """

        :return:
        """
        return_image = preprocess_image_for_ocr(TESTFILE_IMAGE_PATH)
        assert (
            return_image.shape == (600, 1800)
            and return_image.mean() == 217.01633333333334
        )
