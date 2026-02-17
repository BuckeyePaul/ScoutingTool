// Global state
let currentPlayer = null;
let selectedPositions = [];
let selectedRank = null;
let selectedSearchPositions = [];
let allPlayers = [];
let boardRanksRevealed = false;
let bigBoardType = 'overall';
let currentBigBoardPosition = null;
let currentPlayerSourceTab = null;
let importedBoardFiles = [];
let bigBoardController = null;
let playerReportController = null;
const SETTINGS_STORAGE_KEY = 'scout_app_settings';
const ACTIVE_TAB_STORAGE_KEY = 'scout_active_tab';
const DEFAULT_APP_SETTINGS = {
    theme: 'default',
    teamCity: 'Arizona',
    font: 'rajdhani',
    gradingSystems: ['round'],
    showConsensusGradeOnBigBoard: false,
    hiddenRankBoardKeys: []
};
let appSettings = { ...DEFAULT_APP_SETTINGS };

const NFL_TEAM_CITY_THEMES = {
    'Arizona': { primary: '#97233F', secondary: '#1B1B1B', accent: '#6F152B', highlight: '#FFB612', textPrimary: '#FFFFFF', textSecondary: '#E6D9DD', bgStart: '#6F152B', bgEnd: '#1B1B1B' },
    'Atlanta': { primary: '#A71930', secondary: '#101820', accent: '#6D1121', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#D9DDE2', bgStart: '#6D1121', bgEnd: '#101820' },
    'Baltimore': { primary: '#241773', secondary: '#000000', accent: '#3B2A8C', highlight: '#9E7C0C', textPrimary: '#FFFFFF', textSecondary: '#D8D2E8', bgStart: '#241773', bgEnd: '#000000' },
    'Buffalo': { primary: '#00338D', secondary: '#C60C30', accent: '#001E5A', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#D7E2F4', bgStart: '#00338D', bgEnd: '#C60C30' },
    'Carolina': { primary: '#0085CA', secondary: '#101820', accent: '#005F8F', highlight: '#BFC0BF', textPrimary: '#FFFFFF', textSecondary: '#CFE7F4', bgStart: '#005F8F', bgEnd: '#101820' },
    'Chicago': { primary: '#C83803', secondary: '#0B162A', accent: '#8F2802', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#F1D8D1', bgStart: '#C83803', bgEnd: '#0B162A' },
    'Cincinnati': { primary: '#FB4F14', secondary: '#000000', accent: '#C53A08', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#F6D8CB', bgStart: '#C53A08', bgEnd: '#000000' },
    'Cleveland': { primary: '#311D00', secondary: '#FF3C00', accent: '#4C2F00', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#F0DED3', bgStart: '#311D00', bgEnd: '#FF3C00' },
    'Dallas': { primary: '#003594', secondary: '#041E42', accent: '#00296E', highlight: '#869397', textPrimary: '#FFFFFF', textSecondary: '#D4DCE5', bgStart: '#003594', bgEnd: '#041E42' },
    'Denver': { primary: '#FB4F14', secondary: '#002244', accent: '#C53A08', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#F8DACD', bgStart: '#FB4F14', bgEnd: '#002244' },
    'Detroit': { primary: '#0076B6', secondary: '#B0B7BC', accent: '#005886', highlight: '#000000', textPrimary: '#FFFFFF', textSecondary: '#D4E5F1', bgStart: '#0076B6', bgEnd: '#2E3A45' },
    'Green Bay': { primary: '#203731', secondary: '#FFB612', accent: '#162A24', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#D3DDD9', bgStart: '#203731', bgEnd: '#8C6B00' },
    'Houston': { primary: '#03202F', secondary: '#A71930', accent: '#00131D', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#CCD9E1', bgStart: '#03202F', bgEnd: '#A71930' },
    'Indianapolis': { primary: '#002C5F', secondary: '#A2AAAD', accent: '#001D3E', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#CFD9E1', bgStart: '#002C5F', bgEnd: '#3A4A56' },
    'Jacksonville': { primary: '#101820', secondary: '#006778', accent: '#0A1117', highlight: '#D7A22A', textPrimary: '#FFFFFF', textSecondary: '#C8D9DE', bgStart: '#101820', bgEnd: '#006778' },
    'Kansas City': { primary: '#E31837', secondary: '#FFB81C', accent: '#A60F27', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#F9D7DD', bgStart: '#A60F27', bgEnd: '#E31837' },
    'Las Vegas': { primary: '#000000', secondary: '#A5ACAF', accent: '#111111', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#D6D8DA', bgStart: '#000000', bgEnd: '#3A3A3A' },
    'Los Angeles AFC': { primary: '#0080C6', secondary: '#FFC20E', accent: '#005B8D', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#D5EAF5', bgStart: '#005B8D', bgEnd: '#0080C6' },
    'Los Angeles NFC': { primary: '#003594', secondary: '#FFD100', accent: '#00286D', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#D4DDF3', bgStart: '#003594', bgEnd: '#1C4EC2' },
    'Miami': { primary: '#008E97', secondary: '#FC4C02', accent: '#00676D', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#D0ECEE', bgStart: '#008E97', bgEnd: '#FC4C02' },
    'Minnesota': { primary: '#4F2683', secondary: '#FFC62F', accent: '#371A5D', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#DDD1EC', bgStart: '#4F2683', bgEnd: '#2A2A2A' },
    'New England': { primary: '#002244', secondary: '#C60C30', accent: '#00132A', highlight: '#B0B7BC', textPrimary: '#FFFFFF', textSecondary: '#CDD6E0', bgStart: '#002244', bgEnd: '#C60C30' },
    'New Orleans': { primary: '#101820', secondary: '#D3BC8D', accent: '#0A1117', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#E6DFCF', bgStart: '#101820', bgEnd: '#685B44' },
    'New York AFC': { primary: '#125740', secondary: '#FFFFFF', accent: '#0E4332', highlight: '#000000', textPrimary: '#FFFFFF', textSecondary: '#D3E7DF', bgStart: '#125740', bgEnd: '#0E4332' },
    'New York NFC': { primary: '#0B2265', secondary: '#A71930', accent: '#081845', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#CFD7EA', bgStart: '#0B2265', bgEnd: '#A71930' },
    'Philadelphia': { primary: '#004C54', secondary: '#A5ACAF', accent: '#00363C', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#CFE3E5', bgStart: '#004C54', bgEnd: '#1F2A30' },
    'Pittsburgh': { primary: '#FFB612', secondary: '#101820', accent: '#C58A00', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#F5E9C7', bgStart: '#C58A00', bgEnd: '#101820' },
    'San Francisco': { primary: '#AA0000', secondary: '#B3995D', accent: '#760000', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#EFD7D7', bgStart: '#AA0000', bgEnd: '#5A4A2B' },
    'Seattle': { primary: '#002244', secondary: '#69BE28', accent: '#00162D', highlight: '#A5ACAF', textPrimary: '#FFFFFF', textSecondary: '#CDD5DF', bgStart: '#002244', bgEnd: '#275B2A' },
    'Tampa Bay': { primary: '#D50A0A', secondary: '#34302B', accent: '#980707', highlight: '#FF7900', textPrimary: '#FFFFFF', textSecondary: '#F2D0D0', bgStart: '#980707', bgEnd: '#34302B' },
    'Tennessee': { primary: '#0C2340', secondary: '#4B92DB', accent: '#071728', highlight: '#C8102E', textPrimary: '#FFFFFF', textSecondary: '#CFD9E5', bgStart: '#0C2340', bgEnd: '#4B92DB' },
    'Washington': { primary: '#5A1414', secondary: '#FFB612', accent: '#3D0E0E', highlight: '#FFFFFF', textPrimary: '#FFFFFF', textSecondary: '#E7D8D8', bgStart: '#5A1414', bgEnd: '#7B5A00' }
};

// School logos mapping (using logo images)
const schoolLogos = {
    'default': '🏫'
};

// Helper function to get school logo path
function getSchoolLogo(schoolName) {
    if (!schoolName) return null;
    // Convert school name to filename format (lowercase, replace spaces with hyphens)
    const filename = schoolName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    return `static/logos/${filename}.png`;
}

async function requestGetJson(url) {
    if (window.ApiClient?.getJson) {
        return window.ApiClient.getJson(url);
    }

    const response = await fetch(url);
    const data = await response.json();
    return { response, data };
}

async function requestPostJson(url, payload) {
    if (window.ApiClient?.postJson) {
        return window.ApiClient.postJson(url, payload);
    }

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {})
    });
    const data = await response.json();
    return { response, data };
}

async function requestPostNoBody(url) {
    if (window.ApiClient?.postNoBody) {
        return window.ApiClient.postNoBody(url);
    }

    const response = await fetch(url, { method: 'POST' });
    const data = await response.json();
    return { response, data };
}

function openBigBoardPlayerModal(player) {
    const overlay = document.getElementById('player-report-overlay');
    const detailsSection = document.getElementById('player-details');
    overlay.classList.remove('hidden');
    detailsSection.classList.add('modal-mode');

    currentPlayer = player;
    currentPlayerSourceTab = 'bigboard-modal';
    displayPlayerDetails(player);
}

function initializeBigBoardController() {
    if (!window.createBigBoardController) {
        return;
    }

    bigBoardController = window.createBigBoardController({
        getBigBoardType: () => bigBoardType,
        setBigBoardTypeState: (type) => {
            bigBoardType = type;
        },
        getCurrentBigBoardPosition: () => currentBigBoardPosition,
        setCurrentBigBoardPosition: (position) => {
            currentBigBoardPosition = position || null;
        },
        getAppSettings: () => appSettings,
        requestGetJson,
        requestPostJson,
        showToast,
        openBigBoardPlayerModal
    });
}

function initializePlayerReportController() {
    if (!window.createPlayerReportController) {
        return;
    }

    playerReportController = window.createPlayerReportController({
        getCurrentPlayer: () => currentPlayer,
        setCurrentPlayer: (player) => {
            currentPlayer = player;
        },
        requestGetJson,
        requestPostJson,
        requestPostNoBody,
        showToast,
        loadStats,
        loadPositions,
        loadSchools,
        displayPlayerDetails
    });
}

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    loadAppSettings();
    applyVisualSettings();
    populateGradeDropdowns();
    syncSettingsControls();
    setupTabs();
    loadStats();
    loadPositions();
    loadSchools();
    loadRankBoardSettings();
    initializeBigBoardController();
    initializePlayerReportController();
    setupEventListeners();

    const savedTabId = getSavedActiveTabId();
    switchTab(savedTabId);
});

function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    const nextTabId = document.getElementById(tabId) ? tabId : 'search-tab';

    document.querySelectorAll('.tab-btn').forEach(button => {
        button.classList.toggle('active', button.dataset.tab === nextTabId);
    });

    document.querySelectorAll('.tab-panel').forEach(panel => {
        const isActive = panel.id === nextTabId;
        panel.classList.toggle('active', isActive);
        panel.classList.toggle('hidden', !isActive);
    });

    if (nextTabId === 'bigboard-tab') {
        loadBigBoard();
        searchBigBoardPlayers();
    }

    localStorage.setItem(ACTIVE_TAB_STORAGE_KEY, nextTabId);
    updatePlayerDetailsVisibility(nextTabId);
}

function getSavedActiveTabId() {
    const saved = localStorage.getItem(ACTIVE_TAB_STORAGE_KEY);
    return saved && document.getElementById(saved) ? saved : 'search-tab';
}

function updatePlayerDetailsVisibility(activeTabId = null) {
    const detailsSection = document.getElementById('player-details');
    if (!detailsSection) {
        return;
    }

    const activeTab = activeTabId || document.querySelector('.tab-panel.active')?.id;
    const shouldShow = !!currentPlayer && !!currentPlayerSourceTab && (
        currentPlayerSourceTab === 'bigboard-modal' || activeTab === currentPlayerSourceTab
    );
    detailsSection.classList.toggle('hidden', !shouldShow);
}

function positionPlayerDetailsForCurrentSource() {
    const detailsSection = document.getElementById('player-details');
    if (!detailsSection) {
        return;
    }

    if (currentPlayerSourceTab === 'search-tab') {
        const searchTab = document.getElementById('search-tab');
        const resultsSection = searchTab ? searchTab.querySelector('.search-results-section') : null;
        if (searchTab && resultsSection && detailsSection.parentElement !== searchTab) {
            searchTab.insertBefore(detailsSection, resultsSection);
        }
    } else if (currentPlayerSourceTab === 'randomizer-tab') {
        const randomizerTab = document.getElementById('randomizer-tab');
        const randomizerSection = randomizerTab ? randomizerTab.querySelector('.randomizer-section') : null;
        if (randomizerTab && randomizerSection) {
            const insertAfter = randomizerSection.nextSibling;
            if (insertAfter) {
                randomizerTab.insertBefore(detailsSection, insertAfter);
            } else {
                randomizerTab.appendChild(detailsSection);
            }
        }
    }
}

// Load statistics
async function loadStats() {
    try {
        const { data } = await requestGetJson('/api/stats');
        const stats = data;
     
        document.getElementById('total-players').textContent = stats.total_players;
        document.getElementById('scouted-players').textContent = stats.scouted;
        document.getElementById('remaining-players').textContent = stats.remaining;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load available positions
async function loadPositions() {
    try {
        const { data } = await requestGetJson('/api/positions');
        const positions = data;

        const randomizerContainer = document.getElementById('position-filters');
        const searchContainer = document.getElementById('search-position-filters');
        const boardPositionSelect = document.getElementById('bigboard-position-select');
        const exportPositionSelect = document.getElementById('export-position-select');
        const editPositionSelect = document.getElementById('edit-position-input');
        randomizerContainer.innerHTML = '';
        searchContainer.innerHTML = '';
        boardPositionSelect.innerHTML = '';
        if (exportPositionSelect) {
            exportPositionSelect.innerHTML = '<option value="">Select position for export...</option>';
        }
        if (editPositionSelect) {
            editPositionSelect.innerHTML = '<option value="">Select position...</option>';
        }

        positions.forEach(position => {
            const option = document.createElement('option');
            option.value = position;
            option.textContent = position;
            boardPositionSelect.appendChild(option);

            if (exportPositionSelect) {
                const exportOption = document.createElement('option');
                exportOption.value = position;
                exportOption.textContent = position;
                exportPositionSelect.appendChild(exportOption);
            }

            if (editPositionSelect) {
                const editOption = document.createElement('option');
                editOption.value = position;
                editOption.textContent = position;
                editPositionSelect.appendChild(editOption);
            }
        });

        if (editPositionSelect && currentPlayer && currentPlayer.position) {
            const currentPosition = currentPlayer.position;
            const hasOption = Array.from(editPositionSelect.options).some(option => option.value === currentPosition);
            if (!hasOption) {
                const customOption = document.createElement('option');
                customOption.value = currentPosition;
                customOption.textContent = currentPosition;
                editPositionSelect.appendChild(customOption);
            }
        }
        if (positions.length) {
            if (currentBigBoardPosition && positions.includes(currentBigBoardPosition)) {
                boardPositionSelect.value = currentBigBoardPosition;
            } else {
                currentBigBoardPosition = positions[0];
                boardPositionSelect.value = currentBigBoardPosition;
            }
        } else {
            currentBigBoardPosition = null;
        }

        positions.forEach(position => {
            const randomizerBtn = document.createElement('button');
            randomizerBtn.className = 'position-btn';
            randomizerBtn.textContent = position;
            randomizerBtn.dataset.position = position;
            randomizerBtn.addEventListener('click', togglePosition);
            randomizerContainer.appendChild(randomizerBtn);

            const searchBtn = document.createElement('button');
            searchBtn.className = 'position-btn';
            searchBtn.textContent = position;
            searchBtn.dataset.position = position;
            searchBtn.addEventListener('click', toggleSearchPosition);
            searchContainer.appendChild(searchBtn);
        });
    } catch (error) {
        console.error('Error loading positions:', error);
    }
}

// Load available schools for searchable dropdown
async function loadSchools() {
    try {
        const { data } = await requestGetJson('/api/schools');
        const schools = data;

        const schoolSelect = document.getElementById('school-search-input');
        schoolSelect.innerHTML = '<option value="">All schools</option>';

        schools.forEach(school => {
            const option = document.createElement('option');
            option.value = school;
            option.textContent = school;
            schoolSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading schools:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    const stopAppBtn = document.getElementById('stop-app-btn');
    if (stopAppBtn) {
        stopAppBtn.addEventListener('click', shutdownApplication);
    }

    // Randomize button
    document.getElementById('randomize-btn').addEventListener('click', randomizePlayer);
 
    // Ranking filter buttons
    document.querySelectorAll('.rank-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.rank-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedRank = this.dataset.rank === 'all' ? null : parseInt(this.dataset.rank);
        });
    });

    // Scout button
    document.getElementById('mark-scouted-btn').addEventListener('click', toggleScoutStatus);
 
    // Save notes button
    document.getElementById('save-notes-btn').addEventListener('click', saveNotes);
    document.getElementById('save-games-watched-btn').addEventListener('click', saveGamesWatched);
    document.getElementById('close-player-report-btn').addEventListener('click', closePlayerReport);
    document.getElementById('player-report-overlay').addEventListener('click', function(event) {
        if (event.target === this) {
            closePlayerReport();
        }
    });
    document.addEventListener('keydown', function(event) {
        if (event.key !== 'Escape') {
            return;
        }

        const profileDialog = document.getElementById('edit-profile-dialog');
        if (profileDialog && !profileDialog.classList.contains('hidden')) {
            event.preventDefault();
            closeEditProfileDialog();
            return;
        }

        const importUrlDialog = document.getElementById('import-nflmock-url-dialog');
        if (importUrlDialog && !importUrlDialog.classList.contains('hidden')) {
            event.preventDefault();
            closeImportNflmockUrlDialog();
            return;
        }

        const overlay = document.getElementById('player-report-overlay');
        if (overlay && !overlay.classList.contains('hidden')) {
            event.preventDefault();
            closePlayerReport();
        }
    });
 
    // Grade dropdowns
    document.getElementById('grade-dropdown-1').addEventListener('change', function() {
        const system = getGradeSystemForSlot('primary');
        updateGrade(formatGradeForSystem(system, this.value), 'primary');
    });
    document.getElementById('grade-dropdown-2').addEventListener('change', function() {
        const system = getGradeSystemForSlot('secondary');
        updateGrade(formatGradeForSystem(system, this.value), 'secondary');
    });
    document.getElementById('grade-input-1').addEventListener('change', function() {
        updateGrade(formatGradeForSystem('numerical', this.value), 'primary');
    });
    document.getElementById('grade-input-2').addEventListener('change', function() {
        updateGrade(formatGradeForSystem('numerical', this.value), 'secondary');
    });
 
    document.getElementById('player-board-ranks-toggle').addEventListener('click', toggleBoardRanksVisibility);

    document.getElementById('search-btn').addEventListener('click', searchPlayers);
    document.getElementById('search-input').addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchPlayers();
        }
    });

    document.getElementById('theme-select').addEventListener('change', function() {
        appSettings.theme = this.value;
        toggleTeamThemeSelector();
        updateThemeSelectCurrentLabel();
        saveAppSettings();
        applyVisualSettings();
    });

    document.getElementById('theme-team-select').addEventListener('change', function() {
        appSettings.teamCity = this.value;
        saveAppSettings();
        applyVisualSettings();
    });

    document.getElementById('font-select').addEventListener('change', function() {
        appSettings.font = this.value;
        saveAppSettings();
        applyVisualSettings();
    });

    const showConsensusGradeCheckbox = document.getElementById('show-consensus-grade-checkbox');
    if (showConsensusGradeCheckbox) {
        showConsensusGradeCheckbox.addEventListener('change', function() {
            appSettings.showConsensusGradeOnBigBoard = this.checked;
            saveAppSettings();
            loadBigBoard();
        });
    }

    document.querySelectorAll('.grading-system-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleGradingSystemsChange);
    });
    document.getElementById('reset-preferences-btn').addEventListener('click', resetPreferences);
    document.getElementById('toggle-add-player-btn').addEventListener('click', toggleAddPlayerPanel);
    document.getElementById('refresh-logos-btn').addEventListener('click', refreshDownloadedLogos);
    document.getElementById('update-rankings-btn').addEventListener('click', updateRankingsFromTankathon);
    document.getElementById('recalculate-rankings-btn').addEventListener('click', recalculatePlayerRankings);
    document.getElementById('import-consensus-btn').addEventListener('click', importConsensusBoard);
    document.getElementById('import-nflmock-url-btn').addEventListener('click', openImportNflmockUrlDialog);
    document.getElementById('merge-duplicates-btn').addEventListener('click', mergeDuplicatePlayers);
    document.getElementById('board-import-files').addEventListener('change', handleBoardFilesSelected);
    document.getElementById('use-board-weights-checkbox').addEventListener('change', syncBoardWeightInputs);
    document.getElementById('import-big-boards-btn').addEventListener('click', importAndNormalizeBigBoards);
    document.getElementById('export-overall-board-btn').addEventListener('click', () => exportNormalizedBigBoard('overall'));
    document.getElementById('export-position-board-btn').addEventListener('click', () => exportNormalizedBigBoard('position'));
    document.getElementById('save-board-weights-btn').addEventListener('click', saveRankBoardSettings);

    document.getElementById('overall-board-btn').addEventListener('click', () => setBigBoardType('overall'));
    document.getElementById('position-board-btn').addEventListener('click', () => setBigBoardType('position'));
    document.getElementById('bigboard-position-select').addEventListener('change', function() {
        currentBigBoardPosition = this.value || null;
        loadBigBoard();
        searchBigBoardPlayers();
    });
    document.getElementById('bigboard-player-search').addEventListener('input', searchBigBoardPlayers);
    document.getElementById('bigboard-autosort-btn').addEventListener('click', autoSortBigBoard);
    document.getElementById('confirm-add-to-rank-btn').addEventListener('click', confirmAddToRank);
    document.getElementById('confirm-add-to-bottom-btn').addEventListener('click', confirmAddToBottom);
    document.getElementById('cancel-add-to-board-btn').addEventListener('click', closeAddToBoardDialog);
    document.getElementById('close-import-nflmock-url-btn').addEventListener('click', closeImportNflmockUrlDialog);
    document.getElementById('confirm-import-nflmock-url-btn').addEventListener('click', importNflmockBoardByUrl);
    document.getElementById('open-nflmock-boards-btn').addEventListener('click', function() {
        window.open('https://www.nflmockdraftdatabase.com/big-boards/2026', '_blank', 'noopener');
    });
    document.getElementById('import-nflmock-url-dialog').addEventListener('click', function(event) {
        if (event.target === this) {
            closeImportNflmockUrlDialog();
        }
    });

    document.getElementById('settings-add-player-btn').addEventListener('click', addPlayerFromSettings);
    document.getElementById('open-profile-edit-btn').addEventListener('click', openEditProfileDialog);
    document.getElementById('close-profile-edit-btn').addEventListener('click', closeEditProfileDialog);
    document.getElementById('add-profile-stat-btn').addEventListener('click', () => addProfileStatRow());
    document.getElementById('save-profile-btn').addEventListener('click', savePlayerProfile);
    document.getElementById('edit-profile-dialog').addEventListener('click', function(event) {
        if (event.target === this) {
            closeEditProfileDialog();
        }
    });
}

function toggleAddPlayerPanel() {
    const panel = document.getElementById('add-player-panel');
    const toggleBtn = document.getElementById('toggle-add-player-btn');
    const nowHidden = !panel.classList.contains('hidden');
    panel.classList.toggle('hidden', nowHidden);
    toggleBtn.textContent = nowHidden ? 'Add Player to Database' : 'Hide Add Player Form';
}

function resetPreferences() {
    appSettings = { ...DEFAULT_APP_SETTINGS };
    saveAppSettings();
    applyVisualSettings();
    syncSettingsControls();
    populateGradeDropdowns();

    const messageEl = document.getElementById('grading-systems-message');
    if (messageEl) {
        messageEl.classList.add('hidden');
    }
}

function showToast(title, message = '', type = 'success', durationMs = 5000) {
    if (window.UIFeedback?.toast) {
        window.UIFeedback.toast(title, message, type, durationMs);
    }
}

async function shutdownApplication() {
    const userConfirmed = window.UIFeedback?.confirmAction
        ? await window.UIFeedback.confirmAction({
            title: 'Stop Scouting App?',
            message: 'This will stop the local server process and close this session.',
            confirmText: 'Stop App',
            cancelText: 'Cancel'
        })
        : window.confirm('Stop Scouting App? This will stop the local server process and close this session.');

    if (!userConfirmed) {
        return;
    }

    const stopAppBtn = document.getElementById('stop-app-btn');
    if (stopAppBtn) {
        stopAppBtn.disabled = true;
    }

    const closeWindowWithFallback = () => {
        try {
            window.open('', '_self');
            window.close();
        } catch (error) {
            console.error('Window close failed:', error);
        }

        setTimeout(() => {
            if (!window.closed) {
                document.body.innerHTML = '<div style="font-family: sans-serif; padding: 28px; color: #fff; background: #0f172a; min-height: 100vh;"><h2 style="margin-bottom: 10px;">Scouting App stopped</h2><p>The local server process has been stopped. You can safely close this tab.</p></div>';
            }
        }, 400);
    };

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);

        let response = null;
        let result = null;
        try {
            response = await fetch('/api/system/shutdown', {
                method: 'POST',
                signal: controller.signal,
                keepalive: true
            });
            clearTimeout(timeoutId);
            result = await response.json().catch(() => ({}));
        } finally {
            clearTimeout(timeoutId);
        }

        if (response && response.ok && result?.success !== false) {
            showToast('Stopping App', 'Server is shutting down. Closing this tab now.', 'success', 3500);
        } else {
            const errorText = result?.error || 'Shutdown request failed, attempting to close this tab.';
            showToast('Shutdown Warning', errorText, 'error', 4500);
        }
    } catch (error) {
        console.error('Error shutting down app:', error);
        showToast('Shutdown Warning', 'Could not confirm shutdown response. Attempting to close this tab.', 'error', 4500);
    }

    setTimeout(closeWindowWithFallback, 300);
}

async function runSettingsTool(endpoint, buttonId, successMessage) {
    const button = document.getElementById(buttonId);
    const messageEl = document.getElementById('settings-tools-message');

    button.disabled = true;
    messageEl.classList.remove('hidden');
    messageEl.textContent = 'Running... this may take a minute.';

    try {
        const { response, data } = await requestPostNoBody(endpoint);
        const result = data || {};

        if (!response.ok || !result.success) {
            const errorLog = result.output || result.error || 'Failed to run tool.';
            messageEl.textContent = result.error || 'Failed to run tool.';
            showToast('Action Failed', errorLog, 'error', 9000);
            return;
        }

        messageEl.textContent = `${successMessage}`;
        const outputText = (result.output || '').trim();
        const trimmedOutput = outputText.length > 900 ? `${outputText.slice(0, 900)}\n...` : outputText;
        showToast(successMessage, trimmedOutput || 'Completed successfully.', 'success', 9000);
        loadStats();
        loadPositions();
        loadSchools();
        if (document.getElementById('search-tab').classList.contains('active')) {
            searchPlayers();
        }
        if (document.getElementById('bigboard-tab').classList.contains('active')) {
            loadBigBoard();
            searchBigBoardPlayers();
        }
    } catch (error) {
        console.error('Error running settings tool:', error);
        messageEl.textContent = 'Error running tool. Please try again.';
        showToast('Action Failed', 'Error running tool. Please try again.', 'error', 7000);
    } finally {
        button.disabled = false;
    }
}

async function refreshDownloadedLogos() {
    await runSettingsTool('/api/settings/refresh-logos', 'refresh-logos-btn', 'Logos refreshed successfully.');
}

async function updateRankingsFromTankathon() {
    await runSettingsTool('/api/settings/update-rankings', 'update-rankings-btn', 'Tankathon data fetched and imported.');
    loadRankBoardSettings();
}

async function recalculatePlayerRankings() {
    await runSettingsTool('/api/settings/recalculate-player-rankings', 'recalculate-rankings-btn', 'Player rankings recalculated.');
    loadRankBoardSettings();
}

async function importConsensusBoard() {
    await runSettingsTool('/api/settings/import-consensus-board', 'import-consensus-btn', 'Consensus board imported successfully.');
    loadRankBoardSettings();
}

function openImportNflmockUrlDialog() {
    const dialog = document.getElementById('import-nflmock-url-dialog');
    const input = document.getElementById('nflmock-board-url-input');
    const customNameInput = document.getElementById('nflmock-board-custom-name-input');
    const message = document.getElementById('nflmock-url-message');

    if (!dialog || !input || !message) {
        return;
    }

    message.classList.add('hidden');
    message.textContent = '';
    input.value = '';
    if (customNameInput) {
        customNameInput.value = '';
    }
    dialog.classList.remove('hidden');
    input.focus();
}

function closeImportNflmockUrlDialog() {
    const dialog = document.getElementById('import-nflmock-url-dialog');
    if (dialog) {
        dialog.classList.add('hidden');
    }
}

async function importNflmockBoardByUrl() {
    const input = document.getElementById('nflmock-board-url-input');
    const customNameInput = document.getElementById('nflmock-board-custom-name-input');
    const message = document.getElementById('nflmock-url-message');
    const button = document.getElementById('confirm-import-nflmock-url-btn');
    const url = (input?.value || '').trim();
    const customBoardName = (customNameInput?.value || '').trim();

    if (!url) {
        message.textContent = 'Paste a valid NFLMockDraftDatabase big board URL.';
        message.classList.remove('hidden');
        return;
    }

    button.disabled = true;
    message.classList.remove('hidden');
    message.textContent = 'Importing board from URL...';

    try {
        const { response, data } = await requestPostJson('/api/settings/import-nflmock-board-url', {
            url,
            board_name: customBoardName || null
        });
        const result = data || {};

        if (!response.ok || !result.success) {
            const errorText = result.error || 'Could not import board from URL.';
            message.textContent = errorText;
            showToast('Import Failed', errorText, 'error', 9000);
            return;
        }

        const successText = `Imported ${result.board_name} (${result.entries_imported} players).`;
        message.textContent = successText;
        showToast('Board Imported', successText, 'success', 9000);
        closeImportNflmockUrlDialog();
        loadRankBoardSettings();
        loadStats();
        if (document.getElementById('search-tab').classList.contains('active')) {
            searchPlayers();
        }
        if (document.getElementById('bigboard-tab').classList.contains('active')) {
            loadBigBoard();
            searchBigBoardPlayers();
        }
    } catch (error) {
        console.error('Error importing URL board:', error);
        message.textContent = 'Error importing board URL. Please try again.';
        showToast('Import Failed', 'Error importing board URL. Please try again.', 'error', 9000);
    } finally {
        button.disabled = false;
    }
}

async function mergeDuplicatePlayers() {
    await runSettingsTool('/api/settings/merge-player-duplicates', 'merge-duplicates-btn', 'Duplicate player variants merged.');
    loadRankBoardSettings();
}

async function loadRankBoardSettings() {
    const container = document.getElementById('board-weights-list');
    if (!container) {
        return;
    }

    try {
        const { response, data } = await requestGetJson('/api/settings/rank-boards');
        const payload = data || {};
        if (!response.ok || !payload.success) {
            container.innerHTML = '<p class="search-empty">Unable to load board weight settings.</p>';
            return;
        }

        renderRankBoardSettings(payload.boards || []);
    } catch (error) {
        console.error('Error loading rank board settings:', error);
        container.innerHTML = '<p class="search-empty">Unable to load board weight settings.</p>';
    }
}

function renderRankBoardSettings(boards) {
    const container = document.getElementById('board-weights-list');
    const useCustomWeights = document.getElementById('use-board-weights-checkbox')?.checked;
    if (!container) {
        return;
    }

    container.innerHTML = '';
    if (!Array.isArray(boards) || boards.length === 0) {
        container.innerHTML = '<p class="search-empty">No board settings available.</p>';
        return;
    }

    boards.forEach((board, index) => {
        const row = document.createElement('div');
        row.className = 'board-weight-row';
        row.dataset.boardKey = board.board_key;

        const nameWrap = document.createElement('div');
        const name = document.createElement('div');
        name.className = 'board-weight-name';
        name.textContent = board.board_name;

        const type = document.createElement('div');
        type.className = 'board-weight-type';
        type.textContent = `${board.source_type} • ${board.player_count} players ranked`;

        nameWrap.appendChild(name);
        nameWrap.appendChild(type);

        const weightInput = document.createElement('input');
        weightInput.type = 'number';
        weightInput.step = '0.1';
        weightInput.min = '0';
        weightInput.value = Number.isFinite(Number(board.weight)) ? String(board.weight) : '1';
        weightInput.className = 'search-input board-weight-input rank-weight-input';
        weightInput.dataset.boardKey = board.board_key;
        weightInput.dataset.boardName = board.board_name;
        weightInput.title = 'Weight used in weighted average ranking';
        weightInput.setAttribute('aria-label', `Weight for ${board.board_name}`);
        weightInput.disabled = !useCustomWeights;
        weightInput.addEventListener('input', updateBoardWeightingSummary);

        const weightWrap = document.createElement('div');
        weightWrap.className = 'board-weight-value-wrap';
        const weightLabel = document.createElement('span');
        weightLabel.className = 'board-weight-input-label';
        if (useCustomWeights) {
            weightLabel.textContent = 'Weight';
        } else {
            weightInput.value = '1';
            weightLabel.textContent = 'Equal weight';
        }
        weightWrap.appendChild(weightLabel);
        weightWrap.appendChild(weightInput);

        const primaryWrap = document.createElement('label');
        primaryWrap.className = 'board-primary-select';
        const primaryRadio = document.createElement('input');
        primaryRadio.type = 'radio';
        primaryRadio.name = 'primary-rank-board';
        primaryRadio.value = board.board_key;
        primaryRadio.checked = !!board.is_primary;
        primaryRadio.dataset.boardKey = board.board_key;
        primaryRadio.addEventListener('change', updateBoardWeightingSummary);
        const primaryText = document.createElement('span');
        primaryText.className = 'board-primary-text';
        primaryText.textContent = 'Primary Default';
        primaryWrap.appendChild(primaryRadio);
        primaryWrap.appendChild(primaryText);

        const visibilityWrap = document.createElement('label');
        visibilityWrap.className = 'board-visibility-select';
        const visibilityCheckbox = document.createElement('input');
        visibilityCheckbox.type = 'checkbox';
        visibilityCheckbox.checked = isRankBoardVisible(board.board_key);
        visibilityCheckbox.setAttribute('aria-label', `Show ${board.board_name} in player ranking pills`);
        visibilityCheckbox.addEventListener('change', function() {
            setRankBoardVisibility(board.board_key, this.checked);
        });
        const visibilityText = document.createElement('span');
        visibilityText.textContent = 'Show in ranks';
        visibilityWrap.appendChild(visibilityCheckbox);
        visibilityWrap.appendChild(visibilityText);

        row.appendChild(nameWrap);
        row.appendChild(weightWrap);
        row.appendChild(primaryWrap);
        row.appendChild(visibilityWrap);
        container.appendChild(row);

        if (index === boards.length - 1 && !boards.some(item => item.is_primary) && primaryRadio) {
            primaryRadio.checked = true;
        }
    });

    updateBoardWeightingSummary();
}

function updateBoardWeightingSummary() {
    const summaryEl = document.getElementById('board-weighting-summary');
    if (!summaryEl) {
        return;
    }

    const useCustomWeights = document.getElementById('use-board-weights-checkbox')?.checked;

    const weightInputs = Array.from(document.querySelectorAll('.rank-weight-input'));
    if (!weightInputs.length) {
        summaryEl.textContent = 'No board weights loaded yet.';
        return;
    }

    const rows = weightInputs.map(input => {
        const raw = Number(input.value);
        const weight = Number.isFinite(raw) && raw > 0 ? raw : 0;
        return {
            boardKey: input.dataset.boardKey,
            boardName: input.dataset.boardName || input.dataset.boardKey,
            weight
        };
    });

    const totalWeight = useCustomWeights
        ? rows.reduce((sum, row) => sum + row.weight, 0)
        : rows.length;
    const primaryRadio = document.querySelector('input[name="primary-rank-board"]:checked');
    const primaryKey = primaryRadio ? primaryRadio.value : null;
    const primaryName = rows.find(row => row.boardKey === primaryKey)?.boardName || 'None selected';

    if (!useCustomWeights) {
        summaryEl.textContent = `Primary Default: ${primaryName}. Equal average mode is active (all boards weighted evenly).`;
        return;
    }

    if (totalWeight <= 0) {
        summaryEl.textContent = `Primary Default: ${primaryName}. Weighted Avg formula: Σ(rank × weight) ÷ Σ(weights). All current weights are 0, so weighted average is disabled.`;
        return;
    }

    const contributionText = rows
        .filter(row => row.weight > 0)
        .map(row => `${row.boardName} ${((row.weight / totalWeight) * 100).toFixed(1)}%`)
        .join(' • ');

    summaryEl.textContent = `Primary Default: ${primaryName}. Weighted Avg = Σ(rank × weight) ÷ Σ(weights). Current contributions: ${contributionText}.`;
}

async function saveRankBoardSettings() {
    const button = document.getElementById('save-board-weights-btn');
    const messageEl = document.getElementById('board-import-message');
    const useCustomWeights = document.getElementById('use-board-weights-checkbox')?.checked;
    const weightInputs = Array.from(document.querySelectorAll('.rank-weight-input'));
    const primaryRadio = document.querySelector('input[name="primary-rank-board"]:checked');

    if (!weightInputs.length) {
        messageEl.textContent = 'No board weights to save yet.';
        messageEl.classList.remove('hidden');
        return;
    }

    const updates = weightInputs.map(input => ({
        board_key: input.dataset.boardKey,
        weight: useCustomWeights ? parseFloat(input.value || '0') : 1,
        is_primary: primaryRadio ? primaryRadio.value === input.dataset.boardKey : false
    }));

    button.disabled = true;
    try {
        const { response, data } = await requestPostJson('/api/settings/rank-boards', { boards: updates });
        const result = data || {};

        if (!response.ok || !result.success) {
            const errorText = result.error || 'Could not save board settings.';
            messageEl.textContent = errorText;
            messageEl.classList.remove('hidden');
            showToast('Save Failed', errorText, 'error', 7000);
            return;
        }

        messageEl.textContent = 'Board weights updated.';
        messageEl.classList.remove('hidden');
        showToast('Board Settings Saved', 'Weights and primary default board updated.', 'success', 5000);
        await loadRankBoardSettings();
        loadStats();
        if (document.getElementById('search-tab').classList.contains('active')) {
            searchPlayers();
        }
        if (document.getElementById('bigboard-tab').classList.contains('active')) {
            loadBigBoard();
            searchBigBoardPlayers();
        }
    } catch (error) {
        console.error('Error saving rank board settings:', error);
        messageEl.textContent = 'Error saving board settings. Please try again.';
        messageEl.classList.remove('hidden');
    } finally {
        button.disabled = false;
    }
}

function handleBoardFilesSelected(event) {
    const files = Array.from(event.target.files || []);
    importedBoardFiles = files.map(file => ({
        file,
        weight: 1
    }));
    renderImportedBoardList();
}

function renderImportedBoardList() {
    const container = document.getElementById('board-import-list');
    const useWeights = document.getElementById('use-board-weights-checkbox').checked;
    if (!container) {
        return;
    }

    container.innerHTML = '';

    if (!importedBoardFiles.length) {
        container.classList.add('hidden');
        return;
    }

    container.classList.remove('hidden');

    importedBoardFiles.forEach((boardFile, index) => {
        const row = document.createElement('div');
        row.className = 'board-import-row';

        const name = document.createElement('div');
        name.className = 'board-import-name';
        name.textContent = boardFile.file.name;

        const weightWrap = document.createElement('div');
        weightWrap.className = 'board-import-weight-wrap';

        const weightLabel = document.createElement('label');
        weightLabel.textContent = 'Weight';
        weightLabel.setAttribute('for', `board-weight-${index}`);

        const weightInput = document.createElement('input');
        weightInput.id = `board-weight-${index}`;
        weightInput.type = 'number';
        weightInput.step = '0.1';
        weightInput.min = '0.1';
        weightInput.value = String(boardFile.weight || 1);
        weightInput.className = 'search-input board-weight-input imported-board-weight-input';
        weightInput.disabled = !useWeights;
        weightInput.addEventListener('input', function() {
            const parsed = parseFloat(this.value);
            importedBoardFiles[index].weight = Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
        });

        if (useWeights) {
            weightWrap.appendChild(weightLabel);
            weightWrap.appendChild(weightInput);
        } else {
            const equalWeightNote = document.createElement('span');
            equalWeightNote.className = 'search-empty';
            equalWeightNote.textContent = 'Equal weight';
            weightWrap.appendChild(equalWeightNote);
        }
        row.appendChild(name);
        row.appendChild(weightWrap);
        container.appendChild(row);
    });
}

function syncBoardWeightInputs() {
    renderImportedBoardList();
    loadRankBoardSettings();
}

async function importAndNormalizeBigBoards() {
    const button = document.getElementById('import-big-boards-btn');
    const messageEl = document.getElementById('board-import-message');
    const useWeights = document.getElementById('use-board-weights-checkbox').checked;

    if (!importedBoardFiles.length) {
        messageEl.textContent = 'Select at least one .txt file to import.';
        messageEl.classList.remove('hidden');
        return;
    }

    messageEl.classList.remove('hidden');
    messageEl.textContent = 'Importing and normalizing rankings...';
    button.disabled = true;

    try {
        const boardsPayload = [];

        for (const boardFile of importedBoardFiles) {
            const text = await boardFile.file.text();
            boardsPayload.push({
                name: boardFile.file.name,
                text,
                weight: boardFile.weight
            });
        }

        const { response, data } = await requestPostJson('/api/settings/import-big-boards', {
            weighting_mode: useWeights ? 'weighted' : 'equal',
            boards: boardsPayload
        });

        const result = data || {};
        if (!response.ok || !result.success) {
            const errorText = result.error || 'Failed to import boards.';
            messageEl.textContent = errorText;
            showToast('Import Failed', errorText, 'error', 9000);
            return;
        }

        const summary = `${result.players_ranked_from_import} players normalized from ${result.boards_processed} board(s). Unmatched names: ${result.unmatched_count}.`;
        messageEl.textContent = summary;
        showToast('Big Boards Imported', summary, 'success', 9000);

        loadRankBoardSettings();
        loadStats();
        loadPositions();
        loadSchools();
        if (document.getElementById('search-tab').classList.contains('active')) {
            searchPlayers();
        }
        if (document.getElementById('bigboard-tab').classList.contains('active')) {
            loadBigBoard();
            searchBigBoardPlayers();
        }
    } catch (error) {
        console.error('Error importing big boards:', error);
        messageEl.textContent = 'Error importing boards. Please try again.';
        showToast('Import Failed', 'Error importing boards. Please try again.', 'error', 9000);
    } finally {
        button.disabled = false;
    }
}

async function exportNormalizedBigBoard(scope) {
    const positionSelect = document.getElementById('export-position-select');
    const messageEl = document.getElementById('board-import-message');
    const params = new URLSearchParams();
    params.append('scope', scope);

    if (scope === 'position') {
        const position = (positionSelect.value || '').trim();
        if (!position) {
            messageEl.textContent = 'Select a position before exporting a positional board.';
            messageEl.classList.remove('hidden');
            return;
        }
        params.append('position', position);
    }

    try {
        const response = await fetch(`/api/settings/export-big-board?${params.toString()}`);
        if (!response.ok) {
            let errorText = 'Failed to export board.';
            try {
                const errorJson = await response.json();
                errorText = errorJson.error || errorText;
            } catch {
                // no-op
            }
            messageEl.textContent = errorText;
            messageEl.classList.remove('hidden');
            showToast('Export Failed', errorText, 'error', 7000);
            return;
        }

        const text = await response.text();
        const filename = scope === 'position'
            ? `big_board_${positionSelect.value.toLowerCase()}.txt`
            : 'big_board_overall.txt';

        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);

        const successMessage = scope === 'position'
            ? `Exported ${positionSelect.value} board.`
            : 'Exported overall board.';
        messageEl.textContent = successMessage;
        messageEl.classList.remove('hidden');
        showToast('Export Complete', successMessage, 'success', 5000);
    } catch (error) {
        console.error('Error exporting big board:', error);
        messageEl.textContent = 'Error exporting board. Please try again.';
        messageEl.classList.remove('hidden');
        showToast('Export Failed', 'Error exporting board. Please try again.', 'error', 7000);
    }
}

function loadAppSettings() {
    try {
        const saved = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (!saved) {
            appSettings = { ...DEFAULT_APP_SETTINGS };
            return;
        }

        const parsed = JSON.parse(saved);
        const validThemes = ['default', 'light', 'dark', 'nfl-team', 'neon-night', 'gridiron-dark', 'pigskin-classic'];
        const validSystems = ['round', 'poker', 'numerical', 'alphabet'];
        const normalizedSystems = Array.isArray(parsed.gradingSystems)
            ? parsed.gradingSystems.filter(system => validSystems.includes(system)).slice(0, 2)
            : [];
        const hiddenRankBoardKeys = Array.isArray(parsed.hiddenRankBoardKeys)
            ? parsed.hiddenRankBoardKeys.filter(key => typeof key === 'string' && key.trim())
            : [];

        const parsedTheme = validThemes.includes(parsed.theme) ? parsed.theme : DEFAULT_APP_SETTINGS.theme;
        const normalizedTheme = parsedTheme === 'neon-night' ? 'default' :
            (parsedTheme === 'gridiron-dark' || parsedTheme === 'pigskin-classic' ? 'dark' : parsedTheme);

        appSettings = {
            theme: normalizedTheme,
            teamCity: NFL_TEAM_CITY_THEMES[parsed.teamCity] ? parsed.teamCity : DEFAULT_APP_SETTINGS.teamCity,
            font: parsed.font || DEFAULT_APP_SETTINGS.font,
            gradingSystems: normalizedSystems.length
                ? normalizedSystems
                : [...DEFAULT_APP_SETTINGS.gradingSystems],
            showConsensusGradeOnBigBoard: Boolean(parsed.showConsensusGradeOnBigBoard),
            hiddenRankBoardKeys
        };
    } catch (error) {
        console.error('Error loading app settings:', error);
        appSettings = { ...DEFAULT_APP_SETTINGS };
    }
}

function saveAppSettings() {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(appSettings));
}

function isRankBoardVisible(boardKey) {
    if (!boardKey) {
        return true;
    }

    const hiddenKeys = Array.isArray(appSettings.hiddenRankBoardKeys)
        ? appSettings.hiddenRankBoardKeys
        : [];
    return !hiddenKeys.includes(boardKey);
}

function setRankBoardVisibility(boardKey, isVisible) {
    if (!boardKey) {
        return;
    }

    const hiddenKeys = new Set(Array.isArray(appSettings.hiddenRankBoardKeys)
        ? appSettings.hiddenRankBoardKeys
        : []);

    if (isVisible) {
        hiddenKeys.delete(boardKey);
    } else {
        hiddenKeys.add(boardKey);
    }

    appSettings.hiddenRankBoardKeys = Array.from(hiddenKeys);
    saveAppSettings();

    if (currentPlayer) {
        renderPlayerBoardRanks(currentPlayer);
        applyBoardRanksVisibility();
    }
}

function applyVisualSettings() {
    const theme = appSettings.theme || DEFAULT_APP_SETTINGS.theme;
    document.body.setAttribute('data-theme', theme);
    document.body.setAttribute('data-font', appSettings.font || DEFAULT_APP_SETTINGS.font);

    const cssVars = [
        '--primary-color', '--secondary-color', '--accent-color', '--highlight-color',
        '--success-color', '--warning-color', '--text-primary', '--text-secondary'
    ];

    if (theme === 'nfl-team') {
        const city = appSettings.teamCity && NFL_TEAM_CITY_THEMES[appSettings.teamCity]
            ? appSettings.teamCity
            : DEFAULT_APP_SETTINGS.teamCity;
        const palette = NFL_TEAM_CITY_THEMES[city];

        document.body.style.setProperty('--primary-color', palette.primary);
        document.body.style.setProperty('--secondary-color', palette.secondary);
        document.body.style.setProperty('--accent-color', palette.accent);
        document.body.style.setProperty('--highlight-color', palette.highlight);
        document.body.style.setProperty('--success-color', palette.highlight);
        document.body.style.setProperty('--warning-color', palette.accent);
        document.body.style.setProperty('--text-primary', palette.textPrimary);
        document.body.style.setProperty('--text-secondary', palette.textSecondary);
        document.body.style.background = `linear-gradient(135deg, ${palette.bgStart} 0%, ${palette.bgEnd} 100%)`;
    } else {
        cssVars.forEach(cssVar => document.body.style.removeProperty(cssVar));
        document.body.style.background = '';
    }

    applyReadableSurfaceTextVars();
}

function parseCssColorToRgb(colorString) {
    if (!colorString) {
        return null;
    }

    const trimmed = colorString.trim();
    if (trimmed.startsWith('#')) {
        let hex = trimmed.slice(1);
        if (hex.length === 3) {
            hex = hex.split('').map(ch => ch + ch).join('');
        }
        if (hex.length !== 6) {
            return null;
        }
        return {
            r: parseInt(hex.slice(0, 2), 16),
            g: parseInt(hex.slice(2, 4), 16),
            b: parseInt(hex.slice(4, 6), 16)
        };
    }

    const match = trimmed.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
    if (!match) {
        return null;
    }

    return {
        r: Number(match[1]),
        g: Number(match[2]),
        b: Number(match[3])
    };
}

function getReadableTextColor(backgroundColor) {
    const rgb = parseCssColorToRgb(backgroundColor);
    if (!rgb) {
        return '#ffffff';
    }

    const toLinear = (value) => {
        const normalized = value / 255;
        return normalized <= 0.03928
            ? normalized / 12.92
            : Math.pow((normalized + 0.055) / 1.055, 2.4);
    };

    const luminance = 0.2126 * toLinear(rgb.r) + 0.7152 * toLinear(rgb.g) + 0.0722 * toLinear(rgb.b);
    return luminance > 0.58 ? '#111111' : '#ffffff';
}

function applyReadableSurfaceTextVars() {
    const computed = getComputedStyle(document.body);
    const accent = computed.getPropertyValue('--accent-color');
    const highlight = computed.getPropertyValue('--highlight-color');
    const secondary = computed.getPropertyValue('--secondary-color');
    const success = computed.getPropertyValue('--success-color');
    const warning = computed.getPropertyValue('--warning-color');

    document.body.style.setProperty('--text-on-accent', getReadableTextColor(accent));
    document.body.style.setProperty('--text-on-highlight', getReadableTextColor(highlight));
    document.body.style.setProperty('--text-on-secondary', getReadableTextColor(secondary));
    document.body.style.setProperty('--text-on-success', getReadableTextColor(success));
    document.body.style.setProperty('--text-on-warning', getReadableTextColor(warning));
}

function syncSettingsControls() {
    const themeSelect = document.getElementById('theme-select');
    const teamSelect = document.getElementById('theme-team-select');
    const fontSelect = document.getElementById('font-select');
    const showConsensusGradeCheckbox = document.getElementById('show-consensus-grade-checkbox');
    if (themeSelect) {
        themeSelect.value = appSettings.theme;
    }
    if (teamSelect) {
        teamSelect.value = appSettings.teamCity;
    }
    if (fontSelect) {
        fontSelect.value = appSettings.font;
    }
    if (showConsensusGradeCheckbox) {
        showConsensusGradeCheckbox.checked = !!appSettings.showConsensusGradeOnBigBoard;
    }

    toggleTeamThemeSelector();
    updateThemeSelectCurrentLabel();

    const checkboxes = document.querySelectorAll('.grading-system-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = appSettings.gradingSystems.includes(checkbox.value);
    });
}

function toggleTeamThemeSelector() {
    const teamGroup = document.getElementById('theme-team-group');
    if (!teamGroup) {
        return;
    }
    teamGroup.classList.toggle('hidden', appSettings.theme !== 'nfl-team');
}

function updateThemeSelectCurrentLabel() {
    const themeSelect = document.getElementById('theme-select');
    if (!themeSelect) {
        return;
    }

    Array.from(themeSelect.options).forEach(option => {
        const baseLabel = option.dataset.baseLabel || option.textContent.replace(/\s+\(Current\)$/i, '');
        option.dataset.baseLabel = baseLabel;
        option.textContent = option.value === themeSelect.value
            ? `${baseLabel} (Current)`
            : baseLabel;
    });
}

function handleGradingSystemsChange(event) {
    const checkbox = event.target;
    const messageEl = document.getElementById('grading-systems-message');
    const selected = Array.from(document.querySelectorAll('.grading-system-checkbox:checked')).map(c => c.value);

    if (selected.length > 2) {
        checkbox.checked = false;
        messageEl.textContent = 'You can select up to 2 grading systems.';
        messageEl.classList.remove('hidden');
        return;
    }

    if (selected.length === 0) {
        checkbox.checked = true;
        messageEl.textContent = 'Select at least one grading system.';
        messageEl.classList.remove('hidden');
        return;
    }

    messageEl.classList.add('hidden');
    appSettings.gradingSystems = selected;
    saveAppSettings();
    populateGradeDropdowns();
}

function getSystemDisplayName(system) {
    if (system === 'round') return 'Round Grade';
    if (system === 'poker') return 'Poker Chip Grade';
    if (system === 'numerical') return 'Numerical Grade';
    if (system === 'alphabet') return 'Alphabet Grade';
    return 'Grade';
}

function parseNumericalGradeValue(rawGrade) {
    if (rawGrade === null || rawGrade === undefined) {
        return '';
    }

    const gradeText = String(rawGrade).trim();
    if (!gradeText) {
        return '';
    }

    const prefixedMatch = gradeText.match(/^numerical\s*-\s*(\d{1,3})$/i);
    if (prefixedMatch) {
        const value = Number(prefixedMatch[1]);
        const clamped = Math.max(0, Math.min(100, value));
        return String(clamped);
    }

    const numericValue = Number(gradeText);
    if (!Number.isFinite(numericValue)) {
        return '';
    }

    const clamped = Math.max(0, Math.min(100, Math.round(numericValue)));
    return String(clamped);
}

function formatGradeForSystem(system, rawValue) {
    const systemKey = (system || '').trim().toLowerCase();
    const valueText = rawValue === null || rawValue === undefined ? '' : String(rawValue).trim();

    if (systemKey === 'numerical') {
        const parsed = parseNumericalGradeValue(valueText);
        return parsed ? `Numerical - ${parsed}` : '';
    }

    return valueText;
}

function getGradeSystemForSlot(slot = 'primary') {
    const systems = (appSettings.gradingSystems || ['round']).slice(0, 2);
    return slot === 'secondary' ? (systems[1] || '') : (systems[0] || 'round');
}

function buildGradeOptionsForSystem(system) {
    const options = [{ value: '', label: 'Not Graded' }];

    if (system === 'round') {
        [
            'Early-Round 1', 'Mid-Round 1', 'Late-Round 1',
            'Early-Round 2', 'Mid-Round 2', 'Late-Round 2',
            'Early-Round 3', 'Mid-Round 3', 'Late-Round 3',
            'Early-Round 4', 'Mid-Round 4', 'Late-Round 4',
            'Early-Round 5', 'Mid-Round 5', 'Late-Round 5',
            'Early-Round 6', 'Mid-Round 6', 'Late-Round 6',
            'Early-Round 7', 'Mid-Round 7', 'Late-Round 7',
            'UDFA (Undrafted Free Agent)'
        ].forEach(roundGrade => {
            options.push({ value: roundGrade, label: roundGrade });
        });
    }

    if (system === 'poker') {
        ['Purple', 'Black', 'Blue', 'Green', 'Red', 'White'].forEach(chip => {
            options.push({ value: `Poker Chip - ${chip}`, label: `Poker Chip - ${chip}` });
        });
    }

    if (system === 'numerical') {
        for (let score = 100; score >= 0; score -= 1) {
            options.push({ value: `Numerical - ${score}`, label: `Numerical - ${score}` });
        }
    }

    if (system === 'alphabet') {
        ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F+', 'F', 'F-'].forEach(alpha => {
            options.push({ value: `Alphabet - ${alpha}`, label: `Alphabet - ${alpha}` });
        });
    }

    return options;
}

function populateSelectOptions(selectEl, options, selectedValue = '') {
    if (!selectEl) {
        return;
    }

    selectEl.innerHTML = '';

    options.forEach(optionData => {
        const option = document.createElement('option');
        option.value = optionData.value;
        option.textContent = optionData.label;
        selectEl.appendChild(option);
    });

    if (selectedValue && !options.some(option => option.value === selectedValue)) {
        const legacyOption = document.createElement('option');
        legacyOption.value = selectedValue;
        legacyOption.textContent = selectedValue;
        selectEl.appendChild(legacyOption);
    }

    selectEl.value = selectedValue || '';
}

function populateGradeDropdowns(playerGrade = null) {
    const systems = (appSettings.gradingSystems || ['round']).slice(0, 2);
    const playerPrimaryGrade = playerGrade !== null
        ? playerGrade
        : (currentPlayer && currentPlayer.grade ? currentPlayer.grade : '');
    const playerSecondaryGrade = currentPlayer && currentPlayer.grade_secondary ? currentPlayer.grade_secondary : '';

    const playerGradeSelect1 = document.getElementById('grade-dropdown-1');
    const playerGradeSelect2 = document.getElementById('grade-dropdown-2');
    const playerGradeInput1 = document.getElementById('grade-input-1');
    const playerGradeInput2 = document.getElementById('grade-input-2');
    const settingsGradeSelect = document.getElementById('settings-grade');
    const settingsGradeInput = document.getElementById('settings-grade-input');
    const gradeSlot1 = document.getElementById('grade-slot-1');
    const gradeSlot2 = document.getElementById('grade-slot-2');
    const gradeLabel1 = document.getElementById('grade-label-1');
    const gradeLabel2 = document.getElementById('grade-label-2');

    const system1 = systems[0] || 'round';
    if (system1 === 'numerical') {
        if (playerGradeSelect1) {
            playerGradeSelect1.classList.add('hidden');
        }
        if (playerGradeInput1) {
            playerGradeInput1.classList.remove('hidden');
            playerGradeInput1.value = parseNumericalGradeValue(playerPrimaryGrade);
        }
    } else {
        const options1 = buildGradeOptionsForSystem(system1);
        populateSelectOptions(playerGradeSelect1, options1, playerPrimaryGrade);
        if (playerGradeInput1) {
            playerGradeInput1.classList.add('hidden');
            playerGradeInput1.value = '';
        }
        if (playerGradeSelect1) {
            playerGradeSelect1.classList.remove('hidden');
        }
    }

    gradeLabel1.textContent = getSystemDisplayName(system1);
    gradeSlot1.classList.remove('hidden');

    if (systems.length > 1) {
        const system2 = systems[1];
        if (system2 === 'numerical') {
            if (playerGradeSelect2) {
                playerGradeSelect2.classList.add('hidden');
            }
            if (playerGradeInput2) {
                playerGradeInput2.classList.remove('hidden');
                playerGradeInput2.value = parseNumericalGradeValue(playerSecondaryGrade);
            }
        } else {
            const options2 = buildGradeOptionsForSystem(system2);
            populateSelectOptions(playerGradeSelect2, options2, playerSecondaryGrade);
            if (playerGradeInput2) {
                playerGradeInput2.classList.add('hidden');
                playerGradeInput2.value = '';
            }
            if (playerGradeSelect2) {
                playerGradeSelect2.classList.remove('hidden');
            }
        }

        gradeLabel2.textContent = getSystemDisplayName(system2);
        gradeSlot2.classList.remove('hidden');
    } else {
        populateSelectOptions(playerGradeSelect2, [{ value: '', label: 'Not Graded' }], '');
        if (playerGradeInput2) {
            playerGradeInput2.classList.add('hidden');
            playerGradeInput2.value = '';
        }
        if (playerGradeSelect2) {
            playerGradeSelect2.classList.remove('hidden');
        }
        gradeSlot2.classList.add('hidden');
    }

    if (system1 === 'numerical') {
        if (settingsGradeSelect) {
            settingsGradeSelect.classList.add('hidden');
        }
        if (settingsGradeInput) {
            settingsGradeInput.classList.remove('hidden');
            settingsGradeInput.value = parseNumericalGradeValue(settingsGradeInput.value || settingsGradeSelect?.value || '');
        }
    } else {
        const settingsOptions = buildGradeOptionsForSystem(system1);
        populateSelectOptions(settingsGradeSelect, settingsOptions, settingsGradeSelect ? settingsGradeSelect.value : '');
        if (settingsGradeInput) {
            settingsGradeInput.classList.add('hidden');
            settingsGradeInput.value = '';
        }
        if (settingsGradeSelect) {
            settingsGradeSelect.classList.remove('hidden');
        }
    }
}

function setBigBoardType(type) {
    if (!bigBoardController) {
        return;
    }
    bigBoardController.setBigBoardType(type);
}

function getBigBoardParams() {
    if (bigBoardController) {
        return bigBoardController.getBigBoardParams();
    }
    return bigBoardType === 'position'
        ? { type: 'position', position: currentBigBoardPosition }
        : { type: 'overall' };
}

function hasAnyGrade(player) {
    if (!player) {
        return false;
    }
    return Boolean((player.grade || '').trim() || (player.grade_secondary || '').trim());
}

function getPreferredOverallRank(player) {
    if (!player) {
        return null;
    }

    const directRank = Number(player.rank);
    if (Number.isFinite(directRank) && directRank > 0) {
        return Math.round(directRank);
    }

    const weightedRank = Number(player.weighted_avg_rank ?? player.weighted_average_rank);
    if (Number.isFinite(weightedRank) && weightedRank > 0) {
        return Math.round(weightedRank);
    }

    const tankathonRank = Number(player.tankathon_rank);
    if (Number.isFinite(tankathonRank) && tankathonRank > 0) {
        return Math.round(tankathonRank);
    }

    return null;
}

function comparePlayersForBigBoardAdd(a, b) {
    const aPriority = a.scouted ? 0 : (hasAnyGrade(a) ? 1 : 2);
    const bPriority = b.scouted ? 0 : (hasAnyGrade(b) ? 1 : 2);

    if (aPriority !== bPriority) {
        return aPriority - bPriority;
    }

    const aRank = Number.isFinite(Number(a.rank)) ? Number(a.rank) : Number.MAX_SAFE_INTEGER;
    const bRank = Number.isFinite(Number(b.rank)) ? Number(b.rank) : Number.MAX_SAFE_INTEGER;
    if (aRank !== bRank) {
        return aRank - bRank;
    }

    return (a.name || '').localeCompare(b.name || '');
}

async function loadBigBoard() {
    if (!bigBoardController) {
        return;
    }
    await bigBoardController.loadBigBoard();
}

function renderBigBoard(entries) {
    return entries;
}

async function openBigBoardPlayerReport(playerId) {
    if (!bigBoardController) {
        return;
    }
    await bigBoardController.openBigBoardPlayerReport(playerId);
}

function closeBigBoardPlayerReportModal() {
    closePlayerReport();
}

function closePlayerReport() {
    const overlay = document.getElementById('player-report-overlay');
    const detailsSection = document.getElementById('player-details');

    overlay.classList.add('hidden');
    detailsSection.classList.remove('modal-mode');

    currentPlayer = null;
    currentPlayerSourceTab = null;
    updatePlayerDetailsVisibility();

    const activeTab = document.querySelector('.tab-panel.active')?.id;
    if (activeTab === 'search-tab') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

async function searchBigBoardPlayers() {
    if (!bigBoardController) {
        return;
    }
    await bigBoardController.searchBigBoardPlayers();
}

async function confirmAddToRank() {
    if (!bigBoardController) {
        return;
    }
    await bigBoardController.confirmAddToRank();
}

async function confirmAddToBottom() {
    if (!bigBoardController) {
        return;
    }
    await bigBoardController.confirmAddToBottom();
}

async function autoSortBigBoard() {
    if (!bigBoardController) {
        return;
    }
    await bigBoardController.autoSortBigBoard();
}

async function removePlayerFromBigBoard(playerId) {
    if (!bigBoardController) {
        return;
    }
    await bigBoardController.removePlayerFromBigBoard(playerId);
}

function closeAddToBoardDialog() {
    if (!bigBoardController) {
        return;
    }
    bigBoardController.closeAddToBoardDialog();
}

async function addPlayerFromSettings() {
    const messageEl = document.getElementById('settings-message');
    const addBtn = document.getElementById('settings-add-player-btn');

    const payload = {
        name: document.getElementById('settings-name').value.trim(),
        rank: document.getElementById('settings-rank').value ? parseInt(document.getElementById('settings-rank').value, 10) : null,
        position: document.getElementById('settings-position').value.trim(),
        school: document.getElementById('settings-school').value.trim(),
        height: document.getElementById('settings-height').value.trim(),
        weight: document.getElementById('settings-weight').value.trim(),
        jersey_number: document.getElementById('settings-jersey').value.trim(),
        player_url: document.getElementById('settings-url').value.trim(),
        grade: formatGradeForSystem(
            getGradeSystemForSlot('primary'),
            document.getElementById('settings-grade-input')?.classList.contains('hidden')
                ? document.getElementById('settings-grade').value
                : document.getElementById('settings-grade-input').value
        ),
        notes: document.getElementById('settings-notes').value.trim(),
        scouted: document.getElementById('settings-scouted').checked
    };

    if (!payload.name) {
        messageEl.textContent = 'Player name is required.';
        messageEl.classList.remove('hidden');
        return;
    }

    addBtn.disabled = true;
    messageEl.classList.add('hidden');

    try {
        const { response, data } = await requestPostJson('/api/settings/player', payload);
        const result = data || {};

        if (!response.ok || !result.success) {
            messageEl.textContent = result.error || 'Could not add player.';
            messageEl.classList.remove('hidden');
            return;
        }

        messageEl.textContent = 'Player added successfully.';
        messageEl.classList.remove('hidden');

        document.getElementById('settings-name').value = '';
        document.getElementById('settings-rank').value = '';
        document.getElementById('settings-position').value = '';
        document.getElementById('settings-school').value = '';
        document.getElementById('settings-height').value = '';
        document.getElementById('settings-weight').value = '';
        document.getElementById('settings-jersey').value = '';
        document.getElementById('settings-url').value = '';
        document.getElementById('settings-grade').value = '';
        const settingsGradeInput = document.getElementById('settings-grade-input');
        if (settingsGradeInput) {
            settingsGradeInput.value = '';
        }
        document.getElementById('settings-notes').value = '';
        document.getElementById('settings-scouted').checked = false;

        loadStats();
        loadPositions();
        loadSchools();
        if (document.getElementById('bigboard-tab').classList.contains('active')) {
            searchBigBoardPlayers();
        }
    } catch (error) {
        console.error('Error adding player from settings:', error);
        messageEl.textContent = 'Error adding player. Please try again.';
        messageEl.classList.remove('hidden');
    } finally {
        addBtn.disabled = false;
    }
}

function applyBoardRanksVisibility() {
    const ranksContainer = document.getElementById('player-board-ranks');
    const toggleValue = document.getElementById('board-ranks-toggle-value');
    const toggleBadge = document.getElementById('player-board-ranks-toggle');

    if (!ranksContainer || !toggleValue || !toggleBadge) {
        return;
    }

    ranksContainer.classList.toggle('hidden', !boardRanksRevealed);
    toggleValue.textContent = boardRanksRevealed ? 'Shown' : 'Hidden';
    toggleBadge.classList.toggle('revealed', boardRanksRevealed);
}

function toggleBoardRanksVisibility() {
    boardRanksRevealed = !boardRanksRevealed;
    applyBoardRanksVisibility();
}

// Toggle position filter
function togglePosition(event) {
    const btn = event.target;
    const position = btn.dataset.position;
 
    btn.classList.toggle('active');
 
    if (selectedPositions.includes(position)) {
        selectedPositions = selectedPositions.filter(p => p !== position);
    } else {
        selectedPositions.push(position);
    }
}

function toggleSearchPosition(event) {
    const btn = event.target;
    const position = btn.dataset.position;

    btn.classList.toggle('active');

    if (selectedSearchPositions.includes(position)) {
        selectedSearchPositions = selectedSearchPositions.filter(p => p !== position);
    } else {
        selectedSearchPositions.push(position);
    }
}

async function searchPlayers() {
    const searchBtn = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('search-results');
    const nameSearch = document.getElementById('search-input').value.trim();
    const schoolSearch = document.getElementById('school-search-input').value.trim();
    const includeScouted = document.getElementById('search-include-scouted').checked;

    if (currentPlayerSourceTab === 'search-tab') {
        closePlayerReport();
    }

    searchBtn.disabled = true;

    try {
        const params = new URLSearchParams();
        selectedSearchPositions.forEach(pos => params.append('positions[]', pos));
        if (nameSearch) {
            params.append('name', nameSearch);
        }
        if (schoolSearch) {
            params.append('school', schoolSearch);
        }
        params.append('include_scouted', includeScouted ? 'true' : 'false');

        const { data } = await requestGetJson(`/api/players?${params.toString()}`);
        const players = data;

        renderSearchResults(players);

        if (!Array.isArray(players) || players.length === 0) {
            resultsContainer.innerHTML = '<p class="search-empty">No players matched your search criteria.</p>';
        }
    } catch (error) {
        console.error('Error searching players:', error);
        resultsContainer.innerHTML = '<p class="search-empty">Error loading search results. Please try again.</p>';
    } finally {
        searchBtn.disabled = false;
    }
}

function renderSearchResults(players) {
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '';

    if (!Array.isArray(players) || players.length === 0) {
        return;
    }

    players.forEach(player => {
        const card = document.createElement('div');
        card.className = 'search-result-card';

        const name = document.createElement('div');
        name.className = 'search-result-name';
        name.textContent = player.name;

        const meta = document.createElement('div');
        meta.className = 'search-result-meta';
        const positionText = player.position || 'N/A';
        const schoolText = player.school || 'Unknown School';
        const metaParts = [positionText, schoolText];
        const preferredRank = getPreferredOverallRank(player);
        const rankText = preferredRank ? `#${preferredRank}` : 'Unranked';
        metaParts.push(rankText);
        meta.textContent = metaParts.join(' • ');

        card.appendChild(name);
        card.appendChild(meta);

        card.addEventListener('click', () => loadPlayerReport(player.id));
        resultsContainer.appendChild(card);
    });
}

async function loadPlayerReport(playerId) {
    try {
        const { response, data } = await requestGetJson(`/api/player/${playerId}`);
        const player = data || {};

        if (!response.ok || player.error) {
            showToast('Load Failed', player.error || 'Unable to load scout report.', 'error', 6000);
            return;
        }

        currentPlayer = player;
        currentPlayerSourceTab = 'search-tab';
        displayPlayerDetails(player);
    } catch (error) {
        console.error('Error loading player report:', error);
        showToast('Load Failed', 'Error loading scout report. Please try again.', 'error', 6000);
    }
}

// Randomize player with animation
async function randomizePlayer() {
    const randomizeBtn = document.getElementById('randomize-btn');
    randomizeBtn.disabled = true;
 
    try {
        // Build query parameters
        const params = new URLSearchParams();
        selectedPositions.forEach(pos => params.append('positions[]', pos));
        if (selectedRank) {
            params.append('max_rank', selectedRank);
        }
     
        // Fetch eligible players
        const playersResponse = await requestGetJson(`/api/players?${params.toString()}`);
        allPlayers = playersResponse.data || [];
     
        if (allPlayers.length === 0) {
            showToast('No Players Found', 'No players available with current filters.', 'error', 5000);
            randomizeBtn.disabled = false;
            return;
        }
     
        // Get random player
        const { data } = await requestGetJson(`/api/random?${params.toString()}`);
        const player = data || {};
     
        if (player.error) {
            showToast('Randomize Failed', player.error, 'error', 5000);
            randomizeBtn.disabled = false;
            return;
        }
     
        currentPlayer = player;
        currentPlayerSourceTab = 'randomizer-tab';
     
        // Show and animate case opening
        await animateCaseOpening(player);
     
        // Display player details
        displayPlayerDetails(player);
     
        // Reload stats
        loadStats();
     
    } catch (error) {
        console.error('Error randomizing player:', error);
        showToast('Randomize Failed', 'Error selecting player. Please try again.', 'error', 6000);
    } finally {
        randomizeBtn.disabled = false;
    }
}

// Animate CS:GO style case opening
async function animateCaseOpening(selectedPlayer) {
    const caseAnimation = document.getElementById('case-animation');
    const itemsStrip = document.getElementById('items-strip');
 
    // Show animation container
    caseAnimation.classList.remove('hidden');
 
    // Generate random items strip
    const items = [];
    const numItems = 50;
 
    // Fill with random schools from available players
    for (let i = 0; i < numItems; i++) {
        const randomPlayer = allPlayers[Math.floor(Math.random() * allPlayers.length)];
        items.push({
            school: randomPlayer.school || 'Unknown',
            name: randomPlayer.name
        });
    }
 
    // Insert selected player near the end
    const selectedIndex = Math.floor(numItems * 0.7) + Math.floor(Math.random() * 5);
    items[selectedIndex] = {
        school: selectedPlayer.school || 'Unknown',
        name: selectedPlayer.name
    };
 
    // Create item elements
    itemsStrip.innerHTML = '';
    items.forEach((item, index) => {
        const itemEl = document.createElement('div');
        itemEl.className = 'case-item';
        if (index === selectedIndex) {
            itemEl.classList.add('will-select');
        }
     
        const logo = document.createElement('div');
        logo.className = 'case-item-logo';
     
        // Try to load school logo image
        const logoPath = getSchoolLogo(item.school);
        if (logoPath) {
            const img = document.createElement('img');
            img.src = logoPath;
            img.alt = item.school;
            img.onerror = function() {
                // Fallback to emoji if image fails
                logo.innerHTML = schoolLogos[item.school] || schoolLogos['default'];
            };
            logo.appendChild(img);
        } else {
            logo.textContent = schoolLogos[item.school] || schoolLogos['default'];
        }
     
        const name = document.createElement('div');
        name.className = 'case-item-name';
        name.textContent = item.school;
     
        itemEl.appendChild(logo);
        itemEl.appendChild(name);
        itemsStrip.appendChild(itemEl);
    });
 
    // Reset position
    itemsStrip.style.transition = 'none';
    itemsStrip.style.transform = 'translateX(0)';
 
    // Force reflow
    itemsStrip.offsetHeight;
 
    // Calculate final position to center selected item with random offset
    const itemWidth = 220; // 200px width + 20px margin
    const itemHalfWidth = 110; // Half width to center the item
    // Add random offset within the box (-100 to +100 pixels from center)
    const randomOffset = Math.floor(Math.random() * 200) - 100;
    // Items strip is positioned at left: 50%, so we only need to account for item position
    const offsetWithRandom = -(selectedIndex * itemWidth) - itemHalfWidth + randomOffset;
    // Calculate perfectly centered position (center of item aligned with selector line at screen center)
    const centeredOffset = -(selectedIndex * itemWidth) - itemHalfWidth;
 
    // Animate
    return new Promise(resolve => {
        setTimeout(() => {
            // First animation: spin to randomized position
            itemsStrip.style.transition = 'transform 4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
            itemsStrip.style.transform = `translateX(${offsetWithRandom}px)`;
         
            setTimeout(() => {
                // Highlight selected item
                const selectedItem = itemsStrip.querySelector('.will-select');
                if (selectedItem) {
                    selectedItem.classList.add('selected');
                }
             
                // Re-center animation after a brief pause
                setTimeout(() => {
                    itemsStrip.style.transition = 'transform 0.5s ease-out';
                    itemsStrip.style.transform = `translateX(${centeredOffset}px)`;
                 
                    setTimeout(() => {
                        // Hide animation after re-centering
                        caseAnimation.classList.add('hidden');
                        resolve();
                    }, 800);
                }, 500);
            }, 4000);
        }, 100);
    });
}

// Display player details
function displayPlayerDetails(player) {
    const detailsSection = document.getElementById('player-details');
 
    // Update basic info
    document.getElementById('player-name').textContent = player.name;
    document.getElementById('player-position').textContent = player.position;
    document.getElementById('player-school').textContent = player.school || 'Unknown';
 
    // Update jersey number
    const jerseyBadge = document.getElementById('player-jersey');
    if (player.jersey_number) {
        jerseyBadge.textContent = `#${player.jersey_number}`;
        jerseyBadge.style.display = 'inline-block';
    } else {
        jerseyBadge.style.display = 'none';
    }
 
    boardRanksRevealed = false;
 
    // Update measurements
    document.getElementById('player-height').textContent = player.height || 'N/A';
    document.getElementById('player-weight').textContent = player.weight ? `${player.weight} lbs` : 'N/A';
 
    // Update stats
    const statsGrid = document.getElementById('player-stats');
    statsGrid.innerHTML = '';
 
    if (player.stats && typeof player.stats === 'object') {
        Object.entries(player.stats).forEach(([key, value]) => {
            const statBox = document.createElement('div');
            statBox.className = 'stat-box';
         
            const label = document.createElement('div');
            label.className = 'stat-box-label';
            label.textContent = key.replace(/_/g, ' ');
         
            const valueEl = document.createElement('div');
            valueEl.className = 'stat-box-value';
            valueEl.textContent = value;
         
            statBox.appendChild(label);
            statBox.appendChild(valueEl);
            statsGrid.appendChild(statBox);
        });
    }
 
    if (statsGrid.children.length === 0) {
        statsGrid.innerHTML = '<p style="color: var(--text-secondary);">No statistics available</p>';
    }

    renderPlayerBoardRanks(player);
    applyBoardRanksVisibility();
 
    // Update external links
    if (player.sports_reference_url) {
        document.getElementById('sports-ref-link').href = player.sports_reference_url;
    }
    if (player.espn_url) {
        document.getElementById('espn-link').href = player.espn_url;
    }
    if (player.player_url) {
        document.getElementById('tankathon-link').href = player.player_url;
    }
 
    // Update notes
    document.getElementById('notes-input').value = player.notes || '';
    document.getElementById('games-watched-input').value = player.games_watched || '';
 
    // Update grade
    populateGradeDropdowns(player.grade || '');
 
    // Update scout button
    const scoutBtn = document.getElementById('mark-scouted-btn');
    if (player.scouted) {
        scoutBtn.innerHTML = '<span>↺</span> Unmark as Scouted';
        scoutBtn.classList.add('scouted');
    } else {
        scoutBtn.innerHTML = '<span>✓</span> Mark as Scouted';
        scoutBtn.classList.remove('scouted');
    }
 
    // Place details where they should appear for the source tab
    positionPlayerDetailsForCurrentSource();

    // Show details only on the tab that sourced this player
    updatePlayerDetailsVisibility();
    const activeTab = document.querySelector('.tab-panel.active')?.id;
    if (activeTab === 'search-tab') {
        detailsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function renderPlayerBoardRanks(player) {
    const container = document.getElementById('player-board-ranks');
    if (!container) {
        return;
    }

    container.innerHTML = '';

    const overallRow = document.createElement('div');
    overallRow.className = 'board-ranks-row board-ranks-overall-row';

    const positionalRow = document.createElement('div');
    positionalRow.className = 'board-ranks-row board-ranks-positional-row';

    const appendRankPill = (targetRow, label, value, extraClass = '') => {
        if (value === null || value === undefined || value === '') {
            return;
        }
        const pill = document.createElement('div');
        pill.className = `board-rank-pill ${extraClass}`.trim();
        pill.textContent = `${label}: #${value}`;
        targetRow.appendChild(pill);
    };

    const boardRanks = Array.isArray(player.board_ranks) ? player.board_ranks : [];
    const seenBoardLabels = new Set();
    const showConsensusBoard = isRankBoardVisible('consensus_2026');

    const consensusBoardRank = boardRanks.find(board => board.board_key === 'consensus_2026');
    if (consensusBoardRank && showConsensusBoard) {
        const consensusRankNumber = Number.isFinite(Number(consensusBoardRank.rank))
            ? Number(consensusBoardRank.rank).toFixed(1).replace('.0', '')
            : consensusBoardRank.rank;
        appendRankPill(overallRow, 'Consensus Big Board 2026', consensusRankNumber, 'primary');
        const consensusLabel = (consensusBoardRank.board_name || '').trim().toLowerCase();
        if (consensusLabel) {
            seenBoardLabels.add(consensusLabel);
        }
    } else if (showConsensusBoard) {
        const overallRank = getPreferredOverallRank(player);
        if (overallRank) {
            appendRankPill(overallRow, 'Consensus Big Board 2026', overallRank, 'primary');
        }
    }

    const personalBigBoardRank = Number(player.personal_big_board_rank);
    if (Number.isFinite(personalBigBoardRank) && personalBigBoardRank > 0) {
        appendRankPill(overallRow, 'Personal Big Board', Math.round(personalBigBoardRank));
    }

    if (player.positional_rank && String(player.positional_rank).trim()) {
        appendRankPill(positionalRow, 'Consensus Pos Rank', String(player.positional_rank).trim());
    }

    const personalPosRank = Number(player.personal_pos_rank);
    if (Number.isFinite(personalPosRank) && personalPosRank > 0) {
        appendRankPill(positionalRow, 'Personal Pos Rank', Math.round(personalPosRank));
    }

    const boardRankCount = boardRanks.length;
    if (player.weighted_average_rank && boardRankCount > 1) {
        const useCustomWeights = document.getElementById('use-board-weights-checkbox')?.checked;
        const averageRankLabel = useCustomWeights ? 'Weighted Avg' : 'Average Rank';
        appendRankPill(overallRow, averageRankLabel, Number(player.weighted_average_rank).toFixed(1));
    }

    boardRanks.forEach(board => {
        if (!isRankBoardVisible(board.board_key)) {
            return;
        }
        const boardLabel = (board.board_name || '').trim();
        if (!boardLabel || seenBoardLabels.has(boardLabel.toLowerCase())) {
            return;
        }

        seenBoardLabels.add(boardLabel.toLowerCase());
        const rankNumber = Number.isFinite(Number(board.rank)) ? Number(board.rank).toFixed(1).replace('.0', '') : board.rank;
        appendRankPill(overallRow, boardLabel, rankNumber, board.is_primary ? 'primary' : '');
    });

    if (overallRow.children.length) {
        container.appendChild(overallRow);
    }
    if (positionalRow.children.length) {
        container.appendChild(positionalRow);
    }

    if (!container.children.length) {
        const empty = document.createElement('p');
        empty.className = 'search-empty';
        empty.textContent = 'No board-specific ranks available yet.';
        container.appendChild(empty);
    }
}

// Toggle scout status
async function toggleScoutStatus() {
    if (!playerReportController) {
        return;
    }
    await playerReportController.toggleScoutStatus();
}

async function savePlayerProfile() {
    if (!playerReportController) {
        return;
    }
    await playerReportController.savePlayerProfile();
}

async function loadCurrentPlayerBySource(playerId) {
    if (!playerReportController) {
        return;
    }
    await playerReportController.loadCurrentPlayerBySource(playerId);
}

function openEditProfileDialog() {
    if (!playerReportController) {
        return;
    }
    playerReportController.openEditProfileDialog();
}

function closeEditProfileDialog() {
    if (!playerReportController) {
        return;
    }
    playerReportController.closeEditProfileDialog();
}

function renderProfileStatsBuilder(statsObject) {
    if (!playerReportController) {
        return;
    }
    playerReportController.renderProfileStatsBuilder(statsObject);
}

function addProfileStatRow(statKey = '', statValue = '') {
    if (!playerReportController) {
        return;
    }
    playerReportController.addProfileStatRow(statKey, statValue);
}

function collectProfileStatsObject() {
    if (!playerReportController) {
        return {};
    }
    return playerReportController.collectProfileStatsObject();
}

// Save notes
async function saveNotes() {
    if (!playerReportController) {
        return;
    }
    await playerReportController.saveNotes();
}

async function saveGamesWatched() {
    if (!playerReportController) {
        return;
    }
    await playerReportController.saveGamesWatched();
}

// Update grade
async function updateGrade(grade, slot = 'primary') {
    if (!playerReportController) {
        return;
    }
    await playerReportController.updateGrade(grade, slot);
}
