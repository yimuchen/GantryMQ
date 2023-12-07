## Direct methods to be overloaded onto the client
from typing import Tuple, Dict, List

import logging
import cv2
import numpy
import scipy


# Basic methods for accessing the various methods
def register_method_for_client(cls):
    for method in ["reset_camera_device", "get_frame"]:
        cls.register_client_method(method)


# Additional helper methods for helping with the parsing of the captured image

VISALGO_THRESHOLD_DEFAULT = 80  # Luminosity threshold for edge detection  (0-255)
VISALGO_BLUR_DEFAULT = 5  # Blur to apply before thresholding (pixels)
VISALGO_MAXLUMI_DEFAULT = 90  # Luminosity cut-off for determining valid contour
VISALGO_MINSIZE_DEFAULT = 50  # Minimum contour size cutoff (pixels)
VISALGO_MAXRATIO_DEFAULT = 1.4  # Maximum contour bounding box method
VISALGO_POLYEPS_DEFAULT = 0.08  # Polygon approximation threshold


def get_processed_image(orig_img: numpy.ndarray, **kwargs) -> numpy.ndarray:
    """
    Given the original image, return the processed image of the feature finding
    algorithm
    """
    contours = get_unprocessed_contours(orig_img, **kwargs)
    contours = order_contours(orig_img, contours, **kwargs)

    # Creating the new image
    new_image = orig_img.copy()

    # Plotting the failed images
    _color_map_ = {
        "fail_ratio": (100, 255, 255),
        "fail_lumi": (100, 255, 100),
        "fail_rect": (255, 255, 255),
        "good": (255, 255, 100),
    }

    for key, color in _color_map_.items():
        if len(contours[key]):
            new_image = cv2.drawContours(
                *(new_image, contours[key], -1), color=color, thickness=2
            )

    for c, l in zip(contours["fail_lumi"], contours["fail_lumi_val"]):
        result = _summarize_contour(orig_img, c)
        x, y = result["position"]
        new_image = cv2.putText(
            new_image,
            f"{l:.1f}",
            (int(x), int(y)),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.9,
            color=(100, 255, 100),
            thickness=2,
        )

    # Additional information for the found point
    if len(contours["good"]):
        new_image = cv2.drawContours(
            *(new_image, [contours["good"][0]], -1), color=(100, 100, 255), thickness=4
        )
        result = _summarize_contour(orig_img, contours["good"][0])
        x, y = result["position"]
        s2, s4 = result["sharpness"]
        pos_str = f"(x:{x:.1f}, y:{y:.1f})"
        shp_str = f"(s2:{s2:.2f}, s4:{s4:.1f})"
        new_image = cv2.putText(
            *(new_image, pos_str + " " + shp_str, (50, 50)),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.9,
            color=(100, 100, 255),
            thickness=2,
        )
        new_image = cv2.circle(
            *(new_image, (round(x), round(y)), 3), color=(100, 100, 255), thickness=-1
        )
    else:
        new_image = cv2.putText(
            *(new_image, "Not found", (50, 50)),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.9,
            color=(100, 100, 255),
            thickness=2,
        )

    return new_image


def get_unprocessed_contours(img: numpy.ndarray, **kwargs) -> Tuple[numpy.ndarray]:
    """Getting all contours using client level parameters"""
    blur = kwargs.get("visalgo_blur", VISALGO_BLUR_DEFAULT)
    threshold = kwargs.get("visalgo_threshold", VISALGO_THRESHOLD_DEFAULT)

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  #
    img = cv2.blur(img, (blur, blur))
    ret, img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def order_contours(
    img: numpy.ndarray, contours: Tuple[numpy.ndarray], **kwargs
) -> Dict[str, List[numpy.ndarray]]:
    """Organizing and displaying the contours according to the requirements"""

    size_min = kwargs.get("visalgo_minsize", VISALGO_MINSIZE_DEFAULT)
    ratio_max = kwargs.get("visalgo_maxratio", VISALGO_MAXRATIO_DEFAULT)
    lumi_max = kwargs.get("visalgo_maxlumi", VISALGO_MAXLUMI_DEFAULT)
    poly_eps = kwargs.get("visalgo_polyeps", VISALGO_POLYEPS_DEFAULT)

    return_dict = {
        "good": [],  # Good contours that match all criteria (ordered by size)
        "fail_rect": [],  # Contours that fail rectangle approximation
        "fail_lumi": [],  # Contours where the image area is too bright
        "fail_ratio": [],  # Contours that are not sufficiently regular
    }

    # Discarding contours that are considered grains
    _size = [_contour_size(c) for c in contours]
    contours = [c for c, s in zip(contours, _size) if s > size_min]

    # Contours that are not sufficiently regular
    _ratio = [_contour_ratio(c) for c in contours]
    return_dict["fail_ratio"] = [c for c, r in zip(contours, _ratio) if r > ratio_max]
    contours = [c for c, r in zip(contours, _ratio) if r <= ratio_max]

    # Contours that fail a luminosity requirement
    _lumi = [_contour_lumi(img, c) for c in contours]
    return_dict["fail_lumi"] = [c for c, l in zip(contours, _lumi) if l > lumi_max]
    return_dict["fail_lumi_val"] = [l for c, l in zip(contours, _lumi) if l > lumi_max]
    contours = [c for c, l in zip(contours, _lumi) if l <= lumi_max]

    # Converting to convex hull to remove potential reflection artifacts
    contours = [cv2.convexHull(c) for c in contours]

    # Convex hull should approximate to a rectangle
    _poly = [_polygon_approx(c, poly_eps).shape[0] for c in contours]
    return_dict["fail_rect"] = [c for c, p in zip(contours, _poly) if p != 4]
    return_dict["good"] = [c for c, p in zip(contours, _poly) if p == 4]

    # Ordering according to convex hull area size
    return_dict["good"].sort(key=_contour_area, reverse=True)

    return return_dict


