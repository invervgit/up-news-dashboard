let allStories = [];
let currentMode = 'national';

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    document.getElementById('district-filter').addEventListener('change', renderStories);
    document.getElementById('category-filter').addEventListener('change', renderStories);
    document.getElementById('report-date').addEventListener('change', renderDashboardReport);
});

async function fetchData() {
    try {
        const response = await fetch('data/news.json');
        if (!response.ok) throw new Error("Data not found");
        allStories = await response.json();
        
        if(allStories.length > 0) {
            // Setup Date Dropdown for Dashboard
            populateDateDropdown();
            
            // Last Updated
            const dateStr = new Date(allStories[0].timestamp).toLocaleString();
            document.getElementById('last-updated').textContent = `Updated: ${dateStr}`;
        }
        
        // Default View
        switchMode('national');
        
    } catch (error) {
        document.getElementById('news-grid').innerHTML = `<p style="text-align:center">Error loading data. Check back later.</p>`;
        console.error(error);
    }
}

function populateDateDropdown() {
    const dateSelect = document.getElementById('report-date');
    const uniqueDates = [...new Set(allStories.map(s => s.date))].sort().reverse();
    
    dateSelect.innerHTML = '';
    uniqueDates.forEach(date => {
        const opt = document.createElement('option');
        opt.value = date;
        // Make it readable: "13 Jan 2026"
        const readable = new Date(date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
        opt.textContent = readable;
        dateSelect.appendChild(opt);
    });
}

function switchMode(mode) {
    currentMode = mode;
    
    // UI Toggles
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    
    const btns = document.querySelectorAll('.mode-btn');
    if(mode === 'national') btns[0].classList.add('active');
    if(mode === 'international') btns[1].classList.add('active');
    if(mode === 'state') btns[2].classList.add('active');
    if(mode === 'dashboard') btns[3].classList.add('active');

    // Section Visibility
    const filterBar = document.getElementById('filter-bar');
    const dashboardBar = document.getElementById('dashboard-bar');
    const newsGrid = document.getElementById('news-grid');
    const reportContainer = document.getElementById('executive-report');

    if (mode === 'dashboard') {
        filterBar.style.display = 'none';
        dashboardBar.style.display = 'flex';
        newsGrid.style.display = 'none';
        reportContainer.style.display = 'block';
        renderDashboardReport();
    } else {
        dashboardBar.style.display = 'none';
        reportContainer.style.display = 'none';
        newsGrid.style.display = 'grid';
        
        // Show filters only for State
        if (mode === 'state') {
            filterBar.style.display = 'flex';
            populateDistricts();
        } else {
            filterBar.style.display = 'none';
        }
        renderStories();
    }
}

function renderStories() {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = '';

    let filtered = allStories.filter(s => s.section.toLowerCase() === currentMode.toLowerCase().replace('_focus',''));
    
    // Fix for UP Focus naming mismatch ("UP_Focus" vs "state")
    if(currentMode === 'state') {
        filtered = allStories.filter(s => s.section === 'UP_Focus');
        const dist = document.getElementById('district-filter').value;
        const cat = document.getElementById('category-filter').value;
        if(dist !== 'All') filtered = filtered.filter(s => s.district === dist);
        if(cat !== 'All') filtered = filtered.filter(s => s.report_category.includes(cat));
        filtered = filtered.slice(0, 50);
    } else {
        filtered = filtered.slice(0, 40);
    }

    if (filtered.length === 0) {
        grid.innerHTML = '<p style="text-align:center; width:100%">No stories found.</p>';
        return;
    }

    filtered.forEach(item => {
        const timeStr = new Date(item.timestamp).toLocaleTimeString('en-IN', {hour: '2-digit', minute:'2-digit'});
        const card = document.createElement('div');
        card.className = `news-card cat-${item.report_category.split('_')[1] || 'General'}`;
        card.innerHTML = `
            <div class="meta"><span>${item.source}</span><span>${timeStr}</span></div>
            <h3><a href="${item.link}" target="_blank">${item.title}</a></h3>
            <p class="summary">${item.summary}</p>
        `;
        grid.appendChild(card);
    });
}

function populateDistricts() {
    const select = document.getElementById('district-filter');
    if (select.children.length > 1) return;
    const dists = [...new Set(allStories.filter(s => s.section === 'UP_Focus').map(s => s.district))].sort();
    dists.forEach(d => {
        if(d) {
            const opt = document.createElement('option');
            opt.value = d; opt.textContent = d; select.appendChild(opt);
        }
    });
}

// --- DASHBOARD & PDF LOGIC ---

function renderDashboardReport() {
    const selectedDate = document.getElementById('report-date').value;
    const content = document.getElementById('report-content');
    document.getElementById('report-date-display').innerText = `Report Date: ${new Date(selectedDate).toDateString()}`;
    
    // Filter by Date
    const dailyNews = allStories.filter(s => s.date === selectedDate);
    
    if(dailyNews.length === 0) {
        content.innerHTML = "<p>No data available for this date.</p>";
        return;
    }

    // Bucket Logic (Top 50 Total)
    // 1. International (Top 8)
    const intl = dailyNews.filter(s => s.section === 'International').slice(0, 8);
    
    // 2. National Govt (Top 25)
    const natGov = dailyNews.filter(s => s.report_category === 'National_Govt').slice(0, 25);
    
    // 3. Opposition (Top 10)
    const opp = dailyNews.filter(s => s.report_category === 'National_Opposition').slice(0, 10);
    
    // 4. Judicial (Top 7)
    const jud = dailyNews.filter(s => s.report_category === 'National_Judicial').slice(0, 7);

    const generateSection = (title, items) => {
        if(items.length === 0) return '';
        let html = `<div class="pdf-section"><h3>${title}</h3><table class="report-table">`;
        items.forEach(item => {
            html += `
            <tr>
                <td class="col-text">
                    <strong>${item.title}</strong>
                    <br><span class="pdf-summary">${item.summary}</span>
                </td>
                <td class="col-link">
                    <a href="${item.link}" target="_blank">Open Link</a>
                </td>
            </tr>`;
        });
        html += `</table></div>`;
        return html;
    };

    let html = '';
    html += generateSection("1. International Updates", intl);
    html += generateSection("2. National: Government Policies & Mandates", natGov);
    html += generateSection("3. Opposition Activity", opp);
    html += generateSection("4. Judicial & Supreme Court Verdicts", jud);

    content.innerHTML = html || "<p>No specific categorized news found for today.</p>";
}

function downloadPDF() {
    const element = document.getElementById('executive-report');
    const opt = {
        margin:       0.5,
        filename:     `Executive_Briefing_${document.getElementById('report-date').value}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
    };
    
    // Temporarily show element if hidden (though logic handles this)
    html2pdf().set(opt).from(element).save();
}

window.switchMode = switchMode;
window.downloadPDF = downloadPDF;
