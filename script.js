/*
 * Client‑side logic for the enhanced Uttar Pradesh news dashboard.
 *
 * This script fetches the pre‑compiled JSON data file produced by
 * fetch_news.py and renders it into a responsive grid of cards.  Users
 * can filter by date range, category or district, change the number of
 * items per page, and view the top 50 stories published today.  The
 * cards display a coloured badge indicating the category and a
 * multi‑sentence summary so readers do not need to leave the page.
 */

document.addEventListener('DOMContentLoaded', () => {
  let stories = [];
  let filteredStories = [];
  let currentPage = 1;
  let itemsPerPage = 50;

  // Load the JSON data file
  fetch('data/news.json')
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to load news data');
      }
      return response.json();
    })
    .then(data => {
      stories = data;
      initialiseFilters();
      // Apply default filters and render the first page
      applyFilters();
    })
    .catch(err => {
      const container = document.getElementById('news-container');
      container.innerHTML = `<p>Error loading news: ${err.message}</p>`;
    });

  function initialiseFilters() {
    const startInput = document.getElementById('start-date');
    const endInput = document.getElementById('end-date');
    const categorySelect = document.getElementById('category');
    const districtSelect = document.getElementById('district');
    const itemsSelect = document.getElementById('items-per-page');
    const todayBtn = document.getElementById('today-btn');
    const resetBtn = document.getElementById('reset-btn');

    // Populate the district dropdown with unique values from the data
    const districts = Array.from(new Set(stories.map(s => s.district).filter(d => !!d))).sort();
    districts.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d;
      opt.textContent = d;
      districtSelect.appendChild(opt);
    });

    // Set default items per page
    itemsSelect.value = '50';

    // Event listeners for filter changes
    startInput.addEventListener('change', applyFilters);
    endInput.addEventListener('change', applyFilters);
    categorySelect.addEventListener('change', applyFilters);
    districtSelect.addEventListener('change', applyFilters);
    itemsSelect.addEventListener('change', () => {
      itemsPerPage = parseInt(itemsSelect.value, 10) || 50;
      currentPage = 1;
      applyFilters();
    });

    // Event listeners for filter actions
    todayBtn.addEventListener('click', () => {
      const todayStr = new Date().toISOString().split('T')[0];
      const todayStories = stories.filter(s => s.pubDate.startsWith(todayStr));
      filteredStories = todayStories.slice(0, 50);
      itemsPerPage = 50;
      currentPage = 1;
      renderPage(currentPage);
    });

    resetBtn.addEventListener('click', () => {
      startInput.value = '';
      endInput.value = '';
      categorySelect.value = 'All';
      districtSelect.value = 'All';
      itemsSelect.value = '50';
      itemsPerPage = 50;
      currentPage = 1;
      applyFilters();
    });
  }

  function applyFilters() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const category = document.getElementById('category').value;
    const district = document.getElementById('district').value;

    // Filter the stories based on selected filters
    let filtered = stories;

    if (startDate) {
      filtered = filtered.filter(s => s.pubDate >= startDate);
    }

    if (endDate) {
      const end = new Date(endDate);
      end.setDate(end.getDate() + 1);
      const isoNext = end.toISOString().split('T')[0];
      filtered = filtered.filter(s => s.pubDate < isoNext);
    }

    if (category && category !== 'All') {
      filtered = filtered.filter(s => s.category === category);
    }

    if (district && district !== 'All') {
      filtered = filtered.filter(s => s.district === district);
    }

    filteredStories = filtered;
    currentPage = 1;
    renderPage(currentPage);
  }

  function categoryToSlug(cat) {
    return cat.toLowerCase().replace(/\s+/g, '-');
  }

  function render(list) {
    const container = document.getElementById('news-container');
    container.innerHTML = '';

    if (list.length === 0) {
      container.innerHTML = '<p>No news articles match the selected filters.</p>';
      return;
    }

    list.forEach(item => {
      const card = document.createElement('div');
      card.className = 'news-card';
      const dateObj = new Date(item.pubDate);
      const localDateString = dateObj.toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
      const catSlug = categoryToSlug(item.category || 'Uncategorised');
      const badgeClass = `badge-${catSlug}`;
      card.innerHTML = `
        <h3><a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a></h3>
        <div class="meta">${localDateString} • ${item.source} • ${item.district}</div>
        <span class="badge ${badgeClass}">${item.category}</span>
        <p>${item.summary}</p>
        <p><a href="${item.link}" target="_blank" rel="noopener noreferrer">Read more</a></p>
      `;
      container.appendChild(card);
    });
  }

  function renderPage(page) {
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageItems = filteredStories.slice(startIndex, endIndex);
    render(pageItems);
    renderPagination();
  }

  function renderPagination() {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    const totalPages = Math.ceil(filteredStories.length / itemsPerPage);
    if (totalPages <= 1) {
      return;
    }
    for (let i = 1; i <= totalPages; i++) {
      const btn = document.createElement('button');
      btn.className = 'page-link';
      btn.textContent = i;
      if (i === currentPage) {
        btn.classList.add('active');
      }
      btn.addEventListener('click', () => {
        currentPage = i;
        renderPage(currentPage);
      });
      pagination.appendChild(btn);
    }
  }
});
