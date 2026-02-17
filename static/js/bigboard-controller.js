(function () {
    function createBigBoardController(options) {
        const {
            getBigBoardType,
            setBigBoardTypeState,
            getCurrentBigBoardPosition,
            setCurrentBigBoardPosition,
            getAppSettings,
            requestGetJson,
            requestPostJson,
            showToast,
            openBigBoardPlayerModal
        } = options;

        let draggedBoardPlayerId = null;
        let draggedAddPlayerId = null;
        let draggedSource = null;
        let boardDropPlaceholder = null;
        let lastDropIndex = null;
        let pendingAddToBoardPlayer = null;
        let currentBigBoardPlayerIds = new Set();

        function getBigBoardParams() {
            if (getBigBoardType() === 'position') {
                return {
                    type: 'position',
                    position: getCurrentBigBoardPosition()
                };
            }
            return { type: 'overall' };
        }

        function hasAnyGrade(player) {
            if (!player) {
                return false;
            }
            return Boolean((player.grade || '').trim() || (player.grade_secondary || '').trim());
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

        function setBigBoardType(type) {
            setBigBoardTypeState(type);

            const overallBtn = document.getElementById('overall-board-btn');
            const positionBtn = document.getElementById('position-board-btn');
            const positionSelector = document.getElementById('position-board-selector');

            overallBtn.classList.toggle('active', type === 'overall');
            positionBtn.classList.toggle('active', type === 'position');
            positionSelector.classList.toggle('hidden', type !== 'position');

            const positionSelect = document.getElementById('bigboard-position-select');
            if (type === 'position') {
                setCurrentBigBoardPosition(positionSelect.value || getCurrentBigBoardPosition());
            } else {
                setCurrentBigBoardPosition(null);
            }

            loadBigBoard();
            searchBigBoardPlayers();
        }

        async function loadBigBoard() {
            try {
                const params = new URLSearchParams();
                params.append('type', getBigBoardType());
                if (getBigBoardType() === 'position' && getCurrentBigBoardPosition()) {
                    params.append('position', getCurrentBigBoardPosition());
                }

                const { data } = await requestGetJson(`/api/bigboard?${params.toString()}`);
                renderBigBoard(data);
            } catch (error) {
                console.error('Error loading big board:', error);
                document.getElementById('bigboard-list').innerHTML = '<p class="search-empty">Error loading big board.</p>';
            }
        }

        function renderBigBoard(entries) {
            const title = document.getElementById('bigboard-title');
            const list = document.getElementById('bigboard-list');
            title.textContent = getBigBoardType() === 'position' && getCurrentBigBoardPosition()
                ? `${getCurrentBigBoardPosition()} Big Board`
                : 'Overall Big Board';

            list.innerHTML = '';
            currentBigBoardPlayerIds = new Set(
                (Array.isArray(entries) ? entries : []).map(entry => Number(entry.id))
            );

            list.ondragover = handleBoardListDragOver;
            list.ondrop = handleBoardListDrop;

            if (!Array.isArray(entries) || entries.length === 0) {
                list.innerHTML = '<p class="search-empty">No players on this board yet. Add players from the left panel.</p>';
                return;
            }

            entries.forEach((entry, index) => {
                const item = document.createElement('div');
                item.className = 'bigboard-item';
                item.draggable = true;
                item.dataset.playerId = entry.id;

                item.addEventListener('dragstart', handleBoardDragStart);
                item.addEventListener('dragover', handleBoardDragOver);
                item.addEventListener('dragend', handleBoardDragEnd);
                item.addEventListener('click', function (event) {
                    if (event.target.closest('button')) {
                        return;
                    }
                    openBigBoardPlayerReport(entry.id);
                });

                const main = document.createElement('div');
                main.className = 'bigboard-item-main';

                const rank = document.createElement('div');
                rank.className = 'bigboard-rank';
                rank.textContent = `#${index + 1}`;

                const name = document.createElement('div');
                name.className = 'bigboard-name';
                name.textContent = entry.name;

                const meta = document.createElement('div');
                meta.className = 'bigboard-meta';
                const metaParts = [entry.position || 'N/A', entry.school || 'Unknown'];
                if (getAppSettings().showConsensusGradeOnBigBoard) {
                    const consensusRank = Number(entry.consensus_rank);
                    if (Number.isFinite(consensusRank) && consensusRank > 0) {
                        metaParts.push(`Consensus Grade #${Math.round(consensusRank)}`);
                    } else {
                        metaParts.push('Consensus Grade N/A');
                    }
                }
                if (entry.grade) {
                    metaParts.push(entry.grade);
                }
                meta.textContent = metaParts.join(' • ');

                main.appendChild(rank);
                main.appendChild(name);
                main.appendChild(meta);

                const actions = document.createElement('div');
                const removeBtn = document.createElement('button');
                removeBtn.className = 'mini-btn remove';
                removeBtn.textContent = 'Remove';
                removeBtn.addEventListener('click', (event) => {
                    event.stopPropagation();
                    removePlayerFromBigBoard(entry.id);
                });
                actions.appendChild(removeBtn);

                item.appendChild(main);
                item.appendChild(actions);
                list.appendChild(item);
            });
        }

        async function openBigBoardPlayerReport(playerId) {
            try {
                const { response, data } = await requestGetJson(`/api/player/${playerId}`);
                const player = data || {};

                if (!response.ok || player.error) {
                    showToast('Load Failed', player.error || 'Unable to load scout report.', 'error', 6000);
                    return;
                }

                openBigBoardPlayerModal(player);
            } catch (error) {
                console.error('Error loading big board player report:', error);
                showToast('Load Failed', 'Error loading scout report. Please try again.', 'error', 6000);
            }
        }

        function handleBoardDragStart(event) {
            draggedSource = 'board';
            draggedBoardPlayerId = event.currentTarget.dataset.playerId;
            event.currentTarget.classList.add('dragging');
            event.dataTransfer.effectAllowed = 'move';
        }

        function handleBoardDragOver(event) {
            event.preventDefault();
            if (draggedSource !== 'board' && draggedSource !== 'add') {
                return;
            }
            positionDropPlaceholderByPointer(event.clientY);
        }

        function ensureBoardDropPlaceholder() {
            if (!boardDropPlaceholder) {
                boardDropPlaceholder = document.createElement('div');
                boardDropPlaceholder.className = 'bigboard-drop-placeholder';
                const label = document.createElement('span');
                label.className = 'bigboard-drop-label';
                boardDropPlaceholder.appendChild(label);
            }
            return boardDropPlaceholder;
        }

        function updateDropPlaceholderRankLabel() {
            if (!boardDropPlaceholder || !boardDropPlaceholder.parentElement) {
                return;
            }

            const list = boardDropPlaceholder.parentElement;
            const siblings = Array.from(list.children);
            const placeholderIndex = siblings.indexOf(boardDropPlaceholder);
            if (placeholderIndex < 0) {
                return;
            }

            const rank = siblings
                .slice(0, placeholderIndex)
                .filter(el => el.classList.contains('bigboard-item') && !el.classList.contains('dragging'))
                .length + 1;

            const label = boardDropPlaceholder.querySelector('.bigboard-drop-label');
            if (label) {
                label.textContent = `Drop at #${rank}`;
            }
        }

        function placeDropPlaceholderAtIndex(index) {
            const list = document.getElementById('bigboard-list');
            const placeholder = ensureBoardDropPlaceholder();
            const items = Array.from(list.querySelectorAll('.bigboard-item:not(.dragging)'));
            const clampedIndex = Math.max(0, Math.min(index, items.length));

            if (clampedIndex >= items.length) {
                list.appendChild(placeholder);
            } else {
                list.insertBefore(placeholder, items[clampedIndex]);
            }

            list.classList.add('drag-active');
            lastDropIndex = clampedIndex;
            updateDropPlaceholderRankLabel();
        }

        function positionDropPlaceholderByPointer(clientY) {
            const list = document.getElementById('bigboard-list');
            const items = Array.from(list.querySelectorAll('.bigboard-item:not(.dragging)'));

            if (!items.length) {
                placeDropPlaceholderAtIndex(0);
                return;
            }

            const slotPadding = 18;
            const deadZone = 12;
            let targetIndex = items.length;

            for (let index = 0; index < items.length; index += 1) {
                const rect = items[index].getBoundingClientRect();
                const slotTop = rect.top - slotPadding;
                const slotBottom = rect.bottom + slotPadding;
                const midPoint = rect.top + rect.height / 2;

                if (clientY < slotTop) {
                    targetIndex = index;
                    break;
                }

                if (clientY >= slotTop && clientY <= slotBottom) {
                    if (clientY < midPoint - deadZone) {
                        targetIndex = index;
                    } else if (clientY > midPoint + deadZone) {
                        targetIndex = index + 1;
                    } else {
                        targetIndex = lastDropIndex !== null ? lastDropIndex : index + 1;
                    }
                    break;
                }
            }

            placeDropPlaceholderAtIndex(targetIndex);
        }

        function handleBoardListDragOver(event) {
            event.preventDefault();
            if (draggedSource !== 'board' && draggedSource !== 'add') {
                return;
            }

            positionDropPlaceholderByPointer(event.clientY);
        }

        async function handleBoardListDrop(event) {
            event.preventDefault();
            const list = document.getElementById('bigboard-list');

            if (draggedSource === 'add' && draggedAddPlayerId) {
                await addPlayerToBigBoard(Number(draggedAddPlayerId));
                clearBoardDragArtifacts();
                return;
            }

            if (draggedSource !== 'board' || !draggedBoardPlayerId) {
                clearBoardDragArtifacts();
                return;
            }

            const draggedEl = list.querySelector(`[data-player-id="${draggedBoardPlayerId}"]`);

            if (!draggedEl) {
                clearBoardDragArtifacts();
                return;
            }

            if (boardDropPlaceholder && boardDropPlaceholder.parentElement === list) {
                list.insertBefore(draggedEl, boardDropPlaceholder);
            } else {
                list.appendChild(draggedEl);
            }

            await persistBigBoardOrder();
            refreshBigBoardVisibleRanks();
            clearBoardDragArtifacts();
        }

        function clearBoardDragArtifacts() {
            const list = document.getElementById('bigboard-list');
            if (list) {
                list.classList.remove('drag-active');
            }
            if (boardDropPlaceholder && boardDropPlaceholder.parentElement) {
                boardDropPlaceholder.remove();
            }
            draggedBoardPlayerId = null;
            draggedAddPlayerId = null;
            draggedSource = null;
            lastDropIndex = null;
        }

        function handleBoardDragEnd(event) {
            event.currentTarget.classList.remove('dragging');
            clearBoardDragArtifacts();
        }

        function refreshBigBoardVisibleRanks() {
            const items = document.querySelectorAll('#bigboard-list .bigboard-item');
            items.forEach((item, index) => {
                const rankEl = item.querySelector('.bigboard-rank');
                if (rankEl) {
                    rankEl.textContent = `#${index + 1}`;
                }
            });
        }

        async function persistBigBoardOrder() {
            const playerIds = Array.from(document.querySelectorAll('#bigboard-list .bigboard-item'))
                .map(item => parseInt(item.dataset.playerId, 10));

            const payload = {
                ...getBigBoardParams(),
                player_ids: playerIds
            };

            try {
                await requestPostJson('/api/bigboard/reorder', payload);
            } catch (error) {
                console.error('Error persisting big board order:', error);
            }
        }

        async function searchBigBoardPlayers() {
            const searchTerm = document.getElementById('bigboard-player-search').value.trim();
            const resultsContainer = document.getElementById('bigboard-player-results');

            try {
                const params = new URLSearchParams();
                params.append('include_scouted', 'true');
                if (searchTerm) {
                    params.append('name', searchTerm);
                }
                if (getBigBoardType() === 'position' && getCurrentBigBoardPosition()) {
                    params.append('positions[]', getCurrentBigBoardPosition());
                }

                const { data } = await requestGetJson(`/api/players?${params.toString()}`);
                const players = data;

                resultsContainer.innerHTML = '';
                const availablePlayers = Array.isArray(players)
                    ? players.filter(player => !currentBigBoardPlayerIds.has(Number(player.id)))
                    : [];

                availablePlayers.sort(comparePlayersForBigBoardAdd);

                if (availablePlayers.length === 0) {
                    resultsContainer.innerHTML = '<p class="search-empty">No matching players found.</p>';
                    return;
                }

                availablePlayers.slice(0, 100).forEach(player => {
                    const card = document.createElement('div');
                    card.className = 'search-result-card bigboard-add-card';
                    card.draggable = true;
                    card.dataset.playerId = String(player.id);
                    card.addEventListener('dragstart', handleAddCardDragStart);
                    card.addEventListener('dragend', handleAddCardDragEnd);

                    const name = document.createElement('div');
                    name.className = 'search-result-name';
                    name.textContent = player.name;

                    const meta = document.createElement('div');
                    meta.className = 'search-result-meta';
                    const metaParts = [player.position || 'N/A', player.school || 'Unknown'];
                    if (player.grade) {
                        metaParts.push(player.grade);
                    }
                    meta.textContent = metaParts.join(' • ');

                    const scoutStatus = document.createElement('div');
                    scoutStatus.className = `bigboard-scout-status ${player.scouted ? 'scouted' : 'not-scouted'}`;
                    scoutStatus.textContent = player.scouted ? 'Scouted' : 'Not Scouted';

                    const addBtn = document.createElement('button');
                    addBtn.className = 'mini-btn bigboard-add-btn';
                    addBtn.textContent = 'Add to Board';
                    addBtn.addEventListener('click', async (event) => {
                        event.stopPropagation();
                        openAddToBoardDialog(player);
                    });

                    const actionsWrap = document.createElement('div');
                    actionsWrap.className = 'bigboard-add-actions';
                    actionsWrap.appendChild(scoutStatus);
                    actionsWrap.appendChild(addBtn);

                    card.appendChild(name);
                    card.appendChild(meta);
                    card.appendChild(actionsWrap);
                    resultsContainer.appendChild(card);
                });
            } catch (error) {
                console.error('Error loading players for big board:', error);
                resultsContainer.innerHTML = '<p class="search-empty">Error loading players.</p>';
            }
        }

        function handleAddCardDragStart(event) {
            draggedSource = 'add';
            draggedAddPlayerId = event.currentTarget.dataset.playerId;
            event.currentTarget.classList.add('dragging');
            event.dataTransfer.effectAllowed = 'copyMove';
        }

        function handleAddCardDragEnd(event) {
            event.currentTarget.classList.remove('dragging');
            clearBoardDragArtifacts();
        }

        function openAddToBoardDialog(player) {
            pendingAddToBoardPlayer = player;
            const modal = document.getElementById('add-to-board-dialog');
            const title = document.getElementById('add-to-board-title');
            const input = document.getElementById('add-to-board-rank-input');
            const boardCount = document.querySelectorAll('#bigboard-list .bigboard-item').length;
            const maxRank = boardCount + 1;

            title.textContent = `Add ${player.name} to Big Board`;
            input.value = String(maxRank);
            input.min = '1';
            input.max = String(maxRank);
            input.placeholder = `1-${maxRank}`;
            modal.classList.remove('hidden');
            input.focus();
        }

        function closeAddToBoardDialog() {
            pendingAddToBoardPlayer = null;
            const modal = document.getElementById('add-to-board-dialog');
            modal.classList.add('hidden');
        }

        async function confirmAddToRank() {
            if (!pendingAddToBoardPlayer) {
                return;
            }

            const input = document.getElementById('add-to-board-rank-input');
            const boardCount = document.querySelectorAll('#bigboard-list .bigboard-item').length;
            const maxRank = boardCount + 1;
            const parsedRank = parseInt(input.value, 10);
            if (!Number.isInteger(parsedRank) || parsedRank < 1) {
                showToast('Invalid Position', 'Enter a valid board position (1 or greater).', 'error', 5000);
                return;
            }

            const targetRank = Math.min(parsedRank, maxRank);

            const playerId = pendingAddToBoardPlayer.id;
            closeAddToBoardDialog();
            await addPlayerToBigBoard(playerId, { placement: 'rank', targetRank });
        }

        async function confirmAddToBottom() {
            if (!pendingAddToBoardPlayer) {
                return;
            }

            const playerId = pendingAddToBoardPlayer.id;
            closeAddToBoardDialog();
            await addPlayerToBigBoard(playerId, { placement: 'bottom' });
        }

        async function addPlayerToBigBoard(playerId, options = {}) {
            try {
                const { response, data } = await requestPostJson('/api/bigboard/add', {
                    ...getBigBoardParams(),
                    player_id: playerId
                });
                const result = data || {};

                if (!response.ok || !result.success) {
                    showToast('Add Failed', result.error || 'Could not add player to board.', 'error', 6000);
                    return;
                }

                await loadBigBoard();
                if (options.placement === 'rank' && Number.isInteger(options.targetRank)) {
                    await movePlayerWithinBoard(Number(playerId), options.targetRank);
                } else if (options.placement === 'bottom') {
                    await movePlayerWithinBoard(Number(playerId), Number.MAX_SAFE_INTEGER);
                }
                await searchBigBoardPlayers();
            } catch (error) {
                console.error('Error adding player to big board:', error);
                showToast('Add Failed', 'Error adding player to big board.', 'error', 6000);
            }
        }

        async function movePlayerWithinBoard(playerId, targetRank) {
            const list = document.getElementById('bigboard-list');
            const ids = Array.from(list.querySelectorAll('.bigboard-item'))
                .map(item => Number(item.dataset.playerId));

            if (!ids.includes(playerId)) {
                return;
            }

            const withoutPlayer = ids.filter(id => id !== playerId);
            const insertIndex = Math.max(0, Math.min(targetRank - 1, withoutPlayer.length));
            withoutPlayer.splice(insertIndex, 0, playerId);

            await requestPostJson('/api/bigboard/reorder', {
                ...getBigBoardParams(),
                player_ids: withoutPlayer
            });

            await loadBigBoard();
        }

        async function autoSortBigBoard() {
            const confirmed = window.UIFeedback?.confirmAction
                ? await window.UIFeedback.confirmAction({
                    title: 'Auto-sort Big Board',
                    message: 'Auto-sort will reorder this board by current grades. Continue?',
                    confirmText: 'Auto-sort',
                    cancelText: 'Cancel'
                })
                : true;
            if (!confirmed) {
                return;
            }

            try {
                const { response, data } = await requestPostJson('/api/bigboard/autosort', getBigBoardParams());
                const result = data || {};

                if (!response.ok || !result.success) {
                    showToast('Auto-sort Failed', result.error || 'Could not auto-sort big board.', 'error', 6000);
                    return;
                }

                await loadBigBoard();
                await searchBigBoardPlayers();
            } catch (error) {
                console.error('Error auto-sorting big board:', error);
                showToast('Auto-sort Failed', 'Error auto-sorting big board.', 'error', 6000);
            }
        }

        async function removePlayerFromBigBoard(playerId) {
            try {
                await requestPostJson('/api/bigboard/remove', {
                    ...getBigBoardParams(),
                    player_id: playerId
                });
                await loadBigBoard();
                await searchBigBoardPlayers();
            } catch (error) {
                console.error('Error removing player from big board:', error);
            }
        }

        return {
            setBigBoardType,
            getBigBoardParams,
            loadBigBoard,
            searchBigBoardPlayers,
            confirmAddToRank,
            confirmAddToBottom,
            closeAddToBoardDialog,
            autoSortBigBoard,
            removePlayerFromBigBoard,
            openBigBoardPlayerReport
        };
    }

    window.createBigBoardController = createBigBoardController;
})();
