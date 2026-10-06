"""Shared, deterministic game-state and action contract for AutoBTD6 routes.

This module deliberately contains no screen input. It normalizes strategy actions and
tracks only information the runner can observe or confirm from the game UI.
"""

from copy import deepcopy
import math
import time


SUPPORTED_ACTIONS = {
    'place', 'upgrade', 'sell', 'retarget', 'special', 'remove',
    'click', 'move_cursor', 'press', 'ability', 'repeat_ability', 'stop_ability', 'speed', 'speed_toggle', 'start_round', 'await_round', 'await_cash', 'await_delay',
}
POSITION_ACTIONS = {'place', 'upgrade', 'sell', 'retarget', 'special', 'remove', 'click', 'move_cursor'}
TOWER_ACTIONS = {'place', 'upgrade', 'sell', 'retarget', 'special'}
ALLOWED_CLASS_BY_MODE = {
    'primary_only': ['primary'],
    'military_only': ['military'],
    'magic_monkeys_only': ['magic'],
}


def normalize_action(step):
    """Return a validated canonical action dict while preserving route metadata."""
    if not isinstance(step, dict):
        raise ValueError('action must be an object')
    action_type = step.get('action')
    if action_type not in SUPPORTED_ACTIONS:
        raise ValueError('unsupported action: ' + str(action_type))
    action = deepcopy(step)
    action['kind'] = action_type
    if action_type == 'await_delay':
        seconds = action.get('seconds')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError('await_delay needs finite non-negative seconds')
    if action_type == 'await_round' and 'secondsAfterRound' in action:
        seconds = action['secondsAfterRound']
        if type(action.get('round')) is not int or action['round'] < 1:
            raise ValueError('round offset needs a positive round')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError('round offset needs finite non-negative seconds')
    if action_type in POSITION_ACTIONS:
        point = action.get('pos')
        if not isinstance(point, (tuple, list)) or len(point) != 2:
            raise ValueError(action_type + ' action needs a two-coordinate position')
        if not all(type(value) in (int, float) and math.isfinite(value) for value in point):
            raise ValueError(action_type + ' action position must contain finite coordinates')
        action['pos'] = tuple(point)
    if action_type in TOWER_ACTIONS and not isinstance(action.get('name'), str):
        raise ValueError(action_type + ' action needs a tower name')
    valid_key = isinstance(action.get('key'), str) or (
        isinstance(action.get('key'), int) and not isinstance(action.get('key'), bool)
        and 0 <= action['key'] <= 255
    )
    if action_type in {'place', 'upgrade', 'sell', 'retarget', 'special'} and not valid_key:
        raise ValueError(action_type + ' action needs a game key')
    if action_type in {'press', 'ability', 'repeat_ability'} and not valid_key:
        raise ValueError(action_type + ' action needs a game key')
    if action_type in {'repeat_ability', 'stop_ability'}:
        slot = action.get('slot')
        if not (action_type == 'stop_ability' and slot is None) and (type(slot) is not int or not 1 <= slot <= 10):
            raise ValueError(action_type + ' needs a slot from 1 to 10')
    if action_type == 'ability':
        point = action.get('pos')
        if point is not None:
            if not isinstance(point, (tuple, list)) or len(point) != 2:
                raise ValueError('ability target needs a two-coordinate position')
            if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in point):
                raise ValueError('ability target must contain finite coordinates')
            action['pos'] = tuple(point)
        for field in ('timer', 'cursor_delay'):
            value = action.get(field, 0)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('ability ' + field + ' must be a non-negative number')
    if action_type == 'upgrade':
        path = action.get('path')
        if not isinstance(path, int) or path < 0 or path > 2:
            raise ValueError('upgrade path must be 0, 1, or 2')
    if action_type == 'await_round' and (not isinstance(action.get('round'), int) or action['round'] < 1):
        raise ValueError('await_round needs a positive round number')
    if action_type == 'await_cash' and (not isinstance(action.get('cash'), int) or action['cash'] < 0):
        raise ValueError('await_cash needs a non-negative cash amount')
    if action_type in ('speed', 'start_round') and action.get('speed') not in {'fast', 'slow'}:
        raise ValueError('speed action must select fast or slow')
    if action_type == 'speed_toggle' and action.get('speed') not in {None, 'fast', 'slow'}:
        raise ValueError('relative speed intent must select fast or slow')
    return action


