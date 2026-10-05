"""Non-blocking route delays; the main loop keeps observing the live game."""
import math


def delay_ready(step, now):
    if not step or step.get('action') != 'await_delay':
        return True
    seconds = step.get('seconds')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('route delay must be finite and non-negative')
    if 'delayDeadline' not in step:
        step['delayDeadline'] = now + seconds
    deadline = step['delayDeadline']
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('invalid route delay deadline')
    step['delayDeadline'] = min(deadline, now + seconds)
    return now >= step['delayDeadline']


def round_offset_ready(step, now, observed_round, round_started_at):
    """Gate an offset against the observed round start, never a new per-action delay."""
    if not step or step.get('action') != 'await_round' or 'secondsAfterRound' not in step:
        return True
    seconds = step['secondsAfterRound']
    target = step.get('round')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('round offset must be finite and non-negative')
    if type(target) is not int or target < 1:
        raise ValueError('round offset needs a positive round')
    if type(observed_round) is not int or observed_round < target:
        return False
    # An overdue action must not stall forever after a missed transition.
    if observed_round > target:
        return True
    if type(round_started_at) not in (int, float) or not math.isfinite(round_started_at):
        return False
    return now >= round_started_at + seconds


def ability_ready(step, now, round_started_at):
    """Hold ability input in the main loop without blocking screen observation.

    Pin the first observed deadline so a later round transition cannot extend
    the wait. With no known round anchor, preserve legacy immediate execution.
    """
    if not step or step.get('action') != 'ability':
        return True
    if step.get('abilityInputSent') is True:
        deadline = step.get('cursorDeadline')
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            raise ValueError('invalid ability cursor deadline')
        return now >= deadline
    seconds = step.get('timer', 0)
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('ability timer must be finite and non-negative')
    if 'abilityDeadline' not in step:
        anchor = round_started_at
        if type(anchor) not in (int, float) or not math.isfinite(anchor):
            return True
        step['abilityDeadline'] = anchor + seconds
    deadline = step['abilityDeadline']
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('invalid ability deadline')
    return now >= deadline


def issue_ability(step, now, press, move, click):
    """Send once, then optionally defer cursor movement without sleeping.

    Delayed targeting preserves the recorded move-only behavior. Immediate
    targeting preserves move-and-click behavior.
    """
    delay = step.get('cursor_delay', 0)
    if type(delay) not in (int, float) or not math.isfinite(delay) or delay < 0:
        raise ValueError('ability cursor delay must be finite and non-negative')
    target = step.get('pos')
    if step.get('abilityInputSent') is True:
        if not ability_ready(step, now, None):
            return False
        if target is not None:
            move(target)
        return True
    press(step['key'])
    if target is not None:
        if delay:
            step['abilityInputSent'] = True
            step['cursorDeadline'] = now + delay
            return False
        move(target)
        click()
    return True


def upgrade_ready(step, observed_round):
    """Keep a temporarily unavailable upgrade ahead of its dependent actions."""
    if not step or step.get('action') != 'upgrade' or 'deferredUpgradeRound' not in step:
        return True
    target = step['deferredUpgradeRound']
    if type(target) is not int or target < 1:
        raise ValueError('invalid deferred upgrade round')
    return type(observed_round) is int and observed_round >= target


class RepeatedAbilities:
    """Main-loop key scheduler; no worker thread can race placement input.

    BloonsPlayer's implementation keeps repeats until explicit cancellation
    (despite its README mentioning round end). Entries are a multiset: adding
    the same slot twice repeats it twice per cycle; stop removes one entry.
    A cycle lasts at least one second, without catch-up bursts after a pause.
    Checkpoints store slots only, never clock values or arbitrary input keys.
    """
    def __init__(self):
        self.entries = []
        self.index = 0
        self.next_at = None

    def start(self, slot, key):
        if type(slot) is not int or not 1 <= slot <= 10:
            raise ValueError('repeat ability needs a slot from 1 to 10')
        if not (isinstance(key, str) and key or type(key) is int and 0 <= key <= 255):
            raise ValueError('repeat ability needs a bound game key')
        self.entries.append((slot, key))

    def stop(self, slot=None):
        if slot is None:
            self.entries.clear()
        else:
            if type(slot) is not int or not 1 <= slot <= 10:
                raise ValueError('stop ability needs a slot from 1 to 10')
            for index, entry in enumerate(self.entries):
                if entry[0] == slot:
                    self.entries.pop(index)
                    break
        self.index = 0
        self.next_at = None

    def snapshot(self):
        return [slot for slot, _ in self.entries]

    def restore(self, slots, keys):
        if not isinstance(slots, list) or any(type(slot) is not int or not 1 <= slot <= 10 for slot in slots):
            raise ValueError('invalid checkpoint repeat abilities')
        restored = RepeatedAbilities()
        for slot in slots:
            restored.start(slot, keys.get(slot))
        self.entries = restored.entries
        self.index = 0
        self.next_at = None

    def tick(self, now, playing, input_free, press):
        if type(now) not in (int, float) or not math.isfinite(now):
            raise ValueError('invalid repeat ability clock')
        if not self.entries:
            self.next_at = None
            return None
        if not playing or not input_free:
            return None
        if self.next_at is not None and now < self.next_at:
            return None
        self.index %= len(self.entries)
        slot, key = self.entries[self.index]
        press(key)
        self.index = (self.index + 1) % len(self.entries)
        self.next_at = now + 1 / len(self.entries)
        return slot
