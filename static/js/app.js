// Global state
let currentPlayer = null;
let selectedPositions = [];
let selectedRank = null;
let allPlayers = [];
let ranksRevealed = false;
let posRanksRevealed = false;

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

// Helper function to check if logo exists
function checkLogoExists(url, callback) {
  const img = new Image();
  img.onload = () => callback(true);
  img.onerror = () => callback(false);
  img.src = url;
}

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
  loadStats();
  loadPositions();
  setupEventListeners();
});

// Load statistics
async function loadStats() {
  try {
    const response = await fetch('/api/stats');
    const stats = await response.json();
   
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
    const response = await fetch('/api/positions');
    const positions = await response.json();
   
    const container = document.getElementById('position-filters');
    container.innerHTML = '';
   
    positions.forEach(position => {
      const btn = document.createElement('button');
      btn.className = 'position-btn';
      btn.textContent = position;
      btn.dataset.position = position;
      btn.addEventListener('click', togglePosition);
      container.appendChild(btn);
    });
  } catch (error) {
    console.error('Error loading positions:', error);
  }
}

// Setup event listeners
function setupEventListeners() {
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
 
  // Grade dropdown
  document.getElementById('grade-dropdown').addEventListener('change', function() {
    const grade = this.value;
    if (grade) {
      updateGrade(grade);
    }
  });
 
  // Clickable rank badges
  document.getElementById('player-rank').addEventListener('click', function() {
    ranksRevealed = !ranksRevealed;
    toggleRankVisibility();
  });
 
  document.getElementById('player-pos-rank').addEventListener('click', function() {
    posRanksRevealed = !posRanksRevealed;
    togglePosRankVisibility();
  });
}

// Toggle rank visibility
function toggleRankVisibility() {
  const rankBadge = document.getElementById('player-rank');
  const rankValue = rankBadge.querySelector('.rank-value');
 
  if (ranksRevealed && currentPlayer) {
    rankValue.textContent = `#${currentPlayer.rank}`;
    rankBadge.classList.add('revealed');
  } else {
    rankValue.textContent = '???';
    rankBadge.classList.remove('revealed');
  }
}

// Toggle positional rank visibility
function togglePosRankVisibility() {
  const posRankBadge = document.getElementById('player-pos-rank');
  const posRankValue = posRankBadge.querySelector('.pos-rank-value');
 
  if (posRanksRevealed && currentPlayer) {
    // Show positional rank - check if it exists and is not empty
    const hasRank = currentPlayer.positional_rank &&
           currentPlayer.positional_rank !== '' &&
           currentPlayer.positional_rank !== 'null' &&
           currentPlayer.positional_rank !== 'undefined';
   
    if (hasRank) {
      posRankValue.textContent = `#${currentPlayer.positional_rank}`;
    } else {
      posRankValue.textContent = 'N/A';
    }
    posRankBadge.classList.add('revealed');
  } else {
    posRankValue.textContent = '???';
    posRankBadge.classList.remove('revealed');
  }
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
    const playersResponse = await fetch(`/api/players?${params.toString()}`);
    allPlayers = await playersResponse.json();
   
    if (allPlayers.length === 0) {
      alert('No players available with current filters!');
      randomizeBtn.disabled = false;
      return;
    }
   
    // Get random player
    const response = await fetch(`/api/random?${params.toString()}`);
    const player = await response.json();
   
    if (player.error) {
      alert(player.error);
      randomizeBtn.disabled = false;
      return;
    }
   
    currentPlayer = player;
   
    // Show and animate case opening
    await animateCaseOpening(player);
   
    // Display player details
    displayPlayerDetails(player);
   
    // Reload stats
    loadStats();
   
  } catch (error) {
    console.error('Error randomizing player:', error);
    alert('Error selecting player. Please try again.');
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
 
  // Update rank (hidden by default)
  const rankBadge = document.getElementById('player-rank');
  rankBadge.style.display = 'inline-block';
  toggleRankVisibility();
 
  // Update positional rank (always show, even if data is missing)
  const posRankBadge = document.getElementById('player-pos-rank');
  posRankBadge.style.display = 'inline-block';
  togglePosRankVisibility();
 
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
 
  // Update grade
  const gradeDisplay = document.getElementById('grade-display');
  const gradeDropdown = document.getElementById('grade-dropdown');
  if (player.grade) {
    gradeDisplay.textContent = player.grade;
    gradeDropdown.value = player.grade;
  } else {
    gradeDisplay.textContent = 'Not Graded';
    gradeDropdown.value = '';
  }
 
  // Update scout button
  const scoutBtn = document.getElementById('mark-scouted-btn');
  if (player.scouted) {
    scoutBtn.innerHTML = '<span>↺</span> Unmark as Scouted';
    scoutBtn.classList.add('scouted');
  } else {
    scoutBtn.innerHTML = '<span>✓</span> Mark as Scouted';
    scoutBtn.classList.remove('scouted');
  }
 
  // Show details section
  detailsSection.classList.remove('hidden');
  detailsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Toggle scout status
async function toggleScoutStatus() {
  if (!currentPlayer) return;
 
  try {
    const endpoint = currentPlayer.scouted ? 'unscout' : 'scout';
    const response = await fetch(`/api/player/${currentPlayer.id}/${endpoint}`, {
      method: 'POST'
    });
   
    if (response.ok) {
      currentPlayer.scouted = !currentPlayer.scouted;
     
      const scoutBtn = document.getElementById('mark-scouted-btn');
      if (currentPlayer.scouted) {
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
    alert('Error updating scout status. Please try again.');
  }
}

// Save notes
async function saveNotes() {
  if (!currentPlayer) return;
 
  const notes = document.getElementById('notes-input').value;
 
  try {
    const response = await fetch(`/api/player/${currentPlayer.id}/notes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ notes })
    });
   
    if (response.ok) {
      // Visual feedback
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
    alert('Error saving notes. Please try again.');
  }
}

// Update grade
async function updateGrade(grade) {
  if (!currentPlayer) return;
 
  try {
    const response = await fetch(`/api/player/${currentPlayer.id}/grade`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ grade })
    });
   
    if (response.ok) {
      currentPlayer.grade = grade;
      document.getElementById('grade-display').textContent = grade;
    }
  } catch (error) {
    console.error('Error updating grade:', error);
    alert('Error updating grade. Please try again.');
  }
}