def place_tower(name, tower_type, position, key, cost):
    return normalize_action({'action': 'place', 'name': name, 'type': tower_type, 'pos': position, 'key': key, 'cost': cost})


def upgrade_tower(name, path, position, key, cost):
    return normalize_action({'action': 'upgrade', 'name': name, 'path': path, 'pos': position, 'key': key, 'cost': cost})


def sell_tower(name, position, key, value=0):
    return normalize_action({'action': 'sell', 'name': name, 'pos': position, 'key': key, 'cost': -abs(value)})


def change_targeting(name, position, key, target=None):
    action = {'action': 'retarget', 'name': name, 'pos': position, 'key': key}
    if target is not None:
        action['to'] = target
    return normalize_action(action)


def use_ability(name, position, key):
    return normalize_action({'action': 'special', 'name': name, 'pos': position, 'key': key, 'cost': 0})


def start_round(key):
    return normalize_action({'action': 'press', 'key': key, 'cost': 0})


def wait_for_round(round_number):
    return normalize_action({'action': 'await_round', 'round': round_number, 'cost': 0})


def wait_for_cash(amount):
    return normalize_action({'action': 'await_cash', 'cash': amount, 'cost': 0})


class GameState:
    """Current run state, updated from OCR and confirmed route actions."""

    def __init__(self, map_config, run_id):
        self.run_id = str(run_id)
        self.map = map_config.get('map')
        self.difficulty = map_config.get('difficulty')
        self.mode = map_config.get('gamemode')
        self.mode_restrictions = {'allowedTowerClasses': ALLOWED_CLASS_BY_MODE[self.mode]} if self.mode in ALLOWED_CLASS_BY_MODE else {}
        self.hero = map_config.get('hero')
        self.round = None
        self.cash = None
        self.lives = None
        self.speed = None
        self.speed_status = 'unknown'
        self.screen = 'INGAME'
        self.result = None
        self.towers = {}
        self.events = []
        self.observations = []
        self._last_observation = None
        self._last_observation_at = 0.0
        self.started_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.updated_at = self.started_at

    def observe(self, cash=None, round_number=None, screen=None):
        if isinstance(cash, int) and cash >= 0:
            self.cash = cash
        if isinstance(round_number, int) and round_number >= 0:
            self.round = round_number
        if screen:
            self.screen = str(screen)
        sample = {'cash': self.cash, 'round': self.round, 'screen': self.screen,
                  'observedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        prior = self._last_observation or {}
        now = time.monotonic()
        if (not prior or now - self._last_observation_at >= 5.0
                or sample['screen'] != prior.get('screen') or sample['round'] != prior.get('round')
                or (isinstance(sample['cash'], int) and isinstance(prior.get('cash'), int)
                    and abs(sample['cash'] - prior['cash']) >= 100)):
            self.observations.append(sample)
            # Keep a compact five-second history long enough to diagnose a stalled or failed run.
            self.observations = self.observations[-2160:]
            self._last_observation = sample
            self._last_observation_at = now
        self.updated_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

    def mark_action_uncertain(self, action, cash_before, cash_after):
        """Keep an ambiguous input in the run record without claiming it succeeded or failed."""
        name = action.get('name')
        for event in reversed(self.events):
            if (event.get('status') == 'issued-unverified' and event.get('type') == action.get('action')
                    and event.get('tower') == name and event.get('path') == action.get('path')):
                event.update({'status': 'cash-ambiguous', 'cashBefore': cash_before,
                              'cashAfter': cash_after, 'round': self.round,
                              'checkedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
                if isinstance(action.get('upgradeObservation'), dict):
                    event['upgradeObservation'] = dict(action['upgradeObservation'])
                self.updated_at = event['checkedAt']
                return

    def confirm_purchase(self, action, map_config, cash_before, cash_after):
        action_type = action.get('action')
        if action_type not in {'place', 'upgrade'}:
            return
        name = str(action.get('name', 'unknown'))
        config = map_config.get('monkeys', {}).get(name, {})
        tower = self.towers.setdefault(name, {
            'type': config.get('type') or action.get('type'),
            'position': config.get('pos') or action.get('pos'),
            'upgrades': [0, 0, 0],
            'targeting': None,
            'abilitiesUsed': 0,
        })
        if action_type == 'upgrade':
            path = action['path']
            observation = action.get('upgradeObservation', {})
            if observation.get('status') == 'confirmed':
                tower['upgrades'] = list(observation['after'])
            else:
                tower['upgrades'][path] = min(5, tower['upgrades'][path] + 1)
        event = {
            'type': action_type,
            'status': 'panel-tier-confirmed' if action.get('upgradeObservation', {}).get('status') == 'confirmed' else 'cash-confirmed',
            'tower': name,
            'towerType': tower.get('type'),
            'position': list(tower.get('position') or []),
            'path': action.get('path'),
            'upgradeLevel': tower['upgrades'][action['path']] if action_type == 'upgrade' else None,
            'round': self.round,
            'cashBefore': cash_before,
            'cashAfter': cash_after,
            'cost': cash_before - cash_after,
            'confirmedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        self.events.append(event)
        self.updated_at = event['confirmedAt']

    def confirm_sale(self, action, cash_before, cash_after):
        name = str(action.get('name', 'unknown'))
        tower = self.towers.pop(name, {})
        event = {
            'type': 'sell',
            'status': 'cash-confirmed',
            'tower': name,
            'towerType': tower.get('type'),
            'round': self.round,
            'cashBefore': cash_before,
            'cashAfter': cash_after,
            'proceeds': cash_after - cash_before,
            'confirmedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        self.events.append(event)
        self.updated_at = event['confirmedAt']

    def record_issued_action(self, action):
        play_confirmed = action['action'] in ('start_round', 'speed_toggle') and action.get('playStateConfirmed') is True
        if play_confirmed:
            self.speed = action['speed']
            self.speed_status = 'play-state-confirmed'
        event = {
            'type': action['action'],
            'status': 'satisfied' if action['action'] in {'await_round', 'await_cash'} else 'issued-unverified',
            'tower': action.get('name'),
            'path': action.get('path'),
            'round': self.round,
            'position': list(action['pos']) if action.get('pos') is not None else None,
            'issuedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        if play_confirmed:
            event.update(status='play-state-confirmed', speed=action['speed'])
        if action['action'] in {'ability', 'repeat_ability', 'stop_ability'}:
            event['slot'] = action.get('slot')
            event['repeated'] = action.get('repeated') is True
            if action['action'] == 'repeat_ability':
                event['status'] = 'scheduled'
            elif action['action'] == 'stop_ability':
                event['status'] = 'cancelled'
        if action.get('action') == 'upgrade' and isinstance(action.get('expectedUpgradeTiers'), (list, tuple)):
            event['expectedUpgradeTiers'] = list(action['expectedUpgradeTiers'])
        self.events.append(event)
        self.updated_at = event['issuedAt']

    def set_speed(self, speed):
        self.speed = speed
        self.speed_status = 'requested-unverified'
        self.updated_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

    def finish(self, result):
        if result not in {'victory', 'defeat'}:
            raise ValueError('result must be victory or defeat')
        self.result = result
        self.screen = 'VICTORY_SUMMARY' if result == 'victory' else 'DEFEAT'
        self.updated_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

    def to_dict(self):
        return {
            'schemaVersion': 1,
            'runId': self.run_id,
            'map': self.map,
            'difficulty': self.difficulty,
            'mode': self.mode,
            'modeRestrictions': deepcopy(self.mode_restrictions),
            'round': self.round,
            'cash': self.cash,
            'lives': self.lives,
            'hero': self.hero,
            'towers': deepcopy(self.towers),
            'speed': self.speed,
            'speedStatus': self.speed_status,
            'screen': self.screen,
            'result': self.result,
            'events': deepcopy(self.events),
            'observations': deepcopy(self.observations),
            'startedAt': self.started_at,
            'updatedAt': self.updated_at,
            'source': 'autobtd6-observed-and-confirmed',
        }
