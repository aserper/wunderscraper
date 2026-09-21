"""Standalone tests for the retry + stale-hold logic in coordinator.py.

Runs without Home Assistant by stubbing the two HA modules the coordinator
imports. Verifies against the real (currently flaky) Weather.com endpoint, and
against synthetic failures.
"""
import asyncio
import sys
import types


def _install_ha_stubs():
    """Stub the homeassistant modules coordinator.py imports."""
    ha = types.ModuleType("homeassistant")
    helpers = types.ModuleType("homeassistant.helpers")
    uc = types.ModuleType("homeassistant.helpers.update_coordinator")

    class UpdateFailed(Exception):
        pass

    class DataUpdateCoordinator:
        def __init__(self, hass, logger, name=None, update_interval=None):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data = None
            self.last_update_success = True

    uc.UpdateFailed = UpdateFailed
    uc.DataUpdateCoordinator = DataUpdateCoordinator
    helpers.update_coordinator = uc
    ha.helpers = helpers
    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.update_coordinator"] = uc
    return UpdateFailed


sys.path.insert(0, "/tmp/wu")
sys.path.insert(0, "/tmp/wu/custom_components")

UpdateFailed = _install_ha_stubs()

# Import coordinator.py as a submodule of a synthetic package so its relative
# `from .const import DOMAIN` resolves.
import importlib.util

pkg = types.ModuleType("wu_coord")
pkg.__path__ = ["/tmp/wu/custom_components/wunderground_scraper"]
sys.modules["wu_coord"] = pkg

spec = importlib.util.spec_from_file_location(
    "wu_coord.coordinator",
    "/tmp/wu/custom_components/wunderground_scraper/coordinator.py",
)
coord = importlib.util.module_from_spec(spec)
sys.modules["wu_coord.coordinator"] = coord
spec.loader.exec_module(coord)

STATION = "KMAWELLE41"
failures = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f"  {detail}" if detail else ""))
    if not condition:
        failures.append(name)


# ---------------------------------------------------------------- unit tests
print("\n=== station ID extraction ===")
cases = [
    ("https://www.wunderground.com/dashboard/pws/KMAWELLE41", "KMAWELLE41"),
    ("https://www.wunderground.com/weather/us/ma/wellesley/KMAWELLE41", "KMAWELLE41"),
    ("KMAWELLE41", "KMAWELLE41"),
    ("", None),
    (None, None),
    ("https://example.com/nothing", None),
]
for url, expected in cases:
    got = coord.extract_station_id(url)
    check(f"extract {url!r} -> {expected!r}", got == expected, f"got {got!r}")

print("\n=== celsius conversion ===")
for f, c in [(32, 0.0), (212, 100.0), (59.2, 15.1), (None, None)]:
    got = coord.fahrenheit_to_celsius(f)
    check(f"{f}F -> {c}C", got == c, f"got {got!r}")


# ------------------------------------------------------- synthetic retry test
print("\n=== retry: succeeds after transient failures ===")


async def test_retry_succeeds():
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise coord.TransientFetchError("simulated drop")
        return {"temperature": 59.2}

    result = await coord.fetch_with_retry(flaky, attempts=3, backoff=0)
    check("returns value on 3rd attempt", result == {"temperature": 59.2})
    check("made exactly 3 attempts", calls["n"] == 3, f"made {calls['n']}")


print("\n=== retry: non-transient failure is not retried ===")


async def test_no_retry_on_permanent():
    calls = {"n": 0}

    async def permanent():
        calls["n"] += 1
        raise UpdateFailed("station silent (204)")

    try:
        await coord.fetch_with_retry(permanent, attempts=3, backoff=0)
        check("raised UpdateFailed", False, "no exception raised")
    except UpdateFailed:
        check("raised UpdateFailed", True)
    check("attempted only once", calls["n"] == 1, f"made {calls['n']} attempts")


print("\n=== retry: exhausts attempts and raises ===")


async def test_exhaustion():
    calls = {"n": 0}

    async def always_transient():
        calls["n"] += 1
        raise coord.TransientFetchError("always down")

    try:
        await coord.fetch_with_retry(always_transient, attempts=3, backoff=0)
        check("raised after exhaustion", False, "no exception raised")
    except coord.TransientFetchError:
        check("raised after exhaustion", True)
    check("tried all 3 attempts", calls["n"] == 3, f"made {calls['n']}")


