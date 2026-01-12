document.addEventListener('DOMContentLoaded', () => {
    let stories = [];
    let filteredStories = [];
    let currentPage = 1;
    let itemsPerPage = 50;
  
    const container = document.getElementById('news-container');
    const pagination = document.getElementById('pagination');
    
    // UI Elements
    const districtSelect = document.getElementById('district');
    const categorySelect = document.getElementById('category');
    const startInput = document.getElementById('start-date');
    const endInput = document.getElementById('end-date');
    const itemsSelect = document.getElementById('items-per-page');
    const todayBtn = document.getElementById('today-btn');
    const resetBtn = document.getElementById('reset-btn');
  
    // Show Loading State
    container.innerHTML = '<div class="loading">Loading latest news...</div>';
  
    fetch('data/news.json')
      .then(response => {
        if (!response.ok) throw new Error("File not found");
        return response.json();
      })
      .then(data => {
        stories = data;
        if (stories.length === 0) {
            container.innerHTML = '<p>No news data found. Please check back later.</p>';
            return;
        }
        populateFilters();
        applyFilters(); // Render initial data
      })
      .catch(err => {
        console.error(err);
        container.innerHTML = `<div class="error">
          <h3>Failed to load news</h3>
          <p>This might be because the data is being updated. Please try refreshing in a few minutes.</p>
        </div>`;
      });
  
    function populateFilters() {
      // Extract unique districts and sort alphabetically
      const districts = [...new Set(stories.map(s => s.district).filter(d => d))].sort();
      
      // Clear existing options except "All"
      districtSelect.innerHTML = '<option value="All">All districts</option>';
      
      districts.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d;
        opt.textContent = d;
        districtSelect.appendChild(opt);
      });
    }
  
    function applyFilters() {
      const startDate = startInput.value;
      const endDate = endInput.value;
      const category = categorySelect.value;
      const district = districtSelect.value;
      itemsPerPage = parseInt(itemsSelect.value) || 50;
  
      filteredStories = stories.filter(s => {
        const sDate = s.pubDate.split('T')[0]; // YYYY-MM-DD
        
        let matchesDate = true;
        if (startDate) matchesDate = matchesDate && (sDate >= startDate);
        if (endDate) matchesDate = matchesDate && (sDate <= endDate);
        
        let matchesCat = (category === 'All') || (s.category === category);
        let matchesDist = (district === 'All') || (s.district === district);
        
        return matchesDate && matchesCat && matchesDist;
      });
  
      currentPage = 1;
      renderPage(currentPage);
    }
  
    function renderPage(page) {
      container.innerHTML = '';
      
      if (filteredStories.length === 0) {
        container.innerHTML = '<p class="no-results">No stories match your filters.</p>';
        pagination.innerHTML = '';
        return;
      }
  
      const start = (page - 1) * itemsPerPage;
      const end = start + itemsPerPage;
      const pageItems = filteredStories.slice(start, end);
  
      pageItems.forEach(item => {
        const card = document.createElement('div');
        card.className = 'news-card';
        
        const date = new Date(item.pubDate).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
        });
        
        // Safety check for summary
        let cleanSummary = item.summary || "No summary available.";
        // Ensure no "Link Copied" remains
        cleanSummary = cleanSummary.replace(/Link Copied/gi, "").replace(/मेरा शहर/g, "");
  
        card.innerHTML = `
          <div class="card-header">
            <span class="source-tag">${item.source}</span>
            <span class="district-tag">${item.district}</span>
          </div>
          <h3><a href="${item.link}" target="_blank">${item.title}</a></h3>
          <div class="meta-info">
             <span class="date">${date}</span>
             <span class="badge ${item.category.replace(/\s+/g, '-').toLowerCase()}">${item.category}</span>
          </div>
          <p class="summary">${cleanSummary}</p>
        `;
        container.appendChild(card);
      });
  
      renderPagination();
    }
  
    function renderPagination() {
        pagination.innerHTML = '';
        const totalPages = Math.ceil(filteredStories.length / itemsPerPage);
        
        if (totalPages <= 1) return;
  
        const createBtn = (page, text) => {
            const btn = document.createElement('button');
            btn.textContent = text || page;
            btn.className = page === currentPage ? 'active' : '';
            btn.onclick = () => {
                currentPage = page;
                renderPage(currentPage);
                window.scrollTo(0, 0);
            };
            return btn;
        };
  
        // Prev
        if (currentPage > 1) pagination.appendChild(createBtn(currentPage - 1, '«'));
  
        // Simple pagination logic (show current, prev, next)
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, currentPage + 2);
  
        for (let i = startPage; i <= endPage; i++) {
            pagination.appendChild(createBtn(i));
        }
  
        // Next
        if (currentPage < totalPages) pagination.appendChild(createBtn(currentPage + 1, '»'));
    }
  
    // Event Listeners
    [startInput, endInput, categorySelect, districtSelect, itemsSelect].forEach(el => {
        el.addEventListener('change', applyFilters);
    });
  
    todayBtn.addEventListener('click', () => {
        const today = new Date().toISOString().split('T')[0];
        startInput.value = today;
        endInput.value = today;
        categorySelect.value = 'All';
        districtSelect.value = 'All';
        applyFilters();
    });
  
    resetBtn.addEventListener('click', () => {
        startInput.value = '';
        endInput.value = '';
        categorySelect.value = 'All';
        districtSelect.value = 'All';
        itemsSelect.value = '50';
        applyFilters();
    });
});
