import windowed_input  # patch game-relative screenshot/input before helper binds resolutions
from helper import *
from ocr import custom_ocr, cash_ocr, round_recovery_candidate
import subprocess
import os
import hashlib
import json
import tempfile
import threading
import time
from copy import deepcopy
from game_runtime import GameState, normalize_action
from upgrade_rules import can_upgrade_in_roster, read_upgrade_caps
from upgrade_observation import observe_upgrade, resolve_hud_panels, select_tower, verify_tower_placement
from placement_observation import held_placement_visible
from placement_hints import route_placement_hints
from route_timing import delay_ready, round_offset_ready, ability_ready, issue_ability, upgrade_ready, RepeatedAbilities, round_start_ready
from purchase_pacing import affordable_upgrade_batch, purchase_pacing_ready
from map_availability import predicted_thaw_round
from resume_recovery import restore_upgrade_steps, probe_owned_upgrade, resumable_round_start

LAST_HERO_FILE = 'last-hero.json'
UPGRADE_MEMORY_FILE = 'upgrade-memory.json'
PAUSE_FILE = 'pause.flag'
GAME_STATE_FILE = 'game-state.json'
_viewerLastFrame = 0

def publishViewerFrame(frame):
    global _viewerLastFrame
    if time.time() - _viewerLastFrame < 1:
        return
    _viewerLastFrame = time.time()
    try:
        with open('viewer-request.json', encoding='utf-8') as request:
            if json.load(request).get('expiresAt', 0) < time.time() * 1000:
                return
        if not windowed_input.is_game_foreground():
            return
        preview = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
        success, encoded = cv2.imencode('.jpg', preview, [cv2.IMWRITE_JPEG_QUALITY, 76])
        if success:
            with open('live-frame.jpg.tmp', 'wb') as output:
                output.write(encoded.tobytes())
            os.replace('live-frame.jpg.tmp', 'live-frame.jpg')
    except (OSError, ValueError):
        pass  # The viewer must never interrupt a replay.
ROUTE_CHECKPOINT_FILE = 'route-checkpoint.json'
_route_checkpoint_lock = threading.Lock()

def checkpointStepOffset(steps, total):
    """Retries retain original route positions; supplemental actions consume none."""
    indices = [step.get('routeStepIndex') for step in steps]
    return min((index for index in indices if type(index) is int and 0 <= index < total), default=total)


def recordUpgradeCheckpoint(checkpoint, action):
    """Retain planned upgrade intent until the same tower's tiers prove it owned."""
    pending = checkpoint.setdefault('unresolvedUpgrades', [])
    observation = action.get('upgradeObservation', {})
    actual = observation.get('after')
    if observation.get('status') == 'confirmed' and isinstance(actual, list) and len(actual) == 3:
        checkpoint['unresolvedUpgrades'] = [entry for entry in pending
            if not (entry.get('name') == action.get('name')
                    and len(entry.get('expectedUpgradeTiers', [])) == 3
                    and all(a >= t for a, t in zip(actual, entry['expectedUpgradeTiers'])))]
        return
    target = action.get('expectedUpgradeTiers')
    if not isinstance(target, list) or len(target) != 3:
        return  # No trustworthy target; never invent tiers from an unreadable panel.
    entry = {key: action[key] for key in ('action', 'name', 'path', 'key', 'cost') if key in action}
    entry['pos'] = list(action['pos']) if action.get('pos') is not None else None
    entry['expectedUpgradeTiers'] = list(target)
    if 'deferredUpgradeRound' in action:
        entry['deferredUpgradeRound'] = action['deferredUpgradeRound']
    entry['opportunistic'] = bool(action.get('extra', {}).get('opportunistic'))
    entry['observationStatus'] = observation.get('status', 'unknown')
    for index, previous in enumerate(pending):
        if previous.get('name') == action.get('name') and previous.get('expectedUpgradeTiers') == target:
            pending[index] = entry  # Keep the latest tracked position and observation from retries.
            return
    pending.append(entry)

def writeRouteCheckpoint(checkpoint, remainingSteps=None):
    """Atomically persist resume state without letting a transient Windows file lock kill a run."""
    temporary = None
    with _route_checkpoint_lock:
        if remainingSteps is not None:
            checkpoint['remainingSteps'] = deepcopy(remainingSteps)
            checkpoint['version'] = 2
        checkpoint['updatedAt'] = time.time()
        try:
            directory = os.path.dirname(os.path.abspath(ROUTE_CHECKPOINT_FILE))
            fd, temporary = tempfile.mkstemp(prefix='.route-checkpoint-', suffix='.tmp', dir=directory)
            with os.fdopen(fd, 'w', encoding='utf-8') as fp:
                json.dump(checkpoint, fp, indent=2)
                fp.flush()
                os.fsync(fp.fileno())
            last_error = None
            for attempt in range(6):
                try:
                    os.replace(temporary, ROUTE_CHECKPOINT_FILE)
                    return True
                except PermissionError as error:
                    last_error = error
                    if attempt < 5:
                        time.sleep(0.05 * (attempt + 1))
            # Preserve the existing checkpoint and keep playing if an external
            # reader still holds the target. A checkpoint failure is recoverable;
            # it must not become a route defeat or terminate the replay process.
            print(f'WARNING checkpoint save deferred after Windows file lock: {last_error}', flush=True)
            return False
        except OSError as error:
            print(f'WARNING checkpoint save failed; replay continues and previous checkpoint is preserved: {error}', flush=True)
            return False
        finally:
            if temporary and os.path.exists(temporary):
                try: os.unlink(temporary)
                except OSError: pass

def readRouteCheckpoint():
    try:
        with open(ROUTE_CHECKPOINT_FILE, encoding='utf-8') as fp:
            return json.load(fp)
    except (OSError, ValueError):
        return None

def mapSceneSignature(image):
    """Sparse playfield pixels; stable terrain should dominate moving bloons/towers."""
    height, width = image.shape[:2]
    return [image[int(height * (0.18 + row * 0.055)), int(width * (0.18 + col * 0.036))].tolist()
            for row in range(12) for col in range(18)]

def sceneMatches(saved, current):
    if not isinstance(saved, list) or len(saved) != len(current):
        return False
    matching = sum(1 for before, after in zip(saved, current)
                   if len(before) == 3 and sum(abs(int(a) - int(b)) for a, b in zip(before, after)) < 85)
    return matching >= int(len(current) * 0.60)

_game_state_lock = threading.Lock()


def saveGameState(gameState):
    if gameState is None:
        return
    temporaryFile = None
    with _game_state_lock:
        try:
            # Use a private sibling file so concurrent writers cannot truncate
            # the payload waiting for Windows readers to release the target.
            directory = os.path.dirname(os.path.abspath(GAME_STATE_FILE))
            fd, temporaryFile = tempfile.mkstemp(prefix='.game-state-', suffix='.tmp', dir=directory)
            with os.fdopen(fd, 'w', encoding='utf-8') as fp:
                json.dump(gameState.to_dict(), fp, indent=2)
                fp.flush()
                os.fsync(fp.fileno())
            for attempt in range(5):
                try:
                    os.replace(temporaryFile, GAME_STATE_FILE)
                    return
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep(0.05 * (attempt + 1))
        except (OSError, TypeError, ValueError) as error:
            customPrint('WARNING could not persist game state; previous state preserved: ' + str(error))
        finally:
            if temporaryFile and os.path.exists(temporaryFile):
                try:
                    os.unlink(temporaryFile)
                except OSError:
                    pass


