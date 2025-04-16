// Helper functions for the Library Management System

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', () => {
  // Initialize all tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize all popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Setup deletion confirmations
  setupDeleteConfirmations();

  // Setup return date fine calculations
  setupFineCalculations();

  // Setup book search autocomplete
  setupBookSearch();

  // File input preview for book covers
  setupImagePreviews();
});

// Setup delete confirmation handlers
function setupDeleteConfirmations() {
  document.querySelectorAll('.delete-confirm').forEach(button => {
    button.addEventListener('click', (e) => {
      if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
        e.preventDefault();
      }
    });
  });
}

// Setup fine calculation for book returns
function setupFineCalculations() {
  const returnDateInput = document.getElementById('return_date');
  const fineAmountInput = document.getElementById('fine_amount');
  const dueDateElement = document.getElementById('due_date_value');
  
  if (returnDateInput && fineAmountInput && dueDateElement) {
    returnDateInput.addEventListener('change', () => {
      const dueDate = new Date(dueDateElement.dataset.date);
      const returnDate = new Date(returnDateInput.value);
      
      // Calculate days difference
      const diffTime = returnDate - dueDate;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      // Only charge fine if returned after due date
      if (diffDays > 0) {
        // Calculate fine (e.g., $1 per day)
        fineAmountInput.value = diffDays.toFixed(2);
      } else {
        fineAmountInput.value = '0.00';
      }
    });
  }
}

// Setup book search with autocomplete
function setupBookSearch() {
  const searchInput = document.getElementById('search_term');
  const resultsList = document.getElementById('search_results');
  
  if (searchInput && resultsList) {
    searchInput.addEventListener('input', function() {
      const searchTerm = this.value.trim();
      
      if (searchTerm.length < 2) {
        resultsList.innerHTML = '';
        resultsList.style.display = 'none';
        return;
      }
      
      // Make a fetch request to search endpoint
      fetch(`/books/search?term=${encodeURIComponent(searchTerm)}`)
        .then(response => response.json())
        .then(data => {
          resultsList.innerHTML = '';
          
          if (data.length === 0) {
            resultsList.style.display = 'none';
            return;
          }
          
          data.forEach(book => {
            const item = document.createElement('a');
            item.href = `/books/${book.id}`;
            item.classList.add('list-group-item', 'list-group-item-action');
            item.textContent = `${book.title} by ${book.author}`;
            resultsList.appendChild(item);
          });
          
          resultsList.style.display = 'block';
        })
        .catch(error => console.error('Error searching books:', error));
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(e) {
      if (e.target !== searchInput && e.target !== resultsList) {
        resultsList.style.display = 'none';
      }
    });
  }
}

// Setup image preview for book cover uploads
function setupImagePreviews() {
  const fileInput = document.getElementById('cover_image');
  const previewContainer = document.getElementById('image-preview');
  
  if (fileInput && previewContainer) {
    fileInput.addEventListener('change', function() {
      previewContainer.innerHTML = '';
      
      if (this.files && this.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
          const img = document.createElement('img');
          img.src = e.target.result;
          img.classList.add('img-fluid', 'mt-2', 'book-cover');
          previewContainer.appendChild(img);
        }
        
        reader.readAsDataURL(this.files[0]);
      }
    });
  }
}

// Handle rating star selection
function selectRating(rating) {
  document.getElementById('rating').value = rating;
  
  // Update visual stars
  for (let i = 1; i <= 5; i++) {
    const star = document.getElementById(`star-${i}`);
    if (star) {
      if (i <= rating) {
        star.classList.add('filled');
        star.classList.remove('empty');
      } else {
        star.classList.add('empty');
        star.classList.remove('filled');
      }
    }
  }
}
