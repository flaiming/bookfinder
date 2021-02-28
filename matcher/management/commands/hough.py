import os
from PIL import Image
import cv2
import numpy as np
import math

from django.core.management.base import BaseCommand
from matcher.models import BookCover


def polar2cartesian(rho: float, theta_rad: float, rotate90: bool = False):
    """
    Converts line equation from polar to cartesian coordinates
    Args:
        rho: input line rho
        theta_rad: input line theta
        rotate90: output line perpendicular to the input line
    Returns:
        m: slope of the line
           For horizontal line: m = 0
           For vertical line: m = np.nan
        b: intercept when x=0
    """
    x = np.cos(theta_rad) * rho
    y = np.sin(theta_rad) * rho
    m = np.nan
    if not np.isclose(x, 0.0):
        m = y / x
    if rotate90:
        if m is np.nan:
            m = 0.0
        elif np.isclose(m, 0.0):
            m = np.nan
        else:
            m = -1.0 / m
    b = 0.0
    if m is not np.nan:
        b = y - m * x

    return m, b


def solve4x(y: float, m: float, b: float):
    """
    From y = m * x + b
         x = (y - b) / m
    """
    if np.isclose(m, 0.0):
        return 0.0
    if m is np.nan:
        return b
    return (y - b) / m


def solve4y(x: float, m: float, b: float):
    """
    y = m * x + b
    """
    if m is np.nan:
        return b
    return m * x + b


def intersection(m1: float, b1: float, m2: float, b2: float):
    # Consider y to be equal and solve for x
    # Solve:
    #   m1 * x + b1 = m2 * x + b2
    x = (b2 - b1) / (m1 - m2)
    # Use the value of x to calculate y
    y = m1 * x + b1

    return int(round(x)), int(round(y))


def line_end_points_on_image(rho: float, theta: float, image_shape: tuple):
    """
    Returns end points of the line on the end of the image
    Args:
        rho: input line rho
        theta: input line theta
        image_shape: shape of the image
    Returns:
        list: [(x1, y1), (x2, y2)]
    """
    m, b = polar2cartesian(rho, theta, True)

    end_pts = []

    if not np.isclose(m, 0.0):
        x = int(0)
        y = int(solve4y(x, m, b))
        if point_on_image(x, y, image_shape):
            end_pts.append((x, y))
            x = int(image_shape[1] - 1)
            y = int(solve4y(x, m, b))
            if point_on_image(x, y, image_shape):
                end_pts.append((x, y))

    if m is not np.nan:
        y = int(0)
        x = int(solve4x(y, m, b))
        if point_on_image(x, y, image_shape):
            end_pts.append((x, y))
            y = int(image_shape[0] - 1)
            x = int(solve4x(y, m, b))
            if point_on_image(x, y, image_shape):
                end_pts.append((x, y))

    return end_pts


def hough_lines_end_points(lines: np.array, image_shape: tuple):
    """
    Returns end points of the lines on the edge of the image
    """
    if len(lines.shape) == 3 and \
            lines.shape[1] == 1 and lines.shape[2] == 2:
        lines = np.squeeze(lines)
    end_pts = []
    for line in lines:
        rho, theta = line
        end_pts.append(
            line_end_points_on_image(rho, theta, image_shape))
    return end_pts


def hough_lines_intersection(lines: np.array, image_shape: tuple):
    """
    Returns the intersection points that lie on the image
    for all combinations of the lines
    """
    if len(lines.shape) == 3 and \
            lines.shape[1] == 1 and lines.shape[2] == 2:
        lines = np.squeeze(lines)
    lines_count = len(lines)
    intersect_pts = []
    for i in range(lines_count - 1):
        for j in range(i + 1, lines_count):
            m1, b1 = polar2cartesian(lines[i][0], lines[i][1], True)
            m2, b2 = polar2cartesian(lines[j][0], lines[j][1], True)
            try:
                x, y = intersection(m1, b1, m2, b2)
            except Exception as e:
                print("ERROR", e)
                continue
            if point_on_image(x, y, image_shape):
                intersect_pts.append([x, y])
    return np.array(intersect_pts, dtype=int)


def point_on_image(x: int, y: int, image_shape: tuple):
    """
    Returns true is x and y are on the image
    """
    return 0 <= y < image_shape[0] and 0 <= x < image_shape[1]