for t in (test_retry_succeeds, test_no_retry_on_permanent, test_exhaustion):
    asyncio.run(t())


# ----------------------------------------------------- real endpoint, real flak
print("\n=== REAL endpoint: single attempt vs retried (this is the live bug) ===")

N = 30
CONCURRENCY = 6


async def _probe_one():
    """One un-retried poll and one retried poll, run concurrently."""
    loop = asyncio.get_event_loop()

    async def single():
        try:
            await loop.run_in_executor(None, coord.fetch_observations, STATION)
            return True
        except Exception:
            return False

    async def retried():
        try:
            await coord.fetch_with_retry(
                lambda: loop.run_in_executor(None, coord.fetch_observations, STATION),
                attempts=3,
                backoff=1,
            )
            return True
        except Exception:
            return False

    return await asyncio.gather(single(), retried())


async def _run_live():
    sem = asyncio.Semaphore(CONCURRENCY)

    async def guarded():
        async with sem:
            return await _probe_one()

    return await asyncio.gather(*[guarded() for _ in range(N)])


results = asyncio.run(_run_live())
single_ok = sum(1 for s, _ in results if s)
retry_ok = sum(1 for _, r in results if r)
single_fail = N - single_ok
retry_fail = N - retry_ok

print(f"  single attempt : {single_ok} ok / {single_fail} failed "
      f"({100*single_fail/N:.0f}% failure)")
print(f"  with retries   : {retry_ok} ok / {retry_fail} failed "
      f"({100*retry_fail/N:.0f}% failure)")
check("retry reduces failures", retry_fail <= single_fail,
      f"{retry_fail} vs {single_fail}")

# ------------------------------------------------------------ stale-hold logic
print("\n=== stale hold: serves last reading, then gives up ===")


class FakeHass:
    async def async_add_executor_job(self, fn, *a):
        return await asyncio.get_event_loop().run_in_executor(None, fn, *a)


async def test_stale_hold():
    c = coord.WundergroundDataUpdateCoordinator.__new__(
        coord.WundergroundDataUpdateCoordinator
    )
    c.hass = FakeHass()
    c.station_id = STATION
    c._last_good_data = None
    c._consecutive_failures = 0
    c.data = None
    c.logger = __import__("logging").getLogger("test")

    # 1. a good poll caches the reading
    data = await c._async_update_data()
    check("good poll returns data", bool(data) and "temperature" in data)
    check("good poll caches it", c._last_good_data == data)
    check("using_cached_data is False", c.using_cached_data is False)

    # 2. now force failures and confirm the last reading is served
    def boom(*a, **k):
        raise coord.TransientFetchError("simulated outage")

    c.hass.async_add_executor_job = lambda fn, *a: asyncio.sleep(0, result=boom())
    for n in range(1, coord.MAX_CONSECUTIVE_FAILURES + 1):
        got = await c._async_update_data()
        if n <= coord.MAX_CONSECUTIVE_FAILURES:
            check(f"failure #{n} still served last reading",
                  got == data and c.using_cached_data is True)
    # 3. one more failure should now raise
    try:
        await c._async_update_data()
        check("gives up after max failures", False, "no exception")
    except UpdateFailed:
        check("gives up after max failures", True)


asyncio.run(test_stale_hold())


# --------------------------------------------------------------- 204 handling
print("\n=== 204 (station silent) is permanent, not cached ===")


async def test_204():
    c = coord.WundergroundDataUpdateCoordinator.__new__(
        coord.WundergroundDataUpdateCoordinator
    )
    c.hass = FakeHass()
    c.station_id = STATION
    c._last_good_data = {"temperature": 1.0}  # pretend we had a reading
    c._consecutive_failures = 0
    c.data = None
    c.logger = __import__("logging").getLogger("test")

    def silent(*a, **k):
        raise UpdateFailed("station silent")

    c.hass.async_add_executor_job = lambda fn, *a: asyncio.sleep(0, result=silent())
    try:
        await c._async_update_data()
        check("204 raises rather than serving cache", False, "no exception")
    except UpdateFailed:
        check("204 raises rather than serving cache", True)
    check("cache cleared on permanent failure", c._last_good_data is None)


asyncio.run(test_204())

print("\n" + "=" * 60)
if failures:
    print(f"FAILURES ({len(failures)}): " + ", ".join(failures))
    sys.exit(1)
print("ALL TESTS PASSED")
