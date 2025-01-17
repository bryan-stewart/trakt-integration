"""Platform for sensor integration."""
import logging
from datetime import timedelta

from homeassistant.helpers.entity import Entity

from .configuration import Configuration
from .const import DOMAIN
from .models.kind import BASIC_KINDS, NEXT_TO_WATCH_KINDS, TraktKind

LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN]["instances"]["coordinator"]
    configuration = Configuration(hass.data)

    sensors = []

    for trakt_kind in TraktKind:
        identifier = trakt_kind.value.identifier
        for all_medias in [False, True]:
            if configuration.upcoming_identifier_exists(identifier, all_medias):
                sensor = TraktSensor(
                    hass=hass,
                    config_entry=config_entry,
                    coordinator=coordinator,
                    trakt_kind=trakt_kind,
                    source="all_upcoming" if all_medias else "upcoming",
                    prefix="Trakt All Upcoming" if all_medias else "Trakt Upcoming",
                    mdi_icon="mdi:calendar",
                )
                sensors.append(sensor)

        if trakt_kind not in BASIC_KINDS:
            continue

        if configuration.recommendation_identifier_exists(identifier):
            sensor = TraktSensor(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                trakt_kind=trakt_kind,
                source="recommendation",
                prefix="Trakt Recommendation",
                mdi_icon="mdi:movie",
            )
            sensors.append(sensor)

    for trakt_kind in TraktKind:
        if trakt_kind not in NEXT_TO_WATCH_KINDS:
            continue

        identifier = trakt_kind.value.identifier

        if configuration.next_to_watch_identifier_exists(identifier):
            sensor = TraktSensor(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                trakt_kind=trakt_kind,
                source=identifier,
                prefix="Trakt Next To Watch",
                mdi_icon="mdi:calendar",
            )
            sensors.append(sensor)

    for index, list in enumerate(configuration.get_list_configs()):
        sensor = ListSensor(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            config=list,
            source="list",
            index=index,
            prefix="Trakt List",
            mdi_icon="mdi:format-list-group",
        )
        sensors.append(sensor)

    async_add_entities(sensors)


class BaseSensor(Entity):
    """Representation of a trakt sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass,
        config_entry,
        coordinator,
        source: str,
        prefix: str,
        mdi_icon: str,
    ):
        """Initialize the sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator
        self.source = source
        self.prefix = prefix
        self.mdi_icon = mdi_icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return max([len(self.data) - 1, 0])

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self.mdi_icon

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {"data": self.data}

    @property
    def has_entity_name(self) -> bool:
        """Return if the name of the entity is describing only the entity itself."""
        return True

    async def async_update(self):
        """Request coordinator to update data."""
        await self.coordinator.async_request_refresh()


class TraktSensor(BaseSensor):
    """Representation of a trakt sensor."""

    def __init__(
        self,
        hass,
        config_entry,
        coordinator,
        trakt_kind: TraktKind,
        source: str,
        prefix: str,
        mdi_icon: str,
    ):
        """Initialize the sensor."""
        super().__init__(hass, config_entry, coordinator, source, prefix, mdi_icon)
        self.trakt_kind = trakt_kind

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.prefix} {self.trakt_kind.value.name}"

    @property
    def medias(self):
        if self.coordinator.data:
            return self.coordinator.data.get(self.source, {}).get(self.trakt_kind, None)
        return None

    @property
    def configuration(self):
        identifier = self.trakt_kind.value.identifier
        data = self.hass.data[DOMAIN]
        source = (
            "next_to_watch" if self.trakt_kind in NEXT_TO_WATCH_KINDS else self.source
        )
        return data["configuration"]["sensors"][source][identifier]

    @property
    def data(self):
        if self.medias:
            max_medias = self.configuration["max_medias"]
            return self.medias.to_homeassistant({"sort_by": 'released'})[0 : max_medias + 1]
        return []

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self.trakt_kind.value.path.split("/")[0]


class ListSensor(BaseSensor):
    """Representation of a trakt sensor."""

    def __init__(
        self,
        hass,
        config_entry,
        coordinator,
        config: dict,
        source: str,
        index: int,
        prefix: str,
        mdi_icon: str,
    ):
        """Initialize the sensor."""
        super().__init__(hass, config_entry, coordinator, source, prefix, mdi_icon)
        self.config = config
        self.index = index

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.prefix} {self.config['id']}"

    @property
    def medias(self):
        if self.coordinator.data:
            return self.coordinator.data.get(self.source, [])[self.index]
        return None

    @property
    def configuration(self):
        data = self.hass.data[DOMAIN]
        return data["configuration"]["sensors"]["list"][self.config["id"]]

    @property
    def data(self):
        if self.medias:
            return self.medias.to_homeassistant(self.config)
        return []

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return "media"
