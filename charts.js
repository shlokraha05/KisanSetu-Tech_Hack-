// KisanSetu Admin Analytics Visualization using Chart.js

document.addEventListener('DOMContentLoaded', async () => {
    const trendCtx = document.getElementById('dailyTrendChart');
    if (!trendCtx) return; // Not on admin dashboard

    try {
        const response = await fetch('/admin/api/analytics');
        const data = await response.json();

        const agriGreen = '#2d6a4f';
        const agriLight = '#52b788';
        const amberColor = '#d97706';
        const blueColor = '#2563eb';
        const redColor = '#dc2626';

        // 1. Daily Bookings Trend
        new Chart(trendCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: data.daily_trend.labels,
                datasets: [{
                    label: 'Bookings Count',
                    data: data.daily_trend.values,
                    borderColor: agriGreen,
                    backgroundColor: 'rgba(45, 106, 79, 0.12)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: agriGreen,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } }
                }
            }
        });

        // 2. Booking Status Distribution
        const statusCtx = document.getElementById('statusDistributionChart');
        if (statusCtx) {
            new Chart(statusCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: data.status_distribution.labels,
                    datasets: [{
                        data: data.status_distribution.values,
                        backgroundColor: ['#2d6a4f', '#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#6b7280']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 12 } }
                    }
                }
            });
        }

        // 3. Centre-wise Load
        const centreCtx = document.getElementById('centreDistributionChart');
        if (centreCtx) {
            new Chart(centreCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.centre_distribution.labels,
                    datasets: [{
                        label: 'Total Bookings',
                        data: data.centre_distribution.values,
                        backgroundColor: '#40916c',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 } }
                    }
                }
            });
        }

        // 4. Crop-wise Procurement (Quintals)
        const cropCtx = document.getElementById('cropDistributionChart');
        if (cropCtx) {
            new Chart(cropCtx.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: data.crop_distribution.labels,
                    datasets: [{
                        data: data.crop_distribution.values,
                        backgroundColor: ['#1b4332', '#40916c', '#74c69d', '#b7e4c7', '#d8f3dc', '#f3c68f']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 12 } }
                    }
                }
            });
        }

        // 5. Payment Distribution
        const paymentCtx = document.getElementById('paymentDistributionChart');
        if (paymentCtx) {
            new Chart(paymentCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: data.payment_distribution.labels,
                    datasets: [{
                        data: data.payment_distribution.values,
                        backgroundColor: ['#f59e0b', '#3b82f6', '#10b981', '#ef4444']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 12 } }
                    }
                }
            });
        }

    } catch (e) {
        console.error('Failed to load chart analytics:', e);
    }
});