def updateUpgradeMemory(action, mapConfig, runId, cashBefore, cashAfter, roundNumber):
    """Persist route purchases confirmed by tier pips or a positive cash drop."""
    if action.get('action') != 'upgrade' or 'path' not in action:
        return
    try:
        with open(UPGRADE_MEMORY_FILE, encoding='utf-8') as fp:
            memory = json.load(fp)
    except (OSError, ValueError):
        memory = {'version': 2, 'scope': 'positive-net-cash-drop-route-purchases', 'runs': {}}
    memory.setdefault('version', 2)
    memory.setdefault('scope', 'positive-net-cash-drop-route-purchases')
    memory.setdefault('runs', {})
    runKey = str(runId or int(time.time() * 1000))
    run = memory['runs'].setdefault(runKey, {
        'runId': runKey,
        'map': mapConfig.get('map'),
        'difficulty': mapConfig.get('difficulty'),
        'gamemode': mapConfig.get('gamemode'),
        'startedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'towers': {},
    })
    name = str(action.get('name', 'unknown'))
    monkey = mapConfig.get('monkeys', {}).get(name, {})
    entry = run['towers'].setdefault(name, {'type': monkey.get('type'), 'upgrades': [0, 0, 0], 'source': 'cash-confirmed-route'})
    levels = entry.setdefault('upgrades', [0, 0, 0])
    path = int(action['path'])
    if 0 <= path < 3:
        observation = action.get('upgradeObservation', {})
        if observation.get('status') == 'confirmed':
            levels[:] = observation['after']
            entry['source'] = 'panel-tier-confirmed-route'
            memory['scope'] = 'observed-route-purchases'
        else:
            levels[path] = min(5, int(levels[path]) + 1)
        entry['lastUpdated'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        entry['lastAction'] = {
            'path': path,
            'level': levels[path],
            'cost': action.get('cost'),
            'round': roundNumber if roundNumber >= 0 else None,
            'cashBefore': cashBefore,
            'cashAfter': cashAfter,
            'observedSpend': cashBefore - cashAfter,
            'position': monkey.get('pos'),
            'confirmedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        temporaryFile = None
        try:
            directory = os.path.dirname(os.path.abspath(UPGRADE_MEMORY_FILE))
            fd, temporaryFile = tempfile.mkstemp(prefix='.upgrade-memory-', suffix='.tmp', dir=directory)
            with os.fdopen(fd, 'w', encoding='utf-8') as fp:
                json.dump(memory, fp, indent=2)
                fp.flush()
                os.fsync(fp.fileno())
            lastError = None
            for attempt in range(6):
                try:
                    os.replace(temporaryFile, UPGRADE_MEMORY_FILE)
                    temporaryFile = None
                    return
                except PermissionError as error:
                    lastError = error
                    if attempt < 5:
                        time.sleep(0.05 * (attempt + 1))
            customPrint('WARNING could not persist upgrade memory after Windows file-lock retries: ' + str(lastError))
        except OSError as error:
            customPrint('WARNING could not persist upgrade memory: ' + str(error))
        finally:
            if temporaryFile and os.path.exists(temporaryFile):
                try: os.unlink(temporaryFile)
                except OSError: pass

def readLastHero():
    from hero_picker_memory import read_memory
    value = read_memory(LAST_HERO_FILE).get('hero')
    return value if isinstance(value, str) else None


def saveLastHero(hero, pickerHint=None):
    from hero_picker_memory import save_selection
    try:
        save_selection(LAST_HERO_FILE, hero, time.time(), pickerHint)
    except OSError as error:
        customPrint('WARNING hero selection memory not saved: ' + str(error))

_recognizeScreen = recognizeScreen


def mapSelectionChromeVisible(img):
    """Recognize the three fixed menu controls across changing map pages.

    The old reference classifier can report UNKNOWN on a newly added map page.
    The blue Back button, yellow page arrow and orange Expert tab remain fixed.
    """
    h, w = img.shape[:2]
    if h < 700 or w < 1200 or abs(w / h - 16 / 9) > 0.06:
        return False
    def share(box, color):
        x1, y1, x2, y2 = (round(value * w / 1920) if index % 2 == 0
                          else round(value * h / 1080)
                          for index, value in enumerate(box))
        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            return 0.0
        b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
        if color == 'cyan':
            return float(((b > 130) & (g > 100) & (r < 110)).mean())
        return float(((r > 160) & (g > 90) & (b < 100)).mean())
    return (share((25, 20, 125, 115), 'cyan') > 0.25
            and share((1600, 385, 1720, 490), 'warm') > 0.09
            and share((1260, 885, 1420, 1050), 'warm') > 0.18)


def recognizeScreen(img, comparisonImages, ignoreFocus=False):
    if not ignoreFocus and not windowed_input.is_game_foreground():
        return Screen.BTD6_UNFOCUSED
    # Check the distinctive Play button before the legacy reference classifier.
    # A broad map-selection reference can also match the animated home screen,
    # causing repeated Back clicks after we have already reached home.
    if img.shape[:2] in ((1080, 1920), (1440, 2560)):
        scale = img.shape[1] / 2560
        samples = [img[round(y * scale), round(1280 * scale)] for y in (1210, 1320)]
        if all(int(green) > 175 and int(green) > int(red) * 1.35 and int(green) > int(blue) * 1.35
               for blue, green, red in samples):
            return Screen.STARTMENU
    if mapSelectionChromeVisible(img):
        return Screen.MAP_SELECTION
    recognized = _recognizeScreen(img, comparisonImages, ignoreFocus=True)
    return recognized

smallActionDelay = 0.05
actionDelay = 0.2
menuChangeDelay = 1
# Category tabs and page arrows animate in well under half a second; verifyVisibleMapTile
# re-checks the page and advances again if a click landed mid-animation.
mapNavDelay = 0.45

DYNAMIC_PLACEMENT_MAPS = {
    'coveredgarden', 'geared', 'erosion', 'sanctuary', 'onetwotree',
    'polyphemus', 'floodedvalley', 'castlerevenge',
    'mushroomgrotto', 'partyparade', 'trickytracks',
}

_titleStartAttempts = 0


def clickTitleStartIfVisible(screenshot):
    """BTD6's title screen ("Welcome to ... START") after a launch/relaunch is not a known screen;
    Esc there opens Quit Game? and the run looped cancel/Esc forever. Click its START instead."""
    global _titleStartAttempts
    if mapSelectionChromeVisible(screenshot):
        _titleStartAttempts = 0
        return False
    h, w = screenshot.shape[:2]
    s = w / 1920
    crop = screenshot[int(925 * s):int(1015 * s), int(830 * s):int(1090 * s)].astype(np.int32)
    if crop.size == 0:
        return False
    b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
    green = float(((g > 90) & (g > r * 1.5) & (g > b * 1.5)).mean())
    if green < 0.4:
        _titleStartAttempts = 0
        return False
    if not windowed_input.focus_game():
        customPrint('WARNING title START deferred: game focus could not be acquired')
        time.sleep(1)
        return True
    _titleStartAttempts += 1
    customPrint('TITLE_SCREEN detected (green=' + str(round(green, 2))
                + '); held START click attempt=' + str(_titleStartAttempts))
    windowed_input.held_click(int(960 * s), int(970 * s))
    time.sleep(menuChangeDelay * 3)
    after = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
    afterCrop = after[int(925 * s):int(1015 * s), int(830 * s):int(1090 * s)].astype(np.int32)
    b, g, r = afterCrop[..., 0], afterCrop[..., 1], afterCrop[..., 2]
    remaining = float(((g > 90) & (g > r * 1.5) & (g > b * 1.5)).mean())
    if remaining < 0.4:
        customPrint('TITLE_SCREEN START accepted; waiting for main menu')
        _titleStartAttempts = 0
    elif _titleStartAttempts >= 3:
        os.makedirs('failure-shots', exist_ok=True)
        cv2.imwrite('failure-shots/title-start-stalled.png', after)
        customPrint('WARNING START unchanged after held clicks; evidence=failure-shots/title-start-stalled.png; retrying after 10s')
        time.sleep(10)
    return True

KNOWN_SPOTS_DIR = 'placement-maps'
_knownSpots = {}


def placementClassFor(action, mapConfig):
    """Placement evidence applies to one tower footprint, not all land/water towers."""
    kind = str(action.get('type') or 'unknown').lower()
    try:
        if kind == 'hero':
            hero = str(mapConfig.get('hero') or action.get('extra', {}).get('type') or 'unknown').lower()
            terrain = towers['heros'].get(hero, {}).get('class', 'land')
            return str(terrain) + ':hero:' + hero
        terrain = towers['monkeys'].get(kind, {}).get('class', 'land')
    except Exception:
        terrain = 'land'
    return str(terrain) + ':' + kind


def _spotsFile(mapName):
    return os.path.join(KNOWN_SPOTS_DIR, str(mapName) + '__known.json')


def loadKnownSpots(mapName):
    """Live placement evidence keyed by tower footprint, in 1920x1080 coordinates.
    Legacy terrain-only buckets are retained but cannot authorize/reject another tower.
    Winning a route does not establish that every planned tower was placed."""
    if mapName in _knownSpots:
        return _knownSpots[mapName]
    data = {'legal': {}, 'illegal': {}}
    try:
        with open(_spotsFile(mapName), encoding='utf-8') as fp:
            saved = json.load(fp)
        data['legal'] = {k: [tuple(v) for v in vals] for k, vals in saved.get('legal', {}).items()}
        data['illegal'] = {k: [tuple(v) for v in vals] for k, vals in saved.get('illegal', {}).items()}
        data['samples'] = saved.get('samples', {})
    except (OSError, ValueError):
        pass
    _knownSpots[mapName] = data
    return data


def recordSpot(mapName, cls, pos, legal, frameWidth):
    """Learn from the game: a confirmed placement is legal, a red ghost is illegal."""
    data = loadKnownSpots(mapName)
    norm = (round(pos[0] * 1920 / frameWidth), round(pos[1] * 1920 / frameWidth))
    keep, drop = ('legal', 'illegal') if legal else ('illegal', 'legal')
    bucket = data[keep].setdefault(cls, [])
    if any((norm[0] - q[0]) ** 2 + (norm[1] - q[1]) ** 2 <= 64 for q in bucket):
        return
    bucket.append(norm)
    # A live confirmation outranks an older contrary record at the same spot.
    data[drop][cls] = [q for q in data[drop].get(cls, []) if (norm[0] - q[0]) ** 2 + (norm[1] - q[1]) ** 2 > 144]
    _saveKnownSpots(mapName)


def _saveKnownSpots(mapName):
    data = loadKnownSpots(mapName)
    try:
        os.makedirs(KNOWN_SPOTS_DIR, exist_ok=True)
        tmp = _spotsFile(mapName) + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fp:
            json.dump({'map': mapName, 'legal': data['legal'], 'illegal': data['illegal'],
                       'samples': data.get('samples', {})}, fp)
        os.replace(tmp, _spotsFile(mapName))
    except OSError:
        pass


_refusedThisRun = {}


def markRefused(mapName, cls, pos, frameWidth):
    """Spots the game refused in this run; also covers moving maps, where refusals aren't
    persisted because the ground may become legal again."""
    _refusedThisRun.setdefault((str(mapName), cls), []).append((pos[0] * 1920 / frameWidth, pos[1] * 1920 / frameWidth))


def knownSpotIsIllegal(mapName, cls, pos, frameWidth):
    # A refusal on a moving/frozen/covered surface expires with its phase.
    # This cache has no phase evidence, so it cannot blacklist changing maps.
    # Returning False means "not known illegal", not "legal": hover/click
    # confirmation still determines whether the current spot can be used.
    if isDynamicPlacementMap(mapName):
        return False
    norm = (pos[0] * 1920 / frameWidth, pos[1] * 1920 / frameWidth)
    if any((norm[0] - q[0]) ** 2 + (norm[1] - q[1]) ** 2 <= 144 for q in _refusedThisRun.get((str(mapName), cls), [])):
        return True
    # Earlier runs may have had another tower/obstacle occupying this point.
    # Preserve those observations for learning, but do not treat them as a
    # permanent terrain ban under a different placement layout.
    return False


def nearestKnownLegalSpots(mapName, cls, pos, frameWidth, occupied, limit=6, maxDistance1080=300):
    """Known-legal spots nearest to pos (frame coordinates), skipping ones our own towers occupy."""
    scale = frameWidth / 1920
    spots = loadKnownSpots(mapName)['legal'].get(cls, [])
    out = []
    for q in spots:
        cand = (int(q[0] * scale), int(q[1] * scale))
        d = (cand[0] - pos[0]) ** 2 + (cand[1] - pos[1]) ** 2
        if d > (maxDistance1080 * scale) ** 2:
            continue
        if any((cand[0] - o[0]) ** 2 + (cand[1] - o[1]) ** 2 < (34 * scale) ** 2 for o in occupied):
            continue
        out.append((d, cand))
    return [c for _, c in sorted(out)[:limit]]


def patchFeature(patch):
    """Terrain appearance under a spot: colour mean/spread plus hue/saturation/brightness."""
    if patch is None or patch.size == 0 or patch.ndim != 3:
        return None
    small = cv2.resize(patch, (24, 24), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float32)
    bgr = small.reshape(-1, 3).astype(np.float32)
    hue = hsv[:, 0] * (np.pi / 90.0)
    weight = hsv[:, 1] / 255.0
    return [round(float(v), 4) for v in (
        *(bgr.mean(0) / 255.0), *(bgr.std(0) / 128.0),
        float((np.cos(hue) * weight).mean()), float((np.sin(hue) * weight).mean()),
        float(hsv[:, 1].mean() / 255.0), float(hsv[:, 2].mean() / 255.0))]


def learnPlacementSample(mapName, cls, feature, legal):
    if feature is None:
        return
    data = loadKnownSpots(mapName)
    samples = data.setdefault('samples', {}).setdefault(cls, [])
    samples.append(feature + [1 if legal else 0])
    del samples[:-500]
    _saveKnownSpots(mapName)


def predictLegalProbability(mapName, cls, feature, k=7):
    """k-nearest-neighbour vote over this map's learned terrain samples; None until enough data."""
    if feature is None:
        return None
    samples = loadKnownSpots(mapName).get('samples', {}).get(cls, [])
    if len(samples) < 6:
        return None
    arr = np.asarray(samples, dtype=np.float32)
    dist = np.sqrt(((arr[:, :-1] - np.asarray(feature, dtype=np.float32)) ** 2).sum(1))
    nearest = np.argsort(dist)[:k]
    weights = 1.0 / (dist[nearest] + 0.05)
    return float((arr[nearest, -1] * weights).sum() / weights.sum())


class TerrainMotion:
    """Moving terrain (gears, platforms, eroding land, closing glass) changes between rounds.
    Snapshot the map at each round start and count, per downscaled cell, how often it changed
    when our own towers can't explain it. Persisted per map so it improves every match."""
    W, H = 240, 135

    def __init__(self, mapName):
        self.path = os.path.join(KNOWN_SPOTS_DIR, str(mapName) + '__motion.npz')
        self.prev = None
        try:
            saved = np.load(self.path)
            self.counts, self.comparisons = saved['counts'].astype(np.float32), int(saved['comparisons'])
        except (OSError, ValueError, KeyError):
            self.counts, self.comparisons = np.zeros((self.H, self.W), np.float32), 0

    def observeRoundStart(self, frame, towerPositions):
        self.observe(frame, towerPositions)

    def observe(self, frame, towerPositions):
        """Called at each round start and every few seconds in play (also before round 1,
        when nothing but the map itself can move). Colour difference, not brightness: a
        coloured object moving over ground of similar brightness was invisible before."""
        small = cv2.GaussianBlur(cv2.resize(frame, (self.W, self.H), interpolation=cv2.INTER_AREA),
                                 (3, 3), 0).astype(np.int16)
        if self.prev is not None:
            changed = (np.abs(small - self.prev).max(axis=2) > 30).astype(np.uint8)
            scale = self.W / frame.shape[1]
            for pos in towerPositions:
                cv2.circle(changed, (int(pos[0] * scale), int(pos[1] * scale)), 7, 0, -1)
            changed[:, int(1640 * self.W / 1920):] = 0
            changed[:int(90 * self.H / 1080), :] = 0
            self.counts += changed
            self.comparisons += 1
            try:
                os.makedirs(KNOWN_SPOTS_DIR, exist_ok=True)
                np.savez(self.path, counts=self.counts, comparisons=self.comparisons)
            except OSError:
                pass
        self.prev = small

    def isMoving(self, pos, frameWidth):
        if self.comparisons < 3:
            return False
        scale = self.W / frameWidth
        x, y = int(pos[0] * scale), int(pos[1] * scale)
        cell = self.counts[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
        if cell.size == 0:
            return False
        # Periodic movers (glass, platforms that shift every few rounds) change rarely but
        # repeatedly; continuous movers change in most samples. Either counts as moving;
        # a one-off projectile streak doesn't.
        peak = float(cell.max())
        return peak >= 2 and (float(cell.mean()) / self.comparisons > 0.2 or peak >= 4)


# Base attack range in BTD6 units; ~3.3 px per unit at 1920x1080. None = map-wide reach.
TOWER_RANGE_UNITS = {
    'dart': 32, 'boomerang': 43, 'bomb': 40, 'tack': 23, 'ice': 20, 'glue': 46, 'desperado': 40,
    'sniper': None, 'sub': 42, 'buccaneer': 60, 'ace': None, 'heli': None, 'mortar': None,
    'dartling': None, 'wizard': 40, 'super': 50, 'ninja': 40, 'alchemist': 45, 'druid': 35,
    'farm': None, 'spike': 34, 'village': None, 'engineer': 40, 'beasthandler': 45, 'mermonkey': 40,
    'hero': 40,
}


# Towers whose value is buffing neighbours: score their spot by how many of our towers it reaches.
SUPPORT_RANGE_UNITS = {'village': 40, 'alchemist': 45}


def supportRangePx(kind, frameWidth):
    units = SUPPORT_RANGE_UNITS.get(kind)
    return None if units is None else units * 3.3 * frameWidth / 1920


def towersInside(pos, rangePx, positions):
    return sum(1 for q in positions if (q[0] - pos[0]) ** 2 + (q[1] - pos[1]) ** 2 <= rangePx * rangePx)


def towerRangePx(action, frameWidth):
    kind = 'hero' if action.get('type') == 'hero' else action.get('type')
    units = TOWER_RANGE_UNITS.get(kind, 40)
    return None if units is None else units * 3.3 * frameWidth / 1920


class PathHeat:
    """Where bloons actually travel: consecutive in-round frames differ along the track every
    frame. Accumulated per map (HUD and our own towers' animation areas masked) and saved."""
    W, H = 240, 135

    def __init__(self, mapName):
        self.path = os.path.join(KNOWN_SPOTS_DIR, str(mapName) + '__path.npz')
        self.prev = None
        self.unsaved = 0
        self._mask = None
        try:
            saved = np.load(self.path)
            self.counts, self.frames = saved['counts'].astype(np.float32), int(saved['frames'])
        except (OSError, ValueError, KeyError):
            self.counts, self.frames = np.zeros((self.H, self.W), np.float32), 0

    def observeFrame(self, frame, towerPositions):
        # Colour, not brightness: a red bloon on green grass barely changes luminance.
        small = cv2.resize(frame, (self.W, self.H), interpolation=cv2.INTER_AREA).astype(np.int16)
        if self.prev is not None:
            changed = (np.abs(small - self.prev).max(axis=2) > 25).astype(np.uint8)
            scale = self.W / frame.shape[1]
            for pos in towerPositions:
                cv2.circle(changed, (int(pos[0] * scale), int(pos[1] * scale)), 6, 0, -1)
            changed[:, int(1640 * self.W / 1920):] = 0
            changed[:int(90 * self.H / 1080), :] = 0
            if changed.mean() < 0.25:   # whole-screen changes (menus, flashes) aren't bloons
                self.counts += changed
                self.frames += 1
                self.unsaved += 1
                self._mask = None
                if self.unsaved >= 60:
                    self.save()
        self.prev = small

    def save(self):
        try:
            os.makedirs(KNOWN_SPOTS_DIR, exist_ok=True)
            np.savez(self.path, counts=self.counts, frames=self.frames)
            self.unsaved = 0
        except OSError:
            pass

    def ready(self):
        return self.frames >= 400 and float(self.counts.max()) > 0

    def pathMask(self):
        if self._mask is None:
            rate = self.counts / max(1, self.frames)
            self._mask = rate >= max(0.02, 0.3 * float(rate.max()))
        return self._mask

    def coverage(self, pos, rangePx, frameWidth):
        """Path cells inside a tower's range circle at pos."""
        if rangePx is None or not self.ready():
            return None
        scale = self.W / frameWidth
        x, y, r = pos[0] * scale, pos[1] * scale, rangePx * scale
        ys, xs = np.ogrid[:self.H, :self.W]
        inside = (xs - x) ** 2 + (ys - y) ** 2 <= r * r
        return int(np.count_nonzero(self.pathMask() & inside))


class TowerTracker:
    """Towers on moving map parts (Sanctuary's rotating ring, Geared's gears) ride along, so
    their recorded click point goes stale. Keep the area around each tower as it was when
    placed; later, match features between then and now to recover the local rotation/shift
    of its platform and move the tower's click point with it."""

    def __init__(self):
        self.refs = {}
        self.orb = cv2.ORB_create(nfeatures=600)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def remember(self, name, frame, pos):
        self.refs[str(name)] = (cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (int(pos[0]), int(pos[1])),
                                self.platformMask(frame, pos))

    @staticmethod
    def platformMask(frame, pos):
        """The surface the tower stands on (a moving stone, gear, platform): flood-fill similar
        colour outward from points just around the tower sprite. None if it isn't a bounded
        surface (open ground), in which case the whole window is used."""
        h, w = frame.shape[:2]
        scale = w / 1920
        blurred = cv2.GaussianBlur(frame, (7, 7), 0)
        mask = np.zeros((h + 2, w + 2), np.uint8)
        for angle in range(0, 360, 45):
            sx = int(pos[0] + 34 * scale * math.cos(math.radians(angle)))
            sy = int(pos[1] + 34 * scale * math.sin(math.radians(angle)))
            if 0 <= sx < w and 0 <= sy < h and not mask[sy + 1, sx + 1]:
                cv2.floodFill(blurred.copy(), mask, (sx, sy), 0, (14, 14, 14), (14, 14, 14),
                              cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8))
        region = mask[1:-1, 1:-1]
        area = int(np.count_nonzero(region))
        if area < 1500 * scale * scale or area > 0.12 * w * h:
            return None
        return region

    def locate(self, name, frame):
        ref = self.refs.get(str(name))
        if ref is None:
            return None
        refGray, (px, py), platform = ref
        curGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if curGray.shape != refGray.shape:
            return None
        h, w = curGray.shape
        radius = int(260 * w / 1920)
        x0, y0, x1, y1 = max(0, px - radius), max(0, py - radius), min(w, px + radius), min(h, py + radius)
        # Features only on the tower's own platform when one was found: the static background,
        # vines and bloons in the window otherwise outvote the stone that actually moved.
        mask = platform[y0:y1, x0:x1].copy() if platform is not None else np.full((y1 - y0, x1 - x0), 255, np.uint8)
        if platform is not None:
            mask = cv2.dilate(mask, np.ones((9, 9), np.uint8))
        cv2.circle(mask, (px - x0, py - y0), int(36 * w / 1920), 0, -1)   # the tower itself turns to aim
        kp1, d1 = self.orb.detectAndCompute(refGray[y0:y1, x0:x1], mask)
        kp2, d2 = self.orb.detectAndCompute(curGray[y0:y1, x0:x1], None)
        if d1 is None or d2 is None or len(kp1) < 8 or len(kp2) < 12:
            return None
        matches = self.matcher.match(d1, d2)
        if len(matches) < 12:
            return None
        src = np.float32([kp1[m.queryIdx].pt for m in matches])
        dst = np.float32([kp2[m.trainIdx].pt for m in matches])
        M, inliers = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=4.0)
        if M is None or inliers is None or int(inliers.sum()) < 8:
            return None
        if not 0.92 < math.hypot(M[0, 0], M[1, 0]) < 1.08:   # platforms rotate/shift; they don't resize
            return None
        local = np.array([px - x0, py - y0, 1.0])
        nx, ny = M @ local
        return (int(nx + x0), int(ny + y0)), int(inliers.sum())


# With BTD6's placement confirmation on, a placement click only positions the tower: a green
# check (and red X) appears top-right and the tower is bought only when the check is pressed.
CONFIRM_BUTTON_1080 = (1600, 205)
_confirmButton1080 = CONFIRM_BUTTON_1080


def confirmButtonVisible(frame):
    global _confirmButton1080
    h, w = frame.shape[:2]
    s = w / 1920
    # Bottom-right green Play + red nudge controls are NOT purchase confirmation.
    # A false match there starts rounds with an unplaced ghost. Only recognize
    # the outlined check button beside the playfield, with its white check mark.
    def colorFraction(rect, green):
        x1, y1, x2, y2 = rect
        crop = frame[int(y1 * s):int(y2 * s), int(x1 * s):int(x2 * s)].astype(np.int32)
        if not crop.size:
            return 0.0
        b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
        pixels = ((g > 120) & (g > r * 1.35) & (g > b * 1.3)) if green else ((r > 140) & (r > g * 1.4) & (r > b * 1.4))
        return float(pixels.mean())
    def hasCheck(rect):
        x1, y1, x2, y2 = rect
        crop = frame[int(y1 * s):int(y2 * s), int(x1 * s):int(x2 * s)].astype(np.int32)
        if not crop.size:
            return False
        white = np.all(crop > 220, axis=2)
        return colorFraction(rect, True) > 0.25 and float(white.mean()) > 0.10
    if (hasCheck((1570, 12, 1630, 76))
            and colorFraction((1567, 85, 1632, 153), False) > 0.15):
        _confirmButton1080 = (1600, 44)
        return True
    crop = frame[int(183 * s):int(228 * s), int(1578 * s):int(1623 * s)].astype(np.int32)
    if crop.size == 0:
        return False
    b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
    visible = hasCheck((1578, 183, 1623, 228))
    if visible:
        _confirmButton1080 = CONFIRM_BUTTON_1080
    return visible


def confirmButtonPos(frameWidth):
    s = frameWidth / 1920
    return (int(_confirmButton1080[0] * s), int(_confirmButton1080[1] * s))


def isDynamicPlacementMap(mapName):
    key = str(mapName or '').lower().replace(' ', '').replace("'", '').replace('_', '')
    return key in DYNAMIC_PLACEMENT_MAPS or os.environ.get('BLOONS_DYNAMIC_PLACEMENT') == '1'


def hasMovingTowerPlatforms(mapName):
    """Changing access, water or lanes does not mean tower coordinates move."""
    key = str(mapName or '').lower().replace(' ', '').replace("'", '').replace('_', '')
    return key in {'geared', 'sanctuary'} or os.environ.get('BLOONS_MOVING_PLATFORMS') == '1'

def heroSelectionState():
    """Read the hero title and the button state instead of a skin check badge."""
    screenshot = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
    encoded, png = cv2.imencode('.png', screenshot)
    if not encoded:
        return {}
    try:
        result = subprocess.run([os.environ.get('BLOONS_NODE', 'node'), '../tools/read-hero-selection.js'], input=png.tobytes(),
                                capture_output=True, timeout=30)
    except FileNotFoundError:
        # Optional OCR helper is not bundled in VM runtime. Empty state keeps
        # hero selection deterministic: click configured card, then Select.
        customPrint('hero OCR unavailable (node missing); using configured hero and Select fallback')
        return {}
    if result.returncode:
        print('DEBUG hero OCR failed:', result.stderr.decode('utf-8', errors='replace').strip(), flush=True)
        return {}
    try:
        state = json.loads(result.stdout)
        print('DEBUG hero OCR:', state, flush=True)
        return state
    except ValueError:
        return {}


def heroAlreadySelected(hero, state):
    from difflib import SequenceMatcher
    expected = ''.join(character for character in hero.lower() if character.isalpha())
    shown = state.get('title', '')
    # The hero title artwork is stylized enough that the bundled OCR model
    # produces stable, but imperfect, readings. Keep narrow readings observed
    # from the live picker rather than accepting arbitrary short text. This is
    # also independent of portrait order, which BTD6 changes as heroes arrive.
    shortAliases = {
        'quincy': {'quincy', 'uingy'},
        'gwendolin': {'gwendolin', 'swendbool'},
        'strikerjones': {'strikerjones', 'trikern'},
        'benjamin': {'benjamin', 'enyaii'},
        'silas': {'silas', 'ias'},
        'ezili': {'ezili', 'zil'},
        'rosalia': {'rosalia', 'osasa'},
        'etienne': {'etienne', 'tienne'},
        'sauda': {'sauda', 'auda'},
        'psi': {'psi', 'psl'},
    }
    firstName = hero.lower().split('_')[0]
    candidates = [shown] + (state.get('titleCandidates') if isinstance(state.get('titleCandidates'), list) else [])
    titleMatches = any(isinstance(title, str) and bool(title) and
                       (title in shortAliases.get(expected, set())
                        or expected in title or (len(firstName) >= 5 and firstName in title)
                        or SequenceMatcher(None, expected, title).ratio() >= 0.72)
                       for title in candidates)
    return titleMatches and 'selected' in state.get('button', '')


def findHeroCard(hero):
    """Try a verified layout hint, then search by the live displayed hero title."""
    from hero_picker_memory import read_memory, lookup_hint
    resolution = tuple(pyautogui.size())
    height = resolution[1]
    slots = sorted({tuple(pos) for pos in imageAreas['click']['hero_positions'].values()
                    # The live picker has three columns in the left quarter. Older
                    # Geraldo/Corvus entries point into the hero detail panel;
                    # those clicks do not select a card and repeat stale OCR.
                    if 0 < pos[0] < resolution[0] / 4 and 70 < pos[1] < height - 55},
                   key=lambda pos: (pos[1], pos[0]))
    if not slots:
        return {}
    def top():
        pyautogui.moveTo(slots[0][0], height // 2)
        pyautogui.scroll(20)
        sendKey('{WheelUp 20}')
        time.sleep(menuChangeDelay)
    def nextPage():
        pyautogui.moveTo(slots[0][0], height // 2)
        pyautogui.scroll(-4)
        sendKey('{WheelDown 6}')
        time.sleep(menuChangeDelay)
    pageTitles = []
    def readCard(page, slot):
        pyautogui.click(slot)
        time.sleep(0.18)
        candidate = heroSelectionState()
        pageTitles.append(candidate.get('title', ''))
        if heroAlreadySelected(hero, {**candidate, 'button': 'selected'}):
            candidate['pickerHint'] = {'page': page, 'position': list(slot),
                'resolution': list(resolution), 'slots': [list(point) for point in slots]}
            return candidate
        return None
    top()
    hint = lookup_hint(read_memory(LAST_HERO_FILE), hero, resolution, slots)
    if hint:
        for _ in range(hint['page']):
            nextPage()
        candidate = readCard(hint['page'], tuple(hint['position']))
        if candidate is not None:
            customPrint('HERO_PICKER layout hint verified live for ' + hero)
            return candidate
        customPrint('HERO_PICKER layout hint mismatched; searching live cards for ' + hero)
        top()
    for page in range(5):
        pageTitles.clear()
        for slot in slots:
            candidate = readCard(page, slot)
            if candidate is not None:
                customPrint('DEBUG hero ' + hero + ' found visually on page ' + str(page) + ' at ' + str(slot))
                return candidate
        if len(pageTitles) > 1 and all(pageTitles) and len(set(pageTitles)) == 1:
            customPrint('HERO_PICKER search stopped: every card returned the same title on page '
                        + str(page) + ': ' + str(pageTitles[0]))
            break
        nextPage()
    return {}


def resolveRouteHero(mapConfig):
    """Resolve the hero from the route's recorded placement instructions."""
    configured = mapConfig.get('hero')
    for step in mapConfig.get('steps', []):
        if step.get('action') != 'place' or step.get('type') != 'hero':
            continue
        extra = step.get('extra') or {}
        candidate = extra.get('type') or step.get('hero')
        if candidate in towers['heros']:
            if candidate != configured:
                customPrint('DEBUG route hero overrides config: ' + str(configured) + ' -> ' + str(candidate))
            return candidate
    if configured in towers['heros']:
        return configured
    return 'sauda'


def savedHeroMatchesRoute(mapConfig):
    """Use Steam Profile.Save's equipped hero to avoid reopening menus when already correct."""
    active = ''.join(character for character in os.environ.get('BLOONS_ACTIVE_HERO', '').lower() if character.isalpha())
    target = ''.join(character for character in resolveRouteHero(mapConfig).lower() if character.isalpha())
    return bool(active and target and active == target)

def waitForMenuScreen(expected, comparisonImages, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
        if recognizeScreen(current, comparisonImages) == expected:
            return True
        time.sleep(0.2)
    return False


def verifyVisibleMapTile(mapConfig):
    """Use the visible map labels to reject stale page/slot coordinates before clicking."""
    expectedName = maps[mapConfig['map']]['name']
    targetPage = None
    try:
        with open('../data/config/map-order.json', encoding='utf-8') as fp:
            order = json.load(fp)
        normalized = ''.join(ch for ch in expectedName.lower() if ch.isalnum())
        targetPage = order.get('maps', {}).get(normalized, {}).get('globalPage')
    except (OSError, ValueError):
        pass
    width, height = pyautogui.size()
    nextPage = (round(2195 * width / 2560), round(576 * height / 1440))
    for attempt in range(8):
        screenshot = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
        encoded, png = cv2.imencode('.png', screenshot)
        if not encoded:
            return False
        try:
            result = subprocess.run(
                [os.environ.get('BLOONS_NODE', 'node'), '../tools/verify-map-page.js', expectedName, mapConfig['category'],
                 str(mapConfig['page']), str(mapConfig['pos'])],
                input=png.tobytes(), capture_output=True, timeout=30,
            )
        except FileNotFoundError:
            # A coordinate-only click can start the wrong map after tile-order changes.
            # Fail closed until the packaged runtime includes the verifier.
            customPrint('ERROR map tile verifier unavailable (node missing); refusing an unverified map click')
            return False
        try:
            observed = json.loads(result.stdout)
        except ValueError:
            observed = {}
        if result.returncode == 0 and observed.get('correct'):
            return True
        currentPage = observed.get('page')
        customPrint('map tile check ' + str(attempt + 1) + '/8 targetPage=' +
                    str(targetPage) + ': ' + result.stdout.decode('utf-8', errors='replace'))
        if targetPage is not None and isinstance(currentPage, int) and currentPage < targetPage:
            customPrint('DEBUG visible map page is behind target; advancing via right arrow ' + str(nextPage))
            pyautogui.click(nextPage)
            time.sleep(mapNavDelay)
        elif targetPage is not None and isinstance(currentPage, int) and currentPage > targetPage:
            customPrint('ERROR map navigation overshot target page; stopping before map click')
            return False
        else:
            time.sleep(0.6)
    return False


def selectMapFromSelection(mapConfig, comparisonImages):
    """Navigate from the currently visible map list into the requested mode."""
    if mapConfig['category'] == 'beginner':
        pyautogui.click(imageAreas['click']['map_categories']['advanced'])
        time.sleep(mapNavDelay)
        pyautogui.click(imageAreas['click']['map_categories'][mapConfig['category']])
        time.sleep(mapNavDelay)
    else:
        pyautogui.click(imageAreas['click']['map_categories']['beginner'])
        time.sleep(mapNavDelay)
        pyautogui.click(imageAreas['click']['map_categories'][mapConfig['category']])
        time.sleep(mapNavDelay)
    # The category tab selects a category; repeated clicks do not reliably advance pages.
    width, height = pyautogui.size()
    nextPage = (round(2195 * width / 2560), round(576 * height / 1440))
    for pageNumber in range(mapConfig['page']):
        customPrint('DEBUG advancing ' + mapConfig['category'] + ' map page ' +
                    str(pageNumber) + ' -> ' + str(pageNumber + 1) + ' via right arrow ' + str(nextPage))
        pyautogui.click(nextPage)
        time.sleep(mapNavDelay)
    if not waitForMenuScreen(Screen.MAP_SELECTION, comparisonImages, 2):
        customPrint('map page is not visible after category/page navigation')
        return False
    if not verifyVisibleMapTile(mapConfig):
        customPrint('stopping before map click; page or tile does not match ' + mapConfig['map'])
        return False
    customPrint('DEBUG clicking map=' + mapConfig['map'] + ' category=' + mapConfig['category'] +
                ' page=' + str(mapConfig['page']) + ' slot=' + str(mapConfig['pos']) +
                ' at ' + str(imageAreas['click']['map_positions'][mapConfig['pos']]))
    pyautogui.click(imageAreas['click']['map_positions'][mapConfig['pos']])
    if not waitForMenuScreen(Screen.DIFFICULTY_SELECTION, comparisonImages):
        customPrint('map tile did not open difficulty selection')
        return False
    pyautogui.click(imageAreas['click']['gamedifficulty_positions'][mapConfig['difficulty']])
    if not waitForMenuScreen(Screen.GAMEMODE_SELECTION, comparisonImages):
        customPrint('difficulty did not open mode selection')
        return False
    return True

def getResolutionDependentData(resolution = pyautogui.size(), gamemode=''):
    requiredComparisonImages = [{'category': 'screens', 'name': 'startmenu'}, {'category': 'screens', 'name': 'map_selection'}, {'category': 'screens', 'name': 'difficulty_selection'}, {'category': 'screens', 'name': 'gamemode_selection'}, {'category': 'screens', 'name': 'hero_selection'}, {'category': 'screens', 'name': 'ingame'}, {'category': 'screens', 'name': 'ingame_paused'}, {'category': 'screens', 'name': 'victory_summary'}, {'category': 'screens', 'name': 'victory'}, {'category': 'screens', 'name': 'defeat'}, {'category': 'screens', 'name': 'overwrite_save'}, {'category': 'screens', 'name': 'levelup'}, {'category': 'screens', 'name': 'apopalypse_hint'}, {'category': 'screens', 'name': 'insta_granted'}, {'category': 'screens', 'name': 'insta_claimed'}, {'category': 'screens', 'name': 'choose_save_location'}, {'category': 'screens', 'name': 'quit_game_confirm'}, {'category': 'game_state', 'name': 'game_paused'}, {'category': 'game_state', 'name': 'game_playing_slow'}, {'category': 'game_state', 'name': 'game_playing_fast'}]
    optionalComparisonImages = [{'category': 'screens', 'name': 'collection_claim_chest', 'for': [Mode.CHASE_REWARDS.name]},
                                {'category': 'screens', 'name': 'game_error'}]
    requiredLocateImages = [{'name': 'remove_obstacle_confirm_button'}, {'name': 'button_home'}]
    optionalLocateImages = [{'name': 'unknown_insta', 'for': [Mode.CHASE_REWARDS.name]}, {'name': 'unknown_insta_mask', 'for': [Mode.CHASE_REWARDS.name]}]

    imagesDir = 'images/' + getResolutionString(resolution) + '/'

    comparisonImages = {}
    locateImages = {}

    if not exists(imagesDir):
        return None

    supportedModes = dict.fromkeys([e.name for e in Mode], True)

    for img in requiredComparisonImages:
        filename = (img['filename'] if 'filename' in img else img['name']) + '.png'
        if not exists(imagesDir + filename):
            print(filename + ' missing!')
            return None
        elif 'category' in img:
            if not img['category'] in comparisonImages:
                comparisonImages[img['category']] = {}
            comparisonImages[img['category']][img['name']] = cv2.imread(imagesDir + filename)
        else:
            comparisonImages[img['name']] = cv2.imread(imagesDir + filename)
    
    for img in optionalComparisonImages:
        filename = (img['filename'] if 'filename' in img else img['name']) + '.png'
        if not exists(imagesDir + filename):
            if 'for' in img:
                for mode in img['for']:
                    supportedModes.pop(mode, None)
        elif 'category' in img:
            if not img['category'] in comparisonImages:
                comparisonImages[img['category']] = {}
            comparisonImages[img['category']][img['name']] = cv2.imread(imagesDir + filename)
        else:
            comparisonImages[img['name']] = cv2.imread(imagesDir + filename)
    
    for img in requiredLocateImages:
        filename = (img['filename'] if 'filename' in img else img['name']) + '.png'
        if not exists(imagesDir + filename):
            print(filename + ' missing!')
            return None
        elif 'category' in img:
            if not img['category'] in locateImages:
                locateImages[img['category']] = {}
            locateImages[img['category']][img['name']] = cv2.imread(imagesDir + filename)
        else:
            locateImages[img['name']] = cv2.imread(imagesDir + filename)
    
    for img in optionalLocateImages:
        filename = (img['filename'] if 'filename' in img else img['name']) + '.png'
        if not exists(imagesDir + filename):
            if 'for' in img:
                for mode in img['for']:
                    supportedModes.pop(mode, None)
        elif 'category' in img:
            if not img['category'] in locateImages:
                locateImages[img['category']] = {}
            locateImages[img['category']][img['name']] = cv2.imread(imagesDir + filename)
        else:
            locateImages[img['name']] = cv2.imread(imagesDir + filename)

    locateImages['collection'] = {}
    if exists(imagesDir + 'collection_events'):
        for filename in os.listdir(imagesDir + 'collection_events'):
            locateImages['collection'][filename.replace('.png', '')] = cv2.imread(imagesDir + 'collection_events/' + filename)
    
    return {'comparisonImages': comparisonImages, 'locateImages': locateImages, 'supportedModes': supportedModes, 'resolution': resolution}

class State(Enum):
    UNDEFINED = 0
    IDLE = 1
    INGAME = 2
    GOTO_HOME = 3
    GOTO_INGAME = 4
    SELECT_HERO = 5
    FIND_HARDEST_INCREASED_REWARDS_MAP = 6
    MANAGE_OBJECTIVES = 7
    EXIT = 8

class Mode(Enum):
    ERROR = 0
    SINGLE_MAP = 1
    RANDOM_MAP = 2
    CHASE_REWARDS = 3
    DO_ACHIEVEMENTS = 4
    MISSING_MAPS = 5
    XP_FARMING = 6
    MM_FARMING = 7
    MISSING_STATS = 8
    VALIDATE_PLAYTHROUGHS = 9
    VALIDATE_COSTS = 10

def getGamemodePosition(gamemode):
    while not isinstance(imageAreas["click"]["gamemode_positions"][gamemode], list):
        gamemode = imageAreas["click"]["gamemode_positions"][gamemode]
    return imageAreas["click"]["gamemode_positions"][gamemode]

MEDAL_BADGE_EARNED = 0.2


def logModeBadge(gamemode):
    """Score the earned-medal badge drawn at the top-left of the target mode's icon.

    Earned badges carry a blue/green/purple star (measured 0.34-0.39 of the patch), an icon without
    one ~0.01. The black-border sweep skips a mode whose badge scores above MEDAL_BADGE_EARNED.
    """
    time.sleep(0.6)
    image = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
    scale = image.shape[1] / 2560
    x, y = getGamemodePosition(gamemode)
    # getGamemodePosition already uses imageAreas scaled to this game window.
    # Scale only the badge offset; scaling x/y again samples unrelated map art.
    cx, cy, r = round(x - 93 * scale), round(y - 70 * scale), max(8, round(24 * scale))
    hsv = cv2.cvtColor(image[cy - r:cy + r, cx - r:cx + r], cv2.COLOR_BGR2HSV)
    hue, saturation, value = hsv[..., 0].astype(int) * 2, hsv[..., 1] / 255, hsv[..., 2]
    cool = float(((hue >= 80) & (hue <= 330) & (saturation > 0.45) & (value > 80)).mean())
    customPrint('DEBUG mode badge gamemode=' + gamemode + ' cool=' + str(round(cool, 3)))
    try:
        # Kept so the earned threshold can be checked against what the screen really showed.
        os.makedirs(FAILURE_SHOT_DIR, exist_ok=True)
        pad = round(150 * scale)
        cv2.imwrite(os.path.join(FAILURE_SHOT_DIR, 'badge_' + time.strftime('%Y%m%d-%H%M%S') + '_' + gamemode + '_' + str(round(cool, 2)) + '.png'), image[max(0, cy - pad):cy + pad, max(0, cx - pad):cx + pad])
    except Exception as error:
        customPrint('WARNING could not save badge crop: ' + str(error))
    return cool

def getNextNonSellAction(steps):
    for step in steps:
        if step['action'] not in ('sell', 'await_round', 'await_cash'):
            return step
    return {'action': 'nop', 'cost': 0}

def getNextCostingAction(steps):
    for step in steps:
        if step.get('cost', 0) > 0:
            return step
    return {'action': 'nop', 'cost': 0}

def sumAdjacentSells(steps):
    gain = 0
    for step in steps:
        if step['action'] != 'sell':
            return gain
        gain += -step.get('cost', 0)
    return gain

exitAfterGame = False

FAILURE_SHOT_DIR = 'failure-shots'
FAILURE_SHOTS_KEPT = 60


def saveFailureShots(mapConfig, ingame, defeat):
    """Keep the last in-game frame (towers still visible) and the defeat screen for route fixing."""
    try:
        os.makedirs(FAILURE_SHOT_DIR, exist_ok=True)
        stem = os.path.join(FAILURE_SHOT_DIR, time.strftime('%Y%m%d-%H%M%S') + '_' + str(mapConfig.get('map')) + '_' + str(mapConfig.get('gamemode')))
        saved = []
        for suffix, frame in (('_ingame.png', ingame), ('_defeat.png', defeat)):
            if frame is None:
                continue
            path = stem + suffix
            if cv2.imwrite(path, frame) and os.path.isfile(path) and os.path.getsize(path) > 0:
                saved.append(path)
            else:
                customPrint('WARNING could not save failure screenshot: image write failed at ' + os.path.abspath(path))
        if saved:
            customPrint('FAILURE_SHOT ' + os.path.abspath(saved[0]))
        # Oldest first by file time: a name sort put dated shots ("2026...") ahead of the
        # "badge_"/"gamemode_stuck_" ones and deleted every new defeat screenshot instantly.
        # Rotate image payloads only. Structured failure sidecars are permanent
        # history and must survive subsequent defeats and screenshot rotation.
        rotationTime = time.time()
        justSaved = {os.path.basename(path) for path in saved}
        def retentionOrder(name):
            modified = os.path.getmtime(os.path.join(FAILURE_SHOT_DIR, name))
            # VM clock rollback must not instantly discard the current failure.
            # Future-dated older payloads have no trustworthy ordering; expire
            # them before ordinary timestamps without changing any file times.
            return (name in justSaved, modified if modified <= rotationTime else 0)
        shots = sorted((name for name in os.listdir(FAILURE_SHOT_DIR)
                        if os.path.splitext(name)[1].lower() in ('.png', '.jpg', '.jpeg')
                        and os.path.isfile(os.path.join(FAILURE_SHOT_DIR, name))),
                       key=retentionOrder)
        for old in shots[:max(0, len(shots) - FAILURE_SHOTS_KEPT)]:
            os.remove(os.path.join(FAILURE_SHOT_DIR, old))
    except Exception as error:
        customPrint('WARNING could not save failure screenshots: ' + str(error))


def setExitAfterGame():
    global exitAfterGame
    if not windowed_input.is_game_foreground():
        return
    customPrint("script will stop after finishing the current game!")
    exitAfterGame = True

def signalHandler(signum, frame):
    customPrint('received SIGINT! exiting!')
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signalHandler)
    print('DEBUG BTD6 focus attempt', flush=True)
    if not windowed_input.focus_game():
        print('BTD6 window was found but could not be focused; bring the game to the foreground and retry', flush=True)
        return 2

    data = getResolutionDependentData()

    if not data:
        customPrint('ERROR unsupported resolution or missing reference images; refusing to start replay')
        return 2

    comparisonImages = data['comparisonImages']
    locateImages = data['locateImages']
    supportedModes = data['supportedModes']
    resolution = data['resolution']

    allAvailablePlaythroughs = getAllAvailablePlaythroughs(['own_playthroughs'], considerUserConfig=True)
    allAvailablePlaythroughsList = allPlaythroughsToList(allAvailablePlaythroughs)

    mode = Mode.ERROR
    logStats = True
    isContinue = False
    isResume = False
    routeCheckpoint = None
    routeStepTotal = 0
    repeatObjectives = False
    doAllStepsBeforeStart = False
    listAvailablePlaythroughs = False
    handlePlaythroughValidation = ValidatedPlaythroughs.EXCLUDE_NON_VALIDATED
    usesAllAvailablePlaythroughsList = False

    collectionEvent = None
    valueUnit = ''

    originalObjectives = []
    objectives = []

    categoryRestriction = None
    gamemodeRestriction = None

    argv = np.array(sys.argv)

    parsedArguments = []


    # Additional flags:
    # -ns: disable stats logging
    if len(np.where(argv == '-ns')[0]):
        customPrint('stats logging disabled!')
        parsedArguments.append('-ns')
        logStats = False
    else:
        customPrint('stats logging enabled!')
    # -r: after finishing all objectives the program restarts with the first objective
    if len(np.where(argv == '-r')[0]):
        customPrint('repeating objective indefinitely! cancel with ctrl + c!')
        parsedArguments.append('-r')
        repeatObjectives = True

    # -mk: after finishing all objectives the program restarts with the first objective
    if len(np.where(argv == '-mk')[0]):
        customPrint('including playthroughs with monkey knowledge enabled and adjusting prices according to userconfig.json!')
        parsedArguments.append('-mk')
        setMonkeyKnowledgeStatus(True)
    # -nomk: after finishing all objectives the program restarts with the first objective
    elif len(np.where(argv == '-nomk')[0]):
        customPrint('ignoring playthroughs with monkey knowledge enabled!')
        parsedArguments.append('-nomk')
        setMonkeyKnowledgeStatus(False)
    else:
        customPrint('"-mk" (for monkey knowledge enabled) or "-nomk" (for monkey knowledge disabled) must be specified! exiting!')
        return

    # -l: list all available playthroughs(only works with specific modes)
    if len(np.where(argv == '-l')[0]):
        parsedArguments.append('-l')
        listAvailablePlaythroughs = True

    # -nv: include non validated playthroughs. ignored when mode = validate
    if len(np.where(argv == '-nv')[0]):
        parsedArguments.append('-nv')
        handlePlaythroughValidation = ValidatedPlaythroughs.INCLUDE_ALL


    iArg = 1
    if len(argv) <= iArg:
        customPrint('arguments missing! Usage: py replay.py <mode> <mode arguments...> <flags>')
        return
    # py replay.py file <filename> [continue <(int start)|-> [until (int end)]]
    # replays the specified file
    # if continue is specified it is assumed you are already in game. the script starts with instruction start(0 for first instruction)
    #   if the value for continue equals "-" all instructions are executed before the game is started
    # if until is specified the script only executes instructions until instruction end(start=0, end=1 -> only first instruction is executed)
    # the continue option is mainly for creating/debugging playthroughs
    # -r for indefinite playing only works if continue is not set
    elif argv[iArg] == 'file':
        # run single map, next argument should be the filename
        iAdditionalStart = iArg + 2
        iAdditional = iAdditionalStart
        if len(argv) <= iArg + 1:
            customPrint('requested running a playthrough but no playthrough provided! exiting!')
            return

        parsedArguments.append(argv[iArg + 1])
        instructionOffset = -1
        instructionLast = -1
        gamemode = None

        if len(argv) > iAdditional and argv[iAdditional] in gamemodes:
            gamemode = argv[iAdditional]
            parsedArguments.append(argv[iAdditional])
            iAdditional += 1
        
        if len(argv) > iAdditional + 1 and argv[iAdditional] == 'continue':
            parsedArguments.append(argv[iAdditional])

            isContinue = True

            if str(argv[iAdditional + 1]) == '-':
                instructionOffset = 0
                doAllStepsBeforeStart = True
            elif str(argv[iAdditional + 1]).isdigit():
                instructionOffset = int(argv[iAdditional + 1])
            else:
                customPrint('continue of playthrough requested but no instruction offset provided!')
                return
            customPrint('stats logging disabled!')
            logStats = False
            parsedArguments.append(argv[iAdditional + 1])
            iAdditional += 2

            if len(argv) >= iAdditional + 1 and argv[iAdditional] == 'until':
                if str(argv[iAdditional + 1]).isdigit():
                    instructionLast = int(argv[iAdditional + 1])
                else:
                    customPrint('cutting of instructions for playthrough requested but no index provided!')
                    return
                parsedArguments.append(argv[iAdditional])
                parsedArguments.append(argv[iAdditional + 1])
                iAdditional += 2
        if not parseBTD6InstructionFileName(argv[iArg + 1]):
            customPrint('"' + str(argv[iArg + 1]) + '" can\'t be recognized as a playthrough filename! exiting!')
            return
        elif str(argv[iArg + 1]).count('/') or str(argv[iArg + 1]).count('\\') and exists(argv[iArg + 1]):
            filename = argv[iArg + 1]
        elif exists('own_playthroughs/' + argv[iArg + 1]):
            filename = 'own_playthroughs/' + argv[iArg + 1]
        elif exists('playthroughs/' + argv[iArg + 1]):
            filename = 'playthroughs/' + argv[iArg + 1]
        elif exists('unvalidated_playthroughs/' + argv[iArg + 1]):
            filename = 'unvalidated_playthroughs/' + argv[iArg + 1]
        else:
            customPrint('requested playthrough ' + str(argv[iArg + 1]) + ' not found! exiting!')
            return
        mapConfig = parseBTD6InstructionsFile(filename, gamemode=gamemode)
        # Bonus Monkey!/Bonus Glue Gunner share one free-tower slot. Only remove
        # the listed cost when Profile.Save confirms the matching knowledge and
        # that tower is the first eligible placement in this route.
        knowledgeMode = str(mapConfig.get('gamemode', '')).lower()
        knowledgeAllowed = getMonkeyKnowledgeStatus() and knowledgeMode not in ('chimps', 'clicks')
        bonusMonkeyOwned = os.environ.get('BLOONS_BONUS_MONKEY_FREE') == '1' and knowledgeAllowed
        bonusGlueOwned = os.environ.get('BLOONS_BONUS_GLUE_FREE') == '1' and knowledgeAllowed
        bonusFreeTowerUsed = False
        firstDartMarkedFree = False
        for step in mapConfig.get('steps', []):
            if step.get('action') != 'place':
                continue
            isDartPlacement = (step.get('action') == 'place'
                               and (step.get('type') == 'dart'
                                    or step.get('extra', {}).get('type') == 'dart'
                                    or str(step.get('name', '')).lower().startswith('dart')))
            isGluePlacement = (step.get('type') == 'glue'
                               or step.get('extra', {}).get('type') == 'glue'
                               or str(step.get('name', '')).lower().startswith('glue'))
            if isDartPlacement and not firstDartMarkedFree:
                step.setdefault('extra', {})['firstDartCandidate'] = True
                firstDartMarkedFree = True
                customPrint('DEBUG first-Dart Monkey Knowledge: tower=' + str(step.get('name'))
                            + ' bonusMonkeyOwned=' + str(bonusMonkeyOwned)
                            + ' source=' + os.environ.get('BLOONS_BONUS_MONKEY_SOURCE', 'unknown')
                            + ' routeCost=' + str(step.get('cost')))
            eligibleFreePlacement = ((isDartPlacement and bonusMonkeyOwned)
                                     or (isGluePlacement and bonusGlueOwned))
            if eligibleFreePlacement and not bonusFreeTowerUsed:
                step['cost'] = 0
                step.setdefault('extra', {})['freePlacement'] = True
                bonusFreeTowerUsed = True
                customPrint('DEBUG Profile.Save bonus-tower applied: tower=' + str(step.get('name'))
                            + ' dartKnowledge=' + str(bonusMonkeyOwned)
                            + ' glueKnowledge=' + str(bonusGlueOwned)
                            + ' routeCost=' + str(step.get('cost')))
        routeStepTotal = len(mapConfig['steps'])
        for routeStepIndex, step in enumerate(mapConfig['steps']):
            step['routeStepIndex'] = routeStepIndex

        if len(argv) > iAdditional and argv[iAdditional] == 'resume':
            parsedArguments.append('resume')
            isResume = True
            isContinue = True
            logStats = False
            routeCheckpoint = readRouteCheckpoint()
            digest = hashlib.sha256(open(filename, 'rb').read()).hexdigest()
            if (not routeCheckpoint or (routeCheckpoint.get('status') != 'ready'
                                       and not resumable_round_start(routeCheckpoint))
                or routeCheckpoint.get('routeHash') != digest
                or routeCheckpoint.get('gamemode') != mapConfig['gamemode']
                or routeCheckpoint.get('map') != mapConfig['map']):
                customPrint('resume refused: checkpoint is missing, ambiguous, or belongs to another route')
                return 2
            instructionOffset = routeCheckpoint.get('nextStep')
            if type(instructionOffset) is not int or not 0 <= instructionOffset <= routeStepTotal:
                customPrint('resume refused: invalid checkpoint step')
                return 2
            try:
                mapConfig['steps'] = restore_upgrade_steps(mapConfig['steps'], routeCheckpoint)
                mapConfig['roundStartCompleted'] = routeCheckpoint.get('roundStartCompleted') is True
            except ValueError as error:
                customPrint('resume refused: ' + str(error))
                return 2
            customPrint('resuming ' + mapConfig['map'] + ' ' + mapConfig['gamemode']
                        + ' at route step ' + str(instructionOffset) + '/' + str(routeStepTotal))

        mode = Mode.SINGLE_MAP
        if instructionOffset == -1:
            activeHeroMatches = 'hero' in mapConfig and savedHeroMatchesRoute(mapConfig)
            if activeHeroMatches:
                customPrint('DEBUG Profile.Save equipped hero matches route (' + resolveRouteHero(mapConfig) +
                            '); keeping the current menu screen and skipping hero picker')
            else:
                originalObjectives.append({'type': State.GOTO_HOME})
            if 'hero' in mapConfig and not activeHeroMatches:
                originalObjectives.append({'type': State.SELECT_HERO, 'mapConfig': mapConfig})
                originalObjectives.append({'type': State.GOTO_HOME})
            originalObjectives.append({'type': State.GOTO_INGAME, 'mapConfig': mapConfig})
        elif not isResume:
            if instructionOffset >= len(mapConfig['steps']) or (instructionLast != -1 and instructionOffset >= instructionLast):
                customPrint('instruction offset > last instruction (' + (str(instructionLast) if instructionLast != -1 else str(len(mapConfig['steps']))) + ')')
                return

            if instructionLast != -1:
                mapConfig['steps'] = mapConfig['steps'][(instructionOffset + mapConfig['extrainstructions']):instructionLast]
            else:
                mapConfig['steps'] = mapConfig['steps'][(instructionOffset + mapConfig['extrainstructions']):]
            customPrint('continuing playthrough. first instruction:')
            customPrint(mapConfig['steps'][0])
        originalObjectives.append({'type': State.INGAME, 'mapConfig': mapConfig})
        originalObjectives.append({'type': State.MANAGE_OBJECTIVES})
    # py replay.py random [category] [gamemode]
    # plays a random game from all available playthroughs (which fullfill the category and gamemode requirement if specified)
    elif argv[iArg] == 'random':
        iAdditional = iArg + 1
        if len(argv) > iAdditional and argv[iAdditional] in mapsByCategory:
            categoryRestriction = argv[iAdditional]
            parsedArguments.append(argv[iAdditional])
            iAdditional += 1
        
        if len(argv) > iAdditional and argv[iAdditional] in gamemodes:
            gamemodeRestriction = argv[iAdditional]
            parsedArguments.append(argv[iAdditional])
            iAdditional += 1
        
        customPrint('Mode: playing random games' + (f' on {gamemodeRestriction}' if gamemodeRestriction else '') + (f' in {categoryRestriction} category' if categoryRestriction else '') + '!')

        allAvailablePlaythroughs = filterAllAvailablePlaythroughs(allAvailablePlaythroughs, getMonkeyKnowledgeStatus(), handlePlaythroughValidation, categoryRestriction, gamemodeRestriction)
        allAvailablePlaythroughsList = allPlaythroughsToList(allAvailablePlaythroughs)

        originalObjectives.append({'type': State.MANAGE_OBJECTIVES})
        mode = Mode.RANDOM_MAP
        usesAllAvailablePlaythroughsList = True
    # py replay.py chase <event> [category] [gamemode]
    # chases increased rewards for the specified event
    # if category is not provided it finds the map with increased rewards in expert category and plays the most valuable available playthrough and downgrades category if no playthrough is available
    # use -r to farm indefinitely
    elif argv[iArg] == 'chase':
        if len(argv) <= iArg + 1 or not argv[iArg + 1] in locateImages['collection']:
            customPrint('requested chasing event rewards but no event specified or unknown event! exiting!')
            return
        
        collectionEvent = argv[iArg + 1]
        parsedArguments.append(argv[iArg + 1])

        iAdditional = iArg + 2
        if len(argv) > iAdditional and argv[iAdditional] in mapsByCategory:
            categoryRestriction = argv[iAdditional]
            parsedArguments.append(argv[iAdditional])
            iAdditional += 1
        
        if len(argv) > iAdditional and argv[iAdditional] in gamemodes:
            gamemodeRestriction = argv[iAdditional]
            parsedArguments.append(argv[iAdditional])
            iAdditional += 1


        if collectionEvent == 'golden_bloon':
            allAvailablePlaythroughs = filterAllAvailablePlaythroughs(allAvailablePlaythroughs, getMonkeyKnowledgeStatus(), handlePlaythroughValidation, categoryRestriction, gamemodeRestriction, requiredFlags=['gB'])
            customPrint(f'Mode: playing games with golden bloons using special playthroughs' + (f' on {gamemodeRestriction}' if gamemodeRestriction else '') + (f' in {categoryRestriction} category' if categoryRestriction else '') + '!')
        else:
            allAvailablePlaythroughs = filterAllAvailablePlaythroughs(allAvailablePlaythroughs, getMonkeyKnowledgeStatus(), handlePlaythroughValidation, categoryRestriction, gamemodeRestriction)
            customPrint(f'Mode: playing games with increased {collectionEvent} collection event rewards' + (f' on {gamemodeRestriction}' if gamemodeRestriction else '') + (f' in {categoryRestriction} category' if categoryRestriction else '') + '!')
        allAvailablePlaythroughsList = allPlaythroughsToList(allAvailablePlaythroughs)

        originalObjectives.append({'type': State.MANAGE_OBJECTIVES})
        mode = Mode.CHASE_REWARDS
        usesAllAvailablePlaythroughsList = True
    # py replay.py achievements [achievement]
    # plays all achievement related playthroughs
    # if achievement is provided it just plays plays until said achievement is unlocked
    # userconfig.json can be used to specify which achievements have already been unlocked or to document progress(e. g. games won only using primary monkeys)
    # refer to userconfig.example.json for an example
    elif argv[iArg] == 'achievements':
        pass
    # py replay.py missing [category]
    # plays all playthroughs with missing medals
    # if category is not provided from easiest category to hardest
    # if category is provided in said category
    # requires userconfig.json to specify which medals have already been earned
    # unlocking of maps has do be done manually
    elif argv[iArg] == 'missing':
        pass
    # py replay.py xp [int n=1]
    # plays one of the n most efficient(in terms of xp/hour) playthroughs
    # with -r: plays indefinitely
    elif argv[iArg] == 'xp':
        allAvailablePlaythroughsList = sortPlaythroughsByXPGain(allAvailablePlaythroughsList)

        if len(argv) > iArg + 1 and argv[iArg + 1].isdigit():
            allAvailablePlaythroughsList = allAvailablePlaythroughsList[:int(argv[iArg + 1])]
            parsedArguments.append(argv[iArg + 1])
        else:
            allAvailablePlaythroughsList = allAvailablePlaythroughsList[:1]
        
        originalObjectives.append({'type': State.MANAGE_OBJECTIVES})
        mode = Mode.XP_FARMING
        valueUnit = 'XP/h'
        usesAllAvailablePlaythroughsList = True
    # py replay.py mm [int n=1]
    # plays one of the n most efficient(in terms of mm/hour) playthroughs
    # with -r: plays indefinitely
    elif argv[iArg] == 'mm' or argv[iArg] == 'monkey_money':
        allAvailablePlaythroughsList = sortPlaythroughsByMonkeyMoneyGain(allAvailablePlaythroughsList)

        if len(argv) > iArg + 1 and argv[iArg + 1].isdigit():
            allAvailablePlaythroughsList = allAvailablePlaythroughsList[:int(argv[iArg + 1])]
            parsedArguments.append(argv[iArg + 1])
        else:
            allAvailablePlaythroughsList = allAvailablePlaythroughsList[:1]
        
        originalObjectives.append({'type': State.MANAGE_OBJECTIVES})
        mode = Mode.MM_FARMING
        valueUnit = 'MM/h'
        usesAllAvailablePlaythroughsList = True
    # py replay.py validate file <filename>
    # or
    # py replay.py validate all [category]
    elif argv[iArg] == 'validate':
        
        if len(argv) <= iArg + 1:
            customPrint('requested validation but arguments missing!')
            return

        parsedArguments.append(argv[iArg + 1])

        if getMonkeyKnowledgeStatus():
            customPrint('Mode validate only works with monkey knowledge disabled!')
            return

        if argv[iArg + 1] == 'file':
            if len(argv) <= iArg + 2:
                customPrint('no filename provided!')
                return

            if not parseBTD6InstructionFileName(argv[iArg + 2]):
                customPrint('"' + str(argv[iArg + 2]) + '" can\'t be recognized as a playthrough filename! exiting!')
                return
            elif str(argv[iArg + 1]).count('/') or str(argv[iArg + 2]).count('\\') and exists(argv[iArg + 2]):
                filename = argv[iArg + 1]
            elif exists('own_playthroughs/' + argv[iArg + 2]):
                filename = 'own_playthroughs/' + argv[iArg + 2]
            elif exists('playthroughs/' + argv[iArg + 2]):
                filename = 'playthroughs/' + argv[iArg + 2]
            elif exists('unvalidated_playthroughs/' + argv[iArg + 2]):
                filename = 'unvalidated_playthroughs/' + argv[iArg + 2]
            else:
                customPrint('requested playthrough ' + str(argv[iArg + 2]) + ' not found! exiting!')
                return

            parsedArguments.append(argv[iArg + 2])
            
            fileConfig = parseBTD6InstructionFileName(filename)
            allAvailablePlaythroughsList = [{'filename': filename, 'fileConfig': fileConfig, 'gamemode': fileConfig['gamemode'], 'isOriginalGamemode': True}]
        elif argv[iArg + 1] == 'all':
            iAdditional = iArg + 2

            if len(argv) > iAdditional and argv[iAdditional] in mapsByCategory:
                categoryRestriction = argv[iAdditional]
                parsedArguments.append(argv[iAdditional])
                iAdditional += 1

            customPrint('Mode: validating all playthroughs' + (' in ' + categoryRestriction + ' category' if categoryRestriction else '') + '!')

            allAvailablePlaythroughs = filterAllAvailablePlaythroughs(allAvailablePlaythroughs, True, ValidatedPlaythroughs.EXCLUDE_VALIDATED if handlePlaythroughValidation == ValidatedPlaythroughs.INCLUDE_ALL else ValidatedPlaythroughs.INCLUDE_ALL, categoryRestriction, gamemodeRestriction, onlyOriginalGamemodes=True)
            allAvailablePlaythroughsList = allPlaythroughsToList(allAvailablePlaythroughs)

        originalObjectives.append({'type': State.MANAGE_OBJECTIVES})
        usesAllAvailablePlaythroughsList = True
        mode = Mode.VALIDATE_PLAYTHROUGHS
    # py replay.py costs [+heros]
    # determines the base cost and cost of each upgrade for each monkey as well as the base cost for each hero if '+heros' is specified
    elif argv[iArg] == 'costs':
        if getMonkeyKnowledgeStatus():
            customPrint('Mode validate costs only works with monkey knowledge disabled!')
            return

        includeHeros = False

        if len(argv) >= iArg + 2 and argv[iArg + 1] == '+heros':
            includeHeros = True
            parsedArguments.append(argv[iArg + 1])

        customPrint('Mode: validating monkey costs' + (' including heros' if includeHeros else '') + '!')

        allTestPositions = json.load(open('test_positions.json'))
        if getResolutionString() in allTestPositions:
            testPositions = allTestPositions[getResolutionString()]
        else:
            testPositions = json.loads(convertPositionsInString(json.dumps(allTestPositions['2560x1440']), (2560, 1440), pyautogui.size()))

        selectedMap = None
        for mapname in testPositions:
            if getAvailableSandbox(mapname, ['medium_sandbox']):
                selectedMap = mapname
                break
        
        if selectedMap is None:
            customPrint('This mode requires access to medium sandbox for one of the maps in "test_positions.json"!')
            return

        costs = {'monkeys': {}}

        baseMapConfig = {'category': maps[selectedMap]['category'], 'map': selectedMap, 'page': maps[selectedMap]['page'], 'pos': maps[selectedMap]['pos'], 'difficulty': 'medium', 'gamemode': 'medium_sandbox', 'steps': [], 'extrainstructions': 1, 'filename': None}

        monkeySteps = []
        monkeySteps.append({'action': 'click', 'pos': imageAreas['click']['gamemode_deflation_message_confirmation'], 'cost': 0})
        pos = testPositions[selectedMap]
        pos['any'] = pos['land']
        for monkeyType in towers['monkeys']:
            costs['monkeys'][monkeyType] = {'base': 0, 'upgrades': np.zeros((3, 5))}
            for iPath in range(0, 3):
                monkeySteps.append({'action': 'place', 'type': monkeyType, 'name': f"{monkeyType}{iPath}", 'key': keybinds['monkeys'][monkeyType], 'pos': pos[towers['monkeys'][monkeyType]['class']], 'cost': 1, 'extra': {'group': 'monkeys', 'type': monkeyType}})
                for iUpgrade in range(1, 6):
                    monkeySteps.append({'action': 'upgrade', 'name': f"{monkeyType}{iPath}", 'key': keybinds['path'][str(iPath)], 'pos': pos[towers['monkeys'][monkeyType]['class']], 'path': iPath, 'cost': 1, 'extra': {'group': 'monkeys', 'type': monkeyType, 'upgrade': (iPath, iUpgrade)}})
                    if upgradeRequiresConfirmation({'type': monkeyType, 'upgrades': [(iUpgrade if iTmp == iPath else 0) for iTmp in range(0, 3)]}, iPath):
                        monkeySteps.append({'action': 'click', 'name': f"{monkeyType}{iPath}", 'pos': imageAreas['click']['paragon_message_confirmation'], 'cost': 0})
                monkeySteps.append({'action': 'sell', 'name': f"{monkeyType}{iPath}", 'key': keybinds['others']['sell'], 'pos': pos[towers['monkeys'][monkeyType]['class']], 'cost': -1})
        
        monkeyMapConfig = copy.deepcopy(baseMapConfig)
        monkeyMapConfig['steps'] = monkeySteps
        
        originalObjectives.append({'type': State.GOTO_HOME})
        originalObjectives.append({'type': State.GOTO_INGAME, 'mapConfig': monkeyMapConfig})
        originalObjectives.append({'type': State.INGAME, 'mapConfig': monkeyMapConfig})

        if includeHeros:
            costs['heros'] = {}
            
            for hero in towers['heros']:
                costs['heros'][hero] = {'base' : 0}
                heroMapConfig = copy.deepcopy(baseMapConfig)
                heroMapConfig['hero'] = hero
                heroMapConfig['steps'] = [{'action': 'click', 'pos': imageAreas['click']['gamemode_deflation_message_confirmation'], 'cost': 0}, {'action': 'place', 'type': 'hero', 'name': 'hero0', 'key': keybinds['monkeys']['hero'], 'pos': pos[towers['heros'][hero]['class']], 'cost': 1, 'extra': {'group': 'heros', 'type': hero}}]
                originalObjectives.append({'type': State.GOTO_HOME})
                originalObjectives.append({'type': State.SELECT_HERO, 'mapConfig': heroMapConfig})
                originalObjectives.append({'type': State.GOTO_HOME})
                originalObjectives.append({'type': State.GOTO_INGAME, 'mapConfig': heroMapConfig})
                originalObjectives.append({'type': State.INGAME, 'mapConfig': heroMapConfig})

        originalObjectives.append({'type': State.MANAGE_OBJECTIVES})
        usesAllAvailablePlaythroughsList = False
        mode = Mode.VALIDATE_COSTS

    if mode == Mode.ERROR:
        customPrint('invalid arguments! exiting!')
        return

    if not mode.name in supportedModes:
        customPrint('mode not supported due to missing images!')
        return

    parsedArguments.append(argv[0])
    parsedArguments.append(argv[1])

    unparsedArguments = []
    parsedArgumentsTmp = np.array(parsedArguments)
    for arg in sys.argv:
        if len(np.where(parsedArgumentsTmp == arg)[0]):
            parsedArgumentsTmp = np.delete(parsedArgumentsTmp, np.where(parsedArgumentsTmp == arg)[0])
        else:
            unparsedArguments.append(arg)

    if len(unparsedArguments):
        customPrint('unrecognized arguments:')
        customPrint(unparsedArguments)
        customPrint('exiting!')
        return

    if listAvailablePlaythroughs:
        if usesAllAvailablePlaythroughsList:
            customPrint(str(len(allAvailablePlaythroughsList)) + ' playthroughs found:')
            for playthrough in allAvailablePlaythroughsList:
                customPrint(playthrough['filename'] + ': ' + playthrough['fileConfig']['map'] + ' - ' + playthrough['gamemode'] + (' with ' + str(playthrough['value']) + (' ' + valueUnit if len(valueUnit) else '') if 'value' in playthrough else ''))
        else:
            customPrint('Mode doesn\'t qualify for listing all available playthroughs')
        return

    if usesAllAvailablePlaythroughsList and len(allAvailablePlaythroughsList) == 0:
        customPrint('ERROR no playthroughs match the requested mode, resolution, and profile requirements; refusing to start replay')
        return 2

    keyboard.add_hotkey('ctrl+space', setExitAfterGame)

    objectives = copy.deepcopy(originalObjectives)
        
    state = objectives[0]['type']
    lastStateTransitionSuccessful = True
    objectiveFailed = False
    objectiveFailureReason = None
    mapConfig = objectives[0]['mapConfig'] if 'mapConfig' in objectives[0] else None
    # GOTO_INGAME's gamemode click (line ~1516) sometimes needs more than one press to register
    # (animation timing, or a mode-specific confirmation dialog this build doesn't recognize yet).
    # Retry in place a bounded number of times before falling back to a full GOTO_HOME reset, which
    # otherwise repeats forever every ~15-20s until the Node-side watchdog kills the whole process.
    gamemodeClickRetries = 0
    GAMEMODE_CLICK_MAX_RETRIES = 5
    # selectMapFromSelection() failing (page/tile mismatch, category OCR miss, etc.) used to send
    # GOTO_INGAME straight back to GOTO_HOME and let the outer loop re-enter GOTO_INGAME and retry
    # the same navigation forever - each cycle ~30s - until the Node-side 180s stall watchdog finally
    # killed the whole process (e.g. 5 identical cycles wasting 3 minutes on one map). Retry the
    # navigation once in place; if it fails a second time, give up on this route immediately instead
    # of spinning until the external watchdog notices.
    mapSelectionRetries = 0
    MAP_SELECTION_MAX_RETRIES = 1

    gamesPlayed = 0
    victoryRecorded = False
    surplusUpgradeCaps = read_upgrade_caps(os.environ.get('BLOONS_UPGRADE_CAPS', ''))
    customPrint('DEBUG surplus upgrade unlock source=' +
                ('Profile.Save launch snapshot' if surplusUpgradeCaps is not None else 'unavailable; live panel checks'))
    surplusUpgradeAttempts = set()
    surplusUpgradeStopped = False
    surplusBlockedPaths = set()
    startLives = None
    lastLives = None
    pendingLives = None
    pendingLivesFrames = 0
    terrainMotion = None
    lastMotionSampleAt = 0
    # The user may change placement confirmation between runs. A historical flag
    # is not evidence that the current game expects a green check. Discover it
    # from the live post-click control, as normal placement already does below.
    confirmPlacementMode = False
    towerTracker = TowerTracker()
    pathHeat = None
    lastGoodMoney = 0
    lastHudPanelOpen = None
    lastHudRightPanelOpen = None
    pendingMoneySpike = None
    lowLivesFrames = 0
    emergencySpend = False
    lastSurplusWaitCash = None
    lastSurplusWaitRound = None
    lastSurplusWaitAt = 0.0

    lastIterationBalance = -1
    lastIterationRound = -1
    lastIterationScreenshotAreas = []
    lastIterationCost = 0
    iterationBalances = []
    thisIterationAction = None
    lastIterationAction = None
    upgradeRunId = None
    currentGameState = None
    lastGameStatePersist = 0.0

    fast = True

    validationResult = None

    playthroughLog = {}

    lastHeroSelected = None

    increasedRewardsPlaythrough = None

    lastPlaythrough = None
    lastPlaythroughStats = {}

    lastScreen = Screen.UNKNOWN
    lastState = State.UNDEFINED

    unknownScreenHasWaited = False
    ingamePausedResumes = 0
    modeIntroConfirmTried = False
    enteredMatchThisRun = False
    # Screens are matched on tiny pixel patches, so one in-game frame can pass for a menu.
    # Leaving a running game needs the same off-game screen on several frames in a row.
    offGameScreen = None
    offGameFrames = 0
    lastPlayToggleAt = 0
    lastIngameShot = None
    pendingPlacementProbe = None
    unreadableCashFrames = 0
    unreadableRoundFrames = 0
    lastPanelCloseAt = 0
    unreadableRecoveries = 0
    # Explosion particles/projectiles over the cash HUD can make the same misread repeat for several
    # consecutive frames (see the comment above the check below) - it's a known, accepted OCR limit
    # (skippingIteration already handles it safely), but printing it unthrottled every single frame
    # floods the log. Only print a fresh line when the misread value itself changes, or a second has
    # passed, so a real reader can still see it happening without the spam.
    lastCashErrorLogged = None
    lastCashErrorLoggedAt = 0
    observedRound = None
    observedRoundStartedAt = None
    repeatedAbilities = RepeatedAbilities()
    pendingRoundRecovery = None
    pendingRoundRecoveryCount = 0
    lastRejectedRoundSignature = None
    lastRejectedRoundLoggedAt = 0
    # Nearby spots (2560-wide pixels) tried when a placement spent nothing; the first retry is the same spot.
    PLACE_RETRY_OFFSETS = [(0, 0), (40, 0), (-40, 0), (0, 40), (0, -40),
                           (80, 0), (-80, 0), (0, 80), (0, -80),
                           (120, 0), (-120, 0), (0, 120), (0, -120)]
    OFF_GAME_FRAMES_REQUIRED = 4

    def placementVisualCheck(probe, frame):
        """Confirm a no-cash placement from a localized tower-shaped screen change."""
        if not probe or frame is None or frame.ndim != 3:
            return False, {'reason': 'missing-frame-or-probe'}
        height, width = frame.shape[:2]
        x, y = (int(probe['pos'][0]), int(probe['pos'][1]))
        radius = max(30, int(width * 0.021))
        # A clipped crop shifts its measured centre away from the tower point.
        # Edge decorations/animation then look like a placed tower (Infernal x=13).
        # Cashless confirmation requires a complete region around the target;
        # a clipped region provides no evidence that the intended tower exists.
        if x - radius < 0 or x + radius > width or y - radius < 0 or y + radius > height:
            return False, {'reason': 'clipped-placement-region'}
        left, right = max(0, x - radius), min(width, x + radius)
        top, bottom = max(0, y - radius), min(height, y + radius)
        before = probe.get('before')
        after = frame[top:bottom, left:right]
        if before is None or after.size == 0 or before.shape != after.shape:
            return False, {'reason': 'crop-mismatch'}
        gray = cv2.cvtColor(cv2.absdiff(before, after), cv2.COLOR_BGR2GRAY)
        changed = (gray > 28).astype(np.uint8)
        total = int(np.count_nonzero(changed))
        center_y, center_x = changed.shape[0] // 2, changed.shape[1] // 2
        half = max(8, int(radius * 0.48))
        center = changed[max(0, center_y-half):min(changed.shape[0], center_y+half),
                         max(0, center_x-half):min(changed.shape[1], center_x+half)]
        central = int(np.count_nonzero(center))
        ratio = total / max(1, changed.size)
        center_ratio = central / max(1, center.size)
        # A placed monkey changes a dense patch centered on its placement point.
        # Small/low-contrast motion (bloons, water shimmer, cursor movement) won't pass both tests.
        confirmed = total >= 220 and ratio >= 0.055 and central >= 130 and center_ratio >= 0.09
        return confirmed, {'changed': total, 'ratio': round(ratio, 3), 'centerChanged': central,
                           'centerRatio': round(center_ratio, 3)}

    def ghostLooksInvalid(baseline, pos):
        """BTD6 tints a held tower's range circle red over an illegal spot.

        Compares a ring around the cursor (outside the tower sprite, inside typical range)
        against a ghost-free baseline frame. Returns True (red tint), False (neutral tint)
        or None when the frame gives no usable signal.
        """
        frame = np.array(pyautogui.screenshot())[:, :, ::-1]
        if baseline is None or frame.shape != baseline.shape:
            return None
        h, w = frame.shape[:2]
        scale = w / 1920
        x, y = int(pos[0]), int(pos[1])
        ys, xs = np.ogrid[:h, :w]
        dist = np.sqrt((xs - x) ** 2 + (ys - y) ** 2)
        ring = (dist >= 50 * scale) & (dist <= 64 * scale)
        if np.count_nonzero(ring) < 200:
            return None
        delta = frame[ring].astype(np.int16) - baseline[ring].astype(np.int16)
        dB, dG, dR = (float(delta[:, i].mean()) for i in range(3))
        if abs(dR) + abs(dG) + abs(dB) < 6:
            return None
        return (dR - dG) > 18 and (dR - dB) > 10


    def smartPlacementSearch(baseline, origin, mapName, cls, occupied, motion, dynamic, rangePx=None, heat=None,
                             supportPx=None, allies=(), villages=(), allowMoving=False):
        """Rank many candidate spots by how placeable they look (learned per-map terrain model +
        known-legal spots), drop occupied and moving ones, then confirm with the ghost tint in
        that order. Every hover result is learned."""
        h, w = baseline.shape[:2]
        scale = w / 1920
        half = max(12, int(40 * scale))
        known = set(map(tuple, nearestKnownLegalSpots(mapName, cls, origin, w, occupied, limit=12, maxDistance1080=320)))
        candidates = set(known)
        for radius in range(16, 241, 16):
            for i in range(16):
                angle = math.radians(i * 22.5)
                candidates.add((int(origin[0] + radius * scale * math.cos(angle)), int(origin[1] + radius * scale * math.sin(angle))))
        scored = []
        for cand in candidates:
            if not (half <= cand[0] < min(w - half, int(1635 * scale)) and half <= cand[1] < h - half):
                continue
            if any((cand[0] - o[0]) ** 2 + (cand[1] - o[1]) ** 2 < (34 * scale) ** 2 for o in occupied):
                continue
            if motion is not None and not allowMoving and motion.isMoving(cand, w):
                continue
            if knownSpotIsIllegal(mapName, cls, cand, w):
                continue   # the game already refused this spot
            feature = patchFeature(baseline[cand[1] - half:cand[1] + half, cand[0] - half:cand[0] + half])
            prob = predictLegalProbability(mapName, cls, feature)
            prob = 0.5 if prob is None else prob
            if cand in known:
                prob = min(1.0, prob + 0.3)
            dist = math.hypot(cand[0] - origin[0], cand[1] - origin[1]) / (240 * scale)
            scored.append([prob, dist, cand, feature, heat.coverage(cand, rangePx, w) if heat is not None else None])
        # Path coverage: with a learned bloon path, favour spots whose range circle covers the
        # most of it; without one, stay close to the route's own spot (its design covered the path).
        best = max([item[4] for item in scored if item[4] is not None] or [0])
        if best > 0:
            scored = [[prob - 0.4 * dist + 0.9 * (cov / best), cand, feature] for prob, dist, cand, feature, cov in scored
                      if cov is not None and cov >= 0.35 * best]
        else:
            scored = [[prob - 1.2 * dist, cand, feature] for prob, dist, cand, feature, cov in scored]
        # Support towers (village/alchemist) score by allies reached; everything else gets a
        # bonus for sitting inside a placed or planned village's range.
        if supportPx is not None and allies:
            reach = [towersInside(item[1], supportPx, allies) for item in scored]
            most = max(reach or [0])
            if most > 0:
                for item, count in zip(scored, reach):
                    item[0] += 0.8 * count / most
        elif villages:
            villagePx = supportRangePx('village', w)
            for item in scored:
                if any((item[1][0] - v[0]) ** 2 + (item[1][1] - v[1]) ** 2 <= villagePx * villagePx for v in villages):
                    item[0] += 0.3
        scored.sort(key=lambda item: -item[0])
        customPrint('PLACE_SEARCH_DIAGNOSTIC footprint=' + str(cls) + ' origin=' + str(origin)
                    + ' confirm_mode=' + str(confirmPlacementMode) + ' candidates=' + str(len(scored))
                    + ' dynamic=' + str(dynamic) + ' range=' + str(rangePx))
        for priority, cand, feature in scored[:14]:
            pyautogui.moveTo(cand)
            time.sleep(0.08)
            if confirmPlacementMode:
                # The game's own verdict: clicking a legal spot shows the green check.
                pyautogui.click(cand)
                time.sleep(0.2)
                verdict = not confirmButtonVisible(np.array(pyautogui.screenshot())[:, :, ::-1])
            else:
                verdict = ghostLooksInvalid(baseline, cand)
            if verdict is None and not confirmPlacementMode:
                # A legal ghost often shows no tint at all; the old code skipped those and then
                # reported "no legal spot" next to good ground. Try it: a refusal (cash unchanged)
                # marks it illegal and the retry moves on to the next ranked spot.
                return cand, ('known' if cand in known else 'predicted') + ' p=' + str(round(priority, 2)) + ' (untinted, trying)'
            if confirmPlacementMode:
                # The check button is the game's real answer, so it's safe to learn from.
                learnPlacementSample(mapName, cls, feature, verdict is False)
                if verdict is True and not dynamic:
                    recordSpot(mapName, cls, cand, False, w)
            if verdict is False:
                return cand, ('known' if cand in known else 'predicted') + ' p=' + str(round(priority, 2))
        # A source coordinate is only a hover candidate. Different versions and
        # occupied layouts may invalidate it; never add it to confirmed memory.
        # Keep changing terrain and original CHIMPS execution on their existing path.
        if not dynamic and mapConfig.get('gamemode') != 'chimps':
            hints = route_placement_hints('playthroughs', str(mapName), cls)
            tested = {tuple(item[1]) for item in scored[:14]}
            for point, source in sorted(hints, key=lambda item: math.hypot(item[0][0]*scale-origin[0], item[0][1]*scale-origin[1]))[:12]:
                cand = (round(point[0]*scale), round(point[1]*scale))
                if cand in tested or not (half <= cand[0] < min(w-half, int(1635*scale)) and half <= cand[1] < h-half):
                    continue
                if any((cand[0]-o[0])**2 + (cand[1]-o[1])**2 < (34*scale)**2 for o in occupied):
                    continue
                if knownSpotIsIllegal(mapName, cls, cand, w) or motion is not None and motion.isMoving(cand, w):
                    continue
                distance = math.hypot(cand[0]-origin[0], cand[1]-origin[1])
                if distance > 320*scale and (rangePx is not None or supportPx is not None):
                    coverage = heat.coverage(cand, rangePx, w) if heat is not None and rangePx is not None else None
                    if best <= 0 or coverage is None or coverage < .35*best or supportPx is not None:
                        continue
                pyautogui.moveTo(cand)
                time.sleep(.08)
                if confirmPlacementMode:
                    pyautogui.click(cand)
                    time.sleep(.2)
                    verdict = not confirmButtonVisible(np.array(pyautogui.screenshot())[:, :, ::-1])
                else:
                    verdict = ghostLooksInvalid(baseline, cand)
                # Unlike nearby recovery, a distant hint requires positive
                # preview evidence; an unknown tint must not authorize it.
                customPrint('PLACE_HINT_DIAGNOSTIC footprint=' + str(cls) + ' candidate=' + str(cand)
                            + ' verdict=' + str(verdict) + ' confirm_mode=' + str(confirmPlacementMode)
                            + ' source=' + str(source))
                if verdict is False:
                    return cand, 'route hint (unverified source; live preview accepted): ' + source
        if motion is not None and not allowMoving:
            # Mostly-moving maps (Sanctuary's rotating ring): no stable legal spot nearby, so
            # accept moving ground; TowerTracker follows the tower for later upgrades.
            return smartPlacementSearch(baseline, origin, mapName, cls, occupied, motion, dynamic, rangePx, heat,
                                        supportPx, allies, villages, allowMoving=True)
        return None, 'none'

    def recordVictory(screenName):
        """Persist one confirmed win even if BTD6 shows both result screens."""
        nonlocal gamesPlayed, victoryRecorded
        if victoryRecorded:
            customPrint('DEBUG duplicate victory screen ignored screen=' + screenName)
            return
        victoryRecorded = True
        if currentGameState is not None:
            currentGameState.finish('victory')
            saveGameState(currentGameState)
        if logStats:
            lastPlaythroughStats['time'].append(('stop', time.time()))
            lastPlaythroughStats['result'] = PlaythroughResult.WIN
            updateStatsFile(mapConfig['filename'], lastPlaythroughStats)
        gamesPlayed += 1
        filename = mapConfig['filename']
        gamemode = mapConfig['gamemode']
        if filename not in playthroughLog:
            playthroughLog[filename] = {}
        if gamemode not in playthroughLog[filename]:
            playthroughLog[filename][gamemode] = {'attempts': 0, 'wins': 0, 'defeats': 0}
        playthroughLog[filename][gamemode]['attempts'] += 1
        playthroughLog[filename][gamemode]['wins'] += 1
        if routeCheckpoint is not None:
            routeCheckpoint.update(status='victory', pendingAction=None)
            writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
        if not isContinue or isResume:
            updateMedalStatus(mapConfig['map'], gamemode)
        customPrint('VICTORY_CONFIRMED screen=' + screenName + ' map=' + str(mapConfig['map']) +
                    ' mode=' + str(gamemode) + ' round=' + str(lastIterationRound))

    def nextSurplusUpgrade(cash):
        """Choose one affordable, legal next tier from towers already confirmed in this run."""
        if currentGameState is None or not isinstance(cash, int) or cash < 0:
            return None, False
        modeClass = {'primary_only': 'primary', 'military_only': 'military',
                     'magic_monkeys_only': 'magic'}.get(mapConfig.get('gamemode'))
        candidates = []
        anyUntriedLegal = False
        for instance, towerState in currentGameState.towers.items():
            towerType = towerState.get('type')
            catalog = towers.get('monkeys', {}).get(towerType)
            position = towerState.get('position')
            levels = towerState.get('upgrades', [0, 0, 0])
            if not catalog or not isinstance(position, (list, tuple)) or len(position) != 2:
                continue
            if modeClass and catalog.get('type') != modeClass:
                continue
            priceTable = catalog.get('upgrades', [])
            if len(levels) != 3:
                continue
            for path in range(3):
                if not can_upgrade_in_roster(
                        levels, path, towerType, currentGameState.towers,
                        double_cross=(mapConfig.get('gamemode') != 'chimps'
                                      and userHasMonkeyKnowledge('master_double_cross'))):
                    continue
                tier = int(levels[path]) + 1
                if surplusUpgradeCaps is not None and tier > surplusUpgradeCaps.get(towerType, [0, 0, 0])[path]:
                    continue
                if tier > 5 or len(priceTable) <= path or len(priceTable[path]) < tier:
                    continue
                attemptKey = (str(instance), path, tier)
                if attemptKey in surplusUpgradeAttempts or (str(instance), path) in surplusBlockedPaths:
                    continue
                anyUntriedLegal = True
                baseCost = int(priceTable[path][tier - 1])
                try:
                    # Use undiscounted catalog prices with a small cushion: profile Monkey
                    # Knowledge may differ from this route's launch flags.
                    expectedCost = int(adjustPrice(baseCost, mapConfig['difficulty'], mapConfig['gamemode']))
                except Exception:
                    expectedCost = baseCost
                reserve = max(5, int(expectedCost * 0.12))
                if cash < expectedCost + reserve:
                    continue
                expectedTiers = list(levels)
                expectedTiers[path] = tier
                candidates.append((sum(int(value) for value in levels), tier, expectedCost,
                                   str(instance), path, towerType, tuple(position), tuple(expectedTiers)))
        if not anyUntriedLegal:
            return None, True
        if not candidates:
            return None, False
        # Extend the most developed tower first, prioritizing its main/high tier path.
        candidates.sort(key=lambda item: (-item[0], -item[1], item[2], item[3], item[4]))
        _, tier, expectedCost, instance, path, towerType, position, expectedTiers = candidates[0]
        return {
            'action': 'upgrade', 'name': instance, 'path': path,
            'expectedUpgradeTiers': list(expectedTiers),
            'key': keybinds['path'][str(path)], 'pos': position, 'cost': expectedCost,
            'extra': {'group': 'monkeys', 'type': towerType, 'upgrade': (path, tier),
                      'opportunistic': True},
        }, False

    segmentCoordinates = None

    if isResume:
        segmentCoordinates = getIngameOcrSegments(mapConfig)
        resumeImage = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
        resumeScreen = recognizeScreen(resumeImage, comparisonImages)
        if resumeScreen != Screen.INGAME:
            customPrint('resume refused: BTD6 is not on the in-game screen (' + resumeScreen.name + ')')
            return 2
        if not sceneMatches(routeCheckpoint.get('mapScene'), mapSceneSignature(resumeImage)):
            customPrint('resume refused: current playfield does not match the saved map scene')
            return 2
        try:
            x1, y1, x2, y2 = segmentCoordinates['round']
            _, resumeRightPanel = resolve_hud_panels(resumeImage, False, False)
            if resumeRightPanel:
                x1, y1, x2, y2 = [int(value * resumeImage.shape[1] / 960)
                                   for value in (505, 17, 612, 39)]
            resumeRound = int(custom_ocr(resumeImage[y1:y2, x1:x2]).split('/')[0])
        except (ValueError, IndexError, TypeError):
            customPrint('resume refused: current round could not be read')
            return 2
        savedRound = routeCheckpoint.get('round')
        if not isinstance(savedRound, int) or savedRound < 0 or resumeRound < savedRound:
            customPrint('resume refused: current round is behind checkpoint (' + str(savedRound) + ' to ' + str(resumeRound) + ')')
            return 2
        if resumeRound > savedRound + 1:
            customPrint('resume warning: game advanced from round ' + str(savedRound) + ' to ' + str(resumeRound)
                        + ' while app was closed; replay will catch up if the run is still alive')
        upgradeRunId = routeCheckpoint.get('runId') or str(time.time_ns())
        currentGameState = GameState(mapConfig, upgradeRunId)
        try:
            with open(GAME_STATE_FILE, encoding='utf-8') as stateFile:
                savedState = json.load(stateFile)
            if currentGameState.restore_ledger(savedState):
                customPrint('DEBUG resume restored tower/path ledger towers=' + str(len(currentGameState.towers)))
                for event in currentGameState.events:
                    if event.get('type') == 'upgrade' and event.get('status') == 'cash-ambiguous':
                        tower = event.get('tower')
                        path = event.get('path')
                        levels = currentGameState.towers.get(tower, {}).get('upgrades', [0, 0, 0])
                        if isinstance(path, int) and 0 <= path < 3:
                            surplusUpgradeAttempts.add((str(tower), path, int(levels[path]) + 1))
        except (OSError, ValueError, TypeError):
            customPrint('DEBUG resume found no matching persisted tower/path ledger')
        # A checkpoint counter is history, not a fresh screen reading.
        currentGameState.observe(screen=resumeScreen.name)
        repeatedAbilities.restore(routeCheckpoint.get('repeatedAbilities', []), keybinds.get('abilities', {}))
        customPrint('TIMING_RECOVERY restored repeat ability slots=' + str(repeatedAbilities.snapshot()))
        observedRound = resumeRound
        observedRoundStartedAt = time.time()
        if any(step.get('action') == 'await_round' and 'secondsAfterRound' in step and step.get('round') == resumeRound for step in mapConfig['steps']):
            customPrint('TIMING_RECOVERY resumed mid-round; pending offsets use the fresh observed round anchor, not an assumed pre-interruption clock')
        saveGameState(currentGameState)
        routeCheckpoint['runId'] = upgradeRunId
        writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
        customPrint('resume verified in-game screen and round ' + str(resumeRound))

    while True:
        if os.path.exists(PAUSE_FILE):
            customPrint('PAUSED waiting for Bloons+ resume command')
            time.sleep(0.75)
            continue
        screenshot = np.array(pyautogui.screenshot())[:, :, ::-1].copy()

        publishViewerFrame(screenshot)
        screen = recognizeScreen(screenshot, comparisonImages)

        customPrint('DEBUG loop screen=' + screen.name + ' state=' + state.name +
                    ' image=' + str(screenshot.shape[1]) + 'x' + str(screenshot.shape[0]) +
                    ' foreground=' + str(windowed_input.is_game_foreground()))

        if screen != lastScreen:
            customPrint("screen " + screen.name + "!")

        if screen == Screen.GAME_ERROR:
            # BTD6's own exception popup blocks every screen and ignores Esc; the run used to
            # sit on UNKNOWN forever behind it. Dismiss it wherever it appears.
            customPrint('GAME_ERROR popup from BTD6; clicking EXIT to dismiss it')
            pyautogui.click(imageAreas["click"]["screen_game_error_button_exit"])
            time.sleep(menuChangeDelay * 2)
            lastScreen = screen
            continue

        if screen == Screen.BTD6_UNFOCUSED:
            # Windows can give the browser focus while the child process is
            # starting. Re-acquire the game instead of spinning forever.
            focusResult = windowed_input.focus_game()
            customPrint('DEBUG focus recovery result=' + str(focusResult) + ' foreground=' + str(windowed_input.is_game_foreground()))
            time.sleep(0.2)
        # don't do anything when ctrl is pressed: useful for alt + tab / sending SIGINT(ctrl + c) to the script
        elif keyboard.is_pressed('ctrl'):
            pass
        elif state == State.MANAGE_OBJECTIVES:
            customPrint("entered objective management!")
            
            if exitAfterGame:
                state = State.EXIT
                continue
            
            if mode == Mode.VALIDATE_PLAYTHROUGHS:
                if validationResult != None:
                    customPrint('validation result: playthrough ' + lastPlaythrough['filename'] + ' is ' + ('valid' if validationResult else 'invalid') + '!')
                    updatePlaythroughValidationStatus(lastPlaythrough['filename'], validationResult)
                if len(allAvailablePlaythroughsList):
                    playthrough = allAvailablePlaythroughsList.pop(0)
                    customPrint('validation playthrough chosen: ' + playthrough['fileConfig']['map'] + ' on ' + playthrough['gamemode'] + ' (' + playthrough['filename'] + ')')
                    
                    gamemode = getAvailableSandbox(playthrough['fileConfig']['map'])
                    if gamemode:
                        mapConfig = parseBTD6InstructionsFile(playthrough['filename'], gamemode=gamemode)
                        objectives = []
                        objectives.append({'type': State.GOTO_HOME})
                        if 'hero' in mapConfig and lastHeroSelected != mapConfig['hero']:
                            objectives.append({'type': State.SELECT_HERO, 'mapConfig': mapConfig})
                            objectives.append({'type': State.GOTO_HOME})
                        objectives.append({'type': State.GOTO_INGAME, 'mapConfig': mapConfig})
                        objectives.append({'type': State.INGAME, 'mapConfig': mapConfig})
                        objectives.append({'type': State.MANAGE_OBJECTIVES})

                        validationResult = True
                        lastPlaythrough = playthrough
                    else:
                        customPrint('missing sandbox access for ' + playthrough['fileConfig']['map'])
                        objectives = []
                        objectives.append({'type': State.MANAGE_OBJECTIVES})
                else:
                    objectives = []
                    objectives.append({'type': State.EXIT})
            elif mode == Mode.VALIDATE_COSTS:
                oldTowers = copy.deepcopy(towers)
                changes = 0
                for monkeyType in costs['monkeys']:
                    if costs['monkeys'][monkeyType]['base'] and costs['monkeys'][monkeyType]['base'] != oldTowers['monkeys'][monkeyType]['base']:
                        print(f"{monkeyType} base cost: {oldTowers['monkeys'][monkeyType]['base']} -> {int(costs['monkeys'][monkeyType]['base'])}")
                        towers['monkeys'][monkeyType]['base'] = int(costs['monkeys'][monkeyType]['base'])
                        changes += 1
                    for iPath in range(0, 3):
                        for iUpgrade in range(0, 5):
                            if costs['monkeys'][monkeyType]['upgrades'][iPath][iUpgrade] and costs['monkeys'][monkeyType]['upgrades'][iPath][iUpgrade] != oldTowers['monkeys'][monkeyType]['upgrades'][iPath][iUpgrade]:
                                print(f"{monkeyType} path {iPath + 1} upgrade {iUpgrade + 1} cost: {oldTowers['monkeys'][monkeyType]['upgrades'][iPath][iUpgrade]} -> {int(costs['monkeys'][monkeyType]['upgrades'][iPath][iUpgrade])}")
                                towers['monkeys'][monkeyType]['upgrades'][iPath][iUpgrade] = int(costs['monkeys'][monkeyType]['upgrades'][iPath][iUpgrade])
                                changes += 1
                if 'heros' in costs:
                    for hero in costs['heros']:
                        if costs['heros'][hero]['base'] and costs['heros'][hero]['base'] != oldTowers['heros'][hero]['base']:
                            print(f"hero {hero} base cost: {oldTowers['heros'][hero]['base']} -> {int(costs['heros'][hero]['base'])}")
                            towers['heros'][hero]['base'] = int(costs['heros'][hero]['base'])
                            changes += 1

                if changes:
                    print(f"updating \"towers.json\" with {changes} changes!")
                    fp = open('towers_backup.json', "w")
                    fp.write(json.dumps(oldTowers, indent=4))
                    fp.close()
                    fp = open('towers.json', "w")
                    fp.write(json.dumps(towers, indent=4))
                    fp.close()
                else:
                    print(f"no price changes in comparison to \"towers.json\" detected!")
                
                return
            elif repeatObjectives or gamesPlayed == 0:
                if mode == Mode.SINGLE_MAP:
                    objectives = copy.deepcopy(originalObjectives)
                elif mode == Mode.RANDOM_MAP or mode == Mode.XP_FARMING or mode == Mode.MM_FARMING:
                    objectives = []
                    playthrough = random.choice(allAvailablePlaythroughsList)
                    customPrint('random playthrough chosen: ' + playthrough['fileConfig']['map'] + ' on ' + playthrough['gamemode'] + ' (' + playthrough['filename'] + ')')
                    mapConfig = parseBTD6InstructionsFile(playthrough['filename'], gamemode=playthrough['gamemode'])
                    
                    objectives.append({'type': State.GOTO_HOME})
                    if 'hero' in mapConfig and lastHeroSelected != mapConfig['hero']:
                        objectives.append({'type': State.SELECT_HERO, 'mapConfig': mapConfig})
                        objectives.append({'type': State.GOTO_HOME})
                    objectives.append({'type': State.GOTO_INGAME, 'mapConfig': mapConfig})
                    objectives.append({'type': State.INGAME, 'mapConfig': mapConfig})
                    objectives.append({'type': State.MANAGE_OBJECTIVES})
                    lastPlaythrough = playthrough
                elif mode == Mode.CHASE_REWARDS:
                    objectives = []
                    if increasedRewardsPlaythrough:
                        playthrough = increasedRewardsPlaythrough
                        customPrint('highest reward playthrough chosen: ' + playthrough['fileConfig']['map'] + ' on ' + playthrough['gamemode'] + ' (' + playthrough['filename'] + ')')
                        mapConfig = parseBTD6InstructionsFile(playthrough['filename'], gamemode=playthrough['gamemode'])

                        objectives.append({'type': State.GOTO_HOME})
                        if 'hero' in mapConfig and lastHeroSelected != mapConfig['hero']:
                            objectives.append({'type': State.SELECT_HERO, 'mapConfig': mapConfig})
                            objectives.append({'type': State.GOTO_HOME})
                        objectives.append({'type': State.GOTO_INGAME, 'mapConfig': mapConfig})
                        objectives.append({'type': State.INGAME, 'mapConfig': mapConfig})
                        objectives.append({'type': State.MANAGE_OBJECTIVES})
                        increasedRewardsPlaythrough = None
                        lastPlaythrough = playthrough
                    else:
                        objectives.append({'type': State.GOTO_HOME})
                        objectives.append({'type': State.FIND_HARDEST_INCREASED_REWARDS_MAP})
                        objectives.append({'type': State.MANAGE_OBJECTIVES})
                else:
                    objectives = copy.deepcopy(originalObjectives)
            else:
                # Leave the game on the main menu, not the victory screen, so the next run or
                # a medal scan can start from a known screen.
                objectives = [{'type': State.GOTO_HOME}, {'type': State.EXIT}]

            state = objectives[0]['type']
            lastStateTransitionSuccessful = True
            objectiveFailed = False
            objectiveFailureReason = None
        elif state == State.UNDEFINED:
            customPrint("entered state management!")
            if exitAfterGame:
                state = State.EXIT
            if objectiveFailed:
                customPrint('OBJECTIVE_FAILURE step=' + objectives[0]['type'].name + ' screen=' + lastScreen.name +
                            ' reason=' + str(objectiveFailureReason or 'unspecified; inspect preceding ROUTE_FAILURE/ERROR log'))
                if repeatObjectives:
                    state = State.MANAGE_OBJECTIVES
                else:
                    objectives = [{'type': State.GOTO_HOME}, {'type': State.EXIT}]
                    objectiveFailed = False
                    objectiveFailureReason = None
                    state = State.GOTO_HOME
            elif not lastStateTransitionSuccessful:
                state = objectives[0]['type']
                if 'mapConfig' in objectives[0]:
                    mapConfig = objectives[0]['mapConfig']
                lastStateTransitionSuccessful = True
            elif lastStateTransitionSuccessful and len(objectives):
                objectives.pop(0)
                state = objectives[0]['type']
                if 'mapConfig' in objectives[0]:
                    mapConfig = objectives[0]['mapConfig']
            else:
                state = State.EXIT
        elif state == State.IDLE:
            pass
        elif state == State.EXIT:
            customPrint("goal EXIT! exiting!")
            return
        elif state == State.GOTO_HOME:
            if screen == Screen.STARTMENU:
                customPrint("goal GOTO_HOME fullfilled!")
                state = State.UNDEFINED
            elif screen == Screen.UNKNOWN:
                if clickTitleStartIfVisible(screenshot):
                    pass
                elif lastScreen == Screen.UNKNOWN and unknownScreenHasWaited:
                    unknownScreenHasWaited = False
                    sendKey('{Esc}')
                else:
                    unknownScreenHasWaited = True
                    time.sleep(2)
            elif screen == Screen.INGAME:
                sendKey('{Esc}')
            elif screen == Screen.INGAME_PAUSED:
                pyautogui.click(imageAreas["click"]["screen_ingame_paused_button_home"])
            elif screen == Screen.HERO_SELECTION:
                sendKey('{Esc}')
            elif screen == Screen.GAMEMODE_SELECTION:
                sendKey('{Esc}')
            elif screen == Screen.DIFFICULTY_SELECTION:
                sendKey('{Esc}')
            elif screen == Screen.MAP_SELECTION:
                # The guest can drop synthetic Escape events. The visible Back
                # button is a stable game-relative target and uses held input.
                windowed_input.held_click(round(screenshot.shape[1] * 0.04),
                                          round(screenshot.shape[0] * 0.05))
                time.sleep(menuChangeDelay)
            elif screen == Screen.DEFEAT:
                result = cv2.matchTemplate(screenshot, locateImages['button_home'], cv2.TM_SQDIFF_NORMED)
                pyautogui.click(cv2.minMaxLoc(result)[2])
            elif screen == Screen.VICTORY_SUMMARY:
                if routeCheckpoint is not None:
                    routeCheckpoint.update(status='victory', pendingAction=None)
                    writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                pyautogui.click(imageAreas["click"]["screen_victory_summary_button_next"])
            elif screen == Screen.VICTORY:
                # The Home button's vertical position shifts with how many reward rows the
                # victory screen shows (plain cash vs. a newly-earned medal row), so a fixed
                # coordinate drifts off target. Locate it the same way DEFEAT already does.
                result = cv2.matchTemplate(screenshot, locateImages['button_home'], cv2.TM_SQDIFF_NORMED)
                pyautogui.click(cv2.minMaxLoc(result)[2])
            elif screen == Screen.OVERWRITE_SAVE:
                sendKey('{Esc}')
            elif screen == Screen.CHOOSE_SAVE_LOCATION:
                # Steam Cloud offers a choice between the local and cloud save. The local
                # (this-device) save is what every route, medal and progress check in this
                # automation reads and tracks, so always keep it rather than risk desyncing
                # from a cloud save with different unlocks/medals.
                pyautogui.click(imageAreas["click"]["screen_choose_save_location_use_this_device"])
                time.sleep(menuChangeDelay)
            elif screen == Screen.QUIT_GAME_CONFIRM:
                # Pressing Esc on the real main menu (e.g. a stray Esc-based recovery firing
                # while a transient misread called it UNKNOWN) opens this native confirmation
                # instead of doing nothing. Always Cancel - never Quit - so a misfired Esc
                # can't close the game out from under the automation.
                pyautogui.click(imageAreas["click"]["screen_quit_game_confirm_button_cancel"])
                time.sleep(menuChangeDelay)
            elif screen == Screen.LEVELUP:
                pyautogui.click(100, 100)
                time.sleep(menuChangeDelay)
                pyautogui.click(100, 100)
            elif screen == Screen.INSTA_GRANTED:
                pyautogui.click(100, 100)
                time.sleep(menuChangeDelay)
            elif screen == Screen.INSTA_CLAIMED:
                pyautogui.click(imageAreas["click"]["insta_claimed"])
                time.sleep(menuChangeDelay)
            elif screen == Screen.COLLECTION_CLAIM_CHEST:
                pyautogui.click(imageAreas["click"]["collection_claim_chest"])
                time.sleep(menuChangeDelay * 2)
                while True:
                    newScreenshot = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
                    result = [cv2.minMaxLoc(cv2.matchTemplate(newScreenshot, locateImages['unknown_insta'], cv2.TM_SQDIFF_NORMED, mask=locateImages['unknown_insta_mask']))[i] for i in [0,2]]
                    if result[0] < 0.01:
                        pyautogui.click(result[1])
                        time.sleep(menuChangeDelay * 2)
                        pyautogui.click(result[1])
                        time.sleep(menuChangeDelay * 2)
                    else:
                        break
                pyautogui.click(imageAreas["click"]["collection_claim_chest_done"])
                time.sleep(menuChangeDelay)
                sendKey('{Esc}')
            elif screen == Screen.APOPALYPSE_HINT:
                pyautogui.click(imageAreas["click"]["gamemode_apopalypse_message_confirmation"])
        elif state == State.GOTO_INGAME:
            if screen == Screen.STARTMENU:
                playTarget = imageAreas["click"]["screen_startmenu_button_play"]
                customPrint('DEBUG opening map selector with held Play click at ' + str(playTarget))
                windowed_input.held_click(*playTarget, hold_seconds=0.2)
                if not waitForMenuScreen(Screen.MAP_SELECTION, comparisonImages):
                    customPrint('map selection did not open; returning home')
                    state = State.GOTO_HOME
                    lastStateTransitionSuccessful = False
                    continue
                screen = Screen.MAP_SELECTION
            if screen == Screen.MAP_SELECTION:
                customPrint('DEBUG using visible map-selection screen; no main-menu round trip needed')
                if not selectMapFromSelection(mapConfig, comparisonImages):
                    mapSelectionRetries += 1
                    if mapSelectionRetries > MAP_SELECTION_MAX_RETRIES:
                        customPrint('map-selection navigation failed again after ' + str(mapSelectionRetries) +
                                    ' attempts; giving up on this route instead of retrying further')
                        objectiveFailed = True
                        objectiveFailureReason = 'map-selection navigation did not reach requested map/mode'
                        state = State.GOTO_HOME
                        lastStateTransitionSuccessful = True
                        continue
                    customPrint('map-selection navigation did not reach requested map/mode; returning home to retry once')
                    state = State.GOTO_HOME
                    lastStateTransitionSuccessful = False
                    continue
                badge = logModeBadge(mapConfig['gamemode'])
                # The sweep only plays medals the player lacks; the tile scan can't see every mode, this
                # screen can. A plain single-map run still plays whatever the player picked.
                # When Profile.Save was readable the sweep already knows this medal is missing; the
                # badge pixel check misreads some modes (alternate_bloons_rounds) as earned, which
                # skipped them forever while the save kept resetting them to missing.
                if badge >= MEDAL_BADGE_EARNED and os.environ.get('BLOONS_PARENT_JOB') == 'black-border-sweep' \
                        and os.environ.get('BLOONS_MEDALS_FROM_SAVE') != '1':
                    customPrint('MEDAL_ALREADY_EARNED ' + str(mapConfig['map']) + ' ' + str(mapConfig['gamemode']) + ' badge=' + str(round(badge, 3)))
                    updateMedalStatus(mapConfig['map'], mapConfig['gamemode'])
                    objectives = [{'type': State.GOTO_HOME}, {'type': State.EXIT}]
                    state = State.GOTO_HOME
                    continue
                gamemodeClickRetries = 0
                enteredMatchThisRun = True
                pyautogui.click(getGamemodePosition(mapConfig['gamemode']))
            elif screen == Screen.GAMEMODE_SELECTION:
                gamemodeClickRetries += 1
                if gamemodeClickRetries > GAMEMODE_CLICK_MAX_RETRIES:
                    try:
                        os.makedirs(FAILURE_SHOT_DIR, exist_ok=True)
                        shotPath = os.path.join(FAILURE_SHOT_DIR, 'gamemode_stuck_' + time.strftime('%Y%m%d-%H%M%S') +
                                                 '_' + str(mapConfig.get('gamemode')) + '.png')
                        cv2.imwrite(shotPath, np.array(pyautogui.screenshot())[:, :, ::-1])
                        customPrint('DEBUG saved stuck-gamemode-selection screenshot: ' + shotPath)
                    except Exception as error:
                        customPrint('WARNING could not save gamemode-stuck screenshot: ' + str(error))
                    customPrint('gamemode click for ' + str(mapConfig.get('gamemode')) +
                                ' did not leave GAMEMODE_SELECTION after ' + str(gamemodeClickRetries) +
                                ' attempts; returning home for recovery')
                    state = State.GOTO_HOME
                    lastStateTransitionSuccessful = False
                    continue
                customPrint('DEBUG gamemode click did not advance yet (attempt ' + str(gamemodeClickRetries) +
                            '); retrying click for ' + str(mapConfig.get('gamemode')))
                enteredMatchThisRun = True
                pyautogui.click(getGamemodePosition(mapConfig['gamemode']))
            elif screen == Screen.OVERWRITE_SAVE:
                pyautogui.click(imageAreas["click"]["screen_overwrite_save_button_ok"])
            elif screen == Screen.CHOOSE_SAVE_LOCATION:
                # Same local-vs-cloud save conflict as above; keep the local save the
                # automation has been tracking instead of jumping to an out-of-sync cloud one.
                pyautogui.click(imageAreas["click"]["screen_choose_save_location_use_this_device"])
                time.sleep(menuChangeDelay)
            elif screen == Screen.QUIT_GAME_CONFIRM:
                # Same stray-Esc-on-main-menu prompt as in GOTO_HOME; Cancel and keep going.
                pyautogui.click(imageAreas["click"]["screen_quit_game_confirm_button_cancel"])
                time.sleep(menuChangeDelay)
            elif screen == Screen.APOPALYPSE_HINT:
                pyautogui.click(imageAreas["click"]["gamemode_apopalypse_message_confirmation"])
            elif screen == Screen.INGAME and not enteredMatchThisRun and not isResume and not isContinue:
                # BTD6 was already mid-match when this run started (e.g. the app restarted while a
                # game kept running). That match is not this route's map/mode; playing it could
                # even save a medal for the wrong map. Leave it and navigate properly.
                customPrint('stale match already running before navigation; leaving it before starting ' +
                            str(mapConfig.get('map')) + ' ' + str(mapConfig.get('gamemode')))
                state = State.GOTO_HOME
                lastStateTransitionSuccessful = False
                continue
            elif screen == Screen.INGAME:
                customPrint("goal GOTO_INGAME fullfilled!")
                ingamePausedResumes = 0
                modeIntroConfirmTried = False
                customPrint("game: " + mapConfig['map'] + ' - ' + mapConfig['difficulty'])
                customPrint('DEBUG hotkeys from BTD6 save applied=' + str(gameHotkeysApplied)
                            + ' unbound=' + str(sorted([k for k, v in keybinds['monkeys'].items() if v is None]
                                                       + [o for o in ('sell', 'retarget', 'special') if keybinds['others'].get(o) is None]
                                                       + ['ability' + str(a) for a, v in keybinds.get('abilities', {}).items() if v is None])))
                victoryRecorded = False
                observedRound = None
                observedRoundStartedAt = None
                repeatedAbilities = RepeatedAbilities()
                surplusUpgradeAttempts.clear()
                surplusUpgradeStopped = False
                surplusBlockedPaths.clear()
                startLives = None
                lastLives = None
                pendingLives = None
                pendingLivesFrames = 0
                terrainMotion = TerrainMotion(mapConfig['map']) if isDynamicPlacementMap(mapConfig['map']) else None
                towerTracker = TowerTracker()
                pathHeat = PathHeat(mapConfig['map'])
                lastGoodMoney = 0
                pendingMoneySpike = None
                lowLivesFrames = 0
                emergencySpend = False
                lastSurplusWaitCash = None
                lastSurplusWaitRound = None
                lastSurplusWaitAt = 0.0
                upgradeRunId = str(time.time_ns())
                currentGameState = GameState(mapConfig, upgradeRunId)
                currentGameState.observe(screen=Screen.INGAME.name)
                saveGameState(currentGameState)
                lastGameStatePersist = time.time()
                customPrint('DEBUG upgrade ledger run=' + upgradeRunId + ' map=' + str(mapConfig.get('map')) +
                            ' difficulty=' + str(mapConfig.get('difficulty')) + ' gamemode=' + str(mapConfig.get('gamemode')))
                segmentCoordinates = getIngameOcrSegments(mapConfig)
                if mode == Mode.SINGLE_MAP:
                    routeCheckpoint = {
                        'version': 1, 'status': 'ready', 'filename': os.path.basename(filename),
                        'routeHash': hashlib.sha256(open(filename, 'rb').read()).hexdigest(),
                        'map': mapConfig['map'], 'gamemode': mapConfig['gamemode'],
                        'nextStep': 0, 'totalSteps': routeStepTotal, 'round': None,
                        'runId': upgradeRunId, 'mapScene': mapSceneSignature(screenshot),
                        'parentJob': os.environ.get('BLOONS_PARENT_JOB'),
                    }
                    writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                iterationBalances = []
                if logStats:
                    lastPlaythroughStats = {'gamemode': mapConfig['gamemode'], 'time': [], 'result': PlaythroughResult.UNDEFINED}
                    lastPlaythroughStats['time'].append(('start', time.time()))
                lastIterationBalance = -1
                lastIterationCost = 0
                state = State.UNDEFINED
            elif screen == Screen.INGAME_PAUSED:
                # Reverse/deflation open a mode-intro dialog on first load; the Esc below that
                # dismisses it leaves the match paused. Resume instead of abandoning the map,
                # which used to loop map -> mode -> pause -> home all night.
                ingamePausedResumes += 1
                if ingamePausedResumes > 3:
                    customPrint('match stayed paused after ' + str(ingamePausedResumes - 1) + ' resume attempts; returning home')
                    state = State.GOTO_HOME
                    lastStateTransitionSuccessful = False
                    continue
                customPrint('DEBUG match opened paused (mode intro dialog); resuming attempt ' + str(ingamePausedResumes))
                sendKey('{Esc}')
                time.sleep(menuChangeDelay)
            elif screen == Screen.UNKNOWN:
                # An unrecognized overlay (e.g. an uncatalogued dialog) can otherwise sit here
                # forever until the external stall watchdog gives up. Mode-intro dialogs
                # (reverse, deflation, ...) share the Apopalypse hint's OK button, so try it
                # once before the wait-then-Esc recovery.
                if clickTitleStartIfVisible(screenshot):
                    pass
                elif lastScreen == Screen.UNKNOWN and unknownScreenHasWaited:
                    unknownScreenHasWaited = False
                    if not modeIntroConfirmTried:
                        modeIntroConfirmTried = True
                        customPrint('DEBUG unknown overlay after mode pick; clicking mode-intro OK')
                        pyautogui.click(imageAreas["click"]["gamemode_apopalypse_message_confirmation"])
                        time.sleep(menuChangeDelay)
                    else:
                        sendKey('{Esc}')
                else:
                    unknownScreenHasWaited = True
                    time.sleep(2)
            else:
                customPrint("task GOTO_INGAME, but not in startmenu!")
                state = State.GOTO_HOME
                lastStateTransitionSuccessful = False
        elif state == State.SELECT_HERO:
            if screen == Screen.STARTMENU:
                # A cached hero is only a hint. The game can retain a different
                # selection after an interrupted run, so always verify through
                # the picker before accepting it. When a route does not declare
                # a hero, use Sauda as the safe land based default.
                mapConfig['hero'] = resolveRouteHero(mapConfig)
                customPrint('DEBUG SELECT_HERO target=' + mapConfig['hero'] + ' class=' + str(towers['heros'][mapConfig['hero']].get('class')) + ' cached=' + str(readLastHero()))
                if not any(step.get('action') == 'place' and step.get('type') == 'hero' for step in mapConfig.get('steps', [])):
                    customPrint('DEBUG route has no hero placement; using land fallback sauda')
                customPrint('DEBUG opening hero picker to verify actual in-game selection; cached value is advisory only')
                pyautogui.click(imageAreas["click"]["screen_startmenu_button_hero_selection"])
                time.sleep(menuChangeDelay)
                heroState = heroSelectionState()
                for _ in range(3):
                    if heroState.get('button') in ('selected', 'select'):
                        break
                    time.sleep(0.6)
                    heroState = heroSelectionState()
                if heroAlreadySelected(mapConfig['hero'], heroState):
                    customPrint("hero " + mapConfig['hero'] + " already selected; skipping hero change")
                else:
                    customPrint('DEBUG clicking hero card ' + mapConfig['hero'] + ' at ' + str(imageAreas['click']['hero_positions'][mapConfig['hero']]))
                    pyautogui.click(imageAreas["click"]["hero_positions"][mapConfig['hero']])
                    time.sleep(menuChangeDelay)
                    heroState = heroSelectionState()
                    # Hero artwork and the Select button animate independently;
                    # OCR can catch the panel between those frames. Re-read it
                    # briefly before treating the state as unsafe.
                    for _ in range(3):
                        if heroState.get('button') in ('selected', 'select'):
                            break
                        time.sleep(0.6)
                        heroState = heroSelectionState()
                    titleMatches = heroAlreadySelected(mapConfig['hero'], {**heroState, 'button': 'selected'})
                    if not titleMatches:
                        customPrint('WARNING hero portrait index is stale (' + str(heroState.get('title')) +
                                    '); searching the hero cards for ' + mapConfig['hero'])
                        heroState = findHeroCard(mapConfig['hero'])
                        if not heroAlreadySelected(mapConfig['hero'], {**heroState, 'button': 'selected'}):
                            customPrint('ERROR hero ' + mapConfig['hero'] + ' was not found in the picker')
                            sys.exit(2)
                    if heroState.get('button') == 'selected':
                        customPrint("hero " + mapConfig['hero'] + " already selected; skipping select click")
                    elif heroState.get('button') == 'select':
                        confirmedHero = heroState
                        selectPos = imageAreas["click"]["screen_hero_selection_select_hero"]
                        for selectAttempt in range(3):
                            customPrint('DEBUG clicking hero Select attempt ' + str(selectAttempt + 1) + '/3 at ' + str(selectPos))
                            pyautogui.moveTo(selectPos[0], selectPos[1], duration=0.18)
                            pyautogui.click()
                            time.sleep(menuChangeDelay)
                            confirmedHero = heroSelectionState()
                            if heroAlreadySelected(mapConfig['hero'], confirmedHero):
                                break
                        if not heroAlreadySelected(mapConfig['hero'], confirmedHero):
                            customPrint('ERROR hero selection was not confirmed after 3 Select attempts: ' + str(confirmedHero))
                            sys.exit(2)
                    else:
                        customPrint('ERROR hero Select button is unconfirmed; refusing to enter a run with an unverified hero')
                        sys.exit(2)
                customPrint("goal SELECT_HERO " + mapConfig['hero'] + " fullfilled!")
                lastHeroSelected = mapConfig['hero']
                saveLastHero(mapConfig['hero'], heroState.get('pickerHint'))
                state = State.UNDEFINED
            elif screen == Screen.UNKNOWN:
                pass
            else:
                customPrint("task SELECT_HERO, but not in startmenu!")
                state = State.GOTO_HOME
                lastStateTransitionSuccessful = False
        elif state == State.FIND_HARDEST_INCREASED_REWARDS_MAP:
            if screen == Screen.STARTMENU:
                pyautogui.click(imageAreas["click"]["screen_startmenu_button_play"])
                time.sleep(menuChangeDelay)

                if categoryRestriction:
                    pyautogui.click(imageAreas["click"]["map_categories"][('advanced' if categoryRestriction == 'beginner' else 'beginner')])
                    time.sleep(menuChangeDelay)

                    mapname = None
                    for page in range(0, categoryPages[categoryRestriction]):
                        pyautogui.click(imageAreas["click"]["map_categories"][categoryRestriction])
                        if collectionEvent == 'golden_bloon':
                            time.sleep(4)
                        else:
                            time.sleep(menuChangeDelay)
                        newScreenshot = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
                        result = findImageInImage(newScreenshot, locateImages['collection'][collectionEvent])
                        if result[0] < 0.05:
                            mapname = findMapForPxPos(categoryRestriction, page, result[1])
                            break
                    if not mapname:
                        customPrint('no maps with increased rewards found! exiting!')
                        return
                    customPrint('best map: ' + mapname)
                    increasedRewardsPlaythrough = getHighestValuePlaythrough(allAvailablePlaythroughs, mapname, playthroughLog)
                    if not increasedRewardsPlaythrough:
                        customPrint('no playthroughs for map found! exiting!')
                        return
                else:
                    iTmp = 0
                    for category in reversed(list(mapsByCategory.keys())):
                        if iTmp == 0:
                            pyautogui.click(imageAreas["click"]["map_categories"][('advanced' if category == 'beginner' else 'beginner')])
                            time.sleep(menuChangeDelay)

                        mapname = None
                        for page in range(0, categoryPages[category]):
                            pyautogui.click(imageAreas["click"]["map_categories"][category])
                            if collectionEvent == 'golden_bloon':
                                time.sleep(4)
                            else:
                                time.sleep(menuChangeDelay)
                            newScreenshot = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
                            result = findImageInImage(newScreenshot, locateImages['collection'][collectionEvent])
                            if result[0] < 0.05:
                                mapname = findMapForPxPos(category, page, result[1])
                                break
                        if not mapname:
                            customPrint('no maps with increased rewards found! exiting!')
                            return
                        customPrint('best map in ' + category + ': ' + mapname)
                        increasedRewardsPlaythrough = getHighestValuePlaythrough(allAvailablePlaythroughs, mapname, playthroughLog)
                        if increasedRewardsPlaythrough:
                            break
                        else:
                            customPrint('no playthroughs for map found! searching lower map tiers!')
                        iTmp += 1
                    
                    if not increasedRewardsPlaythrough:
                        customPrint('no available playthrough found! exiting!')
                        return
                state = State.UNDEFINED
            elif screen == Screen.UNKNOWN:
                pass
            else:
                customPrint("task FIND_HARDEST_INCREASED_REWARDS_MAP, but not in startmenu!")
                state = State.GOTO_HOME
                lastStateTransitionSuccessful = False
        elif state == State.INGAME:
            if screen == Screen.INGAME_PAUSED:
                # Tiny template patches can classify a live frame as paused. A
                # single false match followed by Esc creates the pause/nudge
                # loop and prevents placement. Require two consecutive frames.
                if lastScreen == Screen.INGAME_PAUSED:
                    if logStats:
                        lastPlaythroughStats['time'].append(('stop', time.time()))
                    if windowed_input.is_game_foreground():
                        customPrint('DEBUG confirmed paused twice; resuming with Esc')
                        sendKey('{Esc}')
                else:
                    customPrint('DEBUG pause screen unconfirmed; waiting for next frame')
                    time.sleep(0.35)
            elif screen == Screen.UNKNOWN:
                if clickTitleStartIfVisible(screenshot):
                    pass
                elif lastScreen == Screen.UNKNOWN and unknownScreenHasWaited:
                    unknownScreenHasWaited = False
                    sendKey('{Esc}')
                else:
                    unknownScreenHasWaited = True
                    time.sleep(2)
            elif screen == Screen.LEVELUP:
                pyautogui.click(100, 100)
                time.sleep(menuChangeDelay)
                pyautogui.click(100, 100)
            elif screen == Screen.INSTA_GRANTED:
                pyautogui.click(100, 100)
                time.sleep(menuChangeDelay)
            elif screen == Screen.INSTA_CLAIMED:
                pyautogui.click(imageAreas["click"]["insta_claimed"])
                time.sleep(menuChangeDelay)
            elif screen == Screen.VICTORY_SUMMARY:
                recordVictory(screen.name)
                state = State.UNDEFINED
            elif screen == Screen.VICTORY:
                # Depending on the route/result flow this can appear before or after
                # VICTORY_SUMMARY. Treat the actual win banner as confirmation too;
                # recordVictory() guards against counting both screens twice.
                recordVictory(screen.name)
                state = State.UNDEFINED
            elif screen == Screen.DEFEAT:
                saveFailureShots(mapConfig, lastIngameShot, screenshot)
                if routeCheckpoint is not None:
                    routeCheckpoint.update(status='defeat', pendingAction=None)
                    writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                if currentGameState is not None:
                    currentGameState.finish('defeat')
                    saveGameState(currentGameState)
                if logStats:
                    lastPlaythroughStats['time'].append(('stop', time.time()))
                    lastPlaythroughStats['result'] = PlaythroughResult.DEFEAT
                    updateStatsFile(mapConfig['filename'], lastPlaythroughStats)
                objectiveFailed = True
                objectiveFailureReason = 'game displayed defeat screen'
                gamesPlayed += 1
                if not mapConfig['filename'] in playthroughLog:
                    playthroughLog[mapConfig['filename']] = {}
                if not mapConfig['gamemode'] in playthroughLog[mapConfig['filename']]:
                    playthroughLog[mapConfig['filename']][mapConfig['gamemode']] = {'attempts': 0, 'wins': 0, 'defeats': 0}
                playthroughLog[mapConfig['filename']][mapConfig['gamemode']]['attempts'] += 1
                playthroughLog[mapConfig['filename']][mapConfig['gamemode']]['defeats'] += 1
                
                state = State.UNDEFINED
            elif screen == Screen.INGAME:
                lastIngameShot = screenshot
                if lastScreen != screen and logStats:
                    lastPlaythroughStats['time'].append(('start', time.time()))

                # BTD6 shifts lives and cash about half a screen right while a
                # tower detail panel is open. The old single crop read scenery
                # or partial numbers, so choose the HUD position from the panel.
                scale = screenshot.shape[1] / 960
                def brownFraction(x1, y1, x2, y2):
                    crop = screenshot[int(y1 * scale):int(y2 * scale),
                                      int(x1 * scale):int(x2 * scale)]
                    if not crop.size:
                        return 0.0
                    blue, green, red = crop[..., 0], crop[..., 1], crop[..., 2]
                    return float(((red.astype(np.float32) > green.astype(np.float32) * 1.2)
                                  & (green.astype(np.float32) > blue.astype(np.float32) * 1.2)
                                  & (blue < 120)).mean())
                # The map itself can be brown (Tricky Tracks is the clearest
                # example), so comparing two narrow brown strips misclassifies
                # an open tower panel. Every tower detail panel has the large
                # cyan portrait card in this fixed region; use that stable UI
                # surface instead of colours from the playfield.
                portrait = screenshot[int(70 * scale):int(200 * scale),
                                      int(20 * scale):int(200 * scale)]
                if portrait.size:
                    blue, green, red = portrait[..., 0], portrait[..., 1], portrait[..., 2]
                    panelCyan = float(((blue.astype(np.float32) > red.astype(np.float32) * 1.1)
                                       & (green.astype(np.float32) > red.astype(np.float32) * 1.1)
                                       & (blue > 130)).mean())
                    portraitMax = portrait.max(axis=2).astype(np.float32)
                    portraitMin = portrait.min(axis=2).astype(np.float32)
                    panelBrightColor = float(((portraitMax - portraitMin > 30)
                                              & (portraitMax > 150)
                                              & (portrait.mean(axis=2) > 135)).mean())
                else:
                    panelCyan = 0.0
                    panelBrightColor = 0.0
                panelBrown = brownFraction(190, 50, 210, 440)
                mapBrown = brownFraction(235, 50, 255, 440)
                panelHeaderBrown = brownFraction(0, 25, 210, 60)
                hudPanelOpen = panelHeaderBrown > 0.45 and (panelCyan > 0.25 or panelBrightColor > 0.45)
                rightPanelBrown = brownFraction(625, 50, 645, 440)
                rightMapBrown = brownFraction(585, 50, 605, 440)
                hudRightPanelOpen = rightPanelBrown > 0.40 and rightPanelBrown > rightMapBrown + 0.22
                hudPanelOpen, hudRightPanelOpen = resolve_hud_panels(screenshot, hudPanelOpen, hudRightPanelOpen)
                if hudPanelOpen != lastHudPanelOpen or hudRightPanelOpen != lastHudRightPanelOpen:
                    customPrint('DEBUG HUD layout leftPanel=' + str(hudPanelOpen) +
                                ' rightPanel=' + str(hudRightPanelOpen) +
                                ' portraitCyan=' + str(round(panelCyan, 2)) +
                                ' portraitColor=' + str(round(panelBrightColor, 2)) +
                                ' headerBrown=' + str(round(panelHeaderBrown, 2)) +
                                ' edgeBrown=' + str(round(panelBrown, 2)) +
                                ' mapBrown=' + str(round(mapBrown, 2)) +
                                ' rightEdgeBrown=' + str(round(rightPanelBrown, 2)))
                    lastHudPanelOpen = hudPanelOpen
                    lastHudRightPanelOpen = hudRightPanelOpen
                def gameBox(box):
                    return [int(value * scale) for value in box]
                # Derive every frame from the base HUD. A right-to-left panel
                # transition must not retain the previous shifted round crop.
                segmentCoordinates = getIngameOcrSegments(mapConfig)
                if hudPanelOpen:
                    segmentCoordinates['lives'] = gameBox((226, 4, 312, 36))
                    # Crop starts after the currency symbol. The digit-only
                    # model can mistake '$' for 2/5/6/9, adding phantom cash.
                    segmentCoordinates['money'] = gameBox((378, 4, 503, 36))
                else:
                    segmentCoordinates['money'] = gameBox((184, 4, 309, 36))
                if hudRightPanelOpen:
                    # The right upgrade panel pushes the round counter from the
                    # far-right HUD into this central slot. Keep the small
                    # ROUND caption above the digits out of the OCR crop.
                    segmentCoordinates['round'] = gameBox((505, 17, 612, 39))
                images = [
                    screenshot[segmentCoordinates[segment][1]:segmentCoordinates[segment][3], segmentCoordinates[segment][0]:segmentCoordinates[segment][2]] for segment in segmentCoordinates
                ]

                currentValues = {}
                thisIterationCost = 0
                thisIterationAction = None
                routeActionExecuted = False
                playToggleIssued = False
                skippingIteration = False

                # Read the HUD fields independently. A transient OCR failure in the cash box
                # must not throw away a valid round reading (and vice versa), because that can
                # make the route wait forever or issue a late action at the wrong round.
                try:
                    currentValues['money'] = cash_ocr(images[2], resolution=(screenshot.shape[1], screenshot.shape[0]))
                except (TypeError, ValueError):
                    currentValues['money'] = -1
                try:
                    rawRound = custom_ocr(images[3])
                    currentValues['round'] = int(rawRound.split('/')[0])
                except (AttributeError, TypeError, ValueError):
                    currentValues['round'] = -1
                    rawRound = ''

                # OCR can concatenate the round label/slash into the numerator (6 -> 46
                # or 76). A replay cannot jump dozens of rounds between captures. Reject
                # these values before they update the ledger or release await_round steps.
                readingRound = currentValues['round']
                startRound = 31 if mapConfig.get('gamemode') == 'deflation' else (6 if mapConfig.get('gamemode') in ('chimps', 'impoppable') else (3 if mapConfig.get('difficulty') == 'hard' else 1))
                anchorRound = observedRound if observedRound is not None else startRound
                if readingRound >= 0 and not anchorRound <= readingRound <= anchorRound + 3:
                    # A long occlusion can span several real rounds. Recover only
                    # from repeated full counter reads, never a bare phantom digit.
                    elapsed = time.time() - observedRoundStartedAt if observedRoundStartedAt else 0
                    eligible = round_recovery_candidate(rawRound, anchorRound, elapsed)
                    # Live rounds keep advancing while OCR is occluded. Requiring
                    # three *identical* frames can never recover on a fast run;
                    # accept a short monotonic sequence of complete HUD reads.
                    priorRound = pendingRoundRecovery[0] if pendingRoundRecovery else None
                    priorLimit = pendingRoundRecovery[1] if pendingRoundRecovery else None
                    parts = rawRound.split('/') if eligible else []
                    newLimit = int(parts[1]) if len(parts) == 2 else None
                    followsPrior = (priorRound is not None and priorLimit == newLimit
                                    and priorRound <= readingRound <= priorRound + 2)
                    pendingRoundRecoveryCount = (pendingRoundRecoveryCount + 1 if eligible and followsPrior
                                                 else (1 if eligible else 0))
                    pendingRoundRecovery = (readingRound, newLimit) if eligible else None
                    rejectedSignature = (readingRound, anchorRound)
                    now = time.time()
                    if rejectedSignature != lastRejectedRoundSignature or now - lastRejectedRoundLoggedAt >= 8:
                        customPrint('WARNING rejecting implausible round OCR ' + str(readingRound)
                                    + ' after ' + str(anchorRound))
                        lastRejectedRoundSignature = rejectedSignature
                        lastRejectedRoundLoggedAt = now
                    if pendingRoundRecoveryCount >= 3:
                        customPrint('WARNING round counter resynchronized after HUD occlusion: ' + rawRound)
                        pendingRoundRecoveryCount = 0
                    else:
                        currentValues['round'] = -1
                else:
                    pendingRoundRecovery = None
                    pendingRoundRecoveryCount = 0
                    lastRejectedRoundSignature = None
                if currentValues['round'] == -1:
                    # A slightly stricter white threshold recovers glyph edges on snowy
                    # maps. Accept it only if it also follows the known round sequence.
                    try:
                        alternateRound = int(custom_ocr(images[3], white_threshold=230).split('/')[0])
                        if anchorRound <= alternateRound <= anchorRound + 3:
                            currentValues['round'] = alternateRound
                            customPrint('DEBUG round OCR recovered at threshold 230: ' + str(alternateRound))
                    except (AttributeError, TypeError, ValueError):
                        pass
                # Never manufacture a balance by removing or replacing digits.
                # The cash crop excludes the currency glyph; implausible openings
                # get an independent mask read of the same frame instead.
                openingCashLimit = 100000 if mapConfig.get('gamemode') == 'deflation' else 10000
                if lastGoodMoney == 0 and currentValues['money'] > openingCashLimit:
                    try:
                        stricterCash = int(custom_ocr(images[2], white_threshold=242))
                    except (TypeError, ValueError):
                        stricterCash = -1
                    if 0 <= stricterCash <= openingCashLimit:
                        customPrint('DEBUG corrected opening cash OCR ' + str(currentValues['money'])
                                    + ' -> ' + str(stricterCash) + ' at threshold 242')
                        currentValues['money'] = stricterCash
                    else:
                        customPrint('WARNING rejecting implausible opening cash OCR ' + str(currentValues['money']))
                        currentValues['money'] = -1

                # OCR sometimes inserts a digit (45628 -> 452506). A lone jump to several times the
                # last good reading is treated as unreadable unless the next frame repeats it.
                if currentValues['money'] > 0 and lastGoodMoney > 0 and currentValues['money'] > max(4 * lastGoodMoney, lastGoodMoney + 20000):
                    if pendingMoneySpike == currentValues['money']:
                        lastGoodMoney = currentValues['money']
                    else:
                        pendingMoneySpike = currentValues['money']
                        currentValues['money'] = -1
                elif currentValues['money'] >= 0:
                    lastGoodMoney = currentValues['money']
                    pendingMoneySpike = None
                try:
                    livesReading = int(custom_ocr(images[0]).split('/')[0])
                except ValueError:
                    livesReading = -1
                customPrint('DEBUG OCR values money=' + str(currentValues['money']) + ' round=' + str(currentValues['round'])
                            + ' lives=' + str(livesReading))
                if terrainMotion is not None and time.time() - lastMotionSampleAt >= 4:
                    lastMotionSampleAt = time.time()
                    terrainMotion.observe(screenshot, [tuple(t.get('position')) for t in (currentGameState.towers.values() if currentGameState else [])
                                                       if isinstance(t.get('position'), (list, tuple)) and len(t.get('position')) == 2])
                if pathHeat is not None and currentValues['round'] >= 0:
                    pathHeat.observeFrame(screenshot, [tuple(t.get('position')) for t in (currentGameState.towers.values() if currentGameState else [])
                                                       if isinstance(t.get('position'), (list, tuple)) and len(t.get('position')) == 2])
                # Lives OCR is noisy (pop particles), so only trust readings within the starting
                # total and require two consecutive low frames before acting on them.
                if livesReading > 0:
                    if startLives is None:
                        startLives = livesReading
                        lastLives = livesReading
                    elif livesReading <= startLives:
                        # A cropped particle or a missed leading digit regularly turns
                        # 156 into 6/5/2. Large real leaks are possible too: require
                        # corroborating masks and a sustained decreasing sequence
                        # instead of permanently rejecting everything below a stale value.
                        maxPlausibleDrop = max(10, int(startLives * 0.15))
                        plausible = lastLives is None or lastLives - maxPlausibleDrop <= livesReading <= lastLives
                        nearbyPending = pendingLives is not None and abs(livesReading - pendingLives) <= 2
                        corroboratedDrop = False
                        if not plausible and lastLives is not None and livesReading < lastLives:
                            try:
                                corroboratedDrop = all(int(custom_ocr(images[0], white_threshold=t).split('/')[0]) == livesReading
                                                       for t in (230, 242))
                            except (AttributeError, TypeError, ValueError):
                                pass
                        if not plausible and not corroboratedDrop:
                            pendingLives = None
                            pendingLivesFrames = 0
                            customPrint('DEBUG rejecting implausible lives OCR ' + str(livesReading) +
                                        ' after ' + str(lastLives))
                        else:
                            if corroboratedDrop:
                                nearbyPending = pendingLives is not None and livesReading <= pendingLives
                            pendingLivesFrames = pendingLivesFrames + 1 if nearbyPending else 1
                            pendingLives = livesReading
                            if pendingLivesFrames >= (3 if corroboratedDrop else 2):
                                confirmedLives = livesReading
                                if lastLives is not None and confirmedLives < lastLives:
                                    customPrint('LIVES_LOST ' + str(lastLives) + ' -> ' + str(confirmedLives)
                                                + ' round=' + str(currentValues['round']))
                                lastLives = confirmedLives
                                pendingLives = None
                                pendingLivesFrames = 0
                                if currentGameState is not None:
                                    currentGameState.lives = confirmedLives
                                # Trigger recovery before a route is one leak away from defeat. This is
                                # especially important on Alternate Bloons rounds, where a single missed
                                # defense can drain lives for several rounds before the route notices.
                                if startLives > 1 and confirmedLives < startLives * 0.85:
                                    lowLivesFrames += 1
                                else:
                                    lowLivesFrames = 0
                                if lowLivesFrames >= 2 and not emergencySpend:
                                    emergencySpend = True
                                    customPrint('EMERGENCY_SPEND lives ' + str(confirmedLives) + '/' + str(startLives)
                                                + ' round=' + str(currentValues['round'])
                                                + '; spending planned and extra upgrades without reserve')

                if currentValues['round'] >= 0 and currentValues['round'] != observedRound:
                    observedRound = currentValues['round']
                    observedRoundStartedAt = time.time()
                    customPrint('DEBUG observed round start round=' + str(observedRound))
                    if terrainMotion is not None:
                        terrainMotion.observeRoundStart(screenshot, [tuple(t.get('position')) for t in (currentGameState.towers.values() if currentGameState else [])
                                                                      if isinstance(t.get('position'), (list, tuple)) and len(t.get('position')) == 2])
                if currentValues['money'] != -1:
                    unreadableCashFrames = 0
                if currentValues['round'] != -1:
                    unreadableRoundFrames = 0
                if currentValues['round'] != -1 and currentValues['money'] != -1:
                    unreadableRecoveries = 0
                if currentGameState is not None:
                    currentGameState.observe(currentValues['money'], currentValues['round'], screen.name)
                    if time.time() - lastGameStatePersist >= 1.0:
                        saveGameState(currentGameState)
                        lastGameStatePersist = time.time()
                if routeCheckpoint is not None and currentValues['round'] >= 0 and routeCheckpoint.get('status') == 'ready':
                    routeCheckpoint['round'] = currentValues['round']
                    # Persist round changes so a restarted runner cannot replay actions after rounds advanced.
                    if currentValues['round'] != routeCheckpoint.get('persistedRound'):
                        routeCheckpoint['persistedRound'] = currentValues['round']
                        writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])

                heldPlacement = bool(lastIterationAction and lastIterationAction.get('action') == 'place'
                                     and held_placement_visible(screenshot))
                # Money can rise while an action is applied because pops and round income
                # arrive between screenshots. Cash can support placement evidence,
                # but cannot identify an upgrade's resulting path/tier.
                if (lastIterationAction and lastIterationAction.get('action') in ('place', 'upgrade')
                    and lastIterationBalance >= 0 and currentValues['money'] >= 0
                    and lastIterationCost > 0):
                    observedSpend = lastIterationBalance - currentValues['money']
                    upgradeStatus = lastIterationAction.get('upgradeObservation', {}).get('status')
                    if upgradeStatus == 'confirmed' or (lastIterationAction.get('action') == 'place' and observedSpend > 0 and not heldPlacement):
                        if currentGameState is not None:
                            currentGameState.confirm_purchase(lastIterationAction, mapConfig, lastIterationBalance, currentValues['money'])
                            saveGameState(currentGameState)
                        if lastIterationAction.get('action') == 'upgrade':
                            updateUpgradeMemory(lastIterationAction, mapConfig, upgradeRunId,
                                                lastIterationBalance, currentValues['money'], currentValues['round'])
                        else:
                            recordSpot(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig), lastIterationAction['pos'], True, screenshot.shape[1])
                            learnPlacementSample(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig), patchFeature(pendingPlacementProbe.get('before')) if pendingPlacementProbe and pendingPlacementProbe.get('name') == lastIterationAction.get('name') else None, True)
                            towerTracker.remember(lastIterationAction.get('name'), screenshot, lastIterationAction['pos'])
                        confidence = ('panel-tier-confirmed' if upgradeStatus == 'confirmed' else
                                      'cash-confirmed' if observedSpend == lastIterationCost else 'cash-drop-confirmed (income/price delta differed)')
                        customPrint('DEBUG ' + lastIterationAction['action'] + ' ' + confidence + ' tower=' + str(lastIterationAction.get('name')) +
                                    ' path=' + str(lastIterationAction.get('path')) + ' expected=' + str(lastIterationCost) + ' observed=' + str(observedSpend))
                    else:
                        if lastIterationAction.get('action') == 'upgrade':
                            plannedTiers = lastIterationAction.get('expectedUpgradeTiers')
                            exactIntent = (isinstance(plannedTiers, (list, tuple)) and len(plannedTiers) == 3
                                           and all(type(tier) is int and 0 <= tier <= 5 for tier in plannedTiers))
                            safeRecheck = upgradeStatus in ('unselected', 'unchanged') or (upgradeStatus in ('unknown', 'unexpected') and exactIntent)
                            towerInfo = currentGameState.towers.get(str(lastIterationAction.get('name')), {}) if currentGameState else {}
                            thawRound = predicted_thaw_round(mapConfig.get('map'), lastIterationAction.get('name'),
                                towerInfo.get('type'), currentGameState.events if currentGameState else [], currentValues.get('round'))
                            deferForThaw = (exactIntent and thawRound is not None
                                            and lastIterationAction.get('upgradeObservation', {}).get('reason') == 'button-unavailable')
                            if safeRecheck and (lastIterationAction.get('selectionAttempts', 0) < 2 or deferForThaw):
                                # Preserve this exact planned tier ahead of its dependents.
                                # Unknown results require an exact target: observe_upgrade
                                # re-reads pips and skips input if that target is already owned.
                                retry = dict(lastIterationAction)
                                retry['selectionAttempts'] = retry.get('selectionAttempts', 0) + 1
                                if upgradeStatus == 'unchanged':
                                    target = list(lastIterationAction['upgradeObservation']['before'])
                                    target[retry['path']] += 1
                                    retry['expectedUpgradeTiers'] = target
                                if exactIntent or upgradeStatus == 'unchanged':
                                    # A delayed purchase may already have spent the money.
                                    # Reconcile visible ownership before waiting to afford it again.
                                    retry['resumeUpgradeProbe'] = True
                                retry.pop('upgradeObservation', None)
                                if deferForThaw:
                                    retry['deferredUpgradeRound'] = thawRound
                                    retry['resumeUpgradeProbe'] = True
                                    if routeCheckpoint is not None:
                                        recordUpgradeCheckpoint(routeCheckpoint, retry)
                                    customPrint('MAP_AVAILABILITY upgrade deferred tower=' + str(retry.get('name'))
                                                + ' observed_round=' + str(currentValues.get('round'))
                                                + ' predicted_thaw_round=' + str(thawRound)
                                                + '; exact tier retained; availability will be re-read')
                                mapConfig['steps'].insert(0, retry)
                                customPrint('RECOVERY upgrade retry queued before dependent steps tower=' + str(retry.get('name'))
                                            + ' reason=' + str(lastIterationAction.get('upgradeObservation', {}).get('reason') or upgradeStatus)
                                            + ' attempt=' + str(retry['selectionAttempts']))
                            # Retrying on cash alone can buy a higher tier when income
                            # masks a successful purchase. The input branch already performs
                            # one button retry only after observing unchanged tier pips.
                            if currentGameState is not None:
                                # Keep recovery compatible with older installed game_runtime.py
                                # copies. A missing optional ledger helper must never terminate
                                # the replay that is meant to recover from an ambiguous upgrade.
                                markUncertain = getattr(currentGameState, 'mark_action_uncertain', None)
                                if callable(markUncertain):
                                    markUncertain(lastIterationAction, lastIterationBalance, currentValues['money'])
                                    saveGameState(currentGameState)
                                else:
                                    customPrint('WARNING upgrade ledger lacks mark_action_uncertain; skipping optional ambiguity annotation and continuing recovery')
                            if lastIterationAction.get('extra', {}).get('opportunistic'):
                                # Usually a tier the profile hasn't unlocked. Stopping all surplus here
                                # left routes losing late with tens of thousands unspent; block just
                                # this tower path and keep spending elsewhere.
                                surplusBlockedPaths.add((str(lastIterationAction.get('name')), lastIterationAction.get('path')))
                                customPrint('SURPLUS_UPGRADE ambiguous purchase; blocking tower=' + str(lastIterationAction.get('name'))
                                            + ' path=' + str(lastIterationAction.get('path')) + ' and continuing with other upgrades')
                            customPrint('WARNING upgrade cash result remains ambiguous after ' +
                                        ('one reselect retry' if lastIterationAction.get('upgradeRetried') else 'first input') +
                                        ' (expected=' + str(lastIterationCost) + ', net spend=' + str(observedSpend) +
                                        '); cash alone cannot distinguish a missed click from pop income, so keep the planned tower actions and continue')
                            failedTower = str(lastIterationAction.get('name', ''))
                            if failedTower:
                                customPrint('RECOVERY upgrade_unconfirmed tower=' + failedTower +
                                            ' skipped_dependent_actions=0' +
                                            ' round=' + str(currentValues['round']))
                                if routeCheckpoint is not None:
                                    routeCheckpoint.update(status='ready',
                                                           nextStep=checkpointStepOffset(mapConfig['steps'], routeStepTotal),
                                                           pendingAction=None)
                                    writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                            lastIterationAction = None
                        else:
                            customPrint('DEBUG placement cash result is not a confirmed purchase expected=' + str(lastIterationCost) +
                                        ' observed=' + str(observedSpend) + '; existing placement recovery will inspect it')
                # A placement cash sample that rose can be masked by in-round income. Only an
                # unchanged reading is eligible for spatial retries; otherwise a duplicate tower
                # could be placed after the first one already succeeded.
                if (lastIterationAction and lastIterationAction.get('action') == 'place'
                    and (heldPlacement or (lastIterationBalance >= 0 and currentValues['money'] == lastIterationBalance))
                    and (lastIterationCost >= 0 or lastIterationAction.get('extra', {}).get('freePlacement'))):
                    probe = pendingPlacementProbe if pendingPlacementProbe and pendingPlacementProbe.get('name') == lastIterationAction.get('name') else None
                    placementConfirmed, visualStats = placementVisualCheck(probe, screenshot)
                    if heldPlacement:
                        placementConfirmed = False
                        visualStats = {**visualStats, 'rejected': 'held-placement-controls'}
                        customPrint('RECOVERY held placement detected tower=' + str(lastIterationAction.get('name'))
                                    + '; cash changes cannot confirm a tower still on the cursor')
                    # A held tower ghost (and its range circle) at the target passes the visual
                    # check too. For a paid tower, unchanged cash means nothing was bought; trusting
                    # the visual left the ghost on the cursor, which hides the round counter and
                    # stalled the whole route at round=-1.
                    if placementConfirmed and lastIterationCost > 0 \
                            and not lastIterationAction.get('extra', {}).get('freePlacement'):
                        placementConfirmed = False
                        visualStats = {**visualStats, 'rejected': 'paid-tower-cash-unchanged'}
                    customPrint('DEBUG no-cash placement visual check tower=' + str(lastIterationAction.get('name'))
                                + ' confirmed=' + str(placementConfirmed) + ' details=' + str(visualStats))
                    if placementConfirmed:
                        if lastIterationAction.get('type') != 'hero':
                            placementConfirmed, panelProbe = verify_tower_placement(lastIterationAction['pos'],
                                lambda: np.array(pyautogui.screenshot())[:, :, ::-1].copy(),
                                pyautogui.click, time.sleep)
                            visualStats = {**visualStats, 'panelProbe': panelProbe}
                            customPrint('PLACEMENT_PANEL_PROBE tower=' + str(lastIterationAction.get('name'))
                                        + ' ' + str(panelProbe))
                            if not placementConfirmed and panelProbe.get('status') != 'held':
                                # A panel may be unavailable on frozen/moving maps. Lack of
                                # proof is not proof of an empty tile; never duplicate a
                                # possibly free tower or teach this tile as illegal.
                                customPrint('WARNING placement remains unverified tower='
                                            + str(lastIterationAction.get('name'))
                                            + '; no blind duplicate placement or terrain refusal recorded')
                                if currentGameState is not None:
                                    currentGameState.mark_action_uncertain(lastIterationAction,
                                        lastIterationBalance, currentValues['money'])
                                    saveGameState(currentGameState)
                                lastIterationAction = None
                                pendingPlacementProbe = None
                                continue
                    if placementConfirmed:
                        if currentGameState is not None:
                            currentGameState.confirm_purchase(lastIterationAction, mapConfig,
                                                             lastIterationBalance, currentValues['money'])
                            saveGameState(currentGameState)
                        customPrint('DEBUG placement visually confirmed with unchanged cash; treating it as free or cash-offset tower=' + str(lastIterationAction.get('name')))
                        recordSpot(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig), lastIterationAction['pos'], True, screenshot.shape[1])
                        learnPlacementSample(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig), patchFeature(pendingPlacementProbe.get('before')) if pendingPlacementProbe and pendingPlacementProbe.get('name') == lastIterationAction.get('name') else None, True)
                        towerTracker.remember(lastIterationAction.get('name'), screenshot, lastIterationAction['pos'])
                        lastIterationAction = None
                        pendingPlacementProbe = None
                        continue
                    if lastIterationCost == 0:
                        customPrint('WARNING zero-cost placement was not visible at its target; retrying a nearby legal spot instead of assuming it placed')
                    # The game refused this spot even if the tint looked fine: learn it as illegal so
                    # the model and known-spot list correct themselves.
                    markRefused(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig),
                                lastIterationAction['pos'], screenshot.shape[1])
                    if not isDynamicPlacementMap(mapConfig.get('map')):
                        recordSpot(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig),
                                   lastIterationAction['pos'], False, screenshot.shape[1])
                    learnPlacementSample(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig),
                                         patchFeature(probe.get('before')) if probe else None, False)
                    # Right-click cancels an unplaced tower ghost. Esc can pause
                    # a live game when the ghost was never created, causing an
                    # endless pause/unpause loop on the next retry.
                    pyautogui.click(button='right')
                    attempts = lastIterationAction.get('placeAttempts', 0)
                    os.makedirs(FAILURE_SHOT_DIR, exist_ok=True)
                    shot = os.path.join(FAILURE_SHOT_DIR, time.strftime('%Y%m%d-%H%M%S') + '_placement_' + str(mapConfig.get('map')) + '_' + str(lastIterationAction.get('name')) + '_' + str(attempts) + '.png')
                    cv2.imwrite(shot, screenshot)
                    customPrint('FAILURE_SHOT ' + os.path.abspath(shot) + ' action=' + str(lastIterationAction))
                    # On maps whose placement surfaces or tower access can change, a nearby
                    # coordinate is not a safe substitute. A nudge could put a tower under
                    # Covered Garden's glass, on a moved Geared/Sanctuary platform, on land
                    # that has eroded/flooded, or outside Polyphemus's closing eye. Keep the
                    # failure screenshot and avoid speculative spatial retries on those maps.
                    dynamicPlacementMaps = DYNAMIC_PLACEMENT_MAPS
                    mapKey = str(mapConfig.get('map', '')).lower().replace(' ', '').replace("'", '').replace('_', '')
                    # BLOONS_DYNAMIC_PLACEMENT is set by automation.js from map-mechanics.js's fuller
                    # per-map catalog (moving/toggled/phase-gated placement surfaces) — this supplements
                    # the hardcoded set above instead of requiring every new dynamic map to be added here too.
                    dynamicMap = mapKey in dynamicPlacementMaps or os.environ.get('BLOONS_DYNAMIC_PLACEMENT') == '1'
                    # Dynamic maps get same-spot retries only; each retry still runs the
                    # tint-verified legal-spot search, which is safe there.
                    if attempts < len(PLACE_RETRY_OFFSETS):
                        origin = lastIterationAction.get('originPos', lastIterationAction['pos'])
                        scale = screenshot.shape[1] / 2560
                        offset = (0, 0) if dynamicMap else PLACE_RETRY_OFFSETS[attempts]
                        newPos = (int(origin[0] + offset[0] * scale),
                                  int(origin[1] + offset[1] * scale))
                        oldPos = tuple(lastIterationAction['pos'])
                        for step in mapConfig['steps']:
                            if step.get('name') == lastIterationAction['name'] and tuple(step.get('pos', ())) == oldPos:
                                step['pos'] = newPos
                        mapConfig['steps'].insert(0, dict(lastIterationAction, pos=newPos,
                                                          placeAttempts=attempts + 1, originPos=origin))
                        customPrint('WARNING place of ' + str(lastIterationAction['name']) + ' at ' + str(oldPos)
                                    + ' spent nothing; retry ' + str(attempts + 1) + ' at ' + str(newPos))
                    else:
                        failedTower = str(lastIterationAction.get('name', 'unknown'))
                        priorCount = len(mapConfig['steps'])
                        mapConfig['steps'] = [step for step in mapConfig['steps']
                                              if str(step.get('name', '')) != failedTower]
                        skippedCount = priorCount - len(mapConfig['steps'])
                        if dynamicMap:
                            customPrint('ERROR dynamic-map placement not confirmed map=' + mapKey + ' at its recorded point; live placement/access state is not calibrated, so no blind coordinate nudge will be attempted; recovery will skip its ' +
                                        str(skippedCount) + ' dependent action(s) and continue the live route')
                        else:
                            customPrint('ERROR place of ' + failedTower + ' failed at every nearby spot; recovery will skip its ' +
                                    str(skippedCount) + ' dependent action(s) and continue the live route')
                        if currentGameState is not None and not currentGameState.towers:
                            # Nothing is on the map yet; starting rounds now is a guaranteed instant
                            # loss (one life in CHIMPS/impoppable). Leave and report a bot-side failure.
                            customPrint('INSTANT_LOSS_PREVENTED opening placement of ' + failedTower
                                        + ' failed and no tower is placed; leaving before the round starts')
                            objectiveFailed = True
                            objectiveFailureReason = 'opening placement failed'
                            state = State.GOTO_HOME
                            lastStateTransitionSuccessful = True
                            lastIterationAction = None
                            pendingPlacementProbe = None
                            continue
                        if routeCheckpoint is not None:
                            routeCheckpoint.update(status='ready',
                                                   nextStep=checkpointStepOffset(mapConfig['steps'], routeStepTotal),
                                                   pendingAction=None)
                            writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                        pendingPlacementProbe = None
                    lastIterationAction = None
                elif (lastIterationAction and lastIterationAction.get('action') == 'place'
                      and lastIterationBalance >= 0 and currentValues['money'] > lastIterationBalance
                      and lastIterationCost > 0):
                    customPrint('WARNING placement cash rose during the action; cost is ambiguous due to in-round income, so no blind duplicate placement will be sent')
                    # Round income hides the purchase in cash, which left the tower out of the
                    # ledger, so later surplus/emergency spending could never upgrade it. Confirm
                    # it from the screen instead.
                    probe = pendingPlacementProbe if pendingPlacementProbe and pendingPlacementProbe.get('name') == lastIterationAction.get('name') else None
                    placedVisually, visualStats = placementVisualCheck(probe, screenshot)
                    if placedVisually and lastIterationAction.get('type') != 'hero':
                        placedVisually, panelProbe = verify_tower_placement(lastIterationAction['pos'],
                            lambda: np.array(pyautogui.screenshot())[:, :, ::-1].copy(),
                            pyautogui.click, time.sleep)
                        visualStats = {**visualStats, 'panelProbe': panelProbe}
                        customPrint('PLACEMENT_PANEL_PROBE tower=' + str(lastIterationAction.get('name'))
                                    + ' ' + str(panelProbe))
                    if placedVisually and currentGameState is not None:
                        currentGameState.confirm_purchase(lastIterationAction, mapConfig,
                                                         lastIterationBalance + lastIterationCost, currentValues['money'])
                        saveGameState(currentGameState)
                        recordSpot(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig), lastIterationAction['pos'], True, screenshot.shape[1])
                        learnPlacementSample(mapConfig.get('map'), placementClassFor(lastIterationAction, mapConfig), patchFeature(pendingPlacementProbe.get('before')) if pendingPlacementProbe and pendingPlacementProbe.get('name') == lastIterationAction.get('name') else None, True)
                        towerTracker.remember(lastIterationAction.get('name'), screenshot, lastIterationAction['pos'])
                        customPrint('DEBUG placement visually confirmed despite in-round income tower='
                                    + str(lastIterationAction.get('name')) + ' details=' + str(visualStats))
                    pendingPlacementProbe = None
                # A single cash sample cannot prove a miss while the round is paying out.
                # Keep the action marked unverified and let the route's actual result decide;
                # blindly repeating a hotkey could buy the next tier instead.
                if (lastIterationAction and lastIterationAction.get('action') == 'sell'
                    and lastIterationBalance >= 0 and currentValues['money'] >= 0
                    and lastIterationAction.get('cost', 0) < 0):
                    observedProceeds = currentValues['money'] - lastIterationBalance
                    if observedProceeds == -lastIterationAction['cost']:
                        if currentGameState is not None:
                            currentGameState.confirm_sale(lastIterationAction, lastIterationBalance, currentValues['money'])
                            saveGameState(currentGameState)
                        customPrint('DEBUG sell cash-confirmed tower=' + str(lastIterationAction.get('name')) +
                                    ' proceeds=' + str(observedProceeds))
                    else:
                        customPrint('DEBUG sell not confirmed expected=' + str(-lastIterationAction['cost']) +
                                    ' observed=' + str(observedProceeds) + '; tower state unchanged')

                
                # to prevent random explosion particles that were recognized as digits from messing up the game
                # still possible: if it habens 2 times in a row
                # potential solution: when placing: check if pixel changed colour(or even is of correct colour) - potentially blocked by particles/projectiles
                # when upgrading: check if corresponding box turned green(for left and right menu)
                # remove obstacle: colour change?

                canBuySurplus = (mode not in (Mode.VALIDATE_PLAYTHROUGHS, Mode.VALIDATE_COSTS)
                                 and mapConfig.get('gamemode') != 'deflation')
                if not mapConfig['steps'] and canBuySurplus and not surplusUpgradeStopped:
                    extraUpgrade, noUpgradesLeft = nextSurplusUpgrade(currentValues['money'])
                    if noUpgradesLeft:
                        surplusUpgradeStopped = True
                        customPrint('SURPLUS_UPGRADE_DONE no legal untried upgrades remain; waiting for victory/defeat')
                    elif extraUpgrade:
                        attemptKey = (str(extraUpgrade['name']), extraUpgrade['path'], extraUpgrade['extra']['upgrade'][1])
                        surplusUpgradeAttempts.add(attemptKey)
                        mapConfig['steps'].append(extraUpgrade)
                        if routeCheckpoint is not None:
                            routeCheckpoint.setdefault('supplementalUpgrades', []).append({
                                'tower': extraUpgrade['name'], 'path': extraUpgrade['path'],
                                'tier': extraUpgrade['extra']['upgrade'][1], 'cost': extraUpgrade['cost'],
                            })
                            writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                        customPrint('SURPLUS_UPGRADE planned tower=' + str(extraUpgrade['name']) +
                                    ' path_index=' + str(extraUpgrade['path']) + ' tier=' +
                                    str(extraUpgrade['extra']['upgrade'][1]) + ' cost=' + str(extraUpgrade['cost']) +
                                    ' cash=' + str(currentValues['money']))
                    elif (lastSurplusWaitRound != currentValues['round']
                          or (lastSurplusWaitCash != currentValues['money']
                              and time.monotonic() - lastSurplusWaitAt >= 15)):
                        lastSurplusWaitCash = currentValues['money']
                        lastSurplusWaitRound = currentValues['round']
                        lastSurplusWaitAt = time.monotonic()
                        customPrint('SURPLUS_UPGRADE waiting for enough cash; round=' +
                                    str(currentValues['round']) + ' cash=' + str(currentValues['money']))

                # Preserve the recorded round order and upgrade paths. Extra spending is
                # allowed above only after every planned action has been executed; buying
                # optional crosspaths mid-route can make later recorded upgrades illegal.

                # Emergency recovery may spend only actions already present in the route. If a
                # route placed its next defense behind an await_round step, release that wait when
                # the action is affordable instead of knowingly letting bloons leak until the
                # recorded round. No new tower or upgrade is invented here.
                # Preserve Glacial Trail's recorded thaw timing; early action release during a storm can target frozen towers.
                if emergencySpend and mapConfig.get('gamemode') != 'chimps' and mapConfig.get('map') != 'glacial_trail':
                    while len(mapConfig['steps']) and mapConfig['steps'][0].get('action') == 'await_round' and 'secondsAfterRound' not in mapConfig['steps'][0]:
                        upcoming = next((step for step in mapConfig['steps'][1:]
                                         if step.get('action') not in ('await_round', 'await_cash', 'speed')), None)
                        if upcoming is None or currentValues.get('money', -1) < int(upcoming.get('cost', 0) or 0):
                            break
                        skippedWait = mapConfig['steps'].pop(0)
                        customPrint('EMERGENCY_SPEND releasing await_round=' + str(skippedWait.get('round'))
                                    + ' for planned action=' + str(upcoming.get('name'))
                                    + ' cost=' + str(upcoming.get('cost')))

                if len(mapConfig['steps']):
                    customPrint('DEBUG next_action=' + str(mapConfig['steps'][0]) + ' balance=' + str(lastIterationBalance) + ' cost=' + str(lastIterationCost))
                    if mapConfig['steps'][0]['action'] == 'sell':
                        customPrint('detected money: ' + str(currentValues['money']) + ', required: ' + str(getNextNonSellAction(mapConfig['steps'])['cost'] - sumAdjacentSells(mapConfig['steps'])) + ' (' + str(getNextNonSellAction(mapConfig['steps'])['cost']) + ' - ' + str(sumAdjacentSells(mapConfig['steps'])) + ')' + '          ', end = '', rewriteLine=True)
                    if mapConfig['steps'][0]['action'] == 'await_round':
                        customPrint('detected round: ' + str(currentValues['round']) + ', awaiting: ' + str(mapConfig['steps'][0]['round']) + '          ', end = '', rewriteLine=True)
                    elif mapConfig['steps'][0]['action'] == 'await_cash':
                        customPrint('detected money: ' + str(currentValues['money']) + ', awaiting: ' + str(mapConfig['steps'][0]['cash']) + '          ', end = '', rewriteLine=True)
                    else:
                        customPrint('detected money: ' + str(currentValues['money']) + ', required: ' + str(mapConfig['steps'][0]['cost']) + '          ', end = '', rewriteLine=True)

                nextStep = mapConfig['steps'][0] if len(mapConfig['steps']) else None
                if nextStep and upgrade_ready(nextStep, currentValues.get('round')) and nextStep.pop('resumeUpgradeProbe', False):
                    # Check ownership before the cash gate: an already bought tier
                    # must not wait for enough cash to buy that tier a second time.
                    pyautogui.click(button='right')
                    try:
                        probe = probe_owned_upgrade(nextStep['expectedUpgradeTiers'],
                            capture=lambda: np.array(pyautogui.screenshot())[:, :, ::-1].copy(),
                            select=lambda: pyautogui.click(nextStep['pos']), wait=time.sleep)
                    finally:
                        pyautogui.click(button='right')
                    customPrint('RESUME_UPGRADE ' + str(nextStep.get('name')) + ' ' + str(probe))
                    if probe['status'] == 'confirmed':
                        nextStep['upgradeObservation'] = probe
                        mapConfig['steps'].pop(0)
                        if currentGameState is not None:
                            currentGameState.confirm_purchase(nextStep, mapConfig, 0, 0)
                            saveGameState(currentGameState)
                        if routeCheckpoint is not None:
                            recordUpgradeCheckpoint(routeCheckpoint, nextStep)
                            routeCheckpoint['nextStep'] = checkpointStepOffset(mapConfig['steps'], routeStepTotal)
                            writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                        lastIterationAction = None
                        lastIterationCost = 0
                        lastIterationBalance = currentValues['money']
                        continue
                nextStepAction = nextStep.get('action') if nextStep else None
                nextStepDelayReady = (delay_ready(nextStep, time.time())
                                      and round_offset_ready(nextStep, time.time(), observedRound, observedRoundStartedAt)
                                      and ability_ready(nextStep, time.time(), observedRoundStartedAt)
                                      and upgrade_ready(nextStep, currentValues.get('round')))
                roundStartInputIssued = False
                if nextStepAction in ('start_round', 'speed_toggle') and nextStepDelayReady:
                    startState, startDiff = None, None
                    for startName, startValue in (('game_playing_fast', 'fast'), ('game_playing_slow', 'slow'), ('game_paused', 'paused')):
                        diff = cv2.matchTemplate(cutImage(screenshot, imageAreas['compare']['game_state']),
                                                cutImage(comparisonImages['game_state'][startName], imageAreas['compare']['game_state']),
                                                cv2.TM_SQDIFF_NORMED)[0][0]
                        if startDiff is None or diff < startDiff:
                            startState, startDiff = startValue, diff
                    def persistRoundStart():
                        if routeCheckpoint is None:
                            return True
                        routeCheckpoint.update(status='ready', pendingAction=None)
                        return writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                    nextStepDelayReady, roundStartInputIssued = round_start_ready(
                        nextStep, time.time(), startState if startDiff < 0.05 else None,
                        not (skippingIteration or heldPlacement or routeActionExecuted), sendKey, persistRoundStart, customPrint)
                    routeActionExecuted = routeActionExecuted or roundStartInputIssued
                    playToggleIssued = playToggleIssued or roundStartInputIssued
                if nextStep and 'secondsAfterRound' in nextStep and observedRound is not None and observedRound > nextStep.get('round', observedRound):
                    customPrint('TIMING_RECOVERY overdue round offset target=' + str(nextStep['round']) + ' observed=' + str(observedRound) + '; executing remaining planned action')
                nextStepCost = int(nextStep.get('cost', 0) or 0) if nextStep else 0
                cashRequiredForNext = bool(nextStep and (nextStepCost > 0 or nextStepAction in ('await_cash', 'sell')))
                roundRequiredForNext = bool(nextStep and nextStepAction == 'await_round')

                # Panel confirmation takes real time. Do not let an untimed,
                # affordable upgrade batch lose several game rounds at 3x speed.
                # The parser stores this opt-out before resume removes old steps.
                if (mapConfig.get('purchasePacingAllowed') is True and nextStepDelayReady
                        and nextStepAction in ('place', 'upgrade', 'retarget', 'special')
                        and affordable_upgrade_batch(mapConfig['steps'], currentValues.get('money'))):
                    paceState, paceDiff = None, None
                    for paceName, paceValue in (('game_playing_fast', 'fast'), ('game_playing_slow', 'slow'), ('game_paused', 'paused')):
                        diff = cv2.matchTemplate(cutImage(screenshot, imageAreas['compare']['game_state']),
                                                cutImage(comparisonImages['game_state'][paceName], imageAreas['compare']['game_state']),
                                                cv2.TM_SQDIFF_NORMED)[0][0]
                        if paceDiff is None or diff < paceDiff:
                            paceState, paceDiff = paceValue, diff
                    paceReady, paceIssued = purchase_pacing_ready(True,
                        paceState if paceDiff < 0.05 else None,
                        not (skippingIteration or heldPlacement or routeActionExecuted or playToggleIssued),
                        time.time(), lastPlayToggleAt, keybinds['others'].get('play'), sendKey)
                    nextStepDelayReady = nextStepDelayReady and paceReady
                    if paceIssued:
                        lastPlayToggleAt = time.time()
                        playToggleIssued = routeActionExecuted = True
                        customPrint('PURCHASE_PACING observed fast; slowing affordable upgrade batch before input')

                if mode == Mode.VALIDATE_PLAYTHROUGHS:
                    if lastIterationBalance != -1 and currentValues['money'] != lastIterationBalance - lastIterationCost:
                        if currentValues['money'] == lastIterationBalance:
                            customPrint('action: ' + str(lastIterationAction) + ' failed!')
                            validationResult = False
                            mapConfig['steps'] = []
                        else:
                            customPrint('pricing error! expected cost: ' + str(lastIterationCost) + ', detected cost: ' + str(lastIterationBalance - currentValues['money']) + '. Is monkey knowledge disabled?')
                elif mode == Mode.VALIDATE_COSTS:
                    if lastIterationBalance != -1 and lastIterationAction:
                        if lastIterationAction['action'] == 'place':
                            costs[lastIterationAction['extra']['group']][lastIterationAction['extra']['type']]['base'] = int(lastIterationBalance - currentValues['money'])
                        elif lastIterationAction['action'] == 'upgrade':
                            costs[lastIterationAction['extra']['group']][lastIterationAction['extra']['type']]['upgrades'][lastIterationAction['extra']['upgrade'][0]][lastIterationAction['extra']['upgrade'][1] - 1] = int(lastIterationBalance - currentValues['money'])

                if mode == Mode.VALIDATE_PLAYTHROUGHS and len(mapConfig['steps']) and (mapConfig['steps'][0]['action'] == 'await_round' or  mapConfig['steps'][0]['action'] == 'speed'):
                    mapConfig['steps'].pop(0)
                elif ((currentValues['money'] == -1 and cashRequiredForNext)
                      or (currentValues['round'] == -1 and roundRequiredForNext)):
                    recognitionErrorSignature = (currentValues['money'], currentValues['round'])
                    if recognitionErrorSignature != lastCashErrorLogged or time.time() - lastCashErrorLoggedAt > 1:
                        customPrint('recognition error. money: ' + str(currentValues['money']) + ', round: ' + str(currentValues['round']))
                        lastCashErrorLogged = recognitionErrorSignature
                        lastCashErrorLoggedAt = time.time()
                    # A tower panel left open on the left moves the whole cash/lives HUD to the right,
                    # so cash stays unreadable and the route stalls until it loses. The same kind of
                    # lingering overlay (a leftover placement tooltip, a stuck panel) can instead cover
                    # only the round counter while cash stays readable - either way, close it by
                    # clicking the middle of the playfield twice.
                    if currentValues['money'] == -1:
                        unreadableCashFrames += 1
                    if currentValues['round'] == -1:
                        unreadableRoundFrames += 1
                    if (unreadableCashFrames >= 6 or unreadableRoundFrames >= 20) and time.time() - lastPanelCloseAt > 3:
                        centre = (screenshot.shape[1] // 2, screenshot.shape[0] // 2)
                        customPrint('WARNING cash/round unreadable for ' + str(unreadableCashFrames) + '/' + str(unreadableRoundFrames) + ' frames; closing any open tower panel (two clicks at screen centre ' + str(centre) + ')')
                        unreadableRecoveries += 1
                        if unreadableRecoveries == 1:
                            try:
                                os.makedirs(FAILURE_SHOT_DIR, exist_ok=True)
                                shot = os.path.join(FAILURE_SHOT_DIR, 'round_unreadable_' + time.strftime('%Y%m%d-%H%M%S')
                                                    + '_' + str(mapConfig.get('map')) + '.png')
                                cv2.imwrite(shot, screenshot)
                                customPrint('FAILURE_SHOT ' + os.path.abspath(shot) + ' reason=round/cash unreadable')
                            except Exception as error:
                                customPrint('WARNING could not save unreadable-HUD screenshot: ' + str(error))
                        # Never use Esc here: in BTD6 it is also the pause shortcut. A recovery
                        # that pauses the game can create a false stuck state and cost lives while
                        # the runner waits for the HUD to return. Cancel a held tower ghost first,
                        # then use the same safe centre clicks on every recovery attempt.
                        customPrint('DEBUG HUD recovery ' + str(unreadableRecoveries) +
                                    ': cancelling ghost and clicking centre twice (no pause key)')
                        pyautogui.click(button='right')
                        time.sleep(0.2)
                        for _ in range(2):
                            pyautogui.click(centre)
                            time.sleep(0.2)
                        lastPanelCloseAt = time.time()
                elif (mode != Mode.VALIDATE_COSTS and currentValues['money'] >= 0
                      and lastIterationBalance - lastIterationCost > currentValues['money']):
                    cashErrorSignature = (lastIterationBalance, lastIterationCost, currentValues['money'])
                    if cashErrorSignature != lastCashErrorLogged or time.time() - lastCashErrorLoggedAt > 1:
                        customPrint('potential cash recognition error: ' + str(lastIterationBalance) + ' - ' + str(lastIterationCost) + ' -> ' + str(currentValues['money']))
                        lastCashErrorLogged = cashErrorSignature
                        lastCashErrorLoggedAt = time.time()
                    # cv2.imwrite('tmp_images/' + time.strftime("%Y-%m-%d_%H-%M-%S") + '_' + str(lastIterationBalance) + '.png', lastIterationScreenshotAreas[2])
                    # cv2.imwrite('tmp_images/' + time.strftime("%Y-%m-%d_%H-%M-%S") + '_' + str(currentValues['money']) + '.png', images[2])
                    skippingIteration = True
                elif mode != Mode.VALIDATE_COSTS and lastIterationRound >= 0 and currentValues['round'] >= 0 and lastIterationRound > currentValues['round'] and len(mapConfig['steps']) and mapConfig['steps'][0]['action'] == 'await_round':
                    roundErrorSignature = (lastIterationRound, currentValues['round'])
                    if roundErrorSignature != lastCashErrorLogged or time.time() - lastCashErrorLoggedAt > 1:
                        customPrint('potential round recognition error: ' + str(lastIterationRound) + ' -> ' + str(currentValues['round']))
                        lastCashErrorLogged = roundErrorSignature
                        lastCashErrorLoggedAt = time.time()
                    skippingIteration = True
                elif len(mapConfig['steps']) and nextStepDelayReady and ((mapConfig['steps'][0]['action'] != 'sell' and mapConfig['steps'][0]['action'] != 'await_round' and mapConfig['steps'][0]['action'] != 'await_cash' and (nextStepCost <= 0 or min(currentValues['money'], lastIterationBalance - lastIterationCost) >= nextStepCost))
                or mapConfig['gamemode'] == 'deflation' and mapConfig['steps'][0]['action'] != 'await_cash'
                or mapConfig['steps'][0]['action'] == 'await_round' and currentValues['round'] >= mapConfig['steps'][0]['round']
                or mapConfig['steps'][0]['action'] == 'await_cash' and currentValues['money'] >= mapConfig['steps'][0]['cash']
                or mapConfig['steps'][0]['action'] == 'await_round' and mode == Mode.VALIDATE_PLAYTHROUGHS
                or ((mapConfig['steps'][0]['action'] == 'sell') and min(currentValues['money'], lastIterationBalance - lastIterationCost) + sumAdjacentSells(mapConfig['steps']) >= getNextNonSellAction(mapConfig['steps'])['cost'])):
                    if routeCheckpoint is not None:
                        routeCheckpoint['status'] = 'pending'
                        routeCheckpoint['pendingAction'] = mapConfig['steps'][0].get('action')
                        writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                    action = mapConfig['steps'].pop(0)
                    try:
                        action = normalize_action(action)
                    except ValueError as error:
                        # Bad route data is local to this step. Keep the live game
                        # running and let later actions provide the route's recovery.
                        customPrint('ERROR invalid standardized action; skipping this step and continuing the live route: ' + str(error))
                        lastIterationAction = None
                        pendingPlacementProbe = None
                        if routeCheckpoint is not None:
                            routeCheckpoint.update(status='ready',
                                                   nextStep=checkpointStepOffset(mapConfig['steps'], routeStepTotal),
                                                   pendingAction=None)
                            writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                        continue
                    thisIterationAction = action
                    routeActionExecuted = True
                    if action['action'] != 'sell' and action['action'] != 'await_round' and action['action'] != 'await_cash':
                        thisIterationCost = action['cost']
                    customPrint('performing action: ' + str(action))
                    customPrint('DEBUG executing action=' + str(action.get('action')) + ' name=' + str(action.get('name')) + ' key=' + str(action.get('key')) + ' pos=' + str(action.get('pos')) + ' cost=' + str(action.get('cost')))
                    if action['action'] in ('place', 'upgrade', 'retarget', 'special', 'sell', 'ability') and action.get('key') is None:
                        customPrint('ERROR no BTD6 hotkey is bound for ' + str(action['action']) + ' '
                                    + str(action.get('type') or action.get('slot') or action.get('name'))
                                    + '; bind one in BTD6 settings. Skipping this step instead of pressing a guessed key')
                        thisIterationAction = None
                        thisIterationCost = 0
                    elif action['action'] == 'place':
                        customPrint('DEBUG place move=' + str(action['pos']) + ' key=' + str(action['key']))
                        px, py = int(action['pos'][0]), int(action['pos'][1])
                        probeRadius = max(30, int(screenshot.shape[1] * 0.021))
                        probeLeft, probeRight = max(0, px-probeRadius), min(screenshot.shape[1], px+probeRadius)
                        probeTop, probeBottom = max(0, py-probeRadius), min(screenshot.shape[0], py+probeRadius)
                        pendingPlacementProbe = {'name': action.get('name'), 'pos': tuple(action['pos']),
                                                 'before': screenshot[probeTop:probeBottom, probeLeft:probeRight].copy()}
                        if action.get('extra', {}).get('freePlacement'):
                            customPrint('DEBUG free-MK placement: cash is not authoritative; visual placement confirmation armed')
                        if action.get('type') == 'hero':
                            heroName = mapConfig.get('hero') or action.get('extra', {}).get('type')
                            heroClass = towers.get('heros', {}).get(heroName, {}).get('class', 'unknown') if heroName else 'unknown'
                            customPrint('DEBUG hero placement target=' + str(heroName) + ' terrain=' + str(heroClass) + ' pos=' + str(action['pos']) + ' map=' + str(mapConfig.get('map')))
                        placeClass = placementClassFor(action, mapConfig)
                        pyautogui.moveTo(action['pos'])
                        time.sleep(actionDelay)
                        sendKey(action['key'])
                        time.sleep(actionDelay)
                        # Check the ghost's range tint before buying: a red circle means BTD6 will
                        # refuse the spot, so hover nearby spots instead of click-and-retry cycles.
                        # Maps whose surfaces move keep the recorded point only.
                        # The tint is the game's own legality verdict for this exact moment, so
                        # it is safe on dynamic maps too (unlike a blind coordinate nudge).
                        frameWidth = screenshot.shape[1]
                        mapName = mapConfig.get('map')
                        dynamicHere = isDynamicPlacementMap(mapName)
                        if confirmPlacementMode:
                            pyautogui.click(action['pos'])
                            time.sleep(0.2)
                            originVerdict = not confirmButtonVisible(np.array(pyautogui.screenshot())[:, :, ::-1])
                        else:
                            originVerdict = ghostLooksInvalid(screenshot, action['pos'])
                        # On maps whose placeable ground itself moves (Sanctuary's stones, Geared's gears)
                        # the recorded spot moving is expected; TowerTracker follows the tower, so only
                        # avoid moving ground on maps where it is an occasional hazard.
                        # Frame differences also include bloons, projectiles and decorative
                        # animation. They are not evidence that a recorded placement on a
                        # static map has moved. Keep the route's exact starting coordinate.
                        originMoving = False
                        # The range tint is only a hint (line-of-sight shading and map colours read as
                        # red), and acting on it skipped spots the game then accepted. The recorded spot
                        # is always tried first; only a real refusal (cash unchanged) marks it illegal.
                        if not action.get('placeAttempts', 0):
                            originVerdict = None if originVerdict is True else originVerdict
                        rangePx = towerRangePx(action, frameWidth)
                        supportPx = supportRangePx(action.get('type'), frameWidth)
                        placedTowers = [(name, t) for name, t in (currentGameState.towers.items() if currentGameState else [])
                                        if isinstance(t.get('position'), (list, tuple)) and len(t.get('position')) == 2]
                        plannedPlaces = [st for st in mapConfig['steps'] if st.get('action') == 'place' and st.get('name') != action.get('name')]
                        allies = [tuple(t['position']) for _, t in placedTowers] + [tuple(st['pos']) for st in plannedPlaces if st.get('pos')]
                        villages = ([tuple(t['position']) for _, t in placedTowers if t.get('type') == 'village']
                                    + [tuple(st['pos']) for st in plannedPlaces if st.get('type') == 'village' and st.get('pos')])
                        poorSupport = False
                        # Coverage optimization is optional, not placement recovery.
                        # Keep recorded support coverage on CHIMPS and changing terrain.
                        if (os.environ.get('BLOONS_EXPERIMENTAL_PLACEMENT') == '1'
                                and mapConfig.get('gamemode') != 'chimps' and not dynamicHere
                                and supportPx is not None and allies and originVerdict is False):
                            originReach = towersInside(action['pos'], supportPx, allies)
                            nearbyReach = max(towersInside((int(action['pos'][0] + rr * math.cos(math.radians(a)) * frameWidth / 1920),
                                                            int(action['pos'][1] + rr * math.sin(math.radians(a)) * frameWidth / 1920)),
                                                           supportPx, allies)
                                              for rr in (40, 80, 120) for a in range(0, 360, 45))
                            poorSupport = nearbyReach >= originReach + 2
                        originCoverage = pathHeat.coverage(action['pos'], rangePx, frameWidth) if pathHeat is not None else None
                        poorCoverage = False
                        # A neutral placement tint only means the spot is legal; it does not
                        # mean the tower covers the active path. Once PathHeat has enough frames,
                        # use coverage as an independent signal on stable maps so alternate-path
                        # routes do not silently keep a legal but ineffective placement.
                        if (os.environ.get('BLOONS_EXPERIMENTAL_PLACEMENT') == '1'
                                and mapConfig.get('gamemode') != 'chimps'
                                and originCoverage is not None and not dynamicHere):
                            # Recorded spot is legal but may barely reach the bloon path (converted
                            # routes drift); compare with the best reachable coverage nearby.
                            nearbyBest = max((pathHeat.coverage((int(action['pos'][0] + rr * math.cos(math.radians(a)) * frameWidth / 1920),
                                                                 int(action['pos'][1] + rr * math.sin(math.radians(a)) * frameWidth / 1920)),
                                                                rangePx, frameWidth) or 0)
                                             for rr in (40, 80, 120) for a in range(0, 360, 45))
                            poorCoverage = nearbyBest > 0 and originCoverage < 0.55 * nearbyBest
                        # A learned "illegal" cell may come from an old ghost/UI failure.
                        # Always try the recorded point first; search after a real refused
                        # placement, or an explicit live red-tint verdict.
                        if (originVerdict is True or poorCoverage or poorSupport
                                or (action.get('placeAttempts', 0) > 0
                                    and knownSpotIsIllegal(mapName, placeClass, action['pos'], frameWidth))):
                            # Ranked search: learned terrain model + proven spots, skipping occupied
                            # and moving ground, confirmed against the live ghost tint.
                            # Planned later placements are reserved: taking one strands that tower.
                            occupied = allies
                            legal, source = smartPlacementSearch(screenshot, action['pos'], mapName, placeClass,
                                                                 occupied, terrainMotion, dynamicHere, rangePx, pathHeat,
                                                                 supportPx, allies, villages, allowMoving=dynamicHere)
                            if poorSupport:
                                source += ' (recorded ' + str(action.get('type')) + ' spot reached ' + str(originReach) + ' allies; more reachable nearby)'
                            if poorCoverage:
                                source += ' (recorded spot covered ' + str(originCoverage) + ' path cells; better coverage nearby)'
                            if originMoving:
                                source += ' (recorded spot is on moving terrain)'
                            if legal is not None and tuple(legal) != tuple(action['pos']):
                                oldPos = tuple(action['pos'])
                                for step in mapConfig['steps']:
                                    if step.get('name') == action.get('name') and tuple(step.get('pos', ())) == oldPos:
                                        step['pos'] = legal
                                action['pos'] = legal
                                px, py = int(legal[0]), int(legal[1])
                                probeLeft, probeRight = max(0, px-probeRadius), min(screenshot.shape[1], px+probeRadius)
                                probeTop, probeBottom = max(0, py-probeRadius), min(screenshot.shape[0], py+probeRadius)
                                pendingPlacementProbe = {'name': action.get('name'), 'pos': tuple(legal),
                                                         'before': screenshot[probeTop:probeBottom, probeLeft:probeRight].copy()}
                                customPrint('PLACE_SEARCH ' + str(action.get('name')) + ' recorded spot ' + str(oldPos)
                                            + ' is illegal; using ' + source + ' legal spot ' + str(legal))
                            else:
                                customPrint('PLACE_SEARCH ' + str(action.get('name')) + ' no legal spot found near ' + str(action['pos']))
                            pyautogui.moveTo(action['pos'])
                            time.sleep(0.05)
                        pyautogui.click()
                        time.sleep(0.25)
                        afterClick = np.array(pyautogui.screenshot())[:, :, ::-1]
                        if confirmButtonVisible(afterClick):
                            if not confirmPlacementMode:
                                confirmPlacementMode = True
                                customPrint('PLACE_CONFIRM_MODE enabled from live check button; historical flags ignored')
                            pyautogui.click(confirmButtonPos(afterClick.shape[1]))
                            customPrint('PLACE_CONFIRM ' + str(action.get('name')) + ' pressed the placement check at ' + str(action['pos']))
                        # Let the purchase reach the cash counter before the next read judges it.
                        time.sleep(0.25)
                        customPrint('DEBUG place click sent; waiting=' + str(actionDelay))
                    elif action['action'] == 'upgrade' or action['action'] == 'retarget' or action['action'] == 'special':
                        # game hints potentially blocking monkeys
                        # Select with a visible move first. In windowed mode this
                        # also gives the game a frame to receive focus before the
                        # path hotkey is sent.
                        towerName = str(action.get('name'))
                        if hasMovingTowerPlatforms(mapConfig.get('map')):
                            tracked = towerTracker.locate(towerName, screenshot)
                            if tracked is not None:
                                newPos, inliers = tracked
                                moved = math.hypot(newPos[0] - action['pos'][0], newPos[1] - action['pos'][1])
                                if 8 * screenshot.shape[1] / 1920 < moved < 400 * screenshot.shape[1] / 1920:
                                    oldPos = tuple(action['pos'])
                                    for step in mapConfig['steps']:
                                        if str(step.get('name')) == towerName and tuple(step.get('pos', ())) == oldPos:
                                            step['pos'] = newPos
                                    action['pos'] = newPos
                                    if currentGameState is not None and towerName in currentGameState.towers:
                                        currentGameState.towers[towerName]['position'] = list(newPos)
                                    towerTracker.remember(towerName, screenshot, newPos)
                                    customPrint('TOWER_TRACK ' + towerName + ' moved with its platform ' + str(oldPos)
                                                + ' -> ' + str(newPos) + ' (' + str(inliers) + ' matched features)')
                        customPrint('DEBUG select tower at ' + str(action['pos']))
                        selectionReady = select_tower(action['pos'], lambda: np.array(pyautogui.screenshot())[:, :, ::-1].copy(),
                                                      lambda point: pyautogui.click(point), time.sleep, customPrint)
                        if selectionReady is False:
                            mapConfig['steps'].insert(0, action)
                            thisIterationAction = None
                            if routeCheckpoint is not None:
                                routeCheckpoint.update(status='ready', pendingAction=None,
                                    nextStep=checkpointStepOffset(mapConfig['steps'], routeStepTotal))
                                writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                            customPrint('SELECTION_RECOVERY held placement still active; queued tower action for a fresh frame')
                            continue
                        time.sleep(max(actionDelay, 0.35))
                        actionTmp = None
                        while action:
                            if 'to' in action:
                                customPrint('DEBUG action target move name=' + str(action.get('name')) + ' to=' + str(action['to']))
                                pyautogui.moveTo(action['to'])
                                time.sleep(smallActionDelay)
                            if action['action'] == 'click':
                                time.sleep(actionDelay)
                                customPrint('DEBUG nested click pos=' + str(action['pos']))
                                pyautogui.moveTo(action['pos'])
                                pyautogui.click()
                                time.sleep(actionDelay)
                            else:
                                customPrint('DEBUG nested key=' + str(action.get('key')))
                                if action['action'] == 'upgrade':
                                    action['upgradeObservation'] = observe_upgrade(
                                        action['path'],
                                        lambda: np.array(pyautogui.screenshot())[:, :, ::-1].copy(),
                                        lambda: sendKey(action['key']),
                                        lambda pos: pyautogui.click(pos), time.sleep,
                                        reselect=lambda: select_tower(action['pos'],
                                            lambda: np.array(pyautogui.screenshot())[:, :, ::-1].copy(),
                                            lambda point: pyautogui.click(point), time.sleep, customPrint),
                                        expected_tiers=action.get('expectedUpgradeTiers'))
                                    customPrint('DEBUG upgrade panel observation tower=' + str(action.get('name'))
                                                + ' path=' + str(action['path']) + ' ' + str(action['upgradeObservation']))
                                    if action['upgradeObservation']['status'] != 'confirmed':
                                        # Capture while the selected panel is still visible, before
                                        # right-click closes it. End-of-run images lose this evidence.
                                        try:
                                            os.makedirs(FAILURE_SHOT_DIR, exist_ok=True)
                                            stem = os.path.join(FAILURE_SHOT_DIR, 'upgrade_' + str(time.time_ns()))
                                            frame = np.array(pyautogui.screenshot())[:, :, ::-1].copy()
                                            if not cv2.imwrite(stem + '.png', frame):
                                                raise OSError('could not encode upgrade evidence')
                                            evidence = {
                                                'map': mapConfig.get('map'), 'mode': mapConfig.get('gamemode'),
                                                'round': currentValues.get('round'), 'cash': currentValues.get('money'),
                                                'tower': action.get('name'), 'position': action.get('pos'),
                                                'path': action.get('path'), 'cost': action.get('cost'),
                                                'expectedTiers': action.get('expectedUpgradeTiers'),
                                                'observation': action['upgradeObservation'],
                                                'selectionAttempts': action.get('selectionAttempts', 0),
                                            }
                                            with open(stem + '.json', 'w', encoding='utf-8') as output:
                                                json.dump(evidence, output, indent=2)
                                            action['upgradeObservation']['screenshot'] = os.path.abspath(stem + '.png')
                                            customPrint('FAILURE_SHOT ' + os.path.abspath(stem + '.png')
                                                        + ' reason=upgrade-' + action['upgradeObservation']['status'])
                                        except Exception as error:
                                            customPrint('WARNING could not save upgrade evidence: ' + str(error))
                                else:
                                    sendKey(action['key'])
                                # BTD6 applies path upgrades on the next frame;
                                # do not close the tower panel immediately.
                                time.sleep(0.18)
                            if 'to' in action and mapConfig['monkeys'][action['name']]['type'] == 'mortar':
                                pyautogui.click()
                            time.sleep(smallActionDelay)
                            actionTmp = action
                            if len(mapConfig['steps']) and 'name' in mapConfig['steps'][0] and mapConfig['steps'][0]['name'] == action['name'] and (mapConfig['steps'][0]['action'] == 'retarget' or mapConfig['steps'][0]['action'] == 'special' or mapConfig['steps'][0]['action'] == 'click'):
                                action = mapConfig['steps'].pop(0)
                                customPrint('+' + action['action'])
                            else:
                                action = None
                        action = actionTmp
                        # A missed selection leaves no panel: Esc would pause the
                        # game. Right-click closes the panel without toggling pause.
                        pyautogui.click(button='right')
                    elif action['action'] == 'sell':
                        customPrint('DEBUG sell pos=' + str(action['pos']) + ' key=' + str(action['key']))
                        select_tower(action['pos'], lambda: np.array(pyautogui.screenshot())[:, :, ::-1].copy(),
                                     lambda point: pyautogui.click(point), time.sleep, customPrint)
                        time.sleep(actionDelay)
                        sendKey(action['key'])
                    elif action['action'] == 'remove':
                        customPrint('removing obstacle at ' + tupleToStr(action['pos']) + ' for ' + str(action['cost']))
                        pyautogui.moveTo(action['pos'])
                        pyautogui.click()
                        time.sleep(menuChangeDelay)
                        result = cv2.matchTemplate(np.array(pyautogui.screenshot())[:, :, ::-1].copy(), locateImages['remove_obstacle_confirm_button'], cv2.TM_SQDIFF_NORMED)
                        pyautogui.click(cv2.minMaxLoc(result)[2])
                    elif action['action'] == 'move_cursor':
                        customPrint('CURSOR_TARGET issued position=' + str(action['pos']) + ' round=' + str(currentValues.get('round')))
                        pyautogui.moveTo(action['pos'])
                    elif action['action'] == 'click':
                        customPrint('DEBUG click pos=' + str(action['pos']))
                        pyautogui.moveTo(action['pos'])
                        pyautogui.click()
                    elif action['action'] == 'press':
                        customPrint('DEBUG press key=' + str(action['key']))
                        sendKey(action['key'])
                    elif action['action'] == 'ability':
                        # The execution gate has waited while screen reads continued.
                        customPrint('DEBUG ability slot=' + str(action.get('slot')) + ' key=' + str(action['key'])
                                    + ' round_delay=' + str(action.get('timer', 0))
                                    + ' deadline=' + str(action.get('abilityDeadline'))
                                    + ' target=' + str(action.get('pos')))
                        if action.get('abilityInputSent') is True:
                            thisIterationAction = None  # Cursor continuation is not a second ability use.
                        if not issue_ability(action, time.time(), sendKey, pyautogui.moveTo, pyautogui.click):
                            mapConfig['steps'].insert(0, action)
                            customPrint('TIMING ability cursor pending slot=' + str(action.get('slot'))
                                        + ' deadline=' + str(action['cursorDeadline']))
                        else:
                            customPrint('TIMING ability completed slot=' + str(action.get('slot')))
                    elif action['action'] == 'repeat_ability':
                        repeatedAbilities.start(action['slot'], action['key'])
                        customPrint('TIMING repeat ability enabled slot=' + str(action['slot']) + ' entries=' + str(repeatedAbilities.snapshot()))
                    elif action['action'] == 'stop_ability':
                        repeatedAbilities.stop(action.get('slot'))
                        customPrint('TIMING repeat ability stopped slot=' + str(action.get('slot')) + ' entries=' + str(repeatedAbilities.snapshot()))
                    elif action['action'] == 'speed':
                        customPrint('DEBUG speed change=' + str(action['speed']))
                        if currentGameState is not None:
                            currentGameState.set_speed(action['speed'])
                        if action['speed'] == 'fast':
                            fast = True
                        elif action['speed'] == 'slow':
                            fast = False
                    elif action['action'] in ('start_round', 'speed_toggle'):
                        action['playStateConfirmed'] = True
                        fast = action['speed'] == 'fast'
                        if action['action'] == 'start_round':
                            mapConfig['roundStartCompleted'] = True
                            if routeCheckpoint is not None:
                                routeCheckpoint['roundStartCompleted'] = True
                        customPrint('ROUND_CONTROL confirmed playing speed=' + action['speed'])
                    elif action['action'] == 'await_delay':
                        customPrint('DEBUG route wait completed seconds=' + str(action['seconds']))
                    elif action['action'] == 'await_cash':
                        customPrint('DEBUG cash threshold reached=' + str(currentValues['money']) + ' requested=' + str(action['cash']))
                        if currentGameState is not None:
                            currentGameState.record_issued_action(action)
                            saveGameState(currentGameState)
                        thisIterationAction = None
                    if currentGameState is not None and thisIterationAction is not None:
                        currentGameState.record_issued_action(action)
                        saveGameState(currentGameState)
                    if routeCheckpoint is not None:
                        if action.get('action') == 'upgrade':
                            recordUpgradeCheckpoint(routeCheckpoint, action)
                        routeCheckpoint['nextStep'] = checkpointStepOffset(mapConfig['steps'], routeStepTotal)
                        routeCheckpoint['pendingAction'] = None
                        routeCheckpoint['repeatedAbilities'] = repeatedAbilities.snapshot()
                        routeCheckpoint['status'] = 'ready'
                        writeRouteCheckpoint(routeCheckpoint, mapConfig['steps'])
                        customPrint('CHECKPOINT ' + mapConfig['map'] + ' ' + mapConfig['gamemode']
                                    + ' step ' + str(routeCheckpoint['nextStep']) + '/' + str(routeStepTotal)
                                    + ' round ' + str(routeCheckpoint.get('round')))

                elif mode in [Mode.VALIDATE_PLAYTHROUGHS, Mode.VALIDATE_COSTS] and len(mapConfig['steps']) == 0 and lastIterationCost == 0:
                    state = State.UNDEFINED

                waitingForLaterRound = (
                    len(mapConfig['steps']) > 0
                    and mapConfig['steps'][0]['action'] == 'await_round'
                    and currentValues['round'] < mapConfig['steps'][0]['round']
                )
                # A placement that spent nothing is retried as the next step, but the balance check
                # below still assumes its cost was paid and started the round with nothing placed;
                # in CHIMPS/impoppable (one life) that lost at round 6 within seconds.
                placementRetryPending = ((len(mapConfig['steps']) > 0 and mapConfig['steps'][0].get('action') == 'place'
                                          and mapConfig['steps'][0].get('placeAttempts', 0) > 0)
                                         or (thisIterationAction is not None and thisIterationAction.get('action') == 'place'))
                startupRoundStartPending = (not mapConfig.get('roundStartCompleted', False)
                                            and any(step.get('action') == 'start_round' for step in mapConfig['steps']))
                # This screenshot predates the action just issued above. Let a
                # fresh frame confirm it before automatic Play/Fast Forward input.
                if (not skippingIteration and not placementRetryPending and not startupRoundStartPending and not roundStartInputIssued
                    and not (routeActionExecuted or heldPlacement or playToggleIssued)
                    and nextStepAction not in ('start_round', 'speed_toggle')
                    and ((not doAllStepsBeforeStart and mapConfig['gamemode'] != 'deflation'
                          and (waitingForLaterRound or getNextCostingAction(mapConfig['steps'])['cost'] > min(currentValues['money'], lastIterationBalance - lastIterationCost)))
                         or len(mapConfig['steps']) == 0)):
                    bestMatchDiff = None
                    gameState = None
                    for screenCfg in [
                        ('game_playing_fast', comparisonImages['game_state']['game_playing_fast'], imageAreas["compare"]["game_state"]),
                        ('game_playing_slow', comparisonImages['game_state']['game_playing_slow'], imageAreas["compare"]["game_state"]),
                        ('game_paused', comparisonImages['game_state']['game_paused'], imageAreas["compare"]["game_state"]),
                    ]:
                        diff = cv2.matchTemplate(cutImage(screenshot, screenCfg[2]), cutImage(screenCfg[1], screenCfg[2]), cv2.TM_SQDIFF_NORMED)[0][0]
                        if bestMatchDiff is None or diff < bestMatchDiff:
                            bestMatchDiff = diff
                            gameState = screenCfg[0]

                    # The closest of three templates isn't proof: a weak match here toggled a running
                    # game into pause over and over. Only act on a confident match, and not in bursts.
                    wantsToggle = ((gameState == 'game_playing_fast' and not fast)
                                   or (gameState == 'game_playing_slow' and fast)
                                   or gameState == 'game_paused')
                    if wantsToggle and bestMatchDiff < 0.05 and time.time() - lastPlayToggleAt > 3:
                        customPrint('DEBUG play toggle state=' + gameState + ' diff=' + str(round(float(bestMatchDiff), 4)) + ' fast=' + str(fast))
                        sendKey(keybinds['others']['play'])
                        lastPlayToggleAt = time.time()
                        playToggleIssued = True
                    elif wantsToggle:
                        customPrint('DEBUG play toggle skipped state=' + gameState + ' diff=' + str(round(float(bestMatchDiff), 4)))
                    
                # Repeating keys stay in this input-owning loop, never a background
                # thread. This frame predates any just-issued action: do not use it
                # to authorize another key during placement or delayed targeting.
                if repeatedAbilities.entries:
                    repeatPlaying = False
                    repeatDiff = None
                    for repeatName in ('game_playing_fast', 'game_playing_slow', 'game_paused'):
                        diff = cv2.matchTemplate(cutImage(screenshot, imageAreas['compare']['game_state']),
                                                cutImage(comparisonImages['game_state'][repeatName], imageAreas['compare']['game_state']),
                                                cv2.TM_SQDIFF_NORMED)[0][0]
                        if repeatDiff is None or diff < repeatDiff:
                            repeatDiff = diff
                            repeatPlaying = repeatName != 'game_paused'
                    cursorPending = any(step.get('abilityInputSent') is True for step in mapConfig['steps'])
                    repeatedSlot = repeatedAbilities.tick(time.monotonic(), repeatPlaying and repeatDiff < 0.05,
                                                          not (skippingIteration or routeActionExecuted or playToggleIssued
                                                               or placementRetryPending or heldPlacement or cursorPending), sendKey)
                    if repeatedSlot is not None:
                        customPrint('TIMING repeated ability issued slot=' + str(repeatedSlot) + ' round=' + str(currentValues.get('round')))
                        if currentGameState is not None:
                            currentGameState.record_issued_action({'action': 'ability', 'slot': repeatedSlot, 'repeated': True})
                lastIterationScreenshotAreas = images
                lastIterationBalance = currentValues['money']
                lastIterationCost = thisIterationCost
                lastIterationAction = thisIterationAction

                if currentValues['round'] >= 0:
                    lastIterationRound = currentValues['round']

                iterationBalances.append((currentValues['money'], thisIterationCost))
            else:
                offGameFrames = offGameFrames + 1 if screen == offGameScreen else 1
                offGameScreen = screen
                if offGameFrames < OFF_GAME_FRAMES_REQUIRED:
                    customPrint('DEBUG ignoring ' + screen.name + ' while in game (' + str(offGameFrames) + '/'
                                + str(OFF_GAME_FRAMES_REQUIRED) + '); waiting for a stable screen')
                    time.sleep(0.3)
                else:
                    customPrint("task INGAME, but not in related screen!")
                    # Keep evidence for the sweep manager, which may retry this strategy or select
                    # another route. A stable menu without a victory is never counted as a clear.
                    saveFailureShots(mapConfig, lastIngameShot, screenshot)
                    customPrint('ROUTE_FAILURE ' + json.dumps({
                        'reason': 'unexpected-screen', 'screen': screen.name,
                        'map': mapConfig.get('map'), 'mode': mapConfig.get('gamemode'),
                        'round': lastIterationRound, 'action': lastIterationAction,
                    }, default=str))
                    customPrint('WARNING unexpected stable screen ' + screen.name + ' during gameplay; saving evidence and handing recovery to route manager')
                    objectiveFailed = True
                    objectiveFailureReason = 'unexpected stable screen during gameplay: ' + screen.name
                    state = State.UNDEFINED
            if screen == Screen.INGAME:
                offGameScreen = None
                offGameFrames = 0
        else:
            state = State.UNDEFINED
            lastStateTransitionSuccessful = False

        if state != lastState:
            customPrint("new state " + state.name + "!")

        lastScreen = screen
        lastState = state

        time.sleep(actionDelay if state == State.INGAME else menuChangeDelay)

if __name__ == "__main__":
    sys.exit(main() or 0)
