let allNews = [];
let currentView = 'national'; // 'national' or 'state'

document.addEventListener('DOMContentLoaded', () => {
    loadNews();

    // Event Listeners for Filters
    document.getElementById('district-select').addEventListener('change', renderNews);
    document.getElementById('category-select').addEventListener('change', renderNews);
});

async function loadNews() {
    try {
        const response = await fetch('data/news.json');
        if (!response.ok) throw new Error("Failed to load data");
        
        allNews = await response.json();
        
        // Update Timestamp from the first story
        if (allNews.length > 0) {
            const latest = new Date(allNews[0].pubDate);
            document.getElementById('last-updated').innerText = 
                `Last Updated: ${latest.toLocaleDateString('en-IN')} ${latest.toLocaleTimeString('en-IN')}`;
        }

        // Initial Render
        setView('national');

    } catch (error) {
        console.error(error);
        document.getElementById('news-grid').innerHTML = 
            `<div class="error">Data not found. Please ensure the GitHub Action has run successfully.</div>`;
    }
}

function setView(view) {
    currentView = view;
    
    // Toggle Button Styles
    document.getElementById('btn-national').classList.toggle('active', view === 'national');
    document.getElementById('btn-state').classList.toggle('active', view === 'state');
    
    // Toggle Filter Visibility
    const filterSection = document.getElementById('filter-section');
    if (view === 'state') {
        filterSection.classList.remove('hidden');
        populateDistricts();
    } else {
        filterSection.classList.add('hidden');
    }

    renderNews();
}

function populateDistricts() {
    const select = document.getElementById('district-select');
    select.innerHTML = '<option value="All">All Districts</option>';
    
    // Get unique districts from State news only
    const districts = [...new Set(
        allNews.filter(n => n.scope === 'state').map(n => n.district)
    )].sort();
    
    districts.forEach(d => {
        if (d && d !== 'Uttar Pradesh') {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            select.appendChild(opt);
        }
    });
}

function renderNews() {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = '';

    // 1. Filter by Scope (National vs State)
    let filtered = allNews.filter(n => n.scope === currentView);

    // 2. Apply Filters (Only for State view)
    if (currentView === 'state') {
        const distFilter = document.getElementById('district-select').value;
        const catFilter = document.getElementById('category-select').value;

        if (distFilter !== 'All') {
            filtered = filtered.filter(n => n.district === distFilter);
        }
        if (catFilter !== 'All') {
            filtered = filtered.filter(n => n.category === catFilter);
        }
        
        // Limit to Top 50 as requested
        filtered = filtered.slice(0, 50);
    } else {
        // Limit National to Top 30
        filtered = filtered.slice(0, 30);
    }

    if (filtered.length === 0) {
        grid.innerHTML = '<div class="empty">No news found for this selection.</div>';
        return;
    }

    // Render Cards
    filtered.forEach(item => {
        const dateStr = new Date(item.pubDate).toLocaleTimeString('en-IN', {
            hour: '2-digit', minute: '2-digit'
        });
        
        // Define color borders based on category
        let borderColor = '#ccc';
        if(item.category === 'Government') borderColor = '#f39c12';
        if(item.category === 'Opposition') borderColor = '#e74c3c';
        if(item.category === 'Governance') borderColor = '#2ecc71';
        if(item.category === 'Judicial') borderColor = '#3498db';

        const card = document.createElement('div');
        card.className = 'card';
        card.style.borderLeft = `5px solid ${borderColor}`;
        
        card.innerHTML = `
            <div class="card-meta">
                <span class="source">${item.source}</span>
                <span class="time">${dateStr}</span>
            </div>
            <h3><a href="${item.link}" target="_blank">${item.title}</a></h3>
            <p>${item.summary}</p>
            <div class="card-tags">
                ${currentView === 'state' ? `<span class="tag district">${item.district}</span>` : ''}
                <span class="tag cat">${item.category}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

// Global scope for onclick handlers
window.setView = setView;
