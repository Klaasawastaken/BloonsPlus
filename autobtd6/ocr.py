from helper import *

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Loading this model (TensorFlow/Keras import + weights) costs several real
# seconds. custom_ocr() is only called once actual gameplay reads cash - a run
# that bails before then (e.g. a MEDAL_ALREADY_EARNED badge check during menu
# navigation) never needs it, so defer the load to first real use instead of
# paying the cost on every process spawn.
_ocr_model = None

def round_recovery_candidate(raw, anchor, elapsed):
    """Allow delayed counter recovery only with a complete, bounded round HUD."""
    parts = raw.split('/')
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return False
    reading, limit = map(int, parts)
    return (limit in (40, 60, 80, 100) and anchor < reading <= limit
            and elapsed >= max(5, reading - anchor))
def _get_ocr_model():
    global _ocr_model
    if _ocr_model is None:
        import keras
        _ocr_model = keras.models.load_model("btd6_ocr_net.h5")
    return _ocr_model


def custom_ocr(img, resolution=pyautogui.size(), white_threshold=224):
    # Work on a private buffer: callers pass crops that are views into the live
    # screenshot. Keep antialiased white text without modifying that screenshot.
    img = np.ascontiguousarray(img.copy())
    original = img.copy()
    h, w = img.shape[:2]
    white = np.array([255, 255, 255], dtype=np.uint8)
    bright = np.all(img >= white_threshold, axis=2)
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

    # Snow, foliage and effects show through the transparent HUD. White pixels
    # alone turn those into phantom digits. HUD glyphs have a dark outline and
    # share a baseline; use the clearly outlined glyphs to establish that row.
    outlines = {}
    anchors = []
    dark = np.all(original < 110, axis=2)
    for index, contour in enumerate(cnts):
        x, y, cw, ch = cv2.boundingRect(contour)
        if ch < 18 * resolution[0] / 2560 or cw > 48 * resolution[1] / 1440:
            continue
        mask = np.zeros((h, w), np.uint8)
        cv2.drawContours(mask, [contour], -1, 1, -1)
        ring = (cv2.dilate(mask, np.ones((5, 5), np.uint8)) > 0) & (mask == 0)
        outline = float(dark[ring].mean()) if np.any(ring) else 0.0
        outlines[index] = outline
        if outline >= 0.15:
            anchors.append((y, y + ch))
    baseline = np.median(np.array(anchors), axis=0) if anchors else None

    for index, c in enumerate(cnts):
        minX, minY, chrW, chrH = cv2.boundingRect(c)
        maxX, maxY = minX + chrW, minY + chrH
        if baseline is not None:
            tolerance = max(3, 5 * resolution[0] / 1920)
            if (outlines.get(index, 0) < 0.06 or abs(minY - baseline[0]) > tolerance
                    or abs(maxY - baseline[1]) > tolerance):
                continue
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
    currentX = None
    for entry in chrImages:
        # The HUD shifts when a panel or badge is shown. The first glyph is
        # allowed anywhere in the crop; a left-padding offset is not a gap.
        if currentX is None or currentX + 50 * resolution[0] / 1920 >= entry[0]:
            currentX = entry[0]
            filteredChrImages.append(entry)
        else:
            break
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