def _summarize_contour(img: numpy.ndarray, contour: numpy.ndarray) -> Dict:
    """
    Summarizing the image and contour properties that can be used to determine
    to detected position in image coordinates
    """
    # position calculation of final contour
    m = cv2.moments(contour)
    mx, my = m["m10"] / m["m00"], m["m01"] / m["m00"]

    # Sharpness
    s2, s4 = _sharpness(img, contour)

    # Returning items of interest
    return {
        "position": (mx, my),
        "sharpness": (s2, s4),
    }


def _contour_size(contour: numpy.ndarray) -> int:
    """Size of contour bounding box"""
    x, y, w, h = cv2.boundingRect(contour)
    return numpy.max([w, h])


def _contour_ratio(contour: numpy.ndarray) -> float:
    x, y, w, h = cv2.boundingRect(contour)
    return numpy.max([w, h]) / numpy.min([w, h])


def _contour_lumi(image: numpy.ndarray, contour: numpy.ndarray) -> float:
    """Getting the average luminosity of an image masked by a contour"""
    mask = numpy.zeros_like(image[..., 0])  # Single channel mask
    cv2.drawContours(mask, [contour], 0, 255, 0)  # Creating mask
    mean = cv2.mean(image, mask)
    # Conversion equation from https://en.wikipedia.org/wiki/Relative_luminance
    return 0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]


def _polygon_approx(contour: numpy.ndarray, epsilon: float) -> numpy.ndarray:
    return cv2.approxPolyDP(
        contour, epsilon=_contour_size(contour) * epsilon, closed=True
    )


def _contour_area(contour: numpy.ndarray) -> int:
    x, y, w, h = cv2.boundingRect(contour)
    return w * h


def _sharpness(img: numpy.ndarray, contour: numpy.ndarray) -> (float, float):
    """
    Calculating the sharpness measure of an image in the region defined around a
    contour
    """
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Crop to region around contour
    x, y, w, h = cv2.boundingRect(contour)
    x_start = numpy.max([int(x - w / 2), 0])
    x_end = numpy.min([x_start + 2 * w, img.shape[1]])
    y_start = numpy.max([int(y - h / 2), 0])
    y_end = numpy.min([y_start + 2 * h, img.shape[0]])
    img = img[y_start:y_end, x_start:x_end]

    # Apply a 2x2 blur to avoid single point noises
    if len(img) == 0:
        return 0, 0
    img = cv2.blur(img, (2, 2))

    # Calculating overall laplacian with a kernel size of 5 pixels
    lap = cv2.Laplacian(img, cv2.CV_64F, 5)

    s2 = scipy.stats.moment(lap, axis=None, moment=2)
    s4 = scipy.stats.moment(lap, axis=None, moment=4)

    return s2, s4


if __name__ == "__main__":
    from zmq_client import HWControlClient

    # Adding the additional methods
    register_method_for_client(HWControlClient)

    logging.root.setLevel(1)
    logging.basicConfig(level=logging.NOTSET)
    client = HWControlClient("localhost", 8989)
    client.reset_camera_device("/dev/video1")

    # Testing the image processing
    while True:
        frame = client.get_frame()
        cv2.imshow("frame", get_processed_image(frame))

        if cv2.waitKey(1) == ord("q"):
            break
