let allStories = [];
let currentMode = 'national'; // 'national' or 'state'

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    
    // Dropdown Listeners
    document.getElementById('district-filter').addEventListener('change', renderStories);
    document.getElementById('category-filter').addEventListener('change', renderStories);
});

async function fetchData() {
    try {
        const response = await fetch('data/news.json');
        if (!response.ok) throw new Error("Data not found");
        allStories = await response.json();
        
        // Update Last Updated Text
        if(allStories.length > 0) {
            const date = new Date(allStories[0].pubDate);
            document.getElementById('last-updated').textContent = `Last Updated: ${date.toLocaleString()}`;
        }

        // Initial Render (National)
        switchMode('national');
        
    } catch (error) {
        document.getElementById('news-grid').innerHTML = `<p style="text-align:center">Error loading data. System may be updating.</p>`;
        console.error(error);
    }
}

function switchMode(mode) {
    currentMode = mode;
    
    // Update Buttons
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active'); // Note: this assumes event is passed implicitly or you bind it, simpler logic below:
    
    // Explicit Button styling fix
    const btns = document.querySelectorAll('.mode-btn');
    if(mode === 'national') { btns[0].classList.add('active'); btns[1].classList.remove('active'); }
    else { btns[1].classList.add('active'); btns[0].classList.remove('active'); }

    // Toggle Filters Visibility
    const filterBar = document.getElementById('filter-bar');
    if (mode === 'state') {
        filterBar.style.display = 'flex';
        populateDistricts();
    } else {
        filterBar.style.display = 'none';
    }

    renderStories();
}

// Global scope for onclick to work
window.switchMode = switchMode; 

function populateDistricts() {
    const districtSelect = document.getElementById('district-filter');
    // Keep "All Districts"
    districtSelect.innerHTML = '<option value="All">All Districts</option>';
    
    // Get unique districts from State stories only
    const stateStories = allStories.filter(s => s.scope === 'state');
    const districts = [...new Set(stateStories.map(s => s.district))].sort();
    
    districts.forEach(d => {
        if (d && d !== 'Uttar Pradesh') { // Don't duplicate generic UP tag
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            districtSelect.appendChild(opt);
        }
    });
}

function renderStories() {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = '';

    // 1. Filter by Mode (National vs State)
    let filtered = allStories.filter(s => s.scope === currentMode);

    // 2. Apply Sub-filters (Only if in State mode)
    if (currentMode === 'state') {
        const distFilter = document.getElementById('district-filter').value;
        const catFilter = document.getElementById('category-filter').value;

        if (distFilter !== 'All') {
            filtered = filtered.filter(s => s.district === distFilter);
        }
        if (catFilter !== 'All') {
            filtered = filtered.filter(s => s.category.includes(catFilter.split(' ')[0])); // Simple check
        }
        
        // Slice Top 50 for UP
        filtered = filtered.slice(0, 50);
    } else {
        // National doesn't need strict district filtering
        filtered = filtered.slice(0, 30); // Top 30 National
    }

    if (filtered.length === 0) {
        grid.innerHTML = '<p style="text-align:center; grid-column: 1/-1;">No stories found matching criteria.</p>';
        return;
    }

    filtered.forEach(item => {
        const dateObj = new Date(item.pubDate);
        const dateStr = dateObj.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute:'2-digit'});
        const catClass = `cat-${item.category.toLowerCase().replace(/[^a-z]/g, '-')}`;

        const card = document.createElement('div');
        card.className = `news-card ${catClass}`;
        card.innerHTML = `
            <div class="meta">
                <span>${item.source}</span>
                <span>${dateStr}</span>
            </div>
            <h3><a href="${item.link}" target="_blank">${item.title}</a></h3>
            <p class="summary">${item.summary}</p>
            <div class="footer">
                <span class="tag">${item.district}</span>
                <span class="tag">${item.category}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}
