let allStories = [];
let currentMode = 'national';

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    document.getElementById('district-filter').addEventListener('change', renderStories);
    document.getElementById('category-filter').addEventListener('change', renderStories);
});

async function fetchData() {
    try {
        const response = await fetch('data/news.json');
        if (!response.ok) throw new Error("Data not found");
        allStories = await response.json();
        
        if(allStories.length > 0) {
            // Simply use the date string as provided by Python
            const dateStr = new Date(allStories[0].pubDate).toLocaleString();
            document.getElementById('last-updated').textContent = `Updated: ${dateStr}`;
        }
        
        switchMode('national');
        
    } catch (error) {
        document.getElementById('news-grid').innerHTML = `<p style="text-align:center">Error loading data. Please wait for the next update cycle.</p>`;
        console.error(error);
    }
}

function switchMode(mode) {
    currentMode = mode;
    
    // Update Buttons
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    // Find button with specific onclick text to add active class
    const buttons = document.querySelectorAll('.mode-btn');
    if(mode === 'national') buttons[0].classList.add('active');
    if(mode === 'international') buttons[1].classList.add('active');
    if(mode === 'state') buttons[2].classList.add('active');

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

function populateDistricts() {
    const districtSelect = document.getElementById('district-filter');
    districtSelect.innerHTML = '<option value="All">All Districts</option>';
    
    const stateStories = allStories.filter(s => s.scope === 'state');
    const districts = [...new Set(stateStories.map(s => s.district))].sort();
    
    districts.forEach(d => {
        if (d && d !== 'Uttar Pradesh' && d !== 'General') {
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

    // 1. Filter by Mode
    let filtered = allStories.filter(s => s.scope === currentMode);

    // 2. Apply UP Specific Filters
    if (currentMode === 'state') {
        const distFilter = document.getElementById('district-filter').value;
        const catFilter = document.getElementById('category-filter').value;

        if (distFilter !== 'All') {
            filtered = filtered.filter(s => s.district === distFilter);
        }
        if (catFilter !== 'All') {
            filtered = filtered.filter(s => s.category.includes(catFilter));
        }
        
        filtered = filtered.slice(0, 50); // Top 50 Limit
    } else {
        // Limit for National/International to keep page light
        filtered = filtered.slice(0, 40);
    }

    if (filtered.length === 0) {
        grid.innerHTML = '<p style="text-align:center; grid-column: 1/-1;">No stories found.</p>';
        return;
    }

    filtered.forEach(item => {
        const dateObj = new Date(item.pubDate);
        const timeStr = dateObj.toLocaleTimeString('en-IN', {hour: '2-digit', minute:'2-digit'});
        const catClass = `cat-${item.category.toLowerCase().split(' ')[0]}`;

        const card = document.createElement('div');
        card.className = `news-card ${catClass}`;
        
        // Tags Logic
        let tagsHtml = `<span class="tag">${item.category}</span>`;
        if (currentMode === 'state') {
            tagsHtml += `<span class="tag">${item.district}</span>`;
        }

        card.innerHTML = `
            <div class="meta">
                <span>${item.source}</span>
                <span>${timeStr}</span>
            </div>
            <h3><a href="${item.link}" target="_blank">${item.title}</a></h3>
            <p class="summary">${item.summary}</p>
            <div class="footer">
                ${tagsHtml}
            </div>
        `;
        grid.appendChild(card);
    });
}

// Global Hook
window.switchMode = switchMode;
