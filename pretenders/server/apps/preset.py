import time

import bottle
from bottle import delete, post, HTTPResponse

try:
    from collections import OrderedDict
except ImportError:
    #2.6 compatibility
    from pretenders.compat.ordered_dict import OrderedDict

from collections import defaultdict

from pretenders.log import get_logger
from pretenders.constants import FOREVER
from pretenders.mock_servers.http import Preset, match_rule_from_dict
from pretenders.server import app

LOGGER = get_logger('pretenders.server.apps.preset')
PRESETS = defaultdict(OrderedDict)


def preset_count(uid):
    """
    Check whether there are any presets.
    """
    return len(PRESETS[uid])


def select_preset(uid, request):
    """
    Select a preset to respond with.

    Look through the presets for a match. If one is found pop off a preset
    response and return it.

    :param uid: The uid to look up presets for
    :param request: A dictionary representing the mock request which is checked
        to see if it matches the rule regex and headers stored in the preset.

    Return 404 if no preset found that matches.
    """
    preset_dict = PRESETS[uid]
    for key, preset_list in preset_dict.items():
        preset = preset_list[0]
        match_rule = match_rule_from_dict(preset.rule)

        if match_rule.matches(request):
            knock_off_preset(preset_dict, key)
            time.sleep(preset.after)
            return preset

    raise HTTPResponse(b"No matching preset response", status=404)


def knock_off_preset(preset_dict, key):
    """Knock a count off the preset at in list ``key`` within ``preset_dict``.

    Reduces the ``times`` paramter of a preset.
    Once the ``times`` reduces to zero it is removed.
    If ``times`` is ``FOREVER`` nothing happens.

    :param preset_dict:
        A dictionary containing preset dictionaries specific for a uid.

    :param key:
        The key pointing to the list to look up and pop an item from.
    """
    preset = preset_dict[key][0]
    if preset.times == FOREVER:
        return
    elif preset.times > 0:
        preset.times -= 1

    if preset.times == 0:
        del preset_dict[key][0]
        if not preset_dict[key]:
            del preset_dict[key]


@app.post('/preset/<uid:int>')
def add_preset(uid):
    """
    Save the incoming request body as a preset response
    """
    preset = Preset(json_data=bottle.request.body.read())
    if preset.times != FOREVER and preset.times <= 0:
        raise HTTPResponse(("Preset has {0} times. Must be greater than "
                             "zero.".format(preset.times).encode()),
                           status=400)

    rule = match_rule_from_dict(preset.rule)

    if rule not in PRESETS[uid]:
        PRESETS[uid][rule] = []
    url_presets = PRESETS[uid][rule]
    url_presets.append(preset)


@app.delete('/preset/<uid:int>')
def clear_presets(uid):
    """
    Delete all recorded presets
    """
    PRESETS[uid].clear()
