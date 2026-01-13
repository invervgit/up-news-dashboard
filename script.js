let allStories = [];
let currentTab = 'dashboard';

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    // Setup listeners
    document.getElementById('district-filter').addEventListener('change', renderGrid);
});

async function fetchData() {
    try {
        const response = await fetch('data/news.json');
        if (!response.ok) throw new Error("Data not found");
        allStories = await response.json();
        
        // Populate Date Dropdown (Last 7 Days)
        setupDateSelector();
        
        // Initial Render
        switchTab('dashboard');
        
        // Update Timestamp
        if(allStories.length > 0) {
            document.getElementById('last-updated').innerText = "Last Sync: " + new Date().toLocaleTimeString();
        }
    } catch (e) {
        console.error(e);
        document.getElementById('report-container').innerHTML = `<div class="error">System Update in Progress. Please check back in 5 minutes.</div>`;
    }
}

function setupDateSelector() {
    const selector = document.getElementById('report-date-select');
    selector.innerHTML = '';
    
    // Get unique dates present in data
    const dates = [...new Set(allStories.map(s => s.date))].sort().reverse();
    
    // Add "Today" explicitly if not present (handled by sort usually)
    const today = new Date().toISOString().split('T')[0];
    
    dates.forEach(date => {
        const opt = document.createElement('option');
        opt.value = date;
        // Format: "13 Jan 2026 (Today)"
        const dateObj = new Date(date);
        let label = dateObj.toLocaleDateString('en-IN', {day: 'numeric', month: 'short', year: 'numeric'});
        if (date === today) label += " (Today)";
        opt.textContent = label;
        selector.appendChild(opt);
    });
}

function switchTab(tab) {
    currentTab = tab;
    
    // UI Toggles
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    // Simple index mapping or find by text
    const buttons = document.querySelectorAll('.tab-btn');
    if(tab === 'dashboard') buttons[0].classList.add('active');
    if(tab === 'international') buttons[1].classList.add('active');
    if(tab === 'national') buttons[2].classList.add('active');
    if(tab === 'up-focus') buttons[3].classList.add('active');

    const dashboardView = document.getElementById('view-dashboard');
    const gridView = document.getElementById('view-grid');
    const datePanel = document.getElementById('date-control-panel');
    const gridFilters = document.getElementById('grid-filters');

    if (tab === 'dashboard') {
        dashboardView.classList.remove('hidden');
        gridView.classList.add('hidden');
        datePanel.style.display = 'flex';
        renderDashboard();
    } else {
        dashboardView.classList.add('hidden');
        gridView.classList.remove('hidden');
        datePanel.style.display = 'none';
        
        // UP Focus specific filters
        if (tab === 'up-focus') {
            gridFilters.classList.remove('hidden');
            populateDistricts();
        } else {
            gridFilters.classList.add('hidden');
        }
        renderGrid();
    }
}

function renderDashboard() {
    const container = document.getElementById('report-container');
    const selectedDate = document.getElementById('report-date-select').value;
    
    // Filter by Date
    const daysNews = allStories.filter(s => s.date === selectedDate);
    
    if (daysNews.length === 0) {
        container.innerHTML = `<div class="empty-report">No reports filed for ${selectedDate}.</div>`;
        return;
    }

    // Bucket Data
    const sections = {
        intl: daysNews.filter(s => s.section === 'International').slice(0, 8),
        govt: daysNews.filter(s => s.report_category === 'National_Govt').slice(0, 30),
        opp: daysNews.filter(s => s.report_category === 'National_Opposition').slice(0, 15),
        jud: daysNews.filter(s => s.report_category === 'National_Judicial').slice(0, 10)
    };

    let html = '';

    // Helper to generate list items
    const generateList = (items) => {
        if (items.length === 0) return '<p class="no-news">No significant updates reported.</p>';
        return items.map(item => `
            <div class="report-item">
                <div class="report-content">
                    <h4>${item.title} <span class="source-badge">${item.source}</span></h4>
                    <p>${item.summary}</p>
                </div>
                <a href="${item.link}" target="_blank" class="report-link" title="Read Full Source">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                </a>
            </div>
        `).join('');
    };

    // 1. International
    html += `<section class="report-section">
        <h2 class="sec-title intl">🌍 1. International Intelligence</h2>
        <div class="report-list">${generateList(sections.intl)}</div>
    </section>`;

    // 2. National Government
    html += `<section class="report-section">
        <h2 class="sec-title govt">🇮🇳 2. Government, Policy & Mandates</h2>
        <div class="report-list">${generateList(sections.govt)}</div>
    </section>`;

    // 3. Opposition
    html += `<section class="report-section">
        <h2 class="sec-title opp">📢 3. Opposition Activity</h2>
        <div class="report-list">${generateList(sections.opp)}</div>
    </section>`;

    // 4. Judicial
    html += `<section class="report-section">
        <h2 class="sec-title jud">⚖️ 4. Judicial & Legal Verdicts</h2>
        <div class="report-list">${generateList(sections.jud)}</div>
    </section>`;

    container.innerHTML = html;
}

function renderGrid() {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = '';
    
    let filtered = [];
    
    // Map tab to section/category logic
    if (currentTab === 'international') {
        filtered = allStories.filter(s => s.section === 'International');
    } else if (currentTab === 'national') {
        filtered = allStories.filter(s => s.section === 'National');
    } else if (currentTab === 'up-focus') {
        filtered = allStories.filter(s => s.section === 'UP_Focus');
        const dist = document.getElementById('district-filter').value;
        if (dist !== 'All') filtered = filtered.filter(s => s.district === dist);
    }
    
    // Sort Grid by latest always
    filtered = filtered.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 50);

    filtered.forEach(item => {
        const card = document.createElement('div');
        card.className = 'grid-card';
        card.innerHTML = `
            <div class="meta">${new Date(item.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})} • ${item.source}</div>
            <h3><a href="${item.link}" target="_blank">${item.title}</a></h3>
            <p>${item.summary}</p>
        `;
        grid.appendChild(card);
    });
}

function populateDistricts() {
    const select = document.getElementById('district-filter');
    if (select.children.length > 1) return; // Already populated
    const dists = [...new Set(allStories.filter(s => s.section === 'UP_Focus').map(s => s.district))].sort();
    dists.forEach(d => {
        if(d) {
            const opt = document.createElement('option');
            opt.value = d; opt.textContent = d; select.appendChild(opt);
        }
    });
}

// Export for HTML access
window.switchTab = switchTab;
window.renderDashboard = renderDashboard;
window.renderGrid = renderGrid;
