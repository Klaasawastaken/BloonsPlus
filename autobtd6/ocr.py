from helper import *

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Loading this model (TensorFlow/Keras import + weights) costs several real
# seconds. custom_ocr() is only called once actual gameplay reads cash - a run
# that bails before then (e.g. a MEDAL_ALREADY_EARNED badge check during menu
# navigation) never needs it, so defer the load to first real use instead of
# paying the cost on every process spawn.
_ocr_model = None
def _get_ocr_model():
    global _ocr_model
    if _ocr_model is None:
        import keras
        _ocr_model = keras.models.load_model("btd6_ocr_net.h5")
    return _ocr_model


def custom_ocr(img, resolution=pyautogui.size()):
    # Work on a private buffer: callers pass crops that are views into the live
    # screenshot. Keep antialiased white text without modifying that screenshot.
    img = np.ascontiguousarray(img.copy())
    h, w = img.shape[:2]
    white = np.array([255, 255, 255], dtype=np.uint8)
    bright = np.all(img >= 224, axis=2)
    img[:] = 0
    img[bright] = white

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)[1]
    cnts, _ = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    chrImages = []
    chrImagesMinX = {}
    chrs = {}

    for c in cnts:
        minX, minY, chrW, chrH = cv2.boundingRect(c)
        maxX, maxY = minX + chrW, minY + chrH
        chrImg = img[minY:maxY, minX:maxX]

        if (
            chrImg.shape[0] >= 18 * resolution[0] / 2560
            and chrImg.shape[0] <= 65 * resolution[0] / 2560
            # Thin digits such as "1" were discarded by the old 14px cutoff.
            and chrImg.shape[1] >= 4 * resolution[1] / 1440
            and chrImg.shape[1] <= 48 * resolution[1] / 1440
        ):
            chrImg = cv2.resize(chrImg, (50, 50))
            chrImg = cv2.copyMakeBorder(
                chrImg, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(0, 0, 0)
            )
            chrImg = chrImg[:, :, 0]

            for y in range(0, 60):
                for x in range(0, 60):
                    chrImg[y][x] = int(chrImg[y][x] / 255)

            chrImages.append([minX, chrImg])

    chrImages.sort(key=lambda item: item[0])
    # ignore entries after gap(e. g. explosion particles)
    filteredChrImages = []
    currentX = 0
    for entry in chrImages:
        if currentX + 50 >= entry[0]:
            currentX = entry[0]
            filteredChrImages.append(entry)
    # minXs = list(map(lambda item: item[0], chrImages))
    if len(filteredChrImages) == 0:
        return "-1"
    chrImages = list(map(lambda item: item[1], filteredChrImages))
    chrImages = np.array(chrImages)

    predictions = _get_ocr_model().predict(chrImages, verbose=0)

    number = ""

    for prediction in predictions:
        value = np.argmax(prediction)
        if value == 10:
            number += '/'
        else:
            number += str(value)

    return number
