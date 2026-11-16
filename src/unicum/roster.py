"""Cached WNX presentation shared by Tab and Scaleform roster rows."""
import math

from unicum import badges

SURFACE = 'battle'

def wnx_data(entry, window, scales):
    """(raw WNX, WNX field) from the cached account and site scale."""
    if entry is None:
        return None, {'wnxAvailable': False}
    value = entry.rating('wnx', window)
    if value is None or math.isnan(value) or math.isinf(value):
        return None, {'wnxAvailable': False}
    band_color = scales.color('wnx', value) if scales is not None else None
    color = scales.text_color('wnx', value) if scales is not None else None
    return value, {'wnx': int(round(value)), 'color': color,
                   'bandColor': band_color, 'wnxAvailable': True}


def tab_battles(value):
    """Compact Tab battles to tenths of a thousand from 100 battles upward."""
    try:
        battles = max(0, int(round(value)))
    except (TypeError, ValueError, OverflowError):
        return None
    if battles < 100:
        return str(battles)
    tenths = (battles + 50) // 100
    whole, decimal = divmod(tenths, 10)
    if decimal:
        return '%d.%dk' % (whole, decimal)
    return '%dk' % whole


def battle_stats(entry, settings):
    """Available battle count and win rate, formatted as the original mod shows them."""
    if entry is None:
        return {}
    out = {}
    for key in ('battles', 'winrate'):
        window = settings.extra(key, SURFACE)
        if window is None:
            continue
        value = entry.stat(key, window)
        if value is None or math.isnan(value) or math.isinf(value):
            continue
        if key == 'battles':
            out[key] = tab_battles(value)
        else:
            out[key] = badges.winrate(value, settings.winrate_decimal())
    return out


def row_data(entry, settings, scales):
    value, data = wnx_data(entry, settings.window_of('wnx'), scales)
    if settings.shows('battle'):
        data.update(battle_stats(entry, settings))
    return data


def marker_text(markers):
    """Stable tab-separated payload for the existing Scaleform bridge."""
    template = '%s\t%s\t%d\t%s\t%d\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s'
    return u'\n'.join(template % ((key,) + tuple(value[:14]))
                      + (u'\t' + u'\t'.join(value[14:]) if len(value) > 14 else u'')
                      for key, value in sorted(markers.items()))


def native_name_fields(data):
    """The client stats exchange's untruncated name inputs, not API aliases."""
    if not isinstance(data, dict) or 'playerName' not in data:
        return ['', '', '', '', '', '']
    fields = [data.get(key) or '' for key in
              ('playerName', 'playerFakeName', 'clanAbbrev', 'region')]
    fields.append(','.join(data.get('userTags') or []))
    # Presence is separate: an empty playerName is an intentional client value.
    return fields + ['1']
