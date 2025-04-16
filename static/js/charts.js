// Dashboard Charts for Library Management System

document.addEventListener('DOMContentLoaded', function() {
  // Category Distribution Chart
  const ctxCategory = document.getElementById('categoryChart');
  if (ctxCategory) {
    const categoryData = JSON.parse(ctxCategory.dataset.categories || '[]');
    const categoryLabels = JSON.parse(ctxCategory.dataset.labels || '[]');
    
    new Chart(ctxCategory, {
      type: 'doughnut',
      data: {
        labels: categoryLabels,
        datasets: [{
          data: categoryData,
          backgroundColor: [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)',
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'right',
          },
          title: {
            display: true,
            text: 'Book Categories'
          }
        }
      }
    });
  }

  // Monthly Issues Chart
  const ctxMonthly = document.getElementById('monthlyChart');
  if (ctxMonthly) {
    const monthlyData = JSON.parse(ctxMonthly.dataset.values || '[]');
    const monthlyLabels = JSON.parse(ctxMonthly.dataset.labels || '[]');
    
    new Chart(ctxMonthly, {
      type: 'line',
      data: {
        labels: monthlyLabels,
        datasets: [{
          label: 'Books Issued',
          data: monthlyData,
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          tension: 0.1,
          fill: true
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Monthly Book Issues'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0
            }
          }
        }
      }
    });
  }

  // Rating Distribution Chart
  const ctxRatings = document.getElementById('ratingsChart');
  if (ctxRatings) {
    const ratingsData = JSON.parse(ctxRatings.dataset.values || '[]');
    const ratingsLabels = JSON.parse(ctxRatings.dataset.labels || '[]');
    
    new Chart(ctxRatings, {
      type: 'bar',
      data: {
        labels: ratingsLabels.map(rating => `${rating} Star${rating > 1 ? 's' : ''}`),
        datasets: [{
          label: 'Number of Reviews',
          data: ratingsData,
          backgroundColor: 'rgba(255, 206, 86, 0.7)',
          borderColor: 'rgba(255, 206, 86, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Rating Distribution'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0
            }
          }
        }
      }
    });
  }
});
