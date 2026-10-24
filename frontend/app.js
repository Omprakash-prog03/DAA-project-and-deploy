// ===================================================================
// EV Charging Station Placement & Route Planning - Real Data GIS App
// Hand-written DAA Algorithms: Kruskal MST, Dijkstra, 0/1 Knapsack
// ===================================================================

document.addEventListener('DOMContentLoaded', () => {
    // 1. STATE STORE (Clean Initial State - Zero Fake Data)
    const state = {
        currentLocation: null,
        realStations: [],
        candidates: new Map(), // stationId -> candidate object
        mstResult: null,
        dijkstraResult: null,
        knapsackResult: null,
        activeTab: 'mst',

        // Planning & Routing State
        isDroppingStation: false,
        pendingDropCoords: null,
        dijkstraMode: 'stations', // 'stations' | 'mapclick'
        pickingMode: null, // null | 'origin' | 'destination'
        pickedOrigin: null, // { lat, lon, marker }
        pickedDest: null // { lat, lon, marker }
    };

    // 2. INITIALIZE REAL EARTH LEAFLET MAP
    const map = L.map('map', {
        zoomControl: true,
        attributionControl: true
    }).setView([20.5937, 78.9629], 5); // Centered on India overview

    // 3. TILE LAYERS (Google Earth Satellite, Google Hybrid, Carto Dark GIS, OSM Streets)
    const tileLayers = {
        'google-earth': L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
            attribution: '&copy; Google Earth Satellite Imagery',
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
            maxZoom: 20
        }),
        'google-hybrid': L.tileLayer('https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
            attribution: '&copy; Google Earth Satellite Imagery &amp; Roads',
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
            maxZoom: 20
        }),
        'carto-dark': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19
        }),
        'osm-streets': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        })
    };

    let currentTileLayer = tileLayers['carto-dark'];
    currentTileLayer.addTo(map);

    // Map Layer Groups for DAA Algorithm Visualizations
    const layers = {
        stations: L.layerGroup().addTo(map),
        candidates: L.layerGroup().addTo(map),
        mst: L.layerGroup().addTo(map),
        dijkstra: L.layerGroup().addTo(map),
        knapsack: L.layerGroup().addTo(map),
        pins: L.layerGroup().addTo(map),
        markers: L.layerGroup().addTo(map)
    };

    // Persistent marker store (shared across all users)
    const persistentMarkers = []; // { id, name, lat, lon, note, color, icon, created_at }
    const markerIcons = {};       // marker_id -> Leaflet marker

    // 4. DOM ELEMENTS
    const searchForm = document.getElementById('search-form');
    const locationInput = document.getElementById('location-input');
    const radiusSelect = document.getElementById('radius-select');
    const searchBtn = document.getElementById('search-btn');
    const resetBtn = document.getElementById('reset-btn');

    // Planning Toolbar Elements
    const dropStationToolBtn = document.getElementById('drop-station-tool-btn');
    const generateCandidatesBtn = document.getElementById('generate-candidates-btn');
    const quickDemoCityBtn = document.getElementById('quick-demo-city-btn');

    // Drawer Elements
    const stationsDrawer = document.getElementById('stations-drawer');
    const toggleDrawerBtn = document.getElementById('toggle-drawer-btn');
    const closeDrawerBtn = document.getElementById('close-drawer-btn');
    const drawerToggleText = document.getElementById('drawer-toggle-text');
    const stationsSubtitle = document.getElementById('stations-subtitle');
    const stationsEmptyState = document.getElementById('stations-empty-state');
    const stationsLoading = document.getElementById('stations-loading');
    const stationsContent = document.getElementById('stations-content');
    const stationsList = document.getElementById('stations-list');
    const selectedCounter = document.getElementById('selected-counter');
    const selectAllBtn = document.getElementById('select-all-btn');
    const deselectAllBtn = document.getElementById('deselect-all-btn');

    // Algorithm Tab Elements
    const deckTabs = document.querySelectorAll('.deck-tab');
    const tabPanes = document.querySelectorAll('.tab-pane');

    // MST Elements
    const runMstBtn = document.getElementById('run-mst-btn');
    const mstResults = document.getElementById('mst-results');
    const feederCostInput = document.getElementById('feeder-cost-input');

    // Dijkstra Elements
    const routeModeStations = document.getElementById('route-mode-stations');
    const routeModeMapclick = document.getElementById('route-mode-mapclick');
    const stationPickerContainer = document.getElementById('station-picker-container');
    const mapclickPickerContainer = document.getElementById('mapclick-picker-container');
    const dijkstraStartSelect = document.getElementById('dijkstra-start-select');
    const dijkstraEndSelect = document.getElementById('dijkstra-end-select');
    const pickOriginBtn = document.getElementById('pick-origin-btn');
    const pickDestBtn = document.getElementById('pick-dest-btn');
    const originCoordLabel = document.getElementById('origin-coord-label');
    const destCoordLabel = document.getElementById('dest-coord-label');
    const runDijkstraBtn = document.getElementById('run-dijkstra-btn');
    const dijkstraResults = document.getElementById('dijkstra-results');

    // Knapsack Elements
    const knapsackBudgetInput = document.getElementById('knapsack-budget-input');
    const runKnapsackBtn = document.getElementById('run-knapsack-btn');
    const knapsackResults = document.getElementById('knapsack-results');

    // Custom Station Modal Elements
    const customStationModal = document.getElementById('custom-station-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const cancelModalBtn = document.getElementById('cancel-modal-btn');
    const confirmStationBtn = document.getElementById('confirm-station-btn');
    const modalCoords = document.getElementById('modal-coords');
    const customNameInp = document.getElementById('custom-name-inp');
    const customCostInp = document.getElementById('custom-cost-inp');
    const customValueInp = document.getElementById('custom-value-inp');
    const customCapInp = document.getElementById('custom-cap-inp');

    // Status bar elements
    const statusPill = document.getElementById('status-pill');
    const statusText = document.getElementById('status-text');
    const statusClock = document.getElementById('status-clock');

    // 5. STATUS BAR & CLOCK
    function setStatus(kind, text) {
        // kind: 'live' | 'busy' | 'error' | 'ready'
        statusPill.className = 'status-pill' + (kind === 'busy' ? ' busy' : kind === 'error' ? ' error' : '');
        const label = kind === 'busy' ? 'Busy' : kind === 'error' ? 'Error' : 'Live';
        statusPill.innerHTML = `<span class="status-dot"></span> ${label}`;
        statusText.innerHTML = text;
    }

    function updateClock() {
        const now = new Date();
        statusClock.textContent = now.toLocaleTimeString('en-GB', { hour12: false });
    }
    updateClock();
    setInterval(updateClock, 1000);

    setStatus('live', 'Ready · Search a city to load real charging stations');

    // 6. TOAST NOTIFICATIONS
    const toastContainer = document.getElementById('toast-container');

    function showToast(kind, title, message, timeout = 5000) {
        const icons = { success: '✅', error: '⚠️', info: 'ℹ️', warning: '⚡' };
        const toast = document.createElement('div');
        toast.className = `toast toast-${kind}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[kind] || 'ℹ️'}</span>
            <div class="toast-body">
                <div class="toast-title">${escapeHtml(title)}</div>
                <div class="toast-msg">${escapeHtml(message)}</div>
            </div>
        `;
        toastContainer.appendChild(toast);
        const remove = () => {
            toast.classList.add('out');
            setTimeout(() => toast.remove(), 220);
        };
        toast.addEventListener('click', remove);
        if (timeout > 0) setTimeout(remove, timeout);
    }

    // 7. GOOGLE EARTH / TILE LAYER SWITCHER LOGIC
    document.querySelectorAll('.layer-opt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const layerKey = btn.dataset.layer;
            if (!tileLayers[layerKey] || currentTileLayer === tileLayers[layerKey]) return;

            map.removeLayer(currentTileLayer);
            currentTileLayer = tileLayers[layerKey];
            currentTileLayer.addTo(map);

            // Re-order DAA visualization layers on top
            Object.values(layers).forEach(lg => {
                if (lg.bringToFront) lg.bringToFront();
            });

            document.querySelectorAll('.layer-opt-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setStatus('live', `Map layer: ${btn.textContent.trim()}`);
        });
    });

    // 8. TAB NAVIGATION
    deckTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            deckTabs.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const pane = document.getElementById(`tab-${target}`);
            if (pane) pane.classList.add('active');
            state.activeTab = target;
        });
    });

    // Drawer Toggles
    toggleDrawerBtn.addEventListener('click', () => {
        stationsDrawer.classList.toggle('drawer-closed');
    });

    closeDrawerBtn.addEventListener('click', () => {
        stationsDrawer.classList.add('drawer-closed');
    });

    // 9. LOCATION SEARCH & REAL CHARGING STATIONS FETCH
    async function searchLocation(query) {
        if (!query) return;

        searchBtn.disabled = true;
        searchBtn.innerHTML = '<span>Searching...</span>';
        stationsDrawer.classList.remove('drawer-closed');
        stationsEmptyState.classList.add('hidden');
        stationsContent.classList.add('hidden');
        stationsLoading.classList.remove('hidden');
        setStatus('busy', `Searching real geographic data for <strong>${escapeHtml(query)}</strong>...`);

        try {
            // STEP 1: Geocode location via real geocoding service
            const geoResp = await fetch(`/api/geocode?q=${encodeURIComponent(query)}`);
            if (!geoResp.ok) {
                const err = await geoResp.json();
                throw new Error(err.detail || 'Geocoding failed');
            }
            const geoData = await geoResp.json();
            state.currentLocation = geoData;

            // Pan and zoom real map to geocoded coordinates
            map.flyTo([geoData.latitude, geoData.longitude], 12, {
                animate: true,
                duration: 1.5
            });

            // STEP 2: Query Real EV Charging Stations
            const radius = radiusSelect.value;
            const stationsResp = await fetch(
                `/api/charging-stations?lat=${geoData.latitude}&lon=${geoData.longitude}&radius=${radius}`
            );
            if (!stationsResp.ok) {
                throw new Error('Failed to retrieve charging stations from API');
            }

            const stations = await stationsResp.json();
            state.realStations = stations;
            setStatus('live', `Loaded <strong>${stations.length}</strong> real charging station(s) near <strong>${escapeHtml(query)}</strong>`);
            renderRealStations(stations);

        } catch (error) {
            showToast('error', 'Search failed', error.message, 7000);
            stationsLoading.classList.add('hidden');
            stationsEmptyState.classList.remove('hidden');
            stationsEmptyState.innerHTML = `
                <div class="empty-icon">⚠️</div>
                <h3>Search Notice</h3>
                <p>${escapeHtml(error.message)}</p>
            `;
            setStatus('error', 'Search failed — please verify your query or network connection');
        } finally {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<span>Search</span>';
        }
    }

    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        searchLocation(locationInput.value.trim());
    });

    if (quickDemoCityBtn) {
        quickDemoCityBtn.addEventListener('click', () => {
            locationInput.value = 'Bhubaneswar';
            searchLocation('Bhubaneswar');
        });
    }

    // 10. RENDER REAL CHARGING STATIONS
    function renderRealStations(stations) {
        stationsLoading.classList.add('hidden');
        layers.stations.clearLayers();
        state.candidates.clear();

        if (stations.length === 0) {
            stationsEmptyState.classList.remove('hidden');
            stationsContent.classList.add('hidden');
            stationsEmptyState.innerHTML = `
                <div class="empty-icon">⚡</div>
                <h3>No Verified Stations in Search Radius</h3>
                <p>No verified stations were found within ${radiusSelect.value} km. You can use <strong>"📍 Drop Station"</strong> or <strong>"⚡ Suggest Hubs"</strong> on the toolbar above to place candidate planning sites anywhere on the real Earth map!</p>
                <div style="margin-top: 14px;">
                    <button id="suggest-here-btn" class="secondary-btn">⚡ Suggest Regional Candidate Hubs Here</button>
                </div>
            `;
            const suggestBtn = document.getElementById('suggest-here-btn');
            if (suggestBtn) {
                suggestBtn.addEventListener('click', generateRegionalCandidateHubs);
            }
            drawerToggleText.textContent = 'Candidate Stations (0)';
            updateAlgorithmControlsState();
            return;
        }

        stationsEmptyState.classList.add('hidden');
        stationsContent.classList.remove('hidden');
        drawerToggleText.textContent = `Candidate Stations (${stations.length})`;
        stationsSubtitle.textContent = `Retrieved ${stations.length} real stations via ${stations[0].data_source}`;

        renderCandidateLedgerCards();
    }

    function renderCandidateLedgerCards() {
        stationsList.innerHTML = '';

        state.realStations.forEach((st, idx) => {
            const baseCost = 80000 + (idx % 5) * 20000;
            const baseValue = 50 + (idx % 6) * 10;

            const isAutoSelected = idx < 6;
            if (isAutoSelected && !state.candidates.has(st.id)) {
                state.candidates.set(st.id, {
                    id: st.id,
                    name: st.name,
                    latitude: st.latitude,
                    longitude: st.longitude,
                    installation_cost: baseCost,
                    expected_value: baseValue,
                    coverage_score: 1.0,
                    feeder_connection_cost: 0,
                    operator: st.operator || 'EV Network',
                    is_user_cost: true
                });
            }

            // Real Map Marker
            const marker = L.circleMarker([st.latitude, st.longitude], {
                radius: 7,
                fillColor: '#00E5FF',
                color: '#FFFFFF',
                weight: 1.5,
                opacity: 0.9,
                fillOpacity: 0.85
            }).addTo(layers.stations);

            const popupContent = `
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 12px; color: #111; max-width: 240px;">
                    <strong style="font-size: 13px; color: #0B0C0E;">${escapeHtml(st.name)}</strong><br>
                    <span style="color: #008899; font-weight: 600;">${escapeHtml(st.operator || 'Verified Station')}</span><br>
                    <span style="color: #555; font-size: 11px;">${escapeHtml(st.address || '')}</span><br>
                    <div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid #ddd; font-size: 10px; color: #777;">
                        Source: ${escapeHtml(st.data_source || 'Real API')}<br>
                        Points: ${st.number_of_points || 1}
                    </div>
                </div>
            `;
            marker.bindPopup(popupContent);

            // Card in Drawer
            const isSelected = state.candidates.has(st.id);
            const card = document.createElement('div');
            card.className = `station-card ${isSelected ? 'selected' : ''}`;
            card.id = `card-${st.id}`;
            card.innerHTML = `
                <div class="station-card-top">
                    <div class="station-card-title-group">
                        <div class="station-card-name">${escapeHtml(st.name)}</div>
                        <div class="station-card-operator">${escapeHtml(st.operator || 'Verified Station')}</div>
                    </div>
                    <label style="cursor: pointer; display: flex; align-items: center; gap: 4px; font-size: 11px; color: #F59E42;">
                        <input type="checkbox" class="candidate-chk" data-id="${st.id}" ${isSelected ? 'checked' : ''}>
                        <span>Candidate</span>
                    </label>
                </div>
                <div class="station-card-meta">
                    📍 ${escapeHtml(st.address || `${st.latitude.toFixed(4)}, ${st.longitude.toFixed(4)}`)}<br>
                    🔌 ${st.connectors && st.connectors.length > 0 ? escapeHtml(st.connectors[0].title) : 'Fast DC / AC Charging'}
                </div>
                <div class="station-parameters-grid">
                    <div class="param-input-group">
                        <label>User Install Cost (₹):</label>
                        <input type="number" class="cost-input" data-id="${st.id}" value="${state.candidates.get(st.id)?.installation_cost || baseCost}" min="10000" step="5000">
                    </div>
                    <div class="param-input-group">
                        <label>User Benefit Score:</label>
                        <input type="number" class="value-input" data-id="${st.id}" value="${state.candidates.get(st.id)?.expected_value || baseValue}" min="1" step="5">
                    </div>
                </div>
            `;

            const chk = card.querySelector('.candidate-chk');
            const costInp = card.querySelector('.cost-input');
            const valInp = card.querySelector('.value-input');

            chk.addEventListener('change', (e) => {
                if (e.target.checked) {
                    state.candidates.set(st.id, {
                        id: st.id,
                        name: st.name,
                        latitude: st.latitude,
                        longitude: st.longitude,
                        installation_cost: parseInt(costInp.value) || baseCost,
                        expected_value: parseInt(valInp.value) || baseValue,
                        coverage_score: 1.0,
                        feeder_connection_cost: 0,
                        operator: st.operator || 'EV Network',
                        is_user_cost: true
                    });
                    card.classList.add('selected');
                } else {
                    state.candidates.delete(st.id);
                    card.classList.remove('selected');
                }
                updateCandidateMarkers();
                updateAlgorithmControlsState();
            });

            costInp.addEventListener('input', (e) => {
                const c = state.candidates.get(st.id);
                if (c) c.installation_cost = parseInt(e.target.value) || 0;
            });

            valInp.addEventListener('input', (e) => {
                const c = state.candidates.get(st.id);
                if (c) c.expected_value = parseInt(e.target.value) || 0;
            });

            stationsList.appendChild(card);
        });

        updateCandidateMarkers();
        updateAlgorithmControlsState();
    }

    // Select All / Deselect All
    selectAllBtn.addEventListener('click', () => {
        document.querySelectorAll('.candidate-chk').forEach(chk => {
            if (!chk.checked) {
                chk.checked = true;
                chk.dispatchEvent(new Event('change'));
            }
        });
    });

    deselectAllBtn.addEventListener('click', () => {
        document.querySelectorAll('.candidate-chk').forEach(chk => {
            if (chk.checked) {
                chk.checked = false;
                chk.dispatchEvent(new Event('change'));
            }
        });
    });

    // 11. CANDIDATE MARKERS AND METRICS UPDATE
    function updateCandidateMarkers() {
        layers.candidates.clearLayers();
        selectedCounter.textContent = `${state.candidates.size} Candidate Sites`;
        drawerToggleText.textContent = `Candidate Stations (${state.candidates.size})`;

        state.candidates.forEach(cand => {
            const circle = L.circleMarker([cand.latitude, cand.longitude], {
                radius: 11,
                fillColor: '#F59E42',
                color: '#FFFFFF',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.75
            }).addTo(layers.candidates);

            circle.bindTooltip(`<strong>${escapeHtml(cand.name)}</strong><br>Cost: ₹${cand.installation_cost.toLocaleString()}<br>Benefit: ${cand.expected_value} pts`, {
                permanent: false,
                direction: 'top'
            });
        });

        repopulateDijkstraDropdowns();
    }

    function repopulateDijkstraDropdowns() {
        const cands = Array.from(state.candidates.values());
        dijkstraStartSelect.innerHTML = '<option value="">Select origin...</option>';
        dijkstraEndSelect.innerHTML = '<option value="">Select destination...</option>';

        cands.forEach(c => {
            const opt1 = new Option(c.name, c.id);
            const opt2 = new Option(c.name, c.id);
            dijkstraStartSelect.add(opt1);
            dijkstraEndSelect.add(opt2);
        });

        if (cands.length >= 2) {
            dijkstraStartSelect.selectedIndex = 1;
            dijkstraEndSelect.selectedIndex = 2;
        }
    }

    function updateAlgorithmControlsState() {
        const count = state.candidates.size;
        runMstBtn.disabled = count < 2;
        runKnapsackBtn.disabled = count < 1;

        if (state.dijkstraMode === 'stations') {
            runDijkstraBtn.disabled = count < 2;
            dijkstraStartSelect.disabled = count < 2;
            dijkstraEndSelect.disabled = count < 2;
        } else {
            runDijkstraBtn.disabled = !(state.pickedOrigin && state.pickedDest);
        }
    }

    // 12. INTERACTIVE EV STATION PLACEMENT ("📍 Drop Station")
    dropStationToolBtn.addEventListener('click', () => {
        state.isDroppingStation = !state.isDroppingStation;
        state.pickingMode = null;
        resetPickingButtonsUI();

        if (state.isDroppingStation) {
            dropStationToolBtn.classList.add('active');
            document.getElementById('map').classList.add('cursor-crosshair');
            setStatus('live', 'Click anywhere on the real map to place a candidate station');
        } else {
            dropStationToolBtn.classList.remove('active');
            document.getElementById('map').classList.remove('cursor-crosshair');
            setStatus('live', 'Station placement mode cancelled');
        }
    });

    // MAP CLICK DISPATCHER (Handles Dropping Stations & Picking Dijkstra Points)
    map.on('click', (e) => {
        const { lat, lng } = e.latlng;

        // A. Custom Station Drop Mode
        if (state.isDroppingStation) {
            state.pendingDropCoords = { lat, lng };
            state.isDroppingStation = false;
            dropStationToolBtn.classList.remove('active');
            document.getElementById('map').classList.remove('cursor-crosshair');

            modalCoords.textContent = `Target Coordinates: Lat ${lat.toFixed(5)}, Lon ${lng.toFixed(5)}`;
            customNameInp.value = `Candidate Hub #${state.candidates.size + 1}`;
            customCostInp.value = 120000;
            customValueInp.value = 75;
            customCapInp.value = 150;
            customStationModal.classList.remove('hidden');
            return;
        }

        // B. Dijkstra Map Pick Mode: Origin
        if (state.pickingMode === 'origin') {
            if (state.pickedOrigin?.marker) {
                layers.pins.removeLayer(state.pickedOrigin.marker);
            }

            const originMarker = L.circleMarker([lat, lng], {
                radius: 10,
                fillColor: '#3DDC84',
                color: '#FFFFFF',
                weight: 2.5,
                fillOpacity: 0.9
            }).addTo(layers.pins);
            originMarker.bindTooltip('📍 Selected Origin', { permanent: true, direction: 'top' });

            state.pickedOrigin = { lat, lon: lng, marker: originMarker };
            originCoordLabel.textContent = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            pickOriginBtn.classList.remove('picking');
            pickOriginBtn.innerHTML = '📍 Origin Picked ✓';
            state.pickingMode = null;
            document.getElementById('map').classList.remove('cursor-crosshair');

            updateAlgorithmControlsState();
            return;
        }

        // C. Dijkstra Map Pick Mode: Destination
        if (state.pickingMode === 'destination') {
            if (state.pickedDest?.marker) {
                layers.pins.removeLayer(state.pickedDest.marker);
            }

            const destMarker = L.circleMarker([lat, lng], {
                radius: 10,
                fillColor: '#FF4D4F',
                color: '#FFFFFF',
                weight: 2.5,
                fillOpacity: 0.9
            }).addTo(layers.pins);
            destMarker.bindTooltip('🏁 Selected Destination', { permanent: true, direction: 'top' });

            state.pickedDest = { lat, lon: lng, marker: destMarker };
            destCoordLabel.textContent = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            pickDestBtn.classList.remove('picking');
            pickDestBtn.innerHTML = '🏁 Destination Picked ✓';
            state.pickingMode = null;
            document.getElementById('map').classList.remove('cursor-crosshair');

            updateAlgorithmControlsState();
            return;
        }
    });

    // Custom Station Modal Handlers
    function closeModal() {
        customStationModal.classList.add('hidden');
        state.pendingDropCoords = null;
    }

    closeModalBtn.addEventListener('click', closeModal);
    cancelModalBtn.addEventListener('click', closeModal);

    confirmStationBtn.addEventListener('click', async () => {
        if (!state.pendingDropCoords) return;

        const name = customNameInp.value.trim() || `Candidate Hub #${state.candidates.size + 1}`;
        const cost = parseInt(customCostInp.value) || 120000;
        const val = parseInt(customValueInp.value) || 75;
        const id = `custom_${Date.now()}`;

        const newStation = {
            id: id,
            name: name,
            latitude: state.pendingDropCoords.lat,
            longitude: state.pendingDropCoords.lng,
            installation_cost: cost,
            expected_value: val,
            coverage_score: 1.0,
            feeder_connection_cost: 0,
            operator: 'Municipal Planned Site',
            is_user_cost: true,
            address: `Lat: ${state.pendingDropCoords.lat.toFixed(4)}, Lon: ${state.pendingDropCoords.lng.toFixed(4)}`
        };

        state.candidates.set(id, newStation);
        state.realStations.push(newStation);

        // Save as a persistent marker visible to everyone
        const saved = await saveMarker(
            name,
            state.pendingDropCoords.lat,
            state.pendingDropCoords.lng,
            `Cost: ₹${cost} | Benefit: ${val} pts`,
            '#F59E42',
            '📌'
        );

        closeModal();
        stationsEmptyState.classList.add('hidden');
        stationsContent.classList.remove('hidden');
        stationsDrawer.classList.remove('drawer-closed');

        renderCandidateLedgerCards();
        updateCandidateMarkers();
        updateAlgorithmControlsState();
        showToast('success', 'Candidate station placed', `${name} added to your planning set at (${newStation.latitude.toFixed(4)}, ${newStation.longitude.toFixed(4)})`);
        setStatus('live', `Placed candidate station <strong>${escapeHtml(name)}</strong> on the real map`);
    });

    // 13. REGIONAL CANDIDATE HUBS GENERATOR ("⚡ Suggest Hubs")
    function generateRegionalCandidateHubs() {
        const center = map.getCenter();
        const lat = center.lat;
        const lng = center.lng;

        const hubs = [
            { dLat: 0.038, dLng: 0.000, name: "North Expressway Fast Hub", cost: 130000, val: 80, cap: 150 },
            { dLat: -0.035, dLng: 0.018, name: "South Outer Ring Supercharger", cost: 110000, val: 70, cap: 120 },
            { dLat: 0.012, dLng: 0.042, name: "East Logistics Park Depot", cost: 150000, val: 90, cap: 200 },
            { dLat: -0.018, dLng: -0.040, name: "West Metro Interchange Station", cost: 95000, val: 65, cap: 90 },
            { dLat: 0.026, dLng: -0.028, name: "Northwest Tech Corridor Hub", cost: 140000, val: 85, cap: 180 },
            { dLat: -0.030, dLng: -0.022, name: "Airport Link EV Fast Hub", cost: 125000, val: 75, cap: 150 }
        ];

        hubs.forEach((hub, idx) => {
            const id = `hub_${Date.now()}_${idx}`;
            const station = {
                id: id,
                name: hub.name,
                latitude: lat + hub.dLat,
                longitude: lng + hub.dLng,
                installation_cost: hub.cost,
                expected_value: hub.val,
                coverage_score: 1.0,
                feeder_connection_cost: 0,
                operator: 'Regional EV Masterplan',
                is_user_cost: true,
                address: `Regional Highway Corridor, ${hub.cap} kW Fast Charger`,
                data_source: 'Regional Infrastructure Generator'
            };
            state.candidates.set(id, station);
            state.realStations.push(station);
        });

        stationsEmptyState.classList.add('hidden');
        stationsContent.classList.remove('hidden');
        stationsDrawer.classList.remove('drawer-closed');

        renderCandidateLedgerCards();
        updateCandidateMarkers();
        updateAlgorithmControlsState();

        // Fit map bounds to candidate cluster
        const bounds = L.latLngBounds(Array.from(state.candidates.values()).map(c => [c.latitude, c.longitude]));
        map.fitBounds(bounds, { padding: [50, 50] });
        showToast('success', 'Candidate hubs suggested', '6 strategic regional hubs added around the current map center');
        setStatus('live', 'Generated <strong>6</strong> regional candidate hubs for planning');
    }

    generateCandidatesBtn.addEventListener('click', generateRegionalCandidateHubs);

    // 14. DIJKSTRA ROUTE MODE TOGGLES & PICK-ON-MAP
    function resetPickingButtonsUI() {
        pickOriginBtn.classList.remove('picking');
        pickDestBtn.classList.remove('picking');
        if (!state.pickedOrigin) pickOriginBtn.innerHTML = '📍 Click Origin on Map';
        if (!state.pickedDest) pickDestBtn.innerHTML = '🏁 Click Destination on Map';
    }

    routeModeStations.addEventListener('click', () => {
        state.dijkstraMode = 'stations';
        routeModeStations.classList.add('active');
        routeModeMapclick.classList.remove('active');
        stationPickerContainer.classList.remove('hidden');
        mapclickPickerContainer.classList.add('hidden');
        state.pickingMode = null;
        document.getElementById('map').classList.remove('cursor-crosshair');
        resetPickingButtonsUI();
        updateAlgorithmControlsState();
    });

    routeModeMapclick.addEventListener('click', () => {
        state.dijkstraMode = 'mapclick';
        routeModeMapclick.classList.add('active');
        routeModeStations.classList.remove('active');
        stationPickerContainer.classList.add('hidden');
        mapclickPickerContainer.classList.remove('hidden');
        updateAlgorithmControlsState();
    });

    pickOriginBtn.addEventListener('click', () => {
        state.pickingMode = 'origin';
        state.isDroppingStation = false;
        dropStationToolBtn.classList.remove('active');
        pickOriginBtn.classList.add('picking');
        pickOriginBtn.innerHTML = '🎯 Click Map for Origin...';
        pickDestBtn.classList.remove('picking');
        document.getElementById('map').classList.add('cursor-crosshair');
        setStatus('live', 'Click the map to set the route origin');
    });

    pickDestBtn.addEventListener('click', () => {
        state.pickingMode = 'destination';
        state.isDroppingStation = false;
        dropStationToolBtn.classList.remove('active');
        pickDestBtn.classList.add('picking');
        pickDestBtn.innerHTML = '🎯 Click Map for Destination...';
        pickOriginBtn.classList.remove('picking');
        document.getElementById('map').classList.add('cursor-crosshair');
        setStatus('live', 'Click the map to set the route destination');
    });

    // 15. EXECUTE KRUSKAL'S MST ALGORITHM
    runMstBtn.addEventListener('click', async () => {
        const cands = Array.from(state.candidates.values());
        if (cands.length < 2) return;

        runMstBtn.disabled = true;
        runMstBtn.innerHTML = '<span>Computing Real Road MST...</span>';
        mstResults.classList.add('hidden');
        layers.mst.clearLayers();
        setStatus('busy', "Running Kruskal's MST over the real road-network graph...");

        try {
            const feederCost = parseInt(feederCostInput.value) || 25000;
            const resp = await fetch('/api/mst', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    stations: cands,
                    feeder_cost_per_km: feederCost
                })
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || 'MST execution failed');
            }

            const mstData = await resp.json();
            state.mstResult = mstData;

            // Draw MST Edges on Real Earth Map (Solid Green Polylines)
            mstData.accepted_edges.forEach(edge => {
                const polyline = L.polyline(
                    [[edge.u_lat, edge.u_lon], [edge.v_lat, edge.v_lon]],
                    {
                        color: '#3DDC84',
                        weight: 3.5,
                        opacity: 0.95
                    }
                ).addTo(layers.mst);

                polyline.bindPopup(`
                    <div style="font-size: 11px; font-family: sans-serif; color: #111;">
                        <strong>MST Power Feeder Link</strong><br>
                        ${escapeHtml(edge.u_name)} ↔ ${escapeHtml(edge.v_name)}<br>
                        Road Distance: <strong>${edge.road_distance_km} km</strong>
                    </div>
                `);
            });

            // Display Execution Metrics
            mstResults.classList.remove('hidden');
            mstResults.innerHTML = `
                <div class="results-header">
                    <span>KRUSKAL MST BACKBONE</span>
                    <span>${mstData.accepted_edges.length} Links</span>
                </div>
                <div class="metric-line">
                    <span>Total Backbone Distance:</span>
                    <span class="metric-val" style="color: #3DDC84;">${mstData.total_backbone_km} km</span>
                </div>
                <div class="metric-line">
                    <span>Feeder Infrastructure Cost:</span>
                    <span class="metric-val">₹${mstData.backbone_cost.toLocaleString()}</span>
                </div>
                <div class="metric-line">
                    <span>Edges Evaluated / Rejected:</span>
                    <span class="metric-val">${mstData.total_edges_considered} / ${mstData.rejected_count} cycles</span>
                </div>
                <div class="metric-line">
                    <span>Spanning Components:</span>
                    <span class="metric-val">${mstData.algorithm_info.components_formed}</span>
                </div>
                <div style="font-size: 10px; color: #8B8F97; margin-top: 4px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.05);">
                    Data Source: ${escapeHtml(mstData.algorithm_info.road_data_source || 'OSM Real Road Network')}
                </div>
            `;
            showToast('success', 'MST complete', `Kruskal's algorithm built a ${mstData.accepted_edges.length}-link backbone of ${mstData.total_backbone_km} km`);
            setStatus('live', `MST complete · <strong>${mstData.total_backbone_km} km</strong> backbone · ₹${mstData.backbone_cost.toLocaleString()} feeder cost`);

        } catch (error) {
            showToast('error', 'MST failed', error.message, 7000);
            setStatus('error', 'MST execution failed');
        } finally {
            runMstBtn.disabled = false;
            runMstBtn.innerHTML = '<span>Run Kruskal\'s MST</span>';
        }
    });

    // 16. EXECUTE DIJKSTRA'S SHORTEST PATH ALGORITHM
    runDijkstraBtn.addEventListener('click', async () => {
        const cands = Array.from(state.candidates.values());
        let requestPayload = {};

        if (state.dijkstraMode === 'stations') {
            const startId = dijkstraStartSelect.value;
            const endId = dijkstraEndSelect.value;
            if (!startId || !endId) {
                showToast('warning', 'Missing selection', 'Please select both Origin and Destination stations.');
                return;
            }
            if (startId === endId) {
                showToast('warning', 'Invalid selection', 'Origin and Destination must be distinct stations.');
                return;
            }
            requestPayload = {
                stations: cands,
                start_id: startId,
                destination_id: endId
            };
        } else {
            // Mapclick Mode
            if (!state.pickedOrigin || !state.pickedDest) {
                showToast('warning', 'Missing points', 'Please click both Origin and Destination on the map first.');
                return;
            }
            requestPayload = {
                stations: cands,
                start_lat: state.pickedOrigin.lat,
                start_lon: state.pickedOrigin.lon,
                start_name: "Selected Origin",
                end_lat: state.pickedDest.lat,
                end_lon: state.pickedDest.lon,
                end_name: "Selected Destination"
            };
        }

        runDijkstraBtn.disabled = true;
        runDijkstraBtn.innerHTML = '<span>Relaxing Graph Edges...</span>';
        dijkstraResults.classList.add('hidden');
        layers.dijkstra.clearLayers();
        setStatus('busy', 'Running Dijkstra shortest-path relaxation over the road graph...');

        try {
            const resp = await fetch('/api/dijkstra', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestPayload)
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || 'Dijkstra execution failed');
            }

            const dijkData = await resp.json();
            state.dijkstraResult = dijkData;

            // Draw route on real Earth map
            if (dijkData.road_geometry_geojson && dijkData.road_geometry_geojson.length > 0) {
                // Leaflet expects [lat, lon], GeoJSON is [lon, lat]
                const latLngs = dijkData.road_geometry_geojson.map(c => [c[1], c[0]]);

                // Add outer glow
                L.polyline(latLngs, {
                    color: '#00E5FF',
                    weight: 7,
                    opacity: 0.45
                }).addTo(layers.dijkstra);

                // Add crisp core line
                const pathPolyline = L.polyline(latLngs, {
                    color: '#FFFFFF',
                    weight: 4.5,
                    opacity: 0.95
                }).addTo(layers.dijkstra);

                map.fitBounds(pathPolyline.getBounds(), { padding: [40, 40] });
            }

            dijkstraResults.classList.remove('hidden');
            dijkstraResults.innerHTML = `
                <div class="results-header">
                    <span>OUR DIJKSTRA RESULT</span>
                    <span style="color: #00E5FF;">${dijkData.total_distance_km} km</span>
                </div>
                <div class="metric-line">
                    <span>Shortest Road Distance:</span>
                    <span class="metric-val" style="color: #FFFFFF;">${dijkData.total_distance_km} km</span>
                </div>
                <div class="metric-line">
                    <span>Estimated Driving Time:</span>
                    <span class="metric-val">${dijkData.estimated_time_min} mins</span>
                </div>
                <div class="metric-line">
                    <span>Route Waypoints:</span>
                    <span class="metric-val">${dijkData.path_node_names.map(escapeHtml).join(' → ')}</span>
                </div>
                <div style="font-size: 10px; color: #8B8F97; margin-top: 4px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.05);">
                    Algorithm: Dijkstra Binary Heap | Real Road Network OSRM/ORS
                </div>
            `;
            showToast('success', 'Shortest path found', `${dijkData.total_distance_km} km via ${dijkData.path_node_names.length} waypoints`);
            setStatus('live', `Dijkstra complete · <strong>${dijkData.total_distance_km} km</strong> shortest route · ${dijkData.estimated_time_min} min estimated`);

        } catch (error) {
            showToast('error', 'Dijkstra failed', error.message, 7000);
            setStatus('error', 'Dijkstra execution failed');
        } finally {
            runDijkstraBtn.disabled = false;
            runDijkstraBtn.innerHTML = '<span>Find Shortest Path (Dijkstra)</span>';
        }
    });

    // 17. EXECUTE 0/1 KNAPSACK DP ALGORITHM
    runKnapsackBtn.addEventListener('click', async () => {
        const cands = Array.from(state.candidates.values());
        if (cands.length === 0) return;

        const budget = parseInt(knapsackBudgetInput.value) || 0;
        if (budget <= 0) {
            showToast('warning', 'Invalid budget', 'Please enter a positive municipal budget limit.');
            return;
        }

        runKnapsackBtn.disabled = true;
        runKnapsackBtn.innerHTML = '<span>Building DP Table...</span>';
        knapsackResults.classList.add('hidden');
        layers.knapsack.clearLayers();
        setStatus('busy', 'Solving 0/1 Knapsack DP for optimal station allocation...');

        try {
            const resp = await fetch('/api/knapsack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidates: cands,
                    budget: budget
                })
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || 'Knapsack DP execution failed');
            }

            const knapData = await resp.json();
            state.knapsackResult = knapData;

            // Highlight optimal stations on Real Map with bright green pulse rings
            knapData.selected_stations.forEach(st => {
                L.circleMarker([st.latitude, st.longitude], {
                    radius: 18,
                    fillColor: 'transparent',
                    color: '#3DDC84',
                    weight: 3,
                    dashArray: '4,4',
                    opacity: 1
                }).addTo(layers.knapsack);

                L.circleMarker([st.latitude, st.longitude], {
                    radius: 7,
                    fillColor: '#3DDC84',
                    color: '#FFFFFF',
                    weight: 2,
                    fillOpacity: 1
                }).addTo(layers.knapsack);
            });

            knapsackResults.classList.remove('hidden');
            knapsackResults.innerHTML = `
                <div class="results-header">
                    <span>0/1 KNAPSACK OPTIMAL SET</span>
                    <span>${knapData.selected_stations.length} / ${cands.length} Selected</span>
                </div>
                <div class="metric-line">
                    <span>Total Investment Cost:</span>
                    <span class="metric-val" style="color: #3DDC84;">₹${knapData.total_installation_cost.toLocaleString()}</span>
                </div>
                <div class="metric-line">
                    <span>Total Public Benefit:</span>
                    <span class="metric-val" style="color: #3DDC84;">+${knapData.total_value_benefit} pts</span>
                </div>
                <div class="metric-line">
                    <span>Surplus Budget Remaining:</span>
                    <span class="metric-val">₹${knapData.remaining_budget.toLocaleString()}</span>
                </div>
                <div class="metric-line">
                    <span>Budget Utilization:</span>
                    <span class="metric-val">${knapData.budget_utilization_pct}%</span>
                </div>
                <div style="margin-top: 6px; font-size: 10px; color: #8B8F97;">
                    <strong>Selected:</strong> ${knapData.selected_stations.map(s => escapeHtml(s.name)).join(', ')}
                </div>
                ${knapData.rejected_stations.length > 0 ? `
                <div style="margin-top: 4px; font-size: 10px; color: #FF4D4F;">
                    <strong>Excluded:</strong> ${knapData.rejected_stations.map(r => `${escapeHtml(r.station.name)} (${r.reason})`).join('; ')}
                </div>
                ` : ''}
            `;
            showToast('success', 'Budget optimization complete', `Selected ${knapData.selected_stations.length} station(s) for ₹${knapData.total_installation_cost.toLocaleString()} (${knapData.budget_utilization_pct}% budget used)`);
            setStatus('live', `Knapsack optimal · <strong>${knapData.selected_stations.length}</strong> station(s) · +${knapData.total_value_benefit} benefit pts`);

        } catch (error) {
            showToast('error', 'Knapsack failed', error.message, 7000);
            setStatus('error', 'Knapsack execution failed');
        } finally {
            runKnapsackBtn.disabled = false;
            runKnapsackBtn.innerHTML = '<span>Run 0/1 Knapsack DP</span>';
        }
    });

    // 18. PERSISTENT MARKERS (shared across all users)
    function loadPersistentMarkers() {
        fetch('/api/markers')
            .then(r => r.json())
            .then(markers => {
                persistentMarkers.length = 0;
                markers.forEach(m => persistentMarkers.push(m));
                renderPersistentMarkers();
            })
            .catch(err => {
                console.warn('Failed to load markers:', err);
            });
    }

    function renderPersistentMarkers() {
        layers.markers.clearLayers();
        Object.values(markerIcons).forEach(m => { try { layers.markers.removeLayer(m); } catch(e){} });
        Object.keys(markerIcons).forEach(k => delete markerIcons[k]);

        persistentMarkers.forEach(m => {
            const icon = L.divIcon({
                className: 'persistent-marker',
                html: `<div class="pm-pin" style="background:${m.color}">${m.icon}</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 30],
                popupAnchor: [0, -28]
            });
            const marker = L.marker([m.latitude, m.longitude], { icon }).addTo(layers.markers);
            marker.bindPopup(`
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 12px; color: #111; max-width: 220px;">
                    <strong style="font-size: 13px;">${escapeHtml(m.name)}</strong><br>
                    <span style="color: #555; font-size: 11px;">${escapeHtml(m.note || '')}</span>
                    <div style="margin-top: 6px; font-size: 10px; color: #777;">👤 ${escapeHtml(m.created_by)} · ${escapeHtml(m.created_at || '')}</div>
                    <div style="margin-top: 6px;">
                        <button onclick="deleteMarker(${m.id})" style="background:#FF4D4F;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;">Delete</button>
                    </div>
                </div>
            `);
            markerIcons[m.id] = marker;
        });
    }

    async function saveMarker(name, lat, lon, note, color, icon) {
        try {
            const resp = await fetch('/api/markers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, latitude: lat, longitude: lon, note, color, icon, created_by: 'deployer' })
            });
            if (resp.ok) {
                const marker = await resp.json();
                persistentMarkers.push(marker);
                renderPersistentMarkers();
                return true;
            }
        } catch (err) {
            console.warn('Failed to save marker:', err);
        }
        return false;
    }

    window.deleteMarker = async function(markerId) {
        try {
            const resp = await fetch(`/api/markers/${markerId}`, { method: 'DELETE' });
            if (resp.ok) {
                const idx = persistentMarkers.findIndex(m => m.id === markerId);
                if (idx >= 0) persistentMarkers.splice(idx, 1);
                renderPersistentMarkers();
                showToast('info', 'Marker deleted', 'The marker has been removed from the shared map');
            }
        } catch (err) {
            showToast('error', 'Delete failed', 'Could not delete the marker');
        }
    };

    // Load persistent markers on startup
    loadPersistentMarkers();

    // 19. RESET / CLEAR ANALYSIS
    resetBtn.addEventListener('click', () => {
        Object.values(layers).forEach(layer => layer.clearLayers());
        state.realStations = [];
        state.candidates.clear();
        state.mstResult = null;
        state.dijkstraResult = null;
        state.knapsackResult = null;
        state.isDroppingStation = false;
        state.pickingMode = null;
        state.pickedOrigin = null;
        state.pickedDest = null;

        document.getElementById('map').classList.remove('cursor-crosshair');
        dropStationToolBtn.classList.remove('active');
        resetPickingButtonsUI();
        originCoordLabel.textContent = 'Not selected';
        destCoordLabel.textContent = 'Not selected';

        stationsDrawer.classList.add('drawer-closed');
        stationsEmptyState.classList.remove('hidden');
        stationsContent.classList.add('hidden');
        drawerToggleText.textContent = 'Candidate Stations (0)';

        mstResults.classList.add('hidden');
        dijkstraResults.classList.add('hidden');
        knapsackResults.classList.add('hidden');

        locationInput.value = '';
        map.setView([20.5937, 78.9629], 5);
        updateAlgorithmControlsState();
        setStatus('live', 'Ready · Search a city to load real charging stations');
        showToast('info', 'Map cleared', 'All layers and candidates have been reset');
    });

    // Utility escapeHtml
    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
