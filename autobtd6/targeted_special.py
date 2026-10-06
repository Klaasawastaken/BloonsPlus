"""Execute a selected tower's targetable special without changing its selector."""


def perform_targeted_special(action, send_key, move_to, click, sleep):
    if action.get('action') != 'special' or len(action.get('to', ())) != 2:
        raise ValueError('Expected a special command with a target coordinate')
    send_key(action['key'])
    sleep(0.2)
    move_to(action['to'])
    sleep(0.1)
    click()
    sleep(0.2)