def intersection2(line1, line2):
    x1, a1, b1, c1 = line1
    x2, a2, b2, c2 = line2

    det = a1 * b2 - a2 * b1
    print("=======determinant", det)
    if det == 0:
        print("PARRALEL LINES")
        return None, None
    else:
        x = -(c1 * b2 - c2 * b1) / det
        y = -(a1 * c2 - a2 * c1) / det
    return x, y


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for name in os.listdir("knihy"):
            image_path = os.path.join("knihy", name)
            print(image_path)
            self.crop(image_path)

    def crop(self, image_path):
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        cv2.imwrite("edges.jpg", edges)

        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        print("lines", len(lines))

        counter = 0
        better_lines = []
        vertical_lines = []
        horizontal_lines = []
        for aa in lines:
            for rho, theta in aa:
                print()
                deg = math.degrees(theta)
                #print("uhel", deg % 90, deg)
                if 5 < deg % 90 < 85:
                    continue

                print(theta, deg)
                m, b = polar2cartesian(rho, theta)
                print("line", m, b)
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                x1 = int(x0 + 1000 * (-b))
                y1 = int(y0 + 1000 * (a))
                x2 = int(x0 - 1000 * (-b))
                y2 = int(y0 - 1000 * (a))

                try:
                    u1 = x2 - x1
                    u2 = y2 - y1
                    aa = u2
                    bb = -u1
                    print("-----a, b", (a, b))
                    print("a, b", (aa, bb))

                    if 175 < deg < 185 or 355 < deg <= 360 or 0 <= deg < 5:
                        # vertical
                        print("vertical")
                        # TODO myslet na primo svislou primku
                        c = -(aa * x1 + bb * y1)
                        y = 100
                        x = (bb * y1 - c) / aa
                        print("x, y", (x, y))
                        vertical_lines.append([x, aa, bb, c])

                        # remove lines that are in the middle
                        vertical_lines = sorted(vertical_lines, key=lambda x: x[0])
                        if len(vertical_lines) > 2:
                            vertical_lines = [vertical_lines[0], vertical_lines[-1]]
                        print(vertical_lines)

                    if 85 < deg < 95 or 265 < deg < 275:
                        # horizontal
                        print("horizontal")
                        c = -(aa * x1 + bb * y1)
                        x = 100
                        y = (aa * x1 - c) / bb
                        print("x, y", (x, y))
                        horizontal_lines.append([y, aa, bb, c])

                        # remove lines that are in the middle
                        horizontal_lines = sorted(horizontal_lines, key=lambda x: x[0])
                        if len(horizontal_lines) > 2:
                            horizontal_lines = [horizontal_lines[0], horizontal_lines[-1]]
                        print(horizontal_lines)

                    #cv2.circle(img, (int(x), int(y)), 5, (255, 0, 0), 10)

                    #cv2.line(img, (xx1, yy1), (xx2, yy2), (0, 0, counter), 2)

                except Exception as e:
                    print("-----ERROR", e)
                    continue

                #cv2.line(img, (x1, y1), (x2, y2), (0, 0, counter), 2)
                print("counter", counter)
                counter += 30

                better_lines.append([rho, theta])
            #if counter >= 6000:
            #    break

        #for x, *_ in vertical_lines:
        #    cv2.circle(img, (int(x), 200), 5, (0, 255, 0), 10)

        #for y, *_ in horizontal_lines:
        #    cv2.circle(img, (200, int(y)), 5, (255, 0, 0), 10)

        if len(vertical_lines) != 2 or len(horizontal_lines) != 2:
            print("=======================NO INTERSECTIONS =============")
            return

        # calculate intersections
        intersections = []
        for i in range(2):
            for j in range(2):
                x, y = intersection2(vertical_lines[j], horizontal_lines[i])
                print("======x, y", (x, y))
                #cv2.circle(img, (int(x), int(y)), 5, (255, 255, 0), 15)
                intersections.append([x, y])

        # warp image
        pts1 = np.float32([intersections])
        #cover_w, cover_h = (100, 158)
        cover_w, cover_h = (253, 400)
        pts2 = np.float32([[0, 0], [cover_w, 0], [0, cover_h], [cover_w, cover_h]])

        M = cv2.getPerspectiveTransform(pts1, pts2)

        dst = cv2.warpPerspective(img, M, (cover_w, cover_h))

        cv2.imwrite("_" + image_path, dst)
