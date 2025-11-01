## A — Założenia zaczynające się na literę A

## A — Assumptions starting with letter A

# Assumptions

This file collects project assumptions for Jadlo. Each section will be headed by the next letter of the alphabet; we start with the letter "A" — below are assumptions that start with A.

- A1 — PoC architecture: The PoC backend will be implemented as a REST service in Python using FastAPI. Main PoC endpoint: POST `/route`.

- A2 — API and formats: The API uses JSON for requests and responses; route export will be in GPX format (GPX returned as a string or downloadable file).

- A3 — Map attributes: We assume OSM data contains sufficient tags for routing heuristics (e.g., `highway`, `surface`, `cycleway`). In practice tags may be missing — the logic must be resilient to missing attributes.

- A4 — Heatmap/telemetry acquisition: Real heatmaps (e.g., Strava) may require permissions or paid access; in the PoC heatmaps will be simulated (mock). In production, plan integration with an external provider or collecting telemetry internally.

- A5 — Local environment and native dependencies: The PoC uses `osmnx`, which relies on native libraries (GEOS/PROJ/GDAL). We assume the developer environment provides these libraries or that we'll use a container with preinstalled dependencies.

- A6 — Authorization and privacy: The PoC does not implement authentication or user data storage. In production, plan for authentication, anonymization, and user consent before storing routes or telemetry.

- A7 — Asynchrony and load: Computing routes with `osmnx` over large areas can be time-consuming and memory intensive; the PoC performs this synchronously over HTTP. Production should use background workers/queues or a dedicated routing server.

- A8 — Attribution and licensing: OpenStreetMap data is covered by the ODbL license — the application must provide proper attribution and comply with license terms.

- A9 — Availability / scalability: For inter-city routing the PoC may not scale. A production solution requires a dedicated routing engine (GraphHopper/Valhalla/ORS) or a hosted service.

- A10 — Imagery analysis (street view): Google Street View requires an API key and may incur costs; Mapillary is an open alternative (crowdsourced imagery). In the PoC imagery coverage checks will be mocked or based on Mapillary.

- A11 — Validation scope: The PoC assumes initial iterations are intended for validation (weighting function, parameters) and will not cover all edge cases. Unit and integration tests will be added in subsequent iterations.

---

Next step: Section "B" — collect assumptions starting with letter B (e.g., Backup & recovery, Binning heatmap, Backend infra). Add suggestions or confirm section A to proceed.