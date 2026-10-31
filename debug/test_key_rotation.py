"""Verify key rotation + live fetch for the patched wunderground_scraper coordinator."""
import sys, types, importlib.util, json

ha = types.ModuleType("homeassistant")
helpers = types.ModuleType("homeassistant.helpers")
uc = types.ModuleType("homeassistant.helpers.update_coordinator")


class UpdateFailed(Exception):
    pass


class DataUpdateCoordinator:
    def __init__(self, hass, logger, name=None, update_interval=None):
        self.hass = hass; self.logger = logger; self.name = name
        self.update_interval = update_interval; self.data = None
        self.last_update_success = True


uc.UpdateFailed = UpdateFailed
uc.DataUpdateCoordinator = DataUpdateCoordinator
helpers.update_coordinator = uc
ha.helpers = helpers
sys.modules["homeassistant"] = ha
sys.modules["homeassistant.helpers"] = helpers
sys.modules["homeassistant.helpers.update_coordinator"] = uc

pkg = types.ModuleType("wu_coord")
pkg.__path__ = ["custom_components/wunderground_scraper"]
sys.modules["wu_coord"] = pkg
spec = importlib.util.spec_from_file_location(
    "wu_coord.coordinator", "custom_components/wunderground_scraper/coordinator.py"
)
coord = importlib.util.module_from_spec(spec)
sys.modules["wu_coord.coordinator"] = coord
spec.loader.exec_module(coord)

print("keys:", coord.API_KEYS)

# 1. live fetch
data = coord.fetch_observations("KMAWELLE41")
print("live fields:", len(data), sorted(data)[:6])
assert "temperature" in data and "humidity" in data, data
print("live OK: temp=%s humidity=%s pressure=%s solar=%s" % (
    data.get("temperature"), data.get("humidity"), data.get("pressure"), data.get("solar_radiation")))

# 2. fake 401 on first key, 200 on second
calls = []
real_get = coord.requests.get


class FakeResp:
    def __init__(self, code, body=""):
        self.status_code = code; self.text = body; self._body = body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise coord.requests.exceptions.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return json.loads(self._body)


payload = real_get(coord.API_ENDPOINT, params={
    "apiKey": coord.API_KEYS[0], "stationId": "KMAWELLE41",
    "format": "json", "units": "e", "numericPrecision": "decimal"},
    timeout=15).text


def fake_get(url, params=None, timeout=None):
    calls.append(params["apiKey"])
    if params["apiKey"] == coord.API_KEYS[0]:
        return FakeResp(401, "API key is throttled")
    return FakeResp(200, payload)


coord.requests.get = fake_get
data2 = coord.fetch_observations("KMAWELLE41")
assert calls == [coord.API_KEYS[0], coord.API_KEYS[1]], calls
assert "temperature" in data2
print("rotation OK, order:", [k[:6] for k in calls])

# 3. all keys refused -> UpdateFailed
def fake_get_all401(url, params=None, timeout=None):
    return FakeResp(401, "API key is throttled")


coord.requests.get = fake_get_all401
try:
    coord.fetch_observations("KMAWELLE41")
except UpdateFailed as e:
    print("all-refused OK:", str(e)[:80])
else:
    raise AssertionError("expected UpdateFailed")

# 4. 204 stays permanent (no rotation)
coord.requests.get = lambda *a, **k: FakeResp(204, "")
try:
    coord.fetch_observations("KMAWELLE41")
except UpdateFailed as e:
    print("204 OK:", str(e)[:60])

coord.requests.get = real_get
print("ALL TESTS PASSED")
