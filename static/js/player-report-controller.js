(function () {
    function createPlayerReportController(options) {
        const {
            getCurrentPlayer,
            setCurrentPlayer,
            requestGetJson,
            requestPostJson,
            requestPostNoBody,
            showToast,
            loadStats,
            loadPositions,
            loadSchools,
            displayPlayerDetails
        } = options;

        async function toggleScoutStatus() {
            const currentPlayer = getCurrentPlayer();
            if (!currentPlayer) {
                return;
            }

            try {
                const endpoint = currentPlayer.scouted ? 'unscout' : 'scout';
                const { response } = await requestPostNoBody(`/api/player/${currentPlayer.id}/${endpoint}`);

                if (response.ok) {
                    const updatedPlayer = { ...currentPlayer, scouted: !currentPlayer.scouted };
                    setCurrentPlayer(updatedPlayer);

                    const scoutBtn = document.getElementById('mark-scouted-btn');
                    if (updatedPlayer.scouted) {
                        scoutBtn.innerHTML = '<span>↺</span> Unmark as Scouted';
                        scoutBtn.classList.add('scouted');
                    } else {
                        scoutBtn.innerHTML = '<span>✓</span> Mark as Scouted';
                        scoutBtn.classList.remove('scouted');
                    }

                    loadStats();
                }
            } catch (error) {
                console.error('Error updating scout status:', error);
                showToast('Update Failed', 'Error updating scout status. Please try again.', 'error', 6000);
            }
        }

        function collectProfileStatsObject() {
            const stats = {};
            document.querySelectorAll('#edit-stats-builder .profile-stat-row').forEach(row => {
                const key = row.querySelector('.profile-stat-key')?.value.trim() || '';
                const value = row.querySelector('.profile-stat-value')?.value.trim() || '';
                if (key) {
                    stats[key] = value;
                }
            });
            return stats;
        }

        function addProfileStatRow(statKey = '', statValue = '') {
            const container = document.getElementById('edit-stats-builder');
            if (!container) {
                return;
            }

            const row = document.createElement('div');
            row.className = 'profile-stat-row';

            const keyInput = document.createElement('input');
            keyInput.type = 'text';
            keyInput.className = 'search-input profile-stat-key';
            keyInput.placeholder = 'Stat name (e.g. forty_time)';
            keyInput.value = statKey || '';

            const valueInput = document.createElement('input');
            valueInput.type = 'text';
            valueInput.className = 'search-input profile-stat-value';
            valueInput.placeholder = 'Stat value (e.g. 4.39)';
            valueInput.value = statValue == null ? '' : String(statValue);

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'mini-btn remove profile-stat-remove';
            removeBtn.textContent = 'Remove';
            removeBtn.addEventListener('click', () => {
                row.remove();
                if (!container.children.length) {
                    addProfileStatRow('', '');
                }
            });

            row.appendChild(keyInput);
            row.appendChild(valueInput);
            row.appendChild(removeBtn);
            container.appendChild(row);
        }

        function renderProfileStatsBuilder(statsObject) {
            const container = document.getElementById('edit-stats-builder');
            if (!container) {
                return;
            }

            container.innerHTML = '';
            const entries = Object.entries(statsObject || {});

            if (!entries.length) {
                addProfileStatRow('', '');
                return;
            }

            entries.forEach(([statKey, statValue]) => {
                addProfileStatRow(statKey, statValue);
            });
        }

        function openEditProfileDialog() {
            const currentPlayer = getCurrentPlayer();
            if (!currentPlayer) {
                showToast('No Player Selected', 'Load a player report first, then edit profile details.', 'error', 5000);
                return;
            }

            document.getElementById('edit-position-input').value = currentPlayer.position || '';
            document.getElementById('edit-school-input').value = currentPlayer.school || '';
            document.getElementById('edit-height-input').value = currentPlayer.height || '';
            document.getElementById('edit-weight-input').value = currentPlayer.weight || '';
            document.getElementById('edit-jersey-input').value = currentPlayer.jersey_number || '';
            document.getElementById('edit-url-input').value = currentPlayer.player_url || '';

            renderProfileStatsBuilder(currentPlayer.stats && typeof currentPlayer.stats === 'object' ? currentPlayer.stats : {});
            document.getElementById('edit-profile-dialog').classList.remove('hidden');
        }

        function closeEditProfileDialog() {
            document.getElementById('edit-profile-dialog').classList.add('hidden');
        }

        async function loadCurrentPlayerBySource(playerId) {
            const { response, data } = await requestGetJson(`/api/player/${playerId}`);
            const player = data || {};

            if (!response.ok || player.error) {
                return;
            }

            setCurrentPlayer(player);
            displayPlayerDetails(player);
        }

        async function savePlayerProfile() {
            const currentPlayer = getCurrentPlayer();
            if (!currentPlayer) {
                return;
            }

            const statsObject = collectProfileStatsObject();

            const payload = {
                position: document.getElementById('edit-position-input').value.trim(),
                school: document.getElementById('edit-school-input').value.trim(),
                height: document.getElementById('edit-height-input').value.trim(),
                weight: document.getElementById('edit-weight-input').value.trim(),
                jersey_number: document.getElementById('edit-jersey-input').value.trim(),
                player_url: document.getElementById('edit-url-input').value.trim(),
                stats_json: JSON.stringify(statsObject)
            };

            const btn = document.getElementById('save-profile-btn');
            const originalText = btn.textContent;
            btn.disabled = true;

            try {
                const { response, data } = await requestPostJson(`/api/player/${currentPlayer.id}/profile`, payload);
                const result = data || {};
                if (!response.ok || !result.success) {
                    const errorText = result.error || 'Could not save profile info.';
                    showToast('Save Failed', errorText, 'error', 7000);
                    return;
                }

                await loadCurrentPlayerBySource(currentPlayer.id);
                closeEditProfileDialog();
                showToast('Profile Saved', 'Player profile fields were updated.', 'success', 5000);
                loadPositions();
                loadSchools();
            } catch (error) {
                console.error('Error saving profile info:', error);
                showToast('Save Failed', 'Error saving profile info.', 'error', 7000);
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        }

        async function saveNotes() {
            const currentPlayer = getCurrentPlayer();
            if (!currentPlayer) {
                return;
            }

            const notes = document.getElementById('notes-input').value;

            try {
                const { response } = await requestPostJson(`/api/player/${currentPlayer.id}/notes`, { notes });

                if (response.ok) {
                    const btn = document.getElementById('save-notes-btn');
                    const originalText = btn.textContent;
                    btn.textContent = '✓ Saved!';
                    btn.style.background = 'var(--success-color)';

                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.style.background = '';
                    }, 2000);
                }
            } catch (error) {
                console.error('Error saving notes:', error);
                showToast('Save Failed', 'Error saving notes. Please try again.', 'error', 6000);
            }
        }

        async function saveGamesWatched() {
            const currentPlayer = getCurrentPlayer();
            if (!currentPlayer) {
                return;
            }

            const games_watched = document.getElementById('games-watched-input').value;

            try {
                const { response } = await requestPostJson(`/api/player/${currentPlayer.id}/games-watched`, { games_watched });

                if (response.ok) {
                    const updatedPlayer = { ...currentPlayer, games_watched };
                    setCurrentPlayer(updatedPlayer);
                    const btn = document.getElementById('save-games-watched-btn');
                    const originalText = btn.textContent;
                    btn.textContent = '✓ Saved!';
                    btn.style.background = 'var(--success-color)';

                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.style.background = '';
                    }, 2000);
                }
            } catch (error) {
                console.error('Error saving games watched:', error);
                showToast('Save Failed', 'Error saving games watched. Please try again.', 'error', 6000);
            }
        }

        async function updateGrade(grade, slot = 'primary') {
            const currentPlayer = getCurrentPlayer();
            if (!currentPlayer) {
                return;
            }

            try {
                const { response } = await requestPostJson(`/api/player/${currentPlayer.id}/grade`, { grade, slot });

                if (response.ok) {
                    const updatedPlayer = { ...currentPlayer };
                    if (slot === 'secondary') {
                        updatedPlayer.grade_secondary = grade;
                    } else {
                        updatedPlayer.grade = grade;
                    }
                    setCurrentPlayer(updatedPlayer);
                }
            } catch (error) {
                console.error('Error updating grade:', error);
                showToast('Update Failed', 'Error updating grade. Please try again.', 'error', 6000);
            }
        }

        return {
            toggleScoutStatus,
            savePlayerProfile,
            loadCurrentPlayerBySource,
            openEditProfileDialog,
            closeEditProfileDialog,
            renderProfileStatsBuilder,
            addProfileStatRow,
            collectProfileStatsObject,
            saveNotes,
            saveGamesWatched,
            updateGrade
        };
    }

    window.createPlayerReportController = createPlayerReportController;
})();
