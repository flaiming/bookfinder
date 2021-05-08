import cv2 as cv
#import matplotlib.pyplot as plt


class FlannMatcher:

    def __init__(self, image_paths):
        self.sift = cv.SIFT_create()
        self.train_images = []
        for image_path in image_paths:
            im = cv.imread(image_path, cv.IMREAD_GRAYSCALE)  # trainImage
            # Initiate SIFT detector
            kp, des = self.sift.detectAndCompute(im, None)
            self.train_images.append((image_path, im, kp, des))

    def find_matches(self, image_path):
        img = cv.imread(image_path, cv.IMREAD_GRAYSCALE)          # queryImage

        # find the keypoints and descriptors with SIFT
        kp, des = self.sift.detectAndCompute(img, None)

        # FLANN parameters
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=10)   # or pass empty dictionary
        flann = cv.FlannBasedMatcher(index_params, search_params)

        counts = {}
        for image_path, im1, kp1, des1 in self.train_images:
            matches = flann.knnMatch(des1, des, k=2)

            #matches = matches[::2]

            # Need to draw only good matches, so create a mask
            matchesMask = [[0, 0] for i in range(len(matches))]

            matches_count = 0
            # ratio test as per Lowe's paper
            for i, (m, n) in enumerate(matches):
                if m.distance < 0.4 * n.distance:
                    matchesMask[i] = [1, 0]
                    matches_count += 1

            if matches_count > 15:
                counts[image_path] = matches_count
                draw_params = dict(matchColor=(0, 255, 0),
                                   singlePointColor=(255, 0, 0),
                                   matchesMask=matchesMask,
                                   flags=cv.DrawMatchesFlags_DEFAULT)
                img3 = cv.drawMatchesKnn(im1, kp1, img, kp, matches, None, **draw_params)

                image_name = image_path.split("/")[-1]
                cv.imwrite(f"output/{image_name}", img3)
                #plt.imshow(img3,), plt.show()
        return counts
