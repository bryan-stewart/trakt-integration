from datetime import datetime
from typing import Any, Dict, List

import pytz
from dateutil.tz import tzlocal
from homeassistant.helpers import config_validation as cv
from voluptuous import ALLOW_EXTRA, PREVENT_EXTRA, In, Required, Optional, Schema

from .const import DOMAIN, LANGUAGE_CODES
from .models.kind import BASIC_KINDS, NEXT_TO_WATCH_KINDS, TraktKind


def dictionary_to_schema(
    dictionary: Dict[str, Any],
    extra: str = PREVENT_EXTRA,
) -> Schema:
    return Schema(
        {
            key: dictionary_to_schema(value) if isinstance(value, dict) else value
            for key, value in dictionary.items()
        },
        extra=extra,
    )


def domain_schema() -> Schema:
    return {
        DOMAIN: {
            "sensors": sensors_schema(),
            Required("language", default="en"): In(LANGUAGE_CODES),
            Required("timezone", default=datetime.now(tzlocal()).tzname()): In(
                pytz.all_timezones_set
            ),
        }
    }


def sensors_schema() -> Dict[str, Any]:
    return {
        "upcoming": upcoming_schema(),
        "all_upcoming": upcoming_schema(),
        "next_to_watch": next_to_watch_schema(),
        "recommendation": recommendation_schema(),
        "list": lists_schema(),
    }


def upcoming_schema() -> Dict[str, Any]:
    subschemas = {}
    for trakt_kind in TraktKind:
        subschemas[trakt_kind.value.identifier] = {
            Required("days_to_fetch", default=30): cv.positive_int,
            Required("max_medias", default=3): cv.positive_int,
        }

    return subschemas


def next_to_watch_schema() -> Dict[str, Any]:
    subschemas = {}
    for trakt_kind in NEXT_TO_WATCH_KINDS:
        subschemas[trakt_kind.value.identifier] = {
            Required("max_medias", default=3): cv.positive_int,
            Required("exclude", default=[]): list,
        }

    return subschemas


def recommendation_schema() -> Dict[str, Any]:
    subschemas = {}
    for trakt_kind in BASIC_KINDS:
        subschemas[trakt_kind.value.identifier] = {
            Required("max_medias", default=3): cv.positive_int,
        }
    return subschemas


def lists_schema() -> List:
    return [list_schema()]


def list_schema() -> Dict[str, Any]:
    return {
        Required("id"): cv.positive_int,
        Optional("sort_by"): In(["rank", "added", "released"]),
        Optional("sort_order"): In(["asc", "desc"]),
        Optional("type"): In(["shows", "movies", "episodes", "all"]),
        Optional("max_medias"): cv.positive_int,
    }


configuration_schema = dictionary_to_schema(domain_schema(), extra=ALLOW_EXTRA)
