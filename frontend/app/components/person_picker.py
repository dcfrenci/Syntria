from nicegui import ui
from api_client.persons import PersonsClient


def full_name(p: dict) -> str:
    return f"{p['first_name']} {p['last_name']}"


class PersonPicker:
    """Search box + select; options come from the server (min 2 chars).
    `cache` (id -> person dict) is filled so callers can render details."""

    def __init__(self, label: str, cache: dict, initial_id: int | None = None):
        self.cache = cache
        self._options: dict[int, str] = {}
        if initial_id in cache:
            self._options[initial_id] = full_name(cache[initial_id])
        self.search = (
            ui.input(f"Search {label.lower()} (min 2 characters)")
            .props("outlined dense clearable debounce=300")
            .classes("w-full")
        )
        self.select = (
            ui.select(options=dict(self._options), label=label)
            .props("outlined")
            .classes("w-full")
        )
        self.search.on_value_change(self._on_search)

    async def _on_search(self, e):
        q = (e.value or "").strip()
        if len(q) < 2:
            return
        found = await PersonsClient.search_persons(q)
        for p in found:
            self.cache[p["id"]] = p
        keep = {}
        if self.select.value in self._options:
            keep = {self.select.value: self._options[self.select.value]}
        self._options = {**keep, **{p["id"]: full_name(p) for p in found}}
        self.select.set_options(self._options, value=self.select.value)

    @property
    def value(self):
        return self.select.value

    def set_person(self, person: dict) -> None:
        self.cache[person["id"]] = person
        self._options[person["id"]] = full_name(person)
        self.select.set_options(self._options, value=person["id"])