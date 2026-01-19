let allStories = [];
let currentMode = 'international';
let isManualMode = false;

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
        const data = await response.json();
        
        // Support both old list and new dict formats
        if (Array.isArray(data)) {
            allStories = data;
            if(allStories.length > 0) updateTimeDisplay(allStories[0].timestamp);
        } else {
            allStories = data.stories;
            updateTimeDisplay(data.generated_at);
        }
        
        if(allStories.length > 0) populateDateDropdown();
        switchMode('international');
        
    } catch (error) {
        console.error("Error loading data:", error);
        document.getElementById('news-grid').innerHTML = '<p style="text-align:center">Error loading data.</p>';
    }
}

function updateTimeDisplay(isoString) {
    if (!isoString) return;
    const date = new Date(isoString);
    const options = { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit', hour12: true };
    document.getElementById('last-updated').textContent = `Updated: ${date.toLocaleDateString('en-IN', options)}`;
}

function populateDateDropdown() {
    const dateSelect = document.getElementById('report-date');
    // Extract unique dates
    const uniqueDates = [...new Set(allStories.map(s => s.date))].sort().reverse();
    
    dateSelect.innerHTML = '';
    uniqueDates.forEach(date => {
        const opt = document.createElement('option');
        opt.value = date;
        opt.textContent = new Date(date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
        dateSelect.appendChild(opt);
    });
}

function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    
    const btns = document.querySelectorAll('.mode-btn');
    if(mode==='international') btns[0].classList.add('active');
    if(mode==='national') btns[1].classList.add('active');
    if(mode==='state') btns[2].classList.add('active');
    if(mode==='dashboard') btns[3].classList.add('active');

    const filterBar = document.getElementById('filter-bar');
    const dashboardBar = document.getElementById('dashboard-bar');
    const newsGrid = document.getElementById('news-grid');
    const reportContainer = document.getElementById('executive-report');

    if (mode === 'dashboard') {
        filterBar.style.display = 'none';
        dashboardBar.style.display = 'flex';
        newsGrid.style.display = 'none';
        reportContainer.style.display = 'block';
        
        // Reset Manual Mode
        isManualMode = false;
        document.getElementById('manual-controls').style.display = 'none';
        document.getElementById('report-title').textContent = 'Daily Digest';
        
        renderDashboardReport();
    } else {
        dashboardBar.style.display = 'none';
        reportContainer.style.display = 'none';
        newsGrid.style.display = 'grid';
        filterBar.style.display = (mode === 'state') ? 'flex' : 'none';
        
        if(mode === 'state') populateDistricts();
        renderStories();
    }
}

// --- READ MORE LOGIC ---
function createSummaryHtml(text) {
    const limit = 350;
    if (!text || text.length <= limit) return text;
    const shortText = text.substring(0, limit);
    return `<span class="short-content">${shortText}... </span><span class="full-content" style="display:none">${text}</span><span class="read-more-link" onclick="toggleReadMore(this)">Read More</span>`;
}

window.toggleReadMore = function(btn) {
    const parent = btn.parentElement;
    const short = parent.querySelector('.short-content');
    const full = parent.querySelector('.full-content');
    
    if (full.style.display === 'none') {
        full.style.display = 'inline';
        short.style.display = 'none';
        btn.textContent = ' Read Less';
    } else {
        full.style.display = 'none';
        short.style.display = 'inline';
        btn.textContent = ' Read More';
    }
};

function renderStories() {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = '';
    
    let filtered = allStories.filter(s => s.section.toLowerCase() === currentMode.toLowerCase().replace('_focus',''));
    
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

    if(filtered.length === 0) { grid.innerHTML = '<p>No stories found.</p>'; return; }

    filtered.forEach(item => {
        const time = new Date(item.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
        const card = document.createElement('div');
        card.className = `news-card cat-${item.report_category.split('_')[1] || 'General'}`;
        card.innerHTML = `<div class="meta"><span>${item.source}</span><span>${time}</span></div><h3><a href="${item.link}" target="_blank">${item.title}</a></h3><p class="summary">${createSummaryHtml(item.summary)}</p>`;
        grid.appendChild(card);
    });
}

function populateDistricts() {
    const select = document.getElementById('district-filter');
    if (select.children.length > 1) return;
    const dists = [...new Set(allStories.filter(s => s.section === 'UP_Focus').map(s => s.district))].sort();
    dists.forEach(d => { if(d) { const o = document.createElement('option'); o.value=d; o.textContent=d; select.appendChild(o); }});
}

// --- DASHBOARD & REPORT ---

function toggleManualMode() {
    isManualMode = !isManualMode;
    const manualControls = document.getElementById('manual-controls');
    const title = document.getElementById('report-title');
    
    if(isManualMode) {
        manualControls.style.display = 'block';
        title.textContent = 'Manual Report Selection';
    } else {
        manualControls.style.display = 'none';
        title.textContent = 'Daily Digest';
    }
    renderDashboardReport();
}

function renderDashboardReport() {
    const selectedDate = document.getElementById('report-date').value;
    const content = document.getElementById('report-content');
    document.getElementById('report-date-display').innerText = `Report Date: ${new Date(selectedDate).toDateString()}`;
    
    const dailyNews = allStories.filter(s => s.date === selectedDate);
    if(dailyNews.length === 0) { content.innerHTML = "<p>No data.</p>"; return; }

    let intl, natGov, opp, jud;

    if(isManualMode) {
        // Show ALL for selection
        intl = dailyNews.filter(s => s.section === 'International');
        natGov = dailyNews.filter(s => s.report_category === 'National_Govt');
        opp = dailyNews.filter(s => s.report_category === 'National_Opposition');
        jud = dailyNews.filter(s => s.report_category === 'National_Judicial');
    } else {
        // Concise Limits for Auto Mode
        intl = dailyNews.filter(s => s.section === 'International').slice(0, 5);
        natGov = dailyNews.filter(s => s.report_category === 'National_Govt').slice(0, 15);
        opp = dailyNews.filter(s => s.report_category === 'National_Opposition').slice(0, 5);
        jud = dailyNews.filter(s => s.report_category === 'National_Judicial').slice(0, 5);
    }

    const generateSection = (title, items) => {
        if(items.length === 0) return '';
        let html = `<div class="pdf-section"><h3>${title}</h3><table class="report-table">`;
        items.forEach(item => {
            const checkbox = isManualMode ? `<input type="checkbox" class="news-select" data-id="${item.id}" checked> ` : '● ';
            html += `
            <tr class="news-row" data-id="${item.id}">
                <td style="width: 85%;">
                    <span class="news-title">${checkbox}${item.title}</span>
                    <span class="news-summary">${item.summary}</span>
                </td>
                <td style="width: 15%; text-align: right; vertical-align: top;">
                    <span class="source-link"><a href="${item.link}" target="_blank">Source</a></span>
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
    content.innerHTML = html || "<p>No categorized news found.</p>";
}

// --- PDF GENERATION LOGIC ---

// 1. Browser Print (Best for Selectable Text)
function printSelectablePDF() {
    // Hide unselected items if in manual mode
    if(isManualMode) {
        document.querySelectorAll('.news-select').forEach(cb => {
            if(!cb.checked) {
                cb.closest('tr').classList.add('hide-for-print');
            } else {
                cb.style.display = 'none'; // Hide checkbox itself
            }
        });
    }
    
    window.print(); // Browser's Native Print to PDF
    
    // Restore UI
    if(isManualMode) {
        document.querySelectorAll('.news-select').forEach(cb => cb.style.display = 'inline');
        document.querySelectorAll('.hide-for-print').forEach(row => row.classList.remove('hide-for-print'));
    }
}

// 2. HTML2PDF (Image Based, Backup)
function getPdfConfig(filename) {
    return {
        margin: [0.25, 0.5, 0.25, 0.5],
        filename: filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['css', 'legacy'] }
    };
}

function downloadAutoPDF() {
    // Simple Image PDF
    const element = document.getElementById('executive-report');
    const filename = `Daily_Digest_${document.getElementById('report-date').value}.pdf`;
    
    // Hide checkboxes
    document.querySelectorAll('.news-select').forEach(cb => cb.style.display = 'none');

    html2pdf().from(element).set(getPdfConfig(filename)).toPdf().get('pdf').then(function(pdf) {
        addHeader(pdf);
    }).save().then(() => {
        if(isManualMode) document.querySelectorAll('.news-select').forEach(cb => cb.style.display = 'inline');
    });
}

function downloadManualPDF() {
    // 1. Hide rows that are NOT checked
    document.querySelectorAll('.news-select').forEach(cb => {
        if(!cb.checked) {
            cb.closest('tr').style.display = 'none';
        } else {
            cb.style.display = 'none'; // Hide the checkbox itself
        }
    });

    const element = document.getElementById('executive-report');
    const filename = `Manual_Report_${document.getElementById('report-date').value}.pdf`;

    html2pdf().from(element).set(getPdfConfig(filename)).toPdf().get('pdf').then(function(pdf) {
        addHeader(pdf);
    }).save().then(() => {
        // Restore all rows
        document.querySelectorAll('tr').forEach(tr => tr.style.display = '');
        document.querySelectorAll('.news-select').forEach(cb => cb.style.display = 'inline');
    });
}

function addHeader(pdf) {
    const totalPages = pdf.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) { // Fixed variable 'i'
        pdf.setPage(i);
        pdf.setFontSize(10);
        pdf.setFont("helvetica", "italic");
        pdf.setTextColor(100);
        pdf.text('Internal Use Only', 6.5, 0.35); 
    }
}

window.switchMode = switchMode;
window.toggleManualMode = toggleManualMode;
// We now map the buttons to these functions
window.downloadAutoPDF = downloadAutoPDF; 
window.downloadManualPDF = downloadManualPDF;
// New function for selectable text
window.printSelectablePDF = printSelectablePDF;
