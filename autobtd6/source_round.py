"""Source logical-round clocks, separate from the observed BTD6 HUD counter."""
from copy import deepcopy
from math import isfinite


def valid_time(value):
    return type(value) in (int, float) and isfinite(value)


def source_round_anchor(config, observed_anchor):
    if not config.get('sourceRoundTiming'):
        return observed_anchor
    context = config.get('sourceRoundContext')
    return context.get('startedAt') if isinstance(context, dict) and valid_time(context.get('startedAt')) else None


def restore_source_round_context(original, checkpoint):
    """Accept clocks only for source commands already consumed in this route."""
    offset = checkpoint.get('nextStep')
    if type(offset) is not int or not 0 <= offset <= len(original):
        raise ValueError('invalid source-round checkpoint offset')
    result = {}
    for key, action in (('sourceRoundContext', 'source_round'), ('sourcePlay', 'play_once')):
        saved = checkpoint.get(key)
        if saved is None:
            continue
        if not isinstance(saved, dict):
            raise ValueError('invalid source-round checkpoint context')
        actions = ('play_once', 'play_twice') if action == 'play_once' else ('source_round',)
        index = saved.get('index')
        clock = 'startedAt' if action == 'source_round' else 'sentAt'
        if (type(index) is not int or not 0 <= index < offset
                or not isinstance(original[index], dict)
                or original[index].get('action') not in actions or not valid_time(saved.get(clock))):
            raise ValueError('source-round context does not match consumed route')
        latest = next((i for i in range(offset - 1, -1, -1)
                       if isinstance(original[i], dict) and original[i].get('action') in actions), None)
        if latest != index:
            raise ValueError('source-round context is stale')
        clean = {'index': index, clock: saved[clock]}
        if action == 'source_round':
            if type(saved.get('round')) is not int or saved['round'] != original[index].get('round'):
                raise ValueError('source logical round differs from route')
            clean['round'] = saved['round']
        result[key] = clean
    return result


def drive_source_round(config, checkpoint, now, persist=lambda: True, report=lambda message: None):
    """Commit a logical marker without changing the observed HUD round.

    The caller owns the frame and has released purchase confirmation. Logical
    markers intentionally do not wait for OCR. An after-Play marker uses the
    source runner's 0.2-second post-key clock, even when confirmation arrived
    later. Missing input evidence leaves that marker queued.
    """
    steps = config.get('steps', [])
    if not steps or steps[0].get('action') != 'source_round':
        return False
    if not valid_time(now):
        raise ValueError('source logical-round clock must be finite')
    step = steps[0]
    number = step.get('round')
    if type(number) is not int or number < 1 or type(step.get('afterPlay', False)) is not bool:
        raise ValueError('invalid source logical-round marker')
    index = step.get('routeStepIndex')
    if type(index) is not int or index < 0:
        raise ValueError('source logical-round marker needs its route index')
    anchor = now
    if step.get('afterPlay'):
        play = config.get('sourcePlay')
        if (not isinstance(play, dict) or not valid_time(play.get('sentAt'))
                or type(play.get('index')) is not int or not 0 <= play['index'] < index
                or play['index'] <= (config.get('sourceRoundContext') or {}).get('index', -1)):
            report('SOURCE_ROUND prior Play evidence missing; retaining logical marker')
            return True
        anchor = min(play['sentAt'] + 0.2, now + 0.2)
    context = {'round': number, 'startedAt': anchor, 'index': step['routeStepIndex']}
    previous = deepcopy(config.get('sourceRoundContext'))
    had_context = 'sourceRoundContext' in config
    saved_checkpoint = deepcopy(checkpoint) if checkpoint is not None else None
    config['sourceRoundContext'] = context
    steps.pop(0)
    if checkpoint is not None:
        checkpoint['sourceRoundContext'] = deepcopy(context)
    try:
        saved = persist() is True
    except Exception as error:
        report('SOURCE_ROUND checkpoint error: ' + str(error))
        saved = False
    if not saved:
        steps.insert(0, step)
        if had_context:
            config['sourceRoundContext'] = previous
        else:
            config.pop('sourceRoundContext', None)
        if checkpoint is not None:
            checkpoint.clear(); checkpoint.update(saved_checkpoint)
        report('SOURCE_ROUND checkpoint not saved; retaining logical marker')
        return True
    report('SOURCE_ROUND committed logical=' + str(number) + ' afterPlay=' + str(step.get('afterPlay', False)))
    return True
